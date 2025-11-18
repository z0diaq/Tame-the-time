# ADR-013: Day Start Configuration

**Title:** Day Start Configuration for Card Management  
**Status:** Accepted  
**Date:** 2025-09-20

## Context

The application previously used both `start_hour` and `end_hour` settings to define the working day range for timeline display and card positioning. This approach had several limitations:

1. **Conceptual Confusion**: Users had to specify both start and end hours, but the end hour was primarily used for timeline display rather than meaningful day boundaries
2. **Limited Flexibility**: The system assumed a continuous 24-hour period, making it difficult to handle scenarios where a "day" should start at non-midnight hours (e.g., shift workers, night owls)
3. **Redundant Configuration**: The end hour was typically just start_hour + 24, making it redundant for most use cases
4. **Complex Logic**: Timeline calculations had to account for both start and end hours, adding unnecessary complexity

## Decision

We will replace the dual `start_hour`/`end_hour` configuration with a single `day_start` setting that defines when a new day begins for card management purposes.

### Implementation Details

**1. Configuration Change**
- Replace `start_hour` and `end_hour` with `day_start` (0-23)
- `day_start` represents the hour when a new day begins for the application
- Default value: 0 (midnight)

**2. User Interface**
- Global Options dialog shows single "Day starts at (hour):" field
- Help text explains the concept: "Hour when a new day begins for card management (0-23)"
- Validation ensures value is between 0-23

**3. Settings Persistence**
- Store `day_start` in user settings JSON file
- Load from settings on application startup
- Save immediately when changed through Global Options

### Use Cases Enabled

1. **Night Shift Workers**: Set day_start=18 so the "day" begins at 6 PM
2. **Late Night Workers**: Set day_start=4 so the "day" begins at 4 AM
3. **Standard Users**: Keep day_start=0 for traditional midnight-to-midnight days
4. **Flexible Scheduling**: Any hour can be the start of a planning "day"

## Consequences

**Positive:**
- **Simplified Configuration**: Single setting instead of two related settings
- **Clearer Semantics**: "When does your day start?" is more intuitive than "start/end hours"
- **Enhanced Flexibility**: Supports non-traditional work schedules and time zones
- **Reduced Complexity**: Timeline and card positioning logic becomes simpler
- **Better User Experience**: More intuitive configuration for diverse use cases

**Negative:**
- **Migration Complexity**: Existing code must be updated to use the new approach
- **Backward Compatibility Overhead**: Must maintain derived values for existing code
- **Documentation Updates**: All references to start_hour/end_hour need updating

**Neutral:**
- **Timeline Display**: Still shows 24-hour timeline, but anchored to day_start
- **Card Positioning**: Same calculation logic, but relative to day_start
- **Settings Storage**: Additional setting in JSON, but removes two others eventually

## Implementation Plan

1. **Phase 1**: Add day_start setting alongside existing start_hour/end_hour
2. **Phase 2**: Update Global Options UI to use day_start
3. **Phase 3**: Update translation files for new labels
4. **Phase 4**: Gradually migrate code to use day_start directly
5. **Phase 5**: Remove start_hour/end_hour references (future cleanup)

## Alternatives Considered

1. **Keep Both Settings**: Rejected - adds unnecessary complexity
2. **Use Time Objects**: Rejected - overkill for hour-only granularity
3. **Multiple Day Boundaries**: Rejected - too complex for current needs
4. **Timezone-Based**: Rejected - day_start is simpler and more flexible

## Related ADRs

- ADR-010: Configuration Management Strategy (settings persistence)
- ADR-007: Canvas-Based Rendering (timeline and card positioning)

---

## Critical Bug Fix: Logical Date Implementation (2025-11-18)

**Update Status:** Fixed  
**Priority:** Critical

### Problem Discovered

After the initial implementation of `day_start`, a **critical bug** was discovered: database entries for tasks were created based on **calendar date** (`date.today()`) instead of **logical date** based on the `day_start` configuration.

#### Impact of the Bug

**Example with `day_start=6` (6 AM):**

| Time | Calendar Date | Logical Day | What Happened (Bug) | What Should Happen |
|------|--------------|-------------|---------------------|-------------------|
| 3:00 AM | Nov 17 | Nov 16 | Tasks saved to **Nov 17** ❌ | Tasks saved to **Nov 16** ✅ |
| 6:00 AM | Nov 17 | Nov 17 | Day rollover, entries for Nov 17 | Day rollover, entries for Nov 17 |
| 8:00 AM | Nov 17 | Nov 17 | Tasks saved to Nov 17 ✅ | Tasks saved to Nov 17 ✅ |

**The mismatch:** Between midnight and `day_start`, tasks were incorrectly recorded for the wrong logical day!

#### Root Cause Analysis

1. **Day rollover detection** correctly used `day_start` (working as intended)
2. **Database operations** used `date.today()` (calendar date) instead of logical date
3. **Startup sequence** loaded `day_start` AFTER creating daily task entries
4. **Result:** Inconsistent behavior between day rollover logic and task tracking

### Solution Implemented

#### 1. Created `TimeUtils.get_logical_date()` Method

**File:** `utils/time_utils.py`

Added utility method to calculate logical date based on `day_start`:

```python
@staticmethod
def get_logical_date(current_datetime: datetime, day_start_hour: int = 0) -> date:
    """
    Calculate the logical date based on day_start configuration.
    
    The logical date represents which "day" we're in from a planning perspective,
    which may differ from the calendar date. For example, if day_start is 6 AM,
    then times from 00:00-05:59 are considered part of the previous day.
    
    Args:
        current_datetime: Current datetime to evaluate
        day_start_hour: Hour when a new day begins (0-23), default is 0 (midnight)
        
    Returns:
        date: The logical date for task tracking purposes
    """
    if not (0 <= day_start_hour <= 23):
        raise ValueError(f"day_start_hour must be between 0-23, got {day_start_hour}")
    
    current_hour = current_datetime.hour
    current_date = current_datetime.date()
    
    # If current hour is before day_start, we're still in the previous logical day
    if current_hour < day_start_hour:
        return current_date - timedelta(days=1)
    else:
        return current_date
```

#### 2. Updated TaskTrackingService Methods

**File:** `services/task_tracking_service.py`

Updated all date-dependent methods to accept and use `day_start_hour` parameter:

- `create_daily_task_entries()` - Creates entries for logical date
- `mark_task_done()` - Marks tasks for logical date
- `mark_task_undone()` - Unmarks tasks for logical date
- `add_new_task_entry()` - Adds entries for logical date
- `get_task_done_states()` - Gets states for logical date
- `get_task_uuids_by_activity_and_name()` - Queries logical date
- `get_task_streak()` - Calculates streaks using logical dates
- Statistics methods (`_get_daily_statistics()`, `_get_weekly_statistics()`, etc.)

**Before (Bug):**
```python
def mark_task_done(self, task_uuid: str, target_date: date = None) -> bool:
    if target_date is None:
        target_date = date.today()  # ❌ Uses calendar date
```

**After (Fixed):**
```python
def mark_task_done(self, task_uuid: str, target_date: date = None, day_start_hour: int = 0) -> bool:
    if target_date is None:
        target_date = TimeUtils.get_logical_date(datetime.now(), day_start_hour)  # ✅ Uses logical date
```

#### 3. Updated All Callers

Updated files to pass `day_start` parameter to TaskTrackingService methods:

- **`ui/app.py`**: `_ensure_daily_task_entries()`, `_load_daily_task_entries()`
- **`ui/app_ui_loop.py`**: `_create_new_day_task_entries()`
- **`ui/card_dialogs.py`**: All calls to `mark_task_done()`, `mark_task_undone()`, `add_new_task_entry()`, `get_task_done_states()`

#### 4. Fixed Startup Sequence Bug

**File:** `ui/app.py`

**Critical fix:** Moved `day_start` initialization BEFORE `_ensure_daily_task_entries()` call.

**Before (Bug):**
```python
# Line 117: Create daily task entries
self._ensure_daily_task_entries()  # day_start not loaded yet! Uses default 0

# Line 131: Load day_start from settings  
self.day_start = self.settings.get("day_start", 0)
```

**After (Fixed):**
```python
# Line 110: Load day_start from settings FIRST
self.day_start = self.settings.get("day_start", 0)

# Line 122: Create daily task entries (now uses correct day_start)
self._ensure_daily_task_entries()
```

### Verification and Testing

#### Automated Tests

Created comprehensive test suite in `test_logical_date.py`:

✅ **11 unit tests** - All passed  
✅ **9 real-world scenario tests** - All passed

**Test coverage includes:**
- Standard midnight rollover (day_start=0)
- Night shift workers (day_start=18)
- Late night workers (day_start=4)
- Early morning workers (day_start=6)
- Edge cases (exactly at day_start, one minute before, etc.)

**Example test case:**
```python
# Night shift worker scenario (day_start=18)
datetime(2025, 11, 19, 2, 0)  # 2 AM on Nov 19 (calendar)
→ Logical date: 2025-11-18     # Still part of Nov 18 shift
```

#### Manual Testing Recommendations

1. **Test with day_start=6:**
   - Start app at 3 AM
   - Mark tasks as done
   - Verify they're saved to previous day's date in database

2. **Test day rollover:**
   - Start app before day_start
   - Wait for time to pass day_start
   - Verify new entries created for new logical day

3. **Test statistics:**
   - View task statistics
   - Verify dates align with logical days, not calendar days

#### Database Verification

Query to verify correct date storage:

```sql
-- Check task entries for a specific date
SELECT date, task_uuid, done_state, timestamp 
FROM task_entries 
WHERE date = '2025-11-18'
ORDER BY timestamp;
```

### Benefits Achieved

✅ **Correct Task Tracking**
- Tasks are now recorded for the correct logical day
- Statistics and streaks accurately reflect user's actual work schedule

✅ **Proper Day Rollover**
- Day rollover detection uses `day_start` (was working correctly)
- DB entry creation now matches day rollover logic

✅ **Startup Accuracy**
- Application correctly determines logical date on startup
- Tasks created for the right day even when started before `day_start`

✅ **Consistent User Experience**
- Night shift workers: Tasks between midnight and 6 PM count toward previous day
- Late night workers: Tasks before 4 AM count toward previous day
- All users: Behavior aligned with their configured day start

### Files Modified

1. **`utils/time_utils.py`** - Added `get_logical_date()` method
2. **`services/task_tracking_service.py`** - Updated 9 methods to use logical date
3. **`ui/app.py`** - Fixed startup sequence + updated 2 methods
4. **`ui/app_ui_loop.py`** - Updated day rollover task creation
5. **`ui/card_dialogs.py`** - Updated 4 task tracking calls

### Backward Compatibility

✅ **Fully backward compatible**

- Default `day_start_hour=0` maintains previous behavior
- All method signatures have optional parameters
- Existing code continues to work (uses default midnight)

### Conclusion

The logical date implementation now **correctly aligns** with the `day_start` configuration across all application functions:

- ✅ Day rollover detection
- ✅ Task entry creation
- ✅ Task completion tracking
- ✅ Statistics calculation
- ✅ Startup initialization

Users with non-midnight `day_start` configurations now experience **correct and consistent** behavior throughout the application. This fix ensures that the `day_start` concept is properly implemented not just for UI rollover, but for all data persistence operations.
