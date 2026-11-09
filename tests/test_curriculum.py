"""Sanity checks for the static curriculum map."""

from app.engine.curriculum import (
    LEVEL_BY_CODE,
    LEVELS,
    TOPIC_BY_KEY,
    level_of,
    topic_of,
)


def test_sixteen_levels_in_order():
    codes = [level.code for level in LEVELS]
    assert codes == [
        "5A", "4A", "3A", "2A", "A", "B", "C", "D",
        "E", "F", "G", "H", "I", "J", "K", "L",
    ]
    assert set(LEVEL_BY_CODE) == set(codes)


def test_topic_keys_are_unique_and_owned():
    assert len(TOPIC_BY_KEY) == len({topic.key for topic in TOPIC_BY_KEY.values()})
    for level in LEVELS:
        assert 3 <= len(level.topics) <= 8
        for topic in level.topics:
            assert topic.key.startswith(level.code + ".")
            assert level_of(level.code).name == level.name
            assert topic_of(topic.key).name == topic.name
            assert topic.description


def test_level_metadata_is_complete():
    for level in LEVELS:
        assert level.name and level.subtitle and level.description
        assert level.color.startswith("#") and len(level.color) == 7
        assert level.target > 0


def test_unknown_codes_raise():
    try:
        level_of("Z")
    except KeyError:
        pass
    else:  # pragma: no cover - explicit failure path
        raise AssertionError("unknown level should raise KeyError")
