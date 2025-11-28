# :material-code-tags: Developer Guide

Technical documentation for contributors and developers working with Loups.

---

## :compass: Developer Documentation

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### :material-sitemap: [Architecture](architecture.md)
System design and module structure
</div>

<div class="feature-card" markdown>
### :material-cogs: [How It Works](how-it-works.md)
Detailed technical implementation
</div>

<div class="feature-card" markdown>
### :material-account-group: [Contributing](contributing.md)
Contribution guidelines and workflow
</div>

</div>

---

## :rocket: Quick Start for Developers

### Development Setup

```bash
# Clone repository
git clone https://github.com/jcspeegs/loups.git
cd loups

# Using devenv (recommended)
devenv shell

# Or using uv
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e ".[dev]"

# Run tests
uv run python -m pytest

# Run linting
flake8 loups tests
black --check loups tests
```

### Project Structure

```
loups/
├── loups/                  # Main package
│   ├── __init__.py
│   ├── loups.py           # Core Loups class
│   ├── cli.py             # CLI interface
│   ├── match_template_scan.py
│   ├── thumbnail_extractor.py
│   ├── frame_utils.py
│   └── geometry.py
├── tests/                  # Test suite
├── docs/                   # Documentation
├── devenv.nix             # Development environment
├── pyproject.toml         # Project configuration
└── README.md
```

---

## :hammer_and_wrench: Development Tools

### Code Quality

Loups uses comprehensive linting and formatting:

| Tool | Purpose | Config |
|------|---------|--------|
| **black** | Code formatting | pyproject.toml |
| **flake8** | Base style checking (PEP 8) | .flake8 |
| **flake8-bugbear** | Additional bug and design problems | .flake8 |
| **flake8-docstrings** | Docstring validation (PEP 257, D401 imperative mood) | .flake8 |
| **pep8-naming** | PEP 8 naming conventions | .flake8 |
| **flake8-quotes** | Quote style consistency | .flake8 |
| **mccabe** | Cyclomatic complexity checker | .flake8 |
| **isort** | Import sorting | pyproject.toml |
| **pytest** | Testing | pytest.ini |

### Pre-commit Hooks

Pre-commit hooks ensure code quality:

```bash
# Hooks run automatically on commit
git commit -m "Your message"

# Manual run
devenv shell
pre-commit run --all-files
```

Active hooks:
- :material-check: black (formatting)
- :material-check: flake8 (linting)
- :material-check: isort (imports)
- :material-check: pytest (tests)

---

## :test_tube: Testing

### Run Tests

```bash
# All tests
uv run python -m pytest

# With coverage
uv run python -m pytest --cov=loups --cov-report=html

# Specific test file
uv run python -m pytest tests/test_loups.py

# Specific test
uv run python -m pytest tests/test_loups.py::test_function_name

# Verbose output
uv run python -m pytest -v
```

### Writing Tests

Follow existing patterns:

```python
import pytest
from loups import Loups

def test_loups_initialization():
    """Test Loups class initialization."""
    loups = Loups(
        video_path="test_video.mp4",
        template_path="test_template.png"
    )

    assert loups.video_path == "test_video.mp4"
    assert loups.template_path == "test_template.png"

def test_chapter_generation():
    """Test chapter generation from video."""
    loups = Loups("test_video.mp4", "template.png")
    chapters = loups.scan()

    assert len(chapters) > 0
    assert all(hasattr(ch, 'timestamp') for ch in chapters)
    assert all(hasattr(ch, 'title') for ch in chapters)
```

---

## :books: Documentation

### Build Documentation

```bash
# Serve locally
devenv shell
docs  # or: mkdocs serve

# Open browser
open http://127.0.0.1:8000

# Build static site
mkdocs build
```

### Docstring Style

Use **Google-style docstrings** with **imperative mood**:

```python
def process_frame(frame, template):
    """Process video frame with template matching.

    Args:
        frame: Video frame as numpy array.
        template: Template image for matching.

    Returns:
        Match confidence score (0.0 to 1.0).

    Raises:
        ValueError: If frame or template is invalid.

    Examples:
        ```python
        score = process_frame(frame, template)
        if score > 0.8:
            print("Strong match!")
        ```
    """
    # Implementation
    pass
```

!!! warning "D401 Compliance"
    Docstrings must start with imperative verb:

    - :material-check: "Process video frame" (correct)
    - :material-close: "Processes video frame" (incorrect)

---

## :material-source-branch: Git Workflow

### Branch Strategy

```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Make changes
git add .
git commit -m "Add feature description"

# Push to GitHub
git push origin feature/your-feature-name

# Open pull request on GitHub
```

### Commit Messages

Follow conventional commits:

```bash
# Format
type(scope): description

# Examples
feat(cli): add batch processing command
fix(ocr): improve text extraction accuracy
docs(api): update Loups class documentation
test(thumbnail): add SSIM threshold tests
refactor(core): simplify frame processing logic
```

---

## :link: Additional Resources

- [:material-sitemap: Architecture Overview](architecture.md) - System design
- [:material-cogs: How It Works](how-it-works.md) - Implementation details
- [:material-account-group: Contributing Guide](contributing.md) - Contribution workflow
- [:material-code-braces: API Reference](../api/index.md) - API documentation

---

## :question: Developer FAQs

??? question "How do I add a new feature?"
    1. Create issue on GitHub describing the feature
    2. Fork and create feature branch
    3. Implement with tests and docs
    4. Submit pull request
    5. See [Contributing Guide](contributing.md)

??? question "How are dependencies managed?"
    - **Runtime deps:** pyproject.toml `dependencies`
    - **Dev deps:** devenv.nix for development environment
    - **CI/CD:** GitHub Actions with Nix

??? question "What Python versions are supported?"
    **Python 3.13+** only. Uses modern Python features.

??? question "How do I debug video processing?"
    ```python
    loups = Loups(
        video_path="video.mp4",
        template_path="template.png",
        log_level="DEBUG",
        log_file="debug.log"
    )

    # Check debug.log for detailed processing info
    ```
