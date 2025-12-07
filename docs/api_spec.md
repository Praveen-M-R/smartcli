# API Specification

REST API documentation for Smart Shell Assistant backend service.

## Base Configuration

- **Base URL**: `http://127.0.0.1:8765`
- **Protocol**: HTTP/1.1
- **Content-Type**: `application/json`
- **Response Format**: JSON

## Endpoints

### 1. Health Check

Check if the service is running and healthy.

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "stats": {
    "retriever": {
      "loaded": true,
      "num_commands": 1234,
      "dimension": 384,
      "metadata": { ... }
    },
    "config": {
      "max_suggestions": 5,
      "safety_check_enabled": true
    }
  }
}
```

**Status Codes**:
- `200 OK`: Service is healthy
- `500 Internal Server Error`: Service has issues

**Example**:
```bash
curl http://127.0.0.1:8765/health
```

---

### 2. Get Command Suggestions

Get context-aware command suggestions based on query and environment.

**Endpoint**: `POST /suggest`

**Request Body**:
```json
{
  "query": "string (required)",
  "cwd": "string (optional)",
  "last_command": "string (optional)",
  "last_exit_code": "integer (optional)",
  "recent_commands": ["string"] (optional),
  "max_suggestions": "integer (optional, default: 5)"
}
```

**Response**:
```json
{
  "success": true,
  "suggestions": [
    {
      "command": "git status",
      "score": 0.95,
      "rank": 0,
      "context_score": 0.85,
      "final_score": 0.90,
      "semantic_score": 0.95,
      "safety": {
        "level": "safe",
        "warning": null,
        "reasons": []
      }
    }
  ],
  "context": {
    "cwd": "/home/user/project",
    "cwd_basename": "project",
    "git_info": {
      "is_git_repo": true,
      "branch": "main",
      "has_uncommitted_changes": false
    },
    "file_types": {
      ".py": 5,
      ".md": 2
    },
    "directory_type": "python,git",
    "env_hints": {}
  },
  "total_candidates": 10
}
```

**Status Codes**:
- `200 OK`: Successfully retrieved suggestions
- `500 Internal Server Error`: Error processing request

**Example**:
```bash
curl -X POST http://127.0.0.1:8765/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "query": "list files",
    "cwd": "/home/user/project",
    "max_suggestions": 3
  }'
```

**Field Descriptions**:

Request:
- `query`: The search query (partial command or description)
- `cwd`: Current working directory
- `last_command`: Last executed command
- `last_exit_code`: Exit code of last command (0 = success)
- `recent_commands`: Array of recently executed commands
- `max_suggestions`: Maximum number of suggestions to return

Response:
- `suggestions`: Array of suggestion objects
  - `command`: The suggested command
  - `score`: Semantic similarity score (0-1)
  - `rank`: Position in results (0-indexed)
  - `context_score`: Context matching score (0-1)
  - `final_score`: Combined final score (0-1)
  - `semantic_score`: Raw semantic similarity
  - `safety`: Safety check results
- `context`: Extracted context information
- `total_candidates`: Total candidates before filtering

---

### 3. Get Error Fix Suggestions

Get fix suggestions for an error message.

**Endpoint**: `POST /fix-error`

**Request Body**:
```json
{
  "error_message": "string (required)",
  "last_command": "string (optional)"
}
```

**Response**:
```json
{
  "success": true,
  "fixes": [
    {
      "category": "permissions",
      "description": "Permission error when executing command",
      "fixes": [
        "Try using sudo: sudo <command>",
        "Check file permissions: ls -l <file>",
        "Change permissions: chmod +x <file>"
      ],
      "confidence": 0.85
    }
  ],
  "quick_fix": "Try using sudo: sudo <command>",
  "error_message": "permission denied"
}
```

**Status Codes**:
- `200 OK`: Successfully retrieved fixes
- `500 Internal Server Error`: Error processing request

**Example**:
```bash
curl -X POST http://127.0.0.1:8765/fix-error \
  -H "Content-Type: application/json" \
  -d '{
    "error_message": "bash: npm: command not found",
    "last_command": "npm install"
  }'
```

**Field Descriptions**:

Request:
- `error_message`: The error message to analyze
- `last_command`: The command that produced the error

Response:
- `fixes`: Array of fix objects
  - `category`: Error category (permissions, git, npm, etc.)
  - `description`: Human-readable error description
  - `fixes`: Array of suggested fix commands
  - `confidence`: Confidence score (0-1)
- `quick_fix`: Most likely single fix (highest confidence)

---

### 4. Rebuild Index

Rebuild the FAISS index with new commands.

**Endpoint**: `POST /rebuild-index`

**Request Body**:
```json
{
  "commands": ["git status", "npm install", "..."]
}
```

**Response**:
```json
{
  "success": true,
  "message": "Index rebuilt successfully",
  "stats": {
    "loaded": true,
    "num_commands": 1500,
    "dimension": 384,
    "metadata": { ... }
  }
}
```

**Status Codes**:
- `200 OK`: Successfully rebuilt index
- `500 Internal Server Error`: Error rebuilding index

**Example**:
```bash
curl -X POST http://127.0.0.1:8765/rebuild-index \
  -H "Content-Type: application/json" \
  -d '{
    "commands": ["ls -la", "git status", "npm install"]
  }'
```

---

### 5. Get Statistics

Get system statistics and configuration.

**Endpoint**: `GET /stats`

**Response**:
```json
{
  "retriever": {
    "loaded": true,
    "num_commands": 1234,
    "dimension": 384,
    "metadata": {
      "num_commands": 1234,
      "dimension": 384,
      "index_type": "IndexFlatL2"
    }
  },
  "config": {
    "max_suggestions": 5,
    "safety_check_enabled": true
  }
}
```

**Status Codes**:
- `200 OK`: Successfully retrieved stats

**Example**:
```bash
curl http://127.0.0.1:8765/stats
```

---

### 6. Root

Service information endpoint.

**Endpoint**: `GET /`

**Response**:
```json
{
  "service": "Smart Shell Assistant API",
  "version": "0.1.0",
  "status": "running"
}
```

**Status Codes**:
- `200 OK`: Service is running

**Example**:
```bash
curl http://127.0.0.1:8765/
```

---

## Error Responses

All endpoints may return error responses in this format:

```json
{
  "detail": "Error message description"
}
```

Common error codes:
- `400 Bad Request`: Invalid request parameters
- `500 Internal Server Error`: Server-side error

---

## Interactive API Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: `http://127.0.0.1:8765/docs`
- **ReDoc**: `http://127.0.0.1:8765/redoc`

These interfaces allow you to:
- View all endpoints
- Try requests interactively
- See request/response schemas
- Download OpenAPI specification

---

## Rate Limiting

Currently, there is no rate limiting implemented. For local use, this is not typically necessary.

## Authentication

Currently, there is no authentication required. The service is designed for local use only.

**Security Note**: Do not expose this service to the internet without proper authentication and encryption.

## CORS

CORS is enabled for all origins to allow browser-based tools to interact with the API during development.

## Versioning

API version is included in the root endpoint response. Future versions may use path-based versioning (e.g., `/v2/suggest`).
