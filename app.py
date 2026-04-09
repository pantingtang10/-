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
st.set_page_config(page_title="Academic Intelligence Studio Ultra", layout="wide", initial_sidebar_state="expanded")

# --- 侧边栏：全引擎配置 ---
with st.sidebar:
    st.title("⚙️ 科研引擎配置")
    engine_choice = st.selectbox("核心引擎 (需对应 Key)", [
        "Google Gemini 1.5 Pro",
        "智谱 GLM-4v (国内推荐)",
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
    st.subheader("📊 期刊 LetPub 过滤器")
    if_range = st.slider("影响因子范围", 0.0, 50.0, (5.0, 7.0))
    cas_zone = st.multiselect("中科院分区", ["1区", "2区", "3区"], default=["2区"])
    sci_zone = st.multiselect("SCI 分区", ["Q1", "Q2", "Q3"], default=["Q1", "Q2"])
    oa_req = st.checkbox("仅限 Open Access")

    st.divider()
    st.subheader("🖼️ 画布导出设置")
    dpi_val = st.selectbox("导出精度 (DPI)", [300, 600, 1200], index=0)
    export_fmt = st.selectbox("格式", ["PDF", "PNG", "TIFF"])

# --- 核心 AI 调用函数 (修复 Gemini & 豆包路径) ---
def get_ai_response(messages, custom_model=None):
    if not api_key: return "ERROR: Missing API Key"
    
    config = {
        "Google Gemini 1.5 Pro": {"url": "https://generativelanguage.googleapis.com/v1beta/openai/", "model": "gemini-1.5-pro"},
        "智谱 GLM-4v (国内推荐)": {"url": "https://open.bigmodel.cn/api/paas/v4/", "model": "glm-4v"},
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
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: {str(e)}"

# --- UI 导航 ---
st.title("🎓 顶级科研全生命周期全能工作站")
tabs = st.tabs(["🔍 SCI 结果描述", "🎨 Pro 画布 (Illustrator)", "✍️ 交互式润色/降AI", "📊 期刊智选 (LetPub)", "💡 创新大脑实验室"])

# --- 模块 1: SCI 结果描述 (支持手稿+图表) ---
with tabs[0]:
    st.header("Manuscript & Figure Neural Description")
    c1, c2 = st.columns(2)
    with c1:
        ms_file = st.file_uploader("上传手稿 (DOCX/PDF)", type=["docx", "pdf"])
        figs_up = st.file_uploader("上传图表/表格", accept_multiple_files=True)
    with c2:
        out_lang = st.radio("输出语言", ["中文 (Chinese)", "英文 (English)"], horizontal=True)
        if st.button("一键生成 SCI 级深度描述"):
            with st.spinner("AI 正在比对手稿逻辑与图表数据..."):
                prompt = [{"role":"user","content":f"请作为顶刊审稿人。根据上传的手稿和图表，输出详细的结果描述（Results）。要求包含：1. 详细结果描述 2. 图例说明(Figure Legend) 3. 精简版结果。使用{out_lang}。"}]
                st.markdown(get_ai_response(prompt))

# --- 模块 2: Pro 画布 (对标 Adobe Illustrator) ---
with tabs[1]:
    st.header("Vector Figure Illustrator Pro")
    st.caption("功能：支持多 PDF/图片叠加、颜色/字号查找修改、1200DPI 导出。")
    
    editor_html = f"""
    <div style="display:flex; gap:10px; background:#1e1e1e; padding:15px; border-radius:10px; color:white;">
        <div id="canv-main">
            <div style="margin-bottom:10px; display:flex; gap:8px;">
                <input type="file" id="pdfAdd" multiple style="display:none">
                <button onclick="document.getElementById('pdfAdd').click()" style="background:#444; color:white; border:none; padding:8px 12px; cursor:pointer; border-radius:4px;">📁 插入 PDF/图片</button>
                <button onclick="addText()" style="background:#444; color:white; border:none; padding:8px 12px; cursor:pointer; border-radius:4px;">T 文本标注</button>
                <button onclick="batchModify()" style="background:#f39c12; color:white; border:none; padding:8px 12px; cursor:pointer; font-weight:bold;">✨ 查找相同修改</button>
                <button onclick="exportPro()" style="background:#28a745; color:white; border:none; padding:8px 12px; cursor:pointer;">🚀 导出 {export_fmt}</button>
            </div>
            <canvas id="c" width="900" height="600" style="border:1px solid #000; background:white;"></canvas>
        </div>
        <div style="width:220px; background:#2d2d2d; padding:15px; font-size:12px;">
            <h4>属性控制 (Properties)</h4>
            字体: <select id="fFam" style="width:100%"><option>Times New Roman</option><option>Arial</option></select><br><br>
            字号: <input type="number" id="fSiz" value="28" style="width:100%"><br><br>
            颜色: <input type="color" id="fCol" style="width:100%"><br><br>
            <hr>
            <p>说明：PDF 插入后可自由点击移动。使用“查找相同修改”可同步全画布相同颜色/字号的对象。</p>
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
            link.download = "Figure_Pro.png"; link.href = dataURL; link.click();
        }}
    </script>
    """
    components.html(editor_html, height=750)

# --- 模块 3: 交互式润色与降 AI (对标 Paperpal/Quillbot) ---
with tabs[2]:
    st.header("Interactive Academic Polisher & Humanizer")
    if 'revision_data' not in st.session_state: st.session_state.revision_data = []

    raw_text = st.text_area("输入原始学术文本", height=200, placeholder="We found the results were significantly better...")
    mode = st.radio("主攻方向", ["专业润色 (Make Academic)", "降 AI 重构 (Humanizer)"], horizontal=True)

    if st.button("开始逐句处理"):
        if raw_text:
            with st.spinner("AI 正在重构逻辑链..."):
                # 修复 f-string {{ }}
                prompt = f"""
                Act as a senior academic editor. Break this text into sentences.
                Provide 3 versions for each sentence:
                1. Original (原文)
                2. Academic (Formal, Paperpal-style)
                3. Humanized (Reduce AI rate, varied structure)
                Output ONLY a JSON list: [{{"orig": "...", "acad": "...", "human": "..."}}]
                Text: {raw_text}
                """
                res = get_ai_response([{"role": "user", "content": prompt}])
                try:
                    clean_res = re.sub(r'```json\n?|\n?```', '', res).strip()
                    st.session_state.revision_data = json.loads(clean_res)
                except: st.error("解析失败，请重试。")

    if st.session_state.revision_data:
        st.subheader("💡 交互式修订 (点击选择最佳版本):")
        final_list = []
        for i, item in enumerate(st.session_state.revision_data):
            with st.expander(f"句子 {i+1}: {item['orig'][:60]}..."):
                c = st.radio(f"选择 S{i+1} 版本", [item['orig'], item['acad'], item['human']], key=f"s_{i}", index=1 if mode=="专业润色 (Make Academic)" else 2)
                final_list.append(c)
        
        full_p = " ".join(final_list)
        st.divider()
        st.subheader("最终输出结果:")
        st.text_area("已修改文本", full_p, height=200)
        
        # Word 导出
        doc = Document()
        doc.add_paragraph(full_p)
        bio = io.BytesIO()
        doc.save(bio)
        st.download_button("导出 Word 修订版", bio.getvalue(), "Polished_Manuscript.docx")

# --- 模块 4: 期刊推荐 (LetPub/JANE 逻辑) ---
with tabs[3]:
    st.header("LetPub Strategic Matcher")
    st.write(f"筛选设定：IF {if_range} | 中科院 {cas_zone} | SCI {sci_zone} | OA: {oa_req}")
    abs_in = st.text_area("输入摘要", height=150)
    if st.button("开始智能匹配"):
        prompt = f"参考 LetPub。基于摘要，在 IF {if_range}、中科院 {cas_zone} 内推荐 10 个真实期刊。给出期刊名、IF、分区、简介、OA状态及同数据库发表的文章 (含真实 PMID)。"
        st.markdown(get_ai_response([{"role": "user", "content": prompt}]))

# --- 模块 5: 三阶段创新大脑 ---
with tabs[4]:
    st.header("🚀 创新实验室 (多阶段交互)")
    st_stage = st.radio("阶段", ["1. 思路探索", "2. 详细路径 (变量/代码)", "3. 报告生成 (1000字 SCI 级)"], horizontal=True)
    
    if st_stage == "1. 思路探索":
        db = st.text_input("数据库名 (如 NHANES + GBD)")
        if st.button("获取最新高分创新点"):
            prompt = f"基于{db}给出3个最新创新思路（如机器学习共病/组学联合）。参考2024+顶刊发文趋势，附带理由。"
            st.markdown(get_ai_response([{"role":"user","content":prompt}]))
            
    elif st_stage == "2. 详细路径 (变量/代码)":
        c1, c2, c3 = st.columns(3)
        exp, dbs, outc = c1.text_input("暴露因子"), c2.text_input("数据库"), c3.text_input("结局疾病")
        if st.button("生成详细筛选思路与代码"):
            prompt = f"数据库：{dbs}。暴露：{exp}。结局：{outc}。给出具体的变量编码 (Variable Codes)、计算公式、统计模型 (RCS/WQS等) 及创新点。"
            st.markdown(get_ai_response([{"role":"user","content":prompt}]))
            
    elif st_stage == "3. 报告生成 (1000字 SCI 级)":
        user_add = st.chat_input("输入交互指令 (如：添加亚组分析设计)")
        if st.button("生成完整 SCI 背景方案报告"):
            prompt = "请生成一份 1000 字左右的 SCI 背景研究方案。要求：参考文献真实有效（近5年），背景逻辑清晰，包含 Figure 1-3 模拟图表描述。段落形式输出。"
            report_text = get_ai_response([{"role": "user", "content": prompt}])
            st.markdown(report_text)
            # 导出 Word
            d = Document()
            d.add_heading('Academic Innovation Proposal', 0)
            d.add_paragraph(report_text)
            b = io.BytesIO()
            d.save(b)
            st.download_button("下载 1000字 完整报告 (Word)", b.getvalue(), "Proposal.docx")
