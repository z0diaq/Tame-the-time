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

---

## Database Entry Creation Timing (2025-11-19)

**Update Status:** Enhanced  
**Priority:** Consistency

### Background

During day rollover (when current time passes the `day_start` hour), the application creates new daily task tracking entries in the database. Previously, these entries were created automatically during the rollover process.

### Enhancement: Deferred Entry Creation

With the implementation of **Interactive Day Rollover** (see ADR-013), database entry creation timing was refined to ensure consistency with user choices.

#### Previous Behavior

**Automatic Entry Creation:**
```python
def _handle_day_rollover(app, now: datetime) -> None:
    # 1. Load new schedule if exists (automatic)
    schedule_loaded = _check_and_load_new_day_schedule(app, now)
    
    # 2. Reset timeline
    _reset_timeline_to_top(app, now)
    
    # 3. Reset task status (if no new schedule)
    if not schedule_loaded:
        _reset_all_task_completion_status(app)
    
    # 4. Create DB entries immediately
    _create_new_day_task_entries(app)  # ← Created before user choice
```

**Problem:**
- Database entries created before user decides on schedule
- If user chooses to load new schedule, entries might be for wrong tasks
- Timing inconsistency between schedule loading and DB entry creation

#### Enhanced Behavior

**Deferred Entry Creation:**
```python
def _handle_day_rollover(app, now: datetime) -> None:
    # 1. Ask user about new schedule (interactive dialog, pauses updates)
    schedule_loaded = _check_and_load_new_day_schedule(app, now)
    
    # 2. Reset timeline
    _reset_timeline_to_top(app, now)
    
    # 3. Reset task status (if user chose to keep current schedule)
    if not schedule_loaded:
        _reset_all_task_completion_status(app)
    
    # 4. Create DB entries AFTER user choice
    _create_new_day_task_entries(app)  # ← Created after user decision
```

**Benefits:**
- Database entries match the schedule user chose to use
- No orphaned entries for tasks from unloaded schedules
- Clear temporal ordering: detect → ask → act → persist
- Consistent with user expectations

### Implementation Details

#### Timeline Pause During Dialog

**File:** `ui/app_ui_loop.py`

When the day rollover dialog is shown:

1. **Pause Flag Set:**
   ```python
   app._day_rollover_dialog_active = True
   ```

2. **Updates Skip All Processing:**
   ```python
   def update_ui(app):
       if getattr(app, '_day_rollover_dialog_active', False):
           app.after(UIConstants.UI_UPDATE_INTERVAL_MS, lambda: update_ui(app))
           return  # Skip updates, including DB operations
   ```

3. **Dialog Shown and Waits:**
   ```python
   user_wants_new_schedule = show_day_rollover_dialog(app, weekday, path)
   ```

4. **Action Taken Based on Choice:**
   ```python
   if user_wants_new_schedule:
       _load_new_schedule_and_replace_cards(app, path)
   ```

5. **Pause Flag Cleared:**
   ```python
   app._day_rollover_dialog_active = False
   ```

6. **DB Entries Created:**
   ```python
   _create_new_day_task_entries(app)  # Now creates for correct schedule
   ```

#### Database Entry Creation

**File:** `ui/app_ui_loop.py`

```python
def _create_new_day_task_entries(app) -> None:
    """
    Create new daily task tracking entries in the database for the new day.
    
    This function is called AFTER user makes their day rollover choice,
    ensuring entries are created for the schedule the user decided to use.
    """
    try:
        if hasattr(app, 'task_tracking_service') and app.task_tracking_service:
            day_start = getattr(app, 'day_start', 0)
            entries_created = app.task_tracking_service.create_daily_task_entries(
                app.schedule, 
                day_start_hour=day_start
            )
            if entries_created > 0:
                log_info(f"Created {entries_created} new task entries for new day")
    except Exception as e:
        log_error(f"Failed to create new day task entries: {e}")
```

### User Experience Benefits

✅ **Database Integrity**
- Entries always match the active schedule
- No cleanup needed for incorrect entries
- One-to-one correspondence between cards and DB entries

✅ **Logical Consistency**
- Database reflects user's actual choice
- No speculative writes before decision
- Clear cause-and-effect sequence

✅ **Performance**
- No redundant DB operations
- Single write operation after choice
- No need to delete/recreate entries

### Technical Guarantees

**Order of Operations (Guaranteed):**

1. Day rollover detected
2. UI updates paused (`_day_rollover_dialog_active = True`)
3. Dialog shown to user (modal, blocking)
4. User makes choice (dialog waits)
5. Choice executed (load new or keep current)
6. UI updates resumed (`_day_rollover_dialog_active = False`)
7. Database entries created for chosen schedule
8. Status bar updated to reflect new entries

**Error Handling:**

```python
try:
    # Show dialog and get choice
    user_wants_new_schedule = show_day_rollover_dialog(...)
    
    if user_wants_new_schedule:
        return _load_new_schedule_and_replace_cards(app, schedule_path)
finally:
    # ALWAYS clear pause flag, even on error
    app._day_rollover_dialog_active = False
```

This ensures:
- UI never permanently freezes
- Database operations always proceed
- Application remains responsive even on errors

### Backward Compatibility

✅ **Fully compatible**

- If no weekday schedule file exists, no dialog shown
- Database entries created immediately (as before)
- Existing `day_start` logic unchanged
- No migration needed for existing databases

### Related ADRs

- **ADR-013**: Day Start Configuration (interactive day rollover implementation)
- **ADR-010**: Configuration Management Strategy (schedule file detection)
