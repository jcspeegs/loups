# :material-package-variant: Loups Class

Main class for video chapter generation using template matching and OCR.

---

## :book: Class Documentation

::: loups.loups.Loups
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3
      members_order: source
      show_signature_annotations: true
      separate_signature: true

---

## :zap: Usage Examples

### Basic Usage

```python
from loups import Loups

# Initialize with video and template
loups = Loups(
    video_path="game_video.mp4",
    template_path="scoreboard_template.png"
)

# Scan for chapters
chapters = loups.scan()

# Print results
for chapter in chapters:
    print(f"{chapter.timestamp} {chapter.title}")
```

### With Custom Options

```python
from loups import Loups

loups = Loups(
    video_path="video.mp4",
    template_path="template.png",
    threshold=0.85,              # Stricter template matching
    ocr_confidence=0.7,          # Higher OCR confidence required
    log_level="DEBUG",           # Enable debug logging
    log_file="processing.log"   # Custom log file
)

chapters = loups.scan()
```

### Save to File

```python
from loups import Loups

loups = Loups("video.mp4", "template.png")
chapters = loups.scan()

# Save in YouTube format
with open("chapters.txt", "w") as f:
    for ch in chapters:
        f.write(f"{ch.timestamp} {ch.title}\n")
```

---

## :material-class: MilliSecond Helper Class

::: loups.loups.MilliSecond
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3
      members_order: source

---

### MilliSecond Examples

```python
from loups.loups import MilliSecond

# Create from milliseconds
ms = MilliSecond(65000)  # 65 seconds

# YouTube format
print(ms.yt_format())  # "01:05"

# With hours
ms_long = MilliSecond(3665000)  # 1 hour, 1 minute, 5 seconds
print(ms_long.yt_format())  # "01:01:05"

# Arithmetic
ms1 = MilliSecond(30000)
ms2 = MilliSecond(15000)
total = ms1 + ms2  # 45000 milliseconds
```

---

## :material-database: Internal Data Structures

### Chapter Object

Each chapter returned from `scan()` typically contains:

```python
class Chapter:
    timestamp: str      # YouTube format "HH:MM:SS" or "MM:SS"
    title: str          # Extracted text from frame
    frame_number: int   # Video frame number
    milliseconds: int   # Timestamp in milliseconds
```

### Match Results

Template matching results are stored internally:

```python
loups = Loups("video.mp4", "template.png")
loups.scan()

# Access matches
for frame_num, match in loups.matches.items():
    print(f"Frame {frame_num}:")
    print(f"  Confidence: {match.confidence}")
    print(f"  Location: {match.location}")
```

---

## :material-alert-circle: Error Handling

```python
from loups import Loups
from pathlib import Path

try:
    # Check video exists
    video_path = Path("video.mp4")
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    # Initialize Loups
    loups = Loups(
        video_path=str(video_path),
        template_path="template.png"
    )

    # Scan
    chapters = loups.scan()

    if not chapters:
        print("⚠️ No chapters found!")
    else:
        print(f"✅ Found {len(chapters)} chapters")

except FileNotFoundError as e:
    print(f"❌ Error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
```

---

## :material-speedometer: Performance Tips

### Frame Sampling

Control how many frames are checked:

```python
loups = Loups(
    video_path="video.mp4",
    template_path="template.png",
    frame_skip=5  # Check every 5th frame (faster, less accurate)
)
```

### Template Size

Smaller templates = faster matching:

- Keep templates focused on the region of interest
- Avoid including large static areas
- Typical size: 200-800 pixels wide

### Video Resolution

Lower resolution = faster processing:

```bash
# Pre-process video to lower resolution
ffmpeg -i input.mp4 -vf scale=1280:-1 output.mp4
```

---

## :link: Related

- [:material-console-line: CLI Module](cli.md) - Command-line interface
- [:material-image-frame: Thumbnail Extraction](thumbnail.md) - Thumbnail API
- [:material-cogs: How It Works](../developer/how-it-works.md) - Implementation details
