import tkinter as tk
import tkinter.messagebox as messagebox

def open_global_options(app):
    """Open a dialog to edit global options."""
    options_win = tk.Toplevel(app)
    options_win.title("Global Options")
    options_win.geometry("300x180")
    options_win.transient(app)
    options_win.grab_set()

    tk.Label(options_win, text="Start hour:").pack(anchor="w", padx=10, pady=(15, 0))
    start_hour_var = tk.IntVar(value=app.start_hour)
    start_hour_entry = tk.Entry(options_win, textvariable=start_hour_var)
    start_hour_entry.pack(fill="x", padx=10)

    tk.Label(options_win, text="End hour:").pack(anchor="w", padx=10, pady=(10, 0))
    end_hour_var = tk.IntVar(value=app.end_hour)
    end_hour_entry = tk.Entry(options_win, textvariable=end_hour_var)
    end_hour_entry.pack(fill="x", padx=10)

    btn_frame = tk.Frame(options_win)
    btn_frame.pack(fill="x", pady=15)
    def on_ok():
        try:
            new_start = int(start_hour_var.get())
            new_end = int(end_hour_var.get())
            if 0 <= new_start < 24 and 0 < new_end <= 24 and new_start < new_end:
                app.start_hour = new_start
                app.end_hour = new_end
                app.update_cards_after_size_change()
                options_win.destroy()
            else:
                messagebox.showerror("Invalid Input", "Start hour must be >=0 and < End hour, End hour must be <=24.")
        except Exception as e:
            messagebox.showerror("Invalid Input", str(e))
    def on_cancel():
        options_win.destroy()
    tk.Button(btn_frame, text="Ok", command=on_ok).pack(side="left", padx=20)
    tk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="right", padx=20)
