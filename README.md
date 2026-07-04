Clipboard Manager
A lightweight Python/Tkinter background utility that saves clipboard history only when explicitly triggered. Normal copy operations (Ctrl + C) are ignored.

⌨️ Hotkeys
Global Shortcuts (Anywhere)
Ctrl + Alt + X — Capture Selection Copies highlighted text or URLs into history. (Used instead of Ctrl + Alt + C to avoid browser address bar conflicts).

Ctrl + Alt + V — Open History Menu Brings up the manager UI panel.

UI Controls (Inside Menu)
Enter / Double-Click — Re-copy selected item and close menu.

P — Pin / Unpin item. Pinned items (📌) cannot be deleted.

Delete / Backspace — Remove unpinned item from history.

Escape — Close menu.

🛠️ Setup
Bash
pip install pyperclip keyboard
python clipboard.pyw
