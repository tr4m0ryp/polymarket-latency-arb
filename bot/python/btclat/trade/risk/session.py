"""A live session's safety shell, shared by probe and micro:

- kill file (`~/.config/btclat/KILL`): `killed()` is checked every loop; touching the file
  stops the run within one loop and blocks any new start until it is removed;
- cancel-all on exit: leaving the `with` block for any reason (normal end, kill, loss cap,
  exception, SIGTERM / SIGINT turned into SystemExit by `install_signals`) sends DELETE
  /cancel-all, retried, and logs the outcome."""
from __future__ import annotations

import signal
import time
from pathlib import Path


class Stop(Exception):
    """Raised inside a session to end it cleanly (kill file, loss cap, venue anomaly)."""


def install_signals() -> None:
    def _raise(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, _raise)


class Session:
    def __init__(self, venue, kill: Path, note=None, retries: int = 3, sleep=time.sleep):
        self.venue, self.kill = venue, Path(kill)
        self.note = note or (lambda kind, **kw: None)
        self.retries, self.sleep = retries, sleep
        self.cancel_all_ok: bool | None = None
        self.exit_reason: str | None = None

    def killed(self) -> bool:
        return self.kill.exists()

    def check(self) -> None:
        if self.killed():
            raise Stop(f"kill file {self.kill}")

    def __enter__(self) -> "Session":
        return self       # the first loop's check() runs inside the block, so exit still cancels

    def cancel_all(self) -> bool:
        for i in range(self.retries):
            try:
                r = self.venue.cancel_all()
                self.note("cancel_all", attempt=i, **(r.brief() if hasattr(r, "brief") else {"resp": repr(r)}))
                if getattr(r, "ok", False):
                    return True
            except Exception as e:  # keep trying: this is the last line of defence
                self.note("cancel_all_error", attempt=i, err=repr(e)[:200])
            self.sleep(0.5 * (i + 1))
        return False

    def __exit__(self, et, ev, tb) -> bool:
        self.exit_reason = "normal" if et is None else f"{et.__name__}: {ev}"
        self.cancel_all_ok = self.cancel_all()
        self.note("session_end", reason=self.exit_reason, cancel_all_ok=self.cancel_all_ok)
        return et is Stop      # a Stop is a clean end; anything else propagates
