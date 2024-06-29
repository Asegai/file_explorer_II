import os
import tkinter as tk # change name to tk
from tkinter import ttk
import ctypes
import subprocess
import tkinter.messagebox as mb
import sys
from tkinter import ttk, Toplevel, Entry, Listbox
from PIL import Image, ImageTk # read https://pypi.org/project/pillow/


class FileExplorer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File Explorer")
        self.geometry("800x600")

        # button here
        self.search_icon = ImageTk.PhotoImage(Image.open("C:/Users/aesas/Desktop/file_explorer_II/search.png").resize((20, 20), Image.Resampling.LANCZOS)) # make button smaller
        self.top_frame = tk.Frame(self)
        self.top_frame.pack(side=tk.TOP, fill=tk.X)
        self.bottom_frame = tk.Frame(self)
        self.bottom_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.search_button = tk.Button(self.top_frame, image=self.search_icon, command=self.open_search_window, padx=0, pady=0)
        self.search_button.pack(side=tk.RIGHT, padx=2, pady=2, anchor='ne') # put in top right corner
        self.tree = ttk.Treeview(self.bottom_frame)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.bottom_frame, orient="vertical", command=self.tree.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.tree["columns"] = ("size", "type")
        self.tree.column("#0", width=300, minwidth=300, stretch=tk.NO)
        self.tree.column("size", width=100, minwidth=100, stretch=tk.NO)
        self.tree.column("type", width=100, minwidth=100, stretch=tk.NO) 

        self.tree.heading("#0", text="Name", anchor=tk.W)
        self.tree.heading("size", text="Size", anchor=tk.W)
        self.tree.heading("type", text="Type", anchor=tk.W)

        self.load_directory(os.path.expanduser("~"))
        self.tree.bind("<Double-1>", self.on_double_click)

    #! search window
    def open_search_window(self):
        pass





    def load_directory(self, path):
        self.tree.delete(*self.tree.get_children())

        parent_node = self.tree.insert("", "end", text=path, open=True, values=("", ""))
        self.populate_tree(parent_node, path)

    def is_admin(self):
        """Check if the current process has administrative privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False


    def populate_tree(self, parent_node, path):
        try:
            dirs = []
            files = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    dirs.append(item)
                else:
                    extension = os.path.splitext(item)[1][1:] if os.path.splitext(item)[1] else "Unknown"
                    files.append((item, os.path.getsize(item_path), extension))
            
            dirs.sort()
            files.sort(key=lambda x: (x[2], x[0]))
            
            for dir in dirs:
                node = self.tree.insert(parent_node, "end", text=dir, values=("", "Folder"))
                self.tree.insert(node, "end")
            
            for file, size, extension in files:
                self.tree.insert(parent_node, "end", text=file, values=(self.format_size(size), extension.upper() if extension != "Unknown" else extension))
        except PermissionError:
            if not self.is_admin() and self.try_run_as_admin():
                return
            else:
                mb.showerror("Access Denied", "You do not have permission to access this directory.")

    
    def try_run_as_admin(self):
        """Attempt to re-run the application with admin rights only if not already running as admin."""
        if self.is_admin():
            return True
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit(0)  
        except Exception as e:
            print(f"Error elevating privileges: {e}")
            return False

    def on_double_click(self, event):
        item_id = self.tree.selection()[0]
        path = self.get_full_path(item_id)
        if os.path.isdir(path):
            self.tree.delete(*self.tree.get_children(item_id))
            self.populate_tree(item_id, path)
        else:
            os.startfile(path)

    def get_full_path(self, item_id):
        path = self.tree.item(item_id, "text")
        parent_id = self.tree.parent(item_id)
        while parent_id:
            path = os.path.join(self.tree.item(parent_id, "text"), path)
            parent_id = self.tree.parent(parent_id)
        return path

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0

if __name__ == "__main__":
    app = FileExplorer()
    app.mainloop()
