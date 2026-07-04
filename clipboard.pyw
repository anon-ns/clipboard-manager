import tkinter as tk
from tkinter import ttk
import keyboard
import pyperclip
import threading
import time
import queue
import json
import os
import sys

# Lock file to prevent multiple instances
LOCK_FILE = "clipboard.lock"

def check_single_instance():
    """Exit if another instance is already running"""
    if os.path.exists(LOCK_FILE):
        print("⚠️ Clipboard manager already running!")
        sys.exit(1)
    
    # Create lock file
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

def cleanup_lock():
    """Remove lock file on exit"""
    try:
        os.remove(LOCK_FILE)
    except:
        pass

# At the start of main():
def main():
    check_single_instance()
    print("📋 Clipboard Manager Started!")
    print("-> Press [ Ctrl + Alt + V ] to open history menu.")
    
    # ... rest of code ...
    
    # Before mainloop ends, cleanup:
    try:
        root_scheduler.mainloop()
    finally:
        cleanup_lock()
        
# Configuration
MAX_HISTORY = None  # Infinite storage
HISTORY_FILE = "clipboard_storage.json"
clipboard_history = []

# Queue to safely communicate between background threads and the main thread
ui_queue = queue.Queue()

# Global tracking variables
active_menu_window = None
is_menu_pending = False  # Prevents multiple SHOW_MENU messages from being queued

# --- FILE STORAGE FUNCTIONS ---

def load_history():
    """Loads saved history from disk on startup"""
    global clipboard_history
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                clipboard_history = json.load(f)
        except Exception:
            clipboard_history = []  # Fallback if file is corrupted

def save_history():
    """Saves current history to disk"""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(clipboard_history, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving history: {e}")

# --- CORE FUNCTIONS ---

def save_to_history():
    """Triggered by hotkey: copies selected text and saves it explicitly"""
    try:
        # 1. Force a system copy of whatever text you currently have highlighted
        keyboard.send('ctrl+c')
        time.sleep(0.1)  # Brief pause to let the OS clipboard update
        
        # 2. Grab that text and pull it into your history file
        current_item = pyperclip.paste()
        if current_item:
            if current_item in clipboard_history:
                clipboard_history.remove(current_item)
            clipboard_history.insert(0, current_item)
            save_history() 
            print(f"💾 Saved to history: {current_item[:30]}...")
    except Exception as e:
        print(f"Error saving selected text: {e}")
        
def create_clipboard_window():
    """Creates the clipboard history window. Returns True if successful, False if already open."""
    global active_menu_window
    
    # Don't create if window already exists
    if active_menu_window is not None:
        active_menu_window.lift()
        active_menu_window.focus_force()
        return False
    
    root = tk.Toplevel() 
    active_menu_window = root 
    
    root.title("Clipboard History")
    root.attributes("-topmost", True)
    root.geometry("400x420") 
    root.resizable(False, False)
    
    label = tk.Label(root, text="Select an item to copy back:", font=("Arial", 11, "bold"), pady=10)
    label.pack()

    listbox = tk.Listbox(root, font=("Arial", 10), width=50, height=12)
    listbox.pack(padx=10, pady=5)

    def toggle_pin(event=None):
        try:
            selected_index = listbox.curselection()[0]
            actual_text = clipboard_history[selected_index]
            
            # If already pinned, unpin it by moving it out of pins (optional logic)
            # For simplicity, we can track pinned items by changing their string 
            # or keeping a parallel set. Let's toggle a prefix marker:
            if actual_text.startswith("📌 "):
                # Unpin
                new_text = actual_text[2:]
            else:
                # Pin
                new_text = "📌 " + actual_text
                
            clipboard_history[selected_index] = new_text
            save_history()
            
            # Refresh listbox display
            listbox.delete(selected_index)
            display_text = new_text.replace("\n", " ")
            if len(display_text) > 50:
                display_text = display_text[:47] + "..."
            listbox.insert(selected_index, display_text)
            listbox.selection_set(selected_index)
        except IndexError:
            pass

    # Bind the 'p' key to toggle pin status [cite: 16]
    root.bind('<p>', toggle_pin)
    root.bind('<P>', toggle_pin)
    
    def close_window():
        """Closes the window and resets the global reference"""
        global active_menu_window, is_menu_pending
        active_menu_window = None
        is_menu_pending = False  # Only reset when window actually closes
        try:
            root.destroy()
        except:
            pass

    def select_item():
        try:
            selected_index = listbox.curselection()[0]
            actual_text = clipboard_history[selected_index]
            pyperclip.copy(actual_text)
            print(f"📋 Re-copied: {actual_text[:30]}...")
        except IndexError:
            pass
        close_window()

    def delete_item(event=None):
        try:
            selected_index = listbox.curselection()[0]
            actual_text = clipboard_history[selected_index]
            
            # CHANGER: Prevent deletion if the item is pinned
            if actual_text.startswith("📌 "):
                print("⚠️ Cannot delete a pinned item! Press 'P' to unpin it first.")
                return
                
            clipboard_history.pop(selected_index)
            listbox.delete(selected_index)
            save_history()
            
            if listbox.size() > 0: 
                new_index = min(selected_index, listbox.size() - 1) 
                listbox.selection_set(new_index) 
                listbox.activate(new_index) 
        except IndexError: 
            pass 
        
    def open_json_file():
        try:
            if os.path.exists(HISTORY_FILE):
                os.startfile(HISTORY_FILE)
            else:
                print("⚠️ No JSON file found yet. Copy something first!")
        except Exception as e:
            print(f"Failed to open file: {e}")

    hint_label = tk.Label(root, text="[Enter] Copy & Close  |  [Delete/Backspace] Remove Item", font=("Arial", 9, "italic"), fg="gray")
    hint_label.pack(pady=5)

    open_file_btn = tk.Button(
        root, 
        text="📁 Open Storage File", 
        font=("Arial", 9, "bold"),
        bg="#e1e1e1",  
        fg="black",
        command=open_json_file
    )
    open_file_btn.pack(pady=10) 

    # Populate listbox
    for item in clipboard_history:
        display_text = item.replace("\n", " ")
        if len(display_text) > 50:
            display_text = display_text[:47] + "..."
        listbox.insert(tk.END, display_text)

    # Bind events
    listbox.bind('<Double-Button-1>', lambda e: select_item())
    root.bind('<Return>', lambda e: select_item())
    root.bind('<FocusOut>', lambda e: close_window())
    root.bind('<Escape>', lambda e: close_window())
    root.bind('<Delete>', delete_item)
    root.bind('<BackSpace>', delete_item)
    
    # Handle window close button
    root.protocol("WM_DELETE_WINDOW", close_window)

    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    root.lift()
    root.focus_force()
    listbox.focus_set()
    if listbox.size() > 0:
        listbox.selection_set(0)
    
    return True

# --- QUEUE MANAGEMENT ---

def process_queue(root_scheduler):
    """Process ONE message from the queue per cycle"""
    try:
        task = ui_queue.get_nowait()  # Get only ONE message
        if task == "SHOW_MENU":
            create_clipboard_window()
    except queue.Empty:
        pass
    
    root_scheduler.after(100, lambda: process_queue(root_scheduler))
    
last_trigger_time = 0

def trigger_menu():
    global is_menu_pending, last_trigger_time
    
    
    current_time = time.time()
    if current_time - last_trigger_time < 0.5:  # Ignore if within 500ms
        return
    
    last_trigger_time = current_time
    
    if not is_menu_pending:
        is_menu_pending = True
        ui_queue.put("SHOW_MENU")
def main():
    print("📋 Clipboard Manager Started!")
    print("-> Press [ Ctrl + Alt + V ] to open history menu.")

    load_history()

    # Start background clipboard watcher thread

    # Set up hotkey
    keyboard.add_hotkey("ctrl+alt+x", save_to_history)
    keyboard.add_hotkey("ctrl+alt+v", trigger_menu)

    # Main Tkinter scheduler loop
    root_scheduler = tk.Tk()
    root_scheduler.withdraw()  # Hide the root window
    root_scheduler.after(100, lambda: process_queue(root_scheduler))
    root_scheduler.mainloop()

if __name__ == "__main__":
    main()
