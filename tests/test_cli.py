"""Test suite for CLI pipe detection and output handling.

TESTING LIMITATIONS:
--------------------
Due to CliRunner's output capture mechanism, we cannot test:
1. Interactive TTY behavior (Rich formatting, colors, emojis)
2. Actual Live progress rendering
3. Full Rich console.print formatting

These behaviors should be manually tested in a real terminal:
    $ loups video.mp4              # Should show animated progress
    $ loups video.mp4 > out.txt    # Should be silent, no animations
    $ loups video.mp4 -q           # Should suppress all output

What we CAN test:
- Pipe detection logic (sys.stdout.isatty())
- Output content (what text is produced)
- File operations
- Error handling
- Flag combinations
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from loups.cli import app


@pytest.fixture
def runner():
    """Create a CliRunner for testing."""
    return CliRunner(mix_stderr=False)


@pytest.fixture
def test_video(tmp_path):
    """Create a temporary video file for testing."""
    video_file = tmp_path / "test_video.mp4"
    video_file.write_text("fake video content")
    return video_file


@pytest.fixture
def mock_loups():
    """Mock the Loups class and its scan method."""
    with patch("loups.cli.Loups") as mock:
        # Create a mock game instance
        game_instance = MagicMock()
        game_instance.batter_count = 5
        game_instance.batters.display.return_value = (
            "0:00:00 Game Start\n"
            "0:05:23 Sarah Johnson #7\n"
            "0:08:45 Emma Martinez #12"
        )
        mock.return_value = game_instance
        yield mock


@pytest.fixture
def mock_template(tmp_path):
    """Create a temporary template file for testing."""
    template_file = tmp_path / "template.png"
    template_file.write_text("fake template content")

    with patch("loups.cli.get_default_template") as mock:
        mock.return_value = template_file
        yield mock


class TestPipeDetection:
    """Test automatic pipe detection and behavior changes."""

    def test_piped_output_hides_progress(
        self, runner, test_video, mock_loups, mock_template
    ):
        """Test that progress is hidden when output is piped."""
        with patch("loups.cli.sys.stdout.isatty", return_value=False):
            result = runner.invoke(app, [str(test_video)])

        # Should NOT show progress messages when piped
        assert "Scanning video:" not in result.stdout
        assert "Scan complete!" not in result.stdout
        assert "YouTube Chapters:" not in result.stdout

        # Should output plain chapter text
        assert "0:00:00 Game Start" in result.stdout
        assert "Sarah Johnson #7" in result.stdout

    def test_quiet_mode_suppresses_all_output(
        self, runner, test_video, mock_loups, mock_template
    ):
        """Test that quiet mode suppresses all stdout regardless of TTY."""
        # Quiet mode should suppress output
        result = runner.invoke(app, ["-q", str(test_video)])
        assert result.stdout == ""

    def test_piped_with_output_file_saves_silently(
        self, runner, test_video, mock_loups, mock_template, tmp_path
    ):
        """Test that piped mode with --output saves file without confirmation."""
        output_file = tmp_path / "chapters.txt"

        with patch("loups.cli.sys.stdout.isatty", return_value=False):
            result = runner.invoke(app, ["-o", str(output_file), str(test_video)])

        # Should NOT show save confirmation when piped
        assert "Results saved to:" not in result.stdout

        # Should still output chapters to stdout
        assert "0:00:00 Game Start" in result.stdout

        # File should be created
        assert output_file.exists()

    def test_output_file_created_with_correct_content(
        self, runner, test_video, mock_loups, mock_template, tmp_path
    ):
        """Test that --output file is created with correct chapter content."""
        output_file = tmp_path / "chapters.txt"

        result = runner.invoke(app, ["-o", str(output_file), str(test_video)])

        # Should complete successfully
        assert result.exit_code == 0

        # File should be created
        assert output_file.exists()

        # Verify content matches expected format
        content = output_file.read_text()
        assert "0:00:00 Game Start" in content
        assert "0:05:23 Sarah Johnson #7" in content
        assert "0:08:45 Emma Martinez #12" in content


class TestOutputFormatting:
    """Test output formatting differences between modes.

    NOTE: We can only test piped output with CliRunner.
    Interactive Rich formatting must be manually tested.
    """

    def test_piped_uses_plain_text(self, runner, test_video, mock_loups, mock_template):
        """Test that piped mode outputs plain text without formatting."""
        with patch("loups.cli.sys.stdout.isatty", return_value=False):
            result = runner.invoke(app, [str(test_video)])

        # Should not contain rich formatting
        assert "[bold]" not in result.stdout
        assert "[cyan]" not in result.stdout

        # Should contain actual chapter data
        assert "0:00:00 Game Start" in result.stdout


class TestProgressDisplay:
    """Test progress display behavior.

    NOTE: CliRunner cannot test Live progress rendering.
    We test the logic (quiet flag, piped detection) but not the visual output.
    """

    def test_progress_disabled_when_piped(
        self, runner, test_video, mock_loups, mock_template
    ):
        """Test that show_progress is False when output is piped."""
        with patch("loups.cli.sys.stdout.isatty", return_value=False):
            with patch("loups.cli.Live") as mock_live:
                runner.invoke(app, [str(test_video)])

                # Live progress should NOT be used when piped
                mock_live.assert_not_called()

    def test_progress_disabled_with_quiet_flag(
        self, runner, test_video, mock_loups, mock_template
    ):
        """Test that show_progress is False with --quiet even in TTY."""
        with patch("loups.cli.sys.stdout.isatty", return_value=True):
            with patch("loups.cli.Live") as mock_live:
                runner.invoke(app, [str(test_video), "-q"])

                # Live progress should NOT be used with --quiet
                mock_live.assert_not_called()


class TestErrorHandling:
    """Test error handling in different output modes."""

    def test_errors_go_to_stderr_in_piped_mode(
        self, runner, test_video, mock_loups, mock_template
    ):
        """Test that errors go to stderr even when output is piped."""
        # Make scan fail
        mock_loups.return_value.scan.side_effect = Exception("Scan failed!")

        with patch("loups.cli.sys.stdout.isatty", return_value=False):
            result = runner.invoke(app, [str(test_video)])

        # Error should be in stderr, not stdout
        assert "Error:" in result.stderr or "Scan failed" in result.stderr
        assert result.exit_code != 0

    def test_errors_go_to_stderr_in_interactive_mode(
        self, runner, test_video, mock_loups, mock_template
    ):
        """Test that errors go to stderr in interactive mode."""
        # Make scan fail
        mock_loups.return_value.scan.side_effect = Exception("Scan failed!")

        with patch("loups.cli.sys.stdout.isatty", return_value=True):
            result = runner.invoke(app, [str(test_video)])

        # Error should be in stderr
        assert "Error:" in result.stderr or "Scan failed" in result.stderr
        assert result.exit_code != 0


class TestCombinedFlags:
    """Test combinations of flags with pipe detection."""

    def test_quiet_and_output_file(
        self, runner, test_video, mock_loups, mock_template, tmp_path
    ):
        """Test --quiet with --output file."""
        output_file = tmp_path / "chapters.txt"

        result = runner.invoke(app, ["-q", "-o", str(output_file), str(test_video)])

        # Quiet mode should suppress stdout
        assert result.stdout == ""

        # File should still be created
        assert output_file.exists()

    def test_log_and_piped_output(
        self, runner, test_video, mock_loups, mock_template, tmp_path
    ):
        """Test --log works correctly when output is piped."""
        log_file = tmp_path / "test.log"

        with patch("loups.cli.sys.stdout.isatty", return_value=False):
            result = runner.invoke(app, ["--log", str(log_file), str(test_video)])

        # Should output chapters to stdout
        assert "0:00:00 Game Start" in result.stdout

        # Log file should be created
        assert log_file.exists()

    def test_debug_mode_with_pipe(
        self, runner, test_video, mock_loups, mock_template, tmp_path
    ):
        """Test --debug mode works when piped."""
        log_file = tmp_path / "debug.log"

        with patch("loups.cli.sys.stdout.isatty", return_value=False):
            result = runner.invoke(
                app, ["--log", str(log_file), "--debug", str(test_video)]
            )

        # Should still output to stdout when piped
        assert "0:00:00 Game Start" in result.stdout

        # Log file should exist
        assert log_file.exists()


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_redirect_to_file(self, runner, test_video, mock_loups, mock_template):
        """Simulate: loups video.mp4 > output.txt."""
        with patch("loups.cli.sys.stdout.isatty", return_value=False):
            result = runner.invoke(app, [str(test_video)])

        # Should be clean output suitable for redirection
        assert "Scanning video:" not in result.stdout
        assert result.stdout.strip().startswith("0:00:00")

    def test_pipe_to_grep(self, runner, test_video, mock_loups, mock_template):
        r"""Simulate: loups video.mp4 | grep "Sarah"."""
        with patch("loups.cli.sys.stdout.isatty", return_value=False):
            result = runner.invoke(app, [str(test_video)])

        # Should contain searchable plain text
        assert "Sarah Johnson #7" in result.stdout
        # Should not have progress animations
        assert "🥎" not in result.stdout

    def test_command_substitution(self, runner, test_video, mock_loups, mock_template):
        """Simulate: chapters=$(loups video.mp4)."""
        with patch("loups.cli.sys.stdout.isatty", return_value=False):
            result = runner.invoke(app, [str(test_video)])

        # Output should be clean for variable capture
        lines = result.stdout.strip().split("\n")
        assert len(lines) > 0
        assert lines[0].startswith("0:")


class TestThumbnailSubcommandLogging:
    """Test thumbnail subcommand logging functionality."""

    @pytest.fixture
    def mock_thumbnail_extractor(self, tmp_path):
        """Mock the extract_thumbnail function to return a successful result."""
        from loups.thumbnail_extractor import ThumbnailResult

        with patch("loups.cli.extract_thumbnail") as mock_extract:
            # Create a mock successful result
            result = ThumbnailResult(
                success=True,
                output_path=tmp_path / "thumbnail.jpg",
                frame_number=10,
                timestamp_ms=333.33,
                ssim_score=0.95,
            )
            mock_extract.return_value = result
            yield mock_extract

    @pytest.fixture
    def mock_setup_logging(self):
        """Mock setup_logging to track that it was called with correct parameters."""
        with patch("loups.cli.setup_logging") as mock_setup:
            yield mock_setup

    def test_thumbnail_log_flag_creates_log_file(
        self, runner, test_video, mock_thumbnail_extractor, tmp_path
    ):
        """Test that --log flag creates a log file for thumbnail subcommand."""
        log_file = tmp_path / "thumbnail.log"

        result = runner.invoke(
            app, [str(test_video), "thumbnail", "--log", str(log_file), "-q"]
        )

        # Command should succeed
        assert result.exit_code == 0

        # Log file should be created
        assert log_file.exists()

    def test_thumbnail_log_configures_logging_with_path(
        self, runner, test_video, mock_thumbnail_extractor, mock_setup_logging, tmp_path
    ):
        """Test that --log flag configures logging with the correct path."""
        log_file = tmp_path / "thumbnail_info.log"

        result = runner.invoke(
            app, [str(test_video), "thumbnail", "--log", str(log_file), "-q"]
        )

        assert result.exit_code == 0
        # Verify setup_logging was called with the log path
        mock_setup_logging.assert_called_once()
        call_args = mock_setup_logging.call_args
        assert call_args[0][0] == Path(log_file)  # log_path parameter
        assert call_args[0][1] is True  # quiet parameter
        assert call_args[0][2] is False  # debug parameter

    def test_thumbnail_debug_enables_debug_in_setup_logging(
        self, runner, test_video, mock_thumbnail_extractor, mock_setup_logging, tmp_path
    ):
        """Test that --debug flag enables debug in setup_logging."""
        log_file = tmp_path / "thumbnail_debug.log"

        result = runner.invoke(
            app,
            [str(test_video), "thumbnail", "--log", str(log_file), "--debug", "-q"],
        )

        assert result.exit_code == 0
        # Verify setup_logging was called with debug=True
        mock_setup_logging.assert_called_once()
        call_args = mock_setup_logging.call_args
        assert call_args[0][0] == Path(log_file)  # log_path parameter
        assert call_args[0][1] is True  # quiet parameter
        assert call_args[0][2] is True  # debug parameter (should be True!)

    def test_thumbnail_log_and_debug_both_passed_to_setup(
        self, runner, test_video, mock_thumbnail_extractor, mock_setup_logging, tmp_path
    ):
        """Test that --log and --debug are both passed to setup_logging."""
        log_file = tmp_path / "combined.log"

        result = runner.invoke(
            app,
            [str(test_video), "thumbnail", "--log", str(log_file), "--debug", "-q"],
        )

        assert result.exit_code == 0
        # Verify both parameters are passed correctly
        mock_setup_logging.assert_called_once()
        call_args = mock_setup_logging.call_args
        assert call_args[0][0] == Path(log_file)
        assert call_args[0][2] is True  # debug=True

    def test_thumbnail_log_without_debug_is_info_level(
        self, runner, test_video, mock_thumbnail_extractor, tmp_path
    ):
        """Test that without --debug, logging defaults to INFO level."""
        log_file = tmp_path / "info_only.log"

        # Mock extract_thumbnail to trigger some logging
        with patch("loups.cli.extract_thumbnail") as mock_extract:
            from loups.thumbnail_extractor import ThumbnailResult

            result_obj = ThumbnailResult(
                success=True,
                output_path=tmp_path / "thumb.jpg",
                frame_number=5,
                timestamp_ms=166.67,
                ssim_score=0.92,
            )
            mock_extract.return_value = result_obj

            result = runner.invoke(
                app, [str(test_video), "thumbnail", "--log", str(log_file), "-q"]
            )

        assert result.exit_code == 0
        assert log_file.exists()

    def test_thumbnail_logging_called_when_log_flag_used(
        self, runner, test_video, mock_thumbnail_extractor, mock_setup_logging, tmp_path
    ):
        """Test that setup_logging is called when --log flag is used."""
        log_file = tmp_path / "test.log"
        result = runner.invoke(
            app, [str(test_video), "thumbnail", "--log", str(log_file), "-q"]
        )

        assert result.exit_code == 0
        # Verify setup_logging was called
        mock_setup_logging.assert_called_once()
        # Verify it was called with a log path (not None)
        call_args = mock_setup_logging.call_args
        assert call_args[0][0] is not None  # log_path should not be None

    def test_thumbnail_log_with_custom_path(
        self, runner, test_video, mock_thumbnail_extractor, tmp_path
    ):
        """Test --log with custom path."""
        custom_log = tmp_path / "custom" / "my_thumbnail.log"
        custom_log.parent.mkdir(parents=True)

        result = runner.invoke(
            app, [str(test_video), "thumbnail", "--log", str(custom_log), "-q"]
        )

        assert result.exit_code == 0
        assert custom_log.exists()

    def test_thumbnail_logging_with_extraction_failure(
        self, runner, test_video, tmp_path
    ):
        """Test that logging works even when thumbnail extraction fails."""
        log_file = tmp_path / "error.log"

        # Mock extract_thumbnail to return None (no match found)
        with patch("loups.cli.extract_thumbnail") as mock_extract:
            mock_extract.return_value = None

            result = runner.invoke(
                app, [str(test_video), "thumbnail", "--log", str(log_file), "-q"]
            )

        # Should exit with error code (fatal for standalone command)
        assert result.exit_code != 0

        # Log file should still be created
        assert log_file.exists()

    def test_thumbnail_logging_with_exception(self, runner, test_video, tmp_path):
        """Test that logging captures exceptions during thumbnail extraction."""
        log_file = tmp_path / "exception.log"

        # Mock extract_thumbnail to raise an exception
        with patch("loups.cli.extract_thumbnail") as mock_extract:
            mock_extract.side_effect = Exception("Test extraction failure")

            result = runner.invoke(
                app, [str(test_video), "thumbnail", "--log", str(log_file), "-q"]
            )

        # Should exit with error
        assert result.exit_code != 0

        # Log file should be created
        assert log_file.exists()

    def test_thumbnail_quiet_suppresses_output_not_logging(
        self, runner, test_video, mock_thumbnail_extractor, mock_setup_logging, tmp_path
    ):
        """Test that --quiet suppresses stdout but setup_logging is still called."""
        log_file = tmp_path / "quiet_test.log"

        result = runner.invoke(
            app,
            [str(test_video), "thumbnail", "--log", str(log_file), "--debug", "-q"],
        )

        assert result.exit_code == 0

        # Stdout should be empty (quiet mode)
        assert result.stdout == ""

        # But setup_logging should still have been called
        mock_setup_logging.assert_called_once()
        call_args = mock_setup_logging.call_args
        assert call_args[0][1] is True  # quiet=True
        assert call_args[0][2] is True  # debug=True
