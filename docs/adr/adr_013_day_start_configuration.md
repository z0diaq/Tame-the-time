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

**2. Backward Compatibility**
- Maintain `start_hour` and `end_hour` as derived values for existing code
- `start_hour = day_start`
- `end_hour = (day_start + 24) % 24` if `day_start != 0` else 24

**3. User Interface**
- Global Options dialog shows single "Day starts at (hour):" field
- Help text explains the concept: "Hour when a new day begins for card management (0-23)"
- Validation ensures value is between 0-23

**4. Settings Persistence**
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
