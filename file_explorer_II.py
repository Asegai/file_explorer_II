import os
import tkinter as tk
from tkinter import ttk
import ctypes
import subprocess
import tkinter.messagebox as mb
import sys
from tkinter import ttk, Toplevel, Entry, Listbox, messagebox
from PIL import Image, ImageTk
import shutil
import time
import json 

class FileExplorer(tk.Tk):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FAVORITES_FILE = os.path.join(BASE_DIR, "favorites.json")
    exe_icon_path = os.path.join(BASE_DIR, "exe.ico")
    folder_icon_path = os.path.join(BASE_DIR, "folder.ico")
    text_icon_path = os.path.join(BASE_DIR, "image_2024-07-01_163309914.ico")

    def __init__(self):
        super().__init__()
        self.title("File Explorer")
        self.geometry("800x600")
        self.iconbitmap(os.path.join(self.BASE_DIR, "icon.ico"))

        self.top_frame = tk.Frame(self)
        self.top_frame.pack(side=tk.TOP, fill=tk.X)
        self.directory_entry = tk.Entry(self.top_frame, width=95)
        self.directory_entry.pack(side=tk.LEFT, padx=2, pady=2)
        self.placeholder_text = "Enter Directory Here"
        self.directory_entry.insert(0, self.placeholder_text)
        self.directory_entry.bind("<FocusIn>", self.remove_placeholder)
        self.directory_entry.bind("<FocusOut>", self.add_placeholder)
        self.directory_entry.bind("<Return>", lambda event: self.navigate_to_directory())

        self.search_icon = ImageTk.PhotoImage(Image.open(os.path.join(self.BASE_DIR, "search.png")).resize((20, 20), Image.LANCZOS))
        self.search_frame = tk.Frame(self.top_frame)
        self.search_button = tk.Button(self.search_frame, image=self.search_icon, command=self.open_search_window, padx=0, pady=0)
        self.search_button.pack(side=tk.RIGHT, padx=2, pady=2)
        self.search_frame.pack(side=tk.RIGHT, fill=tk.X)

        self.bottom_frame = tk.Frame(self)
        self.bottom_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(self.bottom_frame, selectmode='extended')
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

        self.favorites = self.load_favorites()

        self.load_icons()

        self.load_directory(os.path.expanduser("~"))
        self.tree.bind("<Double-1>", self.on_double_click)
        self.cut_paths = []
        self.copy_paths = []
        self.create_context_menu()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_icons(self):
        try:
            self.folder_icon = ImageTk.PhotoImage(Image.open(self.folder_icon_path).resize((16, 16), Image.LANCZOS))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load folder icon. Error: {e}")
            self.folder_icon = None

        try:
            self.text_icon = ImageTk.PhotoImage(Image.open(self.text_icon_path).resize((16, 16), Image.LANCZOS))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load text icon. Error: {e}")
            self.text_icon = None

        try:
            self.exe_icon = ImageTk.PhotoImage(Image.open(self.exe_icon_path).resize((16, 16), Image.LANCZOS))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load exe icon. Error: {e}")
            self.exe_icon = None

    def on_close(self):
        self.save_favorites()
        self.destroy()

    def navigate_to_directory(self):
        directory_path = self.directory_entry.get()
        if os.path.exists(directory_path) and os.path.isdir(directory_path):
            self.load_directory(directory_path)
        else:
            messagebox.showerror("Error", "The specified path does not exist or is not a directory.")

    def add_placeholder(self, event=None):
        if not self.directory_entry.get():
            self.directory_entry.insert(0, self.placeholder_text)
            self.directory_entry.config(fg='#C0C0C0')

    def remove_placeholder(self, event=None):
        if self.directory_entry.get() == self.placeholder_text:
            self.directory_entry.delete(0, tk.END)
            self.directory_entry.config(fg='black')

    def cut_item(self):
        self.cut_paths = [self.get_full_path(item_id) for item_id in self.tree.selection()]

    def delete_item(self):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        confirmed = messagebox.askyesno("Delete", "Selected items won't be available in the recycle bin. Are you sure you want to delete them?")
        if not confirmed:
            return
        
        for item_id in selected_items:
            full_path = self.get_full_path(item_id)
            try:
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                else:
                    os.remove(full_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete {full_path}. Error: {e}")
                return
        
        self.load_directory(os.path.dirname(full_path))

    def paste_item(self):
        destination_dir = self.get_full_path(self.tree.selection()[0])
        if self.cut_paths:
            for cut_path in self.cut_paths:
                if os.path.dirname(cut_path) == destination_dir:
                    messagebox.showwarning("Warning", "Pasted File in Same Location as Cut File")
                else:
                    shutil.move(cut_path, destination_dir)
            self.cut_paths = []
        elif self.copy_paths:
            for copy_path in self.copy_paths:
                if os.path.isdir(copy_path):
                    destination_path = os.path.join(destination_dir, os.path.basename(copy_path))
                    shutil.copytree(copy_path, destination_path)
                else:
                    shutil.copy2(copy_path, destination_dir)
            self.copy_paths = []
        
        self.context_menu.entryconfig("Paste Here", state="disabled")
        self.load_directory(destination_dir)

    def copy_item(self):
        self.copy_paths = [self.get_full_path(item_id) for item_id in self.tree.selection()]

    def show_properties(self):
        selected_items = self.tree.selection()
        for item_id in selected_items:
            item_path = self.get_full_path(item_id)
            if os.path.exists(item_path):
                size = os.path.getsize(item_path)
                creation_time = time.ctime(os.path.getctime(item_path))
                modification_time = time.ctime(os.path.getmtime(item_path))
                if os.path.isdir(item_path):
                    item_type = "Directory"
                    properties_message = f"Type: {item_type}\nSize: {self.format_size(size)}\nCreated: {creation_time}\nModified: {modification_time}"
                else:
                    item_type = "File"
                    _, extension = os.path.splitext(item_path)
                    properties_message = f"Type: {item_type}\nExtension: {extension}\nSize: {self.format_size(size)}\nCreated: {creation_time}\nModified: {modification_time}"
                messagebox.showinfo("Properties", properties_message)
            else:
                messagebox.showerror("Error", "One or more selected items do not exist.")
                return

    def rename_item(self):
        selected_items = self.tree.selection()
        for item_id in selected_items:
            old_name = self.tree.item(item_id, "text")
            rename_window = Toplevel(self)
            rename_window.title("Rename")
            rename_window.geometry("300x100")

            rename_label = tk.Label(rename_window, text="Enter new name:")
            rename_label.pack()

            rename_entry = Entry(rename_window)
            rename_entry.pack()
            rename_entry.insert(0, old_name)

            rename_button = tk.Button(rename_window, text="Rename", command=lambda id=item_id, entry=rename_entry: self.perform_rename(id, entry.get(), rename_window))
            rename_button.pack()

    def perform_rename(self, item_id, new_name, window):
        old_path = self.get_full_path(item_id)
        new_path = os.path.join(os.path.dirname(old_path), new_name)
        try:
            os.rename(old_path, new_path)
            self.tree.item(item_id, text=new_name)
            window.destroy()
            messagebox.showinfo("Success", "File/Folder renamed successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename. Error: {e}")

    def favorite_item(self):
        selected_items = self.tree.selection()
        for item_id in selected_items:
            full_path = self.get_full_path(item_id)
            if full_path in self.favorites:
                self.favorites.remove(full_path)
                messagebox.showinfo("Favorite", f"Removed {full_path} from favorites.")
            else:
                self.favorites.add(full_path)
                messagebox.showinfo("Favorite", f"Added {full_path} to favorites.")
        self.save_favorites()
        self.load_directory(os.path.dirname(full_path))

    def create_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Cut", command=self.cut_item)
        self.context_menu.add_command(label="Copy", command=self.copy_item)
        self.context_menu.add_command(label="Paste Here", command=self.paste_item)
        self.context_menu.add_command(label="Rename", command=self.rename_item)
        self.context_menu.add_command(label="Delete", command=self.delete_item)
        self.context_menu.add_command(label="Properties", command=self.show_properties)
        self.context_menu.add_command(label="Favorite/Unfavorite", command=self.favorite_item)
        self.context_menu.entryconfig("Paste Here", state="disabled")
        self.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        try:
            selected_items = self.tree.selection()
            if selected_items:
                self.context_menu.entryconfig("Paste Here", state="normal" if self.cut_paths or self.copy_paths else "disabled")
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
            messagebox.showinfo("Search Complete", f"Found {len(matches)} matches for '{query}'.\n{result_message}")
        else:
            messagebox.showinfo("Search Complete", "No matches found.")

    def filesystem_search(self, root_path, query):
        matches = []
        for root, dirs, files in os.walk(root_path):
            for file in files:
                if query in file.lower():
                    matches.append(os.path.join(root, file))
        return matches

    def load_directory(self, path):
        self.tree.delete(*self.tree.get_children())

        parent_node = self.tree.insert("", "end", text=path, open=True, values=("", ""))
        self.populate_tree(parent_node, path)

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

            favorite_dirs = [d for d in dirs if os.path.join(path, d) in self.favorites]
            favorite_files = [f for f in files if os.path.join(path, f[0]) in self.favorites]
            non_favorite_dirs = [d for d in dirs if os.path.join(path, d) not in self.favorites]
            non_favorite_files = [f for f in files if os.path.join(path, f[0]) not in self.favorites]

            for dir in favorite_dirs:
                node = self.tree.insert(parent_node, "end", text=dir, image=self.folder_icon if self.folder_icon else "", values=("", "Folder"))
                self.tree.insert(node, "end")

            for file, size, extension in favorite_files:
                icon = self.get_icon_for_extension(extension)
                self.tree.insert(parent_node, "end", text=file, image=icon if icon else "", values=(self.format_size(size), extension.upper() if extension != "Unknown" else extension))

            for dir in non_favorite_dirs:
                node = self.tree.insert(parent_node, "end", text=dir, image=self.folder_icon if self.folder_icon else "", values=("", "Folder"))
                self.tree.insert(node, "end")

            for file, size, extension in non_favorite_files:
                icon = self.get_icon_for_extension(extension)
                self.tree.insert(parent_node, "end", text=file, image=icon if icon else "", values=(self.format_size(size), extension.upper() if extension != "Unknown" else extension))

        except PermissionError:
            if not self.is_admin() and self.try_run_as_admin():
                return
            else:
                messagebox.showerror("Access Denied", "You do not have permission to access this directory.")

    def get_icon_for_extension(self, extension):
        if extension in ["pdf", "txt", "py", "html", "doc", "docx"]:
            return self.text_icon
        elif extension == "exe":
            return self.exe_icon
        else:
            return "" 

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def try_run_as_admin(self):
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

    def load_favorites(self):
        try:
            with open(self.FAVORITES_FILE, 'r') as f:
                return set(json.load(f))
        except FileNotFoundError:
            return set()

    def save_favorites(self):
        with open(self.FAVORITES_FILE, 'w') as f:
            json.dump(list(self.favorites), f)

if __name__ == "__main__":
    app = FileExplorer()
    app.mainloop()
