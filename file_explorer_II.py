import os
import tkinter as tk
from tkinter import ttk
import ctypes
import subprocess
import tkinter.messagebox as mb
import sys
from tkinter import ttk, Toplevel, Entry, Listbox
from PIL import Image, ImageTk
import shutil


class FileExplorer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File Explorer")
        self.geometry("800x600")
        
        self.top_frame = tk.Frame(self)
        self.top_frame.pack(side=tk.TOP, fill=tk.X)
        self.directory_entry = tk.Entry(self.top_frame, width=95)
        self.directory_entry.pack(side=tk.LEFT, padx=2, pady=2)
        self.placeholder_text = "Enter Directory Here"
        self.directory_entry.insert(0, self.placeholder_text)
        self.directory_entry.bind("<FocusIn>", self.remove_placeholder)
        self.directory_entry.bind("<FocusOut>", self.add_placeholder)
        self.directory_entry.bind("<Return>", lambda event: self.navigate_to_directory())
        self.search_icon = ImageTk.PhotoImage(Image.open("C:/Users/aesas/Desktop/file_explorer_II/search.png").resize((20, 20), Image.Resampling.LANCZOS)) # make button smaller
        self.top_frame.pack(side=tk.TOP, fill=tk.X)
        self.bottom_frame = tk.Frame(self)
        self.search_frame = tk.Frame(self.top_frame) #
        self.search_button = tk.Button(self.search_frame, image=self.search_icon, command=self.open_search_window, padx=0, pady=0)
        self.search_button.pack(side=tk.RIGHT, padx=2, pady=2) #
        self.search_frame.pack(side=tk.RIGHT, fill=tk.X) 
        self.bottom_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(self.bottom_frame)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.search_button.pack(side=tk.RIGHT, padx=2, pady=2)
        self.search_entry = tk.Entry(self.search_frame)
        #! removed here
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
        self.cut_path = None 
        self.create_context_menu()

    def navigate_to_directory(self):
        directory_path = self.directory_entry.get()
        if os.path.exists(directory_path) and os.path.isdir(directory_path):
            self.load_directory(directory_path)
        else:
            mb.showerror("Error", "The specified path does not exist or is not a directory.")

    def add_placeholder(self, event=None):
        if not self.directory_entry.get():
            self.directory_entry.insert(0, self.placeholder_text)
            self.directory_entry.config(fg='#C0C0C0')

    def remove_placeholder(self, event=None):
        if self.directory_entry.get() == self.placeholder_text:
            self.directory_entry.delete(0, tk.END)
            self.directory_entry.config(fg='black')

    def cut_item(self):
        selected_item = self.tree.selection()[0]
        self.cut_path = self.get_full_path(selected_item)

    def paste_item(self):
        if not self.cut_path:
            return
        destination_dir = self.get_full_path(self.tree.selection()[0])
        if os.path.isdir(self.cut_path):
            shutil.move(self.cut_path, destination_dir)
        else:
            shutil.move(self.cut_path, destination_dir)
        self.cut_path = None 
        self.load_directory(destination_dir)

    #! context menu
    def create_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Cut", command=self.cut_item)
        self.context_menu.add_command(label="Paste Here", command=self.paste_item)
        self.context_menu.entryconfig("Paste Here", state="disabled")  # turn off when nothing to cut
        self.tree.bind("<Button-3>", self.show_context_menu) 

    def show_context_menu(self, event):
        try:
            item_id = self.tree.identify_row(event.y)
            if item_id:
                self.tree.selection_set(item_id)
                self.context_menu.entryconfig("Paste Here", state="normal" if self.cut_path else "disabled")
                self.context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"Error showing context menu: {e}")

    def open_search_window(self):
        search_window = Toplevel(self)
        search_window.title("Search")
        search_window.geometry("300x100")

        search_label = tk.Label(search_window, text="Enter search query:")
        search_label.pack()

        search_entry = Entry(search_window)
        search_entry.pack()

        search_button = tk.Button(search_window, text="Search", command=lambda: self.search_directory(search_entry.get()))
        search_button.pack()

    def search_directory(self, query):
        root_path = os.path.expanduser("~") 
        matches = self.filesystem_search(root_path, query.lower())
        if matches:
            result_message = "\n".join(matches[:10]) + ("\n..." if len(matches) > 10 else "") 
            mb.showinfo("Search Complete", f"Found {len(matches)} matches for '{query}'.\n{result_message}")
        else:
            mb.showinfo("Search Complete", "No matches found.")


    def filesystem_search(self, root_path, query):
        matches = []
        for root, dirs, files in os.walk(root_path):
            for file in files:
                if query in file.lower():
                    matches.append(os.path.join(root, file))
        return matches

    def recursive_search(self, parent, query, matches):
        for child in self.tree.get_children(parent):
            item_text = self.tree.item(child, "text")
            if query in item_text.lower():
                matches.append(child)
            self.recursive_search(child, query, matches) 


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
