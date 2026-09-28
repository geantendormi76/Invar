from harness.run_models import ResearchRun, ResearchScope, RunStatus, RunTrack


def _make_run(**kwargs):
    return ResearchRun(
        run_id="RUN-TRACK-CONTRACT",
        target_root="example.com",
        scope=ResearchScope(target_domain="example.com"),
        **kwargs,
    )


def test_default_track_is_production():
    run = _make_run()
    assert run.track is RunTrack.PRODUCTION


def test_track_is_exposed_by_inspect():
    run = _make_run()

    inspected = run.inspect()

    assert inspected["track"] == RunTrack.PRODUCTION.value
    assert inspected["status"] == RunStatus.INIT.value


def test_track_round_trips_through_serialization():
    run = _make_run(track=RunTrack.RESEARCH)

    restored = ResearchRun.from_dict(run.to_dict())

    assert restored.track is RunTrack.RESEARCH


def test_legacy_run_payload_preserves_research_semantics():
    run = _make_run()

    data = run.to_dict()
    data.pop("track")

    restored = ResearchRun.from_dict(data)

    assert restored.track is RunTrack.RESEARCH
