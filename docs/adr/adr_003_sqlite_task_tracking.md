# ADR-003: SQLite for Task Tracking Database

**Title:** SQLite for Task Tracking Database with UUID-based Task Identification  
**Status:** Accepted  
**Date:** 2025-08-03  
**Updated:** 2025-08-07  

## Context

The application needed persistent storage for task completion tracking across days to enable:

- Daily task progress monitoring
- Historical statistics and charts
- Progress analytics with day/week grouping
- Data persistence between application sessions
- Support for ~20 tasks per day with minimal overhead

Requirements:
- Lightweight, embedded database
- No external database server setup
- ACID compliance for data integrity
- SQL query capabilities for statistics
- Cross-platform file-based storage

## Decision

We implemented SQLite as the task tracking database with a refined two-table schema:

```sql
-- Task-to-UUID mapping table (stores task definitions)
CREATE TABLE task_to_uuid (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_uuid TEXT NOT NULL UNIQUE,     -- UUID to identify the task
    activity_id TEXT NOT NULL,          -- UUID of the parent activity
    task_name TEXT NOT NULL,            -- Human-readable task name
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(activity_id, task_name)      -- Ensure unique task names per activity
);

-- Task completion entries (stores daily completion data)
CREATE TABLE task_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_uuid TEXT NOT NULL,            -- Reference to task_to_uuid.task_uuid
    date TEXT NOT NULL,                 -- YYYY-MM-DD format
    timestamp TEXT NOT NULL,            -- ISO format with time
    done_state BOOLEAN NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_uuid) REFERENCES task_to_uuid(task_uuid)
);

-- Performance indexes
CREATE INDEX idx_task_entries_date ON task_entries(date);
CREATE INDEX idx_task_entries_task_uuid ON task_entries(task_uuid);
CREATE INDEX idx_task_entries_done_state ON task_entries(done_state);
CREATE INDEX idx_task_to_uuid_activity_id ON task_to_uuid(activity_id);
CREATE INDEX idx_task_to_uuid_task_name ON task_to_uuid(task_name);
```

**Implementation Details:**
- Database stored in user home directory (`~/.tame_the_time_tasks.db`)
- Service layer abstraction (`TaskTrackingService`)
- Two-table design for separation of concerns:
  - `task_to_uuid`: Maps task names to UUIDs (task definitions)
  - `task_entries`: Stores daily completion data by UUID
- **Deferred Database Writes**: Tasks are only saved to database when schedule is saved
- **Unsaved Task Protection**: UI prevents marking unsaved tasks as done with warning
- UUID-based task identification ensures uniqueness and data integrity
- Automatic daily entry creation only for saved tasks
- Optimized queries for statistics generation using UUIDs

## Consequences

**Positive:**
- Zero-configuration embedded database
- Built into Python standard library
- Excellent performance for application scale (~20 tasks/day)
- ACID compliance ensures data integrity
- SQL queries enable complex statistics
- File-based storage is portable and backup-friendly
- Supports concurrent reads efficiently

**Negative:**
- Single-writer limitation (not relevant for single-user desktop app)
- Manual schema migration management required
- No built-in data validation (handled in application layer)

## Alternatives

1. **JSON Files**: Simple but no query capabilities, poor performance for statistics
2. **CSV Files**: Easy to read but no relational capabilities, manual parsing overhead
3. **PostgreSQL/MySQL**: Overkill requiring external server setup for desktop app
4. **NoSQL (MongoDB)**: Additional dependency, unnecessary for structured task data
