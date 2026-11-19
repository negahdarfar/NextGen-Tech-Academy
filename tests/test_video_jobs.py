import json

import pytest

from nextgen_academy.video_jobs import submit_segments
from nextgen_academy.video_segments import build_segments


class FakeProvider:
    def __init__(self):
        self.prompts = []

    def submit_video(self, prompt):
        self.prompts.append(prompt)
        return {"uuid": f"job-{len(self.prompts)}"}


def test_submit_segments_persists_jobs_in_order(tmp_path):
    provider = FakeProvider()
    segments = build_segments("Robotics", ["Factory", "Robot close-up"])
    path = tmp_path / "jobs.json"

    manifest = submit_segments(segments, provider, path)

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["status"] == "submitted"
    assert [job["job_uuid"] for job in saved["jobs"]] == ["job-1", "job-2"]
    assert len(provider.prompts) == 2


def test_resume_skips_already_accepted_jobs(tmp_path):
    segments = build_segments("Robotics", ["Factory", "Robot close-up"])
    path = tmp_path / "jobs.json"
    first_provider = FakeProvider()
    submit_segments(segments[:1], first_provider, path)

    second_provider = FakeProvider()
    manifest = submit_segments(segments, second_provider, path)

    assert len(second_provider.prompts) == 1
    assert [job["job_uuid"] for job in manifest["jobs"]] == ["job-1", "job-1"]


def test_resume_rejects_a_different_storyboard(tmp_path):
    path = tmp_path / "jobs.json"
    submit_segments(build_segments("Robotics", ["Factory"]), FakeProvider(), path)
    with pytest.raises(ValueError):
        submit_segments(build_segments("Space", ["Rocket launch"]), FakeProvider(), path)
