# :material-rocket-launch: Quick Start

Get started with Loups in minutes!

---

## :zap: 5-Minute Quickstart

<div style="text-align: center; margin: 2rem 0;">
  <img src="../loups.gif" alt="Loups Demo" style="max-width: 100%; border-radius: 8px; box-shadow: 0 4px 20px rgba(0, 255, 255, 0.3);">
</div>

---

## :one: Basic Usage

### Lights Out HB Games

For Lights Out HB fastpitch softball games, Loups includes a bundled template:

```bash
loups game_video.mp4
```

!!! success "Expected Output"

    --8<-- "includes/snippets.md:cli-output-example"

### Any Other Video

For other videos, provide your own template:

```bash
loups -t my_template.png video.mp4
```

---

## :two: Save Results to File

Save chapters in YouTube-ready format:

```bash
loups -o chapters.txt video.mp4
```

The `chapters.txt` file will contain:

```
0:00:00 Game Start
0:01:15 Sarah Johnson #7
0:03:42 Emma Martinez #12
0:05:23 Lily Garcia #9
...
```

!!! tip "YouTube Integration"
    Copy the contents of `chapters.txt` directly into your YouTube video description!

    YouTube will automatically create clickable chapter markers.

---

## :three: Common Examples

### :movie_camera: Process with Custom Template

```bash
loups -t ~/templates/scoreboard.png -o chapters.txt game.mp4
```

### :mute: Quiet Mode (No Progress Display)

Perfect for automation and batch processing:

```bash
loups -q -o chapters.txt video.mp4
```

### :memo: Enable Logging

Debug detection issues with logging:

```bash
# Default log location (loups.log)
loups --log video.mp4

# Custom log location
loups --log /path/to/debug.log video.mp4

# Enable debug level logging
loups --log --debug video.mp4
```

---

## :four: Extract Thumbnails

### Dedicated Thumbnail Command

```bash
# Extract thumbnail with default template
loups video.mp4 thumbnail

# Use custom thumbnail template
loups video.mp4 thumbnail --thumbnail-template title_screen.png

# Specify output location
loups video.mp4 thumbnail --thumbnail-output ./thumb.jpg
```

### Extract During Chapter Scan

```bash
loups --extract-thumbnail --thumbnail-output thumb.jpg -o chapters.txt video.mp4
```

!!! info "How Thumbnail Extraction Works"
    1. :material-target: Scans video frames from beginning using SSIM
    2. :material-flash: Stops at first frame exceeding similarity threshold
    3. :material-content-save: Saves matched frame as JPEG
    4. :material-timer: Only scans first N seconds (default: 120s)

---

## :five: Important Notes

!!! warning "Option Order Matters"
    Options must come **BEFORE** the video path:

    === ":material-check-circle: Correct"
        ```bash
        loups -o chapters.txt -t template.png video.mp4
        ```

    === ":material-close-circle: Wrong"
        ```bash
        loups video.mp4 -o chapters.txt -t template.png
        ```

!!! info "Thumbnail Command Different"
    The thumbnail subcommand has different syntax:

    ```bash
    loups VIDEO thumbnail [OPTIONS]
    ```

    The `VIDEO` comes first, then `thumbnail`, then options.

---

## :clipboard: Example Workflows

### YouTube Content Creation

```bash
# Extract thumbnail
loups game.mp4 thumbnail --thumbnail-output game_thumb.jpg

# Generate chapters
loups -o game_chapters.txt game.mp4

# Upload video to YouTube
# - Use game_thumb.jpg as custom thumbnail
# - Paste game_chapters.txt content into description
```

### Batch Processing Multiple Videos

```bash
# Process all MP4 files
for video in *.mp4; do
  echo "Processing $video..."
  loups -q -o "${video%.mp4}_chapters.txt" "$video"
done
```

### Custom Template Workflow

```bash
# Step 1: Create template from video frame
# (Screenshot the text overlay you want to detect)

# Step 2: Test on short clip
loups -t my_template.png --log test_clip.mp4

# Step 3: Check logs to verify detection
cat loups.log

# Step 4: Process full video
loups -t my_template.png -o chapters.txt full_video.mp4
```

---

## :test_tube: Testing Tips

!!! tip "Test on Short Clips First"
    Before processing long videos:

    1. Create a short test clip (1-2 minutes)
    2. Verify template detection works
    3. Check OCR accuracy in logs
    4. Then process full video

    ```bash
    # Create test clip with ffmpeg
    ffmpeg -i full_video.mp4 -t 120 -c copy test_clip.mp4

    # Test with logging
    loups --log --debug -t template.png test_clip.mp4
    ```

---

## :rocket: Next Steps

- [:material-console: CLI Reference](cli-reference.md) - All command options
- [:material-palette: Custom Templates](custom-templates.md) - Create templates for your videos
- [:material-code-braces: API Reference](../api/index.md) - Use Loups programmatically

---

## :question: Common Questions

??? question "Can I use Loups with any video?"
    **Yes!** As long as your video has:

    - Consistent text overlays or identifying frames
    - Readable text that OCR can extract
    - A template image you can create

    See [Custom Templates](custom-templates.md) for details.

??? question "What video formats are supported?"
    Loups supports any format that OpenCV can read:

    - :material-check: MP4 (recommended)
    - :material-check: AVI
    - :material-check: MOV
    - :material-check: MKV
    - :material-check: And more

    If you encounter codec issues, convert to MP4 with H.264 encoding.

??? question "How accurate is the OCR?"
    Accuracy depends on:

    - **Video quality** - Higher resolution = better OCR
    - **Text clarity** - Clear, high-contrast text works best
    - **Steady frames** - Motion blur reduces accuracy

    Loups uses confidence-based filtering to ensure quality results.

??? question "Can I process videos in batch?"
    **Absolutely!** Use quiet mode for scripting:

    ```bash
    loups -q -o output.txt video.mp4
    ```

    Check the exit code to verify success in scripts.
