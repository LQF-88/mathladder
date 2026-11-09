"""Repository persistence, progress aggregation and the mistake book."""

from datetime import date

from app.engine.models import Question, SessionResult
from app.storage.repository import Repository


def _question(qid: str = "q1", level: str = "5A") -> Question:
    return Question(
        level=level,
        topic="5A.count" if level == "5A" else "C.x1",
        prompt="数一数：● ● ●",
        answer="3",
        explanation="一共有 3 个。",
        qid=qid,
    )


def _result(level="5A", topic="5A.count", total=10, correct=8, wrong=None, **kwargs):
    return SessionResult(
        level=level,
        topic=topic,
        total=total,
        correct=correct,
        seconds=90,
        wrong=wrong or [],
        **kwargs,
    )


def test_defaults(tmp_path):
    repo = Repository(str(tmp_path / "progress.json"))
    assert repo.get_setting("questions_per_session") == 20
    assert repo.get_setting("sound") is True
    assert repo.total_answered() == 0
    assert repo.overall_accuracy() == 0
    assert repo.mistake_count() == 0
    assert repo.streak()["current"] == 0
    assert repo.recommended_level() == "5A"


def test_record_session_updates_everything(tmp_path):
    repo = Repository(str(tmp_path / "progress.json"))
    mistake = _question()
    result = _result(wrong=[(mistake, "999")])
    repo.record_session(result)

    progress = repo.level_progress("5A")
    assert progress["answered"] == 10
    assert progress["correct"] == 8
    assert progress["sessions"] == 1
    assert progress["stars"] == 2
    assert progress["topics"]["5A.count"]["answered"] == 10
    assert repo.total_answered() == 10
    assert repo.overall_accuracy() == 80
    assert repo.progress_percent("5A") == 10 / 200
    assert repo.streak()["current"] == 1
    assert repo.streak()["best"] == 1
    assert repo.mistake_count() == 1
    assert repo.mistakes()[0]["qid"] == "q1"
    assert repo.mistakes()[0]["user"] == "999"
    series = repo.daily_series(7)
    assert len(series) == 7
    assert series[-1] == (date.today().isoformat(), 10)
    assert repo.recent_sessions(1)[0]["accuracy"] == 80
    assert repo.last_practiced_topic("5A") == "5A.count"


def test_session_persists_and_star_record_is_kept(tmp_path):
    path = str(tmp_path / "progress.json")
    repo = Repository(path)
    repo.record_session(_result())
    repo.record_session(_result(total=2, correct=2))
    assert repo.level_progress("5A")["stars"] == 3

    reloaded = Repository(path)
    assert reloaded.total_answered() == 12
    assert reloaded.level_progress("5A")["stars"] == 3
    assert reloaded.get_setting("questions_per_session") == 20


def test_corrected_mistake_is_removed(tmp_path):
    repo = Repository(str(tmp_path / "progress.json"))
    mistake = _question()
    repo.add_mistake(mistake, "2")
    repo.save()
    assert repo.mistake_count() == 1

    replay = SessionResult(
        level="5A",
        topic="5A.count",
        total=1,
        correct=1,
        seconds=10,
        correct_ids=["q1"],
        from_mistakes=True,
    )
    repo.record_session(replay)
    assert repo.mistake_count() == 0


def test_mistake_book_is_capped(tmp_path):
    repo = Repository(str(tmp_path / "progress.json"))
    for index in range(105):
        repo.add_mistake(_question(qid=f"q{index}"), "0")
    assert repo.mistake_count() == 100
    assert repo.mistakes()[0]["qid"] == "q104"
    repo.clear_mistakes()
    assert repo.mistake_count() == 0


def test_recommended_level_follows_last_session(tmp_path):
    repo = Repository(str(tmp_path / "progress.json"))
    repo.record_session(_result(level="C", topic="C.x1", total=5, correct=5))
    assert repo.recommended_level() == "C"
    assert repo.progress_percent("C") == 5 / 200


def test_settings_and_reset(tmp_path):
    path = str(tmp_path / "progress.json")
    repo = Repository(path)
    repo.set_setting("sound", False)
    repo.set_setting("questions_per_session", 10)
    repo.record_session(_result())
    assert Repository(path).get_setting("sound") is False
    assert Repository(path).get_setting("questions_per_session") == 10

    repo.reset()
    assert repo.total_answered() == 0
    assert repo.mistake_count() == 0
    assert repo.get_setting("questions_per_session") == 20
    assert Repository(path).total_answered() == 0


def test_corrupt_file_falls_back_to_defaults(tmp_path):
    path = tmp_path / "progress.json"
    path.write_text("{not valid json", encoding="utf-8")
    repo = Repository(str(path))
    assert repo.total_answered() == 0
    assert repo.streak()["current"] == 0
