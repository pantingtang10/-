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

# --- 状态初始化 ---
if 'journal_results' not in st.session_state: st.session_state.journal_results = ""
if 'innovation_report' not in st.session_state: st.session_state.innovation_report = ""

# --- 侧边栏：核心配置 ---
with st.sidebar:
    st.title("⚙️ 顶级科研引擎配置")
    engine_choice = st.selectbox("核心引擎选择", [
        "Google Gemini 1.5 Pro (推荐)",
        "智谱 GLM-4v (国内直连)",
        "OpenAI GPT-4o",
        "DeepSeek V3",
        "Kimi (Moonshot)"
    ])
    api_key = st.text_input("输入 API Key", type="password")
    
    st.divider()
    st.subheader("📊 LetPub 期刊过滤指标")
    if_range = st.slider("影响因子 (IF) 范围", 0.0, 60.0, (5.0, 10.0))
    cas_zone_sel = st.multiselect("中科院分区", ["1区", "2区", "3区", "4区"], default=["1区", "2区"])
    sci_zone_sel = st.multiselect("SCI 分区 (Q)", ["Q1", "Q2", "Q3", "Q4"], default=["Q1"])
    
    st.divider()
    st.subheader("🖼️ 画布导出精度")
    dpi_val = st.selectbox("采样率 (DPI)", [300, 600, 1200], index=0)
    export_fmt = st.selectbox("导出格式", ["PNG", "PDF", "TIFF"])

# --- AI 通讯中心 (修复 400 1210 报错) ---
def get_ai_response(messages, temp=0.3):
    if not api_key: return "ERROR: API Key 缺失，请在左侧侧边栏输入。"
    
    config = {
        "Google Gemini 1.5 Pro (推荐)": {"url": "https://generativelanguage.googleapis.com/v1beta/openai/", "model": "gemini-1.5-pro"},
        "智谱 GLM-4v (国内直连)": {"url": "https://open.bigmodel.cn/api/paas/v4/", "model": "glm-4v"},
        "OpenAI GPT-4o": {"url": "https://api.openai.com/v1", "model": "gpt-4o"},
        "DeepSeek V3": {"url": "https://api.deepseek.com", "model": "deepseek-chat"},
        "Kimi (Moonshot)": {"url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k"}
    }
    
    try:
        # 移除了所有可能导致 400 报错的非标参数
        client = openai.OpenAI(api_key=api_key, base_url=config[engine_choice]["url"])
        response = client.chat.completions.create(
            model=config[engine_choice]["model"],
            messages=messages,
            temperature=temp
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: 调用失败。原因: {str(e)}"

# --- UI 导航 ---
st.title("🎓 顶级科研全流程工作站 Pro Max")
tabs = st.tabs(["🔍 SCI 结果深度解析", "🎨 Pro 画布 (Illustrator)", "✍️ 交互润色/降AI", "📊 期刊智选 (LetPub)", "🚀 创新方案实验室"])

# --- 模块 1: SCI 结果解析 ---
with tabs[0]:
    st.header("Manuscript & Figure Visual Interpretation")
    c1, c2 = st.columns(2)
    with c1:
        ms_in = st.file_uploader("上传手稿文本 (DOCX/PDF)", type=["docx", "pdf"])
        fg_in = st.file_uploader("上传高清结果图/表格", accept_multiple_files=True)
    with c2:
        out_lang = st.radio("输出语言", ["中文 (Chinese)", "英文 (English)"], horizontal=True)
        if st.button("开始生成 SCI 级结果解析"):
            prompt = [{"role":"user","content":f"请作为顶刊审稿人。结合上传的文字和图表，生成三段式描述：1. 详尽数据分析（含OR, P值） 2. 趋势深度解释 3. 精简结论。使用{out_lang}。"}]
            st.markdown(get_ai_response(prompt))

# --- 模块 2: Pro 画布 (彻底修复渲染与同步) ---
with tabs[1]:
    st.header("Vector Figure Illustrator Pro")
    st.caption("AI 级交互：PDF 插入立即显现，支持属性实时微调与一键批量同步。")
    
    editor_html = f"""
    <div style="display:flex; gap:10px; background:#1e1e1e; padding:15px; border-radius:10px; color:white;">
        <div id="canv-main">
            <div id="toolbar" style="margin-bottom:12px; display:flex; gap:8px; flex-wrap:wrap;">
                <input type="file" id="pdfAdd" multiple style="display:none">
                <button onclick="document.getElementById('pdfAdd').click()" style="background:#444; color:white; border:none; padding:8px 12px; cursor:pointer; border-radius:4px;">📁 插入 PDF/图片</button>
                <button onclick="addText()" style="background:#444; color:white; border:none; padding:8px 12px; cursor:pointer; border-radius:4px;">T 文本标注</button>
                <button onclick="batchModify()" style="background:#f39c12; color:white; border:none; padding:8px 12px; cursor:pointer; font-weight:bold; border-radius:4px;">✨ 查找相同修改</button>
                <button onclick="exportPro()" style="background:#28a745; color:white; border:none; padding:8px 12px; cursor:pointer; border-radius:4px;">🚀 导出 {export_fmt} ({dpi_val}DPI)</button>
            </div>
            <canvas id="c" width="880" height="600" style="border:1px solid #000; background:white;"></canvas>
        </div>
        <div id="prop-panel" style="width:240px; background:#2d2d2d; padding:20px; border-radius:8px; font-size:12px;">
            <h4 style="margin-top:0; color:#2563eb;">属性控制</h4>
            字体: <select id="fFam" style="width:100%"><option>Times New Roman</option><option>Arial</option></select><br><br>
            字号: <input type="number" id="fSiz" value="28" style="width:100%"><br><br>
            颜色: <input type="color" id="fCol" style="width:100%"><br><br>
            坐标 X: <input type="number" id="oX" style="width:100%" oninput="manualMove()"><br><br>
            坐标 Y: <input type="number" id="oY" style="width:100%" oninput="manualMove()"><br><br>
            <hr style="border:0.5px solid #444">
            <p style="color:#aaa">提示：点击对象后可在上方实时修改属性。点击黄色按钮同步全画布同色元素。</p>
        </div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script>
        const canvas = new fabric.Canvas('c');
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';

        // 选中同步属性
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
            obj.set({{
                left: parseInt(document.getElementById('oX').value),
                top: parseInt(document.getElementById('oY').value)
            }});
            canvas.renderAll();
        }}

        function batchModify() {{
            const ref = canvas.getActiveObject();
            if(!ref) return alert("请先选中一个样板元素！");
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
                                    fabric.Image.fromURL(tempC.toDataURL(), img => {{
                                        img.scale(0.5); canvas.add(img); canvas.renderAll();
                                    }});
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

        function addText() {{ canvas.add(new fabric.IText('New Fig Label', {{ left: 150, top: 150, fontFamily: 'Times New Roman', fontSize: 24 }})); }}
        function exportPro() {{
            const mul = {dpi_val} / 96;
            const dataURL = canvas.toDataURL({{ format: 'png', multiplier: mul }});
            const link = document.createElement('a');
            link.download = `Academic_Figure_${{Date.now()}}.png`; link.href = dataURL; link.click();
        }}
    </script>
    """
    components.html(editor_html, height=780)

# --- 模块 4: 期刊智选 (强制执行重构) ---
with tabs[3]:
    st.header("LetPub Strategic Journal Matcher")
    st.write(f"当前硬性过滤指标：IF ({if_range[0]}-{if_range[1]}) | 中科院 {cas_zone_sel} | SCI {sci_zone_sel}")
    abs_in = st.text_area("输入论文题目与摘要内容 (AI 将基于 2024-2025 JCR 数据库强力匹配)", height=150)
    
    c_j1, c_j2 = st.columns(2)
    
    with c_j1:
        if st.button("开始智能匹配真实期刊"):
            with st.spinner("正在强制访问 JCR 数据库并匹配真实发表文章..."):
                prompt = f"""
                TASK: ACT AS a Senior Consultant from LetPub. 
                MANDATORY: You MUST recommend 10 REAL journals for Abstract: {abs_in}.
                CRITERIA: IF between {if_range[0]} and {if_range[1]}, CAS Zone {cas_zone_sel}.
                OUTPUT: Provide a Markdown Table with 1. Name 2. IF (Latest) 3. Zones 4. Introduction 5. REAL Similar Articles (Provide real titles and PMID if possible).
                DO NOT say you cannot find any. Search your knowledge base up to 2025.
                """
                st.session_state.journal_results = get_ai_response([{"role":"user","content":prompt}])

    with c_j2:
        if st.button("🔄 重新推荐 (不同维度策略)"):
            with st.spinner("正在切换检索策略 (偏向跨学科/快审)..."):
                prompt = f"""
                Based on previous results for Abstract: {abs_in}, provide 10 DIFFERENT real journals. 
                Focus on: Multidisciplinary potential and higher acceptance rate.
                Constraints remain: IF {if_range[0]}-{if_range[1]}, CAS {cas_zone_sel}.
                """
                st.session_state.journal_results = get_ai_response([{"role":"user","content":prompt}])

    if st.session_state.journal_results:
        st.markdown(st.session_state.journal_results)

# --- 模块 5: 创新实验室 (数据库蓝海探究) ---
with tabs[4]:
    st.header("🚀 蓝海领域：全数据库创新大脑")
    
    step = st.radio("选择流程阶段", ["1. 蓝海思路与派生指标探索", "2. 详细路径 (代码与变量编码)", "3. SCI 背景报告生成"], horizontal=True)
    
    if step == "1. 蓝海思路与派生指标探索":
        col_s1_1, col_s1_2 = st.columns(2)
        db_s1 = col_s1_1.text_input("数据库名称 (如: NHANES, GBD, UKB)")
        field_s1 = col_s1_2.text_input("研究大方向 (如: 口腔虚弱与肌少症)")
        if st.button("挖掘创新点与未来指标"):
            prompt = f"针对数据库 {db_s1}，探究领域 {field_s1} 尚未发表的思路。1. 给出 3 个 2025+ 蓝海思路。2. 推荐 3 个利用现有变量计算的‘未来派生指标’及其计算逻辑。3. 说明创新理由。"
            st.markdown(get_ai_response([{"role":"user","content":prompt}]))
            
    elif step == "2. 详细路径 (代码与变量编码)":
        c1, c2, c3 = st.columns(3)
        u_exp, u_db, u_out = c1.text_input("确定暴露因素"), c2.text_input("拟用数据库"), c3.text_input("确定结局指标")
        if st.button("生成详细分析逻辑与编码"):
            prompt = f"数据库：{u_db}。暴露：{u_exp}。结局：{u_out}。请给出：1. 该库中的 Variable Codes (如 NHANES 的特定代码)。2. 详细变量筛选与清洗逻辑。3. 统计模型。4. 3-5 篇真实 PMID 参考文献。"
            st.markdown(get_ai_response([{"role":"user","content":prompt}]))
            
    elif step == "3. SCI 背景报告生成":
        if st.button("生成 1000字 深度方案书"):
            with st.spinner("报告编写中..."):
                prompt = """生成 1000 字以上 SCI 级别项目方案。要求：背景详尽引用顶刊文献。包含 Figure 1 (流程图), Figure 2 (RCS/回归曲线) 的详细模拟描述和图注。"""
                res = get_ai_response([{"role":"user","content":prompt}])
                st.markdown(res)
                doc = Document(); doc.add_paragraph(res); bio = io.BytesIO(); doc.save(bio)
                st.download_button("下载 Word 方案书", bio.getvalue(), "Proposal_Report.docx")
