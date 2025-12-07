#!/usr/bin/env bash
# Installation script for Smart Shell Assistant

set -e

GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
RESET="\033[0m"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}================================${RESET}"
echo -e "${BLUE}Smart Shell Assistant Installer${RESET}"
echo -e "${BLUE}================================${RESET}"
echo ""

# Detect shell
detect_shell() {
    if [[ -n "$ZSH_VERSION" ]]; then
        echo "zsh"
    elif [[ -n "$BASH_VERSION" ]]; then
        echo "bash"
    else
        echo "unknown"
    fi
}

SHELL_TYPE=$(detect_shell)

if [[ "$SHELL_TYPE" == "unknown" ]]; then
    echo -e "${YELLOW}Warning: Could not detect shell type${RESET}"
    echo "Please specify your shell:"
    echo "  1) Zsh"
    echo "  2) Bash"
    read -p "Choice [1-2]: " choice

    case $choice in
        1) SHELL_TYPE="zsh" ;;
        2) SHELL_TYPE="bash" ;;
        *) echo -e "${RED}Invalid choice${RESET}"; exit 1 ;;
    esac
fi

echo -e "${GREEN}✓ Detected shell: $SHELL_TYPE${RESET}"

# Check Python
echo ""
echo "Checking Python installation..."

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is required but not installed${RESET}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${RESET}"

# Create virtual environment (optional but recommended)
echo ""
read -p "Create a virtual environment? (recommended) [y/N]: " create_venv

if [[ "$create_venv" =~ ^[Yy]$ ]]; then
    echo "Creating virtual environment..."
    cd "$PROJECT_ROOT"

    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
        echo -e "${GREEN}✓ Virtual environment created${RESET}"
    else
        echo -e "${YELLOW}Virtual environment already exists${RESET}"
    fi

    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
cd "$PROJECT_ROOT"

pip install -q --upgrade pip
pip install -q -r requirements.txt

echo -e "${GREEN}✓ Dependencies installed${RESET}"

# Export model to ONNX (one-time setup)
echo ""
read -p "Export embedding model to ONNX format? (required for first-time setup) [Y/n]: " export_onnx

if [[ ! "$export_onnx" =~ ^[Nn]$ ]]; then
    echo "Checking for ONNX model..."
    
    if [[ -f "$PROJECT_ROOT/models/embeddings_model/model.onnx" ]]; then
        echo -e "${YELLOW}ONNX model already exists${RESET}"
    else
        echo "Exporting model to ONNX format (one-time download ~22MB)..."
        echo "This requires temporary installation of sentence-transformers and torch..."
        
        # Install export dependencies temporarily
        pip install -q sentence-transformers torch
        
        # Run export script
        python3 scripts/export_to_onnx.py
        
        # Remove heavy dependencies
        echo "Removing temporary export dependencies..."
        pip uninstall -q -y sentence-transformers torch
        
        echo -e "${GREEN}✓ ONNX model exported${RESET}"
    fi
else
    echo -e "${YELLOW}Skipping ONNX export. You can run it later with:${RESET}"
    echo "  pip install sentence-transformers torch"
    echo "  python scripts/export_to_onnx.py"
    echo "  pip uninstall sentence-transformers torch -y"
fi

# Export and build index
echo ""
echo "Setting up command history..."

read -p "Export your shell history and build index? [y/N]: " export_history

if [[ "$export_history" =~ ^[Yy]$ ]]; then
    echo "Exporting history..."
    python3 scripts/export_history.py

    echo ""
    echo "Building FAISS index..."
    python3 scripts/build_index.py

    echo -e "${GREEN}✓ Index built successfully${RESET}"
else
    echo -e "${YELLOW}Skipping history export. You can run it later with:${RESET}"
    echo "  python scripts/export_history.py"
    echo "  python scripts/build_index.py"
fi

# Install shell plugin
echo ""
echo "Installing shell plugin..."

if [[ "$SHELL_TYPE" == "zsh" ]]; then
    RC_FILE="$HOME/.zshrc"
    PLUGIN_FILE="$PROJECT_ROOT/shell_plugin/smart_assistant.zsh"
elif [[ "$SHELL_TYPE" == "bash" ]]; then
    RC_FILE="$HOME/.bashrc"
    PLUGIN_FILE="$PROJECT_ROOT/shell_plugin/smart_assistant.bash"
fi

# Check if already installed
if grep -q "smart_assistant" "$RC_FILE" 2>/dev/null; then
    echo -e "${YELLOW}Plugin already seems to be installed in $RC_FILE${RESET}"
    read -p "Re-install anyway? [y/N]: " reinstall

    if [[ ! "$reinstall" =~ ^[Yy]$ ]]; then
        echo "Skipping plugin installation"
    else
        # Remove old installation
        sed -i.bak '/smart_assistant/d' "$RC_FILE"
    fi
fi

# Add source line to RC file
echo "" >> "$RC_FILE"
echo "# Smart Shell Assistant" >> "$RC_FILE"
echo "source \"$PLUGIN_FILE\"" >> "$RC_FILE"

echo -e "${GREEN}✓ Plugin installed to $RC_FILE${RESET}"

# Start backend service
echo ""
read -p "Start the backend service now? [Y/n]: " start_backend

if [[ ! "$start_backend" =~ ^[Nn]$ ]]; then
    echo "Starting backend service..."

    # Check if already running
    if lsof -i :8765 &> /dev/null; then
        echo -e "${YELLOW}Backend service already running on port 8765${RESET}"
    else
        # Start backend in background
        cd "$PROJECT_ROOT"
        nohup python3 backend/app.py > /tmp/smart_assistant.log 2>&1 &
        sleep 2

        # Check if started successfully
        if lsof -i :8765 &> /dev/null; then
            echo -e "${GREEN}✓ Backend service started${RESET}"
            echo "  Logs: /tmp/smart_assistant.log"
        else
            echo -e "${RED}✗ Failed to start backend service${RESET}"
            echo "  Check logs: /tmp/smart_assistant.log"
        fi
    fi
else
    echo "You can start the backend later with:"
    echo "  python backend/app.py"
fi

# Installation complete
echo ""
echo -e "${GREEN}================================${RESET}"
echo -e "${GREEN}Installation Complete!${RESET}"
echo -e "${GREEN}================================${RESET}"
echo ""
echo "Next steps:"
echo "  1. Reload your shell: source ~/${RC_FILE##*/}"
echo "  2. Try it out: ss 'list files'"
echo "  3. Get help: smart-suggest --help"
echo ""
echo "Available commands:"
echo "  ss / smart-suggest  - Get command suggestions"
echo "  sf / smart-fix      - Fix last error"
echo "  st / smart-toggle   - Enable/disable assistant"
echo ""
echo -e "${BLUE}Happy coding! 🚀${RESET}"
