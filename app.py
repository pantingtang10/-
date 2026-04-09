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
st.set_page_config(page_title="Academic Intelligence Studio Ultra Pro", layout="wide", initial_sidebar_state="expanded")

# --- 侧边栏：核心引擎配置 ---
with st.sidebar:
    st.title("⚙️ 顶级科研引擎中心")
    engine_choice = st.selectbox("选择核心引擎", [
        "Google Gemini 1.5 Pro (推荐)",
        "智谱 GLM-4v (国内直连)",
        "OpenAI GPT-4o",
        "DeepSeek V3",
        "Kimi (Moonshot)"
    ])
    api_key = st.text_input("输入 API Key", type="password")
    
    st.divider()
    st.subheader("📊 LetPub 期刊过滤指标")
    if_range = st.slider("影响因子范围", 0.0, 50.0, (5.0, 7.0))
    cas_zone_sel = st.multiselect("中科院分区", ["1区", "2区", "3区", "4区"], default=["2区"])
    sci_zone_sel = st.multiselect("SCI 分区 (Q)", ["Q1", "Q2", "Q3", "Q4"], default=["Q1"])
    oa_req = st.checkbox("仅显示 Open Access")

    st.divider()
    st.subheader("🖼️ 画布与导出")
    dpi_val = st.selectbox("导出精度 (DPI)", [300, 600, 1200], index=0)
    export_fmt = st.selectbox("文件格式", ["PDF", "PNG", "TIFF"])

# --- AI 通讯逻辑 (解决 AI 拒绝回答与解析问题) ---
def get_ai_response(messages):
    if not api_key: return "ERROR: 请在左侧输入 API Key。"
    
    urls = {
        "Google Gemini 1.5 Pro (推荐)": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "智谱 GLM-4v (国内直连)": "https://open.bigmodel.cn/api/paas/v4/",
        "OpenAI GPT-4o": "https://api.openai.com/v1",
        "DeepSeek V3": "https://api.deepseek.com",
        "Kimi (Moonshot)": "https://api.moonshot.cn/v1"
    }
    models = {
        "Google Gemini 1.5 Pro (推荐)": "gemini-1.5-pro",
        "智谱 GLM-4v (国内直连)": "glm-4v",
        "OpenAI GPT-4o": "gpt-4o",
        "DeepSeek V3": "deepseek-chat",
        "Kimi (Moonshot)": "moonshot-v1-8k"
    }
    
    try:
        client = openai.OpenAI(api_key=api_key, base_url=urls[engine_choice])
        response = client.chat.completions.create(
            model=models[engine_choice],
            messages=messages,
            temperature=0.2 # 降低随机性，确保期刊数据准确
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: 调用失败。错误详情: {str(e)}"

# --- UI 导航 ---
st.title("🎓 顶级科研全流程工作站 Pro Max")
tabs = st.tabs(["🔍 SCI 结果描述", "🎨 Pro 画布 (Illustrator)", "✍️ 交互润色/降AI", "📊 期刊智选 (LetPub)", "🚀 创新方案实验室"])

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
            prompt = [{"role":"user","content":f"请作为顶刊审稿人。结合上传的文字和图表，生成详尽的SCI Results描述。必须包含两个版本：1. 带有P值和具体统计趋势的详版 2. 仿Nature精简版。同时给出对应的Figure Legend。请用{out_lang}输出。"}]
            st.markdown(get_ai_response(prompt))

# --- 模块 2: Pro 画布 (对标 Adobe Illustrator) ---
with tabs[1]:
    st.header("Vector Figure Illustrator")
    st.caption("支持多 PDF 混合排版，一键查找相同属性并同步。")
    
    editor_html = f"""
    <div style="display:flex; gap:10px; background:#1e1e1e; padding:15px; border-radius:10px; color:white;">
        <div id="canv-main">
            <div id="toolbar" style="margin-bottom:12px; display:flex; gap:8px;">
                <input type="file" id="pdfAdd" multiple style="display:none">
                <button onclick="document.getElementById('pdfAdd').click()" style="background:#444; color:white; border:none; padding:8px 12px; cursor:pointer;">📁 插入 PDF/图片</button>
                <button onclick="addText()" style="background:#444; color:white; border:none; padding:8px 12px; cursor:pointer;">T 文本</button>
                <button onclick="batchModify()" style="background:#f39c12; color:white; border:none; padding:8px 12px; cursor:pointer; font-weight:bold;">✨ 查找相同修改</button>
                <button onclick="exportPro()" style="background:#28a745; color:white; border:none; padding:8px 12px; cursor:pointer;">🚀 导出 {export_fmt} ({dpi_val}DPI)</button>
            </div>
            <canvas id="c" width="880" height="600" style="border:1px solid #000; background:white;"></canvas>
        </div>
        <div id="prop-panel" style="width:240px; background:#2d2d2d; padding:20px; border-radius:8px; font-size:12px;">
            <h4 style="margin-top:0">属性面板 (Properties)</h4>
            字体: <select id="fFam" style="width:100%"><option>Times New Roman</option><option>Arial</option></select><br><br>
            字号: <input type="number" id="fSiz" value="28" style="width:100%"><br><br>
            颜色: <input type="color" id="fCol" style="width:100%"><br><br>
            <hr>
            <p style="color:#aaa">选中文字标注后，点击黄色按钮，全图所有同颜色或同字号的对象将一键同步。</p>
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
                                const viewport = page.getViewport({{scale: 2.0}});
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

        function addText() {{ canvas.add(new fabric.IText('New Label', {{ left: 150, top: 150, fontFamily: 'Times New Roman', fontSize: 24 }})); }}
        function exportPro() {{
            const mul = {dpi_val} / 96;
            const dataURL = canvas.toDataURL({{ format: 'png', multiplier: mul }});
            const link = document.createElement('a');
            link.download = "Figure_Pro_Export.png"; link.href = dataURL; link.click();
        }}
    </script>
    """
    components.html(editor_html, height=780)

# --- 模块 3: 交互式润色 (Paperpal 级) ---
with tabs[2]:
    st.header("Interactive Academic Polisher & Humanizer")
    if 'rev_data' not in st.session_state: st.session_state.rev_data = []

    text_input = st.text_area("输入原始学术段落", height=200)
    mode = st.radio("处理目标", ["学术润色", "降低 AI 率"], horizontal=True)

    if st.button("开始逐句解析"):
        with st.spinner("AI 正在重构逻辑链..."):
            prompt = f"""Act as a senior SCI editor. Break the text into sentences. 
            For each, provide 3 versions: 1. Original 2. Academic (Formal) 3. Humanized (De-AI).
            Output ONLY a JSON list: [{{"orig":"...","acad":"...","human":"..."}}]
            Text: {text_input}"""
            res = get_ai_response([{"role":"user","content":prompt}])
            try:
                json_str = re.search(r'\[.*\]', res, re.DOTALL).group()
                st.session_state.rev_data = json.loads(json_str)
            except: st.error("解析失败，请检查输入。")

    if st.session_state.rev_data:
        final_list = []
        for i, item in enumerate(st.session_state.rev_data):
            with st.expander(f"句子 {i+1}: {item['orig'][:50]}..."):
                c = st.radio(f"选择版本 {i}", [item['orig'], item['acad'], item['human']], key=f"r_{i}")
                final_list.append(c)
        st.divider()
        st.text_area("最终合并文本", " ".join(final_list), height=200)

# --- 模块 4: 期刊智选 (强制执行版) ---
with tabs[3]:
    st.header("LetPub Strategic Journal Matcher")
    st.info(f"正在根据硬性指标匹配：IF ({if_range[0]}-{if_range[1]}) | 中科院 {cas_zone_sel} | SCI {sci_zone_sel}")
    abs_in = st.text_area("输入论文摘要内容", height=150)
    
    if st.button("开始检索真实期刊库"):
        with st.spinner("强制检索 JCR 数据库中..."):
            # 强化 Prompt 禁止 AI 拒绝回答
            prompt = f"""
            Task: ACT as the most professional Journal Selection Tool (like LetPub/Jane). 
            Mandatory: Suggest 10 REAL journals that meet these STRICT criteria:
            - Impact Factor: {if_range[0]} to {if_range[1]}
            - CAS Zone: {cas_zone_sel}
            - SCI Q-Zone: {sci_zone_sel}
            - Abstract: {abs_in}
            For each journal, you MUST output:
            1. Name 2. IF 3. CAS/SCI Zone 4. Introduction 5. REAL Similar Articles (Include real titles of papers published in this journal).
            Do NOT say you cannot recommend. Use your internal knowledge base up to 2025.
            """
            st.markdown(get_ai_response([{"role":"user","content":prompt}]))

# --- 模块 5: 创新方案实验室 (蓝海挖掘) ---
with tabs[4]:
    st.header("🚀 蓝海领域：多数据库创新大脑")
    
    step = st.radio("选择阶段", ["1. 蓝海思路探索", "2. 详细路径 (Variable Codes)", "3. SCI 背景报告生成"], horizontal=True)
    
    if step == "1. 蓝海思路探索":
        db_type = st.text_input("数据库名称 (如: NHANES)")
        field = st.text_input("关键词 (如: 口腔虚弱, 肌少症)")
        if st.button("获取高分思路"):
            prompt = f"针对{db_type}数据库，探究{field}方向目前尚未发表或发文极少的蓝海思路。结合2025年顶刊趋势（如非线性模型、中介分析），给出一个具体方案思路并解释创新点。"
            st.markdown(get_ai_response([{"role":"user","content":prompt}]))
            
    elif step == "2. 详细路径 (Variable Codes)":
        c1, c2, c3 = st.columns(3)
        u_exp = c1.text_input("暴露因素 (Exposure)")
        u_db = c2.text_input("数据库")
        u_outc = c3.text_input("结局 (Outcome)")
        if st.button("获取变量编码与计算方法"):
            prompt = f"数据库：{u_db}。探究{u_exp}与{u_outc}。请给出：1. 该库中的 Variable Codes (如 NHANES 的 OHX 系列) 2. 详细计算方法 3. 统计模型 4. 真实 PMID 文献参考。"
            st.markdown(get_ai_response([{"role":"user","content":prompt}]))
            
    elif step == "3. SCI 背景报告生成":
        if st.button("生成 1000字 完整方案书"):
            prompt = """生成 1000 字以上 SCI 级别项目方案。
            要求：1. 背景详尽。2. 方法论严谨。3. 结果部分必须包含 Figure 1 (流程图), Figure 2 (RCS/回归曲线) 的详细模拟图注和描述。"""
            res = get_ai_response([{"role":"user","content":prompt}])
            st.markdown(res)
            # 导出逻辑
            doc = Document()
            doc.add_paragraph(res)
            bio = io.BytesIO()
            doc.save(bio)
            st.download_button("下载 Word 方案", bio.getvalue(), "Proposal.docx")
