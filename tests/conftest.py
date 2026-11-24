import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "teach" / "scripts"
VALIDATORS = ROOT / "scripts"

for path in (str(SCRIPTS), str(VALIDATORS)):
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def fixtures() -> Path:
    return ROOT / "tests" / "fixtures"


@pytest.fixture
def plugin_root(tmp_path: Path) -> Path:
    target = tmp_path / "plugin"
    shutil.copytree(
        ROOT,
        target,
        ignore=shutil.ignore_patterns(
            ".git", ".pytest_cache", ".venv", "__pycache__",
            ".coverage", "coverage.xml", "htmlcov",
        ),
    )
    return target


@pytest.fixture
def study(tmp_path: Path, fixtures: Path) -> Path:
    target = tmp_path / "study"
    shutil.copytree(fixtures / "valid-study", target)
    return target


def replace_in(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def codes(report) -> set[str]:
    return {issue.code for issue in report.errors}
