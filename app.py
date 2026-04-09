import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import openai
import base64

# --- 页面全局配置 ---
st.set_page_config(page_title="Academic Intelligence Suite Pro Max", layout="wide")

# --- 侧边栏：AI引擎与期刊硬性指标设置 ---
with st.sidebar:
    st.title("⚙️ AI & Publishing Config")
    provider = st.selectbox("Select Engine", ["Zhipu AI (GLM-4v)", "DeepSeek", "OpenAI"])
    api_key = st.text_input("Master API Key", type="password")
    
    st.divider()
    st.subheader("📊 Journal Strategy Filters")
    min_if, max_if = st.slider("Target Impact Factor", 0.0, 50.0, (5.0, 7.0))
    cas_zone = st.selectbox("CAS Zone", ["Zone 1", "Zone 2", "Zone 3"], index=1)
    
    base_url = "https://open.bigmodel.cn/api/paas/v4/" if provider == "Zhipu AI (GLM-4v)" else "https://api.openai.com/v1"
    model_name = "glm-4v" if provider == "Zhipu AI (GLM-4v)" else "gpt-4o"

# --- AI 调用逻辑 ---
def get_ai_response(messages):
    if not api_key: return "⚠️ Please enter API Key in sidebar."
    try:
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(model=model_name, messages=messages, temperature=0.3)
        return response.choices[0].message.content
    except Exception as e: return f"❌ Error: {str(e)}"

st.title("🔬 Elite Academic Production Platform")
tabs = st.tabs(["🔍 Figure Analysis", "🎨 Pro AI Illustrator", "✍️ 3-Tier Polisher", "📊 Journal Finder", "💡 Multi-DB Innovation"])

# --- 模块 1: 视觉结果描述 ---
with tabs[0]:
    st.header("Literature-Style Visual Interpretation")
    up_img = st.file_uploader("Upload Figure", type=["png", "jpg", "jpeg"])
    if st.button("Deep Interpret"):
        if up_img:
            b64 = base64.b64encode(up_img.read()).decode('utf-8')
            msg = [{"role":"user","content":[{"type":"text","text":"Analyze this image like a Nature editor. Provide: 1. Results Description (Academic style) 2. Key findings with potential p-values 3. Comparison with published literature styles. Output in CN & EN."},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}]
            st.markdown(get_ai_response(msg))

# --- 模块 2: Adobe Illustrator 风格 PDF 编辑器 ---
with tabs[1]:
    st.header("Multi-PDF Pro Illustrator")
    st.caption("Instructions: 1. Insert multiple PDFs. 2. Drag & Scale. 3. Modify Properties. 4. High-Res Export.")
    
    editor_html = f"""
    <div style="display: flex; gap: 10px; background: #2c2c2c; padding: 15px; color: white; border-radius: 8px;">
        <div id="canvas-area">
            <div id="tools" style="margin-bottom:10px; display:flex; gap:8px;">
                <input type="file" id="pdfLoader" accept="application/pdf" multiple style="display:none">
                <button onclick="document.getElementById('pdfLoader').click()">📁 Insert PDF(s)</button>
                <button onclick="addText()">T Text</button>
                <button onclick="canvas.bringToFront(canvas.getActiveObject())">🔼 Front</button>
                <button onclick="canvas.remove(canvas.getActiveObject())" style="background:#d9534f">🗑️ Delete</button>
                <button onclick="exportFile()" style="background:#28a745">🚀 EXPORT</button>
            </div>
            <canvas id="c" width="880" height="600" style="border:1px solid #000; background:white;"></canvas>
        </div>
        <div id="prop-panel" style="width:200px; font-size:12px; background:#383838; padding:10px; border-radius:5px;">
            <h4 style="margin-top:0">Properties</h4>
            X: <input type="number" id="oX" style="width:60px" oninput="upObj()"><br>
            Y: <input type="number" id="oY" style="width:60px" oninput="upObj()"><br>
            Scale: <input type="number" id="oS" step="0.1" style="width:60px" oninput="upObj()"><br>
            Opacity: <input type="range" id="oA" min="0" max="1" step="0.1" oninput="upObj()"><br>
            Color: <input type="color" id="oC" onchange="upObj()"><br>
            Font Size: <input type="number" id="oF" value="24" style="width:60px" oninput="upObj()"><br>
            <hr>
            <h4>Export Format</h4>
            <select id="exFmt" style="width:100%"><option>PDF</option><option>PNG (300DPI)</option><option>TIFF (600DPI)</option></select>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>

    <script>
        const canvas = new fabric.Canvas('c');
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';

        document.getElementById('pdfLoader').onchange = function(e) {{
            const files = e.target.files;
            for(let file of files) {{
                const reader = new FileReader();
                reader.onload = function() {{
                    const typedarray = new Uint8Array(this.result);
                    pdfjsLib.getDocument(typedarray).promise.then(pdf => {{
                        pdf.getPage(1).then(page => {{
                            const viewport = page.getViewport({{scale: 1.5}});
                            const tempCanvas = document.createElement('canvas');
                            const context = tempCanvas.getContext('2d');
                            tempCanvas.height = viewport.height;
                            tempCanvas.width = viewport.width;
                            page.render({{canvasContext: context, viewport: viewport}}).promise.then(() => {{
                                fabric.Image.fromURL(tempCanvas.toDataURL(), img => {{
                                    img.set({{left: 50, top: 50}});
                                    canvas.add(img);
                                }});
                            }});
                        }});
                    }});
                }};
                reader.readAsArrayBuffer(file);
            }}
        }};

        function addText() {{
            const t = new fabric.IText('New Label', {{ left: 100, top: 100, fontFamily: 'Arial', fontSize: 24 }});
            canvas.add(t);
        }}

        function upObj() {{
            const obj = canvas.getActiveObject();
            if(!obj) return;
            obj.set({{
                left: parseFloat(document.getElementById('oX').value),
                top: parseFloat(document.getElementById('oY').value),
                scaleX: parseFloat(document.getElementById('oS').value),
                scaleY: parseFloat(document.getElementById('oS').value),
                opacity: parseFloat(document.getElementById('oA').value)
            }});
            if(obj.type === 'i-text') {{
                obj.set({{ fill: document.getElementById('oC').value, fontSize: parseInt(document.getElementById('oF').value) }});
            }}
            canvas.renderAll();
        }}

        function exportFile() {{
            const fmt = document.getElementById('exFmt').value;
            const dataURL = canvas.toDataURL({{ format: 'png', multiplier: 3 }});
            if(fmt === 'PDF') {{
                const {{ jsPDF }} = window.jspdf;
                const pdf = new jsPDF('l', 'px', [880, 600]);
                pdf.addImage(dataURL, 'PNG', 0, 0, 880, 600);
                pdf.save("Figure_Export.pdf");
            }} else {{
                const link = document.createElement('a');
                link.download = `Export_Image.${{fmt.toLowerCase()}}`;
                link.href = dataURL; link.click();
            }}
        }}
    </script>
    """
    components.html(editor_html, height=750)

# --- 模块 4: 深度期刊推荐 ---
with tabs[3]:
    st.header("Journal Strategic Analytics")
    st.write(f"Targeting: IF {min_if}-{max_if} | {cas_zone}")
    abs_input = st.text_area("Input Manuscript Abstract:", height=150)
    if st.button("Match Journals"):
        prompt = f"""
        Act as Elsevier Journal Finder. For abstract: {abs_input}
        Identify 5 journals strictly within:
        - Impact Factor: {min_if} to {max_if}
        - CAS Zone: {cas_zone}
        For each, include: IF, Acceptance Rate, Review Cycle, and 2 similar articles published recently.
        """
        st.markdown(get_ai_response([{"role":"user","content":prompt}]))

# --- 模块 5: 创新点查询 (多数据库支持) ---
with tabs[4]:
    st.header("Global Database Innovation Brain")
    col_db1, col_db2 = st.columns(2)
    with col_db1:
        db_name = st.text_input("Database Name:", placeholder="e.g., UK Biobank, TCGA, GBD, NHANES...")
    with col_db2:
        research_topic = st.text_input("Research Interest:", placeholder="e.g., Cancer, Mental Health, Sarcopenia")

    if st.button("Explore 3 Innovation Directions"):
        with st.spinner("Synthesizing research gaps and database structure..."):
            inn_prompt = f"""
            Database: {db_name}. Topic: {research_topic}.
            Generate 3 distinct innovative research directions for 2026.
            For each direction, provide:
            1. Title (CN/EN).
            2. Research Gap: Why this is a 2026 Nature/Lancet level hot topic.
            3. Detailed Methodology:
               - Exposure Factor (with Variable Codes if available in {db_name}).
               - Outcome Factor (with Variable Codes).
               - Mediation/Moderation logic.
               - Statistical Strategy (e.g., Cox, RCS, Machine Learning).
            4. Step-by-Step implementation for {db_name}.
            5. Real-style References (provide 3 real DOI-formatted references).
            6. Mock Figure Legend for Result Illustration.
            """
            st.markdown(get_ai_response([{"role":"user","content":inn_prompt}]))
        
