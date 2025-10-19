from utils.logging import log_debug
from ui.timeline import reposition_timeline, reposition_current_time_line
from datetime import datetime
import tkinter.font as tkfont


def _update_activity_label_truncation(app):
    """Update activity label text with truncation based on current window width."""
    # Import here to avoid circular dependency
    from ui.app_ui_loop import truncate_text_to_width
    
    # Only update if we have stored full text
    if not hasattr(app, '_activity_label_full_text'):
        return
    
    full_text = app._activity_label_full_text
    label_font = tkfont.Font(font=app.activity_label['font'])
    label_width = app.activity_label.winfo_width()
    # Account for padding and border (approx 10px on each side)
    available_width = max(label_width - 20, 50)
    truncated_text = truncate_text_to_width(full_text, label_font, available_width)
    app.activity_label.config(text=truncated_text)


def move_timelines_and_cards(app, delta_y):
    """Move both timelines and all cards by delta_y."""
    for tid in getattr(app, 'timeline_1h_ids', []):
        app.canvas.move(tid, 0, delta_y)
    for tid in getattr(app, 'timeline_5m_ids', []):
        app.canvas.move(tid, 0, delta_y)
    # Move current time line
    for tid in getattr(app, 'current_time_ids', []):
        app.canvas.move(tid, 0, delta_y)
    now = app.now_provider().time()
    # Move all cards
    for card_obj in app.cards:
        card_obj.y += delta_y
        for cid in [card_obj.card, card_obj.label]:
            if cid:
                app.canvas.move(cid, 0, delta_y)
        card_obj.update_card_visuals(
            card_obj.start_hour, card_obj.start_minute, app.start_hour, app.pixels_per_hour, app.offset_y, now=now, width=app.winfo_width()
        )

def is_mouse_in_window(app):
    """Check if mouse is in the window."""
    x, y = app.winfo_pointerx(), app.winfo_pointery()
    x0, y0 = app.winfo_rootx(), app.winfo_rooty()
    x1, y1 = x0 + app.winfo_width(), y0 + app.winfo_height()
    menu_bar_height = 30 if app.menu_visible else 0
    y0 -= menu_bar_height
    return x0 <= x <= x1 and y0 <= y <= y1

def poll_mouse(app):
    """Poll mouse position and hide menu bar if mouse is not in window."""
    from ui.app_ui_events import hide_menu_bar
    if app.menu_visible and not is_mouse_in_window(app):
        hide_menu_bar(app)
    app.after(200, lambda: poll_mouse(app))

def zoom(app, event, delta: int):
    """Zoom in or out based on mouse wheel event."""
    zoom_step = 0.1
    a = app.zoom_factor + (-zoom_step if delta > 0 else zoom_step)
    app.zoom_factor = max(0.5, min(6, a))
    old_pph = app.pixels_per_hour
    app.pixels_per_hour = max(50, int(50 * app.zoom_factor))
    mouse_y = event.y
    rel_y = mouse_y - 100 - app.offset_y
    scale = app.pixels_per_hour / old_pph
    app.offset_y = min(100, int(mouse_y - 100 - rel_y * scale))
    resize_timelines_and_cards(app)
    app.last_action = datetime.now()

def resize_timelines_and_cards(app):
    """Resize timelines and cards based on new PPH and offset Y."""
    log_debug(f"Resizing timelines and cards, new PPH: {app.pixels_per_hour}, Offset Y: {app.offset_y}")
    now = app.now_provider().time()
    for card_obj in app.cards:
        card_obj.update_card_visuals(
            card_obj.start_hour, card_obj.start_minute, app.start_hour, app.pixels_per_hour, app.offset_y, now=now, width=app.winfo_width()
        )
    reposition_timeline(app.canvas, app.timeline_1h_ids, app.pixels_per_hour, app.offset_y, app.winfo_width(), granularity=60)
    reposition_timeline(app.canvas, app.timeline_5m_ids, app.pixels_per_hour, app.offset_y, app.winfo_width(), granularity=5)
    # Reposition current time line
    mouse_inside = app._is_mouse_inside_window()
    reposition_current_time_line(app.canvas, app.current_time_ids, app.start_hour, app.pixels_per_hour, app.offset_y, app.winfo_width(), now, mouse_inside)
    app.activity_label.place(x=10, y=40, width=app.winfo_width() - 20)
    
    # Recalculate text truncation on resize
    _update_activity_label_truncation(app)
    
def scroll(app, event, delta: int):
    """Scroll timelines and cards based on scroll event."""
    log_debug(f"Scrolling: {delta}, PPH: {app.pixels_per_hour}, Current Offset Y: {app.offset_y}")
    if app.pixels_per_hour > 50:
        scroll_step = -40 if delta > 0 else 40
        app.offset_y += scroll_step
        move_timelines_and_cards(app, scroll_step)
        app.last_action = datetime.now()
