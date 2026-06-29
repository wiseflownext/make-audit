"""Tests for project structure and dependency availability (Task 1.1)."""
import importlib
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).parent.parent


def test_requirements_txt_exists():
    assert (BACKEND_ROOT / "requirements.txt").exists(), "requirements.txt missing"


def test_requirements_contains_key_deps():
    reqs = (BACKEND_ROOT / "requirements.txt").read_text()
    for pkg in ["fastapi", "uvicorn", "openpyxl", "pandas", "Pillow", "weasyprint"]:
        assert pkg.lower() in reqs.lower(), f"Missing dependency: {pkg}"


def test_app_package_exists():
    assert (BACKEND_ROOT / "app" / "__init__.py").exists()


def test_app_submodules_exist():
    for module in ["api", "core", "models", "services"]:
        assert (BACKEND_ROOT / "app" / module / "__init__.py").exists(), (
            f"Missing submodule: app/{module}"
        )


def test_main_module_importable():
    sys.path.insert(0, str(BACKEND_ROOT))
    try:
        import app.main  # noqa: F401
    except ImportError as e:
        raise AssertionError(f"app.main not importable: {e}")
    finally:
        sys.path.pop(0)
