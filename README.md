# Smart Shell Assistant 🚀

> **Context-aware command suggestions powered by local AI embeddings**

Smart Shell Assistant is an intelligent command-line tool that provides real-time, context-aware shell command suggestions using semantic search and local machine learning models. No cloud APIs required – everything runs on your machine.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- **🧠 Semantic Command Search**: Find commands based on what they do, not just what they're called
- **🎯 Context-Aware Suggestions**: Considers your current directory, git status, file types, and recent commands
- **⚡ Fast Retrieval**: Uses FAISS for lightning-fast similarity search
- **🪶 Lightweight**: ONNX-based inference (~20MB model, no PyTorch needed)
- **🔒 Privacy-First**: All data stays local – no external API calls
- **⚠️ Safety Checks**: Warns about potentially destructive commands
- **🛠️ Error Fixes**: Suggests fixes for common errors
- **🐚 Multi-Shell Support**: Works with both Zsh and Bash

## 🎯 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url> smartcli
cd smartcli

# Run the installation script
bash shell_plugin/install.sh
```

The installer will:
1. Detect your shell (Zsh or Bash)
2. Install Python dependencies
3. Export model to ONNX format (one-time setup)
4. Export and index your shell history
5. Configure your shell
6. Start the backend service

### Usage

After installation, restart your shell and try:

```bash
# Get command suggestions
ss "list all files including hidden"

# Shortcuts
ss "commit changes"       # Suggests git commit commands
ss "run tests"            # Context-aware test runner suggestions
ss "start server"         # Suggests development server commands

# Fix errors
sf                        # Analyze and fix the last command error

# Toggle assistant
st                        # Enable/disable the assistant
```

## 📖 How It Works

```mermaid
graph LR
    A[User Query] --> B[Context Extraction]
    B --> C[Shell Context<br/>cwd, git, files]
    C --> D[Embedder]
    D --> E[FAISS Search]
    E --> F[Retriever]
    F --> G[Ranker]
    G --> H[Safety Check]
    H --> I[Suggestions]
```

1. **Context Extraction**: Analyzes your current directory, git status, file types, and recent commands
2. **Semantic Embedding**: Converts your query to a vector embedding using sentence-transformers
3. **Similarity Search**: Uses FAISS to find similar commands from your history
4. **Context-Aware Ranking**: Ranks results based on relevance to your current context
5. **Safety Checking**: Flags potentially destructive commands
6. **Smart Display**: Shows top suggestions with safety warnings

## 🏗️ Architecture

```
smartcli/
├── backend/              # Core backend services
│   ├── app.py           # FastAPI server
│   ├── embedder.py      # Sentence-transformers embedding
│   ├── retriever.py     # FAISS-based search
│   ├── ranker.py        # Context-aware ranking
│   ├── safety.py        # Destructive command detection
│   └── error_fixes.py   # Error pattern matching
│
├── shell_plugin/         # Shell integration
│   ├── smart_assistant.zsh
│   ├── smart_assistant.bash
│   └── install.sh
│
├── scripts/             # Utility scripts
│   ├── export_history.py
│   ├── build_index.py
│   └── update_embeddings.py
│
└── tests/               # Test suite
```

## ⚙️ Configuration

Set environment variables to customize behavior:

```bash
# API endpoint (default: http://127.0.0.1:8765)
export SMART_ASSISTANT_API="http://localhost:8765"

# Enable/disable assistant (default: true)
export SMART_ASSISTANT_ENABLED="true"

# Maximum suggestions to show (default: 5)
export SMART_ASSISTANT_MAX_SUGGESTIONS="5"

# Device for ONNX inference (default: cpu)
export EMBEDDING_DEVICE="cpu"  # or "cuda" for GPU
```

## 🧪 Development

### Setup Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Export model to ONNX (first time only, requires sentence-transformers)
pip install sentence-transformers torch  # Temporary for export
python scripts/export_to_onnx.py
pip uninstall sentence-transformers torch -y  # Remove heavy deps

# Export history and build index
python scripts/export_history.py
python scripts/build_index.py

# Run tests
pytest tests/ -v

# Start backend
python backend/app.py
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_retriever.py -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html
```

### API Endpoints

The backend exposes these REST API endpoints:

- `POST /suggest` - Get command suggestions
- `POST /fix-error` - Get error fix suggestions
- `GET /health` - Health check
- `POST /rebuild-index` - Rebuild the FAISS index
- `GET /stats` - Get system statistics

See `docs/api_spec.md` for detailed API documentation.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [ONNX Runtime](https://onnxruntime.ai/) for efficient ML inference
- [Transformers](https://huggingface.co/transformers/) for the tokenizer
- [FAISS](https://github.com/facebookresearch/faiss) for efficient similarity search
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework

## 🗺️ Roadmap

See `docs/roadmap.md` for planned features and improvements.

### v0.1.0 (Current)
- ✅ Basic semantic search
- ✅ Context awareness (git, files, directory type)
- ✅ Safety checking
- ✅ Error fix suggestions
- ✅ Zsh and Bash plugins

### v0.2.0 (Planned)
- 🔄 Command success rate tracking
- 🔄 User feedback integration
- 🔄 ML-based ranker
- 🔄 Multi-language support
- 🔄 Plugin system for custom integrations

## 📚 Documentation

- [Installation Guide](docs/installation.md)
- [Architecture](docs/architecture.md)
- [Design Decisions](docs/design_decisions.md)
- [API Specification](docs/api_spec.md)
- [Roadmap](docs/roadmap.md)

## 🐛 Troubleshooting

### Backend not starting

```bash
# Check if port 8765 is in use
lsof -i :8765

# Check logs
tail -f /tmp/smart_assistant.log
```

### No suggestions appearing

```bash
# Verify index exists
ls -lh models/faiss_index.bin

# Rebuild index
python scripts/build_index.py
```

### Model download issues

If the embedding model fails to download, you can manually download it:

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
model.save('models/embeddings_model')
```

---

**Made with ❤️ by the Smart Shell Assistant team**
