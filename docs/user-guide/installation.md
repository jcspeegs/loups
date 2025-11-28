# :material-download: Installation

Get Loups installed and running on your system.

---

## :computer: System Requirements

!!! info "Python Version Required"
    **Python 3.13 or higher** is required.

    Loups uses modern Python features and requires Python 3.13+.

### :material-check-circle: Supported Platforms

| Platform | Status | Tested |
|----------|--------|--------|
| :material-linux: **Linux** | :material-check-circle:{ .icon-glow } Fully Supported | :material-check: CI/CD |
| :material-apple: **macOS** | :material-check-circle:{ .icon-glow } Fully Supported | :material-check: CI/CD |
| :material-microsoft-windows: **Windows** | :material-check-circle:{ .icon-glow } Fully Supported | :material-check: CI/CD |

---

## :rocket: Installation Methods

=== ":material-package-variant: pip (Recommended)"

    The easiest way to install Loups is via pip:

    ```bash
    pip install loups
    ```

    Verify installation:

    ```bash
    loups --help
    ```

=== ":material-language-python: uv"

    Using the modern uv package manager:

    ```bash
    uv pip install loups
    ```

    Or run directly without installing:

    ```bash
    uvx loups --help
    ```

=== ":material-cube-outline: pipx (Isolated)"

    For isolated installation:

    ```bash
    pipx install loups
    ```

    This installs Loups in its own virtual environment.

---

## :wrench: Verify Installation

After installation, verify everything is working:

```bash
# Check Loups version
loups --version

# View help
loups --help

# Test with a video (if you have one)
loups test_video.mp4
```

!!! success "Installation Successful!"
    If you see the help message, you're all set! :tada:

---

## :mag: Python Version Check

Not sure what Python version you have?

```bash
# Check your Python version
python --version

# Or try python3
python3 --version
```

### :arrow_up: Upgrading Python

If you need to upgrade to Python 3.13+:

=== ":material-linux: Linux"

    ```bash
    # Ubuntu/Debian
    sudo apt update
    sudo apt install python3.13

    # Fedora
    sudo dnf install python3.13

    # Arch
    sudo pacman -S python
    ```

=== ":material-apple: macOS"

    ```bash
    # Using Homebrew
    brew install python@3.13

    # Or download from python.org
    open https://www.python.org/downloads/
    ```

=== ":material-microsoft-windows: Windows"

    Download the latest Python from [python.org](https://www.python.org/downloads/)

    Make sure to check "Add Python to PATH" during installation!

---

## :warning: Troubleshooting

### ModuleNotFoundError

!!! danger "Error: ModuleNotFoundError"
    **Symptom:** `ModuleNotFoundError` or `SyntaxError` during installation

    **Solution:** You're likely using Python < 3.13. Upgrade Python first.

    ```bash
    # Check version
    python --version

    # Use specific Python version
    python3.13 -m pip install loups
    ```

### First Run is Slow

!!! info "First Execution Takes Time"
    **Behavior:** First run takes several minutes to start

    **Why:** EasyOCR automatically downloads OCR models (~100MB) on first use

    **Solution:** This is normal! Be patient during initial setup. Subsequent runs will be much faster.

    The models are cached locally, so you only download once.

### Video Codec Issues

!!! warning "Video Won't Open"
    **Error:** `cv2.error` or video file won't open

    **Solution:** Some video formats require additional codecs. Try converting to MP4 (H.264):

    ```bash
    # Using ffmpeg
    ffmpeg -i input_video.mov -c:v libx264 -c:a aac output_video.mp4
    ```

---

## :arrow_forward: Next Steps

Now that you have Loups installed, check out:

- [:material-rocket-launch: Quick Start Guide](quick-start.md) - Start using Loups
- [:material-console: CLI Reference](cli-reference.md) - All command options
- [:material-palette: Custom Templates](custom-templates.md) - Create your own templates

---

## :package: Dependencies

Loups automatically installs these dependencies:

- **easyocr** - OCR text extraction
- **opencv-python-headless** - Video processing
- **typer** - CLI framework
- **rich** - Beautiful terminal output
- **scikit-image** - SSIM thumbnail matching

No manual dependency installation needed! :sparkles:
