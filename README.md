# Loups

Scan Lights Out HB fastpitch game videos to extract batter information.

## Installation
> Soon to be available in pypi
```bash
pip install loups
```

## Usage

```bash
# Scan a video with default bundled template
loups video.mp4

# Specify custom template and output file
loups video.mp4 -t custom_template.png -o chapters.txt

# Quiet mode for scripting (no progress display)
loups video.mp4 -q -o chapters.txt

# Custom log location
loups video.mp4 -l /path/to/custom.log

# Disable logging entirely
loups video.mp4 --no-log

# Save results to file without progress display
loups video.mp4 -q -o chapters.txt --no-log
```

## CLI Options

**Positional Arguments:**
- `video`: Path to video file (required)

**Options:**
- `-t, --template PATH`: Path to custom template image (defaults to bundled `template_solid.png`)
- `-l, --log PATH`: Path to log file (default: `loups.log` in current directory)
  - Automatically rotates at 5MB
  - Keeps 3 backup files
  - **Mutually exclusive with `--no-log`**
- `--no-log`: Disable log file creation entirely
  - **Mutually exclusive with `--log`**
- `-o, --output PATH`: Save results to file in YouTube chapter format
- `-q, --quiet`: Suppress stdout progress display (errors still go to stderr)

## Important Notes

**Logging Options:**
- By default, logs are written to `loups.log` in the current directory
- Use `--log PATH` to specify a custom log file location
- Use `--no-log` to disable logging completely
- ⚠️ **You cannot use both `--log` and `--no-log` together** - they are mutually exclusive

## Features

- **Animated Progress Display**: Real-time scanning progress with softball animation 🥎
- **Batter Detection**: Automatically finds and timestamps each batter appearance
- **YouTube Chapter Format**: Outputs results ready for YouTube video chapters
- **Log Rotation**: Automatic log rotation (5MB max, keeps 3 backups)
- **Bundled Template**: Includes default template for Lights Out HB scoreboard
- **Custom Templates**: Support for custom scoreboard templates
