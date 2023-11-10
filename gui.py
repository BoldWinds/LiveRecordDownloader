import os
import signal
import sys
import psutil
import subprocess
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog, ttk
from config import *


class LiveRecorderGUI:
    def __init__(self, root):
        self.proc = None
        self.config_path = './config/config.json'  # Define this before setup_ui()
        self.config = Config(self.config_path)

        # --------UI--------
        self.path_button = None
        self.stop_button = None
        self.start_button = None
        self.add_button = None
        self.tree = None
        self.quality_combobox = None
        self.root = root
        self.root.title("抖音直播下载")
        self.setup_ui()
        self.update_interval = 3000  # 每隔 3 秒更新一次 Treeview
        self.update_treeview()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        # 创建一个Frame来包含按钮
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y, expand=True)

        # 创建一个新的Frame来包裹按钮，并让它可以在button_frame中居中
        center_frame = tk.Frame(button_frame)
        center_frame.pack(expand=True)

        # 在center_frame内部创建按钮，并使用anchor=tk.CENTER使它们居中
        self.add_button = tk.Button(center_frame, text="添加直播间", command=self.add_live_room)
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

    def on_close(self):
        """在窗口关闭时调用的方法。"""
        # 将config保存
        self.config.save_config()
        # 首先检查是否有录制正在进行，如果有，则停止录制
        self.stop_recording()
        # 然后销毁窗口
        self.root.destroy()

    def add_live_room(self):
        # 从对话框获取信息并添加到配置文件
        url = simpledialog.askstring("添加直播", "请输入直播链接:")
        if url:
            live_room = LiveRoomConfig(url=url, description="", start_time="", is_recording=False, is_living="停止直播")
            self.config.live_rooms.append(live_room)
            self.config.save_config()

    def choose_directory(self):
        # 弹出对话框让用户选择目录
        directory = filedialog.askdirectory()
        if directory:
            # 将选择的目录路径保存到配置文件的 video_path 字段
            self.config.video_save_path = directory
            self.config.save_config()

    def update_video_quality(self, event):
        # 更新配置文件中的video_quality字段
        video_quality = self.quality_combobox.get()
        self.config.video_quality = video_quality
        self.config.save_config()
        print("update video quality")

    def update_treeview(self):
        """定期检查 JSON 文件并更新 Treeview."""
        print("update treeview")
        self.load_urls()  # 加载最新的 URLs
        # 设置定时器，每隔一定时间重复调用该方法
        self.root.after(self.update_interval, self.update_treeview)

    def start_recording(self):
        if self.proc is None:
            try:
                self.proc = subprocess.Popen(['python', 'main.py'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)

                # 启动一个线程来异步读取输出
                def read_output(proc):
                    while True:
                        output = proc.stdout.readline()
                        if proc.poll() is not None and output == '':
                            break
                        if output:
                            print(output.strip().decode('utf-8'))
                    proc.stdout.close()

                # 启动读取 stdout 的线程
                thread = threading.Thread(target=read_output, args=(self.proc,))
                thread.daemon = True
                thread.start()
            except Exception as e:
                print("启动录制时发生错误:", e)
            messagebox.showinfo("直播", "开始直播录制。")
        else:
            messagebox.showinfo("直播", "已经有一个直播录制正在进行。")

    def stop_recording(self):
        os.killpg(os.getpgid(os.getpid()), signal.SIGTERM)

    def load_urls(self):
        self.config.load()
        for i in self.tree.get_children():
            self.tree.delete(i)
        for room in self.config.live_rooms:
            self.tree.insert('', 'end', values=(room.url, room.description, room.start_time, room.is_living))


if __name__ == "__main__":
    root = tk.Tk()
    app = LiveRecorderGUI(root)
    root.mainloop()
