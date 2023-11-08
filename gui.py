import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog, ttk
from subprocess import Popen
import json
import threading
import os
import sys


class LiveRecorderGUI:
    def __init__(self, root):
        self.path_button = None
        self.stop_button = None
        self.start_button = None
        self.add_button = None
        self.tree = None
        self.quality_combobox = None
        self.root = root
        self.root.title("抖音直播下载")
        self.process = None  # 用于存储子进程的引用
        self.config = './config/config.json'  # Define this before setup_ui()
        self.url_config = './config/url_config.json'  # Define this before setup_ui()
        self.setup_ui()
        self.update_interval = 10000  # 每隔 10 秒更新一次 Treeview
        self.update_treeview()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """在窗口关闭时调用的方法。"""
        # 首先检查是否有录制正在进行，如果有，则停止录制
        if self.process:
            self.stop_recording()
        # 然后销毁窗口
        self.root.destroy()

    def setup_ui(self):
        # 创建一个Frame来包含按钮
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y, expand=True)

        # 创建一个新的Frame来包裹按钮，并让它可以在button_frame中居中
        center_frame = tk.Frame(button_frame)
        center_frame.pack(expand=True)

        # 在center_frame内部创建按钮，并使用anchor=tk.CENTER使它们居中
        self.add_button = tk.Button(center_frame, text="添加直播间", command=self.add_url)
        self.add_button.pack(side=tk.TOP, fill=tk.X)

        self.start_button = tk.Button(center_frame, text="开始下载", command=self.start_recording)
        self.start_button.pack(side=tk.TOP, fill=tk.X)

        self.stop_button = tk.Button(center_frame, text="停止下载", command=self.stop_recording)
        self.stop_button.pack(side=tk.TOP, fill=tk.X)

        # 在center_frame内部创建选择视频路径的按钮
        self.path_button = tk.Button(center_frame, text="选择下载保存路径", command=self.choose_directory)
        self.path_button.pack(side=tk.TOP, fill=tk.X)

        # 视频质量的选择框
        quality_label = tk.Label(center_frame, text="选择下载质量:")
        quality_label.pack(side=tk.TOP, fill=tk.X)
        self.quality_combobox = ttk.Combobox(center_frame,
                                             values=["蓝光", "超清", "高清", "标清"],
                                             state="readonly")
        self.quality_combobox.set("蓝光")  # 设置默认值
        self.quality_combobox.pack(side=tk.TOP, fill=tk.X)
        self.quality_combobox.bind('<<ComboboxSelected>>', self.update_video_quality)

        # 树形视图区域
        self.tree = ttk.Treeview(self.root, columns=('url', 'description', 'startTime', 'isLiving'), show='headings')
        self.tree.heading('url', text="直播间链接")
        self.tree.heading('description', text="主播名称")
        self.tree.heading('startTime', text="开始录制时间")
        self.tree.heading('isLiving', text="直播状态")
        self.tree.pack(side=tk.RIGHT, padx=5, pady=5, fill=tk.BOTH, expand=True)

    def add_url(self):
        # 从对话框获取信息并添加到配置文件
        url = simpledialog.askstring("添加直播", "请输入直播链接:")

        if url:
            new_entry = {
                "url": url,
                "description": "",
                "startTime": "",
                "isLiving": False
            }
            urls = self.load_urls()
            urls.append(new_entry)
            with open(self.url_config, 'w', encoding="utf-8-sig") as file:
                json.dump(urls, file, indent=4)
            self.load_urls()

    def update_treeview(self):
        """定期检查 JSON 文件并更新 Treeview."""
        self.load_urls()  # 加载最新的 URLs
        # 设置定时器，每隔一定时间重复调用该方法
        self.root.after(self.update_interval, self.update_treeview)

    def start_recording(self):
        # 启动录制进程
        self.process = Popen(['python', self.resource_path('main.py')])
        messagebox.showinfo("直播", "开始直播录制。")

    def stop_recording(self):
        # 停止录制进程
        if self.process:
            self.process.terminate()
            self.process = None
            messagebox.showinfo("直播", "已停止直播录制。")

    def load_urls(self):
        # 从配置文件加载直播链接到树形视图
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            with open(self.url_config, 'r', encoding="utf-8-sig") as file:
                urls = json.load(file)
                for entry in urls:
                    self.tree.insert('', 'end',
                                     values=(entry['url'], entry['description'], entry['startTime'], entry['isLiving']))
            return urls
        except FileNotFoundError:
            with open(self.url_config, 'w', encoding="utf-8-sig") as file:
                json.dump([], file)  # 如果文件不存在，创建文件
            return []

    def update_video_quality(self, event):
        # 更新配置文件中的video_quality字段
        video_quality = self.quality_combobox.get()
        self.update_config({'video_quality': video_quality})
        print("finish")

    def choose_directory(self):
        # 弹出对话框让用户选择目录
        directory = filedialog.askdirectory()
        if directory:
            # 将选择的目录路径保存到配置文件的 video_path 字段
            self.update_config({'video_save_path': directory})

    def update_config(self, updates):
        # 创建并启动线程来处理 I/O
        threading.Thread(target=self._update_config_thread, args=(updates,), daemon=True).start()

    def _update_config_thread(self, updates):
        """在单独的线程中执行耗时的 I/O 操作"""
        try:
            # 打开文件并加载 JSON 数据
            with open(self.config, 'r', encoding='utf-8-sig') as file:
                config_data = json.load(file)

            # 更新 JSON 数据
            config_data.update(updates)

            # 将更新后的 JSON 数据写回文件
            with open(self.config, 'w', encoding='utf-8-sig') as file:
                json.dump(config_data, file, ensure_ascii=False, indent=4)

        except Exception as e:
            # 在 GUI 中显示错误消息
            self.show_error_message(f"更新配置文件时发生错误：{e}")

    def show_error_message(self, message):
        """在 GUI 线程中显示错误消息"""
        messagebox.showerror("错误", message)

    def resource_path(self, relative_path):
        """ 获取资源的绝对路径。用于PyInstaller的--onefile。 """
        try:
            # PyInstaller创建的临时文件夹
            base_path = sys._MEIPASS
        except Exception:
            # 如果不是使用PyInstaller打包，则正常使用相对路径
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)


if __name__ == "__main__":
    root = tk.Tk()
    app = LiveRecorderGUI(root)
    root.mainloop()
