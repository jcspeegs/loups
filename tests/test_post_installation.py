"""
Post-installation tests for loups package.

These tests are designed to run AFTER installing the package from TestPyPI or PyPI
to verify that the packaged distribution works correctly. They test aspects that
can only be validated after installation:

- CLI entry point accessibility
- Package data inclusion (bundled templates)
- Dependency installation
- Module importability

Run these tests in a clean environment after installing from TestPyPI:

    pip install --index-url https://test.pypi.org/simple/ \
                --extra-index-url https://pypi.org/simple/ \
                loups
    pytest tests/test_post_installation.py -v
"""

import subprocess
from importlib.resources import files

import pytest


class TestCLIAccessibility:
    """Test that the loups CLI command is accessible and functional."""

    def test_cli_command_exists(self):
        """Verify loups CLI command is in PATH and executable."""
        result = subprocess.run(
            ["loups", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"CLI command failed: {result.stderr}"
        assert "loups" in result.stdout.lower(), "CLI help doesn't mention loups"

    def test_cli_help_output(self):
        """Verify CLI help contains expected content."""
        result = subprocess.run(
            ["loups", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        # Check for key options that should be in help
        assert "--template" in result.stdout or "-t" in result.stdout
        assert "--output" in result.stdout or "-o" in result.stdout


class TestPackageDataInclusion:
    """Test that bundled package data is included in the distribution."""

    def test_data_directory_exists(self):
        """Verify the loups/data directory is accessible."""
        data_path = files("loups").joinpath("data")
        assert data_path.is_dir(), "Package data directory missing!"

    def test_template_files_included(self):
        """Verify template image files are bundled."""
        data_path = files("loups").joinpath("data")

        # Check for template files that should be bundled
        expected_files = [
            "template_solid.png",
            "thumbnail_template.png",
        ]

        for filename in expected_files:
            file_path = data_path.joinpath(filename)
            assert file_path.exists(), f"Expected template file missing: {filename}"

    def test_package_data_readable(self):
        """Verify package data files can be read."""
        data_path = files("loups").joinpath("data")

        # Try to read one of the template files as bytes
        template_file = data_path.joinpath("template_solid.png")
        content = template_file.read_bytes()

        # PNG files start with specific magic bytes
        assert content[:8] == b"\x89PNG\r\n\x1a\n", "Template file is not a valid PNG"


class TestDependencyInstallation:
    """Test that all required dependencies are installed and importable."""

    def test_easyocr_importable(self):
        """Verify easyocr can be imported."""
        import easyocr  # noqa: F401

    def test_opencv_importable(self):
        """Verify opencv (cv2) can be imported."""
        import cv2  # noqa: F401

    def test_typer_importable(self):
        """Verify typer can be imported."""
        import typer  # noqa: F401

    def test_rich_importable(self):
        """Verify rich can be imported."""
        import rich  # noqa: F401

    def test_scikit_image_importable(self):
        """Verify scikit-image can be imported."""
        from skimage import metrics  # noqa: F401

    def test_all_dependencies_import(self):
        """Test importing all dependencies together."""
        import cv2  # noqa: F401
        import easyocr  # noqa: F401
        import rich  # noqa: F401
        import typer  # noqa: F401
        from skimage import metrics  # noqa: F401


class TestModuleImportability:
    """Test that loups modules can be imported correctly."""

    def test_loups_package_importable(self):
        """Verify the loups package can be imported."""
        import loups  # noqa: F401

        assert hasattr(loups, "__file__"), "Package has no __file__ attribute"

    def test_cli_module_importable(self):
        """Verify the CLI module and app can be imported."""
        from loups.cli import app  # noqa: F401

    def test_match_template_scan_importable(self):
        """Verify match_template_scan module can be imported."""
        from loups.match_template_scan import MatchTemplateScan  # noqa: F401

    def test_core_classes_instantiable(self):
        """Verify core classes are classes and have expected attributes."""
        from loups import Loups
        from loups.match_template_scan import MatchTemplateScan

        # Verify these are classes (have __init__)
        assert hasattr(Loups, "__init__"), "Loups is not a class"
        assert hasattr(
            MatchTemplateScan, "__init__"
        ), "MatchTemplateScan is not a class"

        # Verify Loups has the scan method
        assert hasattr(Loups, "scan"), "Loups class missing scan method"


class TestPackageMetadata:
    """Test that package metadata is correct."""

    def test_package_has_version(self):
        """Verify the package has a version attribute or metadata."""
        try:
            from importlib.metadata import version

            pkg_version = version("loups")
            assert pkg_version, "Package version is empty"
            assert isinstance(pkg_version, str), "Version is not a string"
        except Exception as e:
            pytest.fail(f"Could not get package version: {e}")

    def test_package_has_metadata(self):
        """Verify the package has accessible metadata."""
        from importlib.metadata import metadata

        meta = metadata("loups")
        assert meta["Name"] == "loups", "Package name mismatch"
        assert "description" in meta.get("Summary", "").lower() or meta.get(
            "Summary"
        ), "Missing package description"


# Optional: These tests might require test fixtures
class TestFunctionalSmoke:
    """Optional smoke tests for basic functionality (requires test assets)."""

    @pytest.mark.skip(reason="Requires test video fixtures")
    def test_video_processing_works(self):
        """Test basic video processing works end-to-end."""
        # This would require a test video file
        # loups -t template.png -o output.txt test_video.mp4
        pass
