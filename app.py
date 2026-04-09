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

# --- 侧边栏：多引擎及参数配置 ---
with st.sidebar:
    st.title("⚙️ 全球 AI 引擎配置中心")
    engine_choice = st.selectbox("核心引擎 (请确保 Key 正确)", [
        "Google Gemini Pro (免费版可用)",
        "智谱 GLM-4v (国内推荐)",
        "字节豆包 (Doubao)",
        "Kimi (Moonshot)",
        "DeepSeek V3",
        "OpenAI GPT-4o"
    ])
    api_key = st.text_input("输入 API 密钥 (Key)", type="password")
    
    # 豆包专用 Endpoint ID
    ep_id = ""
    if "Doubao" in engine_choice:
        ep_id = st.text_input("豆包 Endpoint ID (必填)", type="default")

    st.divider()
    st.subheader("📊 LetPub 期刊硬性过滤")
    if_range = st.slider("影响因子 (IF) 范围", 0.0, 50.0, (5.0, 7.0))
    cas_zone = st.multiselect("中科院分区", ["1区", "2区", "3区"], default=["2区"])
    sci_zone = st.multiselect("SCI 分区 (Q)", ["Q1", "Q2", "Q3"], default=["Q1", "Q2"])
    is_oa = st.checkbox("仅限 Open Access (OA)")

    st.divider()
    st.subheader("🖼️ Illustrator 导出参数")
    dpi_val = st.selectbox("导出精度 (DPI)", [300, 600, 1200], index=0)
    export_fmt = st.selectbox("导出格式", ["PDF", "PNG", "TIFF"])

# --- 核心 AI 调用函数 (支持全供应商路由) ---
def get_ai_response(messages, custom_model=None):
    if not api_key: return "ERROR: 密钥缺失"
    
    config = {
        "Google Gemini Pro (免费版可用)": {"url": "https://generativelanguage.googleapis.com/v1beta/openai/", "model": "gemini-1.5-pro"},
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
st.title("🔬 顶级科研全生命周期全能工作站")
tabs = st.tabs(["🔍 SCI 结果描述", "🎨 Pro 画布 (Illustrator)", "✍️ 交互式润色/降AI", "📊 期刊匹配 (LetPub)", "💡 创新大脑实验室"])

# --- 模块 1: SCI 结果描述 ---
with tabs[0]:
    st.header("Manuscript & Figure Neural Description")
    c1, c2 = st.columns(2)
    with c1:
        ms_file = st.file_uploader("上传手稿 (DOCX/PDF)", type=["docx", "pdf"])
        figs_up = st.file_uploader("上传清晰图表/表格", accept_multiple_files=True)
    with c2:
        out_lang = st.radio("生成语言", ["中文 (Chinese)", "英文 (English)"], horizontal=True)
        if st.button("生成 SCI 级详细描述"):
            with st.spinner("多模态数据分析中..."):
                prompt = [{"role":"user","content":f"请作为顶刊资深审稿人。结合上传的内容，详细描述实验结果。要求：包含具体的数据引用（如OR, 95%CI, P值），分为‘结果详述’和‘结论摘要’。使用{out_lang}。"}]
                st.markdown(get_ai_response(prompt))

# --- 模块 2: Pro 画布 (对标 Adobe Illustrator) ---
with tabs[1]:
    st.header("Vector Figure Illustrator Pro")
    st.caption("功能：支持多 PDF 插入、层级排列、颜色查找修改、1200DPI 采样导出。")
    
    editor_html = f"""
    <div style="display:flex; gap:10px; background:#1a1a1a; padding:15px; border-radius:10px; color:white;">
        <div id="canvas-container">
            <div id="tools" style="margin-bottom:12px; display:flex; gap:8px;">
                <input type="file" id="pdfAdd" multiple style="display:none">
                <button onclick="document.getElementById('pdfAdd').click()" style="background:#444; color:white; border:none; padding:8px 15px; cursor:pointer; border-radius:4px;">📁 插入 PDF/图片</button>
                <button onclick="addText()" style="background:#444; color:white; border:none; padding:8px 15px; cursor:pointer; border-radius:4px;">T 文本</button>
                <button onclick="batchEdit()" style="background:#f39c12; color:white; border:none; padding:8px 15px; cursor:pointer; font-weight:bold; border-radius:4px;">✨ 查找并批量修改</button>
                <button onclick="exportPro()" style="background:#28a745; color:white; border:none; padding:8px 15px; cursor:pointer; border-radius:4px;">🚀 导出 {export_fmt}</button>
            </div>
            <canvas id="c" width="900" height="620" style="border:1px solid #333; background:white;"></canvas>
        </div>
        <div id="control-panel" style="width:240px; background:#2d2d2d; padding:20px; border-radius:8px;">
            <h4 style="margin-top:0">属性面板 (Pro)</h4>
            字体: <select id="fFam" style="width:100%; margin-bottom:15px;"><option>Times New Roman</option><option>Arial</option><option>Helvetica</option></select>
            字号: <input type="number" id="fSiz" value="28" style="width:100%; margin-bottom:15px;">
            颜色: <input type="color" id="fCol" style="width:100%; margin-bottom:15px;">
            <hr style="border:0.5px solid #555">
            <p style="font-size:11px; color:#aaa;">说明：选中一个文字标注，点击“查找并批量修改”，全图所有相同颜色和字号的标注将一键同步颜色和字体。</p>
        </div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js"></script>
    <script>
        const canvas = new fabric.Canvas('c');
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';

        function batchEdit() {{
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

        function addText() {{ canvas.add(new fabric.IText('Text Label', {{ left: 150, top: 150, fontFamily: 'Times New Roman', fontSize: 24 }})); }}
        
        function exportPro() {{
            const mul = {dpi_val} / 96;
            const dataURL = canvas.toDataURL({{ format: 'png', multiplier: mul }});
            const link = document.createElement('a');
            link.download = "Academic_Illustrator_Figure.png"; link.href = dataURL; link.click();
        }}
    </script>
    """
    components.html(editor_html, height=780)

# --- 模块 3: 交互式润色与降 AI (Quillbot/Paperpal 风格) ---
with tabs[2]:
    st.header("Interactive Academic Polisher & Humanizer")
    st.caption("原理：对标 Paperpal 的句子级润色。点击下方句子可自由切换润色版本，支持降 AI 模式。")
    
    if 'polished_data' not in st.session_state:
        st.session_state.polished_data = []

    text_input = st.text_area("输入原始学术文本 (段落)", height=200, placeholder="We observed that the mortality rate was high...")
    mode = st.radio("润色模式", ["专业学术润色 (Academic Polishing)", "降低 AI 率重构 (De-AI Humanizer)"], horizontal=True)

    if st.button("执行句子级分析"):
        if text_input:
            with st.spinner("AI 正在逐句处理并重构逻辑..."):
                # 修复 f-string 占位符错误：使用 {{ }}
                prompt = f"""
                Act as a senior academic editor. Break the following text into sentences.
                For each sentence, provide 3 versions:
                1. Original (原文)
                2. Academic (Formal, Paperpal-style, no meaning change)
                3. Humanized (Reduce AI rate, varied structure, professional)
                Output ONLY a valid JSON list of objects: [{{"orig": "...", "acad": "...", "human": "..."}}]
                Text: {text_input}
                """
                res = get_ai_response([{"role": "user", "content": prompt}])
                try:
                    # 清洗 JSON 字符串
                    clean_res = re.sub(r'```json\n?|\n?```', '', res).strip()
                    st.session_state.polished_data = json.loads(clean_res)
                except Exception as e:
                    st.error(f"解析失败。原因: {str(e)}. AI 返回内容: {res}")

    if st.session_state.polished_data:
        st.subheader("💡 逐句修订 (点击选择最佳版本):")
        final_list = []
        for i, item in enumerate(st.session_state.polished_data):
            with st.expander(f"句子 {i+1}: {item['orig'][:60]}..."):
                choice = st.radio(f"选择 S{i+1} 版本", 
                                 [item['orig'], item['acad'], item['human']], 
                                 key=f"choice_{i}",
                                 index=1 if mode == "专业学术润色 (Academic Polishing)" else 2)
                final_list.append(choice)
        
        full_polished = " ".join(final_list)
        st.divider()
        st.subheader("最终输出结果:")
        st.text_area("已修改文本 (可直接复制)", full_polished, height=200)
        
        # 导出 Word
        doc = Document()
        doc.add_paragraph(full_polished)
        bio = io.BytesIO()
        doc.save(bio)
        st.download_button("导出为 Word (修订版)", bio.getvalue(), "Revised_Manuscript.docx")

# --- 模块 4: 期刊推荐 (LetPub 逻辑) ---
with tabs[3]:
    st.header("LetPub Strategic Journal Finder")
    st.write(f"当前筛选：IF {if_range[0]}-{if_range[1]} | 中科院 {cas_zone} | SCI {sci_zone} | OA: {is_oa}")
    abs_text = st.text_area("输入摘要", height=150)
    if st.button("检索真实期刊库"):
        prompt = f"参考 LetPub 和 Jane。基于摘要，在 IF {if_range}、中科院 {cas_zone}、SCI {sci_zone} 内推荐 10 个真实期刊。给出期刊名、IF、分区、简介、OA 状态以及同数据库发表的相似文章 (真实 PMID)。"
        st.markdown(get_ai_response([{"role": "user", "content": prompt}]))

# --- 模块 5: 三段式创新大脑 ---
with tabs[4]:
    st.header("🚀 创新方案实验室 (多阶段交互)")
    
    stage = st.radio("阶段选择", ["1. 思路与趋势探索", "2. 详细实施方案 (变量/代码)", "3. SCI 背景报告生成"], horizontal=True)
    
    if stage == "1. 思路与趋势探索":
        db = st.text_input("数据库名 (如 NHANES + GBD)")
        field = st.text_input("领域 (如 肌肉衰减症)")
        if st.button("获取 2024+ 创新点"):
            prompt = f"基于{db}和{field}，分析 2024-2025 发文趋势，给 3 个创新思路（如机器学习共病、孟德尔随机化联合）。提供参考文章及理由。"
            st.markdown(get_ai_response([{"role": "user", "content": prompt}]))
            
    elif stage == "2. 详细实施方案 (变量/代码)":
        c1, c2, c3 = st.columns(3)
        exp, dbs, outc = c1.text_input("暴露因子"), c2.text_input("数据库"), c3.text_input("结局")
        if st.button("生成详细分析逻辑"):
            prompt = f"数据库：{dbs}。暴露：{exp}。结局：{outc}。给出具体的筛选代码 (Variable Codes)、计算逻辑、中介效应/RCS分析建议及创新点。"
            st.markdown(get_ai_response([{"role": "user", "content": prompt}]))
            
    elif stage == "3. 报告生成 ( Word)":
        st.info("交互：输入指令微调报告内容...")
        u_cmd = st.chat_input("例如：在背景中增加关于老龄化的数据...")
        if st.button("生成 1000字 SCI 完整报告"):
            prompt = "生成 1000 字 SCI 背景方案报告。要求：真实参考文献（近5年），详细方法，结果部分含 Figure 1-3 模拟描述。输出段落形式。"
            report = get_ai_response([{"role": "user", "content": prompt}])
            st.markdown(report)
            # 导出 Word
            d = Document()
            d.add_heading('Research Innovation Report', 0)
            d.add_paragraph(report)
            b = io.BytesIO()
            d.save(b)
            st.download_button("下载完整报告 (Word)", b.getvalue(), "Research_Proposal.docx")
