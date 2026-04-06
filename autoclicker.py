import time
import threading
import random
import json
t_lock = threading.Lock()
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import pyautogui
from pynput import mouse, keyboard

class AutoClicker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Pro Auto-Clicker")
        self.root.geometry("450x550")
        self.root.attributes('-topmost', True)

        self.sequence = []  # Stores (x, y, delay, type)
        self.is_recording = False
        self.is_running = False

        self.setup_ui()
        self.setup_listeners()

    def setup_ui(self):
        # Delay and Loop Settings
        settings_frame = ttk.LabelFrame(self.root, text=" Settings ", padding=10)
        settings_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(settings_frame, text="Click Delay (ms):").grid(row=0, column=0, sticky="w")
        self.delay_var = tk.StringVar(value="500")
        ttk.Entry(settings_frame, textvariable=self.delay_var, width=10).grid(row=0, column=1, padx=5)

        ttk.Label(settings_frame, text="Loops (0=∞):").grid(row=1, column=0, sticky="w", pady=5)
        self.loop_var = tk.StringVar(value="1")
        ttk.Entry(settings_frame, textvariable=self.loop_var, width=10).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(settings_frame, text="Click Type:").grid(row=0, column=2, padx=5, sticky="w")
        self.type_var = tk.StringVar(value="left")
        self.type_combo = ttk.Combobox(settings_frame, textvariable=self.type_var, values=["left", "right", "double"], width=8, state="readonly")
        self.type_combo.grid(row=0, column=3, padx=5)

        # Sequence List
        list_frame = ttk.LabelFrame(self.root, text=" Click Sequence ", padding=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(list_frame, columns=("Index", "X", "Y", "Delay", "Type"), show="headings", height=8)
        self.tree.heading("Index", text="#")
        self.tree.heading("X", text="X")
        self.tree.heading("Y", text="Y")
        self.tree.heading("Delay", text="Wait (ms)")
        self.tree.heading("Type", text="Type")
        self.tree.column("Index", width=30, anchor="center")
        self.tree.column("X", width=80, anchor="center")
        self.tree.column("Y", width=80, anchor="center")
        self.tree.column("Delay", width=80, anchor="center")
        self.tree.column("Type", width=80, anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.on_double_click)

        # Controls
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill="x")

        self.record_btn = ttk.Button(btn_frame, text="Record (F7)", command=self.toggle_record)
        self.record_btn.pack(side="left", padx=5)

        self.run_btn = ttk.Button(btn_frame, text="Start (F8)", command=self.toggle_run)
        self.run_btn.pack(side="left", padx=5)

        self.del_btn = ttk.Button(btn_frame, text="Delete Selected", command=self.delete_selected)
        self.del_btn.pack(side="left", padx=5)

        ttk.Button(btn_frame, text="Clear", command=self.clear_sequence).pack(side="right", padx=5)

        # File Controls
        file_frame = ttk.Frame(self.root, padding=10)
        file_frame.pack(fill="x")
        ttk.Button(file_frame, text="Save Sequence", command=self.save_sequence).pack(side="left", padx=5)
        ttk.Button(file_frame, text="Load Sequence", command=self.load_sequence).pack(side="left", padx=5)

        status_label = ttk.Label(self.root, text="F7: Record | F8: Start/Stop | F12: Exit", foreground="gray")
        status_label.pack(pady=5)

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
        for i, (x, y, delay, click_type) in enumerate(self.sequence):
            self.tree.insert("", "end", values=(i + 1, x, y, delay, click_type))

    def on_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        
        idx = self.tree.index(item_id)
        x, y, delay, click_type = self.sequence[idx]
        
        new_val = simpledialog.askstring("Edit Step", f"Edit step {idx+1} (X, Y, Delay, Type):", 
                                         initialvalue=f"{x}, {y}, {delay}, {click_type}", parent=self.root)
        if new_val:
            try:
                parts = [p.strip() for p in new_val.split(",")]
                if len(parts) == 4:
                    self.sequence[idx] = (int(parts[0]), int(parts[1]), int(parts[2]), parts[3])
                self.refresh_tree()
            except Exception:
                messagebox.showerror("Error", "Format: X (int), Y (int), Delay (int), Type (left/right/double)")

    def on_click(self, x, y, button, pressed):
        if pressed and self.is_recording:
            try:
                delay = int(self.delay_var.get())
            except ValueError:
                delay = 500

            click_type = self.type_var.get()
            self.sequence.append((x, y, delay, click_type))
            # Update GUI from thread safely
            self.root.after(0, lambda: self.tree.insert("", "end", values=(len(self.sequence), x, y, delay, click_type)))

    def toggle_record(self):
        self.is_recording = not self.is_recording
        color = "red" if self.is_recording else "black"
        self.record_btn.config(text=f"{'STOP' if self.is_recording else 'Record'} (F7)")
        if self.is_recording:
            self.root.title("RECORDING MODE - Click to add points")
        else:
            self.root.title("Pro Auto-Clicker")

    def run_sequence(self):
        try:
            loops = int(self.loop_var.get())
        except ValueError:
            loops = 1
        
        iterations = 0
        while self.is_running:
            for x, y, delay_ms, click_type in self.sequence:
                if not self.is_running:
                    break
                
                if click_type == "double":
                    pyautogui.doubleClick(x, y)
                else:
                    pyautogui.click(x, y, button=click_type)
                    
                # Randomize pause by +/- 10% to avoid detection
                jitter = random.uniform(-0.1, 0.1) * delay_ms
                time.sleep(max(0, (delay_ms + jitter) / 1000.0))
            
            iterations += 1
            if loops > 0 and iterations >= loops:
                self.is_running = False
                break
        
        self.is_running = False
        self.root.after(0, lambda: self.run_btn.config(text="Start (F8)"))

    def toggle_run(self):
        if self.is_running:
            self.is_running = False
            self.run_btn.config(text="Start (F8)")
        else:
            if not self.sequence:
                messagebox.showwarning("Warning", "Record some points first!")
                return
            self.is_running = True
            self.run_btn.config(text="STOP (F8)")
            threading.Thread(target=self.run_sequence, daemon=True).start()

    def start(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AutoClicker()
    app.start()
