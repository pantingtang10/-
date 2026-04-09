import streamlit as st
import streamlit.components.v1 as components
import json

st.set_page_config(page_title="Academic Toolkit Pro", layout="wide")

# --- CSS 样式 ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔬 Advanced Academic Publishing Platform")

tabs = st.tabs(["📊 Data Description", "🖼️ Interactive Figure Editor", "✍️ Language Polishing", "📑 Journal Finder"])

# --- 模块 1: 数据/图片描述 ---
with tabs[0]:
    st.header("Data & Image Interpretation")
    col1, col2 = st.columns([1, 1])
    with col1:
        uploaded_data = st.file_uploader("Upload Table (CSV/XLSX) or Figure", type=["png", "jpg", "csv", "xlsx"])
        detail_level = st.select_slider("Detail Level", options=["Brief", "Standard", "Comprehensive"])
    with col2:
        if st.button("Generate Academic Description"):
            st.info("AI is analyzing the visual patterns and data trends...")
            st.subheader("English Analysis")
            st.write("""
            The experimental results demonstrate a statistically significant correlation between variables A and B (p < 0.01). 
            As illustrated in the data, the peak intensity reaches its maximum at the 45-minute mark, followed by a gradual 
            plateau phase, suggesting a saturated kinetic response in the observed environment.
            """)
            st.subheader("中文分析")
            st.write("实验结果表明变量A与B之间存在显著的正相关性（p < 0.01）。如图所示，峰值强度在45分钟时达到最大。")

# --- 模块 2: 核心排版编辑器 (Fabric.js 实现) ---
with tabs[1]:
    st.header("Interactive Figure Stitching & PDF Layout")
    st.write("Drag images to move, use handles to scale. Add text for figure labels (e.g., 'Fig 1A').")
    
    # 定义前端 HTML/JS 画布
    canvas_html = """
    <div id="toolbar" style="margin-bottom: 10px; display: flex; gap: 10px; align-items: center; background: #eee; padding: 10px; border-radius: 5px;">
        <input type="file" id="imgLoader" accept="image/*" style="width: 200px;">
        <button onclick="addText()" style="padding: 5px 10px;">Add Text</button>
        <input type="color" id="textColor" value="#000000">
        <input type="number" id="fontSize" value="20" style="width: 50px;">
        <button onclick="downloadPDF()" style="padding: 5px 10px; background: #28a745; color: white; border: none; border-radius: 3px;">Export PDF</button>
    </div>
    <canvas id="c" width="800" height="600" style="border:1px solid #ccc; background: #fff;"></canvas>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>

    <script>
        const canvas = new fabric.Canvas('c');
        
        // 1. 上传并添加图片 (可移动/缩放)
        document.getElementById('imgLoader').onchange = function(e) {
            var reader = new FileReader();
            reader.onload = function(event) {
                var imgObj = new Image();
                imgObj.src = event.target.result;
                imgObj.onload = function() {
                    var image = new fabric.Image(imgObj);
                    image.set({ left: 100, top: 100 }).scale(0.3);
                    canvas.add(image);
                }
            }
            reader.readAsDataURL(e.target.files[0]);
        };

        // 2. 添加可编辑文本
        function addText() {
            const color = document.getElementById('textColor').value;
            const size = document.getElementById('fontSize').value;
            const text = new fabric.IText('Double click to edit', {
                left: 150,
                top: 150,
                fontFamily: 'Times New Roman',
                fontSize: parseInt(size),
                fill: color
            });
            canvas.add(text);
        }

        // 3. 导出PDF
        function downloadPDF() {
            const dataURL = canvas.toDataURL({ format: 'png', quality: 1.0 });
            const { jsPDF } = window.jspdf;
            const pdf = new jsPDF('l', 'px', [800, 600]);
            pdf.addImage(dataURL, 'PNG', 0, 0, 800, 600);
            pdf.save("academic_figure_layout.pdf");
        }
    </script>
    """
    
    components.html(canvas_html, height=750)

# --- 模块 3: 语言润色 ---
with tabs[2]:
    st.header("Academic Language Polishing")
    input_text = st.text_area("Paste your manuscript paragraph here:", height=200, placeholder="e.g., We found that the results were very good...")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        tone = st.selectbox("Target Tone", ["Nature/Science Style", "Technical/Engineering", "Social Science"])
    with col_p2:
        if st.button("Polish Paragraph"):
            st.subheader("Polished Version (English)")
            st.success("Our findings demonstrate significant efficacy, outperforming existing benchmarks in...")
            st.caption("Changes: Replaced 'very good' with 'significant efficacy'; Enhanced sentence structure.")

# --- 模块 4: 期刊推荐 ---
with tabs[3]:
    st.header("Journal Recommendation Engine")
    abstract = st.text_area("Input Manuscript Abstract:", height=150)
    if st.button("Match Journals"):
        results = [
            {"Journal": "Journal of Advanced Research", "Match": "94%", "IF": "12.8", "OA": "Yes"},
            {"Journal": "Nature Methods", "Match": "89%", "IF": "48.0", "OA": "No"},
            {"Journal": "IEEE Access", "Match": "82%", "IF": "3.9", "OA": "Yes"},
        ]
        st.table(results)
