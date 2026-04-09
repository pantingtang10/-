import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import openai
import base64
import io
import json
import re
from docx import Document

# --- 页面配置 ---
st.set_page_config(page_title="Academic Studio Ultra Pro", layout="wide", initial_sidebar_state="expanded")

# --- 侧边栏：修复所有变量定义 ---
with st.sidebar:
    st.title("⚙️ 全球引擎中心")
    engine_choice = st.selectbox("选择核心引擎", [
        "Google Gemini 1.5 Pro",
        "智谱 GLM-4v (国内推荐)",
        "字节豆包 (Doubao)",
        "Kimi (Moonshot)",
        "OpenAI GPT-4o"
    ])
    api_key = st.text_input("API Key", type="password")
    
    # 豆包 Endpoint ID
    ep_id = st.text_input("豆包 Endpoint ID (仅豆包需要)", "")

    st.divider()
    st.subheader("📊 期刊 LetPub 过滤器")
    if_range = st.slider("影响因子 (IF)", 0.0, 50.0, (5.0, 7.0))
    cas_zone = st.multiselect("中科院分区", ["1区", "2区", "3区"], default=["2区"])
    sci_zone = st.multiselect("SCI 分区", ["Q1", "Q2", "Q3"], default=["Q1"])
    oa_req = st.checkbox("仅 Open Access")

    st.divider()
    st.subheader("🖼️ Illustrator 导出")
    dpi_val = st.selectbox("DPI", [300, 600, 1200], index=0)
    export_fmt = st.selectbox("格式", ["PDF", "PNG", "TIFF"])

# --- 核心 AI 调用函数 (增强鲁棒性) ---
def get_ai_response(messages):
    if not api_key: return "ERROR: Missing API Key"
    
    config = {
        "Google Gemini 1.5 Pro": {"url": "https://generativelanguage.googleapis.com/v1beta/openai/", "model": "gemini-1.5-pro"},
        "智谱 GLM-4v (国内推荐)": {"url": "https://open.bigmodel.cn/api/paas/v4/", "model": "glm-4v"},
        "字节豆包 (Doubao)": {"url": "https://ark.cn-beijing.volces.com/api/v3", "model": ep_id},
        "Kimi (Moonshot)": {"url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k"},
        "OpenAI GPT-4o": {"url": "https://api.openai.com/v1", "model": "gpt-4o"}
    }
    
    target = config[engine_choice]
    try:
        client = openai.OpenAI(api_key=api_key, base_url=target["url"])
        response = client.chat.completions.create(
            model=target["model"],
            messages=messages,
            temperature=0.3,
            response_format={ "type": "text" } # 某些模型不支持 json_object，此处用文本接收
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: {str(e)}"

# --- 模块 1: SCI 结果描述 ---
st.title("🎓 顶级科研全能工作站 Pro")
tabs = st.tabs(["🔍 SCI 结果解析", "🎨 Pro 画布(AI级)", "✍️ 交互润色/降AI", "📊 期刊智选", "🚀 创新大脑"])

with tabs[0]:
    st.header("SCI Results & Figure Interpretation")
    c1, c2 = st.columns(2)
    with c1:
        ms_file = st.file_uploader("上传手稿", type=["docx", "pdf"])
        figs_up = st.file_uploader("上传清晰结果图", accept_multiple_files=True)
    with c2:
        out_lang = st.radio("输出语言", ["中文", "英文"], horizontal=True)
        if st.button("开始深度解析"):
            prompt = [{"role":"user","content":f"结合上传内容，生成两版本SCI结果描述：1. 详细数据版（含P值/趋势） 2. 图注版。使用{out_lang}。"}]
            st.markdown(get_ai_response(prompt))

# --- 模块 2: Pro 画布 (修复渲染 & 批量修改) ---
with tabs[1]:
    st.header("Vector Figure Illustrator")
    st.caption("AI级交互：插入多个PDF，点击元素修改，点‘✨’同步全图同属性对象。")
    
    editor_html = f"""
    <div style="display:flex; gap:10px; background:#1e1e1e; padding:15px; border-radius:10px; color:white;">
        <div id="canv-container">
            <div style="margin-bottom:10px; display:flex; gap:8px;">
                <input type="file" id="pdfAdd" multiple style="display:none">
                <button onclick="document.getElementById('pdfAdd').click()" style="background:#444; color:white; border:none; padding:8px 12px; cursor:pointer;">📁 插入 PDF/图片</button>
                <button onclick="addText()" style="background:#444; color:white; border:none; padding:8px 12px; cursor:pointer;">T 文本</button>
                <button onclick="batchEdit()" style="background:#f39c12; color:white; border:none; padding:8px 12px; cursor:pointer; font-weight:bold;">✨ 查找相同修改</button>
                <button onclick="exportPro()" style="background:#28a745; color:white; border:none; padding:8px 12px; cursor:pointer;">🚀 导出 {export_fmt}</button>
            </div>
            <canvas id="c" width="850" height="550" style="border:1px solid #000; background:white;"></canvas>
        </div>
        <div style="width:200px; background:#2d2d2d; padding:15px; font-size:12px;">
            <h4>属性面板</h4>
            字体: <select id="fFam" style="width:100%"><option>Times New Roman</option><option>Arial</option></select><br><br>
            字号: <input type="number" id="fSiz" value="28" style="width:100%"><br><br>
            颜色: <input type="color" id="fCol" style="width:100%"><br><br>
            <hr>
            <p>说明：PDF 插入看不见通常是因为渲染未完成，请稍等2秒。选中文字后点黄色按钮可批量修改颜色/字号。</p>
        </div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js"></script>
    <script>
        const canvas = new fabric.Canvas('c');
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';

        function batchEdit() {{
            const ref = canvas.getActiveObject();
            if(!ref) return alert("请先选中一个样板标注");
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

        function addText() {{ canvas.add(new fabric.IText('New Label', {{ left: 100, top: 100, fontFamily: 'Times New Roman', fontSize: 24 }})); }}
        function exportPro() {{
            const mul = {dpi_val} / 96;
            const dataURL = canvas.toDataURL({{ format: 'png', multiplier: mul }});
            const link = document.createElement('a');
            link.download = "Figure_Export.png"; link.href = dataURL; link.click();
        }}
    </script>
    """
    components.html(editor_html, height=750)

# --- 模块 3: 交互式润色 (Paperpal 级) ---
with tabs[2]:
    st.header("Interactive Academic Polisher")
    if 'p_data' not in st.session_state: st.session_state.p_data = []

    raw_text = st.text_area("输入原始学术文本", height=200)
    mode = st.radio("模式", ["专业润色", "降 AI 重构"], horizontal=True)

    if st.button("开始逐句解析"):
        with st.spinner("AI 正在重构..."):
            # 修复转义 {{ }} 解决 ValueError
            prompt = f"""Act as a senior editor. Break the text into sentences. For each, provide 3 versions: 
            1. Original 2. Academic 3. Humanized (Reduce AI rate). 
            Output ONLY a JSON list: [{{"orig":"...","acad":"...","human":"..."}}]
            Text: {raw_text}"""
            res = get_ai_response([{"role":"user","content":prompt}])
            try:
                # 鲁棒 JSON 解析
                json_match = re.search(r'\[.*\]', res, re.DOTALL)
                if json_match:
                    st.session_state.p_data = json.loads(json_match.group())
                else: st.error("AI 未返回标准 JSON 格式")
            except: st.error("解析失败，请重试")

    if st.session_state.p_data:
        st.subheader("💡 逐句确认 (点击切换版本):")
        final_list = []
        for i, item in enumerate(st.session_state.p_data):
            with st.expander(f"句子 {i+1}: {item['orig'][:50]}..."):
                c = st.radio(f"S{i+1}", [item['orig'], item['acad'], item['human']], key=f"rev_{i}")
                final_list.append(c)
        st.divider()
        full_res = " ".join(final_list)
        st.text_area("润色后全文本", full_res, height=200)

# --- 模块 4: 期刊智选 (LetPub 逻辑) ---
with tabs[3]:
    st.header("LetPub Strategic Matcher")
    st.write(f"当前过滤: IF {if_range} | 中科院 {cas_zone} | SCI {sci_zone} | OA: {oa_req}")
    abs_in = st.text_area("输入论文摘要", height=150)
    if st.button("检索真实期刊库"):
        prompt = f"参考 LetPub。基于摘要，在 IF {if_range} 范围内推荐 10 个中科院 {cas_zone} 期刊。要求给出真实 PMID 的相关文章。"
        st.markdown(get_ai_response([{"role":"user","content":prompt}]))

# --- 模块 5: 创新实验室 (三段式) ---
with tabs[4]:
    st.header("🚀 创新方案实验室")
    step = st.radio("阶段", ["1. 思路探索", "2. 详细路径", "3. 生成 1000字 方案"], horizontal=True)
    
    if step == "1. 思路探索":
        db = st.text_input("数据库名 (如 NHANES + GBD)")
        if st.button("获取高分发文思路"):
            st.markdown(get_ai_response([{"role":"user","content":f"分析数据库{db}的2025创新思路，给出参考文章。"}]))
    elif step == "2. 详细路径":
        c1, c2, c3 = st.columns(3)
        exp, dbs, outc = c1.text_input("暴露"), c2.text_input("数据库"), c3.text_input("结局")
        if st.button("生成详细筛选编码"):
            st.markdown(get_ai_response([{"role":"user","content":f"数据库{dbs}中，探究{exp}与{outc}。给出Variable Codes和计算公式。"}]))
    elif step == "3. 生成 方案":
        if st.button("生成 Word 报告预览"):
            report = get_ai_response([{"role":"user","content":"生成 1000 字 SCI 背景方案报告，含真实近5年文献及 Figure 1-3 模拟描述。"}])
            st.markdown(report)
            doc = Document()
            doc.add_paragraph(report)
            bio = io.BytesIO()
            doc.save(bio)
            st.download_button("下载 Word 报告", bio.getvalue(), "Proposal.docx")
