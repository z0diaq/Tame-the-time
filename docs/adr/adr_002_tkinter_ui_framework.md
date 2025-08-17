# ADR-002: Tkinter as UI Framework

**Title:** Tkinter as UI Framework  
**Status:** Accepted  
**Date:** 2025-08-03  

## Context

The timeboxing application required a desktop GUI framework for displaying timeline visualizations, task cards, and interactive dialogs. The application needed to:

- Display complex timeline graphics with precise positioning
- Handle mouse interactions (drag, resize, context menus)
- Support custom drawing for progress bars and visual indicators
- Provide cross-platform compatibility
- Minimize external dependencies for easy deployment

## Decision

We chose Tkinter as the primary UI framework with Canvas for custom graphics rendering.

**Key Implementation Details:**
- `tk.Canvas` for timeline and task card rendering
- Custom drawing for progress bars, timelines, and visual effects
- Real-time current time indicator with dynamic formatting (HH:MM/HH:MM:SS based on mouse position)
- Event binding for mouse interactions (drag, scroll, resize)
- Modal dialogs for task editing and statistics
- Menu system with auto-hide functionality

**UI Architecture:**
```
TimeboxApp (tk.Tk)
├── Canvas (timeline + task cards)
├── Status Bar (task statistics)
├── Menu System (auto-hide)
└── Modal Dialogs (edit, statistics)
```

## Consequences

**Positive:**
- Built into Python standard library - no external dependencies
- Excellent Canvas support for custom graphics and precise positioning
- Cross-platform compatibility (Windows, macOS, Linux)
- Lightweight and fast for desktop applications
- Direct control over drawing and event handling
- Easy integration with matplotlib for charts

**Negative:**
- Less modern appearance compared to newer frameworks
- Limited built-in widgets require custom implementations
- Canvas-based approach requires manual layout management
- Styling options are limited compared to web-based frameworks

## Alternatives

1. **PyQt/PySide**: More modern widgets but adds significant dependency and complexity
2. **wxPython**: Cross-platform but additional dependency and learning curve
3. **Web-based (Flask/FastAPI + HTML/CSS)**: Modern UI but requires browser and more complex architecture
4. **Kivy**: Touch-friendly but overkill for desktop timeline application
