import streamlit as st
import requests

# ---------------- PAGE CONFIG ---------------- #
st.set_page_config(page_title="Clinical AI", layout="wide")

# ---------------- TITLE & STYLE ---------------- #
st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Poppins', sans-serif; background-color: #0b1120; color: white; }
.main-box { background: linear-gradient(145deg, #0f172a, #020617); padding: 30px; border-radius: 20px; border: 1px solid rgba(0, 255, 255, 0.2); text-align: center; margin-bottom: 20px; }
.title { font-family: 'Orbitron', sans-serif; font-size: 48px; font-weight: 600; background: linear-gradient(90deg, #00c6ff, #0072ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.subtitle { font-size: 20px; color: #cbd5f5; }
section[data-testid="stFileUploader"] { border: 2px dashed #00c6ff; border-radius: 12px; padding: 10px; background-color: #020617; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-box"><div class="title">Clinical Intelligence Engine</div></div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Smart AI assistant for analyzing patient reports</div>', unsafe_allow_html=True)
st.caption("Built for ET Gen AI Hackathon • Clinical Decision Support System")
st.markdown("---")

# ---------------- FILE UPLOAD ---------------- #
uploaded_file = st.file_uploader("📂 Upload Patient Report (PDF)", type=["pdf"])

def call_backend(file):
    url = "http://127.0.0.1:8000/process"
    files = {"file": (file.name, file, "application/pdf")}
    try:
        response = requests.post(url, files=files)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Backend error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
        return None

# ---------------- MAIN LOGIC ---------------- #
if uploaded_file is not None:
    st.success("✅ File uploaded successfully!")

    with st.spinner("🤖 AI analyzing report..."):
        data = call_backend(uploaded_file)

    if data is None:
        st.warning("❌ Backend failed to process report. Using dummy data for demo.")
        data = {
            "summary": "Dummy patient summary",
            "risk": "Low",
            "insights": ["Bilirubin Total: Normal", "ALT: Normal"],
            "extracted": {"Bilirubin Total": "0.5", "ALT": "22.3"},
            "explanation": "Disease prediction: Healthy"
        }

    st.success("🎉 Analysis complete!")
    st.markdown("---")

    # ---------------- DISPLAY COLUMNS ---------------- #
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 📄 Status")
        st.success("Processed")

    with col2:
        st.markdown("### ⚠️ Risk Level")
        if data["risk"] == "High":
            st.error("🔴 HIGH RISK")
        elif data["risk"] == "Medium":
            st.warning("🟡 MEDIUM RISK")
        else:
            st.success("🟢 LOW RISK")

    with col3:
        st.markdown("### 🧪 Parameters")
        st.info(f"{len(data['extracted'])} Checked")

    st.markdown("---")
    st.subheader("Patient Summary")
    st.write(data["summary"])

    st.subheader("📊 Key Insights")
    for insight in data["insights"]:
        st.write(f"✔ {insight}")

    st.subheader("📄 Extracted Report Values")
    for key, value in data["extracted"].items():
        if key.lower() in ["glucose", "cholesterol"]:
            st.error(f"🔴 {key}: {value}")
        elif key.lower() == "hemoglobin":
            st.warning(f"🟡 {key}: {value}")
        else:
            st.success(f"🟢 {key}: {value}")

    st.markdown("---")
    st.subheader("💡 Why this Risk?")
    st.info(data["explanation"])

    st.markdown("---")
    with st.expander("🔍 View Full Technical Data"):
        st.json(data)

else:
    st.info("👆 Upload a patient report to begin analysis")

# ---------------- FOOTER ---------------- #
st.markdown("---")
st.caption("🚀 Designed to reduce doctor workload and improve patient safety")
st.info("💡 This demo uses simulated AI results. Backend integration will provide real-time analysis.")