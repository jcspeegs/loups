# ⚾ Loups

> **Automated video chapter generation using template matching and OCR**

Automatically scan any video with on-screen text overlays to extract information and generate timestamped YouTube chapters! 🎥✨

Originally designed for Lights Out HB fastpitch softball games, but works with any video content that has consistent identifying frames or text overlays.

[![PyPI version](https://img.shields.io/pypi/v/loups.svg)](https://pypi.org/project/loups/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Actions](https://github.com/jcspeegs/loups/actions/workflows/test.yaml/badge.svg)](https://github.com/jcspeegs/loups/actions/workflows/test.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/loups.svg)](https://pypi.org/project/loups/)

**Links:** [Repository](https://github.com/jcspeegs/loups) • [Issues](https://github.com/jcspeegs/loups/issues) • [PyPI](https://pypi.org/project/loups/) • [Author](mailto:justin@speegs.com)

## ✨ What is Loups?

Loups uses template matching and OCR to automatically scan videos, detect specific frames with identifying information, and generate timestamped chapters.

**Use cases include:**
- 🥎 **Sports Games** - Track player at-bats, shifts, or appearances (originally designed for fastpitch softball)
- 🎓 **Educational Content** - Chapter markers for different topics or speakers
- 🎙️ **Podcasts/Interviews** - Detect guest name overlays or topic cards
- 🎮 **Gaming** - Mark level changes, character selections, or game modes
- 📺 **TV Shows/Series** - Detect episode titles or scene markers
- 🎬 **Any Video** - With consistent text overlays or identifying frames

## 📑 Table of Contents

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Thumbnail Extraction](#️-thumbnail-extraction)
- [Common Workflows](#-common-workflows)
- [CLI Options](#️-cli-options)
- [Features](#-features)
- [How It Works](#-how-it-works)
- [Creating Custom Templates](#-creating-custom-templates)
- [Tips & Best Practices](#-tips--best-practices)
- [Contributing](#-contributing)
- [License](#-license)

## 📦 Installation

**Requirements:** Python 3.13 or higher

**Supported Platforms:** Linux • macOS • Windows (tested via CI/CD)

```bash
# Install from PyPI
pip install loups

# Verify installation
loups --help
```

**Note:** If you're using an older Python version, you may need to upgrade:
```bash
# Check your Python version
python --version

# Install with specific Python version if needed
python3.13 -m pip install loups
```

## 🚀 Quick Start

```bash
# 🎬 For Lights Out HB games (uses bundled template)
loups game_video.mp4
```

**Expected output:**
```
🥎 Scanning video for batter at-bats...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:05:23

Found 12 batters:
0:00:00 Game Start
0:01:15 Sarah Johnson #7
0:03:42 Emma Martinez #12
0:05:23 Lily Garcia #9
...
```

**More examples:**
```bash
# 🎨 For any other video (use your own template)
loups -t my_template.png video.mp4

# 💾 Save results to a file for YouTube chapters
loups -o chapters.txt video.mp4

# 🤫 Quiet mode for automation/batch processing
loups -q -o chapters.txt video.mp4
```

**Important:** Options must be specified *before* the video argument.

## 🖼️ Thumbnail Extraction

Loups can automatically extract thumbnails from your videos using SSIM (Structural Similarity Index) matching!

```bash
# Extract thumbnail using default template
loups video.mp4 thumbnail

# Use custom thumbnail template
loups video.mp4 thumbnail --thumbnail-template my_thumb_template.png

# Customize output location
loups video.mp4 thumbnail --thumbnail-output ./thumbnails/game_thumb.jpg

# Fine-tune the matching
loups video.mp4 thumbnail --thumbnail-threshold 0.85 --thumbnail-scan-duration 180

# Extract thumbnail during chapter scanning (options BEFORE video)
loups --extract-thumbnail --thumbnail-output thumb.jpg video.mp4
```

### How Thumbnail Extraction Works

1. **🎯 Template Matching** - Scans video frames from the beginning using SSIM scoring
2. **⚡ First-Match Strategy** - Stops as soon as a frame exceeds the similarity threshold
3. **💾 Automatic Saving** - Saves the matched frame as a JPEG thumbnail
4. **⏱️ Configurable Duration** - Only scans the first N seconds (default: 120s)

**Key Features:**
- 🎯 **SSIM-based matching** - More accurate than simple template matching
- ⚡ **Efficient scanning** - Stops at first match, doesn't scan entire video
- 🎨 **Default template support** - Include `thumbnail_template.png` in package data
- 🔧 **Highly configurable** - Control threshold, scan duration, and frame sampling

**Options:**
- `--thumbnail-template` - Path to template image (uses default if not specified)
- `--thumbnail-output` - Where to save thumbnail (default: `<video>-thumbnail.jpg` in current directory)
- `--thumbnail-threshold` - Minimum SSIM score (0.0-1.0, default: 0.35)
- `--thumbnail-scan-duration` - Max seconds to scan from start (default: 120)
- `--thumbnail-frames-per-second` - Frame sampling rate (default: 3)

## 📋 Common Workflows

### 📹 Creating YouTube Chapters
```bash
# Scan video and save chapters for YouTube description
loups -o youtube_chapters.txt my_video.mp4
# Copy the contents of youtube_chapters.txt to your video description!
```

### 🎨 Using Custom Templates
```bash
# Step 1: Create a template from a clear frame
# (Screenshot the text/overlay you want to detect)

# Step 2: Use your template
loups -t my_custom_template.png -o chapters.txt video.mp4
```

### 🔧 Troubleshooting with Logs
```bash
# Enable logging to debug detection issues
loups --log video.mp4

# Use custom log location with debug level
loups --log /path/to/debug.log --debug video.mp4
```

### 🤖 Automation & Batch Processing
```bash
# Process multiple videos quietly
loups -q -o video1_chapters.txt video1.mp4
loups -q -o video2_chapters.txt video2.mp4
loups -q -o video3_chapters.txt video3.mp4
```

### 🖼️ Creating Thumbnails for YouTube
```bash
# Extract thumbnail with chapters in one command
loups -o chapters.txt --extract-thumbnail --thumbnail-output thumbnail.jpg game_video.mp4

# Or extract thumbnail separately
loups game_video.mp4 thumbnail --thumbnail-template title_screen.png

# Batch thumbnail extraction
loups video1.mp4 thumbnail --thumbnail-output vid1_thumb.jpg
loups video2.mp4 thumbnail --thumbnail-output vid2_thumb.jpg
loups video3.mp4 thumbnail --thumbnail-output vid3_thumb.jpg
```

## ⚙️ CLI Options

**Command Structure:**
- Default scanning: `loups [OPTIONS] VIDEO` - Options must come BEFORE the video path
- Thumbnail extraction: `loups VIDEO thumbnail [OPTIONS]` - Thumbnail options come AFTER the subcommand

### Main Command: `loups [OPTIONS] VIDEO`

Scan video for chapters (batter at-bats or any detected frames).

**Required Arguments:**

| Argument | Description |
|----------|-------------|
| `VIDEO` | 🎥 Path to the video file to scan (must come AFTER options) |

**Optional Flags:**

| Flag | Short | Description |
|------|-------|-------------|
| `--template PATH` | `-t` | 🎨 Path to template image for detection<br>• Defaults to bundled Lights Out HB template<br>• Provide your own for any video content |
| `--output PATH` | `-o` | 💾 Save results to file in YouTube chapter format |
| `--log [PATH]` | `-l` | 📝 Enable logging (defaults to `loups.log`, or specify custom path)<br>• Rotates at 10MB<br>• Keeps 3 backup files |
| `--quiet` | `-q` | 🤫 Suppress progress display (errors still shown) |
| `--debug` | `-d` | 🔍 Enable DEBUG level logging (requires `--log`) |
| `--extract-thumbnail` | | 🖼️ Extract thumbnail during chapter scan |
| `--thumbnail-template PATH` | | 🎨 Path to thumbnail template (optional) |
| `--thumbnail-output PATH` | | 💾 Thumbnail save location (default: `<video>-thumbnail.jpg`) |
| `--thumbnail-threshold FLOAT` | | 🎯 SSIM threshold 0.0-1.0 (default: 0.35) |
| `--thumbnail-scan-duration INT` | | ⏱️ Max seconds to scan for thumbnail (default: 120) |
| `--thumbnail-frames-per-second INT` | | 📊 Frame sampling rate (default: 3) |

### Thumbnail Command: `loups VIDEO thumbnail [OPTIONS]`

Extract thumbnail from video using SSIM-based template matching.

**Required Arguments:**

| Argument | Description |
|----------|-------------|
| `VIDEO` | 🎥 Path to the video file (comes BEFORE the `thumbnail` subcommand) |

**Optional Flags:**

| Flag | Description |
|------|-------------|
| `--thumbnail-template PATH` | 🎨 Path to thumbnail template (defaults to bundled template) |
| `--thumbnail-output PATH` | 💾 Output path (default: `<video>-thumbnail.jpg` in cwd) |
| `--thumbnail-threshold FLOAT` | 🎯 Minimum SSIM score 0.0-1.0 (default: 0.35) |
| `--thumbnail-scan-duration INT` | ⏱️ Max seconds to scan from start (default: 120) |
| `--thumbnail-frames-per-second INT` | 📊 Frame sampling rate (default: 3) |
| `--quiet` | 🤫 Suppress output |

## ⭐ Features

### 🎯 Core Features
- 🥎 **Animated Progress Display** - Real-time scanning with fun animations
- 🔍 **Template Matching** - Detects specific frames using image templates
- 📝 **OCR Text Extraction** - Reads text from matched frames to create chapter titles
- 📺 **YouTube-Ready Output** - Generates properly formatted chapter timestamps
- 🖼️ **Thumbnail Extraction** - SSIM-based automatic thumbnail extraction
- 🎨 **Universal Custom Templates** - Works with ANY video content
- 🏆 **Bundled Templates** - Ready to use with Lights Out HB fastpitch games

### 🛠️ Technical Features
- 📝 **Optional Logging** - File logging with automatic rotation (10MB, 3 backups)
- 🔧 **Debug Mode** - Detailed logs for troubleshooting
- 🤫 **Quiet Mode** - Perfect for automation and scripting
- ⚡ **Efficient Processing** - Optimized video frame analysis
- 🎯 **Smart OCR** - Confidence-based text extraction with filtering
- 🔄 **Smart Text Sorting** - Left-to-right ordering of OCR results

## 📚 How It Works

Loups processes your video in several steps to create YouTube chapters:

1. **🔍 Template Matching** - Scans video frames looking for your template image
   - The template acts as a "trigger" that identifies frames of interest
   - When a match is found, Loups knows this frame contains information to extract

2. **📝 OCR Text Extraction** - On each matched frame, OCR reads the visible text
   - Extracts all text from the matched region (names, numbers, titles, etc.)
   - Applies confidence filtering to ensure accuracy
   - Sorts text elements left-to-right for proper ordering

3. **⏱️ Chapter Title & Timestamp** - Combines the extracted text with video timestamp
   - Creates a chapter entry like: `0:05:23 John Smith #12`
   - Each detection becomes a new YouTube chapter marker

4. **💾 YouTube Format Output** - Exports chapters in YouTube-ready format
   - Copy and paste directly into your video description
   - Format: `HH:MM:SS Chapter Title`

**Example:**
```
0:00:00 Game Start
0:05:23 Sarah Johnson #7
0:08:45 Emma Martinez #12
0:12:30 Lily Garcia #9
```

## 🎨 Creating Custom Templates

Loups works with any video - just provide a template!

1. **Find a clear frame** - Pause your video where the text/overlay is visible
2. **Take a screenshot** - Capture the region you want to detect
3. **Crop the template** - Include the area where text appears
4. **Use it** - `loups -t my_template.png video.mp4`

**Tips for good templates:**
- ✅ Clear, high-contrast text
- ✅ Consistent position throughout video
- ✅ No motion blur or partial occlusion
- ✅ Crop tightly around the target region

**Example use cases:**
- 🎮 Game mode indicators or level titles
- 🎓 Speaker name overlays in lectures
- 📺 Episode titles or scene markers
- 🏆 Scoreboard player names (original use case)
- 🎵 Song title overlays in music videos
- 📰 News segment titles or chyrons

## 💡 Tips & Best Practices

### 🎯 For Best Results
- ✅ Use high-quality video recordings (720p or higher recommended)
- ✅ Ensure your template region is consistently visible throughout the video
- ✅ Steady lighting/contrast improves OCR accuracy
- ✅ Test on a short clip before processing full videos
- ✅ The text in matched frames becomes your chapter titles - ensure it's readable!

### 🔧 Troubleshooting

#### Common Issues

**Python Version Errors**
- **Error:** `ModuleNotFoundError` or `SyntaxError` during installation
- **Solution:** Loups requires Python 3.13+. Check your version with `python --version` and upgrade if needed

**First Run is Slow**
- **Behavior:** First execution takes several minutes to start
- **Why:** EasyOCR automatically downloads OCR models (~100MB) on first run
- **Solution:** This is normal! Subsequent runs will be much faster. Be patient during the initial setup.

**Detection Issues**
- **Missed detections?** Enable `--log --debug` to see template matches and OCR results
- **Wrong text extracted?** Your template might be too large or including unwanted regions
- **False positives?** Consider cropping your template more tightly around the identifying region
- **Template not matching?** Ensure the template exactly matches the video frames (size, position, quality)

**OCR Issues**
- **Names in wrong order?** OCR results are automatically sorted left-to-right
- **Blank chapter titles?** OCR confidence might be too low - check logs with `--debug`
- **Garbled text?** Improve video quality or use a clearer template region

**Video Codec Issues**
- **Error:** `cv2.error` or video won't open
- **Solution:** Some video formats require additional codecs. Try converting to MP4 (H.264) format

## 🤝 Contributing

Contributions are welcome! Whether it's:
- 🐛 Bug reports
- 💡 Feature suggestions
- 📝 Documentation improvements
- 🔧 Code contributions
- 🎨 Sharing interesting use cases and templates

Please open an issue or pull request on GitHub.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

Originally created for Lights Out HB fastpitch softball coverage, now a flexible tool for any video content creator!

---

Made with ❤️ for content creators 🎬
