# Design Decisions

This document explains the key design decisions made in building the Smart Shell Assistant.

## Why Local-First?

**Decision**: All processing happens locally without cloud API calls.

**Rationale**:
- **Privacy**: Shell commands often contain sensitive information (passwords, API keys, internal URLs)
- **Latency**: Local processing is faster than network round-trips
- **Reliability**: Works offline and doesn't depend on external services
- **Cost**: No per-request API costs

**Trade-offs**:
- Requires local compute resources
- Model quality limited by what runs locally
- No collaborative learning across users

## Why FAISS?

**Decision**: Use FAISS for vector similarity search.

**Alternatives Considered**:
- Elasticsearch: Too heavy for local deployment
- Annoy: Less maintained, fewer features
- Chromadb: Good alternative but more complex setup

**Why FAISS Won**:
- Extremely fast (10ms for 10k vectors)
- Battle-tested (used by Facebook, Google)
- Minimal dependencies
- Easy persistence
- Multiple index types for scaling

## Why Sentence-Transformers?

**Decision**: Use sentence-transformers/all-MiniLM-L6-v2 for embeddings.

**Alternatives Considered**:
- OpenAI embeddings: Requires API calls (violates local-first)
- Word2Vec: Outdated, poor quality for sentences
- USE (Universal Sentence Encoder): Larger model size

**Why Sentence-Transformers Won**:
- State-of-the-art quality
- Small model size (22MB for all-MiniLM-L6-v2)
- Fast inference
- Easy to use
- Pre-trained on diverse text

**Model Choice**: all-MiniLM-L6-v2 specifically because:
- Best quality/size trade-off
- 384-dimensional embeddings (good balance)
- Trained on 1B+ sentence pairs

## Why FastAPI?

**Decision**: Use FastAPI for the backend service.

**Alternatives Considered**:
- Flask: Simpler but less performant
- WebSocket server: More complex, overkill for use case
- gRPC: Harder to debug, requires more setup

**Why FastAPI Won**:
- Excellent performance (async support)
- Auto-generated API docs
- Type validation with Pydantic
- Easy to deploy
- Modern Python patterns

## Shell Plugin Design

**Decision**: Separate plugins for Zsh and Bash instead of unified script.

**Rationale**:
- Shells have different hook mechanisms
- Shell-specific optimizations possible
- Cleaner code without compatibility checks
- Better error handling per shell

**Trade-offs**:
- Code duplication
- Need to maintain both plugins

## Context-Aware Ranking

**Decision**: Use weighted scoring for ranking instead of pure semantic similarity.

**Rationale**:
- Pure semantic similarity misses important context
- Git commands make sense in git repos
- Python commands make sense in Python projects
- Recency matters for common workflows

**Weights Chosen**:
- Semantic: 50% (base relevance)
- Git context: 15% (strong signal)
- Directory type: 15% (strong signal)
- File types: 10% (moderate signal)
- Recency: 10% (weak signal)

These weights were chosen through manual testing and seem to provide good balance.

## Error Fix Pattern Matching

**Decision**: Use regex pattern matching instead of ML for error fixes.

**Rationale**:
- Errors have predictable patterns
- Regex is fast and deterministic
- Easy to add new patterns
- No training data required
- Explainable results

**When to Reconsider**:
- If pattern count exceeds ~100
- If accuracy becomes an issue
- If we have user feedback data

## Safety Checking

**Decision**: Pattern-based safety checking with severity levels.

**Rationale**:
- Destructive commands have known patterns
- False positives are acceptable (better safe than sorry)
- Can't catch everything, but catches common mistakes
- Educational value in showing warnings

**Not Included**:
- Sandbox execution
- Actual command analysis
- User permission system

**Reason**: Scope creep, complex to implement correctly

## History Sanitization

**Decision**: Remove sensitive data from history before indexing.

**Patterns Removed**:
- API keys and tokens
- Passwords in URLs
- Environment variable secrets

**Trade-off**: May remove legitimate commands that happen to match patterns

## Singleton Pattern for Models

**Decision**: Use singleton pattern for embedder and retriever.

**Rationale**:
- Model loading is expensive (~1-2 seconds)
- Multiple instances waste memory
- Single instance per process is sufficient

## Index Persistence

**Decision**: Save index to disk for fast startup.

**Alternatives Considered**:
- Rebuild on every startup: Too slow
- Keep in memory only: Lost on restart
- Database storage: Overkill for use case

## No Auto-Execution

**Decision**: Never auto-execute suggested commands.

**Rationale**:
- Safety: User must review before running
- Trust: User controls their system
- Explainability: User sees what will run

**Alternative Considered**: Trusted command list for auto-execution
**Rejected Because**: Too risky, false sense of security

## Metadata in FAISS

**Decision**: Store commands and metadata in separate JSON file.

**Rationale**:
- FAISS only stores vectors
- Need command text for display
- Need metadata for debugging
- JSON is human-readable

**Trade-off**: Two files to keep in sync

## Async API Design

**Decision**: Use FastAPI's async capabilities.

**Rationale**:
- Better concurrency for multiple requests
- Non-blocking I/O for file operations
- Modern Python best practices

**Trade-off**: More complex code than sync

## Configuration via Environment Variables

**Decision**: Use environment variables for configuration.

**Rationale**:
- Standard practice for services
- Easy to override
- No config files to manage
- Shell-friendly

**Alternative Considered**: Config file (YAML/JSON)
**Rejected Because**: Adds complexity, environment variables sufficient

## Future Considerations

### What We Might Change

1. **ML Ranker**: If we collect enough user feedback data
2. **Advanced FAISS Index**: IVF index for >100k commands
3. **Collaborative Features**: Shared indexes for teams (opt-in)
4. **Plugin System**: For custom command sources
5. **Better Embedding Model**: As models improve and shrink

### What We Won't Change

1. **Local-first**: This is a core principle
2. **Privacy**: No telemetry or data collection
3. **No auto-execution**: Too risky
