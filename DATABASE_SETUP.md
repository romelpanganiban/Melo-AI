# Database Migration Guide for Melo-AI

## Overview

Melo-AI now uses a **relational database** instead of JSON files for better scalability, querying, and support for complex features like RAG, document storage, and embeddings.

### Supported Databases

1. **SQLite** (Development) ✅
   - Easier setup
   - File-based storage
   - No server needed
   - Perfect for local development

2. **PostgreSQL** (Production) ✅
   - Better performance
   - Concurrent access
   - Advanced features
   - Scalable

---

## Quick Start: SQLite (Recommended for Dev)

### 1. Update Backend

```bash
cd backend
pip install -r requirements.txt
```

### 2. Create `.env` File

Copy `backend/.env.example` to `backend/.env`:

```bash
# Default SQLite configuration (included in .env.example)
DATABASE_URL=sqlite:///./melo_ai.db
```

### 3. Database Initialization

Database tables are created automatically when the backend starts. No manual setup needed!

```bash
python -m uvicorn main:app --reload
```

You'll see:
```
INFO: Initializing database
INFO: Database initialized successfully
```

### 4. Verify Database

Check if database file was created:
```bash
ls -la melo_ai.db
```

---

## PostgreSQL Setup (Production)

### 1. Install PostgreSQL

**Windows:**
- Download from [postgresql.org](https://www.postgresql.org/download/windows/)
- Run installer
- Remember the password you set

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE melo_ai;
CREATE USER melo_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE melo_ai TO melo_user;
\q
```

### 3. Update `.env`

Edit `backend/.env`:

```bash
# PostgreSQL connection string
DATABASE_URL=postgresql://melo_user:secure_password_here@localhost:5432/melo_ai
```

Format: `postgresql://[user]:[password]@[host]:[port]/[database]`

### 4. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

psycopg2 (PostgreSQL driver) is in requirements.txt

### 5. Start Backend

```bash
python -m uvicorn main:app --reload
```

Database tables will be created automatically on first startup.

---

## Database Schema

### Tables

#### `sessions`
Stores chat sessions
```sql
- id (UUID, Primary Key)
- title (String)
- created_at (DateTime)
- updated_at (DateTime)
```

#### `messages`
Stores chat messages
```sql
- id (Integer, Primary Key)
- session_id (UUID, Foreign Key)
- role (String: "user" or "assistant")
- content (Text)
- created_at (DateTime)
- tokens_used (Integer, nullable)
```

#### `settings`
Stores application settings
```sql
- id (Integer, Primary Key = 1)
- model_name (String)
- provider (String)
- temperature (Float)
- top_p (Float)
- top_k (Integer)
- system_prompt (Text)
- updated_at (DateTime)
```

#### `documents`
Stores uploaded documents (for Knowledge Base)
```sql
- id (UUID, Primary Key)
- session_id (UUID, Foreign Key, nullable)
- filename (String)
- file_type (String: "pdf", "docx", "txt")
- content (Text)
- chunk_count (Integer)
- created_at (DateTime)
- updated_at (DateTime)
```

#### `document_chunks`
Stores text chunks from documents (for RAG)
```sql
- id (UUID, Primary Key)
- document_id (UUID, Foreign Key)
- chunk_index (Integer)
- content (Text)
- embedding (Text, nullable - JSON array)
- tokens (Integer)
- created_at (DateTime)
```

---

## RAG Setup

Melo-AI already has the database tables needed for Knowledge Base and RAG storage, but the full retrieval pipeline still needs to be installed and wired up.

### What You Already Have

- `documents` table for uploaded files
- `document_chunks` table for chunked text and embeddings
- Backend service and API structure ready for document features

### What You Still Need To Install

Install these backend packages for RAG:

```bash
cd backend
pip install qdrant-client sentence-transformers pypdf python-docx
```

Recommended local vector store:

- Qdrant
- Run locally with Docker or a local binary

### What Each Package Is For

- `qdrant-client` - store and search embeddings
- `sentence-transformers` - generate vector embeddings
- `pypdf` - extract text from PDF files
- `python-docx` - extract text from DOCX files

### RAG Pipeline Still To Build

1. Upload PDF, DOCX, or TXT files
2. Extract text from the file
3. Split text into chunks
4. Generate embeddings for each chunk
5. Store chunks in Qdrant and the database
6. Retrieve top matching chunks during chat
7. Inject retrieved context into the Ollama prompt
8. Show source references in the response

### Offline Note

If the machine has no internet, install everything on another machine first and copy:

- Python wheels or a prepared virtual environment
- Qdrant locally
- Any embedding model files you plan to use

---

## Migration from JSON

### Automatic Migration

The old JSON files are NOT automatically deleted. Data stays in JSON for reference.

To manually migrate old data:

```bash
# This is optional - database starts fresh
# Old data in backend/data/ remains untouched
# You can delete JSON files after verifying everything works:

rm backend/data/chat_history.json
rm backend/data/sessions.json
rm backend/data/settings.json
```

**Old files:** `backend/data/*.json`
**New database:** `backend/melo_ai.db` (SQLite) or PostgreSQL

---

## Environment Variables

### Development (SQLite)
```bash
DATABASE_URL=sqlite:///./melo_ai.db
DEBUG_SQL=false
```

### Production (PostgreSQL)
```bash
DATABASE_URL=postgresql://user:password@hostname:5432/dbname
DEBUG_SQL=false  # Enable to see SQL queries in logs
```

---

## Testing

Run database tests:

```bash
cd backend

# Test models
pytest tests/test_database_models.py -v

# Test repositories
pytest tests/test_database_repositories.py -v

# Test integration
pytest tests/test_database_integration.py -v

# Run all tests
pytest tests/ -v
```

All tests use in-memory SQLite, so no setup needed.

---

## Troubleshooting

### Issue: "No such table: sessions"
**Cause:** Database not initialized
**Solution:**
```bash
python -m uvicorn main:app --reload
# Wait for "Database initialized successfully"
```

### Issue: "connection refused" (PostgreSQL)
**Cause:** PostgreSQL server not running
**Solution:**
```bash
# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql  # macOS
# Windows: Start from Services app
```

### Issue: "FATAL: Ident authentication failed for user"
**Cause:** PostgreSQL authentication issue
**Solution:**
```bash
# Use password authentication instead
# Edit /etc/postgresql/*/main/pg_hba.conf
# Change "ident" to "md5"
sudo systemctl restart postgresql
```

### Issue: "permission denied for schema public"
**Cause:** User lacks permissions
**Solution:**
```bash
psql -U postgres -d melo_ai
GRANT ALL ON SCHEMA public TO melo_user;
```

### Enable SQL Query Logging
```bash
# Set in .env
DEBUG_SQL=true

# Restart backend - all SQL queries will appear in logs
```

---

## Database Operations

### View Data (SQLite)

```bash
# Install sqlite3 CLI
sqlite3 melo_ai.db

# View tables
.tables

# View sessions
SELECT * FROM sessions;

# View messages
SELECT * FROM messages;

# Exit
.quit
```

### View Data (PostgreSQL)

```bash
psql -U melo_user -d melo_ai

# View tables
\dt

# View sessions
SELECT * FROM sessions;

# Exit
\q
```

### Backup Database

**SQLite:**
```bash
cp melo_ai.db melo_ai.db.backup
```

**PostgreSQL:**
```bash
pg_dump -U melo_user -d melo_ai > melo_ai_backup.sql
```

### Restore Database

**SQLite:**
```bash
cp melo_ai.db.backup melo_ai.db
```

**PostgreSQL:**
```bash
psql -U melo_user -d melo_ai < melo_ai_backup.sql
```

---

## Performance Optimization

### SQLite (Development)

SQLite has built-in optimizations for development use.

### PostgreSQL (Production)

Add indexes for common queries:
```sql
-- Already created by SQLAlchemy models
-- Check existing indexes:
SELECT * FROM pg_indexes WHERE tablename = 'messages';
```

Connection pooling (optional, already configured):
```python
# In database/connection.py - uses SQLAlchemy pooling by default
```

---

## Next Steps

1. ✅ Database initialized
2. ⏭️ **Phase 8:** Knowledge Base (PDF/DOCX upload)
3. ⏭️ **Phase 9:** RAG with vector search
4. ⏭️ **Phase 10:** Coding assistant

---

## API Changes (Backward Compatible)

The API endpoints remain the same! The database change is internal only.

- `/chat` - Still works
- `/history/{session_id}` - Still works
- `/sessions` - Still works
- `/settings` - Still works

No frontend changes needed! ✨

---

## Documentation

- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [SQLite Docs](https://www.sqlite.org/docs.html)
