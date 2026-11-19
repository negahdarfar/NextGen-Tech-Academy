import pytest

from nextgen_academy.automation import run_automated


def test_cloud_pipeline_requires_a_visual_provider(monkeypatch, tmp_path):
    monkeypatch.delenv("AGNES_API_KEY", raising=False)
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="visual provider"):
        run_automated("test topic", output_dir=tmp_path)
