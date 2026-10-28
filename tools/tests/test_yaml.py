"""Restricted YAML is checked before the loader can normalize forbidden features."""

import pytest

from homalg.schemas import YamlError, load_yaml


@pytest.mark.parametrize(
    "source",
    [
        "a: 1\n<<: {b: 2}",
        "outer: {a: 1, <<: {b: 2}}",
        '"<<": {a: 1}',
        "a: &a {value: 1}\nb: *a",
        "a: !custom value",
        "a: 1\na: 2",
    ],
)
def test_yaml_rejects_forbidden_features(source: str) -> None:
    """Merge mappings without anchors must be rejected as well as aliased merges."""
    with pytest.raises(YamlError):
        load_yaml(source)


def test_yaml12_values_remain_literal() -> None:
    """YAML 1.2 avoids legacy implicit booleans; a value may contain merge-like text."""
    assert load_yaml('on: "2000-01-01"\nanswer: yes\noperator: "<<"') == {
        "on": "2000-01-01",
        "answer": "yes",
        "operator": "<<",
    }
