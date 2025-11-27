# :material-book-open-variant: User Guide

Welcome to the Loups user guide! This section covers everything you need to know to use Loups effectively.

## :compass: Navigation

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### :material-download: [Installation](installation.md)
Get Loups installed on your system with Python 3.13+
</div>

<div class="feature-card" markdown>
### :material-rocket-launch: [Quick Start](quick-start.md)
Start scanning videos and generating chapters in minutes
</div>

<div class="feature-card" markdown>
### :material-console: [CLI Reference](cli-reference.md)
Complete command-line interface documentation
</div>

<div class="feature-card" markdown>
### :material-palette: [Custom Templates](custom-templates.md)
Create templates for any video content
</div>

</div>

---

## :zap: Quick Example

```bash
# Install
pip install loups

# Scan a video
loups game_video.mp4

# Save chapters to file
loups -o chapters.txt video.mp4

# Use custom template
loups -t my_template.png video.mp4
```

---

## :bulb: Common Workflows

### :movie_camera: Creating YouTube Chapters

1. Install Loups
2. Create or use existing template
3. Scan your video: `loups -o chapters.txt video.mp4`
4. Copy `chapters.txt` content to YouTube description

### :frame_with_picture: Extracting Thumbnails

1. Use thumbnail subcommand: `loups video.mp4 thumbnail`
2. Or extract during scanning: `loups --extract-thumbnail video.mp4`
3. Upload thumbnail to YouTube

### :gear: Batch Processing

Use quiet mode for automation:

```bash
for video in *.mp4; do
  loups -q -o "${video%.mp4}_chapters.txt" "$video"
done
```

---

## :question: Need Help?

- :material-bug: [Report issues on GitHub](https://github.com/jcspeegs/loups/issues)
- :material-email: [Contact the author](mailto:justin@speegs.com)
- :material-book: [Read the full documentation](../index.md)
