import numpy as np
import pytest

from football_intelligence.dna.registry import CORE, FAMILIES
from football_intelligence.dna.similarity import Representation, matrix, percentile, select, topk


def test_symmetry_identical_profiles_and_family_weighting():
    x = np.random.default_rng(17).normal(size=(30, len(CORE)))
    model = Representation().fit(x)
    d = model.distances(x, x)
    assert np.allclose(d, d.T) and np.allclose(d.diagonal(), 0)
    assert model.distances(x[:1], x[:1])[0, 0] == 0
    for family in set(FAMILIES.values()):
        assert sum(
            model.weights[j] for j, f in enumerate(CORE) if FAMILIES[f] == family
        ) == pytest.approx(0.2)
    explanation = model.explain(x[0], x[1])
    assert explanation["distance"] == pytest.approx(d[0, 1])
    assert sum(explanation["families"].values()) == pytest.approx(1)
    assert sum(f["squared_contribution"] for f in explanation["features"]) == pytest.approx(
        d[0, 1] ** 2
    )


def test_null_and_constant_profiles_rejected():
    with pytest.raises(ValueError, match="Missing"):
        Representation().fit(np.full((3, len(CORE)), np.nan))
    with pytest.raises(ValueError, match="constant"):
        Representation().fit(np.zeros((3, len(CORE))))
    with pytest.raises(ValueError, match="Missing"):
        matrix([{"values": dict.fromkeys(CORE, None)}])


def test_topk_ties_stable_no_self():
    assert topk(np.zeros((3, 3)), ["c", "a", "b"], k=2) == [[1, 2], [2, 0], [1, 0]]


def test_role_eligibility_and_percentile_ties():
    profiles = [
        dict(
            player_id=str(i),
            minutes=1000,
            primary_role="CM" if i < 12 else "AM",
            values=dict.fromkeys(CORE, 1),
        )
        for i in range(13)
    ]
    assert len(select(profiles, 900)) == 12
    assert percentile(np.array([0, 0, 1, 2]), 0) == 25


@pytest.mark.parametrize("method", ["euclidean", "cosine", "pca"])
def test_methods_finite_and_reproducible(method):
    x = np.random.default_rng(1).normal(size=(15, len(CORE)))
    a = Representation(method=method).fit(x)
    b = Representation(method=method).fit(x)
    assert np.allclose(a.distances(x, x), b.distances(x, x))
    assert np.isfinite(a.distances(x, x)).all()
    assert np.allclose(np.diag(a.distances(x, x)), 0, atol=1e-8)
