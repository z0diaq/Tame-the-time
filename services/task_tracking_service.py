"""
Task tracking service using SQLite database.
Tracks task completion status across days for statistics and progress monitoring.
"""

import sqlite3
import os
import uuid
from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple, Optional
from utils.logging import log_debug, log_error, log_info


class TaskTrackingService:
    """Service for tracking task completion across days using SQLite."""
    
    def __init__(self, db_path: str = None):
        """Initialize the task tracking service with database path."""
        if db_path is None:
            db_path = os.path.expanduser("~/.tame_the_time_tasks.db")
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create tasks table with UUID-based structure
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS task_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_uuid TEXT NOT NULL,  -- UUID to identify the task
                        activity_id TEXT NOT NULL,  -- UUID of the parent activity
                        task_name TEXT NOT NULL,  -- Human-readable task name for display
                        date TEXT NOT NULL,  -- YYYY-MM-DD format
                        timestamp TEXT NOT NULL,  -- ISO format with time
                        done_state BOOLEAN NOT NULL DEFAULT 0,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_task_entries_date 
                    ON task_entries(date)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_task_entries_task_uuid 
                    ON task_entries(task_uuid)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_task_entries_activity_id 
                    ON task_entries(activity_id)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_task_entries_done_state 
                    ON task_entries(done_state)
                ''')
                
                conn.commit()
                log_debug("Task tracking database initialized successfully")
                
        except sqlite3.Error as e:
            log_error(f"Failed to initialize task tracking database: {e}")
            raise
    
    def create_daily_task_entries(self, activities: List[Dict], target_date: date = None) -> int:
        """
        Create task entries for all tasks in activities for a specific date.
        Each task gets a unique UUID for identification.
        Returns the number of entries created.
        """
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.isoformat()
        timestamp = datetime.now().isoformat()
        entries_created = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for activity in activities:
                    activity_id = activity.get("id")
                    if not activity_id:
                        log_error(f"Activity '{activity.get('name', 'Unknown')}' has no ID, skipping")
                        continue
                        
                    tasks = activity.get("tasks", [])
                    
                    for task_name in tasks:
                        if not task_name.strip():
                            continue
                        
                        # Generate a unique UUID for this task instance
                        task_uuid = str(uuid.uuid4())
                        
                        # Check if entry already exists for this activity and task on this date
                        cursor.execute('''
                            SELECT id FROM task_entries 
                            WHERE activity_id = ? AND task_name = ? AND date = ?
                        ''', (activity_id, task_name, date_str))
                        
                        if cursor.fetchone() is None:
                            # Create new entry with UUID
                            cursor.execute('''
                                INSERT INTO task_entries 
                                (task_uuid, activity_id, task_name, date, timestamp, done_state)
                                VALUES (?, ?, ?, ?, ?, 0)
                            ''', (task_uuid, activity_id, task_name, date_str, timestamp))
                            entries_created += 1
                
                conn.commit()
                log_info(f"Created {entries_created} task entries for {date_str}")
                return entries_created
                
        except sqlite3.Error as e:
            log_error(f"Failed to create daily task entries: {e}")
            raise
    
    def mark_task_done(self, task_uuid: str, target_date: date = None) -> bool:
        """
        Mark a task as done for a specific date and update timestamp.
        Returns True if successful, False otherwise.
        """
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.isoformat()
        timestamp = datetime.now().isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE task_entries 
                    SET done_state = 1, timestamp = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE task_uuid = ? AND date = ?
                ''', (timestamp, task_uuid, date_str))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    log_debug(f"Marked task with UUID '{task_uuid}' as done for {date_str}")
                    return True
                else:
                    log_error(f"Task with UUID '{task_uuid}' not found for {date_str}")
                    return False
                    
        except sqlite3.Error as e:
            log_error(f"Failed to mark task as done: {e}")
            return False
    
    def mark_task_undone(self, task_uuid: str, target_date: date = None) -> bool:
        """
        Mark a task as not done for a specific date and update timestamp.
        Returns True if successful, False otherwise.
        """
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.isoformat()
        timestamp = datetime.now().isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE task_entries 
                    SET done_state = 0, timestamp = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE task_uuid = ? AND date = ?
                ''', (timestamp, task_uuid, date_str))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    log_debug(f"Marked task with UUID '{task_uuid}' as undone for {date_str}")
                    return True
                else:
                    log_error(f"Task with UUID '{task_uuid}' not found for {date_str}")
                    return False
                    
        except sqlite3.Error as e:
            log_error(f"Failed to mark task as undone: {e}")
            return False
    
    def add_new_task_entry(self, activity_id: str, task_name: str, target_date: date = None) -> str:
        """
        Add a new task entry for a specific date.
        Returns the task UUID if successful, None otherwise.
        """
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.isoformat()
        timestamp = datetime.now().isoformat()
        task_uuid = str(uuid.uuid4())
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if entry already exists for this activity and task on this date
                cursor.execute('''
                    SELECT task_uuid FROM task_entries 
                    WHERE activity_id = ? AND task_name = ? AND date = ?
                ''', (activity_id, task_name, date_str))
                
                existing = cursor.fetchone()
                if existing is not None:
                    log_debug(f"Task entry already exists for '{task_name}' on {date_str}")
                    return existing[0]  # Return existing UUID
                
                # Create new entry with UUID
                cursor.execute('''
                    INSERT INTO task_entries 
                    (task_uuid, activity_id, task_name, date, timestamp, done_state)
                    VALUES (?, ?, ?, ?, ?, 0)
                ''', (task_uuid, activity_id, task_name, date_str, timestamp))
                
                conn.commit()
                log_info(f"Added new task entry '{task_name}' with UUID '{task_uuid}' for {date_str}")
                return task_uuid
                
        except sqlite3.Error as e:
            log_error(f"Failed to add new task entry: {e}")
            return None
    
    def remove_task_entries(self, task_uuid: str) -> int:
        """
        Remove all entries for a specific task UUID across all dates.
        Returns the number of entries removed.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count entries to be removed
                cursor.execute('''
                    SELECT COUNT(*) FROM task_entries 
                    WHERE task_uuid = ?
                ''', (task_uuid,))
                
                count = cursor.fetchone()[0]
                
                if count > 0:
                    # Remove entries
                    cursor.execute('''
                        DELETE FROM task_entries 
                        WHERE task_uuid = ?
                    ''', (task_uuid,))
                    
                    conn.commit()
                    log_info(f"Removed {count} entries for task UUID '{task_uuid}'")
                
                return count
                
        except sqlite3.Error as e:
            log_error(f"Failed to remove task entries: {e}")
            return 0
    
    def get_task_done_states(self, target_date: date = None) -> Dict[str, bool]:
        """
        Get done states for all tasks on a specific date.
        Returns dict with task_uuid as key and done_state as value.
        """
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT task_uuid, done_state 
                    FROM task_entries 
                    WHERE date = ?
                ''', (date_str,))
                
                results = {}
                for row in cursor.fetchall():
                    task_uuid, done_state = row
                    results[task_uuid] = bool(done_state)
                
                return results
                
        except sqlite3.Error as e:
            log_error(f"Failed to get task done states: {e}")
            return {}
    
    def get_all_unique_tasks(self) -> List[Dict[str, str]]:
        """
        Get all unique tasks from database with their metadata.
        Returns list of dictionaries with task_uuid, activity_id, and task_name.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT DISTINCT task_uuid, activity_id, task_name 
                    FROM task_entries 
                    ORDER BY task_name
                ''')
                
                results = []
                for row in cursor.fetchall():
                    task_uuid, activity_id, task_name = row
                    results.append({
                        'task_uuid': task_uuid,
                        'activity_id': activity_id,
                        'task_name': task_name
                    })
                
                return results
                
        except sqlite3.Error as e:
            log_error(f"Failed to get unique tasks: {e}")
            return []
    
    def get_task_statistics(self, task_list: List[str], 
                          grouping: str = "Day", ignore_weekends: bool = False,
                          limit: int = 10) -> Dict[str, List[Dict]]:
        """
        Get statistics for specified tasks.
        
        Args:
            task_list: List of task UUIDs
            grouping: "Day" or "Week"
            ignore_weekends: Skip Saturday and Sunday data
            limit: Maximum number of data points to return
        
        Returns:
            Dict with task UUIDs as keys and list of data points as values
        """
        if not task_list:
            return {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                results = {}
                
                for task_uuid in task_list:
                    if grouping == "Day":
                        data = self._get_daily_statistics(cursor, task_uuid, 
                                                        ignore_weekends, limit)
                    else:  # Week
                        data = self._get_weekly_statistics(cursor, task_uuid, 
                                                         ignore_weekends, limit)
                    
                    results[task_uuid] = data
                
                return results
                
        except sqlite3.Error as e:
            log_error(f"Failed to get task statistics: {e}")
            return {}
    
    def _get_daily_statistics(self, cursor, task_uuid: str,
                            ignore_weekends: bool, limit: int) -> List[Dict]:
        """Get daily statistics for a task."""
        # Get last N days of data
        end_date = date.today()
        start_date = end_date - timedelta(days=limit * 2)  # Get extra days in case of weekends
        
        cursor.execute('''
            SELECT date, done_state 
            FROM task_entries 
            WHERE task_uuid = ? 
            AND date >= ? AND date <= ?
            ORDER BY date DESC
        ''', (task_uuid, start_date.isoformat(), end_date.isoformat()))
        
        data = []
        for row in cursor.fetchall():
            date_str, done_state = row
            task_date = datetime.fromisoformat(date_str).date()
            
            # Skip weekends if requested
            if ignore_weekends and task_date.weekday() >= 5:  # Saturday=5, Sunday=6
                continue
            
            data.append({
                'date': date_str,
                'completed': bool(done_state),
                'display_label': task_date.strftime('%m-%d')
            })
            
            if len(data) >= limit:
                break
        
        return data[:limit]
    
    def _get_weekly_statistics(self, cursor, task_uuid: str,
                             ignore_weekends: bool, limit: int) -> List[Dict]:
        """Get weekly statistics for a task."""
        # Get data for last N weeks
        end_date = date.today()
        start_date = end_date - timedelta(weeks=limit + 2)  # Get extra weeks for safety
        
        cursor.execute('''
            SELECT date, done_state 
            FROM task_entries 
            WHERE task_uuid = ? 
            AND date >= ? AND date <= ?
            ORDER BY date
        ''', (task_uuid, start_date.isoformat(), end_date.isoformat()))
        
        # Group by week (Monday to Sunday)
        weekly_data = {}
        for row in cursor.fetchall():
            date_str, done_state = row
            task_date = datetime.fromisoformat(date_str).date()
            
            # Skip weekends if requested
            if ignore_weekends and task_date.weekday() >= 5:
                continue
            
            # Get Monday of the week
            monday = task_date - timedelta(days=task_date.weekday())
            week_key = monday.isoformat()
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {'completed_count': 0, 'total_count': 0}
            
            weekly_data[week_key]['total_count'] += 1
            if done_state:
                weekly_data[week_key]['completed_count'] += 1
        
        # Convert to list and sort by week
        data = []
        for week_start, stats in sorted(weekly_data.items(), reverse=True):
            monday = datetime.fromisoformat(week_start).date()
            sunday = monday + timedelta(days=6)
            
            data.append({
                'week_start': week_start,
                'completed_count': stats['completed_count'],
                'total_count': stats['total_count'],
                'completion_rate': stats['completed_count'] / stats['total_count'] if stats['total_count'] > 0 else 0,
                'display_label': f"{monday.strftime('%m-%d')} - {sunday.strftime('%m-%d')}"
            })
            
            if len(data) >= limit:
                break
        
        return data[:limit]
    
    def get_task_info_by_uuid(self, task_uuid: str) -> Optional[Dict[str, str]]:
        """
        Get task information by UUID.
        Returns dict with task_uuid, activity_id, and task_name, or None if not found.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT DISTINCT task_uuid, activity_id, task_name 
                    FROM task_entries 
                    WHERE task_uuid = ?
                    LIMIT 1
                ''', (task_uuid,))
                
                row = cursor.fetchone()
                if row:
                    task_uuid, activity_id, task_name = row
                    return {
                        'task_uuid': task_uuid,
                        'activity_id': activity_id,
                        'task_name': task_name
                    }
                return None
                
        except sqlite3.Error as e:
            log_error(f"Failed to get task info by UUID: {e}")
            return None
    
    def get_task_uuids_by_activity_and_name(self, activity_id: str, task_name: str, target_date: date = None) -> List[str]:
        """
        Get task UUIDs for a specific activity and task name on a given date.
        Returns list of task UUIDs.
        """
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT task_uuid 
                    FROM task_entries 
                    WHERE activity_id = ? AND task_name = ? AND date = ?
                ''', (activity_id, task_name, date_str))
                
                return [row[0] for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            log_error(f"Failed to get task UUIDs: {e}")
            return []
    
    def check_duplicate_task_names(self, activities: List[Dict]) -> List[Tuple[str, List[str]]]:
        """
        Check for duplicate task names within activities.
        Returns list of (activity_name, duplicate_task_names) tuples.
        """
        duplicates = []
        
        for activity in activities:
            activity_name = activity.get("name", "")
            tasks = activity.get("tasks", [])
            
            # Find duplicates
            seen = set()
            duplicate_tasks = set()
            
            for task in tasks:
                task = task.strip()
                if task in seen:
                    duplicate_tasks.add(task)
                else:
                    seen.add(task)
            
            if duplicate_tasks:
                duplicates.append((activity_name, list(duplicate_tasks)))
        
        return duplicates
