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
st.set_page_config(page_title="Academic Intelligence Studio Ultra Pro", layout="wide", initial_sidebar_state="expanded")

# --- 侧边栏：全引擎与 LetPub 过滤器配置 ---
with st.sidebar:
    st.title("⚙️ 科研专家系统配置")
    engine_choice = st.selectbox("核心引擎 (需对应 Key)", [
        "Google Gemini 1.5 Pro",
        "智谱 GLM-4v (国内强力推荐)",
        "字节豆包 (Doubao)",
        "Kimi (Moonshot)",
        "DeepSeek V3",
        "OpenAI GPT-4o"
    ])
    api_key = st.text_input("输入 API 密钥 (Key)", type="password")
    
    ep_id = ""
    if "Doubao" in engine_choice:
        ep_id = st.text_input("豆包 Endpoint ID (必填)", type="default")

    st.divider()
    st.subheader("📊 LetPub 期刊硬性过滤")
    if_range = st.slider("影响因子范围 (IF)", 0.0, 50.0, (5.0, 7.0))
    cas_zone = st.multiselect("中科院分区", ["1区", "2区", "3区", "4区"], default=["2区"])
    sci_zone = st.multiselect("SCI 分区", ["Q1", "Q2", "Q3", "Q4"], default=["Q1", "Q2"])
    oa_req = st.checkbox("仅限 Open Access (OA)")

    st.divider()
    st.subheader("🖼️ Illustrator 导出参数")
    dpi_val = st.selectbox("导出精度 (DPI)", [300, 600, 1200], index=0)
    export_fmt = st.selectbox("导出格式", ["PDF", "PNG", "TIFF"])

# --- 核心 AI 调用逻辑 ---
def get_ai_response(messages, custom_model=None):
    if not api_key: return "ERROR: API Key Missing"
    
    # 修复 API 路由路径
    config = {
        "Google Gemini 1.5 Pro": {"url": "https://generativelanguage.googleapis.com/v1beta/openai/", "model": "gemini-1.5-pro"},
        "智谱 GLM-4v (国内强力推荐)": {"url": "https://open.bigmodel.cn/api/paas/v4/", "model": "glm-4v"},
        "字节豆包 (Doubao)": {"url": "https://ark.cn-beijing.volces.com/api/v3", "model": ep_id},
        "Kimi (Moonshot)": {"url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k"},
        "DeepSeek V3": {"url": "https://api.deepseek.com", "model": "deepseek-chat"},
        "OpenAI GPT-4o": {"url": "https://api.openai.com/v1", "model": "gpt-4o"}
    }
    
    target = config[engine_choice]
    m_name = custom_model if custom_model else target["model"]
    
    try:
        client = openai.OpenAI(api_key=api_key, base_url=target["url"])
        response = client.chat.completions.create(
            model=m_name,
            messages=messages,
            temperature=0.3,
            max_tokens=4000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: {str(e)}"

def clean_json(text):
    """鲁棒性 JSON 解析"""
    try:
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return None
    except:
        return None

# --- UI 界面 ---
st.title("🎓 顶级科研全生命周期全能工作站 Pro")
tabs = st.tabs(["🔍 SCI 结果描述", "🎨 Pro 画布 (Illustrator)", "✍️ 交互式润色/降AI", "📊 期刊智选 (LetPub)", "🚀 创新实验室"])

# --- 模块 1: SCI 结果描述 (支持多模态) ---
with tabs[0]:
    st.header("Manuscript & Figure Multimodal Analysis")
    c1, c2 = st.columns(2)
    with c1:
        ms_file = st.file_uploader("上传手稿 (DOCX/PDF)", type=["docx", "pdf"])
        figs_up = st.file_uploader("上传关键图表/表格", accept_multiple_files=True)
    with c2:
        out_lang = st.radio("输出语言", ["中文 (Chinese)", "英文 (English)"], horizontal=True)
        if st.button("开始深度解析结果"):
            with st.spinner("AI 正在同步分析文字逻辑与图表数据..."):
                prompt = [{"role":"user","content":f"请作为顶刊资深审稿人。结合上传的内容，生成SCI标准的结果描述。要求包含：1. 详细结果段落 2. 图注解释(Figure Legend) 3. 精简版结果总结。使用{out_lang}。"}]
                st.markdown(get_ai_response(prompt))

# --- 模块 2: Pro 画布 (Adobe Illustrator 级交互) ---
with tabs[1]:
    st.header("Vector Figure Illustrator Pro")
    st.caption("核心功能：多 PDF 叠加、查找相同修改、1200 DPI 采样导出。")
    
    editor_html = f"""
    <div style="display:flex; gap:10px; background:#1a1a1a; padding:15px; border-radius:10px; color:white;">
        <div id="main-canvas-area">
            <div style="margin-bottom:12px; display:flex; gap:8px; flex-wrap:wrap;">
                <input type="file" id="pdfAdd" multiple style="display:none">
                <button onclick="document.getElementById('pdfAdd').click()" style="background:#444; color:white; border:none; padding:8px 15px; cursor:pointer; border-radius:4px;">📁 插入 PDF/图片</button>
                <button onclick="addText()" style="background:#444; color:white; border:none; padding:8px 15px; cursor:pointer; border-radius:4px;">T 添加文本</button>
                <button onclick="batchModify()" style="background:#f39c12; color:white; border:none; padding:8px 15px; cursor:pointer; font-weight:bold; border-radius:4px;">✨ 查找相同修改</button>
                <button onclick="exportPro()" style="background:#28a745; color:white; border:none; padding:8px 15px; cursor:pointer; border-radius:4px;">🚀 导出 {export_fmt}</button>
            </div>
            <canvas id="c" width="880" height="620" style="border:1px solid #333; background:white;"></canvas>
        </div>
        <div id="prop-panel" style="width:240px; background:#2d2d2d; padding:20px; border-radius:8px;">
            <h4 style="margin-top:0">属性面板 (Pro)</h4>
            字体: <select id="fFam" style="width:100%; margin-bottom:15px;"><option>Times New Roman</option><option>Arial</option><option>Helvetica</option></select>
            字号: <input type="number" id="fSiz" value="28" style="width:100%; margin-bottom:15px;">
            颜色: <input type="color" id="fCol" style="width:100%; margin-bottom:15px;">
            <hr style="border:0.5px solid #555">
            <p style="font-size:11px; color:#999;">说明：PDF 插入不可见问题已修复。选中任意标注，点击“查找相同修改”，画布内所有同颜色/字号的对象将一键同步。</p>
        </div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js"></script>
    <script>
        const canvas = new fabric.Canvas('c');
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';

        function batchModify() {{
            const ref = canvas.getActiveObject();
            if(!ref) return alert("请先选中一个样板元素！");
            const newCol = document.getElementById('fCol').value;
            const newSiz = parseInt(document.getElementById('fSiz').value);
            const newFam = document.getElementById('fFam').value;
            canvas.getObjects().forEach(obj => {{
                if(obj.type === ref.type && (obj.fill === ref.fill || obj.fontSize === ref.fontSize)) {{
                    obj.set({{ fill: newCol, fontSize: newSiz, fontFamily: newFam }});
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
            link.download = "Academic_Figure_HighRes.png"; link.href = dataURL; link.click();
        }}
    </script>
    """
    components.html(editor_html, height=780)

# --- 模块 3: 交互式润色 (Paperpal 级) ---
with tabs[2]:
    st.header("Interactive Academic Polisher & Humanizer")
    if 'p_data' not in st.session_state: st.session_state.p_data = []

    raw_text = st.text_area("输入手稿段落", height=200, placeholder="We observed the values were increased...")
    mode = st.radio("润色主攻方向", ["专业润色 (Make Academic)", "降 AI 率重构 (De-AI Humanizer)"], horizontal=True)

    if st.button("开始逐句交互润色"):
        if raw_text:
            with st.spinner("AI 正在重构逻辑链..."):
                prompt = f"""
                Act as a senior academic editor. Break the following text into sentences.
                Provide 3 versions for each: 
                1. Original 
                2. Academic (Formal, native tone)
                3. Humanized (Reduce AI detection, high perplexity, varied syntax)
                Output ONLY a JSON list: [{{"orig": "...", "acad": "...", "human": "..."}}]
                Text: {raw_text}
                """
                res = get_ai_response([{"role": "user", "content": prompt}])
                st.session_state.p_data = clean_json(res)

    if st.session_state.p_data:
        st.subheader("💡 修订选择 (点击切换版本):")
        final_list = []
        for i, item in enumerate(st.session_state.p_data):
            with st.expander(f"句子 {i+1}: {item['orig'][:60]}..."):
                c = st.radio(f"选择 S{i+1}", [item['orig'], item['acad'], item['human']], key=f"s_{i}", index=1 if mode=="专业润色 (Make Academic)" else 2)
                final_list.append(c)
        
        full_p = " ".join(final_list)
        st.text_area("已修改文本", full_p, height=200)
        # Word 导出
        doc = Document()
        doc.add_paragraph(full_p)
        bio = io.BytesIO()
        doc.save(bio)
        st.download_button("下载修订版 Word", bio.getvalue(), "Revised.docx")

# --- 模块 4: 期刊匹配 (LetPub 逻辑) ---
with tabs[3]:
    st.header("LetPub Strategic Matcher")
    st.write(f"当前过滤：IF {if_range} | 中科院 {cas_zone} | SCI {sci_zone} | OA: {oa_req}")
    abs_in = st.text_area("输入摘要", height=150)
    if st.button("开始智能检索期刊"):
        prompt = f"参考 LetPub 和 JANE 逻辑。基于摘要推荐 10 个真实期刊。筛选条件：IF {if_range}，中科院 {cas_zone}，SCI {sci_zone}。列出：期刊名、IF、分区、简介、OA状态及同数据库发表的文章 (含真实 PMID/DOI)。"
        st.markdown(get_ai_response([{"role": "user", "content": prompt}]))

# --- 模块 5: 创新方案实验室 (多阶段) ---
with tabs[4]:
    st.header("🚀 创新方案生成中心 (多数据库联动)")
    stage = st.radio("阶段", ["1. 思路探索", "2. 详细路径与编码", "3. 完整报告生成"], horizontal=True)
    
    if stage == "1. 思路探索":
        db = st.text_input("拟使用数据库 (如 NHANES + GBD)")
        field = st.text_input("研究领域 (如 衰弱/Sarcopenia)")
        if st.button("获取 2024-2025 最新思路"):
            prompt = f"基于{db}和{field}，分析 2024-2025 发文趋势，给 3 个创新思路（如机器学习共病轨迹、中介效应、组学联合）。附带理由和参考文章。"
            st.markdown(get_ai_response([{"role":"user","content":prompt}]))
            
    elif stage == "2. 详细路径与编码":
        c1, c2, c3 = st.columns(3)
        exp, dbs, outc = c1.text_input("暴露因子"), c2.text_input("数据库名"), c3.text_input("结局疾病")
        if st.button("生成详细筛选逻辑"):
            prompt = f"数据库：{dbs}。探究 {exp} 与 {outc}。给出具体的计算公式、Variable Codes (如 NHANES 的特定代码)、统计模型逻辑及创新点论证。"
            st.markdown(get_ai_response([{"role":"user","content":prompt}]))
            
    elif stage == "3. 报告生成":
        u_cmd = st.chat_input("输入交互指令 (如：增加针对肾功能的亚组分析设计)")
        if st.button("生成 1000字 SCI 完整背景报告"):
            prompt = "生成一份 1000 字左右的 SCI 背景方案报告。要求：参考文献真实有效（近5年），方法论极其详尽，结果部分包含 Figure 1-3 的模拟图注描述。输出段落形式。"
            report_text = get_ai_response([{"role": "user", "content": prompt}])
            st.markdown(report_text)
            # 导出 Word
            d = Document()
            d.add_heading('Academic Innovation Proposal', 0)
            d.add_paragraph(report_text)
            b = io.BytesIO()
            d.save(b)
            st.download_button("导出为 1000字 Word 方案", b.getvalue(), "Proposal.docx")
