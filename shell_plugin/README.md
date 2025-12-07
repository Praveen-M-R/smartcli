# Shell Plugin - Shell Installation Guide

This directory contains shell plugins for Smart Shell Assistant.

## Quick Start

Run the installation script:

```bash
./install.sh
```

The script will:
- Detect your shell (Zsh or Bash)
- Install Python dependencies
- Export and index your shell history
- Add the plugin to your shell configuration
- Start the backend service

## Manual Installation

### For Zsh

Add to your `~/.zshrc`:

```bash
source /path/to/smartcli/shell_plugin/smart_assistant.zsh
```

### For Bash

Add to your `~/.bashrc`:

```bash
source /path/to/smartcli/shell_plugin/smart_assistant.bash
```

## Commands

Once installed, you have access to:

- `smart-suggest <query>` or `ss <query>` - Get command suggestions
- `smart-fix` or `sf` - Get fixes for the last error
- `smart-toggle` or `st` - Enable/disable the assistant

## Examples

```bash
# Get suggestions for listing files
ss "list all files"

# Get suggestions for git operations
ss "commit changes"

# Fix the last error
sf

# Toggle assistant on/off
st
```

## Configuration

Set these environment variables to customize behavior:

```bash
export SMART_ASSISTANT_API="http://127.0.0.1:8765"
export SMART_ASSISTANT_ENABLED="true"
export SMART_ASSISTANT_MAX_SUGGESTIONS="5"
```

## Troubleshooting

### Plugin not loading

1. Make sure the backend is running:
   ```bash
   python backend/app.py
   ```

2. Reload your shell:
   ```bash
   source ~/.zshrc  # or ~/.bashrc
   ```

### No suggestions appearing

1. Check the backend is accessible:
   ```bash
   curl http://127.0.0.1:8765/health
   ```

2. Verify the index exists:
   ```bash
   ls -lh models/faiss_index.bin
   ```

3. Rebuild the index if needed:
   ```bash
   python scripts/export_history.py
   python scripts/build_index.py
   ```

### Commands not found

Make sure you've reloaded your shell configuration after installation.

## Uninstalling

Remove the source line from your `.zshrc` or `.bashrc`:

```bash
# Remove this line:
source /path/to/smartcli/shell_plugin/smart_assistant.zsh
```

Then reload your shell.
