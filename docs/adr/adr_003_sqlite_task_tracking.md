# ADR-003: SQLite for Task Tracking Database

**Title:** SQLite for Task Tracking Database  
**Status:** Accepted  
**Date:** 2025-08-03  

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

We implemented SQLite as the task tracking database with the following schema:

```sql
CREATE TABLE task_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_name TEXT NOT NULL,
    task_name TEXT NOT NULL,
    date TEXT NOT NULL,           -- YYYY-MM-DD format
    timestamp TEXT NOT NULL,      -- ISO format with time
    done_state BOOLEAN NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Performance indexes
CREATE INDEX idx_task_entries_date ON task_entries(date);
CREATE INDEX idx_task_entries_activity_task ON task_entries(activity_name, task_name);
CREATE INDEX idx_task_entries_done_state ON task_entries(done_state);
```

**Implementation Details:**
- Database stored in user home directory (`~/.tame_the_time_tasks.db`)
- Service layer abstraction (`TaskTrackingService`)
- Automatic daily entry creation at app launch
- Optimized queries for statistics generation

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
