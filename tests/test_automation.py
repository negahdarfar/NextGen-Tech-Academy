import pytest

from nextgen_academy.automation import run_automated


def test_cloud_pipeline_requires_free_pexels_key(monkeypatch, tmp_path):
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="PEXELS_API_KEY"):
        run_automated("test topic", output_dir=tmp_path)
