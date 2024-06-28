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

        self.tree.column("#0", width=800, minwidth=800, stretch=tkr.NO)

        self.tree.heading("#0", text="Name", anchor=tkr.W)

        self.load_directory(os.path.expanduser("~"))

    def load_directory(self, path):
        self.tree.delete(*self.tree.get_children())

        parent_node = self.tree.insert("", "end", text=path, open=True)
        self.populate_tree(parent_node, path)

    def populate_tree(self, parent_node, path):
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    self.tree.insert(parent_node, "end", text=item)
                else:
                    self.tree.insert(parent_node, "end", text=item)
        except PermissionError:
            pass

if __name__ == "__main__":
    app = FileExplorer()
    app.mainloop()
