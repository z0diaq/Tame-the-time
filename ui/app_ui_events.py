import tkinter.messagebox as messagebox
from utils.logging import log_debug
from ui.zoom_and_scroll import zoom, scroll, resize_timelines_and_cards

def show_menu_bar(app):
    if not app.menu_visible:
        app.config(menu=app.menu_bar)
        app.menu_visible = True
    if app.menu_hide_job:
        app.after_cancel(app.menu_hide_job)
        app.menu_hide_job = None

def hide_menu_bar(app):
    app.config(menu="")
    app.menu_visible = False
    app.menu_hide_job = None

def on_motion(app, event):
    # Show menu bar if mouse is near the top of the canvas
    if event.y < 30:
        show_menu_bar(app)
    else:
        if app.menu_visible and not app.menu_hide_job:
            app.menu_hide_job = app.after(500, lambda: hide_menu_bar(app))
    # Reset mouse cursor if not hovering over a card
    items = app.canvas.find_overlapping(event.x, event.y, event.x, event.y)
    card_ids = [card_obj.card for card_obj in app.cards]
    if not any(item in card_ids for item in items):
        app.config(cursor="")

def on_close(app):
    app.save_settings(immediate=True)  # Save immediately on close
    if app.schedule_changed:
        if messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Do you want to save them?"):
            app.save_schedule(ask_for_confirmation=False)
    app.destroy()

def on_resize(app, event):
    if event.widget == app:
        width, height = event.width, event.height
        last_width, last_height = app._last_size
        if any(abs(d) >= 10 for d in [width - last_width, height - last_height]):
            app._last_size = (width, height)
            app.canvas.config(width=width, height=height)
            if not app.skip_redraw:
                resize_timelines_and_cards(app)

def on_mouse_wheel(app, event):
    ctrl_held = (event.state & 0x0004) != 0
    log_debug(f"Mouse Wheel Event: {event.num}, Delta: {event.delta}, Ctrl Held: {ctrl_held}")
    delta = 0
    if event.num == 4 or event.delta > 0:  # Scroll up
        delta = -1
    elif event.num == 5 or event.delta < 0:  # Scroll down
        delta = 1
    
    if ctrl_held:
        zoom(app, event, delta)
    else:
        scroll(app, event, delta)
