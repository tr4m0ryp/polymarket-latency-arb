"""Entry point: `python3 research/predict/improve/diag/loss-anatomy {build|calib|analyze}`.

Registers this hyphenated directory as the package `loss_anatomy` (repo root on sys.path,
the directory itself removed so its subfolders cannot shadow top-level modules)."""
import importlib
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def bootstrap():
    sys.path[:] = [p for p in sys.path if p and Path(p).resolve() != HERE]
    sys.path.insert(0, str(ROOT))
    if "loss_anatomy" not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            "loss_anatomy", HERE / "__init__.py", submodule_search_locations=[str(HERE)])
        mod = importlib.util.module_from_spec(spec)
        sys.modules["loss_anatomy"] = mod
        spec.loader.exec_module(mod)


if __name__ == "__main__":
    bootstrap()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    target = {"build": "loss_anatomy.build", "calib": "loss_anatomy.data.calib",
              "analyze": "loss_anatomy.analyze.run"}[cmd]
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    importlib.import_module(target).main()
