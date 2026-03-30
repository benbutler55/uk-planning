"""Regression test: verify refactored build produces identical HTML output."""
import hashlib
import json
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SITE = ROOT / "site"
FIXTURE = Path(__file__).parent / "baseline_snapshot.json"


def hash_file(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def snapshot_site() -> dict[str, str]:
    return {
        str(p.relative_to(SITE)): hash_file(p)
        for p in sorted(SITE.rglob("*.html"))
    }


@pytest.fixture
def baseline_snapshot():
    return json.loads(FIXTURE.read_text())


def test_build_output_unchanged(baseline_snapshot):
    """Compare current build output against saved baseline."""
    current = snapshot_site()
    assert set(current.keys()) == set(baseline_snapshot.keys()), (
        f"File set changed.\n"
        f"  Added: {set(current.keys()) - set(baseline_snapshot.keys())}\n"
        f"  Removed: {set(baseline_snapshot.keys()) - set(current.keys())}"
    )
    mismatches = [
        f for f in current
        if current[f] != baseline_snapshot[f]
    ]
    assert not mismatches, f"Content changed in: {mismatches}"
