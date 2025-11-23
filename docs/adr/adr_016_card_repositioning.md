# ADR-016: Card Repositioning with Time Validation

**Title:** Interactive Card Repositioning with Day Boundary and Conflict Detection  
**Status:** Accepted  
**Date:** 2025-11-22

## Context

Users needed the ability to reposition cards on the timeline after initial placement. The existing workflow required:

1. Delete the card
2. Create a new card at the desired time
3. Re-enter all activity details
4. Reconfigure tasks if present

This was particularly problematic when:
- Minor schedule adjustments were needed
- Multiple cards needed shifting by the same amount
- Users wanted to experiment with different time slots

Without repositioning, users were hesitant to make schedule changes, leading to rigid schedules that didn't adapt to real-world needs. Additionally, the application had no safeguards against moving cards to invalid positions (crossing day boundaries or creating unintended overlaps).

## Decision

We will implement an interactive card repositioning feature accessible via the context menu with the following capabilities:

### Dual Input Methods

**Option 1: Absolute Time Setting**
- User enters desired start time in HH:MM format
- Card moves to exact specified time
- Best for: Precise scheduling needs

**Option 2: Relative Time Shifting**
- User enters time shift in ±HH:MM format
- Positive values move forward (e.g., "01:30")
- Negative values move backward (e.g., "-00:30")
- Best for: Bulk adjustments or proportional moves

Both methods preserve card duration automatically.

### Validation System

**Day Boundary Protection**
- Validates against configured `day_start` setting
- Ensures card stays within single logical day period
- Prevents cards from spanning across day rollover
- Shows error dialog if boundary would be crossed

**Conflict Detection**
- Identifies overlapping time ranges with other cards
- Compares new position against all existing cards
- Handles midnight wrap-around correctly
- Shows warning dialog with list of conflicting cards
- Allows user to proceed or cancel

### Technical Implementation

**Dialog Window (`MoveCardDialog`):**
```python
class MoveCardDialog:
    - Shows current card time
    - Two input fields (absolute/relative)
    - Format hints for user guidance
    - Modal blocking dialog
    - Centered on parent window
```

**Validation Logic:**
```python
_check_day_boundary(new_hour, new_minute) -> bool
    - Converts to minutes from day_start
    - Checks if card fits within 24-hour period
    - Validates end time doesn't exceed boundary

_check_conflicts(new_hour, new_minute) -> List[cards]
    - Normalizes times relative to day_start
    - Detects overlapping ranges
    - Returns list of conflicting cards
```

**Move Operation:**
- Updates card start/end times
- Updates activity dictionary
- Syncs schedule data structure
- Triggers full UI redraw
- Marks schedule as changed

### Internationalization

Fully localized in all supported languages:
- **English**: "Move Card", "Move"
- **French**: "Déplacer la Carte", "Déplacer"
- **Spanish**: "Mover Tarjeta", "Mover"
- **Polish**: "Przenieś kartę", "Przenieś"

All error messages, hints, and labels translated.

## Consequences

**Positive:**
- **Flexible Scheduling**: Easy to adjust timeline without data loss
- **Two Input Methods**: Supports different user mental models
- **Preserved Duration**: Card length maintained automatically
- **Day Integrity**: Prevents invalid moves across day boundaries
- **Conflict Awareness**: Users informed of overlaps before confirming
- **Non-Destructive**: Can cancel without losing card data
- **Localized**: Full support for all application languages
- **Discoverable**: Integrated into existing context menu pattern

**Negative:**
- **Learning Curve**: Two input methods might confuse new users initially
- **Modal Dialog**: Blocks interaction during repositioning
- **No Visual Preview**: Can't see new position before committing
- **No Undo**: Once confirmed, move is permanent (requires manual reversal)
- **Conflict Flexibility**: Allowing overlaps might lead to ambiguous schedules

**Neutral:**
- **Performance**: Dialog creation and validation are lightweight operations
- **Code Organization**: Adds new file but follows existing patterns
- **Dependencies**: Uses only standard Tkinter components
- **Complexity**: Conflict detection algorithm handles edge cases but adds code

## Use Cases

### Scenario 1: Precise Time Adjustment
```
Current: Card at 09:00-10:00
Action: Right-click → Move → Enter "09:30"
Result: Card moves to 09:30-10:30
```

### Scenario 2: Bulk Schedule Shift
```
Current: Multiple cards need +30 minute shift
Action: For each card, Move → Enter "00:30"
Result: All cards shifted forward by 30 minutes
```

### Scenario 3: Day Boundary Violation
```
Current: Card at 23:30-00:30 (day_start=0)
Action: Move → Enter "00:30"
Result: Error - "Cannot move card: would cross day boundary"
```

### Scenario 4: Conflict Detection
```
Current: Card A at 10:00-11:00, Card B at 14:00-15:00
Action: Move Card B → Enter "10:30"
Result: Warning - "Will overlap with Card A. Proceed?"
User: Can confirm or cancel
```

### Scenario 5: Backward Shift
```
Current: Card at 15:00-16:00
Action: Move → Enter "-02:00"
Result: Card moves to 13:00-14:00
```

## Alternatives Considered

### 1. Drag-and-Drop Repositioning
**Description**: Click and drag card to new position on timeline  
**Rejected**: More complex to implement with pixel-to-time conversion, harder to be precise, requires additional drag state management

### 2. Inline Time Editors
**Description**: Click on card time to edit in-place  
**Rejected**: Less discoverable, doesn't support relative shifts, harder to validate before commit

### 3. Arrow Key Nudging
**Description**: Use keyboard arrows to move card in small increments  
**Rejected**: Requires focus management, less intuitive, no conflict preview

### 4. Strict Conflict Prevention
**Description**: Block all moves that would create overlaps  
**Rejected**: Too restrictive, users sometimes intentionally overlap activities

### 5. Auto-Gap Filling
**Description**: Automatically adjust other cards to make room  
**Rejected**: Too much "magic", could move cards user didn't intend to change

### 6. Time Picker Widget
**Description**: Use graphical time picker instead of text entry  
**Rejected**: Takes more clicks, doesn't support relative shifts, larger dialog

## Related ADRs

- **ADR-002**: Tkinter UI Framework (dialog implementation)
- **ADR-009**: Event-Driven UI Architecture (context menu events)
- **ADR-012**: JSON Internationalization (dialog translations)
- **ADR-013**: Day Start Configuration (boundary validation logic)
- **ADR-015**: URL Extraction from Context Menu (similar context menu pattern)

## Implementation Details

**Files Created:**
- `ui/move_card_dialog.py`: Complete dialog and validation implementation

**Files Modified:**
- `ui/context_menu.py`: Added Move menu item and integration logic
- `locales/en.json`: Added move card translations
- `locales/fr.json`: Added move card translations
- `locales/es.json`: Added move card translations
- `locales/pl.json`: Added move card translations

**Key Classes:**
- `MoveCardDialog`: Main dialog window with dual input methods
- `open_move_card_dialog()`: Public API function for opening dialog

**Key Methods:**
- `_calculate_new_time()`: Parses user input (absolute or relative)
- `_parse_shift_time()`: Handles ±HH:MM format with sign
- `_check_day_boundary()`: Validates against day_start configuration
- `_check_conflicts()`: Detects overlapping time ranges
- `show()`: Modal display with result return

**Dependencies:**
- `tkinter`: Dialog UI components
- `utils.time_utils.TimeUtils`: Time parsing and validation
- `utils.translator`: Localization support

## Future Considerations

1. **Drag-and-Drop Support**: Add visual repositioning alongside dialog method
2. **Batch Move**: Select multiple cards and move together
3. **Undo/Redo**: Support for reverting move operations
4. **Visual Preview**: Show ghost card at new position before confirming
5. **Auto-Conflict Resolution**: Suggest alternative times when conflicts detected
6. **Keyboard Shortcuts**: Quick shifts with Ctrl+Arrow keys
7. **Move History**: Track recent moves for quick reversal
8. **Smart Snapping**: Auto-align to adjacent cards or time boundaries
9. **Recurring Moves**: Apply same move to multiple days/weeks
10. **Conflict Highlighting**: Visual indication of overlap severity

## Testing Considerations

**Manual Test Cases:**
1. Move to absolute time within valid range
2. Shift forward with positive offset
3. Shift backward with negative offset
4. Attempt day boundary crossing (should error)
5. Move to position with conflicts (should warn)
6. Cancel dialog (should not move)
7. Invalid time format input (should error)
8. Edge case: midnight wrap-around
9. Edge case: very short cards (< 5 minutes)
10. Test in all four supported languages

**Validation Tests:**
- Day boundary detection with various day_start values (0, 4, 6, 18)
- Conflict detection with adjacent cards
- Conflict detection with midnight-spanning cards
- Time arithmetic with negative shifts
- Format validation for HH:MM input
