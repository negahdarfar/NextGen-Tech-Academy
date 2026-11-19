import json

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
