import streamlit as st
import requests

# Page config
st.set_page_config(page_title="Clinical AI", layout="wide")

# Title
st.title("🧠 Clinical Intelligence Engine")
st.markdown("Upload a patient report and get AI-powered insights")

st.divider()

# Upload section
uploaded_file = st.file_uploader("📂 Upload Patient Report (PDF)", type=["pdf"])

if uploaded_file is not None:

    st.success("✅ File uploaded successfully!")

    # Processing
    with st.spinner("Analyzing report..."):

        try:
            response = requests.post(
                "http://127.0.0.1:8000/process",
                files={
                    "file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")
                },
                timeout=30
            )

            # Success
            if response.status_code == 200:
                data = response.json()

                st.success("🎉 Analysis Completed!")

                st.divider()

                # -------- DISPLAY SECTION -------- #

                # If structured response exists
                if isinstance(data, dict):

                    # Summary
                    st.subheader("🧠 Summary")
                    st.write(data.get("summary", "No summary available"))

                    # Risk Level
                    st.subheader("⚠️ Risk Level")

                    risk = data.get("risk", "Unknown")

                    if risk.lower() == "high":
                        st.error(f"High Risk ⚠️")
                    elif risk.lower() == "medium":
                        st.warning(f"Medium Risk ⚠️")
                    elif risk.lower() == "low":
                        st.success(f"Low Risk ✅")
                    else:
                        st.info(risk)

                    # Insights
                    st.subheader("📊 Key Insights")
                    st.write(data.get("insights", "No insights available"))

                    # Raw data (optional)
                    with st.expander("🔍 View Full Data"):
                        st.json(data)

                else:
                    st.json(data)

            # Backend error
            else:
                st.error("❌ Backend returned an error")
                st.write(response.text)

        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to backend")
            st.info("Make sure backend is running on port 8000")

        except Exception as e:
            st.error("❌ Something went wrong")
            st.write(e)

else:
    st.info("👆 Upload a PDF file to begin")