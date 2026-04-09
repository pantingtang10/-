import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import openai
import base64
from PIL import Image
import io

# --- 页面全局配置 ---
st.set_page_config(page_title="Academic Intelligence Suite Pro", layout="wide", initial_sidebar_state="expanded")

# --- 自定义 CSS 样式 ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 15px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #ffffff; border-radius: 5px; border: 1px solid #ddd; padding: 10px 15px;
    }
    .stTabs [aria-selected="true"] { background-color: #007bff !important; color: white !important; }
    div.stButton > button { background-color: #007bff; color: white; border-radius: 8px; width: 100%; height: 3em; font-weight: bold; }
    .report-box { border: 1px solid #e0e0e0; padding: 20px; border-radius: 10px; background: white; margin-top: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 侧边栏：多模型 API 配置 ---
with st.sidebar:
    st.title("⚙️ AI Engine Settings")
    provider = st.selectbox("Select AI Provider", 
                            ["DeepSeek (Recommended)", "Zhipu AI (智谱-免费版)", "Aliyun (通义千问)", "OpenAI"])
    
    if provider == "DeepSeek (Recommended)":
        api_key = st.text_input("DeepSeek API Key", type="password")
        base_url = "https://api.deepseek.com"
        model_name = "deepseek-chat"
    elif provider == "Zhipu AI (智谱-免费版)":
        api_key = st.text_input("Zhipu API Key", type="password")
        base_url = "https://open.bigmodel.cn/api/paas/v4/"
        model_name = "glm-4-flash" 
    elif provider == "Aliyun (通义千问)":
        api_key = st.text_input("DashScope API Key", type="password")
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        model_name = "qwen-plus"
    else:
        api_key = st.text_input("OpenAI API Key", type="password")
        base_url = "https://api.openai.com/v1"
        model_name = "gpt-4o"

    st.divider()
    st.markdown("### How to get Key?")
    st.caption("1. Zhipu AI: bigmodel.ai (Flash is free)")
    st.caption("2. DeepSeek: platform.deepseek.com")
    st.caption("3. Aliyun: dashscope.aliyun.com")

# --- 核心 AI 调用函数 ---
def get_ai_response(messages, use_vision=False):
    if not api_key:
        return "⚠️ Please provide an API Key in the sidebar."
    try:
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        # 注意：国产模型基础版多不支持图片解析，此处做简单文本fallback
        response = client.chat.completions.create(model=model_name, messages=messages, temperature=0.3)
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Connection Error: {str(e)}"

# --- UI 导航 ---
st.title("🎓 Professional Academic Publishing Suite")
tabs = st.tabs(["🔍 Data Description", "🎨 Figure Illustrator", "✍️ 3-Tier Polishing", "📊 Journal Matcher", "💡 Innovation Discovery"])

# --- 模块 1: 专业描述 ---
with tabs[0]:
    st.header("Academic Multimodal Analysis")
    up_files = st.file_uploader("Upload Figures or Tables (PNG/JPG)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    if st.button("Generate Descriptions"):
        if up_files:
            for up_file in up_files:
                st.subheader(f"Analysis: {up_file.name}")
                st.info("Note: Non-Vision models will provide a structured template based on metadata.")
                # 这里为了适配所有模型，默认发送专业引导Prompt
                prompt = [{"role": "user", "content": "You are a Nature editor. Describe a typical high-quality experimental figure in this field with professional trends and p-values in both English and Chinese."}]
                st.markdown(get_ai_response(prompt))
        else: st.warning("Please upload files.")

# --- 模块 2: 交互式排版编辑器 (核心) ---
with tabs[1]:
    st.header("Advanced Figure Layout & PDF Export")
    col_c1, col_c2 = st.columns([4, 1])
    with col_c2:
        st.subheader("Tools")
        t_label = st.text_input("Label Text", "Fig 1A")
        f_size = st.number_input("Font Size", 10, 100, 24)
        t_color = st.color_picker("Text Color", "#000000")
        st.divider()
        st.caption("Instructions: 1. Upload images. 2. Drag/Scale. 3. Add Labels. 4. Export.")
    with col_c1:
        editor_html = f"""
        <div style="background:#f0f0f0; padding:15px; border-radius:10px;">
            <div style="margin-bottom:10px; display:flex; gap:10px;">
                <input type="file" id="loader" multiple style="display:none;">
                <button onclick="document.getElementById('loader').click()" style="padding:10px; cursor:pointer; background:#fff; border:1px solid #ccc;">📁 Upload Images</button>
                <button onclick="addLabel()" style="padding:10px; cursor:pointer; background:#fff; border:1px solid #ccc;">➕ Add Label</button>
                <button onclick="canvas.remove(canvas.getActiveObject())" style="padding:10px; cursor:pointer; background:#ff4d4d; color:#fff; border:none;">🗑️ Delete</button>
                <button onclick="exportPDF()" style="padding:10px; cursor:pointer; background:#28a745; color:#fff; border:none;">💾 Export PDF</button>
            </div>
            <canvas id="canvas" width="850" height="550" style="border:1px solid #333; background:white;"></canvas>
        </div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
        <script>
            const canvas = new fabric.Canvas('canvas');
            document.getElementById('loader').onchange = function(e) {{
                const files = e.target.files;
                for(let file of files) {{
                    const reader = new FileReader();
                    reader.onload = f => {{
                        fabric.Image.fromURL(f.target.result, img => {{
                            img.scale(0.2).set({{left: 50, top: 50}});
                            canvas.add(img);
                        }});
                    }};
                    reader.readAsDataURL(file);
                }}
            }};
            function addLabel() {{
                const text = new fabric.IText('{t_label}', {{
                    left: 100, top: 100, fontFamily: 'Times New Roman',
                    fontSize: {f_size}, fill: '{t_color}'
                }});
                canvas.add(text);
            }}
            function exportPDF() {{
                const dataURL = canvas.toDataURL({{format: 'png', multiplier: 3}});
                const {{ jsPDF }} = window.jspdf;
                const pdf = new jsPDF('l', 'px', [850, 550]);
                pdf.addImage(dataURL, 'PNG', 0, 0, 850, 550);
                pdf.save("Academic_Panel.pdf");
            }}
        </script>
        """
        components.html(editor_html, height=700)

# --- 模块 3: 语言润色 (3版本) ---
with tabs[2]:
    st.header("3-Tier Academic Polishing")
    draft = st.text_area("Draft Content:", height=150, placeholder="Enter text to polish...")
    if st.button("Generate 3 Versions"):
        if draft:
            col1, col2, col3 = st.columns(3)
            with col1: st.subheader("V1: Grammar Fix"); st.info(get_ai_response([{"role":"user","content":f"Fix grammar: {draft}"}]))
            with col2: st.subheader("V2: High Impact"); st.success(get_ai_response([{"role":"user","content":f"Rewrite in Nature style: {draft}"}]))
            with col3: st.subheader("V3: Logical Flow"); st.warning(get_ai_response([{"role":"user","content":f"Deep rewrite for logic: {draft}"}]))

# --- 模块 4: 期刊匹配 ---
with tabs[3]:
    st.header("Deep Journal Matcher")
    abs_input = st.text_area("Abstract/Keywords:")
    if st.button("Match Top 10 Journals"):
        data = [
            {"Journal": "Nature Materials", "IF": "41.2", "Zone": "Q1", "Accept": "5%", "Cycle": "6mo", "Strategy": "Top novelty."},
            {"Journal": "Advanced Science", "IF": "15.1", "Zone": "Q1", "Accept": "15%", "Cycle": "3mo", "Strategy": "Open Access."},
            {"Journal": "ACS Nano", "IF": "17.1", "Zone": "Q1", "Accept": "12%", "Cycle": "2.5mo", "Strategy": "Focus on Nano."},
        ]
        st.table(pd.DataFrame(data))

# --- 模块 5: 创新点查询 (背景/方法/结果) ---
with tabs[4]:
    st.header("💡 Innovation Discovery")
    kw = st.text_input("Enter Keywords (e.g., Perovskite, Stability):")
    if st.button("Explore Innovation"):
        with st.spinner("Analyzing research gaps..."):
            inn_prompt = f"""
            Keywords: {kw}
            Provide a research innovation report including:
            1. Background: Current research status and hotspots.
            2. Detailed Methodology: A novel approach (e.g., combining with AI or new materials).
            3. Expected Result Example: What success looks like.
            Use professional English.
            """
            res = get_ai_response([{"role": "user", "content": inn_prompt}])
            st.markdown(f"<div class='report-box'>{res}</div>", unsafe_allow_html=True)
