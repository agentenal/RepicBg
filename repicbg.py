import os
import sys
import io
import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox
from PIL import Image, ImageTk
import threading
import requests
from tkinterdnd2 import TkinterDnD, DND_FILES
import sv_ttk
from colorpicker import pick_screen_color

# ======================== 配置部分 ========================
MODEL_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx"
MODEL_NAME = "u2net.onnx"
MODEL_DIR = os.path.join(os.path.expanduser("~"), ".u2net")
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)

# ======================== 工具函数 ========================
def download_file(url, save_path):
    """带进度条的下载函数"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        chunk_size = 8192
        downloaded = 0

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                f.write(chunk)
                downloaded += len(chunk)
                progress = (downloaded / total_size) * 100
                sys.stdout.write(f"\r下载进度: {progress:.1f}%")
                sys.stdout.flush()

        print("\n下载完成！")
        return True
    except Exception as e:
        print(f"\n下载失败: {str(e)}")
        return False

def check_model():
    """检查模型文件是否存在"""
    if not os.path.exists(MODEL_PATH):
        print("未找到模型文件，开始下载...")
        if not download_file(MODEL_URL, MODEL_PATH):
            messagebox.showerror(
                "模型下载失败",
                f"无法下载AI模型文件\n"
                f"请手动下载: {MODEL_URL}\n"
                f"并保存到: {MODEL_PATH}"
            )
            return False
    return True

# ======================== 主应用类 ========================
class AIBackgroundReplacer(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI证件照批量处理工具")
        self.geometry("1400x900")
        self.minsize(1200, 700)

        # 应用现代化主题
        self.theme_mode = "light"  # 默认主题
        sv_ttk.set_theme(self.theme_mode)

        # 状态变量
        self.bg_color = (255, 255, 255)  # 默认白色背景
        self.image_files = []
        self.current_image = None
        self.session = None
        self.view_mode = "thumbnail"  # 默认缩略图模式
        self.recent_colors = [(255, 255, 255)]  # 最近5个背景色

        # 初始化UI
        self.setup_ui()

        # 初始化AI模型
        self.init_model()

        # 窗口居中
        self.center_window()

    def center_window(self):
        """窗口居中显示"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def init_model(self):
        """初始化AI模型"""
        if not check_model():
            return

        try:
            from rembg import new_session
            self.session = new_session("u2net")
            print("AI模型加载成功")
        except Exception as e:
            messagebox.showerror("AI加载失败", f"无法加载AI模型:\n{str(e)}")

    def toggle_theme(self):
        """切换明亮/黑暗模式"""
        self.theme_mode = "dark" if self.theme_mode == "light" else "light"
        sv_ttk.set_theme(self.theme_mode)

    def setup_ui(self):
        """设置用户界面"""
        # 主容器
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建可调整区域
        self.paned_main = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.paned_main.pack(fill=tk.BOTH, expand=True)

        # ========== 左侧文件列表 ==========
        left_frame = ttk.LabelFrame(self.paned_main, text="文件列表", padding=10)
        left_frame.pack_propagate(False)
        left_frame.configure(width=260)
        self.paned_main.add(left_frame, weight=1)

        # 顶部工具栏
        toolbar_frame = ttk.Frame(left_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))

        # 主题切换按钮
        self.theme_btn = ttk.Button(toolbar_frame, text="切换主题",
                                    command=self.toggle_theme, width=10)
        self.theme_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # 视图模式切换按钮
        switch_frame = ttk.Frame(toolbar_frame)
        switch_frame.pack(side=tk.LEFT, padx=0)
        self.switch_list_btn = ttk.Button(switch_frame, text="列表视图",
                                          command=lambda: self.set_view_mode("list"))
        self.switch_list_btn.pack(side=tk.LEFT, padx=2)
        self.switch_thumb_btn = ttk.Button(switch_frame, text="缩略图视图",
                                           command=lambda: self.set_view_mode("thumbnail"))
        self.switch_thumb_btn.pack(side=tk.LEFT, padx=2)

        # 文件操作按钮
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        self.add_btn = ttk.Button(
            btn_frame, text="添加图片",
            command=self.add_images, width=8
        )
        self.add_btn.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)

        self.folder_btn = ttk.Button(
            btn_frame, text="添加文件夹",
            command=self.add_folder, width=8
        )
        self.folder_btn.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)

        self.clear_btn = ttk.Button(
            btn_frame, text="清空列表",
            command=self.clear_list, width=8
        )
        self.clear_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 文件列表容器
        self.list_container = ttk.Frame(left_frame)
        self.list_container.pack(fill=tk.BOTH, expand=True)

        # 列表模式
        self.list_frame = ttk.Frame(self.list_container)
        scrollbar = ttk.Scrollbar(self.list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox = tk.Listbox(
            self.list_frame,
            selectmode=tk.SINGLE,
            relief=tk.FLAT,
            font=('Segoe UI', 11),
            yscrollcommand=scrollbar.set,
            highlightthickness=0
        )
        self.file_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_select)
        self.file_listbox.drop_target_register(DND_FILES)
        self.file_listbox.dnd_bind('<<Drop>>', self.on_drop_files)

        # 缩略图模式（初始隐藏）
        self.thumbnail_frame = ttk.Frame(self.list_container)
        self.thumbnail_canvas = tk.Canvas(self.thumbnail_frame, highlightthickness=0)
        self.thumbnail_scroll = ttk.Scrollbar(self.thumbnail_frame, orient="vertical", command=self.thumbnail_canvas.yview)
        self.thumbnail_container = ttk.Frame(self.thumbnail_canvas)
        self.thumbnail_canvas.configure(yscrollcommand=self.thumbnail_scroll.set)
        self.thumbnail_scroll.pack(side="right", fill="y")
        self.thumbnail_canvas.pack(side="left", fill="both", expand=True)
        self.thumbnail_canvas.create_window((0, 0), window=self.thumbnail_container, anchor="nw")
        self.thumbnail_container.bind("<Configure>", lambda e: self.thumbnail_canvas.configure(
            scrollregion=self.thumbnail_canvas.bbox("all")
        ))

        # 默认显示列表模式
        self.set_view_mode("list")

        # ========== 中间预览区域 ==========
        center_frame = ttk.Frame(self.paned_main)
        self.paned_main.add(center_frame, weight=3)

        # 上下布局对比
        compare_frame = ttk.Frame(center_frame)
        compare_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 原图
        self.src_frame = ttk.LabelFrame(compare_frame, text="原始图片", padding=10)
        self.src_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=0, pady=(0, 4))

        self.src_container = ttk.Frame(self.src_frame)
        self.src_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.src_canvas = tk.Canvas(
            self.src_container, bg="#f8f9fa", highlightthickness=0
        )
        self.src_canvas.pack(fill=tk.BOTH, expand=True)

        # 效果图
        self.dst_frame = ttk.LabelFrame(compare_frame, text="效果预览", padding=10)
        self.dst_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=0, pady=(4, 0))

        self.dst_container = ttk.Frame(self.dst_frame)
        self.dst_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.dst_canvas = tk.Canvas(
            self.dst_container, bg="#f8f9fa", highlightthickness=0
        )
        self.dst_canvas.pack(fill=tk.BOTH, expand=True)

        # ========== 右侧控制面板 ==========
        right_frame = ttk.LabelFrame(self.paned_main, text="工具面板", padding=10)
        right_frame.pack_propagate(False)
        right_frame.configure(width=300)
        self.paned_main.add(right_frame, weight=1)

        # 背景设置
        bg_frame = ttk.LabelFrame(right_frame, text="背景设置", padding=(15, 10))
        bg_frame.pack(fill=tk.X, pady=(0, 10))

        self.color_btn = ttk.Button(bg_frame, text="选择背景颜色",
                                    command=self.choose_color)
        self.color_btn.pack(fill=tk.X, pady=5)

        self.color_preview = tk.Canvas(bg_frame, width=40, height=40,
                                       highlightthickness=1, highlightbackground="#cccccc")
        self.color_preview.pack(pady=5)
        self.color_preview.create_rectangle(0, 0, 40, 40, fill="#FFFFFF", outline="")

        # 最近颜色区
        ttk.Label(bg_frame, text="最近使用的颜色:").pack(anchor=tk.W, pady=(10, 5))
        self.recent_color_frame = ttk.Frame(bg_frame)
        self.recent_color_frame.pack(fill=tk.X, pady=(0, 10))
        self.update_recent_colors()

        # 背景类型选择
        bg_type_frame = ttk.Frame(bg_frame)
        bg_type_frame.pack(fill=tk.X, pady=(5, 0))

        self.bg_type = tk.StringVar(value="color")
        ttk.Radiobutton(bg_type_frame, text="纯色背景", variable=self.bg_type,
                        value="color", command=self.update_bg_preview).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(bg_type_frame, text="透明背景", variable=self.bg_type,
                        value="transparent", command=self.update_bg_preview).pack(side=tk.LEFT)

        # 处理操作
        process_frame = ttk.LabelFrame(right_frame, text="图片处理", padding=(15, 10))
        process_frame.pack(fill=tk.X, pady=10)

        self.cutout_btn = ttk.Button(process_frame, text="抠出人像",
                                     command=self.auto_cutout)
        self.cutout_btn.pack(fill=tk.X, pady=8)

        self.replace_btn = ttk.Button(process_frame, text="替换背景",
                                      command=self.batch_process)
        self.replace_btn.pack(fill=tk.X, pady=8)

        # 导出操作
        export_frame = ttk.LabelFrame(right_frame, text="导出选项", padding=(15, 10))
        export_frame.pack(fill=tk.X, pady=(0, 10))

        self.export_btn = ttk.Button(export_frame, text="批量导出",
                                     command=self.batch_export)
        self.export_btn.pack(fill=tk.X, pady=8)

        # 状态栏
        status_frame = ttk.Frame(self)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        self.progress = ttk.Progressbar(status_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 5))

        self.status_var = tk.StringVar(value="准备就绪")
        status_bar = ttk.Label(status_frame, textvariable=self.status_var,
                               anchor=tk.W, padding=(10, 5))
        status_bar.pack(fill=tk.X)

        # 自定义样式
        self.style = ttk.Style()
        self.configure_styles()

    def configure_styles(self):
        """配置自定义样式"""
        # 按钮样式
        self.style.configure("Accent.TButton", font=("Segoe UI", 11), padding=8)
        self.style.configure("Large.TButton", font=("Segoe UI", 12), padding=10)

        # 应用按钮样式
        self.color_btn.configure(style="Accent.TButton")
        self.cutout_btn.configure(style="Large.TButton")
        self.replace_btn.configure(style="Large.TButton")
        self.export_btn.configure(style="Large.TButton")

    # ======================== 功能方法 ========================
    def set_view_mode(self, mode):
        """设置文件列表视图模式，并高亮切换按钮"""
        self.view_mode = mode

        # 隐藏所有视图
        self.list_frame.pack_forget()
        self.thumbnail_frame.pack_forget()

        # 显示选中的视图
        if mode == "list":
            self.list_frame.pack(fill=tk.BOTH, expand=True)
            self.update_file_list()
        else:
            self.thumbnail_frame.pack(fill=tk.BOTH, expand=True)
            self.update_thumbnail_view()

    def add_images(self):
        """添加图片文件"""
        files = filedialog.askopenfilenames(
            title="选择图片文件",
            filetypes=[("图片文件", "*.jpg;*.jpeg;*.png;*.bmp")]
        )

        if files:
            self.image_files.extend(files)
            self.update_file_list()
            self.status_var.set(f"已添加 {len(files)} 张图片")

    def add_folder(self):
        """添加文件夹中的所有图片"""
        folder = filedialog.askdirectory(title="选择图片文件夹")
        if not folder:
            return

        valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp')
        files = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if os.path.splitext(f)[1].lower() in valid_extensions
        ]

        if files:
            self.image_files.extend(files)
            self.update_file_list()
            self.status_var.set(f"已添加 {len(files)} 张图片")

    def clear_list(self):
        """清空文件列表"""
        self.image_files = []
        self.update_file_list()
        self.src_canvas.delete("all")
        self.dst_canvas.delete("all")
        self.status_var.set("已清空文件列表")

    def on_drop_files(self, event):
        """处理拖拽文件"""
        files = self.tk.splitlist(event.data)
        valid_files = []

        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                valid_files.append(f)

        if valid_files:
            self.image_files.extend(valid_files)
            self.update_file_list()
            self.status_var.set(f"已添加 {len(valid_files)} 张图片")

    def update_file_list(self):
        """更新文件列表显示（列表模式）"""
        self.file_listbox.delete(0, tk.END)
        for i, f in enumerate(self.image_files, 1):
            self.file_listbox.insert(tk.END, f"{i}. {os.path.basename(f)}")

        # 同时更新缩略图视图
        if self.view_mode == "thumbnail":
            self.update_thumbnail_view()

    def update_thumbnail_view(self):
        """更新缩略图视图"""
        # 清除现有缩略图
        for widget in self.thumbnail_container.winfo_children():
            widget.destroy()

        # 添加新缩略图
        for i, img_path in enumerate(self.image_files):
            try:
                img = Image.open(img_path)
                img.thumbnail((80, 80))
                photo = ImageTk.PhotoImage(img)

                frame = ttk.Frame(self.thumbnail_container)
                frame.pack(fill=tk.X, pady=5, padx=5)

                # 缩略图容器
                thumb_frame = ttk.Frame(frame)
                thumb_frame.pack(side=tk.LEFT, padx=(0, 10))

                # 添加序号标签
                index_label = ttk.Label(thumb_frame, text=str(i + 1),
                                        font=("Segoe UI", 9, "bold"),
                                        foreground="gray")
                index_label.pack(anchor=tk.NW)

                # 缩略图
                label_img = ttk.Label(thumb_frame, image=photo)
                label_img.image = photo
                label_img.pack()

                # 文件名
                filename = os.path.basename(img_path)
                if len(filename) > 20:
                    filename = filename[:17] + "..."

                label_text = ttk.Label(frame, text=filename,
                                       anchor="w", justify=tk.LEFT)
                label_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

                # 绑定点击事件
                label_img.bind("<Button-1>", lambda e, idx=i: self.select_thumbnail(idx))
                label_text.bind("<Button-1>", lambda e, idx=i: self.select_thumbnail(idx))

            except Exception as e:
                print(f"无法加载缩略图: {str(e)}")

    def select_thumbnail(self, index):
        """选择缩略图"""
        if 0 <= index < len(self.image_files):
            self.current_image = self.image_files[index]
            self.show_preview(self.current_image)

    def on_file_select(self, event):
        """选择文件时显示预览"""
        selection = self.file_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if 0 <= index < len(self.image_files):
            self.current_image = self.image_files[index]
            self.show_preview(self.current_image)

    def show_preview(self, image_path):
        """显示图片预览（原图和效果图）"""
        try:
            img = Image.open(image_path)

            # 计算适合画布的尺寸
            canvas_width = self.src_container.winfo_width() - 20
            canvas_height = self.src_container.winfo_height() - 20

            # 保持宽高比缩放
            img_ratio = img.width / img.height
            canvas_ratio = canvas_width / canvas_height

            if img_ratio > canvas_ratio:
                new_width = min(img.width, canvas_width)
                new_height = int(new_width / img_ratio)
            else:
                new_height = min(img.height, canvas_height)
                new_width = int(new_height * img_ratio)

            img = img.resize((new_width, new_height), Image.LANCZOS)
            self.src_photo = ImageTk.PhotoImage(img)

            self.src_canvas.delete("all")
            x = (self.src_container.winfo_width() - new_width) // 2
            y = (self.src_container.winfo_height() - new_height) // 2
            self.src_canvas.create_image(x, y, anchor=tk.NW, image=self.src_photo)

            # 效果区清空
            self.dst_canvas.delete("all")
        except Exception as e:
            messagebox.showerror("图片加载错误", f"无法加载图片:\n{str(e)}")

    def show_result(self, result_img):
        """显示效果图"""
        # 计算适合画布的尺寸
        canvas_width = self.dst_container.winfo_width() - 20
        canvas_height = self.dst_container.winfo_height() - 20

        # 保持宽高比缩放
        img_ratio = result_img.width / result_img.height
        canvas_ratio = canvas_width / canvas_height

        if img_ratio > canvas_ratio:
            new_width = min(result_img.width, canvas_width)
            new_height = int(new_width / img_ratio)
        else:
            new_height = min(result_img.height, canvas_height)
            new_width = int(new_height * img_ratio)

        result_img = result_img.resize((new_width, new_height), Image.LANCZOS)
        self.dst_photo = ImageTk.PhotoImage(result_img)

        self.dst_canvas.delete("all")
        x = (self.dst_container.winfo_width() - new_width) // 2
        y = (self.dst_container.winfo_height() - new_height) // 2
        self.dst_canvas.create_image(x, y, anchor=tk.NW, image=self.dst_photo)

    def update_recent_colors(self):
        """更新最近使用的颜色预览"""
        # 清空
        for w in self.recent_color_frame.winfo_children():
            w.destroy()

        # 显示最近5个颜色
        for c in self.recent_colors[-5:][::-1]:
            hex_color = '#%02x%02x%02x' % c
            btn = tk.Button(self.recent_color_frame, bg=hex_color, width=3, height=1,
                            relief=tk.RAISED, bd=1,
                            command=lambda col=c: self.set_bg_color(col))
            btn.pack(side=tk.LEFT, padx=3, ipadx=5, ipady=5)

    def set_bg_color(self, color):
        """设置背景颜色"""
        self.bg_color = color
        hex_color = '#%02x%02x%02x' % color
        self.color_preview.delete("all")
        self.color_preview.create_rectangle(0, 0, 40, 40, fill=hex_color, outline="")

        # 更新最近颜色列表
        if color not in self.recent_colors:
            self.recent_colors.append(color)
            if len(self.recent_colors) > 5:
                self.recent_colors = self.recent_colors[-5:]

        self.update_recent_colors()

    def update_bg_preview(self):
        """更新背景预览"""
        if self.bg_type.get() == "transparent":
            # 创建棋盘格透明背景
            from PIL import ImageDraw
            bg = Image.new('RGBA', (40, 40), (0, 0, 0, 0))
            draw = ImageDraw.Draw(bg)
            for i in range(0, 40, 10):
                for j in range(0, 40, 10):
                    if (i // 10 + j // 10) % 2 == 0:
                        draw.rectangle([i, j, i + 10, j + 10], fill="#CCCCCC")

            self.transparent_bg = ImageTk.PhotoImage(bg)
            self.color_preview.delete("all")
            self.color_preview.create_image(0, 0, anchor=tk.NW, image=self.transparent_bg)
        else:
            # 显示纯色背景
            hex_color = '#%02x%02x%02x' % self.bg_color
            self.color_preview.delete("all")
            self.color_preview.create_rectangle(0, 0, 40, 40, fill=hex_color, outline="")

    def choose_color(self):
        """选择背景颜色"""
        import tkinter.simpledialog
        choice = tkinter.simpledialog.askstring(
            "取色方式", "输入1=自定义取色, 2=屏幕吸管取色 (推荐先安装pyautogui)", initialvalue="1")

        if choice == "2":
            rgb = pick_screen_color()
            if rgb:
                self.set_bg_color(tuple(map(int, rgb)))
        else:
            color = colorchooser.askcolor(title="选择背景颜色", initialcolor=self.bg_color)
            if color[0]:
                self.set_bg_color(tuple(map(int, color[0])))

    def auto_cutout(self):
        """自动抠人像"""
        if not self.current_image or not self.session:
            messagebox.showwarning("操作提示", "请先选择图片!")
            return

        try:
            from rembg import remove
            with open(self.current_image, "rb") as f:
                img_bytes = f.read()

            result = remove(
                img_bytes,
                session=self.session,
                bgcolor=(255, 255, 255, 0) if self.bg_type.get() == "transparent" else self.bg_color
            )

            result_img = Image.open(io.BytesIO(result))
            self.show_result(result_img)
            self.status_var.set("人像抠图完成")
        except Exception as e:
            messagebox.showerror("处理错误", f"人像抠图失败:\n{str(e)}")

    def batch_process(self):
        """批量替换背景"""
        if not self.image_files or not self.session:
            messagebox.showwarning("操作提示", "请先添加图片!")
            return

        output_dir = filedialog.askdirectory(title="选择输出文件夹")
        if not output_dir:
            return

        self.progress["maximum"] = len(self.image_files)
        self.progress["value"] = 0

        def worker():
            from rembg import remove

            for i, img_path in enumerate(self.image_files, 1):
                try:
                    filename = os.path.basename(img_path)
                    name, ext = os.path.splitext(filename)
                    output_path = os.path.join(output_dir, f"{name}_processed{ext}")

                    with open(img_path, "rb") as f:
                        result = remove(
                            f.read(),
                            session=self.session,
                            bgcolor=(255, 255, 255, 0) if self.bg_type.get() == "transparent" else self.bg_color
                        )

                    with open(output_path, "wb") as f:
                        f.write(result)

                    # 更新进度
                    self.progress["value"] = i
                    self.status_var.set(f"处理中: {i}/{len(self.image_files)} - {filename}")

                except Exception as e:
                    print(f"处理 {img_path} 失败: {str(e)}")

            # 处理完成
            self.status_var.set(f"批量处理完成! 共处理 {len(self.image_files)} 张图片")
            messagebox.showinfo("完成", "批量处理完成！")

        # 在后台线程中处理
        threading.Thread(target=worker, daemon=True).start()

    def batch_export(self):
        """批量导出图片"""
        if not self.image_files:
            messagebox.showwarning("操作提示", "请先添加图片!")
            return

        output_dir = filedialog.askdirectory(title="选择导出文件夹")
        if not output_dir:
            return

        self.progress["maximum"] = len(self.image_files)
        self.progress["value"] = 0

        def worker():
            for i, img_path in enumerate(self.image_files, 1):
                try:
                    filename = os.path.basename(img_path)
                    output_path = os.path.join(output_dir, filename)

                    img = Image.open(img_path)
                    img.save(output_path)

                    # 更新进度
                    self.progress["value"] = i
                    self.status_var.set(f"导出中: {i}/{len(self.image_files)} - {filename}")

                except Exception as e:
                    print(f"导出 {img_path} 失败: {str(e)}")

            # 处理完成
            self.status_var.set(f"导出完成! 共导出 {len(self.image_files)} 张图片")
            messagebox.showinfo("完成", "批量导出完成！")

        # 在后台线程中处理
        threading.Thread(target=worker, daemon=True).start()

# ======================== 主程序 ========================
if __name__ == "__main__":
    # 检查依赖
    try:
        from rembg import new_session
        import PIL
        import requests
        import numpy
    except ImportError as e:
        messagebox.showerror(
            "缺少依赖",
            f"请先安装必要依赖:\n{e}\n\n"
            "pip install pillow requests numpy rembg tkinterdnd2 sv-ttk"
        )
        sys.exit(1)

    app = AIBackgroundReplacer()
    app.mainloop()    