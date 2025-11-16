# Thumbnail Template

## Required File
`thumbnail_template.png` - Your default thumbnail template image

## Instructions
1. Copy your thumbnail template image to this directory
2. Rename it to `thumbnail_template.png`
3. This template will be used by default when running thumbnail extraction without the `--thumbnail-template` option

## Usage
```bash
# Use default template (thumbnail_template.png from this directory)
loups thumbnail video.mp4

# Or use a custom template
loups thumbnail video.mp4 --thumbnail-template /path/to/custom-template.png
```

## Template Format
- Should be a PNG image
- Represents the typical thumbnail frame you want to match
- SSIM (Structural Similarity Index) will be used to compare video frames against this template
