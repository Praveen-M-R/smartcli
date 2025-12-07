# Roadmap

## Version History & Future Plans

### v0.1.0 - Initial Release (Current) ✅

**Core Features**:
- [x] Semantic command search using sentence-transformers
- [x] FAISS-based vector similarity search 
- [x] Context extraction (cwd, git, file types)
- [x] Context-aware ranking algorithm
- [x] Safety checking for destructive commands
- [x] Error pattern matching and fix suggestions
- [x] Zsh plugin with command hooks
- [x] Bash plugin with command hooks
- [x] FastAPI backend service
- [x] History export and sanitization
- [x] Automated installation script

**Documentation**:
- [x] README with quick start
- [x] Architecture documentation
- [x] Design decisions
- [x] Installation guide
- [x] API specification
- [x] Test suite

### v0.2.0 - User Feedback & Learning (Planned)

**Learning System**:
- [ ] Command success rate tracking
- [ ] User feedback collection (thumbs up/down)
- [ ] Suggestion acceptance analytics
- [ ] Personalized ranking based on user history

**Improved Ranking**:
- [ ] ML-based ranker trained on user feedback
- [ ] Time-of-day awareness
- [ ] Project-specific command patterns
- [ ] Command chaining detection

**UX Improvements**:
- [ ] Inline suggestions (like fish shell)
- [ ] Fuzzy matching for typos
- [ ] Command explanation/documentation
- [ ] Keyboard shortcuts for quick acceptance

**Technical Improvements**:
- [ ] Incremental index updates without full rebuild
- [ ] Better memory management
- [ ] Caching layer for frequent queries

### v0.3.0 - Multi-Language & Extensibility (Planned)

**Language Support**:
- [ ] Fish shell plugin
- [ ] PowerShell plugin (Windows)
- [ ] Nushell plugin

**Plugin System**:
- [ ] Custom command sources (not just history)
- [ ] Integration plugins (kubectl, terraform, aws-cli)
- [ ] Custom ranker plugins
- [ ] Custom context extractors

**Tool-Specific Integrations**:
- [ ] Kubernetes command suggestions with context
- [ ] Docker Compose command patterns
- [ ] Git workflow suggestions
- [ ] NPM script suggestions from package.json

### v0.4.0 - Advanced Features (Future)

**Command Understanding**:
- [ ] Natural language to command (simple cases)
- [ ] Command output explanation
- [ ] Man page integration
- [ ] Example command generation

**Collaboration**:
- [ ] Team shared indexes (opt-in)
- [ ] Command snippet library
- [ ] Best practices recommendations
- [ ] Organizational policy enforcement

**Performance**:
- [ ] IVF FAISS index for large histories (>100k)
- [ ] GPU acceleration option
- [ ] Distributed index for multi-machine setups
- [ ] Streaming suggestions for large result sets

**Safety**:
- [ ] Advanced destructive command detection
- [ ] Dry-run mode for risky commands
- [ ] Undo/rollback suggestions
- [ ] Audit log for all executed suggestions

### v1.0.0 - Production Ready (Long-term)

**Enterprise Features**:
- [ ] Authentication and authorization
- [ ] Multi-user support
- [ ] Centralized management
- [ ] Compliance reporting
- [ ] RBAC for sensitive commands

**Observability**:
- [ ] Metrics and monitoring
- [ ] Performance dashboards
- [ ] Error tracking and alerting
- [ ] Usage analytics

**Quality**:
- [ ] 95%+ test coverage
- [ ] Load testing for scale
- [ ] Security audit
- [ ] Documentation completeness audit

**Platform Support**:
- [ ] macOS installer (.pkg)
- [ ] Linux packages (.deb, .rpm)
- [ ] Homebrew formula
- [ ] Snapcraft package

## Community Contributions Welcome

We welcome contributions in these areas:

### High Priority
- Additional error fix patterns
- Shell plugin improvements
- Performance optimizations
- Bug fixes

### Medium Priority
- New integration plugins (kubectl, aws, etc.)
- Documentation improvements
- Test coverage improvements
- CI/CD setup

### Nice to Have
- UI/UX improvements
- Advanced features from roadmap
- Mobile terminal support (Termux, etc.)
- Alternative embedding models

## Research & Experimental

Ideas being explored but not committed:

- **Graph-based command sequences**: Learn command workflows
- **Reinforcement learning**: Optimize suggestions based on user actions
- **Multi-modal understanding**: Include command output for context
- **Semantic code search**: Extend to finding code snippets
- **Voice commands**: Voice-to-command conversion
- **AR/VR terminal integration**: Future terminal interfaces

## How to Contribute

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on:
- Setting up dev environment
- Code style and conventions
- Testing requirements
- Pull request process

## Release Timeline

- **v0.1.0**: Now (Initial Release)
- **v0.2.0**: Q1 2024 (User Feedback & Learning)
- **v0.3.0**: Q2 2024 (Multi-Language)
- **v0.4.0**: Q3 2024 (Advanced Features)
- **v1.0.0**: Q4 2024 (Production Ready)

*Timeline is aspirational and subject to change based on community involvement and feedback.*

## Feedback

We'd love to hear from you! Please:
- Open issues for bugs or feature requests
- Start discussions for ideas
- Submit PRs for contributions
- Share your use cases and workflows

Together we can make the command line more intelligent and user-friendly!
