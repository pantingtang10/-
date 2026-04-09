import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import openai
import base64
import io
from docx import Document
from diff_match_patch import diff_match_patch

# --- 页面全局配置 ---
st.set_page_config(page_title="Academic Intelligence Studio Ultra", layout="wide")

# --- 侧边栏：多引擎及参数配置 ---
with st.sidebar:
    st.title("⚙️ 系统专家配置")
    engine = st.selectbox("核心引擎", ["GPT-4o (推荐)", "Gemini 1.5 Pro", "Claude 3.5 Sonnet", "智谱 GLM-4v"])
    api_key = st.text_input("API 密钥", type="password")
    
    st.divider()
    st.subheader("📚 期刊筛选预设")
    if_limit = st.slider("影响因子 (IF)", 0.0, 50.0, (5.0, 7.0))
    cas_zone = st.multiselect("中科院分区", ["一区", "二区", "三区"], default=["二区"])
    
    st.divider()
    st.subheader("🖼️ 矢量导出参数")
    dpi_val = st.selectbox("导出 DPI", [300, 600, 1200], index=0)
    export_fmt = st.selectbox("格式", ["PDF", "PNG", "TIFF"])

# --- AI 调用逻辑 ---
def get_ai_response(messages, model="gpt-4o"):
    if not api_key: return "⚠️ 请在侧边栏输入 API Key。"
    try:
        # 此处根据所选引擎动态切换 BaseURL，此处以 OpenAI 格式为例
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(model=model, messages=messages, temperature=0.3)
        return response.choices[0].message.content
    except Exception as e: return f"❌ 出错: {str(e)}"

# --- UI 导航 ---
st.title("🎓 顶级学术科研全生命周期工作站")
tabs = st.tabs(["🔍 SCI 结果描述", "🎨 Pro 画布 (AI级交互)", "✍️ 润色与降AI", "📊 期刊智选引擎", "💡 创新方案实验室"])

# --- 模块 1: SCI 结果描述 ---
with tabs[0]:
    st.header("SCI Results Interpretation")
    c1, c2 = st.columns(2)
    with c1:
        doc_up = st.file_uploader("上传手稿 (DOCX/PDF/TXT)", type=["docx", "pdf", "txt"])
        fig_up = st.file_uploader("上传图表/表格 (所有格式)", accept_multiple_files=True)
    with c2:
        out_lang = st.radio("输出语言", ["中文 (Chinese)", "英文 (English)"], horizontal=True)
        detail_mode = st.checkbox("深度详细模式 (包含图例描述)", value=True)
    
    if st.button("生成 SCI 级描述"):
        with st.spinner("AI 正在解析多模态数据..."):
            prompt = f"请作为顶刊审稿人。结合上传的手稿和图表，生成一段专业、详细的SCI Results段落。要求：1. 严谨引用数据和p值。2. 提供详细版和精简版。3. 使用{out_lang}输出。"
            st.markdown(get_ai_response([{"role": "user", "content": prompt}]))

# --- 模块 2: Pro 画布 (对标 Adobe Illustrator) ---
with tabs[1]:
    st.header("Vector-Grade Figure Illustrator")
    st.caption("核心功能：多 PDF 叠加、一键查找相同修改属性、1200 DPI 导出。")
    
    illustrator_html = f"""
    <div style="display: flex; gap: 10px; background: #222; padding: 15px; color: white; border-radius: 10px;">
        <div id="editor-main">
            <div id="toolbar" style="margin-bottom:12px; display:flex; gap:8px;">
                <input type="file" id="pdfLdr" multiple style="display:none">
                <button onclick="document.getElementById('pdfLdr').click()" style="background:#444; color:white; border:1px solid #666; padding:5px 12px; cursor:pointer;">📁 插入 PDF/图片</button>
                <button onclick="addText()" style="background:#444; color:white; border:1px solid #666; padding:5px 12px; cursor:pointer;">T 文本</button>
                <button onclick="batchModify()" style="background:#f39c12; color:white; border:none; padding:5px 12px; cursor:pointer; font-weight:bold;">✨ 查找相同并修改</button>
                <button onclick="canvas.remove(canvas.getActiveObject())" style="background:#d9534f; color:white; border:none; padding:5px 12px; cursor:pointer;">🗑️ 删除</button>
                <button onclick="exportPro()" style="background:#28a745; color:white; border:none; padding:5px 12px; cursor:pointer; font-weight:bold;">🚀 导出 {export_fmt}</button>
            </div>
            <canvas id="c" width="900" height="600" style="border:1px solid #000; background:white;"></canvas>
        </div>
        <div id="prop-panel" style="width:240px; background:#333; padding:15px; border-radius:5px; font-size:12px;">
            <h4 style="margin-top:0">属性面板 (Pro)</h4>
            <label>字体:</label>
            <select id="fFam" style="width:100%"><option>Times New Roman</option><option>Arial</option><option>Helvetica</option></select><br><br>
            <label>字号:</label><input type="number" id="fSiz" value="28" style="width:100%" oninput="updateProp()"><br><br>
            <label>颜色:</label><input type="color" id="fCol" style="width:100%" onchange="updateProp()"><br><br>
            <label>X 坐标:</label><input type="number" id="oX" style="width:100%" oninput="updateProp()"><br><br>
            <label>Y 坐标:</label><input type="number" id="oY" style="width:100%" oninput="updateProp()"><br><br>
            <label>透明度:</label><input type="range" id="oA" min="0" max="1" step="0.1" style="width:100%" oninput="updateProp()">
            <hr>
            <p>提示：点击任意对象即可修改属性。点击“查找相同并修改”将同步画布上所有相同颜色或字体的元素。</p>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>

    <script>
        const canvas = new fabric.Canvas('c');
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';

        // 核心：查找相同并批量修改
        function batchModify() {{
            const ref = canvas.getActiveObject();
            if(!ref) return alert("请先选中一个样板对象");
            const newColor = document.getElementById('fCol').value;
            const newSize = parseInt(document.getElementById('fSiz').value);
            const newFam = document.getElementById('fFam').value;

            canvas.getObjects().forEach(obj => {{
                if(obj.type === ref.type && (obj.fill === ref.fill || obj.fontSize === ref.fontSize)) {{
                    obj.set({{ fill: newColor, fontSize: newSize, fontFamily: newFam }});
                }}
            }});
            canvas.renderAll();
        }}

        // 处理 PDF/图片插入
        document.getElementById('pdfLdr').onchange = function(e) {{
            const files = e.target.files;
            for(let file of files) {{
                if(file.type === "application/pdf") {{
                    const reader = new FileReader();
                    reader.onload = function() {{
                        const typedarray = new Uint8Array(this.result);
                        pdfjsLib.getDocument(typedarray).promise.then(pdf => {{
                            pdf.getPage(1).then(page => {{
                                const viewport = page.getViewport({{scale: 2.0}});
                                const tempC = document.createElement('canvas');
                                const ctx = tempC.getContext('2d');
                                tempC.height = viewport.height; tempC.width = viewport.width;
                                page.render({{canvasContext: ctx, viewport: viewport}}).promise.then(() => {{
                                    fabric.Image.fromURL(tempC.toDataURL(), img => {{
                                        img.scale(0.5); canvas.add(img);
                                    }});
                                }});
                            }});
                        }});
                    }};
                    reader.readAsArrayBuffer(file);
                }} else {{
                    const reader = new FileReader();
                    reader.onload = f => fabric.Image.fromURL(f.target.result, img => {{ img.scale(0.2); canvas.add(img); }});
                    reader.readAsDataURL(file);
                }}
            }}
        }};

        function addText() {{
            const t = new fabric.IText('New Text', {{ left: 150, top: 150, fontFamily: 'Times New Roman', fontSize: 24 }});
            canvas.add(t);
        }}

        function updateProp() {{
            const obj = canvas.getActiveObject();
            if(!obj) return;
            obj.set({{
                left: parseFloat(document.getElementById('oX').value),
                top: parseFloat(document.getElementById('oY').value),
                opacity: parseFloat(document.getElementById('oA').value)
            }});
            if(obj.type === 'i-text') {{
                obj.set({{ 
                    fill: document.getElementById('fCol').value, 
                    fontSize: parseInt(document.getElementById('fSiz').value),
                    fontFamily: document.getElementById('fFam').value
                }});
            }}
            canvas.renderAll();
        }}

        function exportPro() {{
            const mul = {dpi_val} / 96;
            const fmt = '{export_fmt}';
            const dataURL = canvas.toDataURL({{ format: 'png', multiplier: mul }});
            if(fmt === 'PDF') {{
                const {{ jsPDF }} = window.jspdf;
                const pdf = new jsPDF('l', 'px', [canvas.width * mul, canvas.height * mul]);
                pdf.addImage(dataURL, 'PNG', 0, 0, canvas.width * mul, canvas.height * mul);
                pdf.save("Academic_Illustrator.pdf");
            }} else {{
                const link = document.createElement('a');
                link.download = `Figure.${{fmt.toLowerCase()}}`;
                link.href = dataURL; link.click();
            }}
        }}
    </script>
    """
    components.html(illustrator_html, height=750)

# --- 模块 3: 润色与降AI ---
with tabs[2]:
    st.header("Academic Humanizer & Polisher")
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        text_input = st.text_area("输入手稿段落", height=250)
    with t_col2:
        mode = st.radio("处理目标", ["专业学术润色 (不改变原意)", "降 AI 率 (Humanizing / Reduce AI Rate)"])
        if st.button("开始处理"):
            with st.spinner("执行重构逻辑..."):
                prompt = f"请作为顶刊资深编辑。目标：{mode}。要求：1. 保持内容完整和学术严谨。2. 如果是降AI，请使用非线性句式和领域特定的学术变体。对标 Brandwell AI 检测标准。"
                polished = get_ai_response([{"role": "user", "content": prompt + text_input}])
                
                # 修订显示
                dmp = diff_match_patch()
                diffs = dmp.diff_main(text_input, polished)
                dmp.diff_cleanupEfficiency(diffs)
                
                st.subheader("修订预览 (接受/拒绝):")
                html_res = ""
                for tag, data in diffs:
                    if tag == 0: html_res += data
                    elif tag == 1: html_res += f'<span style="color:green;background:#e6ffed">{data}</span>'
                    elif tag == -1: html_res += f'<span style="color:red;text-decoration:line-through;background:#ffeef0">{data}</span>'
                st.markdown(html_res, unsafe_allow_html=True)
                
                st.download_button("导出为 Word", "Polished text...", file_name="Revised.docx")

# --- 模块 4: 期刊智选引擎 ---
with tabs[3]:
    st.header("Elite Journal Strategic Matcher")
    abs_input = st.text_area("输入摘要内容:", height=150)
    if st.button("匹配顶刊数据库"):
        prompt = f"参考 Elsevier, Jane 和 LetPub。基于摘要推荐 10 个 IF 在 {if_limit} 之间且为中科院 {cas_zone} 的真实期刊。要求包含：期刊名、IF、分区、简介、以及同数据库(如NHANES/UKB)发表过的相似文章。"
        st.markdown(get_ai_response([{"role": "user", "content": prompt}]))

# --- 模块 5: 创新方案实验室 (三阶段) ---
with tabs[4]:
    st.header("🚀 交互式多数据库创新大脑")
    
    stage = st.radio("当前流程", ["阶段 1: 发文情况 & 创新思路探索", "阶段 2: 实施路径 & 变量确定", "阶段 3: 方案报告生成 (Word)"])
    
    if stage == "阶段 1: 发文情况 & 创新思路探索":
        db_name = st.text_input("数据库 (不限, 如: NHANES+GBD):")
        if st.button("分析最新发文趋势与思路"):
            prompt = f"基于数据库 {db_name}，分析 2024-2025 最新高分文章，给出三个创新思路。例如：机器学习预测、共病轨迹联合分析等。给出参考文章和理由。"
            st.markdown(get_ai_response([{"role": "user", "content": prompt}]))
            
    elif stage == "阶段 2: 实施路径 & 变量确定":
        c1, c2, c3 = st.columns(3)
        expo = c1.text_input("拟定暴露 (Exposure)")
        db_sel = c2.text_input("选定数据库")
        outc = c3.text_input("目标结局 (Outcome)")
        if st.button("生成详细筛选思路与编码"):
            prompt = f"数据库：{db_sel}。探究 {expo} 与 {outc}。请给出具体计算方法、Variable Codes (如 NHANES 的特定代码)、创新点分析及思路图说明。"
            st.markdown(get_ai_response([{"role": "user", "content": prompt}]))
            
    elif stage == "阶段 3: 方案报告生成 (Word)":
        st.info("交互式对话：在此输入额外分析点以完善报告。")
        user_inst = st.chat_input("例如：添加亚组分析或敏感性分析逻辑...")
        if st.button("生成 1000字 SCI 背景方案报告"):
            prompt = "生成完整的 SCI 背景方案报告。要求：背景 1000 字，真实有效参考文献(近5年)，详细方法，例图描述(含图注)。"
            report_text = get_ai_response([{"role": "user", "content": prompt}])
            st.markdown(report_text)
            # Word 导出逻辑
            doc = Document()
            doc.add_heading('Research Innovation Report', 0)
            doc.add_paragraph(report_text)
            bio = io.BytesIO()
            doc.save(bio)
            st.download_button("下载完整报告 (.docx)", bio.getvalue(), "Proposal.docx")
