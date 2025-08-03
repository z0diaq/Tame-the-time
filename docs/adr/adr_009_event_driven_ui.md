# ADR-009: Event-Driven UI Architecture

**Title:** Event-Driven UI Architecture  
**Status:** Accepted  
**Date:** 2025-08-03  

## Context

The application needed to handle complex user interactions with the timeline interface:

- Mouse events (click, drag, scroll, wheel, motion)
- Keyboard shortcuts and window events
- Real-time updates and animations
- Context-sensitive menus and tooltips
- Responsive UI that reacts to time changes

The challenge was organizing event handling code to avoid a monolithic event handler while maintaining responsive user experience.

## Decision

We implemented an event-driven architecture with modular event handlers:

```
ui/
├── app.py                 # Main application and event coordination
├── app_ui_events.py       # Core UI events (resize, close, motion)
├── app_card_handling.py   # Card-specific interactions (drag, press)
├── app_ui_loop.py         # Real-time update loop
├── context_menu.py        # Context menu handling
└── zoom_and_scroll.py     # Viewport manipulation
```

**Event Flow:**
```python
# Event binding in main app
self.canvas.bind('<Motion>', lambda event: on_motion(self, event))
self.canvas.bind('<Button-3>', lambda event: show_canvas_context_menu(self, event))

# Modular event handlers
def on_motion(app, event):
    # Auto-hide menu logic
    # Cursor management
    
def on_card_press(app, event):
    # Card selection and drag initiation
```

**Key Patterns:**
- Event handlers receive app instance for state access
- Modular organization by functionality
- Lambda wrappers for parameter passing
- State management through app instance
- Clean separation of concerns

## Consequences

**Positive:**
- Modular event handling improves code organization
- Easy to test individual event handlers
- Clear separation between different interaction types
- Responsive UI with smooth interactions
- Easy to add new event types and handlers

**Negative:**
- Event handler coordination requires careful state management
- Debugging event flow can be complex
- Potential for event handler conflicts
- Memory overhead from multiple event bindings

## Alternatives

1. **Monolithic Event Handler**: Single large handler - rejected due to maintainability
2. **Observer Pattern**: Pub/sub events - overkill for direct UI interactions
3. **Command Pattern**: Event as commands - too much abstraction for simple UI events
4. **State Machine**: Formal state management - unnecessary complexity for current needs
