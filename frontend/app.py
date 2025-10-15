import streamlit as st
import requests

API_BASE = "http://localhost:8000/pdf"

# === Page Config ===
st.set_page_config(page_title="PDF QA Assistant", layout="wide")

# === Initialize Upload Toggle ===
if "show_upload" not in st.session_state:
    st.session_state.show_upload = False

# === Inject StarJedi Special Edition Font and Banner ===
def inject_star_wars_banner():
    st.markdown("""
        <link href="https://fonts.cdnfonts.com/css/starjedi-special-edition" rel="stylesheet">
        <style>
        .jedi-banner {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 20px;
            margin-top: 30px;
        }
        .star-wars-heading {
            font-family: 'StarJedi Special Edition', sans-serif;
            font-size: 60px;
            color: #ffe81f;
            background: none;
            padding: 0;
            margin: 0;
            text-shadow: none;
        }
        .vader-img {
            width: 80px;
            height: auto;
            filter: none;
        }
        </style>
        <div class='jedi-banner'>
            <div class='star-wars-heading'>PDF wars</div>
            <img class='vader-img' src='https://pngimg.com/uploads/darth_vader/darth_vader_PNG14.png' alt='Darth Vader'>
        </div>
    """, unsafe_allow_html=True)

inject_star_wars_banner()

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
            background-color: #00ffe5;
            color: black;
            font-weight: bold;
            border-radius: 8px;
            box-shadow: 0 0 10px #00ffe5;
            transition: 0.3s ease;
        }}
        .stButton > button:hover {{
            background-color: black;
            color: #00ffe5;
            box-shadow: 0 0 20px #00ffe5;
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
    if st.button("Upload your PDFs here, Padawan!"):
        st.session_state.show_upload = not st.session_state.show_upload

    if st.session_state.show_upload:
        uploaded_files = st.file_uploader("Choose up to 2 PDFs", type=["pdf"], accept_multiple_files=True)

        if uploaded_files:
            if len(uploaded_files) > 2:
                st.warning("Please upload only up to 2 PDFs.")
            else:
                if st.button("Upload PDFs", key="upload_button"):
                    files = [("files", (f.name, f, "application/pdf")) for f in uploaded_files]
                    try:
                        res = requests.post(f"{API_BASE}/upload", files=files)
                        if res.ok:
                            st.success("PDFs uploaded and indexed successfully!")
                        else:
                            st.error(res.json().get("detail", "Upload failed."))
                    except Exception as e:
                        st.error(f"Upload failed: {e}")