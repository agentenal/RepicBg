import streamlit as st
import os
import time
import zipfile
import io
from PIL import Image
from rembg import remove, new_session
import numpy as np

# 设置页面
st.set_page_config(
    page_title="AI批量抠图换背景工具",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 缓存模型加载
@st.cache_resource
def load_model():
    return new_session("u2net")

# 处理单张图片
def process_image(image, bg_color=None):
    """
    处理单张图片，移除背景并应用新背景
    
    参数:
        image: PIL图像对象
        bg_color: 背景颜色 (R, G, B) 或 None表示透明背景
        
    返回:
        处理后的PIL图像对象
    """
    # 将图像转换为字节
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()
    
    # 设置背景颜色
    if bg_color:
        # 转换为整数元组 (R, G, B)
        bg_color = tuple(int(bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        # 添加Alpha通道
        bg_color = bg_color + (255,)
    else:
        # 透明背景
        bg_color = (255, 255, 255, 0)
    
    # 移除背景
    result = remove(
        img_bytes,
        session=st.session_state.model,
        bgcolor=bg_color
    )
    
    # 将结果转换为PIL图像
    return Image.open(io.BytesIO(result))

# 创建ZIP文件
def create_zip(processed_images):
    """
    创建包含所有处理后的图片的ZIP文件
    
    参数:
        processed_images: 处理后的图片列表
        
    返回:
        ZIP文件的字节数据
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
        for i, img in enumerate(processed_images):
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            zip_file.writestr(f"processed_{i+1}.png", img_byte_arr.getvalue())
    
    zip_buffer.seek(0)
    return zip_buffer

# 初始化会话状态
if 'model' not in st.session_state:
    st.session_state.model = load_model()

if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []

if 'processed_images' not in st.session_state:
    st.session_state.processed_images = []

# 页面标题
st.title("🖼️ AI批量抠图换背景工具")
st.markdown("""
使用AI技术批量移除图片背景并替换为纯色或透明背景。上传图片，设置背景选项，然后批量处理并下载结果。
""")

# 侧边栏 - 设置选项
with st.sidebar:
    st.header("⚙️ 设置选项")
    
    # 背景类型选择
    bg_type = st.radio("背景类型", ["纯色背景", "透明背景"], index=0)
    
    # 颜色选择器（仅在纯色背景时显示）
    bg_color = None
    if bg_type == "纯色背景":
        bg_color = st.color_picker("选择背景颜色", "#FFFFFF")
    
    # 批量处理按钮
    if st.button("🚀 开始批量处理", use_container_width=True, type="primary"):
        if not st.session_state.uploaded_files:
            st.warning("请先上传图片")
        else:
            with st.spinner("正在处理图片..."):
                st.session_state.processed_images = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, uploaded_file in enumerate(st.session_state.uploaded_files):
                    # 更新进度
                    progress = int((i + 1) / len(st.session_state.uploaded_files) * 100)
                    progress_bar.progress(progress)
                    status_text.text(f"处理中: {i+1}/{len(st.session_state.uploaded_files)} - {uploaded_file.name}")
                    
                    # 读取图片
                    image = Image.open(uploaded_file)
                    
                    # 处理图片
                    processed_image = process_image(image, bg_color if bg_type == "纯色背景" else None)
                    st.session_state.processed_images.append(processed_image)
                
                progress_bar.empty()
                status_text.success("✅ 处理完成!")
    
    # 分隔线
    st.divider()
    
    # 下载按钮
    if st.session_state.processed_images:
        # 创建ZIP文件
        zip_buffer = create_zip(st.session_state.processed_images)
        
        st.download_button(
            label="📥 下载所有处理后的图片",
            data=zip_buffer,
            file_name="processed_images.zip",
            mime="application/zip",
            use_container_width=True
        )
    
    # 重置按钮
    if st.button("🔄 重置所有内容", use_container_width=True):
        st.session_state.uploaded_files = []
        st.session_state.processed_images = []
        st.rerun()

# 文件上传区域
st.subheader("📤 上传图片")
uploaded_files = st.file_uploader(
    "拖放图片文件到这里或点击选择",
    type=["png", "jpg", "jpeg", "bmp"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

# 更新会话状态中的文件列表
if uploaded_files:
    st.session_state.uploaded_files = uploaded_files

# 显示上传的图片
if st.session_state.uploaded_files:
    st.subheader("📂 已上传图片")
    
    # 使用列布局显示缩略图
    cols = st.columns(4)
    for i, uploaded_file in enumerate(st.session_state.uploaded_files):
        with cols[i % 4]:
            try:
                # 显示缩略图
                image = Image.open(uploaded_file)
                st.image(
                    image, 
                    caption=uploaded_file.name,
                    use_column_width=True
                )
            except Exception as e:
                st.error(f"无法加载图片: {uploaded_file.name}")

# 显示处理后的图片
if st.session_state.processed_images:
    st.subheader("🖼️ 处理结果预览")
    st.info("只显示前4张处理后的图片预览，完整结果请下载ZIP文件")
    
    # 使用列布局显示缩略图
    cols = st.columns(4)
    for i, img in enumerate(st.session_state.processed_images[:4]):
        with cols[i % 4]:
            st.image(
                img, 
                caption=f"processed_{i+1}.png",
                use_column_width=True
            )

# 页脚
st.divider()
st.markdown("""
### 使用说明
1. 上传一张或多张图片（支持PNG, JPG, BMP格式）
2. 在左侧边栏选择背景类型（纯色或透明）
3. 点击"开始批量处理"按钮进行处理
4. 处理完成后点击"下载所有处理后的图片"按钮下载结果

**提示**: 首次使用时需要下载AI模型（约176MB），请耐心等待。
""")

# 隐藏Streamlit默认样式
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)