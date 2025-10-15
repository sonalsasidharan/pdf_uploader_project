import streamlit as st
import requests

API_BASE = "http://localhost:8000/pdf"

# === Page Config ===
st.set_page_config(page_title="PDF QA Assistant", layout="wide")

# === Inject Jedi Font ===
def inject_jedi_font():
    st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600&display=swap" rel="stylesheet">
        <style>
        .jedi-heading {
            font-family: 'Orbitron', sans-serif;
            font-size: 48px;
            text-align: center;
            color: #00ffe5;
            letter-spacing: 2px;
            text-shadow: 0 0 10px #00ffe5;
            margin-top: 30px;
        }
        </style>
    """, unsafe_allow_html=True)

inject_jedi_font()

# === Custom Background ===
def set_background(image_url):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("{image_url}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .block-container {{
            background-color: rgba(0, 0, 0, 0.6);
            padding: 2rem;
            border-radius: 10px;
        }}
        h1, h2, h3, h4, h5, h6, p, div {{
            color: white !important;
        }}
        .stTextInput > div > input {{
            background-color: #1e1e1e;
            color: white;
        }}
        .stButton > button {{
            background-color: #4B8BBE;
            color: white;
            border-radius: 5px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background("https://images.wallpapersden.com/image/download/darth-vader-4k_bGpnbGeUmZqaraWkpJRobWllrWdma2U.jpg")

# === Layout Columns ===
left, center, right = st.columns([1, 2, 1])

# === Center Column: QA Input and Upload ===
with center:
    st.markdown("<div class='jedi-heading'>PDF JEDI</div>", unsafe_allow_html=True)
    question = st.text_input("Enter your question")

    if question and st.button("Get Answer"):
        try:
            res = requests.get(f"{API_BASE}/ask", params={"q": question})
            if res.ok:
                data = res.json()
                st.markdown("#### Answer")
                st.markdown(data["answer"])
                if data.get("context_preview"):
                    with st.expander("Context Preview"):
                        for i, chunk in enumerate(data["context_preview"], 1):
                            st.markdown(f"**Chunk {i}:**\n{chunk}")
            else:
                st.error("Failed to get answer. Try again.")
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("---")

    # === Toggle PDF Upload Section ===
    show_upload = st.button("Upload your PDFs here Padawan!")

    if show_upload:
        uploaded_files = st.file_uploader("Choose up to 2 PDFs", type=["pdf"], accept_multiple_files=True)

        if uploaded_files:
            if len(uploaded_files) > 2:
                st.warning("Please upload only up to 2 PDFs.")
            else:
                if st.button("Upload PDFs"):
                    files = [("files", (f.name, f, "application/pdf")) for f in uploaded_files]
                    try:
                        res = requests.post(f"{API_BASE}/upload", files=files)
                        if res.ok:
                            st.success("PDFs uploaded and indexed successfully!")
                        else:
                            st.error(res.json().get("detail", "Upload failed."))
                    except Exception as e:
                        st.error(f"Upload failed: {e}")

# === Right Column: View-only PDF List ===
#with right:
#    try:
#        res = requests.get(f"{API_BASE}/pdf/list")
#        if res.ok:
#            pdfs = res.json().get("pdfs", [])
#            if pdfs:
#                st.markdown("### Uploaded PDFs")
#                with st.expander("View All PDFs"):
#                    for pdf in pdfs:
#                        st.markdown(f"- {pdf}")
#        else:
#            st.warning("Could not fetch PDF list.")
#    except Exception as e:
#        st.warning(f"Error fetching PDF list: {e}")