# :material-code-braces: API Reference

Complete API documentation for using Loups programmatically in your Python projects.

---

## :books: Module Overview

Loups provides a clean Python API for video chapter generation and thumbnail extraction.

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### :material-package-variant: [Loups Class](loups.md)
Main class for video processing and chapter generation
</div>

<div class="feature-card" markdown>
### :material-console-line: [CLI Module](cli.md)
Command-line interface implementation using Typer
</div>

<div class="feature-card" markdown>
### :material-image-frame: [Thumbnail Extraction](thumbnail.md)
SSIM-based thumbnail matching and extraction
</div>

</div>

---

## :zap: Quick API Example

```python
from loups import Loups

# Create Loups instance
loups = Loups(
    video_path="game_video.mp4",
    template_path="template.png"
)

# Scan for chapters
chapters = loups.scan()

# Print results
for chapter in chapters:
    print(f"{chapter.timestamp} {chapter.title}")
```

---

## :package: Installation

```bash
pip install loups
```

Then import in your Python code:

```python
from loups import Loups
from loups.cli import app
from loups.thumbnail_extractor import extract_thumbnail
```

---

## :link: Module Links

| Module | Description | Link |
|--------|-------------|------|
| `loups.loups` | Main Loups class | [Documentation](loups.md) |
| `loups.cli` | CLI application | [Documentation](cli.md) |
| `loups.thumbnail_extractor` | Thumbnail extraction | [Documentation](thumbnail.md) |
| `loups.match_template_scan` | Template matching | API docs |
| `loups.frame_utils` | Frame utilities | API docs |
| `loups.geometry` | Geometry helpers | API docs |

---

## :bulb: Common Use Cases

### Batch Processing

```python
from pathlib import Path
from loups import Loups

videos = Path("videos").glob("*.mp4")

for video in videos:
    loups = Loups(
        video_path=str(video),
        template_path="template.png"
    )

    chapters = loups.scan()

    # Save chapters
    output = video.with_suffix(".txt")
    output.write_text("\n".join([
        f"{ch.timestamp} {ch.title}"
        for ch in chapters
    ]))
```

### Custom Processing

```python
from loups import Loups

loups = Loups(
    video_path="video.mp4",
    template_path="template.png",
    threshold=0.8,  # Stricter matching
    log_level="DEBUG"
)

# Access internal data
for frame_num, match in loups.matches.items():
    print(f"Frame {frame_num}: {match.confidence}")
```

### Integration with Other Tools

```python
from loups import Loups
import json

loups = Loups("video.mp4", "template.png")
chapters = loups.scan()

# Export as JSON
chapters_json = json.dumps([
    {
        "timestamp": ch.timestamp,
        "title": ch.title,
        "frame_number": ch.frame_number
    }
    for ch in chapters
], indent=2)

print(chapters_json)
```

---

## :question: API Questions

??? question "Can I use Loups without the CLI?"
    **Yes!** The Python API is fully featured:

    ```python
    from loups import Loups

    loups = Loups("video.mp4", "template.png")
    chapters = loups.scan()
    ```

??? question "How do I access raw OCR results?"
    Access the internal OCR data:

    ```python
    loups = Loups("video.mp4", "template.png")
    loups.scan()

    # Access OCR results for each match
    for frame_num, ocr_result in loups.ocr_results.items():
        print(f"Frame {frame_num}: {ocr_result}")
    ```

??? question "Can I customize the OCR engine?"
    Currently Loups uses EasyOCR. You can configure:

    ```python
    loups = Loups(
        video_path="video.mp4",
        template_path="template.png",
        ocr_languages=['en'],  # Languages
        ocr_confidence=0.6     # Confidence threshold
    )
    ```

---

## :link: Related Documentation

- [:material-rocket-launch: Quick Start](../user-guide/quick-start.md) - Get started with Loups
- [:material-console: CLI Reference](../user-guide/cli-reference.md) - Command-line usage
- [:material-cogs: How It Works](../developer/how-it-works.md) - Technical details
