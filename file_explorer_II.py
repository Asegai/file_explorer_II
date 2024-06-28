import os
import tkinter as tkr
from tkinter import ttk

class FileExplorer(tkr.Tk):
    def __init__(self):
        super().__init__()

        self.title("File Explorer")
        self.geometry("800x600")

        
        self.tree = ttk.Treeview(self)
        self.tree.pack(fill=tkr.BOTH, expand=True)

        
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscroll=self.scrollbar.set)

      
        self.tree["columns"] = ("size", "type")
        self.tree.column("#0", width=300, minwidth=300, stretch=tkr.NO)
        self.tree.column("size", width=100, minwidth=100, stretch=tkr.NO)
        self.tree.column("type", width=100, minwidth=100, stretch=tkr.NO)

    
        self.tree.heading("#0", text="Name", anchor=tkr.W)
        self.tree.heading("size", text="Size", anchor=tkr.W)
        self.tree.heading("type", text="Type", anchor=tkr.W)

        
        self.load_directory(os.path.expanduser("~"))

  
        self.tree.bind("<Double-1>", self.on_double_click)

    def load_directory(self, path):
        self.tree.delete(*self.tree.get_children())

   
        parent_node = self.tree.insert("", "end", text=path, open=True, values=("", ""))
        self.populate_tree(parent_node, path)

    def populate_tree(self, parent_node, path):
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    node = self.tree.insert(parent_node, "end", text=item, values=("", "Folder"))
                    self.tree.insert(node, "end")
                else:
                    size = os.path.getsize(item_path)
                    self.tree.insert(parent_node, "end", text=item, values=(self.format_size(size), "File"))
        except PermissionError:
            pass

    def on_double_click(self, event):
        item_id = self.tree.selection()[0]
        path = self.get_full_path(item_id)
        if os.path.isdir(path):
            self.tree.delete(*self.tree.get_children(item_id))
            self.populate_tree(item_id, path)

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
