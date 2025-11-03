# ⚾ Loups

> **Automated video chapter generation using template matching and OCR**

Automatically scan any video with on-screen text overlays to extract information and generate timestamped YouTube chapters! 🎥✨

Originally designed for Lights Out HB fastpitch softball games, but works with any video content that has consistent identifying frames or text overlays.

[![PyPI - Coming Soon](https://img.shields.io/badge/PyPI-coming%20soon-blue)](https://pypi.org/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## ✨ What is Loups?

Loups uses template matching and OCR to automatically scan videos, detect specific frames with identifying information, and generate timestamped chapters.

**Use cases include:**
- 🥎 **Sports Games** - Track player at-bats, shifts, or appearances (originally designed for fastpitch softball)
- 🎓 **Educational Content** - Chapter markers for different topics or speakers
- 🎙️ **Podcasts/Interviews** - Detect guest name overlays or topic cards
- 🎮 **Gaming** - Mark level changes, character selections, or game modes
- 📺 **TV Shows/Series** - Detect episode titles or scene markers
- 🎬 **Any Video** - With consistent text overlays or identifying frames

## 📦 Installation

**Coming soon to PyPI!** For now, install from source:

```bash
pip install loups
```

## 🚀 Quick Start

```bash
# 🎬 For Lights Out HB games (uses bundled template)
loups game_video.mp4

# 🎨 For any other video (use your own template)
loups video.mp4 -t my_template.png

# 💾 Save results to a file for YouTube chapters
loups video.mp4 -o chapters.txt

# 🤫 Quiet mode for automation/batch processing
loups video.mp4 -q -o chapters.txt
```

## 📋 Common Workflows

### 📹 Creating YouTube Chapters
```bash
# Scan video and save chapters for YouTube description
loups my_video.mp4 -o youtube_chapters.txt
# Copy the contents of youtube_chapters.txt to your video description!
```

### 🎨 Using Custom Templates
```bash
# Step 1: Create a template from a clear frame
# (Screenshot the text/overlay you want to detect)

# Step 2: Use your template
loups video.mp4 -t my_custom_template.png -o chapters.txt
```

### 🔧 Troubleshooting with Logs
```bash
# Enable logging to debug detection issues
loups video.mp4 --log

# Use custom log location with debug level
loups video.mp4 --log /path/to/debug.log --debug
```

### 🤖 Automation & Batch Processing
```bash
# Process multiple videos quietly
loups video1.mp4 -q -o video1_chapters.txt
loups video2.mp4 -q -o video2_chapters.txt
loups video3.mp4 -q -o video3_chapters.txt
```

## ⚙️ CLI Options

### Required Arguments

| Argument | Description |
|----------|-------------|
| `VIDEO` | 🎥 Path to the video file to scan |

### Optional Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--template PATH` | `-t` | 🎨 Path to template image for detection<br>• Defaults to bundled Lights Out HB template<br>• Provide your own for any video content |
| `--output PATH` | `-o` | 💾 Save results to file in YouTube chapter format |
| `--log [PATH]` | `-l` | 📝 Enable logging (defaults to `loups.log`, or specify custom path)<br>• Rotates at 10MB<br>• Keeps 3 backup files |
| `--quiet` | `-q` | 🤫 Suppress progress display (errors still shown) |
| `--debug` | `-d` | 🔍 Enable DEBUG level logging (requires `--log`) |

## ⭐ Features

### 🎯 Core Features
- 🥎 **Animated Progress Display** - Real-time scanning with fun animations
- 🔍 **Template Matching** - Detects specific frames using image templates
- 📝 **OCR Text Extraction** - Reads text from matched frames to create chapter titles
- 📺 **YouTube-Ready Output** - Generates properly formatted chapter timestamps
- 🎨 **Universal Custom Templates** - Works with ANY video content
- 🏆 **Bundled Template** - Ready to use with Lights Out HB fastpitch games

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
4. **Use it** - `loups video.mp4 -t my_template.png`

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
- **Missed detections?** Enable `--log --debug` to see template matches and OCR results
- **Wrong text extracted?** Your template might be too large or including unwanted regions
- **False positives?** Consider cropping your template more tightly around the identifying region
- **Template not matching?** Ensure the template exactly matches the video frames
- **Names in wrong order?** OCR results are automatically sorted left-to-right
- **Blank chapter titles?** OCR confidence might be too low - check logs with `--debug`

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
