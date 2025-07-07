import os
import sys
import io
import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox
from PIL import Image, ImageTk
import threading
import requests
from tkinterdnd2 import TkinterDnD, DND_FILES
import sv_ttk  # 现代化主题库

# ======================== 配置部分 ========================
MODEL_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx"
MODEL_NAME = "u2net.onnx"
MODEL_DIR = os.path.join(os.path.expanduser("~"), ".u2net")
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)

# 图标路径配置（使用开源图标）
ICON_DIR = "icons"
os.makedirs(ICON_DIR, exist_ok=True)
ICONS = {
    "add": "add_icon.png",
    "clear": "clear_icon.png",
    "color": "color_icon.png",
    "cutout": "cutout_icon.png",
    "replace": "replace_icon.png",
    "export": "export_icon.png",
    "list": "list_icon.png",
    "thumbnail": "thumbnail_icon.png",
    "folder": "folder_icon.png",
    "process": "process_icon.png"
}

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

def download_icons():
    """下载开源图标（在实际应用中替换为本地路径）"""
    # 这里仅作演示，实际应使用本地图标文件
    icon_urls = {
        "add": "https://cdn-icons-png.flaticon.com/512/2997/2997933.png",
        "clear": "https://cdn-icons-png.flaticon.com/512/660/660252.png",
        "color": "https://cdn-icons-png.flaticon.com/512/1048/1048964.png",
        "cutout": "https://cdn-icons-png.flaticon.com/512/1048/1048971.png",
        "replace": "https://cdn-icons-png.flaticon.com/512/1048/1048966.png",
        "export": "https://cdn-icons-png.flaticon.com/512/3580/3580088.png",
        "list": "https://cdn-icons-png.flaticon.com/512/833/833471.png",
        "thumbnail": "https://cdn-icons-png.flaticon.com/512/833/833593.png",
        "folder": "https://cdn-icons-png.flaticon.com/512/3580/3580088.png",
        "process": "https://cdn-icons-png.flaticon.com/512/1995/1995455.png"
    }
    
    for name, url in icon_urls.items():
        path = os.path.join(ICON_DIR, ICONS[name])
        if not os.path.exists(path):
            try:
                response = requests.get(url)
                with open(path, 'wb') as f:
                    f.write(response.content)
            except:
                pass  # 如果下载失败，使用默认按钮文本

def get_icon(name, size=(24, 24)):
    """获取图标"""
    path = os.path.join(ICON_DIR, ICONS[name])
    if os.path.exists(path):
        img = Image.open(path)
        img = img.resize(size)
        return ImageTk.PhotoImage(img)
    return None

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
        self.geometry("1200x800")
        
        # 应用现代化主题
        sv_ttk.set_theme("light")
        
        # 下载图标
        download_icons()
        
        # 状态变量
        self.bg_color = (255, 255, 255)  # 默认白色背景
        self.image_files = []
        self.current_image = None
        self.session = None
        self.view_mode = "list"  # 列表模式或缩略图模式
        
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

    def setup_ui(self):
        """设置用户界面"""
        # 主容器
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # ========== 左侧文件列表 ==========
        left_frame = ttk.LabelFrame(main_frame, text="文件列表", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10), pady=5, expand=True)
        
        # 文件操作按钮
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 添加图标按钮
        self.add_icon = get_icon("add")
        ttk.Button(btn_frame, text="添加图片", image=self.add_icon, 
                  compound=tk.LEFT, command=self.add_images).pack(side=tk.LEFT, padx=5)
        
        self.clear_icon = get_icon("clear")
        ttk.Button(btn_frame, text="清空列表", image=self.clear_icon,
                  compound=tk.LEFT, command=self.clear_list).pack(side=tk.LEFT, padx=5)
        
        # 视图模式切换
        view_frame = ttk.Frame(btn_frame)
        view_frame.pack(side=tk.RIGHT, padx=5)
        
        self.list_icon = get_icon("list")
        ttk.Button(view_frame, image=self.list_icon, 
                  command=lambda: self.set_view_mode("list")).pack(side=tk.LEFT, padx=2)
        
        self.thumbnail_icon = get_icon("thumbnail")
        ttk.Button(view_frame, image=self.thumbnail_icon,
                  command=lambda: self.set_view_mode("thumbnail")).pack(side=tk.LEFT, padx=2)
        
        # 文件列表容器
        self.list_container = ttk.Frame(left_frame)
        self.list_container.pack(fill=tk.BOTH, expand=True)
        
        # 列表模式
        self.list_frame = ttk.Frame(self.list_container)
        self.list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(
            self.list_frame,
            selectmode=tk.SINGLE,
            bg="white",
            relief=tk.FLAT,
            font=('Segoe UI', 10),
            yscrollcommand=scrollbar.set
        )
        self.file_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_select)
        
        # 拖拽支持
        self.file_listbox.drop_target_register(DND_FILES)
        self.file_listbox.dnd_bind('<<Drop>>', self.on_drop_files)
        
        # 缩略图模式（初始隐藏）
        self.thumbnail_frame = ttk.Frame(self.list_container)
        self.thumbnail_canvas = tk.Canvas(self.thumbnail_frame, bg='white')
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
        center_frame = ttk.Frame(main_frame)
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 原始图像预览
        self.src_frame = ttk.LabelFrame(center_frame, text="原始图片", padding=10)
        self.src_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.src_canvas = tk.Canvas(self.src_frame, bg="#f5f5f5", highlightthickness=0)
        self.src_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ========== 右侧控制面板 ==========
        right_frame = ttk.Frame(main_frame, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # 背景设置
        bg_frame = ttk.LabelFrame(right_frame, text="背景设置", padding=10)
        bg_frame.pack(fill=tk.X, pady=5)
        
        self.color_icon = get_icon("color")
        ttk.Button(bg_frame, text="背景颜色", image=self.color_icon, compound=tk.LEFT,
                  command=self.choose_color).pack(fill=tk.X, pady=5)
        
        self.color_preview = tk.Canvas(bg_frame, width=40, height=40, bg="#FFFFFF", highlightthickness=1, 
                                     highlightbackground="#cccccc")
        self.color_preview.pack(pady=5)
        
        # 背景类型
        self.bg_type = tk.StringVar(value="color")
        ttk.Radiobutton(bg_frame, text="纯色背景", variable=self.bg_type, 
                       value="color").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(bg_frame, text="透明背景", variable=self.bg_type, 
                       value="transparent").pack(anchor=tk.W, pady=2)
        
        # 处理操作
        process_frame = ttk.LabelFrame(right_frame, text="图片处理", padding=10)
        process_frame.pack(fill=tk.X, pady=5)
        
        self.cutout_icon = get_icon("cutout")
        ttk.Button(process_frame, text="抠出人像", image=self.cutout_icon, compound=tk.LEFT,
                  command=self.auto_cutout).pack(fill=tk.X, pady=5)
        
        self.replace_icon = get_icon("replace")
        ttk.Button(process_frame, text="替换背景", image=self.replace_icon, compound=tk.LEFT,
                  command=self.batch_process).pack(fill=tk.X, pady=5)
        
        # 导出操作
        export_frame = ttk.LabelFrame(right_frame, text="导出选项", padding=10)
        export_frame.pack(fill=tk.X, pady=5)
        
        self.export_icon = get_icon("export")
        ttk.Button(export_frame, text="批量导出", image=self.export_icon, compound=tk.LEFT,
                  command=self.batch_export).pack(fill=tk.X, pady=5)
        
        # 状态栏
        status_frame = ttk.Frame(self)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        self.progress = ttk.Progressbar(status_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 5))
        
        self.status_var = tk.StringVar(value="准备就绪")
        status_bar = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X)

    # ======================== 功能方法 ========================
    def set_view_mode(self, mode):
        """设置文件列表视图模式"""
        self.view_mode = mode
        
        if mode == "list":
            self.thumbnail_frame.pack_forget()
            self.list_frame.pack(fill=tk.BOTH, expand=True)
            self.update_file_list()
        else:
            self.list_frame.pack_forget()
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

    def clear_list(self):
        """清空文件列表"""
        self.image_files = []
        self.update_file_list()
        self.src_canvas.delete("all")
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
                frame.pack(fill=tk.X, pady=2, padx=5)
                
                label_img = ttk.Label(frame, image=photo)
                label_img.image = photo
                label_img.pack(side=tk.LEFT, padx=5)
                
                label_text = ttk.Label(frame, text=os.path.basename(img_path)[:20] + "...", 
                                     width=20, anchor="w")
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
        """显示图片预览"""
        try:
            img = Image.open(image_path)
            img.thumbnail((500, 500))
            
            # 显示原始图像
            self.src_photo = ImageTk.PhotoImage(img)
            self.src_canvas.delete("all")
            canvas_width = self.src_canvas.winfo_width()
            canvas_height = self.src_canvas.winfo_height()
            x = (canvas_width - img.width) // 2
            y = (canvas_height - img.height) // 2
            self.src_canvas.create_image(x, y, anchor=tk.NW, image=self.src_photo)
            
        except Exception as e:
            messagebox.showerror("图片加载错误", f"无法加载图片:\n{str(e)}")

    def choose_color(self):
        """选择背景颜色"""
        color = colorchooser.askcolor(title="选择背景颜色", initialcolor=self.bg_color)
        if color[0]:
            self.bg_color = tuple(map(int, color[0]))
            self.color_preview.config(bg=color[1])

    def auto_cutout(self):
        """自动抠人像"""
        if not self.current_image or not self.session:
            return
            
        try:
            from rembg import remove
            
            with open(self.current_image, "rb") as f:
                img_bytes = f.read()
            
            # 使用AI移除背景
            result = remove(
                img_bytes,
                session=self.session,
                bgcolor=(255, 255, 255, 0) if self.bg_type.get() == "transparent" else self.bg_color
            )
            
            # 显示结果
            result_img = Image.open(io.BytesIO(result))
            result_img.thumbnail((500, 500))
            
            self.dst_photo = ImageTk.PhotoImage(result_img)
            self.src_canvas.delete("all")
            canvas_width = self.src_canvas.winfo_width()
            canvas_height = self.src_canvas.winfo_height()
            x = (canvas_width - result_img.width) // 2
            y = (canvas_height - result_img.height) // 2
            self.src_canvas.create_image(x, y, anchor=tk.NW, image=self.dst_photo)
            
            self.status_var.set("人像抠图完成")
            
        except Exception as e:
            messagebox.showerror("处理错误", f"人像抠图失败:\n{str(e)}")

    def batch_process(self):
        """批量替换背景"""
        if not self.image_files or not self.session:
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
                    output_path = os.path.join(output_dir, filename)
                    
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
    except ImportError:
        messagebox.showerror(
            "缺少依赖",
            "请先安装必要依赖:\n"
            "pip install pillow requests numpy rembg tkinterdnd2 sv-ttk"
        )
        sys.exit(1)
    
    app = AIBackgroundReplacer()
    app.mainloop()