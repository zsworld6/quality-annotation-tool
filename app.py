import streamlit as st
import json
import os
from pathlib import Path
from PIL import Image
import io

# 页面配置
st.set_page_config(
    page_title="质量评分标注工具",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 质量评分选项
QUALITY_OPTIONS = [
    "P0(质量很好)",
    "P1(质量一般)", 
    "P2(质量差，信息量少)"
]

# 获取项目根目录
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"

# 确保目录存在
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_jsonl_file(file_path):
    """加载JSONL文件"""
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        st.error(f"第{line_num}行JSON解析错误: {e}")
        return data
    except FileNotFoundError:
        st.error(f"找不到文件: {file_path}")
        return []
    except Exception as e:
        st.error(f"读取文件时出错: {e}")
        return []

def load_existing_annotations(output_file):
    """加载已有的标注结果"""
    annotations = {}
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        # 使用url_id作为标识符
                        annotations[data.get('url_id')] = data
        except Exception as e:
            st.error(f"读取已有标注时出错: {e}")
    return annotations

def display_image(image_path, image_base_dir):
    """显示图片"""
    # 处理路径
    if os.path.isabs(image_path) and os.path.exists(image_path):
        full_path = image_path
    else:
        # 拼接基础目录
        full_path = os.path.join(image_base_dir, image_path)
    
    if os.path.exists(full_path):
        try:
            image = Image.open(full_path)
            st.image(image, use_column_width=True)
            st.caption(f"图片: {os.path.basename(full_path)}")
        except Exception as e:
            st.error(f"无法显示图片: {e}")
    else:
        st.warning("图片文件不存在")
        # 显示占位图片或文本
        st.text("📷 图片占位符")
        st.caption(f"预期路径: {full_path}")

def save_annotations_to_file(annotations, output_file):
    """保存所有标注到文件"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for url_id, data_item in annotations.items():
                f.write(json.dumps(data_item, ensure_ascii=False) + '\n')
        return True
    except Exception as e:
        st.error(f"保存文件时出错: {e}")
        return False

def main():
    st.title("🏷️ 质量评分标注工具")
    
    # 侧边栏配置
    st.sidebar.header("📁 文件配置")
    
    # 文件选择方式
    file_source = st.sidebar.radio(
        "选择数据源",
        ["仓库数据文件", "上传文件", "输入文件路径"]
    )
    
    input_file = None
    
    if file_source == "仓库数据文件":
        # 获取仓库中的JSONL文件
        jsonl_dir = BASE_DIR / "data" / "jsonl"
        if jsonl_dir.exists():
            jsonl_files = list(jsonl_dir.glob("*.jsonl"))
            if jsonl_files:
                file_names = [f.name for f in jsonl_files]
                selected_file = st.sidebar.selectbox(
                    "选择数据文件",
                    file_names
                )
                input_file = str(jsonl_dir / selected_file)
                st.sidebar.success(f"✅ 已选择: {selected_file}")
            else:
                st.sidebar.warning("仓库中没有找到JSONL文件")
        else:
            st.sidebar.warning("数据目录不存在")
            
    elif file_source == "上传文件":
        uploaded_file = st.sidebar.file_uploader(
            "上传JSONL文件",
            type=['jsonl'],
            help="选择要标注的JSONL格式数据文件"
        )
        if uploaded_file is not None:
            # 保存上传的文件到临时位置
            temp_file = OUTPUT_DIR / f"temp_{uploaded_file.name}"
            with open(temp_file, "wb") as f:
                f.write(uploaded_file.getbuffer())
            input_file = str(temp_file)
            st.sidebar.success(f"✅ 文件已上传: {uploaded_file.name}")
            
    else:  # 输入文件路径
        input_file = st.sidebar.text_input(
            "输入文件路径",
            value="",
            placeholder="/path/to/your/data.jsonl",
            help="输入JSONL文件的完整路径"
        )
    
    # 图片目录路径
    if file_source == "仓库数据文件":
        image_base_dir = str(BASE_DIR / "data" / "images")
        st.sidebar.write(f"**图片目录**: `data/images/`")
    else:
        image_base_dir = st.sidebar.text_input(
            "图片基础目录",
            value="",
            placeholder="/path/to/images/",
            help="图片文件的基础目录路径"
        )
    
    # 标注者信息
    annotator_name = st.sidebar.selectbox(
        "选择标注者",
        ["lpr", "zsh", "zxh"]
    )
    
    # 输出文件路径
    output_file = OUTPUT_DIR / f"annotated_by_{annotator_name}.jsonl"
    st.sidebar.write(f"**输出文件**: `{output_file.name}`")
    
    # 加载数据
    if st.sidebar.button("🔄 加载数据"):
        if input_file and os.path.exists(input_file):
            st.session_state.data = load_jsonl_file(input_file)
            st.session_state.current_index = 0
            st.session_state.annotations = {}
            # 加载已有的标注结果
            st.session_state.existing_annotations = load_existing_annotations(output_file)
            st.success(f"成功加载 {len(st.session_state.data)} 条数据")
            if st.session_state.existing_annotations:
                st.info(f"发现 {len(st.session_state.existing_annotations)} 条已有标注")
        elif input_file:
            st.error(f"文件不存在: {input_file}")
        else:
            st.error("请选择或输入有效的文件路径")
    
    # 检查是否有数据
    if 'data' not in st.session_state or not st.session_state.data:
        st.info("请先加载数据文件")
        
        # 显示使用说明
        st.markdown("""
        ## 📖 使用说明
        
        ### 1. 数据准备
        - **仓库数据文件**: 使用仓库中预置的数据文件（推荐）
        - **上传文件**: 直接上传你的JSONL格式数据文件
        - **文件路径**: 输入服务器上的文件完整路径
        
        ### 2. 标注流程
        1. 选择标注者身份 (lpr/zsh/zxh)
        2. 选择对应的数据文件：
           - lpr → test_set_unmatched_part1.jsonl
           - zsh → test_set_unmatched_part2.jsonl  
           - zxh → test_set_unmatched_part3.jsonl
        3. 点击"🔄 加载数据"
        4. 查看图片和HTML内容
        5. 点击质量评分按钮 (P0/P1/P2)
        6. 自动保存并跳转到下一条
        
        ### 3. 数据格式
        输入的JSONL文件每行应包含以下字段：
        ```json
        {
            "url_id": "唯一标识符",
            "ori_pic": "图片路径 (如: pic/xxx.png)",
            "ori_html": "原始HTML内容",
            "predicted_quality_score": "模型预测评分",
            "processed_html": "处理后的文本内容"
        }
        ```
        
        ### 4. 质量评分标准
        - **P0 (质量很好)**: 内容丰富，信息完整，格式良好
        - **P1 (质量一般)**: 内容基本完整，有一定信息价值  
        - **P2 (质量差，信息量少)**: 内容缺失严重，信息价值低
        
        ### 5. 工作分配
        - **lpr**: 负责标注 part1 数据
        - **zsh**: 负责标注 part2 数据  
        - **zxh**: 负责标注 part3 数据
        """)
        return
    
    data = st.session_state.data
    current_index = st.session_state.get('current_index', 0)
    
    # 进度显示
    progress = (current_index + 1) / len(data)
    st.progress(progress)
    st.write(f"进度: {current_index + 1} / {len(data)} ({progress:.1%})")
    
    # 导航按钮
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    
    with col1:
        if st.button("⬅️ 上一条") and current_index > 0:
            st.session_state.current_index -= 1
            st.rerun()
    
    with col2:
        if st.button("➡️ 下一条") and current_index < len(data) - 1:
            st.session_state.current_index += 1
            st.rerun()
    
    with col3:
        jump_to = st.number_input("跳转到", min_value=1, max_value=len(data), value=current_index + 1)
        if st.button("🎯 跳转"):
            st.session_state.current_index = jump_to - 1
            st.rerun()
    
    with col4:
        # 下载标注结果
        if st.session_state.get('existing_annotations'):
            annotations_json = []
            for data_item in st.session_state.existing_annotations.values():
                annotations_json.append(data_item)
            
            if annotations_json:
                json_str = '\n'.join([json.dumps(item, ensure_ascii=False) for item in annotations_json])
                st.download_button(
                    label="📥 下载标注",
                    data=json_str,
                    file_name=f"annotated_by_{annotator_name}.jsonl",
                    mime="application/json"
                )
    
    with col5:
        existing_count = len(st.session_state.get('existing_annotations', {}))
        st.write(f"已标注: {existing_count}")
    
    # 当前数据
    current_data = data[current_index]
    
    # 获取当前标注相关数据
    current_url_id = current_data.get('url_id')
    existing_annotations = st.session_state.get('existing_annotations', {})
    
    # 显示当前条目信息
    st.header(f"📄 条目 #{current_index + 1}")
    
    # 🏷️ 质量评分按钮选择 - 放在最上面
    st.subheader("🏷️ 质量评分选择")
    
    # 创建三列布局放置按钮
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    
    # 检查当前是否已标注
    is_annotated = current_url_id in existing_annotations
    current_annotation_value = ""
    if is_annotated:
        current_annotation_value = existing_annotations[current_url_id].get('human_predicted_quality_score', '')
    
    # 按钮样式函数
    def get_button_style(option, current_value):
        if option == current_value:
            return "✅ " + option
        else:
            return option
    
    selected_quality = None
    
    with btn_col1:
        p0_label = get_button_style("P0(质量很好)", current_annotation_value)
        if st.button(p0_label, key="btn_p0", use_container_width=True):
            selected_quality = "P0(质量很好)"
    
    with btn_col2:
        p1_label = get_button_style("P1(质量一般)", current_annotation_value)
        if st.button(p1_label, key="btn_p1", use_container_width=True):
            selected_quality = "P1(质量一般)"
    
    with btn_col3:
        p2_label = get_button_style("P2(质量差，信息量少)", current_annotation_value)
        if st.button(p2_label, key="btn_p2", use_container_width=True):
            selected_quality = "P2(质量差，信息量少)"
    
    # 显示当前标注状态
    if is_annotated:
        st.info(f"✅ 当前标注: {current_annotation_value}")
    else:
        st.warning("⏳ 等待标注...")
    
    st.divider()  # 添加分隔线
    
    # 创建两列布局
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("🖼️ 图片预览")
        image_path = current_data.get('ori_pic', '')
        if image_path and image_base_dir:
            display_image(image_path, image_base_dir)
        else:
            st.text("📷 请设置图片基础目录")
        
        st.subheader("🤖 模型预测")
        st.write(f"**预测质量评分**: {current_data.get('predicted_quality_score', 'N/A')}")
        st.write(f"**置信度**: {current_data.get('confidence_quality', 'N/A')}")
        
        if 'explanation_quality' in current_data:
            st.write("**质量解释**:")
            st.write(current_data['explanation_quality'])
    
    with col_right:
        st.subheader("📝 HTML内容")
        
        # HTML原始内容（折叠显示）
        with st.expander("查看原始HTML"):
            st.code(current_data.get('ori_html', ''), language='html')
        
        # 处理后的HTML内容
        if 'processed_html' in current_data:
            st.write("**处理后的文本内容**:")
            st.text_area(
                "内容预览",
                current_data['processed_html'],
                height=200,
                disabled=True
            )
        
        # 显示其他字段
        st.write("**其他信息**:")
        for key, value in current_data.items():
            if key not in ['ori_html', 'processed_html', 'ori_pic']:
                if isinstance(value, str) and len(value) > 100:
                    with st.expander(f"查看 {key}"):
                        st.write(value)
                else:
                    st.write(f"**{key}**: {value}")
    
    st.divider()  # 添加分隔线
    
    # 备注区域
    st.subheader("📝 标注备注")
    existing_note = ""
    if current_url_id in existing_annotations:
        existing_note = existing_annotations[current_url_id].get('annotation_note', '')
    
    note = st.text_area(
        "标注备注（可选）",
        value=existing_note,
        key=f"note_{current_index}",
        height=100,
        placeholder="可以在这里记录标注理由、特殊情况等..."
    )
    
    # 处理按钮点击事件
    if selected_quality:
        # 准备保存的数据 (排除ori_html字段)
        annotated_data = current_data.copy()
        if 'ori_html' in annotated_data:
            del annotated_data['ori_html']  # 移除ori_html字段
        
        annotated_data['human_predicted_quality_score'] = selected_quality
        annotated_data['annotator'] = annotator_name
        if note:
            annotated_data['annotation_note'] = note
        
        # 更新已有标注记录
        if 'existing_annotations' not in st.session_state:
            st.session_state.existing_annotations = {}
        st.session_state.existing_annotations[current_url_id] = annotated_data
        
        # 保存到文件
        if save_annotations_to_file(st.session_state.existing_annotations, output_file):
            st.success(f"✅ 已保存标注: {selected_quality}")
            
            # 自动跳转到下一条
            if current_index < len(data) - 1:
                st.session_state.current_index += 1
                st.success("⏭️ 自动跳转到下一条")
                st.rerun()
            else:
                st.success("🎉 所有数据已标注完成!")
                st.balloons()  # 显示庆祝动画
        else:
            st.error("❌ 保存失败")
    
    # 如果有备注变化但没有重新选择评分，单独保存备注
    elif note != existing_note and is_annotated:
        annotated_data = existing_annotations[current_url_id].copy()
        annotated_data['annotation_note'] = note
        st.session_state.existing_annotations[current_url_id] = annotated_data
        
        if save_annotations_to_file(st.session_state.existing_annotations, output_file):
            st.success("✅ 备注已更新")
        else:
            st.error("❌ 备注更新失败")
    
    # 侧边栏统计信息
    st.sidebar.header("📊 标注统计")
    existing_annotations = st.session_state.get('existing_annotations', {})
    if existing_annotations:
        quality_counts = {}
        for data_item in existing_annotations.values():
            quality = data_item.get('human_predicted_quality_score', '')
            if quality:
                quality_counts[quality] = quality_counts.get(quality, 0) + 1
        
        st.sidebar.write(f"**总标注数**: {len(existing_annotations)}")
        for quality, count in quality_counts.items():
            st.sidebar.write(f"- {quality}: {count}")
            
        # 显示进度百分比
        if len(data) > 0:
            completion_rate = len(existing_annotations) / len(data) * 100
            st.sidebar.write(f"**完成度**: {completion_rate:.1f}%")
            
            # 进度条
            st.sidebar.progress(completion_rate / 100)
    else:
        st.sidebar.write("暂无标注数据")
    
    # 使用说明
    st.sidebar.header("⌨️ 使用说明")
    st.sidebar.write("🔘 点击质量评分按钮即可自动保存并跳转")
    st.sidebar.write("- ⬅️ 上一条: 手动导航")
    st.sidebar.write("- ➡️ 下一条: 手动导航或自动跳转")
    st.sidebar.write("- 🎯 跳转: 快速定位到指定条目")
    st.sidebar.write("- 📥 下载: 下载当前标注结果")

if __name__ == "__main__":
    main()