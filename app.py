import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import openai
import base64
import io
import json
import re
from docx import Document

# --- 页面全局配置 ---
st.set_page_config(page_title="Academic Studio Ultra Pro Max", layout="wide", initial_sidebar_state="expanded")

# --- 侧边栏：核心配置 ---
with st.sidebar:
    st.title("⚙️ 顶级科研引擎配置")
    engine_choice = st.selectbox("核心引擎", [
        "Google Gemini 1.5 Pro (全能推荐)",
        "智谱 GLM-4v (国内推荐)",
        "OpenAI GPT-4o",
        "DeepSeek V3",
        "Kimi (Moonshot)"
    ])
    api_key = st.text_input("输入 API Key", type="password")
    
    st.divider()
    st.subheader("📊 期刊 LetPub 过滤指标")
    if_range = st.slider("影响因子范围", 0.0, 50.0, (5.0, 7.0))
    cas_zone_sel = st.multiselect("中科院分区", ["1区", "2区", "3区", "4区"], default=["2区"])
    sci_zone_sel = st.multiselect("SCI 分区 (Q)", ["Q1", "Q2", "Q3", "Q4"], default=["Q1"])
    is_oa = st.checkbox("仅显示 Open Access")

    st.divider()
    st.subheader("🖼️ Illustrator 画布与导出")
    dpi_val = st.selectbox("导出精度 (DPI)", [300, 600, 1200], index=0)
    export_fmt = st.selectbox("文件格式", ["PNG", "PDF", "TIFF"])

# --- AI 通讯逻辑 (深度修复 Gemini 404 与解析逻辑) ---
def get_ai_response(messages):
    if not api_key: return "ERROR: API Key 缺失，请在左侧输入。"
    
    # 修复：Gemini 的 OpenAI 兼容 Base URL 必须极其精准
    urls = {
        "Google Gemini 1.5 Pro (全能推荐)": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "智谱 GLM-4v (国内推荐)": "https://open.bigmodel.cn/api/paas/v4/",
        "OpenAI GPT-4o": "https://api.openai.com/v1",
        "DeepSeek V3": "https://api.deepseek.com",
        "Kimi (Moonshot)": "https://api.moonshot.cn/v1"
    }
    # 修复：Gemini 模型 ID 移除 models/ 前缀，避免 404
    models = {
        "Google Gemini 1.5 Pro (全能推荐)": "gemini-1.5-pro",
        "智谱 GLM-4v (国内推荐)": "glm-4v",
        "OpenAI GPT-4o": "gpt-4o",
        "DeepSeek V3": "deepseek-chat",
        "Kimi (Moonshot)": "moonshot-v1-8k"
    }
    
    try:
        client = openai.OpenAI(api_key=api_key, base_url=urls[engine_choice])
        response = client.chat.completions.create(
            model=models[engine_choice],
            messages=messages,
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: 调用失败。原因: {str(e)}"

# --- UI 导航 ---
st.title("🎓 顶级科研全流程工作站 Pro Max")
tabs = st.tabs(["🔍 SCI 结果深度解析", "🎨 Pro 画布 (Illustrator)", "✍️ 交互润色/降AI", "📊 期刊智选 (LetPub)", "🚀 创新方案实验室"])

# --- 模块 1: SCI 结果深度解析 ---
with tabs[0]:
    st.header("Manuscript & Figure Visual Interpretation")
    c1, c2 = st.columns(2)
    with c1:
        ms_in = st.file_uploader("上传手稿文本", type=["docx", "pdf", "txt"])
        fg_in = st.file_uploader("上传高精结果图/表格", accept_multiple_files=True)
    with c2:
        out_lang = st.radio("输出语言", ["中文 (Chinese)", "英文 (English)"], horizontal=True)
        if st.button("开始深度解析"):
            with st.spinner("AI 正在交叉比对数据与逻辑..."):
                prompt = [{"role":"user","content":f"请作为顶刊审稿人。结合上传的文字和图表，生成详尽的SCI Results描述。必须输出三个版本：1. 带有统计指标（OR, CI, P值）的详版描述 2. 对图表中每一个趋势的专业解释 3. 仿Nature的精简结论。请用{out_lang}输出。"}]
                st.markdown(get_ai_response(prompt))

# --- 模块 2: Pro 画布 (Adobe Illustrator 级交互) ---
with tabs[1]:
    st.header("Vector Figure Illustrator")
    st.caption("核心交互：插入多 PDF/图片，选中标注后‘✨’键同步全图同属性对象。")
    
    editor_html = f"""
    <div style="display:flex; gap:10px; background:#1e1e1e; padding:15px; border-radius:10px; color:white;">
        <div id="canv-main">
            <div id="toolbar" style="margin-bottom:12px; display:flex; gap:8px;">
                <input type="file" id="pdfAdd" multiple style="display:none">
                <button onclick="document.getElementById('pdfAdd').click()" style="background:#444; color:white; border:none; padding:8px 12px; cursor:pointer;">📁 插入 PDF/图片</button>
                <button onclick="addText()" style="background:#444; color:white; border:none; padding:8px 12px; cursor:pointer;">T 文本标注</button>
                <button onclick="batchModify()" style="background:#f39c12; color:white; border:none; padding:8px 12px; cursor:pointer; font-weight:bold;">✨ 查找相同修改</button>
                <button onclick="exportPro()" style="background:#28a745; color:white; border:none; padding:8px 12px; cursor:pointer;">🚀 导出 {export_fmt} ({dpi_val}DPI)</button>
            </div>
            <canvas id="c" width="880" height="600" style="border:1px solid #000; background:white;"></canvas>
        </div>
        <div id="prop-panel" style="width:240px; background:#2d2d2d; padding:20px; border-radius:8px; font-size:12px;">
            <h4 style="margin-top:0">属性 (Properties)</h4>
            字体: <select id="fFam" style="width:100%"><option>Times New Roman</option><option>Arial</option></select><br><br>
            字号: <input type="number" id="fSiz" value="28" style="width:100%"><br><br>
            颜色: <input type="color" id="fCol" style="width:100%"><br><br>
            <hr>
            <p style="color:#aaa">提示：点击选中标注，点‘✨’按钮同步修改全图。PDF 插入可能需 1-2 秒渲染，请耐心等待。</p>
        </div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js"></script>
    <script>
        const canvas = new fabric.Canvas('c');
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';

        function batchModify() {{
            const ref = canvas.getActiveObject();
            if(!ref) return alert("请先选中一个样板！");
            const nCol = document.getElementById('fCol').value;
            const nSiz = parseInt(document.getElementById('fSiz').value);
            canvas.getObjects().forEach(obj => {{
                if(obj.type === ref.type && (obj.fill === ref.fill || obj.fontSize === ref.fontSize)) {{
                    obj.set({{ fill: nCol, fontSize: nSiz, fontFamily: document.getElementById('fFam').value }});
                }}
            }});
            canvas.renderAll();
        }}

        document.getElementById('pdfAdd').onchange = function(e) {{
            const files = e.target.files;
            for(let file of files) {{
                const reader = new FileReader();
                if(file.type === "application/pdf") {{
                    reader.onload = function() {{
                        const uint8 = new Uint8Array(this.result);
                        pdfjsLib.getDocument(uint8).promise.then(pdf => {{
                            pdf.getPage(1).then(page => {{
                                const viewport = page.getViewport({{scale: 1.5}});
                                const tempC = document.createElement('canvas');
                                tempC.height = viewport.height; tempC.width = viewport.width;
                                page.render({{canvasContext: tempC.getContext('2d'), viewport: viewport}}).promise.then(() => {{
                                    fabric.Image.fromURL(tempC.toDataURL(), img => {{ img.scale(0.5); canvas.add(img); }});
                                }});
                            }});
                        }});
                    }};
                    reader.readAsArrayBuffer(file);
                }} else {{
                    reader.onload = f => fabric.Image.fromURL(f.target.result, img => {{ img.scale(0.2); canvas.add(img); }});
                    reader.readAsDataURL(file);
                }}
            }}
        }};

        function addText() {{ canvas.add(new fabric.IText('Fig Label', {{ left: 150, top: 150, fontFamily: 'Times New Roman', fontSize: 24 }})); }}
        function exportPro() {{
            const mul = {dpi_val} / 96;
            const dataURL = canvas.toDataURL({{ format: 'png', multiplier: mul }});
            const link = document.createElement('a');
            link.download = "Figure_Export_HighRes.png"; link.href = dataURL; link.click();
        }}
    </script>
    """
    components.html(editor_html, height=780)

# --- 模块 3: 交互式润色 (Paperpal 级) ---
with tabs[2]:
    st.header("Interactive Academic Polisher & Humanizer")
    if 'rev_data' not in st.session_state: st.session_state.rev_data = []

    text_input = st.text_area("输入原始文本", height=200)
    mode = st.radio("润色偏好", ["专业润色", "降 AI 重构"], horizontal=True)

    if st.button("逐句解析润色"):
        with st.spinner("AI 正在重组学术逻辑..."):
            prompt = f"""Act as a senior editor. Break the text into sentences. 
            For each, provide 3 versions: 1. Original 2. Academic (Formal) 3. Humanized (De-AI).
            Output ONLY a JSON list: [{{"orig":"...","acad":"...","human":"..."}}]
            Text: {text_input}"""
            res = get_ai_response([{"role":"user","content":prompt}])
            try:
                json_str = re.search(r'\[.*\]', res, re.DOTALL).group()
                st.session_state.rev_data = json.loads(json_str)
            except: st.error("解析失败。请确保输入的是完整的学术文本。")

    if st.session_state.rev_data:
        final_list = []
        for i, item in enumerate(st.session_state.rev_data):
            with st.expander(f"句子 {i+1}: {item['orig'][:60]}..."):
                c = st.radio(f"选择版本 {i}", [item['orig'], item['acad'], item['human']], key=f"r_{i}")
                final_list.append(c)
        st.divider()
        st.text_area("最终合并文本 (可直接复制)", " ".join(final_list), height=200)

# --- 模块 4: 期刊智选 (LetPub 强制检索) ---
with tabs[3]:
    st.header("LetPub Strategic Journal Matcher")
    st.info(f"过滤条件：IF ({if_range[0]}-{if_range[1]}) | 中科院 {cas_zone_sel} | SCI {sci_zone_sel}")
    abs_in = st.text_area("输入论文题目与摘要", height=150)
    
    if st.button("开始强制检索期刊库"):
        with st.spinner("检索 2024-2025 JCR 数据库中..."):
            prompt = f"""
            TASK: ACT AS LetPub Senior Consultant.
            MANDATORY: Suggest 10 REAL journals for Abstract: {abs_in}
            Criteria: IF {if_range[0]} to {if_range[1]}, CAS {cas_zone_sel}, SCI {sci_zone_sel}.
            Each journal must include: 1. Name 2. IF 3. Zones 4. REAL similar articles titles published in this journal (PMID style).
            DO NOT apologize or say you cannot find any. OUTPUT AS MARKDOWN TABLE.
            """
            st.markdown(get_ai_response([{"role":"user","content":prompt}]))

# --- 模块 5: 创新实验室 (含未来指标开发) ---
with tabs[4]:
    st.header("🚀 蓝海领域：全数据库创新大脑")
    
    step = st.radio("选择流程阶段", ["1. 蓝海思路探索", "2. 详细路径 (代码与未来指标)", "3. SCI 背景报告生成"], horizontal=True)
    
    if step == "1. 蓝海思路探索":
        db_type = st.text_input("数据库名称 (如: NHANES, UKB, GBD)")
        field = st.text_input("研究大方向 (如: 口腔虚弱与肌少症)")
        if st.button("挖掘高分创新思路"):
            prompt = f"""针对数据库 {db_type}，探究领域 {field} 尚未发表的蓝海思路。
            要求：1. 结合 2025 最新科研趋势（如因果中介、多组学、时空模型）。
            2. 提供 3 个具体的可落地思路并解释为什么这是未来的高分方向。"""
            st.markdown(get_ai_response([{"role":"user","content":prompt}]))
            
    elif step == "2. 详细路径 (代码与未来指标)":
        c1, c2, c3 = st.columns(3)
        u_exp = c1.text_input("确定暴露 (Exposure)")
        u_db = c2.text_input("拟用数据库")
        u_out = c3.text_input("确定结局 (Outcome)")
        if st.button("生成详细方案与未来指标"):
            prompt = f"""针对数据库 {u_db} 研究暴露 {u_exp} 与结局 {u_out}。
            要求：1. 给出 Variable Codes (如 NHANES 的特定变量)。
            2. **重点**：开发 3 个‘未来可以研究的指标’（未来指标定义为：利用现有变量通过特定算法计算出的派生变量，如生物学年龄、特定指数、累积负荷评分等），并给出具体计算公式。
            3. 统计模型逻辑。
            4. 给出真实 PMID 参考文献。"""
            st.markdown(get_ai_response([{"role":"user","content":prompt}]))
            
    elif step == "3. SCI 背景报告生成":
        if st.button("生成 1000字 深度方案书"):
            with st.spinner("报告编写中..."):
                prompt = """生成 1000 字以上 SCI 项目背景方案报告。
                要求：1. 背景详尽对标顶刊。2. 方法论严谨。
                3. 结果部分必须包含 Figure 1 (流程图), Figure 2 (派生未来指标趋势图) 的模拟描述。"""
                res = get_ai_response([{"role":"user","content":prompt}])
                st.markdown(res)
                doc = Document()
                doc.add_paragraph(res)
                bio = io.BytesIO()
                doc.save(bio)
                st.download_button("下载 Word 方案书", bio.getvalue(), "Research_Innovation_Report.docx")
