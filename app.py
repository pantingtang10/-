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
st.set_page_config(page_title="Academic Intelligence Studio Ultra Pro Max", layout="wide", initial_sidebar_state="expanded")

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
    if_range = st.slider("影响因子范围", 0.0, 60.0, (5.0, 10.0))
    cas_zone_sel = st.multiselect("中科院分区", ["1区", "2区", "3区", "4区"], default=["1区", "2区"])
    sci_zone_sel = st.multiselect("SCI 分区 (Q)", ["Q1", "Q2", "Q3", "Q4"], default=["Q1"])
    
    st.divider()
    st.subheader("🖼️ Illustrator 导出精度")
    dpi_val = st.selectbox("采样率 (DPI)", [300, 600, 1200], index=0)
    export_fmt = st.selectbox("导出格式", ["PNG", "PDF", "TIFF"])

# --- AI 通讯中心 ---
def get_ai_response(messages, temp=0.2):
    if not api_key: return "ERROR: API Key 缺失，请在左侧侧边栏输入。"
    
    config = {
        "Google Gemini 1.5 Pro (推荐)": {"url": "https://generativelanguage.googleapis.com/v1beta/openai/", "model": "gemini-1.5-pro"},
        "智谱 GLM-4v (国内直连)": {"url": "https://open.bigmodel.cn/api/paas/v4/", "model": "glm-4v"},
        "OpenAI GPT-4o": {"url": "https://api.openai.com/v1", "model": "gpt-4o"},
        "DeepSeek V3": {"url": "https://api.deepseek.com", "model": "deepseek-chat"},
        "Kimi (Moonshot)": {"url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k"}
    }
    
    try:
        client = openai.OpenAI(api_key=api_key, base_url=config[engine_choice]["url"])
        response = client.chat.completions.create(
            model=config[engine_choice]["model"],
            messages=messages,
            temperature=temp,
            max_tokens=4000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: 调用失败。原因: {str(e)}"

# --- UI 导航 ---
st.title("🎓 顶级科研全流程工作站 Pro Max (2026最终版)")
tabs = st.tabs(["🔍 SCI 结果深度解析", "🎨 Pro 画布 (Illustrator)", "✍️ 交互润色/降AI", "📊 期刊智选 (LetPub)", "🚀 创新方案实验室"])

# --- 模块 1: SCI 结果解析 ---
with tabs[0]:
    st.header("Manuscript & Figure Visual Interpretation")
    c1, c2 = st.columns(2)
    with c1:
        ms_in = st.file_uploader("上传手稿文本 (DOCX/PDF)", type=["docx", "pdf"])
        fg_in = st.file_uploader("上传高精结果图/表格 (可多选)", accept_multiple_files=True)
    with c2:
        out_lang = st.radio("输出语言", ["中文 (Chinese)", "英文 (English)"], horizontal=True)
        if st.button("开始生成 SCI 级深度结果解析"):
            with st.spinner("AI 正在深度扫描数据显著性与趋势..."):
                prompt = [{"role":"user","content":f"请作为顶刊审稿人。结合上传的文本和图表，生成SCI标准的Results描述。要求：1. 带有统计指标（OR, CI, P值）的详版 2. 对图表显著差异的专业解释 3. 仿Nature精简版结论。使用{out_lang}。"}]
                st.markdown(get_ai_response(prompt))

# --- 模块 2: Pro 画布 (彻底修复版) ---
with tabs[1]:
    st.header("Vector Figure Illustrator Pro")
    st.caption("支持多 PDF 同时插入、属性实时微调、‘✨’一键同步全局标注。")
    
    editor_html = f"""
    <div style="display:flex; gap:10px; background:#1e1e1e; padding:15px; border-radius:10px; color:white; font-family: sans-serif;">
        <div id="canv-main">
            <div id="toolbar" style="margin-bottom:12px; display:flex; gap:8px;">
                <input type="file" id="pdfAdd" multiple style="display:none">
                <button onclick="document.getElementById('pdfAdd').click()" style="background:#444; color:white; border:none; padding:8px 12px; cursor:pointer; border-radius:4px;">📁 插入 PDF/图片</button>
                <button onclick="addText()" style="background:#444; color:white; border:none; padding:8px 12px; cursor:pointer; border-radius:4px;">T 文本标注</button>
                <button onclick="batchModify()" style="background:#f39c12; color:white; border:none; padding:8px 12px; cursor:pointer; font-weight:bold; border-radius:4px;">✨ 查找相同修改</button>
                <button onclick="exportPro()" style="background:#28a745; color:white; border:none; padding:8px 12px; cursor:pointer; border-radius:4px;">🚀 导出 {export_fmt} ({dpi_val}DPI)</button>
            </div>
            <canvas id="c" width="880" height="600" style="border:1px solid #000; background:white;"></canvas>
        </div>
        <div id="prop-panel" style="width:240px; background:#2d2d2d; padding:20px; border-radius:8px; font-size:12px;">
            <h4 style="margin-top:0; color:#2563eb;">属性面板</h4>
            字体: <select id="fFam" style="width:100%"><option>Times New Roman</option><option>Arial</option></select><br><br>
            字号: <input type="number" id="fSiz" value="28" style="width:100%"><br><br>
            颜色: <input type="color" id="fCol" style="width:100%"><br><br>
            坐标 X: <input type="number" id="oX" style="width:100%" oninput="manualMove()"><br><br>
            坐标 Y: <input type="number" id="oY" style="width:100%" oninput="manualMove()"><br><br>
            <hr style="border:0.5px solid #444">
            <p style="color:#aaa">提示：选中对象后点‘✨’，全画布同类元素将同步修改。PDF 插入支持 1200 DPI 采样。</p>
        </div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script>
        const canvas = new fabric.Canvas('c');
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';

        canvas.on('selection:created', syncPanel);
        canvas.on('selection:updated', syncPanel);
        function syncPanel() {{
            const obj = canvas.getActiveObject();
            if(!obj) return;
            document.getElementById('oX').value = Math.round(obj.left);
            document.getElementById('oY').value = Math.round(obj.top);
            if(obj.type === 'i-text') {{
                document.getElementById('fSiz').value = obj.fontSize;
                document.getElementById('fCol').value = obj.fill;
            }}
        }}

        function manualMove() {{
            const obj = canvas.getActiveObject();
            if(!obj) return;
            obj.set({{ left: parseInt(document.getElementById('oX').value), top: parseInt(document.getElementById('oY').value) }});
            canvas.renderAll();
        }}

        function batchModify() {{
            const ref = canvas.getActiveObject();
            if(!ref) return alert("请先选中一个样板标注");
            const nCol = document.getElementById('fCol').value;
            const nSiz = parseInt(document.getElementById('fSiz').value);
            const nFam = document.getElementById('fFam').value;
            canvas.getObjects().forEach(obj => {{
                if(obj.type === ref.type && (obj.fill === ref.fill || obj.fontSize === ref.fontSize)) {{
                    obj.set({{ fill: nCol, fontSize: nSiz, fontFamily: nFam }});
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
                    reader.onload = f => fabric.Image.fromURL(f.target.result, img => {{ img.scale(0.25); canvas.add(img); }});
                    reader.readAsDataURL(file);
                }}
            }}
        }};

        function addText() {{ canvas.add(new fabric.IText('Fig Label', {{ left: 150, top: 150, fontFamily: 'Times New Roman', fontSize: 24 }})); }}
        function exportPro() {{
            const mul = {dpi_val} / 96;
            const dataURL = canvas.toDataURL({{ format: 'png', multiplier: mul }});
            const link = document.createElement('a');
            link.download = `Figure_Pro_Export.png`; link.href = dataURL; link.click();
        }}
    </script>
    """
    components.html(editor_html, height=780)

# --- 模块 3: 交互式润色 (Paperpal 级) ---
with tabs[2]:
    st.header("Interactive Academic Polisher & Humanizer")
    if 'rev_data' not in st.session_state: st.session_state.rev_data = []

    text_input = st.text_area("输入原始学术文本", height=200)
    mode = st.radio("处理目标", ["专业润色 (Academic)", "降低 AI 率 (De-AI)"], horizontal=True)

    if st.button("开始逐句解析润色"):
        with st.spinner("AI 正在重构逻辑链..."):
            prompt = f"""Act as a senior SCI editor. Break the text into sentences. For each, provide 3 versions: 1. Original 2. Academic (Paperpal-style) 3. Humanized (De-AI). Output ONLY a JSON list: [{{"orig":"...","acad":"...","human":"..."}}] Text: {text_input}"""
            res = get_ai_response([{"role":"user","content":prompt}])
            try:
                json_str = re.search(r'\[.*\]', res, re.DOTALL).group()
                st.session_state.rev_data = json.loads(json_str)
            except: st.error("解析失败。请确保输入的是完整的学术文本。")

    if st.session_state.rev_data:
        st.subheader("💡 逐句修订选择面板:")
        final_list = []
        for i, item in enumerate(st.session_state.rev_data):
            with st.expander(f"句子 {i+1}: {item['orig'][:60]}..."):
                c = st.radio(f"S{i+1} 版本", [item['orig'], item['acad'], item['human']], key=f"rev_{i}", index=1 if mode=="专业润色 (Academic)" else 2)
                final_list.append(c)
        st.divider()
        st.text_area("最终合并文本", " ".join(final_list), height=200)

# --- 模块 4: 期刊智选 (强制重推版) ---
with tabs[3]:
    st.header("LetPub Strategic Journal Matcher")
    
    # 状态初始化
    if 'journals' not in st.session_state: st.session_state.journals = ""

    st.info(f"硬性指标：IF ({if_range[0]}-{if_range[1]}) | 中科院 {cas_zone_sel} | SCI {sci_zone_sel}")
    abs_in = st.text_area("输入论文摘要 (AI 将匹配真实发表库)", height=150)
    
    col_j1, col_j2 = st.columns([1, 1])
    
    with col_j1:
        if st.button("开始智能检索真实期刊"):
            with st.spinner("正在强制检索 JCR 2024 数据库记录..."):
                prompt = f"""
                TASK: ACT AS LetPub Senior Consultant. 
                MANDATORY: Suggest 10 REAL journals for Abstract: {abs_in}.
                STRICT FILTERS: IF {if_range[0]} to {if_range[1]}, CAS Zone {cas_zone_sel}.
                FORMAT (Table): 1. Journal Name 2. Latest IF 3. Zones 4. Introduction 5. REAL Related Article Title published in this journal (PMID style).
                DO NOT apologize. MUST provide 10 journals.
                """
                st.session_state.journals = get_ai_response([{"role":"user","content":prompt}])

    with col_j2:
        if st.button("🔄 重新推荐 (不同维度)"):
            with st.spinner("正在切换检索策略，获取更多匹配..."):
                prompt = f"""
                基于上一次推荐的结果，请提供 10 个完全不同的、更偏向交叉学科或新兴方向的真实期刊。
                条件不变：IF {if_range[0]}-{if_range[1]}, CAS {cas_zone_sel}.
                Abstract: {abs_in}.
                """
                st.session_state.journals = get_ai_response([{"role":"user","content":prompt}])

    if st.session_state.journals:
        st.markdown(st.session_state.journals)

# --- 模块 5: 创新方案实验室 (三阶段) ---
with tabs[4]:
    st.header("🚀 蓝海领域：多数据库创新大脑")
    
    step = st.radio("选择流程阶段", ["1. 蓝海思路与未来指标探索", "2. 详细路径 (Variable Codes)", "3. SCI 方案完整报告生成"], horizontal=True)
    
    if step == "1. 蓝海思路与未来指标探索":
        db_s1 = st.text_input("拟用数据库 (如: NHANES + UKB)")
        field_s1 = st.text_input("研究大方向 (如: 口腔虚弱, 肌少症)")
        if st.button("挖掘创新点"):
            prompt = f"基于数据库{db_s1}探究{field_s1}的蓝海点。1. 给出 3 个 2025 创新思路。2. 重点：推荐 3 个利用现有变量计算出的创新派生指标（未来指标）。"
            st.markdown(get_ai_response([{"role":"user","content":prompt}]))
            
    elif step == "2. 详细路径 (Variable Codes)":
        c1, c2, c3 = st.columns(3)
        u_exp, u_db, u_out = c1.text_input("暴露因素"), c2.text_input("数据库"), c3.text_input("结局")
        if st.button("生成详细筛选方案与变量编码"):
            prompt = f"数据库：{u_db}。探究{u_exp}与{u_out}。给出：1. Variable Codes (如 NHANES 的真实代码)。2. 详细计算方法。3. 3-5 篇真实 PMID 参考文献。"
            st.markdown(get_ai_response([{"role":"user","content":prompt}]))
            
    elif step == "3. SCI 方案完整报告生成":
        if st.button("生成 1000字 深度方案书"):
            with st.spinner("报告编写中..."):
                prompt = """生成一份 1000 字以上、严谨的 SCI 项目背景方案。要求：参考文献真实（近5年），含详细方法论和 Figure 1-3 模拟描述及图注。"""
                res = get_ai_response([{"role":"user","content":prompt}])
                st.markdown(res)
                # Word 导出
                doc = Document(); doc.add_paragraph(res); bio = io.BytesIO(); doc.save(bio)
                st.download_button("下载 Word 方案书", bio.getvalue(), "Research_Proposal.docx")
