# Installation Guide

Complete step-by-step installation guide for Smart Shell Assistant.

## Prerequisites

- **Python 3.8+**: Check with `python3 --version`
- **pip**: Python package manager
- **Shell**: Zsh or Bash
- **curl**: For API calls (usually pre-installed)
- **git** (optional): For version control features

## Quick Installation

### Automated Installation (Recommended)

```bash
# Clone the repository
git clone <repository-url> smartcli
cd smartcli

# Run the installer
bash shell_plugin/install.sh
```

The installer will guide you through:
1. Shell detection
2. Dependency installation
3. History export and indexing
4. Shell configuration
5. Backend service setup

### Manual Installation

If you prefer manual control or the automated installer doesn't work:

#### Step 1: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 2: Export Shell History

```bash
python3 scripts/export_history.py
```

This will:
- Find your shell history file
- Parse and sanitize commands
- Save to `data/history/history.json`

#### Step 3: Build FAISS Index

```bash
python3 scripts/build_index.py
```

This will:
- Load commands from history
- Generate embeddings (downloads model on first run)
- Build and save FAISS index

**Note**: First run will download the embedding model (~22MB). This might take a few minutes depending on your internet connection.

#### Step 4: Start Backend Service

```bash
# Run in foreground (for testing)
python3 backend/app.py

# Or run in background
nohup python3 backend/app.py > /tmp/smart_assistant.log 2>&1 &
```

Verify it's running:
```bash
curl http://127.0.0.1:8765/health
```

#### Step 5: Install Shell Plugin

**For Zsh**:

Add to `~/.zshrc`:
```bash
source /path/to/smartcli/shell_plugin/smart_assistant.zsh
```

**For Bash**:

Add to `~/.bashrc`:
```bash
source /path/to/smartcli/shell_plugin/smart_assistant.bash
```

#### Step 6: Reload Shell

```bash
# For Zsh
source ~/.zshrc

# For Bash
source ~/.bashrc
```

## Verification

Test the installation:

```bash
# Check if commands are available
type smart-suggest
type smart-fix

# Try a suggestion
ss "list files"

# Check backend health
curl http://127.0.0.1:8765/health
```

## Platform-Specific Notes

### macOS

```bash
# Install Python if needed
brew install python@3.11

# You may need to install Xcode Command Line Tools
xcode-select --install
```

### Ubuntu/Debian

```bash
# Install Python and dependencies
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv

# Install curl if needed
sudo apt-get install curl
```

### Arch Linux

```bash
# Install Python
sudo pacman -S python python-pip

# Install curl if needed
sudo pacman -S curl
```

### Windows (WSL)

The tool works in WSL (Windows Subsystem for Linux). Follow the Ubuntu/Debian instructions.

**Note**: Native Windows support is not available yet.

## Configuration

### Environment Variables

Create a `~/.smartassistant` file:

```bash
# API Configuration
export SMART_ASSISTANT_API="http://127.0.0.1:8765"
export SMART_ASSISTANT_ENABLED="true"
export SMART_ASSISTANT_MAX_SUGGESTIONS="5"

# Model Configuration
export EMBEDDING_MODEL_NAME="sentence-transformers/all-MiniLM-L6-v2"
export EMBEDDING_DEVICE="cpu"  # or "cuda" for GPU

# FAISS Configuration
export TOP_K_CANDIDATES="10"
export SIMILARITY_THRESHOLD="0.3"
```

Then source it in your shell RC file:
```bash
[ -f ~/.smartassistant ] && source ~/.smartassistant
```

## Troubleshooting

### Issue: "Module not found" errors

**Solution**:
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Backend won't start

**Solution 1**: Check if port is already in use
```bash
lsof -i :8765
# Kill the process if needed
kill -9 <PID>
```

**Solution 2**: Check logs
```bash
tail -f /tmp/smart_assistant.log
```

### Issue: No history found

**Solution**:
```bash
# Check history file location
ls -la ~/.zsh_history  # or ~/.bash_history

# If in different location, create symlink
ln -s /path/to/actual/history ~/.zsh_history
```

### Issue: Model download fails

**Solution**:
```bash
# Download manually
python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
model.save('models/embeddings_model')
"
```

### Issue: Commands not suggesting

**Solution 1**: Rebuild index
```bash
python3 scripts/export_history.py
python3 scripts/build_index.py
```

**Solution 2**: Check API connectivity
```bash
curl -X POST http://127.0.0.1:8765/suggest \
  -H "Content-Type: application/json" \
  -d '{"query":"test"}'
```

### Issue: Slow suggestions

**Possible causes**:
- Large history (>50k commands): Consider filtering
- CPU-intensive: Use GPU if available with `EMBEDDING_DEVICE=cuda`
- Disk I/O: Move index to SSD

**Solution**:
```bash
# Filter history to recent commands only
python3 scripts/export_history.py --limit 10000
python3 scripts/build_index.py
```

## Uninstallation

```bash
# 1. Remove from shell configuration
# Edit ~/.zshrc or ~/.bashrc and remove the source line

# 2. Stop backend service
pkill -f "python.*backend/app.py"

# 3. Remove project directory
rm -rf /path/to/smartcli

# 4. (Optional) Remove virtual environment
rm -rf venv
```

## Updating

```bash
# Pull latest changes
cd smartcli
git pull origin main

# Update dependencies
pip install --upgrade -r requirements.txt

# Rebuild index (if needed)
python3 scripts/export_history.py
python3 scripts/build_index.py

# Restart backend
pkill -f "python.*backend/app.py"
nohup python3 backend/app.py > /tmp/smart_assistant.log 2>&1 &
```

## Getting Help

If you encounter issues not covered here:

1. Check [GitHub Issues](https://github.com/yourrepo/smartcli/issues)
2. Review [Architecture docs](architecture.md) for system understanding
3. Enable debug logging:
   ```bash
   export LOG_LEVEL=DEBUG
   python3 backend/app.py
   ```
4. Create a new issue with:
   - Your OS and Python version
   - Error messages
   - Steps to reproduce
