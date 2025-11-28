# :material-account-group: Contributing

Welcome contributors! This guide will help you get started with contributing to Loups.

---

## :heart: Ways to Contribute

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### :material-bug: Bug Reports
Found a bug? Open an issue with details and reproduction steps
</div>

<div class="feature-card" markdown>
### :material-lightbulb: Feature Requests
Have an idea? Suggest new features or improvements
</div>

<div class="feature-card" markdown>
### :material-code-tags: Code Contributions
Submit pull requests with bug fixes or new features
</div>

<div class="feature-card" markdown>
### :material-file-document: Documentation
Help improve docs, add examples, fix typos
</div>

<div class="feature-card" markdown>
### :material-palette: Templates & Examples
Share custom templates and interesting use cases
</div>

<div class="feature-card" markdown>
### :material-chat: Community Support
Help others in issues and discussions
</div>

</div>

---

## :rocket: Getting Started

### 1. Fork & Clone

```bash
# Fork on GitHub
# (Click "Fork" button on https://github.com/jcspeegs/loups)

# Clone your fork
git clone https://github.com/YOUR_USERNAME/loups.git
cd loups

# Add upstream remote
git remote add upstream https://github.com/jcspeegs/loups.git
```

### 2. Set Up Development Environment

=== ":material-snowflake: devenv (Recommended)"

    ```bash
    # Enter development shell
    devenv shell

    # Verify setup
    python --version  # Should be 3.13+
    pytest --version
    ```

=== ":material-language-python: uv"

    ```bash
    # Create virtual environment
    uv venv
    source .venv/bin/activate  # or .venv\Scripts\activate on Windows

    # Install in development mode
    uv pip install -e ".[dev]"

    # Verify
    loups --help
    pytest --version
    ```

=== ":material-package: pip"

    ```bash
    # Create virtual environment
    python -m venv .venv
    source .venv/bin/activate  # or .venv\Scripts\activate on Windows

    # Install in development mode
    pip install -e ".[dev]"
    ```

### 3. Create a Branch

```bash
# Update main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-description
```

---

## :hammer_and_wrench: Development Workflow

### Making Changes

1. **Write Code**
   ```python
   # Follow existing code style
   # Add type hints
   # Write docstrings (Google style)
   ```

2. **Run Tests**
   ```bash
   # Run all tests
   uv run python -m pytest

   # Run specific test
   uv run python -m pytest tests/test_loups.py::test_scan

   # With coverage
   uv run python -m pytest --cov=loups
   ```

3. **Run Linters**
   ```bash
   # Format code
   black loups tests

   # Check style
   flake8 loups tests

   # Sort imports
   isort loups tests

   # Or run all pre-commit hooks
   git add .
   git commit -m "Your message"  # Hooks run automatically
   ```

4. **Test Manually**
   ```bash
   # Test CLI
   loups test_video.mp4

   # Test your changes
   python -c "from loups import Loups; ..."
   ```

---

## :memo: Coding Standards

### Python Style

Follow PEP 8 and project conventions:

```python
# Good example
def process_video_frame(
    frame: np.ndarray,
    template: np.ndarray,
    threshold: float = 0.8
) -> Optional[MatchResult]:
    """Process video frame with template matching.

    Args:
        frame: Video frame as numpy array.
        template: Template image for matching.
        threshold: Minimum confidence threshold (0.0-1.0).

    Returns:
        MatchResult object if match found, None otherwise.

    Raises:
        ValueError: If threshold is not in valid range.

    Examples:
        ```python
        result = process_video_frame(frame, template, 0.9)
        if result:
            print(f"Match found with {result.confidence:.2f} confidence")
        ```
    """
    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"Threshold must be 0.0-1.0, got {threshold}")

    # Implementation
    match = match_template(frame, template)

    if match.confidence >= threshold:
        return match

    return None
```

### Docstring Requirements

!!! warning "D401: Imperative Mood Required"
    All docstrings must start with imperative verb:

    === ":material-check-circle: Correct"
        ```python
        def calculate_score():
            """Calculate similarity score."""
            pass
        ```

    === ":material-close-circle: Incorrect"
        ```python
        def calculate_score():
            """Calculates similarity score."""  # ❌ Present tense
            pass

        def calculate_score():
            """This function calculates..."""  # ❌ Not imperative
            pass
        ```

### Type Hints

Always use type hints:

```python
from typing import List, Optional, Tuple
import numpy as np

def extract_frames(
    video_path: str,
    start_frame: int = 0,
    end_frame: Optional[int] = None
) -> List[np.ndarray]:
    """Extract frames from video."""
    pass
```

### Example Names in Docstrings

Use **full names** for batter examples (project requirement):

```python
# ✅ Good
"""
Examples:
    ```python
    chapter = Chapter("0:05:23", "Sarah Johnson #7")
    ```
"""

# ❌ Bad
"""
Examples:
    ```python
    chapter = Chapter("0:05:23", "Sarah #7")  # Missing last name
    ```
"""
```

---

## :test_tube: Testing Guidelines

### Writing Tests

```python
import pytest
from loups import Loups

class TestLoups:
    """Test suite for Loups class."""

    def test_initialization(self):
        """Test Loups initialization with valid parameters."""
        loups = Loups(
            video_path="test.mp4",
            template_path="template.png"
        )

        assert loups.video_path == "test.mp4"
        assert loups.template_path == "template.png"

    def test_initialization_invalid_video(self):
        """Test Loups initialization with invalid video path."""
        with pytest.raises(FileNotFoundError):
            Loups(
                video_path="nonexistent.mp4",
                template_path="template.png"
            )

    @pytest.mark.parametrize("threshold", [0.5, 0.8, 0.95])
    def test_different_thresholds(self, threshold):
        """Test scanning with different confidence thresholds."""
        loups = Loups("test.mp4", "template.png", threshold=threshold)
        chapters = loups.scan()
        assert isinstance(chapters, list)
```

### Test Fixtures

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def test_video_path():
    """Provide path to test video."""
    return Path(__file__).parent / "fixtures" / "test_video.mp4"

@pytest.fixture
def test_template_path():
    """Provide path to test template."""
    return Path(__file__).parent / "fixtures" / "test_template.png"

# Usage in tests
def test_with_fixtures(test_video_path, test_template_path):
    """Test using fixtures."""
    loups = Loups(
        video_path=str(test_video_path),
        template_path=str(test_template_path)
    )
    assert loups is not None
```

### Running Tests

```bash
# All tests
uv run python -m pytest

# Verbose
uv run python -m pytest -v

# Specific test file
uv run python -m pytest tests/test_loups.py

# Specific test function
uv run python -m pytest tests/test_loups.py::test_initialization

# With coverage report
uv run python -m pytest --cov=loups --cov-report=html

# Open coverage report
open htmlcov/index.html
```

---

## :material-git: Git Commit Guidelines

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

### Types

| Type | Usage |
|------|-------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `style` | Code style (formatting, no logic change) |
| `refactor` | Code restructuring (no feature/fix) |
| `test` | Adding/updating tests |
| `chore` | Build process, dependencies |
| `perf` | Performance improvements |

### Examples

```bash
# Feature
git commit -m "feat(cli): add batch processing command"

# Bug fix
git commit -m "fix(ocr): improve text extraction for low contrast frames"

# Documentation
git commit -m "docs(api): add examples for Loups class usage"

# Refactoring
git commit -m "refactor(core): simplify frame processing pipeline"

# Test
git commit -m "test(thumbnail): add SSIM threshold edge cases"

# With body
git commit -m "feat(cli): add progress bar for batch processing

Implement rich progress bar that shows:
- Current video being processed
- Overall progress across all videos
- Estimated time remaining

Closes #123"
```

---

## :material-pull-request: Pull Request Process

### 1. Prepare Your PR

```bash
# Make sure tests pass
uv run python -m pytest

# Make sure linting passes
black --check loups tests
flake8 loups tests
isort --check loups tests

# Update your branch
git checkout main
git pull upstream main
git checkout your-feature-branch
git rebase main

# Push to your fork
git push origin your-feature-branch
```

### 2. Create Pull Request

1. Go to https://github.com/jcspeegs/loups
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill in the PR template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Tests pass locally
- [ ] Added new tests for changes
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style
- [ ] Docstrings added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### 3. Code Review

- Address reviewer feedback
- Push updates to same branch
- PR will update automatically

```bash
# Make requested changes
# ...

# Commit and push
git add .
git commit -m "fix: address review comments"
git push origin your-feature-branch
```

### 4. Merge

Once approved:
- Maintainer will merge your PR
- Delete your branch
- Celebrate! :tada:

---

## :books: Documentation

### Building Docs Locally

```bash
# Serve documentation
devenv shell
docs  # or: mkdocs serve

# Open in browser
open http://127.0.0.1:8000

# Build static site
mkdocs build

# Output in site/ directory
```

### Documentation Style

- Use clear, concise language
- Include code examples
- Add diagrams where helpful
- Use admonitions for important notes

```markdown
!!! tip "Pro Tip"
    Use `--quiet` flag for batch processing scripts!

!!! warning "Important"
    Options must come BEFORE the video path.

!!! info "Note"
    First run downloads OCR models (~100MB).
```

---

## :material-checkbox-marked-circle: Checklist for Contributors

Before submitting PR:

- [ ] Code follows PEP 8 and project style
- [ ] Type hints added to functions
- [ ] Docstrings added (Google style, imperative mood)
- [ ] Full names in batter examples
- [ ] Tests written and passing
- [ ] Linting passes (black, flake8, isort)
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] PR description filled out
- [ ] No breaking changes (or documented)

---

## :question: Questions?

Need help?

- :material-github: [Open an issue](https://github.com/jcspeegs/loups/issues)
- :material-email: [Email maintainer](mailto:justin@speegs.com)
- :material-comment: Comment on existing issues/PRs

---

## :trophy: Recognition

Contributors are recognized in:

- GitHub contributors page
- Release notes
- Special thanks in documentation

Thank you for contributing to Loups! :heart:

---

## :link: Additional Resources

- [:material-sitemap: Architecture](architecture.md) - System design
- [:material-cogs: How It Works](how-it-works.md) - Technical details
- [:material-code-braces: API Reference](../api/index.md) - Code documentation
- [:material-github: GitHub Repository](https://github.com/jcspeegs/loups)
