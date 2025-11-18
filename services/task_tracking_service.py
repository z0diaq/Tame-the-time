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
from utils.time_utils import TimeUtils


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
                
                # Create task_to_uuid mapping table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS task_to_uuid (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_uuid TEXT NOT NULL UNIQUE,  -- UUID to identify the task
                        activity_id TEXT NOT NULL,  -- UUID of the parent activity
                        task_name TEXT NOT NULL,  -- Human-readable task name
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(activity_id, task_name)  -- Ensure unique task names per activity
                    )
                ''')
                
                # Create simplified task_entries table (only UUID and completion data)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS task_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_uuid TEXT NOT NULL,  -- Reference to task_to_uuid.task_uuid
                        date TEXT NOT NULL,  -- YYYY-MM-DD format
                        timestamp TEXT NOT NULL,  -- ISO format with time
                        done_state BOOLEAN NOT NULL DEFAULT 0,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (task_uuid) REFERENCES task_to_uuid(task_uuid)
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
                    CREATE INDEX IF NOT EXISTS idx_task_entries_done_state 
                    ON task_entries(done_state)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_task_to_uuid_activity_id 
                    ON task_to_uuid(activity_id)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_task_to_uuid_task_name 
                    ON task_to_uuid(task_name)
                ''')
                
                conn.commit()
                log_debug("Task tracking database initialized successfully")
                
        except sqlite3.Error as e:
            log_error(f"Failed to initialize task tracking database: {e}")
            raise
    
    def create_daily_task_entries(self, activities: List[Dict], target_date: date = None, day_start_hour: int = 0) -> int:
        """
        Create task entries for all saved tasks for a specific date.
        Only creates entries for tasks that exist in the task_to_uuid table.
        Returns the number of entries created.
        
        Args:
            activities: List of activity dictionaries containing tasks
            target_date: Date to create entries for (uses logical date if None)
            day_start_hour: Hour when day starts (0-23), used for logical date calculation
        """
        if target_date is None:
            target_date = TimeUtils.get_logical_date(datetime.now(), day_start_hour)
        
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
                    
                    for task in tasks:
                        # Handle both string and object task formats
                        if isinstance(task, str):
                            task_name = task.strip()
                            task_uuid = None  # Will be looked up from database
                        elif isinstance(task, dict) and "name" in task:
                            task_name = task["name"].strip()
                            task_uuid = task.get("uuid")  # Use UUID from YAML if available
                        else:
                            log_error(f"Invalid task format: {task}")
                            continue
                        
                        if not task_name:
                            continue
                        
                        # If no UUID from YAML, get from database (for backward compatibility)
                        if not task_uuid:
                            task_uuid = self.get_task_uuid(activity_id, task_name)
                            if not task_uuid:
                                log_debug(f"Task '{task_name}' not found in database, skipping daily entry creation")
                                continue
                        
                        # Check if entry already exists for this task on this date
                        cursor.execute('''
                            SELECT id FROM task_entries 
                            WHERE task_uuid = ? AND date = ?
                        ''', (task_uuid, date_str))
                        
                        if cursor.fetchone() is None:
                            # Create new entry
                            cursor.execute('''
                                INSERT INTO task_entries 
                                (task_uuid, date, timestamp, done_state)
                                VALUES (?, ?, ?, 0)
                            ''', (task_uuid, date_str, timestamp))
                            entries_created += 1
                
                conn.commit()
                log_info(f"Created {entries_created} task entries for {date_str}")
                return entries_created
                
        except sqlite3.Error as e:
            log_error(f"Failed to create daily task entries: {e}")
            raise
    
    def mark_task_done(self, task_uuid: str, target_date: date = None, day_start_hour: int = 0) -> bool:
        """
        Mark a task as done for a specific date and update timestamp.
        Returns True if successful, False otherwise.
        
        Args:
            task_uuid: UUID of the task to mark as done
            target_date: Date to mark task for (uses logical date if None)
            day_start_hour: Hour when day starts (0-23), used for logical date calculation
        """
        if target_date is None:
            target_date = TimeUtils.get_logical_date(datetime.now(), day_start_hour)
        
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
    
    def mark_task_undone(self, task_uuid: str, target_date: date = None, day_start_hour: int = 0) -> bool:
        """
        Mark a task as not done for a specific date and update timestamp.
        Returns True if successful, False otherwise.
        
        Args:
            task_uuid: UUID of the task to mark as undone
            target_date: Date to mark task for (uses logical date if None)
            day_start_hour: Hour when day starts (0-23), used for logical date calculation
        """
        if target_date is None:
            target_date = TimeUtils.get_logical_date(datetime.now(), day_start_hour)
        
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
    
    def add_new_task_entry(self, activity_id: str, task_name: str, task_uuid: str = None, target_date: date = None, day_start_hour: int = 0) -> str:
        """
        Add a new task entry for a specific date.
        First registers the task in task_to_uuid table (uses provided UUID or creates new one if needed),
        then creates entry in task_entries.
        
        Args:
            activity_id: The activity's UUID
            task_name: The task's name
            task_uuid: Optional existing UUID for the task (if already assigned)
            target_date: The date for the entry (uses logical date if None)
            day_start_hour: Hour when day starts (0-23), used for logical date calculation
        
        Returns the task UUID if successful, None otherwise.
        """
        if target_date is None:
            target_date = TimeUtils.get_logical_date(datetime.now(), day_start_hour)
        
        date_str = target_date.isoformat()
        timestamp = datetime.now().isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if task already exists in task_to_uuid table
                cursor.execute('''
                    SELECT task_uuid FROM task_to_uuid 
                    WHERE activity_id = ? AND task_name = ?
                ''', (activity_id, task_name))
                
                result = cursor.fetchone()
                if result:
                    existing_uuid = result[0]
                    if task_uuid and task_uuid != existing_uuid:
                        log_debug(f"Task '{task_name}' UUID mismatch: provided={task_uuid}, DB={existing_uuid}. Using DB UUID.")
                    task_uuid = existing_uuid
                    log_debug(f"Found existing task UUID '{task_uuid}' for '{task_name}'")
                else:
                    # Task doesn't exist, register it with provided or new UUID
                    if not task_uuid:
                        task_uuid = str(uuid.uuid4())
                    cursor.execute('''
                        INSERT INTO task_to_uuid (task_uuid, activity_id, task_name)
                        VALUES (?, ?, ?)
                    ''', (task_uuid, activity_id, task_name))
                    log_info(f"Registered new task '{task_name}' with UUID '{task_uuid}'")
                
                # Check if entry already exists for this task UUID on this date
                cursor.execute('''
                    SELECT task_uuid FROM task_entries 
                    WHERE task_uuid = ? AND date = ?
                ''', (task_uuid, date_str))
                
                existing = cursor.fetchone()
                if existing is not None:
                    log_debug(f"Task entry already exists for '{task_name}' on {date_str}")
                    return existing[0]  # Return existing UUID
                
                # Create new entry with UUID (only task_uuid, date, timestamp, done_state)
                cursor.execute('''
                    INSERT INTO task_entries 
                    (task_uuid, date, timestamp, done_state)
                    VALUES (?, ?, ?, 0)
                ''', (task_uuid, date_str, timestamp))
                
                conn.commit()
                log_info(f"Added new task entry '{task_name}' with UUID '{task_uuid}' for {date_str}")
                return task_uuid
                
        except sqlite3.Error as e:
            log_error(f"Failed to add new task entry: {e}")
            return None
       
    def get_task_done_states(self, target_date: date = None, day_start_hour: int = 0) -> Dict[str, bool]:
        """
        Get done states for all tasks on a specific date.
        Returns dict with task_uuid as key and done_state as value.
        
        Args:
            target_date: Date to check tasks for (uses logical date if None)
            day_start_hour: Hour when day starts (0-23), used for logical date calculation
        """
        if target_date is None:
            target_date = TimeUtils.get_logical_date(datetime.now(), day_start_hour)
        
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
        Get all unique tasks from task_to_uuid table with their metadata.
        Returns list of dictionaries with task_uuid, activity_id, and task_name.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT task_uuid, activity_id, task_name 
                    FROM task_to_uuid 
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
                          limit: int = 10, day_start_hour: int = 0) -> Dict[str, List[Dict]]:
        """
        Get statistics for specified tasks.
        
        Args:
            task_list: List of task UUIDs
            grouping: "Day", "Week", "Month", or "Year"
            ignore_weekends: Skip Saturday and Sunday data
            limit: Maximum number of data points to return
            day_start_hour: Hour when day starts (0-23), used for logical date calculation
        
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
                                                        ignore_weekends, limit, day_start_hour)
                    elif grouping == "Week":
                        data = self._get_weekly_statistics(cursor, task_uuid, 
                                                         ignore_weekends, limit, day_start_hour)
                    elif grouping == "Month":
                        data = self._get_monthly_statistics(cursor, task_uuid, 
                                                          ignore_weekends, limit, day_start_hour)
                    else:  # Year
                        data = self._get_yearly_statistics(cursor, task_uuid, 
                                                         ignore_weekends, limit, day_start_hour)
                    
                    results[task_uuid] = data
                
                return results
                
        except sqlite3.Error as e:
            log_error(f"Failed to get task statistics: {e}")
            return {}
    
    def _get_daily_statistics(self, cursor, task_uuid: str,
                            ignore_weekends: bool, limit: int, day_start_hour: int) -> List[Dict]:
        """Get daily statistics for a task."""
        # Get last N days of data
        end_date = TimeUtils.get_logical_date(datetime.now(), day_start_hour)
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
                             ignore_weekends: bool, limit: int, day_start_hour: int) -> List[Dict]:
        """Get weekly statistics for a task."""
        # Get last N weeks of data
        end_date = TimeUtils.get_logical_date(datetime.now(), day_start_hour)
        start_date = end_date - timedelta(weeks=limit * 2)  # Get extra weeks
        
        cursor.execute('''
            SELECT date, done_state 
            FROM task_entries 
            WHERE task_uuid = ? 
            AND date >= ? AND date <= ?
            ORDER BY date DESC
        ''', (task_uuid, start_date.isoformat(), end_date.isoformat()))
        
        # Group by week
        weekly_data = {}
        for row in cursor.fetchall():
            date_str, done_state = row
            task_date = datetime.fromisoformat(date_str).date()
            
            # Skip weekends if requested
            if ignore_weekends and task_date.weekday() >= 5:  # Saturday=5, Sunday=6
                continue
            
            # Get Monday of the week (ISO week starts on Monday)
            week_start = task_date - timedelta(days=task_date.weekday())
            week_key = week_start.isoformat()
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {'completed_days': 0, 'total_days': 0}
            
            weekly_data[week_key]['total_days'] += 1
            if done_state:
                weekly_data[week_key]['completed_days'] += 1
        
        # Convert to list format
        data = []
        for week_start_str in sorted(weekly_data.keys(), reverse=True):
            week_start = datetime.fromisoformat(week_start_str).date()
            week_data = weekly_data[week_start_str]
            
            completion_rate = (week_data['completed_days'] / week_data['total_days'] 
                             if week_data['total_days'] > 0 else 0)
            
            data.append({
                'date': week_start_str,
                'completed': completion_rate,
                'display_label': f"Week {week_start.strftime('%m-%d')}"
            })
            
            if len(data) >= limit:
                break
        
        return data[:limit]

    def _get_monthly_statistics(self, cursor, task_uuid: str,
                              ignore_weekends: bool, limit: int, day_start_hour: int) -> List[Dict]:
        """Get monthly statistics for a task."""
        # Get last N months of data
        end_date = TimeUtils.get_logical_date(datetime.now(), day_start_hour)
        start_date = end_date.replace(day=1) - timedelta(days=limit * 32)  # Get extra months
        
        cursor.execute('''
            SELECT date, done_state 
            FROM task_entries 
            WHERE task_uuid = ? 
            AND date >= ? AND date <= ?
            ORDER BY date DESC
        ''', (task_uuid, start_date.isoformat(), end_date.isoformat()))
        
        # Group by month
        monthly_data = {}
        for row in cursor.fetchall():
            date_str, done_state = row
            task_date = datetime.fromisoformat(date_str).date()
            
            # Skip weekends if requested
            if ignore_weekends and task_date.weekday() >= 5:  # Saturday=5, Sunday=6
                continue
            
            # Get first day of the month
            month_start = task_date.replace(day=1)
            month_key = month_start.isoformat()
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {'completed_days': 0, 'total_days': 0}
            
            monthly_data[month_key]['total_days'] += 1
            if done_state:
                monthly_data[month_key]['completed_days'] += 1
        
        # Convert to list format
        data = []
        for month_start_str in sorted(monthly_data.keys(), reverse=True):
            month_start = datetime.fromisoformat(month_start_str).date()
            month_data = monthly_data[month_start_str]
            
            completion_rate = (month_data['completed_days'] / month_data['total_days'] 
                             if month_data['total_days'] > 0 else 0)
            
            data.append({
                'date': month_start_str,
                'completed': completion_rate,
                'display_label': month_start.strftime('%Y-%m'),
                'completed_days': month_data['completed_days'],
                'total_days': month_data['total_days']
            })
            
            if len(data) >= limit:
                break
        
        return data[:limit]

    def _get_yearly_statistics(self, cursor, task_uuid: str,
                             ignore_weekends: bool, limit: int, day_start_hour: int) -> List[Dict]:
        """Get yearly statistics for a task."""
        # Get last N years of data
        end_date = TimeUtils.get_logical_date(datetime.now(), day_start_hour)
        start_date = end_date.replace(month=1, day=1) - timedelta(days=limit * 366)  # Get extra years
        
        cursor.execute('''
            SELECT date, done_state 
            FROM task_entries 
            WHERE task_uuid = ? 
            AND date >= ? AND date <= ?
            ORDER BY date DESC
        ''', (task_uuid, start_date.isoformat(), end_date.isoformat()))
        
        # Group by year
        yearly_data = {}
        for row in cursor.fetchall():
            date_str, done_state = row
            task_date = datetime.fromisoformat(date_str).date()
            
            # Skip weekends if requested
            if ignore_weekends and task_date.weekday() >= 5:  # Saturday=5, Sunday=6
                continue
            
            # Get first day of the year
            year_start = task_date.replace(month=1, day=1)
            year_key = year_start.isoformat()
            
            if year_key not in yearly_data:
                yearly_data[year_key] = {'completed_days': 0, 'total_days': 0}
            
            yearly_data[year_key]['total_days'] += 1
            if done_state:
                yearly_data[year_key]['completed_days'] += 1
        
        # Convert to list format
        data = []
        for year_start_str in sorted(yearly_data.keys(), reverse=True):
            year_start = datetime.fromisoformat(year_start_str).date()
            year_data = yearly_data[year_start_str]
            
            completion_rate = (year_data['completed_days'] / year_data['total_days'] 
                             if year_data['total_days'] > 0 else 0)
            
            data.append({
                'date': year_start_str,
                'completed': completion_rate,
                'display_label': year_start.strftime('%Y'),
                'completed_days': year_data['completed_days'],
                'total_days': year_data['total_days']
            })
            
            if len(data) >= limit:
                break
        
        return data[:limit]

    def get_task_uuid(self, activity_id: str, task_name: str) -> Optional[str]:
        """
        Get the UUID for a task by activity ID and task name.
        Returns None if the task is not registered in the database.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT task_uuid FROM task_to_uuid 
                    WHERE activity_id = ? AND task_name = ?
                ''', (activity_id, task_name))
                
                result = cursor.fetchone()
                return result[0] if result else None
                
        except sqlite3.Error as e:
            log_error(f"Failed to get task UUID: {e}")
            return None
    
    def is_task_saved_to_db(self, activity_id: str, task_name: str) -> bool:
        """
        Check if a task is already saved to the database (exists in task_to_uuid table).
        """
        return self.get_task_uuid(activity_id, task_name) is not None
    
    def save_tasks_to_db(self, activities: List[Dict]) -> int:
        """
        Save all tasks from activities to the database.
        This should be called when the user saves the schedule.
        Returns the number of new tasks registered.
        """
        new_tasks_count = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for activity in activities:
                    activity_id = activity.get("id")
                    if not activity_id:
                        log_error(f"Activity '{activity.get('name', 'Unknown')}' has no ID, skipping")
                        continue
                    
                    tasks = activity.get("tasks", [])
                    for task in tasks:
                        # Handle both string and object task formats
                        if isinstance(task, str):
                            task_name = task.strip()
                            task_uuid = None  # Will generate new UUID
                        elif isinstance(task, dict) and "name" in task:
                            task_name = task["name"].strip()
                            task_uuid = task.get("uuid")  # Use UUID from YAML
                        else:
                            log_error(f"Invalid task format: {task}")
                            continue
                        
                        if not task_name:
                            continue
                        
                        # Check if task already exists in database
                        cursor.execute('''
                            SELECT task_uuid FROM task_to_uuid 
                            WHERE activity_id = ? AND task_name = ?
                        ''', (activity_id, task_name))
                        
                        existing_result = cursor.fetchone()
                        if existing_result is None:
                            # Task doesn't exist in database, register it
                            if not task_uuid:
                                task_uuid = str(uuid.uuid4())  # Generate new UUID if not provided
                            
                            cursor.execute('''
                                INSERT INTO task_to_uuid (task_uuid, activity_id, task_name)
                                VALUES (?, ?, ?)
                            ''', (task_uuid, activity_id, task_name))
                            new_tasks_count += 1
                            log_debug(f"Registered new task '{task_name}' with UUID '{task_uuid}'")  
                        else:
                            # Task exists, verify UUID matches if provided in YAML
                            existing_uuid = existing_result[0]
                            if task_uuid and task_uuid != existing_uuid:
                                log_debug(f"Task '{task_name}' UUID mismatch: YAML={task_uuid}, DB={existing_uuid}. Using DB UUID.")
                
                conn.commit()
                log_info(f"Saved {new_tasks_count} new tasks to database")
                return new_tasks_count
                
        except sqlite3.Error as e:
            log_error(f"Failed to save tasks to database: {e}")
            return 0
    
    def has_unsaved_tasks(self, activity: Dict) -> bool:
        """
        Check if an activity has any tasks that are not yet saved to the database.
        """
        activity_id = activity.get("id")
        if not activity_id:
            return False
        
        tasks = activity.get("tasks", [])
        for task in tasks:
            # Handle both string and object task formats
            if isinstance(task, str):
                task_name = task.strip()
            elif isinstance(task, dict) and "name" in task:
                task_name = task["name"].strip()
            else:
                continue
            
            if not task_name:
                continue
            if not self.is_task_saved_to_db(activity_id, task_name):
                return True
        
        return False
    
    def get_unsaved_tasks(self, activity: Dict) -> List[str]:
        """
        Get a list of task names that are not yet saved to the database for an activity.
        """
        activity_id = activity.get("id")
        if not activity_id:
            return []
        
        unsaved_tasks = []
        tasks = activity.get("tasks", [])
        for task in tasks:
            # Handle both string and object task formats
            if isinstance(task, str):
                task_name = task.strip()
            elif isinstance(task, dict) and "name" in task:
                task_name = task["name"].strip()
            else:
                continue
            
            if not task_name:
                continue
            if not self.is_task_saved_to_db(activity_id, task_name):
                unsaved_tasks.append(task_name)
        
        return unsaved_tasks
     
    def get_task_uuids_by_activity_and_name(self, activity_id: str, task_name: str, target_date: date = None, day_start_hour: int = 0) -> List[str]:
        """
        Get task UUIDs for a specific activity and task name on a given date.
        Returns list of task UUIDs.
        
        Args:
            activity_id: UUID of the activity
            task_name: Name of the task
            target_date: Date to check tasks for (uses logical date if None)
            day_start_hour: Hour when day starts (0-23), used for logical date calculation
        """
        if target_date is None:
            target_date = TimeUtils.get_logical_date(datetime.now(), day_start_hour)
        
        date_str = target_date.isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Join task_to_uuid and task_entries to get UUIDs for specific activity/task on date
                cursor.execute('''
                    SELECT te.task_uuid 
                    FROM task_entries te
                    JOIN task_to_uuid tu ON te.task_uuid = tu.task_uuid
                    WHERE tu.activity_id = ? AND tu.task_name = ? AND te.date = ?
                ''', (activity_id, task_name, date_str))
                
                return [row[0] for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            log_error(f"Failed to get task UUIDs: {e}")
            return []
    
    def get_task_streak(self, task_uuid: str, target_date: date = None, day_start_hour: int = 0) -> int:
        """
        Calculate the current streak for a task.
        A streak is the number of consecutive days (going backwards from target_date) 
        where the task was completed (done_state = 1).
        
        New behavior:
        - Ignores current day if task is not done (day isn't finished yet)
        - Ignores dates with no data (missing entries don't break the streak)
        - Only breaks streak when an entry exists but is marked as not done (False)
        
        Args:
            task_uuid: UUID of the task to check
            target_date: End date for streak calculation (uses logical date if None)
            day_start_hour: Hour when day starts (0-23), used for logical date calculation
            
        Returns:
            The number of consecutive days the task was completed (0 if never done or broken streak)
        """
        if target_date is None:
            target_date = TimeUtils.get_logical_date(datetime.now(), day_start_hour)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all task entries for this task, ordered by date descending
                cursor.execute('''
                    SELECT date, done_state 
                    FROM task_entries 
                    WHERE task_uuid = ?
                    ORDER BY date DESC
                ''', (task_uuid,))
                
                rows = cursor.fetchall()
                if not rows:
                    return 0
                
                # Build a map of date -> done_state for efficient lookup
                date_map = {datetime.fromisoformat(row[0]).date(): bool(row[1]) for row in rows}
                
                # Start from target_date
                current_date = target_date
                
                # Get logical today for comparison
                logical_today = TimeUtils.get_logical_date(datetime.now(), day_start_hour)
                
                # If target_date is today and task is not done, skip it (day isn't finished yet)
                if current_date == logical_today and current_date in date_map and not date_map[current_date]:
                    current_date -= timedelta(days=1)
                
                # Count consecutive days backwards
                streak = 0
                # Set a reasonable limit to avoid infinite loops (e.g., 10 years back)
                max_days_back = 3650
                days_checked = 0
                
                while days_checked < max_days_back:
                    days_checked += 1
                    
                    if current_date in date_map:
                        if date_map[current_date]:
                            # Task was completed on this day
                            streak += 1
                            current_date -= timedelta(days=1)
                        else:
                            # Task was not completed on this day - streak broken
                            break
                    else:
                        # No data for this date - skip it and continue counting backwards
                        current_date -= timedelta(days=1)
                
                return streak
                
        except sqlite3.Error as e:
            log_error(f"Failed to get task streak: {e}")
            return 0
    
