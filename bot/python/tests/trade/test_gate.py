"""Refusal without --i-approve, credentials, safe permissions, an unlocked day, an allowed region."""
import os

import pytest

from btclat.trade import __main__ as cli
from btclat.trade.gate import preflight
from btclat.trade.gate.creds import Creds

from .fakes import FUNDER, KEY, FakeVenue, write_creds


def test_refuses_without_approve(tmp_path):
    write_creds(tmp_path)
    with pytest.raises(preflight.Refused, match="--i-approve"):
        preflight.offline(False, tmp_path)


def test_refuses_without_creds_file(tmp_path):
    with pytest.raises(preflight.Refused, match="no credentials file"):
        preflight.offline(True, tmp_path)


@pytest.mark.parametrize("mode", [0o644, 0o640, 0o604, 0o660])
def test_refuses_loose_permissions(tmp_path, mode):
    write_creds(tmp_path, mode=mode)
    with pytest.raises(preflight.Refused, match="chmod 600"):
        preflight.offline(True, tmp_path)


def test_refuses_writable_dir(tmp_path):
    write_creds(tmp_path)
    os.chmod(tmp_path, 0o777)
    with pytest.raises(preflight.Refused, match="chmod 700"):
        preflight.offline(True, tmp_path)


@pytest.mark.parametrize("kw,msg", [({"POLY_PRIVATE_KEY": "0x1234"}, "PRIVATE_KEY"),
                                    ({"POLY_FUNDER": "nope"}, "FUNDER"),
                                    ({"POLY_SIGNATURE_TYPE": "7"}, "SIGNATURE_TYPE"),
                                    ({"POLY_API_KEY": "k"}, "all of")])
def test_refuses_bad_values(tmp_path, kw, msg):
    write_creds(tmp_path, **kw)
    with pytest.raises(preflight.Refused, match=msg):
        preflight.offline(True, tmp_path)


def test_refuses_with_kill_file(tmp_path):
    write_creds(tmp_path)
    (tmp_path / "KILL").touch()
    with pytest.raises(preflight.Refused, match="kill file"):
        preflight.offline(True, tmp_path)


def test_accepts_and_redacts(tmp_path):
    write_creds(tmp_path, mode=0o400)
    c = preflight.offline(True, tmp_path)
    assert isinstance(c, Creds) and c.sig_type == 3 and c.funder == FUNDER and not c.has_l2
    assert KEY not in repr(c) and KEY[2:] not in str(c)


@pytest.mark.parametrize("geo", [{"blocked": True, "country": "FR"}, {"blocked": True, "country": "GB"},
                                 {"country": "IE"}, {"blocked": None}])
def test_online_refuses_geoblock(geo):
    with pytest.raises(preflight.Refused, match="geoblock"):
        preflight.online(FakeVenue(geo=geo), "micro")


@pytest.mark.parametrize("country", ["IE", "JP", "NL", "KR"])
def test_online_accepts_frontend_only_block(country):
    geo = {"blocked": True, "country": country, "region": "L"}
    assert preflight.online(FakeVenue(geo=geo), "micro")["geoblock"] == geo


def test_online_zero_probe_needs_no_balance():
    with pytest.raises(preflight.Refused, match="balance"):
        preflight.online(FakeVenue(balance=0.0), "probe")
    assert preflight.online(FakeVenue(balance=0.0), "probe0")["balance"] == 0.0


def test_online_refuses_version_and_balance():
    with pytest.raises(preflight.Refused, match="version"):
        preflight.online(FakeVenue(version=1), "micro")
    with pytest.raises(preflight.Refused, match="balance"):
        preflight.online(FakeVenue(balance=4.0), "micro")
    v = FakeVenue(balance=4.0)
    assert preflight.online(v, "probe")["balance"] == 4.0
    v.balance = lambda: {"balance": 50.0, "allowance_ok": False}
    with pytest.raises(preflight.Refused, match="allowance"):
        preflight.online(v, "micro")


def test_cli_refuses_before_any_network(tmp_path):
    write_creds(tmp_path)

    def factory(creds, clock):
        raise AssertionError("venue built without approval")
    with pytest.raises(preflight.Refused, match="--i-approve"):
        cli.start(["micro"], venue_factory=factory, config=tmp_path, clock=object(), root=tmp_path / "runs")
    os.chmod(tmp_path / "polymarket.env", 0o644)
    with pytest.raises(preflight.Refused, match="chmod 600"):
        cli.start(["probe", "--i-approve"], venue_factory=factory, config=tmp_path, clock=object(),
                  root=tmp_path / "runs")


def test_cli_geoblocked_sends_nothing(tmp_path):
    write_creds(tmp_path)
    v = FakeVenue(geo={"blocked": True, "country": "FR", "region": "IDF"})
    with pytest.raises(preflight.Refused, match="geoblock"):
        cli.start(["probe", "--i-approve"], venue_factory=lambda c, k: v, config=tmp_path, clock=object(),
                  root=tmp_path / "runs")
    assert v.closed and v.n("post") == 0 and v.n("sign") == 0


def test_cli_cannot_raise_limits(tmp_path):
    write_creds(tmp_path)
    with pytest.raises(SystemExit, match="looser"):
        cli.start(["micro", "--i-approve", "--max-orders-hour", "100"], config=tmp_path, clock=object())


def test_cli_refuses_existing_run_dir(tmp_path):
    write_creds(tmp_path)
    (tmp_path / "runs" / "r1").mkdir(parents=True)
    v = FakeVenue()
    with pytest.raises(preflight.Refused, match="run directory"):
        cli.start(["probe", "--i-approve", "--run", "r1"], venue_factory=lambda c, k: v, config=tmp_path,
                  clock=object(), root=tmp_path / "runs")
    assert v.closed and v.n("post") == 0
