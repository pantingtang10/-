import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import openai
import base64
import io
import json
from docx import Document
from diff_match_patch import diff_match_patch

# --- 页面全局配置 ---
st.set_page_config(page_title="Academic Intelligence Studio Ultra", layout="wide", initial_sidebar_state="expanded")

# --- 侧边栏：全引擎配置 ---
with st.sidebar:
    st.title("⚙️ 全球 AI 引擎中心")
    engine_choice = st.selectbox("核心引擎 (需对应 Key)", [
        "Google Gemini Pro",
        "智谱 GLM-4v (推荐)",
        "字节豆包 (Doubao)",
        "Kimi (Moonshot)",
        "DeepSeek V3",
        "OpenAI GPT-4o"
    ])
    api_key = st.text_input("输入 API 密钥 (Key)", type="password")
    
    # 特殊处理：豆包需要 Endpoint ID
    ep_id = ""
    if engine_choice == "字节豆包 (Doubao)":
        ep_id = st.text_input("豆包 Endpoint ID (必填)", type="default")

    st.divider()
    st.subheader("📚 期刊 LetPub 筛选器")
    if_range = st.slider("影响因子", 0.0, 50.0, (5.0, 7.0))
    cas_zone = st.multiselect("分区", ["Zone 1", "Zone 2", "Zone 3"], default=["Zone 2"])
    
    st.divider()
    st.subheader("🖼️ Illustrator 导出")
    dpi_val = st.selectbox("导出精度 (DPI)", [300, 600, 1200], index=0)

# --- 核心 AI 调用函数 (全供应商自动路由) ---
def get_ai_response(messages, custom_model=None):
    if not api_key: return "ERROR: Missing API Key"
    
    config = {
        "Google Gemini Pro": {"url": "https://generativelanguage.googleapis.com/v1beta/openai/", "model": "gemini-1.5-pro"},
        "智谱 GLM-4v (推荐)": {"url": "https://open.bigmodel.cn/api/paas/v4/", "model": "glm-4v"},
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
tabs = st.tabs(["🔍 SCI 结果描述", "🎨 Pro 画布 (Illustrator)", "✍️ 交互式润色/降AI", "📊 期刊匹配", "💡 创新大脑实验室"])

# --- 模块 1: SCI 结果描述 ---
with tabs[0]:
    st.header("SCI Results & Figure Analysis")
    c1, c2 = st.columns(2)
    with c1:
        ms_file = st.file_uploader("上传手稿", type=["docx", "pdf", "txt"])
        figs_up = st.file_uploader("上传关键图表", accept_multiple_files=True)
    with c2:
        out_lang = st.radio("生成语言", ["中文", "英文"], horizontal=True)
        if st.button("开始解析描述"):
            with st.spinner("AI 正在比对手稿与图表..."):
                prompt = [{"role":"user","content":f"请作为顶刊审稿人。结合上传的内容，生成符合SCI标准的结果描述。包含详细数据版和精简版。使用{out_lang}。"}]
                st.markdown(get_ai_response(prompt))

# --- 模块 2: Pro 画布 (对标 Adobe Illustrator) ---
with tabs[1]:
    st.header("Vector Figure Illustrator Pro")
    st.caption("支持 PDF 插入、层级管理、查找相同颜色/字号并批量修改。")
    
    editor_html = f"""
    <div style="display:flex; gap:10px; background:#1e1e1e; padding:15px; border-radius:10px; color:white;">
        <div id="canv-main">
            <div style="margin-bottom:10px; display:flex; gap:8px;">
                <input type="file" id="pdfAdd" multiple style="display:none">
                <button onclick="document.getElementById('pdfAdd').click()" style="background:#444; color:white; border:none; padding:8px 12px; cursor:pointer;">📁 插入 PDF/图片</button>
                <button onclick="addText()" style="background:#444; color:white; border:none; padding:8px 12px; cursor:pointer;">T 文本</button>
                <button onclick="batchModify()" style="background:#f39c12; color:white; border:none; padding:8px 12px; cursor:pointer; font-weight:bold;">✨ 查找相同修改</button>
                <button onclick="exportPro()" style="background:#28a745; color:white; border:none; padding:8px 12px; cursor:pointer;">🚀 导出 {dpi_val}DPI</button>
            </div>
            <canvas id="c" width="900" height="600" style="border:1px solid #000; background:white;"></canvas>
        </div>
        <div style="width:220px; background:#2d2d2d; padding:15px; font-size:12px;">
            <h4>属性 (Properties)</h4>
            字体: <select id="fFam" style="width:100%"><option>Times New Roman</option><option>Arial</option></select><br><br>
            字号: <input type="number" id="fSiz" value="28" style="width:100%"><br><br>
            颜色: <input type="color" id="fCol" style="width:100%"><br><br>
            <hr>
            <p>说明：PDF 插入后点击元素即可移动。使用批量修改同步全画布标签。</p>
        </div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js"></script>
    <script>
        const canvas = new fabric.Canvas('c');
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';

        function batchModify() {{
            const ref = canvas.getActiveObject();
            if(!ref) return;
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

        function addText() {{ canvas.add(new fabric.IText('Text Label', {{ left: 150, top: 150, fontFamily: 'Times New Roman', fontSize: 24 }})); }}
        function exportPro() {{
            const mul = {dpi_val} / 96;
            const dataURL = canvas.toDataURL({{ format: 'png', multiplier: mul }});
            const link = document.createElement('a');
            link.download = "Academic_Figure.png"; link.href = dataURL; link.click();
        }}
    </script>
    """
    components.html(editor_html, height=750)

# --- 模块 3: 交互式润色与降 AI (Quillbot/Paperpal 风格) ---
with tabs[2]:
    st.header("Interactive Academic Polisher & Humanizer")
    
    if 'polished_sentences' not in st.session_state:
        st.session_state.polished_sentences = []

    text_to_process = st.text_area("输入原始学术文本", height=200)
    mode = st.radio("模式", ["专业润色 (Make Academic)", "降 AI 重构 (Humanizer)"], horizontal=True)

    if st.button("开始润色"):
        with st.spinner("正在逐句处理..."):
            # 这里的逻辑是把整段话传给AI，让它按JSON格式返回每一句的润色建议
            prompt = f"""
            Act as a senior academic editor. For the following text, break it into sentences.
            For each sentence, provide 3 versions: 
            1. Original
            2. Academic (Formal, Paperpal-style)
            3. Fluent/Humanized (Reduce AI rate, Quillbot-style)
            Output ONLY a JSON list: [{"orig": "...", "acad": "...", "human": "..."}]
            Text: {text_to_process}
            """
            res = get_ai_response([{"role": "user", "content": prompt}])
            if "ERROR" in res:
                st.error(res)
            else:
                try:
                    # 去除可能存在的 Markdown 代码块
                    clean_res = res.replace("```json", "").replace("```", "").strip()
                    st.session_state.polished_sentences = json.loads(clean_res)
                except:
                    st.error("AI 响应格式解析失败，请重试。")

    # 渲染交互式句子列表
    if st.session_state.polished_sentences:
        st.subheader("点击句子进行替换:")
        final_output = []
        for i, item in enumerate(st.session_state.polished_sentences):
            with st.expander(f"Sentence {i+1}: {item['orig'][:50]}..."):
                choice = st.radio(f"Select version for S{i+1}", 
                                  [item['orig'], item['acad'], item['human']], 
                                  key=f"choice_{i}")
                final_output.append(choice)
        
        st.divider()
        st.subheader("最终合成文本:")
        full_text = " ".join(final_output)
        st.text_area("已修改内容", full_text, height=200)
        st.download_button("导出修订版 DOCX", "Download logic here...", file_name="Revised.docx")

# --- 模块 4: 期刊推荐 (LetPub/JANE 逻辑) ---
with tabs[3]:
    st.header("LetPub Strategic Matcher")
    abs_text = st.text_area("输入论文摘要", height=150)
    if st.button("深度匹配期刊"):
        prompt = f"基于摘要，在 IF {if_range} 和 中科院 {cas_zone} 范围内推荐 10 个真实期刊。给出期刊名、IF、分区、简介及相似数据库发表文章。"
        st.markdown(get_ai_response([{"role": "user", "content": prompt}]))

# --- 模块 5: 三段式创新大脑 (全数据库) ---
with tabs[4]:
    st.header("🚀 创新方案生成器 (全数据库联动)")
    
    stage = st.radio("阶段", ["1. 思路探索", "2. 详细路径 (变量/计算)", "3. 报告生成 (1000字 Word)"], horizontal=True)
    
    if stage == "1. 思路探索":
        db = st.text_input("拟使用数据库 (如 NHANES + GBD)")
        field = st.text_input("研究领域 (如 心血管共病)")
        if st.button("获取最新高分发文思路"):
            prompt = f"基于数据库{db}和领域{field}，给出3个最新创新思路（如机器学习预测、共病轨迹），附带近5年高分参考文章及创新性理由。"
            st.markdown(get_ai_response([{"role": "user", "content": prompt}]))
            
    elif stage == "2. 详细路径 (变量/计算)":
        c1, c2, c3 = st.columns(3)
        exp, dbs, outc = c1.text_input("暴露因子"), c2.text_input("数据库名"), c3.text_input("结局疾病")
        if st.button("生成详细筛选方案"):
            prompt = f"数据库：{dbs}。暴露：{exp}。结局：{outc}。给出变量编码、计算公式、统计模型（RCS/WQS等）及创新逻辑。"
            st.markdown(get_ai_response([{"role": "user", "content": prompt}]))
            
    elif stage == "3. 报告生成 (1000字 Word)":
        st.chat_input("输入交互指令 (如：添加亚组分析)")
        if st.button("生成 1000 字 SCI 背景完整报告"):
            prompt = "生成一份 1000 字左右的 SCI 背景研究方案。要求：参考文献真实有效（近5年），方法论详尽。结果部分描述 Figure 1 (Flow chart), Table 1, Figure 2 (RCS plot), Figure 3 (Subgroup Forest Plot)。"
            res = get_ai_response([{"role": "user", "content": prompt}])
            st.markdown(res)
            # Word 导出代码 (使用 python-docx)
            doc = Document()
            doc.add_heading('Research Innovation Report', 0)
            doc.add_paragraph(res)
            bio = io.BytesIO()
            doc.save(bio)
            st.download_button("下载完整 Word 报告", bio.getvalue(), "Proposal.docx")
