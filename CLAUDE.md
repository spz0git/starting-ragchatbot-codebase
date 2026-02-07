# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Retrieval-Augmented Generation (RAG) chatbot** that answers questions about course materials using semantic search and AI-powered responses. The system uses ChromaDB for vector storage, Anthropic's Claude API for generation, and provides a vanilla JavaScript web interface.

## ⚠️ Important: Package Manager

**This project uses `uv` for package management.** Always use `uv` commands - never use `pip` directly.

```bash
# ✅ Correct
uv sync                    # Install/sync dependencies
uv run uvicorn app:app     # Run commands in uv environment
uv add package-name        # Add new dependencies

# ❌ Incorrect - DO NOT USE
pip install ...            # Will not work correctly with uv
python -m venv ...         # uv manages virtual environments
```

## Development Commands

### Setup & Installation
```bash
# Install dependencies (requires uv package manager)
uv sync

# Create .env file with your API key
echo "ANTHROPIC_API_KEY=your-key-here" > .env
```

### Running the Application
```bash
# Using the run script (recommended)
./run.sh

# Manual start
cd backend && uv run uvicorn app:app --reload --port 8000

# Access points:
# - Web UI: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Development Operations
```bash
# Clear vector database (forces rebuild on next startup)
rm -rf backend/chroma_db

# View current configuration
cat backend/config.py

# Monitor server logs
# (run.sh already includes --reload for auto-restart on code changes)
```

## Architecture

### RAG Pipeline Flow

The system processes queries through a multi-stage pipeline:

1. **User Query** → Frontend (`script.js`) sends POST to `/api/query`
2. **FastAPI** (`app.py`) → Creates/retrieves session, calls RAG system
3. **RAG Orchestrator** (`rag_system.py`) → Coordinates all components
4. **AI Generator** (`ai_generator.py`) → Sends query to Claude API with tool definitions
5. **Claude Decision** → Determines if tool usage is needed
6. **Tool Execution** (`search_tools.py`) → If needed, executes semantic search
7. **Vector Store** (`vector_store.py`) → Queries ChromaDB with embeddings
8. **ChromaDB** → Returns top-N similar chunks with metadata
9. **Result Formatting** → Adds course/lesson context to results
10. **Claude Response** → Generates final answer based on search results
11. **Session Update** → Conversation history is stored
12. **Response Return** → JSON with answer, sources, and session_id

### Two-Collection Architecture

The system uses **two separate ChromaDB collections**:

1. **`course_catalog`**: Stores course-level metadata
   - Documents: Course titles (searchable)
   - Metadata: instructor, course_link, lessons (JSON), lesson_count
   - Purpose: Fuzzy course name resolution via semantic search
   - IDs: Course title (used as unique identifier)

2. **`course_content`**: Stores actual course content chunks
   - Documents: Text chunks with lesson context prefixes
   - Metadata: course_title, lesson_number, chunk_index
   - Purpose: Content retrieval for answering queries
   - IDs: `{course_title}_{chunk_index}`

**Why two collections?** This enables:
- Fuzzy course name matching ("MCP" → "Introduction to MCP Servers")
- Filtered searches by resolved course title and/or lesson number
- Separation of metadata search from content search

### Tool-Based Search System

The RAG system uses **Anthropic's tool calling** rather than direct vector search:

- **Tool Definition**: `search_course_content` with parameters (query, course_name, lesson_number)
- **Execution Flow**: Claude decides when to search → Tool executes → Results formatted → Claude generates answer
- **Benefits**: Claude intelligently decides when course search is needed vs. using general knowledge
- **Source Tracking**: `CourseSearchTool.last_sources` stores sources for UI display

### Document Processing Pipeline

Course documents follow a strict format (see `/docs/course1_script.txt`):

```
Course Title: [title]
Course Link: [url]
Course Instructor: [name]

Lesson 0: [lesson title]
Lesson Link: [url]
[lesson content...]

Lesson 1: [lesson title]
Lesson Link: [url]
[lesson content...]
```

**Processing stages**:
1. **DocumentProcessor.process_course_document()** parses metadata and lessons
2. **DocumentProcessor.chunk_text()** splits content using sentence-based chunking with overlap
3. **Chunks** get prefixed with context: `"Course {title} Lesson {N} content: {chunk}"`
4. **VectorStore.add_course_metadata()** indexes course in catalog collection
5. **VectorStore.add_course_content()** indexes chunks in content collection

**Key settings** (in `config.py`):
- `CHUNK_SIZE: 800` characters per chunk
- `CHUNK_OVERLAP: 100` characters overlap between consecutive chunks
- `MAX_RESULTS: 5` top results returned from vector search

### Session Management

Conversations maintain context via `SessionManager`:
- Each session gets unique ID: `session_{counter}`
- Stores last `MAX_HISTORY * 2` messages (2 exchanges by default)
- History formatted as: `"User: {query}\nAssistant: {answer}\n..."`
- Passed to Claude in system prompt for context-aware responses

### Configuration System

All settings centralized in `backend/config.py`:
- Uses `dotenv` for environment variables
- `Config` dataclass with defaults
- Single `config` instance imported across modules
- **Critical**: `ANTHROPIC_MODEL` is currently `"claude-sonnet-4-20250514"` - update if using different model

## Key Implementation Details

### Vector Search Resolution

When a course name is provided in search:
1. `VectorStore._resolve_course_name()` semantically searches `course_catalog`
2. Returns exact course title from best match
3. This title filters `course_content` search via ChromaDB's `where` clause
4. Enables queries like "Find MCP in intro course" to work with partial names

### ChromaDB Filter Building

`VectorStore._build_filter()` creates ChromaDB filters:
- Course only: `{"course_title": "exact_title"}`
- Lesson only: `{"lesson_number": 1}`
- Both: `{"$and": [{"course_title": "..."}, {"lesson_number": 1}]}`
- Neither: `None` (searches all content)

### Startup Document Loading

`app.py` startup event:
1. Checks if `../docs` folder exists
2. Calls `rag_system.add_course_folder(docs_path, clear_existing=False)`
3. Skips courses already in vector store (checks existing titles)
4. Only processes new `.txt`, `.pdf`, `.docx` files
5. Prints: `"Loaded {N} courses with {M} chunks"`

### Model Data Flow

The system uses Pydantic models (`models.py`) for type safety:
- **Lesson**: lesson_number, title, lesson_link
- **Course**: title (unique ID), course_link, instructor, lessons[]
- **CourseChunk**: content, course_title, lesson_number, chunk_index

These models ensure consistent data structure from document parsing → vector storage → API responses.

### Frontend-Backend Contract

API responses follow strict schema:
```python
QueryResponse {
    answer: str,           # Markdown-formatted answer
    sources: List[str],    # e.g., ["Course Title - Lesson 1"]
    session_id: str        # For maintaining conversation
}
```

Frontend (`script.js`) expects this exact structure and renders:
- `answer` via `marked.parse()` for markdown support
- `sources` in collapsible details element

## Common Gotchas

### ChromaDB Persistence
- Database stored in `backend/chroma_db/` (relative to backend dir)
- Collections persist across restarts
- **Must delete `chroma_db/` folder** to rebuild from scratch
- No migration system - structure changes require full rebuild

### Session History Context
- Only last 2 exchanges kept (configurable via `MAX_HISTORY`)
- Formatted as plain text in system prompt, not message array
- History passed on **every** AI generation call
- No session expiration - grows indefinitely in memory

### Tool Execution Pattern
- AI Generator handles tool execution internally via `_handle_tool_execution()`
- Tool results sent back to Claude in new message turn
- Final response extracted from second API call
- **Sources must be extracted** from `tool_manager.get_last_sources()` before reset

### Document Format Requirements
- First 3 lines MUST be: Course Title, Course Link, Course Instructor
- Lesson markers: `Lesson N: Title` (case-insensitive, N is integer)
- Optional Lesson Link on next line after lesson marker
- Breaks if format is not followed - will treat as unstructured content

### Embedding Model Consistency
- Uses `all-MiniLM-L6-v2` (384-dimensional embeddings)
- **Changing model requires rebuilding entire vector database**
- Model loaded via SentenceTransformer in ChromaDB embedding function
- No versioning - incompatible embeddings will cause poor results

## Working with the Codebase

### Adding New Search Filters
To add a new filter parameter (e.g., instructor):
1. Update `CourseSearchTool.get_tool_definition()` input schema
2. Add parameter to `CourseSearchTool.execute()`
3. Update `VectorStore.search()` signature
4. Modify `VectorStore._build_filter()` to handle new filter
5. Ensure metadata is stored in chunks during `add_course_content()`

### Changing Chunking Strategy
Chunking logic in `DocumentProcessor.chunk_text()`:
- Currently: sentence-based with overlap
- Preserves sentence boundaries (regex-based splitting)
- Calculates overlap by backing up N sentences
- Alternative strategies would require rewriting this method
- **Must rebuild vector DB** after changing chunk logic

### Modifying Claude System Prompt
System prompt in `AIGenerator.SYSTEM_PROMPT`:
- Static class variable (not rebuilt per call)
- Instructs on tool usage, response format, brevity
- History appended dynamically in `generate_response()`
- Changes affect all future queries immediately (no restart needed with `--reload`)

### API Endpoint Extension
To add new endpoints:
1. Add route in `app.py` with `@app.get()` or `@app.post()`
2. Define Pydantic request/response models
3. Access `rag_system` instance for RAG operations
4. Frontend can call via `fetch('/api/new-endpoint')`
5. Auto-documented at `/docs` (FastAPI Swagger UI)
