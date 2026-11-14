"""Entry point: `python3 research/predict/improve/diag/mechanism-literature {build|analyze|calib|fills|posthoc|sidecheck|deciles|surprise|gate}`.

Registers this hyphenated directory as the package `mech_lit` (repo root on sys.path, the
directory itself removed so its subfolders cannot shadow top-level modules)."""
import importlib
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def bootstrap():
    sys.path[:] = [p for p in sys.path if p and Path(p).resolve() != HERE]
    sys.path.insert(0, str(ROOT))
    if "mech_lit" not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            "mech_lit", HERE / "__init__.py", submodule_search_locations=[str(HERE)])
        mod = importlib.util.module_from_spec(spec)
        sys.modules["mech_lit"] = mod
        spec.loader.exec_module(mod)


if __name__ == "__main__":
    bootstrap()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    target = {"build": "mech_lit.build", "analyze": "mech_lit.analyze.run",
              "calib": "mech_lit.calib.rows", "fills": "mech_lit.calib.fills",
              "posthoc": "mech_lit.analyze.posthoc", "sidecheck": "mech_lit.race.sidecheck",
              "deciles": "mech_lit.race.deciles", "surprise": "mech_lit.race.surprise", "gate": "mech_lit.race.gate"}[cmd]
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    importlib.import_module(target).main()
