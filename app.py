import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import openai
import base64
import json

# --- 页面全局配置 ---
st.set_page_config(page_title="Academic Intelligence Suite Pro Max", layout="wide")

# --- 侧边栏：多模型与导出参数 ---
with st.sidebar:
    st.title("⚙️ 系统配置")
    provider = st.selectbox("AI 引擎", ["OpenAI (GPT-4o)", "Zhipu AI (GLM-4v)"])
    api_key = st.text_input("API 密钥", type="password")
    
    st.divider()
    st.subheader("🖼️ 导出导出设置")
    export_dpi = st.select_slider("自定义 DPI", options=[72, 96, 150, 300, 600, 1200], value=300)
    export_fmt = st.selectbox("导出格式", ["pdf", "png", "tiff"])
    
    base_url = "https://api.openai.com/v1" if provider == "OpenAI (GPT-4o)" else "https://open.bigmodel.cn/api/paas/v4/"
    model_name = "gpt-4o" if provider == "OpenAI (GPT-4o)" else "glm-4v"

# --- 通用 AI 调用函数 ---
def get_ai_response(messages):
    if not api_key: return "⚠️ 请在侧边栏输入 API Key。"
    try:
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(model=model_name, messages=messages, temperature=0.3)
        return response.choices[0].message.content
    except Exception as e: return f"❌ AI 出错: {str(e)}"

# --- UI 导航 ---
st.title("🔬 顶级学术科研全生命周期平台")
tabs = st.tabs(["🔍 稿件/结果描述", "🎨 Pro 画布编辑器", "✍️ 润色与降重", "📊 真实期刊筛选", "💡 交互式创新大脑"])

# --- 模块 1: 手稿与结果描述 ---
with tabs[0]:
    st.header("Manuscript & Figure Interpretation")
    col_l, col_r = st.columns([1, 1])
    with col_l:
        up_file = st.file_uploader("上传手稿或实验图", type=["png", "jpg", "jpeg", "docx", "pdf"])
        out_lang = st.radio("输出语言", ["中文 (Chinese)", "英文 (English)"])
    with col_r:
        if st.button("生成学术描述"):
            with st.spinner("深度解析中..."):
                prompt = f"请作为顶刊审稿人，详细分析此内容。如果包含图片，描述其趋势、统计学意义和结论。请使用{out_lang}输出，确保学术严谨。"
                # 视觉逻辑（简化演示）
                st.info("结果描述将在此处显示，对标 Nature/Science 范式。")

# --- 模块 2: Pro Illustrator (支持 PDF & 批量修改) ---
with tabs[1]:
    st.header("Vector-Grade PDF Illustrator")
    st.caption("支持一键查找相同属性并修改颜色/字号。")
    
    editor_html = f"""
    <div style="display: flex; gap: 10px; background: #2c2c2c; padding: 15px; color: white; border-radius: 8px;">
        <div id="canvas-area">
            <div id="toolbar" style="margin-bottom:10px; display: flex; gap: 8px;">
                <input type="file" id="pdfInp" accept="application/pdf" multiple style="display:none">
                <button onclick="document.getElementById('pdfInp').click()">📁 插入 PDF(s)</button>
                <button onclick="addText()">T 添加文本</button>
                <button onclick="findSimilarChange()" style="background:#f39c12">✨ 查找并批量修改</button>
                <button onclick="canvas.remove(canvas.getActiveObject())" style="background:#d9534f">🗑️ 删除选中</button>
                <button onclick="processExport()" style="background:#28a745; font-weight:bold;">🚀 导出 ({export_fmt.upper()})</button>
            </div>
            <canvas id="c" width="900" height="600" style="border:1px solid #000; background:white;"></canvas>
        </div>
        <div id="side-panel" style="width: 240px; background: #383838; padding: 15px; font-size:12px;">
            <h4>属性面板</h4>
            <label>字体:</label><select id="fFamily" style="width:100%"><option>Arial</option><option>Times New Roman</option></select><br><br>
            <label>字号:</label><input type="number" id="fSize" value="24" oninput="updateObj()"><br><br>
            <label>颜色:</label><input type="color" id="fColor" onchange="updateObj()"><br><br>
            <label>不透明度:</label><input type="range" id="fAlpha" min="0" max="1" step="0.1" oninput="updateObj()">
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>

    <script>
        const canvas = new fabric.Canvas('c');
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';

        // 批量修改核心逻辑
        function findSimilarChange() {{
            const active = canvas.getActiveObject();
            if(!active) return alert("请先选中一个作为参考样板");
            const targetColor = active.fill;
            const targetType = active.type;
            const newSize = parseInt(document.getElementById('fSize').value);
            const newColor = document.getElementById('fColor').value;

            canvas.getObjects().forEach(obj => {{
                if(obj.type === targetType && obj.fill === targetColor) {{
                    obj.set({{ fill: newColor, fontSize: newSize }});
                }}
            }});
            canvas.renderAll();
        }}

        document.getElementById('pdfInp').onchange = function(e) {{
            const files = e.target.files;
            for(let file of files) {{
                const reader = new FileReader();
                reader.onload = function() {{
                    const typedarray = new Uint8Array(this.result);
                    pdfjsLib.getDocument(typedarray).promise.then(pdf => {{
                        pdf.getPage(1).then(page => {{
                            const viewport = page.getViewport({{scale: 1.5}});
                            const canvasTemp = document.createElement('canvas');
                            const context = canvasTemp.getContext('2d');
                            canvasTemp.height = viewport.height;
                            canvasTemp.width = viewport.width;
                            page.render({{canvasContext: context, viewport: viewport}}).promise.then(() => {{
                                fabric.Image.fromURL(canvasTemp.toDataURL(), img => {{
                                    img.set({{left: 50, top: 50}});
                                    canvas.add(img);
                                }});
                            }});
                        }});
                    }});
                }};
                reader.readAsArrayBuffer(file);
            }}
        }};

        function addText() {{
            const t = new fabric.IText('Double Click to Edit', {{ left: 100, top: 100, fontFamily: 'Arial', fontSize: 24 }});
            canvas.add(t);
        }}

        function updateObj() {{
            const obj = canvas.getActiveObject();
            if(!obj) return;
            obj.set({{ 
                fontSize: parseInt(document.getElementById('fSize').value), 
                fill: document.getElementById('fColor').value,
                opacity: parseFloat(document.getElementById('fAlpha').value)
            }});
            canvas.renderAll();
        }}

        function processExport() {{
            const multiplier = {export_dpi} / 96;
            const fmt = '{export_fmt}';
            const dataURL = canvas.toDataURL({{ format: 'png', multiplier: multiplier }});
            if(fmt === 'pdf') {{
                const {{ jsPDF }} = window.jspdf;
                const pdf = new jsPDF('l', 'px', [canvas.width * multiplier, canvas.height * multiplier]);
                pdf.addImage(dataURL, 'PNG', 0, 0, canvas.width * multiplier, canvas.height * multiplier);
                pdf.save("Publication_Figure.pdf");
            }} else {{
                const link = document.createElement('a');
                link.download = `Figure.${{fmt}}`;
                link.href = dataURL;
                link.click();
            }}
        }}
    </script>
    """
    components.html(editor_html, height=750)

# --- 模块 3: 润色与降重 (专业学术) ---
with tabs[2]:
    st.header("Academic Polishing & AI-Humanizer")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        raw_text = st.text_area("输入原始文本", height=250)
    with col_t2:
        mode = st.selectbox("功能选择", ["深度润色 (Academic Polishing)", "去AI痕迹/降重 (Reduce AI Rate)"])
        if st.button("开始处理"):
            with st.spinner("执行专业降重逻辑..."):
                prompt = f"请作为顶刊编辑，对以下内容执行 {mode}。要求：1. 提升学术深度。2. 改变句式结构以绕过AI检测。3. 使用精准的领域术语。"
                st.markdown(get_ai_response([{"role": "user", "content": prompt + raw_text}]))

# --- 模块 4: 真实期刊筛选 (Database-Specific) ---
with tabs[3]:
    st.header("Strategic Journal Matcher (Real Data)")
    target_db = st.selectbox("研究涉及的数据库", ["FAERS", "NHANES", "UK Biobank", "CHARLS", "GBD", "MIMIC"])
    abs_input = st.text_area("输入手稿摘要", height=150)
    
    if st.button("查找真实发表匹配"):
        with st.spinner("正在检索真实影响因子与发表记录..."):
            prompt = f"基于摘要和数据库 {target_db}，推荐5个真实期刊。要求：影响因子真实，列出近期该期刊发表过的使用 {target_db} 数据库的相关文章题目。按Elsevier Journal Finder逻辑匹配。"
            st.markdown(get_ai_response([{"role": "user", "content": prompt + abs_input}]))

# --- 模块 5: 交互式创新大脑 ---
with tabs[4]:
    st.header("🚀 交互式科研方案生成器")
    st.caption("对标专业方案报告，生成包含暴露、结局及具体实施步骤的方案。")
    
    with st.expander("🛠️ 配置研究参数", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        exp = c1.text_input("想做的暴露 (Exposure)", placeholder="如：奥沙利铂")
        out = c2.text_input("想做的结局 (Outcome)", placeholder="如：周围神经病变")
        dis = c3.text_input("针对的疾病 (Disease)", placeholder="如：结直肠癌")
        db = c4.selectbox("使用数据库", ["FAERS", "NHANES", "CHARLS", "GBD", "MIMIC"])
        lang_sel = st.radio("生成语言", ["中文", "英文"], horizontal=True)

    if st.button("生成具体实施方案"):
        with st.spinner("正在构建深度方案报告..."):
            # 这里的 Prompt 模仿您提供的 FAERS 报告逻辑
            prompt = f"""
            请根据以下参数生成一份高质量科研方案：
            数据库：{db}
            研究方向：探索 {exp} 对 {dis} 患者 {out} 的影响。
            要求包含：
            1. 研究标题与背景（对标顶刊思路）。
            2. 具体实施方案：提供具体的变量编码（如果是NHANES请给出Variable Code，如果是FAERS请说明信号检测算法）。
            3. 暴露、结局、协变量的提取方法。
            4. 统计模型：建议具体的模型（如逻辑回归、SHAP机器学习、RCS等）。
            5. 模拟例图说明：描述 Table 1 和 Figure 1 应展示的内容及图注。
            6. 真实参考文献：列出3-5条与此方向和数据库真实相关的文献。
            请使用 {lang_sel} 输出。
            """
            st.markdown(get_ai_response([{"role": "user", "content": prompt}]))
