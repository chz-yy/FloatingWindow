import json
import os
import tkinter as tk
from tkinter import font, ttk, messagebox, simpledialog
import logging

class FloatingWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("悬浮小窗")
        self.root.geometry("200x300+1250+100")
        self.root.overrideredirect(True)
        self.root.attributes("-alpha", 0.8)

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.create_custom_style()

        self.x = 0
        self.y = 0

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.load_content()

        if not self.notebook.tabs():
            self.add_new_page()

        self.create_bottom_buttons()
        self.bind_events()

    def create_custom_style(self):
        self.style = ttk.Style()
        self.style.theme_create("CustomNotebook", parent="alt", settings={
            "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0]}},
            "TNotebook.Tab": {
                "configure": {"padding": [5, 2], "background": "white"},
                "map": {
                    "background": [("selected", "white"), ("!selected", "#f0f0f0")],
                    "expand": [("selected", [1, 2, 1, 0])],  # 选中时稍微扩展
                }
            }
        })
        
        self.style.theme_use("CustomNotebook")

        self.style.layout("TNotebook", [('TNotebook.client', {'sticky': 'nswe'})])
        self.style.layout("TNotebook.Tab", [
            ('TNotebook.tab', {
                'sticky': 'nswe', 
                'children': [
                    ('TNotebook.padding', {
                        'side': 'top', 
                        'sticky': 'nswe',
                        'children': [
                            ('TNotebook.label', {'side': 'left', 'sticky': ''})
                        ]
                    })
                ]
            })
        ])

        self.style.configure("TNotebook", background='white')
        self.style.configure("TNotebook.Tab", background='#f0f0f0', foreground='black', padding=[5, 2])
        self.style.map("TNotebook.Tab", 
                       background=[("selected", "white"), ("!selected", "#f0f0f0")],
                       expand=[("selected", [1, 2, 1, 0])])  # 选中时稍微扩展

    def load_content(self):
        if os.path.exists("E:\\data.json"):
            with open("E:\\data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                for page_data in data.get("contents", []):
                    self.add_new_page(page_data["name"], page_data["content"])
        else:
            self.logger.warning("JSON file not found")

    def add_new_page(self, name=None, content=""):
        if name is None:
            page_number = len(self.notebook.tabs()) + 1
            name = f'Page {page_number}'

        new_page = ttk.Frame(self.notebook)
        self.notebook.add(new_page, text=name)
        text_box = tk.Text(new_page, wrap='word', height=10, width=30, bg='white', fg='black', bd=0)
        text_box.pack(fill=tk.BOTH, expand=True)
        text_box.configure(font=font.Font(family="宋体", size=14))
        text_box.insert(tk.END, content)

    def create_bottom_buttons(self):
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(fill=tk.X)

        self.prev_button = tk.Button(self.button_frame, text="<", command=self.prev_page)
        self.prev_button.pack(side=tk.LEFT)

        self.add_button = tk.Button(self.button_frame, text="+", command=lambda: self.add_new_page())
        self.add_button.pack(side=tk.LEFT)

        self.next_button = tk.Button(self.button_frame, text=">", command=self.next_page)
        self.next_button.pack(side=tk.LEFT)

        self.restore_button = tk.Button(self.button_frame, text="复原", command=self.restore_from_json)
        self.restore_button.pack(side=tk.LEFT)

        self.close_button = tk.Button(self.button_frame, text="×", command=self.close_current_page)
        self.close_button.pack(side=tk.RIGHT)

    def bind_events(self):
        self.notebook.bind("<ButtonPress-1>", self.start_move)
        self.notebook.bind("<B1-Motion>", self.do_move)
        self.notebook.bind("<ButtonRelease-1>", self.stop_move)
        self.root.bind("<Control-s>", self.save_all_content)
        self.notebook.bind("<Double-1>", self.on_double_click)
        self.notebook.bind("<Button-3>", self.show_tab_menu)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        x = self.root.winfo_x() - self.x + event.x
        y = self.root.winfo_y() - self.y + event.y
        self.root.geometry(f"+{x}+{y}")

    def stop_move(self, event):
        pass

    def on_double_click(self, event):
        element = self.notebook.identify(event.x, event.y)
        if "label" in element:
            index = self.notebook.index("@%d,%d" % (event.x, event.y))
            self.rename_tab_inline(index)

    def rename_tab_inline(self, index):
        current_name = self.notebook.tab(index, "text")
        entry = tk.Entry(self.notebook)
        entry.insert(0, current_name)
        entry.select_range(0, tk.END)
        entry.focus_set()
        entry.bind("<Return>", lambda e: self.finish_rename(index, entry))
        entry.bind("<FocusOut>", lambda e: self.finish_rename(index, entry))
        self.notebook.tab(index, text="")
        entry.place(x=self.notebook.bbox(index)[0], y=self.notebook.bbox(index)[1],
                    width=self.notebook.bbox(index)[2] - self.notebook.bbox(index)[0],
                    height=self.notebook.bbox(index)[3] - self.notebook.bbox(index)[1])

    def finish_rename(self, index, entry):
        new_name = entry.get()
        if new_name:
            self.notebook.tab(index, text=new_name)
        else:
            self.notebook.tab(index, text=self.notebook.tab(index, "text"))
        entry.destroy()

    def show_tab_menu(self, event):
        clicked_tab = self.notebook.tk.call(self.notebook._w, "identify", "tab", event.x, event.y)
        if clicked_tab != "":
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="重命名", command=lambda: self.rename_tab(clicked_tab))
            menu.add_command(label="删除", command=lambda: self.delete_tab(clicked_tab))
            menu.post(event.x_root, event.y_root)

    def rename_tab(self, tab_id):
        current_name = self.notebook.tab(tab_id, "text")
        new_name = simpledialog.askstring("重命名", "输入新的标签名:", initialvalue=current_name)
        if new_name:
            self.notebook.tab(tab_id, text=new_name)

    def delete_tab(self, tab_id):
        if len(self.notebook.tabs()) > 1:
            index = self.notebook.index(tab_id)
            self.delete_page_data(index)
            self.notebook.forget(tab_id)

    def delete_page_data(self, index):
        if os.path.exists("E:\\data.json"):
            with open("E:\\data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if "contents" in data and index < len(data["contents"]):
                del data["contents"][index]
                
                with open("E:\\data.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

    def prev_page(self):
        current_index = self.notebook.index(self.notebook.select())
        if current_index > 0:
            self.notebook.select(current_index - 1)

    def next_page(self):
        current_index = self.notebook.index(self.notebook.select())
        if current_index < len(self.notebook.tabs()) - 1:
            self.notebook.select(current_index + 1)

    def close_current_page(self):
        current = self.notebook.select()
        if len(self.notebook.tabs()) > 1:
            index = self.notebook.index(current)
            self.notebook.forget(current)

    def save_all_content(self, event=None):
        contents = []
        for tab in self.notebook.tabs():
            text_box = self.notebook.nametowidget(tab).winfo_children()[0]
            contents.append({
                "name": self.notebook.tab(tab, "text"),
                "content": text_box.get("1.0", tk.END).strip()
            })
        with open("E:\\data.json", "w", encoding="utf-8") as f:
            json.dump({"contents": contents}, f, ensure_ascii=False, indent=4)

    def restore_from_json(self):
        # 关闭所有现有标签页
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)

        # 重新加载内容
        self.load_content()

        # 如果没有页面被加载，创建一个默认页面
        if not self.notebook.tabs():
            self.add_new_page()

    def on_close(self):
        if messagebox.askyesno("确认退出", "是否要保存更改并退出？"):
            self.save_all_content()
            self.root.destroy()
        elif messagebox.askyesno("确认退出", "是否要直接退出？未保存的更改将丢失。"):
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FloatingWindow(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
