import time
import threading
import random
import json
t_lock = threading.Lock()
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import pyautogui
from pynput import mouse, keyboard
import pygetwindow as gw

class AutoClicker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Pro Auto-Clicker")
        self.root.geometry("820x920")
        self.root.minsize(820, 900)
        self.root.attributes('-topmost', True)
        self.root.configure(bg="#1c1c1c") # Professional Slate Dark

        self.sequence = []  # Stores (x, y, delay, type, is_relative, name, win_title)
        self.is_recording = False
        self.is_running = False
        self._drag_data = None
        self.last_click_data = {"time": 0, "x": 0, "y": 0}

        self.apply_style()
        self.setup_ui()
        self.setup_listeners()
        self.update_mouse_pos()

    def apply_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # UI Palette
        bg_color = "#1c1c1c"
        card_color = "#2d2d2d"
        entry_bg = "#383838"
        text_color = "#ffffff"
        accent_blue = "#0078d4"
        record_red = "#ef4444"
        start_green = "#22c55e"

        # Font configuration
        title_font = ('Segoe UI Variable Display', 10, 'bold')
        ui_font = ('Segoe UI Variable Text', 10)
        
        style.configure("TFrame", background=bg_color)
        style.configure("TLabelframe", background=bg_color, foreground=text_color, bordercolor=card_color)
        style.configure("TLabelframe.Label", background=bg_color, foreground=accent_blue, font=title_font)
        style.configure("TLabel", background=bg_color, foreground=text_color, font=ui_font)
        
        # Global Button Styling
        style.configure("TButton", background=card_color, foreground=text_color, borderwidth=0, padding=8, font=title_font)
        style.map("TButton", background=[('active', accent_blue)], foreground=[('active', '#ffffff')])

        # Entry and Combobox Styling via Option Database
        self.root.option_add("*TEntry*Font", ui_font)
        self.root.option_add("*TCombobox*Font", ui_font)
        # Fix for the dropdown listbox background/foreground
        self.root.option_add('*TCombobox*Listbox.background', entry_bg)
        self.root.option_add('*TCombobox*Listbox.foreground', text_color)
        self.root.option_add('*TCombobox*Listbox.selectBackground', accent_blue)
        self.root.option_add('*TCombobox*Listbox.selectForeground', '#ffffff')
        style.configure("TEntry", fieldbackground=entry_bg, foreground=text_color, bordercolor=card_color)

        # Checkbutton Styling
        style.configure("TCheckbutton", background=bg_color, foreground=text_color, font=ui_font, focuscolor=bg_color)
        style.map("TCheckbutton", 
                  background=[('active', bg_color)], 
                  foreground=[('active', accent_blue)])

        style.configure("Record.TButton", foreground=record_red)
        style.configure("Start.TButton", foreground=start_green)

        style.configure("Treeview", background="#252525", foreground=text_color, fieldbackground="#252525", borderwidth=0, rowheight=32, font=ui_font)
        style.map("Treeview", background=[('selected', accent_blue)])
        style.configure("Heading", background="#333333", foreground=text_color, font=title_font, borderwidth=0)

    def update_mouse_pos(self):
        x, y = pyautogui.position()
        try:
            win = gw.getActiveWindow()
            if win:
                rel_x, rel_y = x - win.left, y - win.top
                win_title = (win.title[:20] + '..') if len(win.title) > 20 else win.title
                self.pos_label.config(text=f"📍 ABS: {x},{y}   🔲 REL: {rel_x},{rel_y}   🏷️ {win_title}")
            else:
                self.pos_label.config(text=f"ABS: {x},{y}")
        except Exception:
            pass
        self.root.after(100, self.update_mouse_pos)

    def setup_ui(self):
        # Main Container
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Settings
        settings_frame = ttk.LabelFrame(main_frame, text=" CONFIGURATION ", padding=15)
        settings_frame.pack(fill="x", pady=5)

        ttk.Label(settings_frame, text="Default Wait (ms):").grid(row=0, column=0, sticky="w", padx=5)
        self.delay_var = tk.StringVar(value="500")
        ttk.Entry(settings_frame, textvariable=self.delay_var, width=12).grid(row=0, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(settings_frame, text="Loops (0=∞):").grid(row=1, column=0, sticky="w", padx=5)
        self.loop_var = tk.StringVar(value="1")
        ttk.Entry(settings_frame, textvariable=self.loop_var, width=12).grid(row=1, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(settings_frame, text="Click Type:").grid(row=0, column=2, padx=10, sticky="w")
        self.type_var = tk.StringVar(value="left")
        self.type_combo = ttk.Combobox(settings_frame, textvariable=self.type_var, values=["left", "right", "double", "middle", "mouse4", "mouse5"], width=12, state="readonly")
        self.type_combo.grid(row=0, column=3, padx=5, sticky="w")

        ttk.Label(settings_frame, text="Loop Wait (ms):").grid(row=1, column=2, padx=10, sticky="w")
        self.loop_delay_var = tk.StringVar(value="0")
        ttk.Entry(settings_frame, textvariable=self.loop_delay_var, width=12).grid(row=1, column=3, padx=5, sticky="w")
        
        self.rel_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            settings_frame, 
            text="Enable Window-Relative Offsets", 
            variable=self.rel_var,
            bg="#1c1c1c",
            fg="#ffffff",
            selectcolor="#2d2d2d",
            activebackground="#1c1c1c",
            activeforeground="#0078d4",
            font=('Segoe UI Variable Text', 10),
            bd=0,
            highlightthickness=0
        ).grid(row=2, column=0, columnspan=4, sticky="w", pady=(10, 2), padx=5)

        # Sequence List
        list_frame = ttk.LabelFrame(main_frame, text=" ACTION SEQUENCE ", padding=10)
        list_frame.pack(fill="both", expand=True, pady=5)

        self.tree = ttk.Treeview(list_frame, columns=("Index", "Name", "X", "Y", "Delay", "Type", "Mode"), show="headings", height=12)
        self.tree.heading("Index", text="ID")
        self.tree.heading("Name", text="Action Name")
        self.tree.heading("X", text="X")
        self.tree.heading("Y", text="Y")
        self.tree.heading("Delay", text="Wait (ms)")
        self.tree.heading("Type", text="Type")
        self.tree.heading("Mode", text="Ref")
        self.tree.column("Index", width=30, anchor="center")
        self.tree.column("Name", width=150, anchor="w")
        self.tree.column("X", width=60, anchor="center")
        self.tree.column("Y", width=60, anchor="center")
        self.tree.column("Delay", width=70, anchor="center")
        self.tree.column("Type", width=70, anchor="center")
        self.tree.column("Mode", width=70, anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.tag_configure("dragging_item", background="#404040", foreground="#ffffff")
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<ButtonPress-1>", self.on_drag_start)
        self.tree.bind("<B1-Motion>", self.on_drag_motion)
        self.tree.bind("<ButtonRelease-1>", self.on_drag_stop)

        # Controls
        ctrl_frame = ttk.Frame(main_frame)
        ctrl_frame.pack(fill="x", pady=5)

        self.record_btn = ttk.Button(ctrl_frame, text="● Record (F7)", style="Record.TButton", command=self.toggle_record)
        self.record_btn.pack(side="left", padx=3)
        self.run_btn = ttk.Button(ctrl_frame, text="▶ Start (F8)", style="Start.TButton", command=self.toggle_run)
        self.run_btn.pack(side="left", padx=3)
        ttk.Button(ctrl_frame, text="🗑 Delete", command=self.delete_selected).pack(side="left", padx=3)
        ttk.Button(ctrl_frame, text="🧹 Clear All", command=self.clear_sequence).pack(side="left", padx=3)

        # Separate File Controls Row
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill="x", pady=5)
        ttk.Button(file_frame, text="💾 Save Sequence", command=self.save_sequence).pack(side="left", padx=3)
        ttk.Button(file_frame, text="📂 Load Sequence", command=self.load_sequence).pack(side="left", padx=3)

        # Status Bar
        status_frame = ttk.Frame(self.root, padding=5)
        status_frame.pack(fill="x", side="bottom")
        self.pos_label = ttk.Label(status_frame, text="📍 ABS: 0,0", font=('Segoe UI Variable Text', 9))
        self.pos_label.pack(side="right", padx=5)
        ttk.Label(status_frame, text="F7: Record | F8: Start | F12: Exit", foreground="#aaaaaa").pack(side="left", padx=5)

    def save_sequence(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(self.sequence, f)
            messagebox.showinfo("Success", "Sequence saved successfully!")

    def load_sequence(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    self.sequence = json.load(f)
                self.refresh_tree()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load sequence: {e}")

    def setup_listeners(self):
        # Mouse listener for recording
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.mouse_listener.start()

        # Fixed Global Hotkeys strings to prevent ValueError
        self.hotkeys = keyboard.GlobalHotKeys({
            '<f7>': self.toggle_record,
            '<f8>': self.toggle_run,
            '<f12>': self.on_exit
        })
        self.hotkeys.start()

    def on_exit(self):
        self.is_running = False
        self.root.quit()

    def clear_sequence(self):
        self.sequence = []
        for item in self.tree.get_children():
            self.tree.delete(item)

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        
        # Get indices and remove in reverse order to maintain correct sequence mapping
        indices = sorted([self.tree.index(item) for item in selected], reverse=True)
        for idx in indices:
            self.sequence.pop(idx)
        self.refresh_tree()

    def refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, step in enumerate(self.sequence):
            x, y, d, t, is_rel = step[0], step[1], step[2], step[3], step[4]
            name = step[5] if len(step) > 5 else f"Step {i+1}"
            mode = "Window" if is_rel else "Screen"
            # win_title (step[6]) is kept hidden to save space
            self.tree.insert("", "end", values=(i + 1, name, x, y, d, t, mode))

    # Drag and Drop functionality
    def on_drag_start(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self._drag_data = item
            # Visual feedback: Change cursor to a move icon
            self.tree.configure(cursor="fleur")
            # Apply a tag to the dragged item to change its appearance
            self.tree.item(item, tags=("dragging_item",))

    def on_drag_motion(self, event):
        if self._drag_data:
            target = self.tree.identify_row(event.y)
            if target:
                # Visual feedback: Highlight the potential drop target
                self.tree.selection_set(target)

    def on_drag_stop(self, event):
        # Reset cursor back to normal
        self.tree.configure(cursor="")
        # Remove the dragging tag from the original item
        if self._drag_data:
            self.tree.item(self._drag_data, tags=())
        target = self.tree.identify_row(event.y)
        if target and self._drag_data and target != self._drag_data:
            source_idx = self.tree.index(self._drag_data)
            target_idx = self.tree.index(target)
            
            # Move data in our list
            item = self.sequence.pop(source_idx)
            self.sequence.insert(target_idx, item)
            
            self.refresh_tree()
            # Select the moved item
            new_item_id = self.tree.get_children()[target_idx]
            self.tree.selection_set(new_item_id)
        self._drag_data = None

    def on_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        
        idx = self.tree.index(item_id)
        step = self.sequence[idx]

        # Create a custom popup for multi-field editing
        edit_win = tk.Toplevel(self.root)
        edit_win.title(f"Edit Step {idx+1}")
        edit_win.geometry("320x520")
        edit_win.configure(bg="#1c1c1c")
        edit_win.transient(self.root)
        edit_win.grab_set()

        # Create local variables for entry fields
        vars = {
            "name": tk.StringVar(value=step[5] if len(step) > 5 else f"Step {idx+1}"),
            "x": tk.StringVar(value=str(step[0])),
            "y": tk.StringVar(value=str(step[1])),
            "delay": tk.StringVar(value=str(step[2])),
            "type": tk.StringVar(value=step[3])
        }

        # UI Layout for edit window
        fields = [("Action Name:", "name"), ("Coordinate X:", "x"), ("Coordinate Y:", "y"), ("Delay (ms):", "delay")]
        for i, (label_text, key) in enumerate(fields):
            ttk.Label(edit_win, text=label_text).pack(pady=(10, 0))
            ttk.Entry(edit_win, textvariable=vars[key], width=20).pack(pady=5)

        ttk.Label(edit_win, text="Click Type:").pack(pady=(10, 0))
        ttk.Combobox(edit_win, textvariable=vars["type"], values=["left", "right", "double", "middle", "mouse4", "mouse5"], state="readonly").pack(pady=5)

        def save_edit():
            try:
                is_rel = step[4]
                win_title = step[6] if len(step) > 6 else ""
                self.sequence[idx] = (int(vars["x"].get()), int(vars["y"].get()), int(vars["delay"].get()), vars["type"].get(), is_rel, vars["name"].get(), win_title)
                self.refresh_tree()
                edit_win.destroy()
            except ValueError:
                messagebox.showerror("Error", "X, Y, and Delay must be integers.")

        ttk.Button(edit_win, text="Apply Changes", command=save_edit).pack(pady=20)

    def on_click(self, x, y, button, pressed):
        if pressed and self.is_recording:
            # Use pyautogui coordinates to match exactly what is shown in the status bar (logical pixels)
            x, y = pyautogui.position()
            
            now = time.time()
            delay = int(self.delay_var.get()) if self.delay_var.get().isdigit() else 500
            
            # Determine button type
            click_type = "left"
            if button == mouse.Button.right:
                click_type = "right"
            elif button == mouse.Button.middle:
                click_type = "middle"
            elif button == mouse.Button.x1:
                click_type = "mouse4"
            elif button == mouse.Button.x2:
                click_type = "mouse5"

            # Detect double click (if same button, same spot, within 300ms)
            if click_type == "left" and (now - self.last_click_data["time"] < 0.3):
                if abs(x - self.last_click_data["x"]) < 5 and abs(y - self.last_click_data["y"]) < 5:
                    if self.sequence:
                        self.sequence.pop()
                    click_type = "double"

            relative_active = self.rel_var.get()
            recorded_x, recorded_y = x, y
            target_win_title = ""
            
            if relative_active:
                win = gw.getActiveWindow()
                # Ignore the bot's own window
                if win and win.title != "Pro Auto-Clicker":
                    recorded_x = x - win.left
                    recorded_y = y - win.top
                    target_win_title = win.title
                else:
                    relative_active = False

            name = f"Recorded Step {len(self.sequence) + 1}"
            self.sequence.append((recorded_x, recorded_y, delay, click_type, relative_active, name, target_win_title))
            self.last_click_data = {"time": now, "x": x, "y": y}
            
            self.root.after(0, self.refresh_tree)

    def toggle_record(self):
        self.is_recording = not self.is_recording
        self.record_btn.config(text=f"{'■ STOP' if self.is_recording else '● Record'} (F7)")

    def run_sequence(self):
        try:
            loops = int(self.loop_var.get())
        except ValueError:
            loops = 1
            
        try:
            loop_wait = float(self.loop_delay_var.get()) / 1000.0
        except ValueError:
            loop_wait = 0
        
        iterations = 0
        while self.is_running:
            for step in self.sequence:
                if not self.is_running:
                    break
                
                x, y, delay_ms, click_type, is_rel = step[0], step[1], step[2], step[3], step[4]
                win_title = step[6] if len(step) > 6 else ""
                
                target_x, target_y = x, y
                if is_rel:
                    # Locate the specific window by title
                    try:
                        matches = gw.getWindowsWithTitle(win_title)
                        if matches:
                            # Use the first matching window found
                            target_win = matches[0]
                            target_x = target_win.left + x
                            target_y = target_win.top + y
                    except Exception:
                        # Fallback to recorded absolute coordinates if window lookup fails
                        pass

                # Add miniscule coordinate jitter (±1 pixel) to avoid perfect clicking
                target_x += random.randint(-1, 1)
                target_y += random.randint(-1, 1)

                # Map user-friendly names back to PyAutoGUI button names
                btn_map = {"mouse4": "x1", "mouse5": "x2"}
                exec_btn = btn_map.get(click_type, click_type)

                if click_type == "double":
                    pyautogui.doubleClick(target_x, target_y)
                else:
                    pyautogui.click(target_x, target_y, button=exec_btn)

                # Small random timing jitter (±15ms)
                time_jitter = random.uniform(-15, 15)
                time.sleep(max(0, (delay_ms + time_jitter) / 1000.0))
            
            iterations += 1
            if loops > 0 and iterations >= loops:
                self.is_running = False
                break
            
            if self.is_running and loop_wait > 0:
                time.sleep(loop_wait)
        
        self.is_running = False
        self.root.after(0, lambda: self.run_btn.config(text="▶ Start (F8)"))

    def toggle_run(self):
        if self.is_running:
            self.is_running = False
            self.run_btn.config(text="▶ Start (F8)")
        else:
            if not self.sequence:
                messagebox.showwarning("Warning", "Record some points first!")
                return
            self.is_running = True
            self.run_btn.config(text="■ STOP (F8)")
            threading.Thread(target=self.run_sequence, daemon=True).start()

    def start(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AutoClicker()
    app.start()
