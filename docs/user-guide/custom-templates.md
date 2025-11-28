# :material-palette: Creating Custom Templates

Learn how to create templates for any video content to use with Loups.

---

## :question: What is a Template?

A template is an **image that acts as a trigger** - Loups scans your video looking for frames that match this template. When a match is found, Loups extracts the text from that frame to create a chapter entry.

!!! example "Template Analogy"
    Think of the template as a "bookmark shape" - Loups flips through your video looking for frames that look like your bookmark. When it finds one, it reads the text on that page.

---

## :footprints: 4-Step Process

### :one: Find a Clear Frame

Pause your video where the identifying text overlay is clearly visible:

- Sports: Scoreboard with player name
- Podcasts: Guest name overlay
- Gaming: Level title card
- Educational: Speaker introduction

!!! tip "Best Practices"
    - :material-check: Text is fully visible and readable
    - :material-check: No motion blur
    - :material-check: Consistent lighting
    - :material-check: Frame appears multiple times in video

### :two: Take a Screenshot

Capture the frame:

=== ":material-apple: macOS"
    - Press `⌘` + `Shift` + `4`
    - Select area to capture
    - File saved to Desktop

=== ":material-microsoft-windows: Windows"
    - Press `Win` + `Shift` + `S`
    - Select area
    - Save from clipboard

=== ":material-linux: Linux"
    - Use screenshot tool
    - Or: `gnome-screenshot -a`

### :three: Crop the Template

Open in image editor and crop to include:

- :material-check: The region where text appears
- :material-check: Some surrounding context (helps matching)
- :material-close: **Exclude** elements that change frame-to-frame

!!! warning "Crop Carefully"
    **Too large:** May include changing elements → false negatives
    **Too small:** May not match reliably → missed detections

    **Just right:** Includes text region + stable surrounding area

### :four: Save and Use

Save as PNG (recommended) or JPG:

```bash
loups -t my_template.png video.mp4
```

---

## :art: Template Examples

### :material-baseball-bat: Sports Scoreboard

```
┌─────────────────────────────┐
│  BATTER: Sarah Johnson #7   │  ← Include this
│  INNING: 3   SCORE: 2-1     │  ← Crop around text
└─────────────────────────────┘
```

**What to include:**
- Player name area
- Jersey number location
- Stable background elements

**What to exclude:**
- Changing score
- Moving elements
- Video timestamp

### :material-microphone: Podcast Guest Overlay

```
┌──────────────────────┐
│  NOW SPEAKING:       │
│  Dr. Jane Smith      │  ← Crop this region
│  AI Researcher       │
└──────────────────────┘
```

**What to include:**
- Name card background
- "NOW SPEAKING" label if consistent
- Text region

### :material-gamepad-variant: Game Level Card

```
┌─────────────────┐
│  LEVEL 5        │  ← Level text
│  The Castle     │  ← Level name
└─────────────────┘
```

**What to include:**
- Level indicator
- Title text area
- Consistent UI elements

---

## :white_check_mark: Template Quality Checklist

!!! success "Good Template Characteristics"
    - [x] :material-check-circle: **High contrast** - Text clearly visible
    - [x] :material-check-circle: **Consistent position** - Same location throughout video
    - [x] :material-check-circle: **Clear text** - No blur, pixelation, or distortion
    - [x] :material-check-circle: **Stable background** - Unchanging elements
    - [x] :material-check-circle: **Appropriate size** - Not too large, not too small
    - [x] :material-check-circle: **Good resolution** - Match video quality

!!! danger "Avoid These Issues"
    - [ ] :material-close-circle: Motion blur or partial frames
    - [ ] :material-close-circle: Changing elements (scores, timers)
    - [ ] :material-close-circle: Low resolution or compression artifacts
    - [ ] :material-close-circle: Text partially cut off
    - [ ] :material-close-circle: Inconsistent appearance across video

---

## :test_tube: Testing Your Template

### Step 1: Test on Short Clip

Create a test clip first:

```bash
# Extract first 2 minutes with ffmpeg
ffmpeg -i full_video.mp4 -t 120 -c copy test_clip.mp4
```

### Step 2: Run with Logging

```bash
loups --log --debug -t my_template.png test_clip.mp4
```

### Step 3: Check Results

```bash
# View the log
cat loups.log

# Look for:
# - Template match timestamps
# - OCR confidence scores
# - Extracted text
```

### Step 4: Adjust if Needed

!!! tip "Troubleshooting"
    **Too many matches?** → Crop template more tightly
    **Missing matches?** → Include more surrounding context
    **Wrong text extracted?** → Adjust template boundaries
    **Garbled OCR?** → Use higher quality source frame

---

## :bulb: Advanced Tips

### Multiple Templates

Can't find one template that works for all frames? Use different templates:

```bash
# Process same video multiple times with different templates
loups -t template1.png -o chapters1.txt video.mp4
loups -t template2.png -o chapters2.txt video.mp4

# Combine results manually
cat chapters1.txt chapters2.txt | sort > all_chapters.txt
```

### Template for Thumbnails

Create a separate template for thumbnail extraction:

```bash
# Different template for title screen
loups video.mp4 thumbnail --thumbnail-template title_screen_template.png
```

### Video Quality Matters

!!! info "Source Quality"
    Template matching works best with:

    - **720p or higher** video resolution
    - **Minimal compression** artifacts
    - **Steady camera** (for handheld footage)
    - **Good lighting** and contrast

---

## :material-shape: Use Case Examples

### :material-school: Educational Lecture

**Scenario:** Video with speaker name overlays

```
Template includes:
┌─────────────────────┐
│ 👤 Speaker Name     │
│    Title/Role       │
└─────────────────────┘
```

**Result:**
```
0:00:00 Introduction
0:05:30 Dr. Sarah Chen - Computer Science
0:25:15 Prof. Michael Brown - Mathematics
0:45:00 Dr. Lisa Wang - Physics
```

### :material-music: Music Performance

**Scenario:** Song title cards between performances

```
Template includes:
┌──────────────────────┐
│  🎵 Now Playing:     │
│  [Song Title]        │
│  [Artist Name]       │
└──────────────────────┘
```

**Result:**
```
0:00:00 Opening
0:03:45 Song Title - Artist Name
0:08:20 Another Song - Different Artist
```

### :material-television: TV Series

**Scenario:** Episode title cards

```
Template includes:
┌────────────────────┐
│  EPISODE 5         │
│  "Episode Title"   │
└────────────────────┘
```

---

## :hammer_and_wrench: Tools for Template Creation

### Recommended Tools

| Tool | Platform | Free | Use Case |
|------|----------|------|----------|
| **Preview** | :material-apple: macOS | :material-check: | Built-in, simple cropping |
| **Paint** | :material-microsoft-windows: Windows | :material-check: | Basic editing |
| **GIMP** | :material-linux::material-apple::material-microsoft-windows: All | :material-check: | Advanced editing |
| **ffmpeg** | :material-linux::material-apple::material-microsoft-windows: All | :material-check: | Extract frames |
| **VLC** | :material-linux::material-apple::material-microsoft-windows: All | :material-check: | Screenshot frames |

### Extract Frame with ffmpeg

Get a perfect frame from exact timestamp:

```bash
# Extract frame at 01:23:45
ffmpeg -ss 01:23:45 -i video.mp4 -frames:v 1 template.png
```

---

## :link: Next Steps

Now that you have a template:

1. [:material-rocket-launch: Quick Start](quick-start.md) - Use your template
2. [:material-console: CLI Reference](cli-reference.md) - Template options
3. [:material-code-braces: API Reference](../api/index.md) - Programmatic usage

---

## :question: Common Questions

??? question "Can I use the same template for different videos?"
    **Yes**, if the videos have the same overlay/UI format!

    For example:
    - All episodes of same TV series
    - Same game with consistent UI
    - Videos from same production

??? question "What image format should I use?"
    **PNG recommended** for best quality (lossless compression)

    Also supported:
    - JPG/JPEG (acceptable, slightly lower quality)
    - BMP (works but larger files)

??? question "Does template size matter?"
    **Yes!** Template should be:

    - Same resolution as video (or close)
    - Large enough to be distinctive
    - Small enough to avoid changing elements

    Typically 200-800 pixels wide works well.

??? question "Can I create templates from YouTube videos?"
    **Absolutely!** Take screenshots while watching:

    - Pause at the overlay you want
    - Screenshot the browser window
    - Crop to just the overlay region
    - Use with downloaded video file

??? question "My template isn't matching. What now?"
    Try these steps:

    1. **Enable debug logging:** `loups --log --debug -t template.png video.mp4`
    2. **Check the log** for match confidence scores
    3. **Verify template** matches video frames exactly
    4. **Adjust crop** - try larger/smaller regions
    5. **Check resolution** - template should match video quality

    Still stuck? [Open an issue](https://github.com/jcspeegs/loups/issues) with:
    - Sample frame from video
    - Your template image
    - Debug log output
