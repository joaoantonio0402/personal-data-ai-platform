import subprocess
import sys
from pathlib import Path


def test_spt_pipeline_direct_execution_does_not_fail_on_src_import():
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(repo_root / "src" / "pipelines" / "spt_pipeline.py")],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
