# ADR-014: Forgiving Streak Counting Logic

**Title:** Forgiving Streak Counting Logic for Task Completion  
**Status:** Accepted  
**Date:** 2025-10-24

## Context

The original task streak calculation was overly strict and penalized users in scenarios that didn't truly represent a broken habit or commitment:

1. **Current Day Penalty**: If a user checked their statistics during the day before completing a task, the streak would break even though the day wasn't finished yet
2. **Missing Data Penalty**: Days with no data entries (e.g., when the app wasn't used, system was off, or schedule didn't include the task) would break the streak
3. **User Frustration**: Users felt discouraged when streaks broke for technical reasons rather than actual failure to complete tasks

The strict approach assumed:
- Every day must have an entry
- The current incomplete day breaks the streak
- Any gap in data represents a failure

This didn't match real-world usage patterns where users might:
- Check statistics mid-day while tasks are still pending
- Skip days when traveling or during weekends
- Not use the application every single day

## Decision

We will implement a "forgiving" streak counting algorithm that focuses on intentional failures rather than technical gaps.

### New Streak Logic

The `get_task_streak()` method now implements three key behavioral changes:

**1. Ignore Current Incomplete Day**
- If the target date is today AND the task is not yet completed
- Skip today and start counting from yesterday
- Rationale: The day isn't finished yet, so it shouldn't break the streak

**2. Skip Missing Data Days**
- Days with no database entry are ignored when counting backwards
- Only continue looking for the next available entry
- Rationale: Missing data shouldn't penalize the user

**3. Break Only on Explicit Failures**
- Streak breaks ONLY when an entry exists but is marked as not completed (False)
- This represents an actual day where the task could have been done but wasn't
- Rationale: This reflects true commitment failures, not technical gaps

### Implementation Details

```python
# Pseudocode of the logic:
if target_date == today and task_not_done:
    start_from = yesterday  # Day isn't done yet
else:
    start_from = target_date

streak = 0
current_date = start_from

while looking_back (up to 10 years):
    if date_has_entry:
        if task_completed:
            streak += 1
            current_date -= 1 day
        else:
            break  # Explicit failure - break streak
    else:
        current_date -= 1 day  # No data - keep looking
```

### Safety Mechanisms

- **Maximum Lookback**: 3650 days (10 years) to prevent infinite loops
- **Date Map**: Efficient O(1) lookup for date entries
- **Error Handling**: SQLite errors return 0 streak gracefully

## Consequences

**Positive:**
- **User-Friendly**: Encourages users by not penalizing them for incomplete days or technical gaps
- **Realistic Tracking**: Focuses on actual behavior rather than data completeness
- **Mid-Day Checking**: Users can check progress during the day without fear of breaking streaks
- **Flexible Usage**: Supports irregular app usage patterns (weekends, travel, etc.)
- **Motivation Preservation**: Streaks survive temporary interruptions, maintaining user motivation

**Negative:**
- **Less Strict Accountability**: Users might rationalize gaps as "missing data" rather than acknowledging skipped days
- **Data Quality Dependency**: Assumes missing data is intentional/acceptable, which may not always be true
- **Potential Gaming**: Users could theoretically avoid marking tasks as incomplete to preserve streaks
- **Complexity**: More complex logic than simple consecutive day counting

**Neutral:**
- **Performance**: 10-year lookback with loop iteration is acceptable for typical usage
- **Database Load**: No additional queries, just more iteration in memory
- **Migration**: No database changes required, only logic changes

## Use Cases

### Scenario 1: Mid-Day Check
```
Today 12:00 PM (task not done yet)
Yesterday (done)
2 days ago (done)
Result: Streak = 2 (ignores today since it's incomplete)
```

### Scenario 2: Weekend Gap
```
Today (done)
Yesterday (done)
2 days ago (no data - weekend)
3 days ago (no data - weekend)
4 days ago (done)
Result: Streak = 3 (skips weekend, counts all done days)
```

### Scenario 3: Explicit Failure
```
Today (done)
Yesterday (done)
2 days ago (NOT done - explicit False)
3 days ago (done)
Result: Streak = 2 (breaks at explicit failure on day 2)
```

### Scenario 4: Mixed Pattern
```
Today (not done yet)
Yesterday (done)
2 days ago (no data)
3 days ago (done)
4 days ago (NOT done)
Result: Streak = 2 (ignores today, counts yesterday, skips missing, counts 3 days ago, breaks at 4 days ago)
```

## Alternatives Considered

### 1. Strict Consecutive Days
**Description**: Only count days that are explicitly consecutive with no gaps  
**Rejected**: Too harsh for real-world usage patterns, would frustrate users

### 2. Configurable Forgiveness
**Description**: Let users choose "strict" or "forgiving" mode  
**Rejected**: Adds unnecessary complexity, most users would choose forgiving anyway

### 3. Grace Period Days
**Description**: Allow X days of missing data before breaking streak  
**Rejected**: Arbitrary threshold, doesn't address the core issue of data vs. behavior

### 4. Weighted Streak Score
**Description**: Reduce streak value for gaps instead of breaking completely  
**Rejected**: Overly complex, harder to understand and communicate to users

### 5. Current Day as Half Point
**Description**: Count incomplete current day as 0.5 in the streak  
**Rejected**: Fractional streaks are confusing, simple skip is clearer

## Related ADRs

- **ADR-003**: SQLite for Task Tracking Database (persistence layer)
- **ADR-006**: Service Layer Pattern for Business Logic (streak calculation location)
- **ADR-008**: Matplotlib for Statistics Visualization (streak display)

## Future Considerations

1. **Streak Insights**: Could add UI indicators showing "X days of missing data" vs "Y days of actual completion"
2. **Configurable Lookback**: Allow users to limit how far back to look for streak calculation
3. **Multiple Streak Types**: Support both "forgiving" and "strict" streaks displayed side-by-side
4. **Streak Warnings**: Notify users when a day is ending and tasks remain incomplete
5. **Data Quality Metrics**: Track data completeness separately from task completion
