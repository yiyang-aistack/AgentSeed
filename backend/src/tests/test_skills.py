"""Tests for :mod:`src.capabilities.skills` and the ``functional_testcase`` asset.

The skills layer is pure text plumbing, so what is worth asserting is that the
asset is *discoverable* and that the loader hands back the body **without** the
YAML front matter — a front-matter regression would silently ship ``name:`` and
``description:`` lines to the model as if they were instructions.
"""

import pytest
from src.capabilities.skills import available, get_texts
from src.capabilities.skills.loader import _ENTRIES_DIR


def test_functional_testcase_is_discoverable():
    assert "functional_testcase" in available()


def test_asset_file_exists_where_the_loader_looks():
    """Guards against the asset being moved out of the scanned directory."""
    assert (_ENTRIES_DIR / "functional_testcase.md").is_file()


def test_get_texts_strips_front_matter():
    [body] = get_texts(["functional_testcase"])
    assert not body.startswith("---")
    assert "name: functional_testcase" not in body
    assert body.lstrip().startswith("# Functional Test Case Design")


def test_get_texts_carries_the_methodology():
    [body] = get_texts(["functional_testcase"])
    # The playbook is only useful if the techniques are actually in it.
    for technique in ("Equivalence partitioning", "Boundary value analysis", "Decision table"):
        assert technique in body


def test_get_texts_returns_requested_order():
    """Order matters: the agent layers project policy under the playbook."""
    bodies = get_texts(["functional_testcase", "review_policy"])
    assert len(bodies) == 2
    assert "Functional Test Case Design" in bodies[0]
    assert "Review Policy" in bodies[1]


def test_unknown_skill_raises_key_error():
    with pytest.raises(KeyError, match="No skill named 'nope'"):
        get_texts(["nope"])
