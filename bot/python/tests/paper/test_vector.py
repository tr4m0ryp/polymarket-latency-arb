"""The pandas-free vectorizer + C trees reproduce the research scorer (sklearn) exactly."""
import numpy as np
import pandas as pd
import pytest

from research.predict.model.data import TAB
from research.predict.model.store import predict_sides


@pytest.mark.skipif(not (TAB / "471.npz").exists(), reason="research tables not present")
def test_vector_equals_sklearn():
    from btclat.paper.model.load import ValueModel
    vm = ValueModel("v1_L0")
    with np.load(TAB / "471.npz") as z:
        df = pd.DataFrame({k: z[k] for k in z.files}).iloc[::7].reset_index(drop=True)
    pu, pdn = predict_sides(df, {"model": vm.sk, "vf": vm.vec.vf})
    got = np.array([vm(r) for r in df.to_dict("records")])
    assert np.abs(got - np.c_[pu, pdn]).max() < 1e-12


def test_hash_mismatch_refuses(tmp_path, monkeypatch):
    from btclat.paper.model import load
    p = tmp_path / "prereg2.json"
    p.write_text('{"models_sha256_16": {"v1_L0.pkl": "0000000000000000"}}')
    monkeypatch.setattr(load, "PREREG", p)
    with pytest.raises(SystemExit):
        load.ValueModel("v1_L0")
