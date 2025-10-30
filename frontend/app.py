import streamlit as st
import requests

API_BASE = "http://localhost:8000/pdf"


st.set_page_config(page_title="PDF QA Assistant", layout="wide")

if "show_upload" not in st.session_state:
    st.session_state.show_upload = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "project_name" not in st.session_state:
    st.session_state.project_name = ""
if "upload_success_message" not in st.session_state:
    st.session_state.upload_success_message = ""
if "question_text" not in st.session_state:
    st.session_state.question_text = ""
if "is_uploading" not in st.session_state:
    st.session_state.is_uploading = False


def inject_harry_potter_banner():
    st.markdown("""
        <!-- Harry P font, a classic Harry Potter style font -->
        <link href="https://fonts.cdnfonts.com/css/harry-p" rel="stylesheet">
        <style>
        .hp-banner {
            display: flex;
            justify-content: center;
            align-items: flex-end;
            gap: 20px;
            margin-top: 60px;
        }
        .hp-heading {
            font-family: 'Harry P', fantasy, serif !important;
            font-size: 100px;
            color: #ffd700;
            letter-spacing: 2px;
            margin: 0;
            padding: 0;
            background: none;
            text-shadow: 2px 2px 15px #5f3b11;
            line-height: 1.1;
            display: flex;
            align-items: flex-end;
        }
        .hp-img {
            width: 100px;
            height: auto;
            margin-bottom: 4px;
        }
        .hp-scholar {
            font-family: 'Harry P', fantasy, serif !important;
            font-size: 36px;
            color: #ffd700;
            letter-spacing: 2px;
            margin-bottom: 16px;
            margin-top: 32px;
            text-align: left;
            text-shadow: 1px 1px 10px #412f09;
        }
        </style>
        <div class='hp-banner'>
            <div class='hp-heading'>WizVault</div>
            <img class='hp-img' src='https://png.pngtree.com/png-vector/20240724/ourmid/pngtree-harry-potter-a-stack-of-books-png-image_12786717.png' alt='Harry Potter'>
        </div>
    """, unsafe_allow_html=True)

inject_harry_potter_banner()

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
            background-color: transparent;
            color: white;
            font-weight: bold;
            border: 2px solid white;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
            transition: 0.3s ease;
        }}
        .stButton > button:hover {{
            background-color: rgba(255, 255, 255, 0.1);
            color: white;
            box-shadow: 0 0 8px rgba(255, 255, 255, 0.4);
            border-color: white;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background("https://i.pinimg.com/1200x/45/25/cf/4525cfc2dc240372aba97f50528c9396.jpg")

def show_upload_spinner(show):
    if show:
        st.markdown(
            f"""
            <style>
            .overlay {{
                position: fixed;
                top: 0; left: 0;
                width: 100vw; height: 100vh;
                background: rgba(10, 10, 10, 0.6);
                display: flex; justify-content: center; align-items: center;
                z-index: 9999;
            }}
            .rotating-img {{
                width: 220px; height: 220px;
                animation: spin 1.2s linear infinite;
                border-radius: 50%;
                box-shadow: 0 0 24px 8px #d3ad74;
                background: #221d14;
                padding: 25px;
            }}
            @keyframes spin {{
                0%   {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            .upload-text {{
                text-align: center;
                color: #ffd700;
                font-size: 26px;
                font-family: 'Harry P', fantasy, serif;
                margin-top: 30px;
                text-shadow: 1px 1px 10px #412f09;
                line-height: 1.4;
            }}
            </style>
            <div class="overlay">
                <div>
                    <img src="https://w7.pngwing.com/pngs/536/147/png-transparent-logo-harry-potter-and-the-cursed-child-hogwarts-james-potter-fictional-universe-of-harry-potter-harry-potter-logo-magic-witchcraft-thumbnail.png" class="rotating-img" alt="Sorting Hat">
                    <div class="upload-text">Sorting your PDFs...<br>Don't move a muscle!</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<div></div>", unsafe_allow_html=True)


left, center, right = st.columns([1, 2, 1])

with center:
    st.markdown("<div class='hp-scholar'>Hello Scholar</div>", unsafe_allow_html=True)

    project_name = st.text_input(
        "Enter your Project Name",
        value=st.session_state.project_name,
        help="Project name scopes your uploads and queries, isolating data."
    )
    if project_name.strip() != st.session_state.project_name:
        st.session_state.project_name = project_name.strip()
        st.session_state.chat_history = []
        st.session_state.upload_success_message = ""

    if not st.session_state.project_name:
        st.stop()

    try:
        res = requests.get(f"{API_BASE}/pdf/list", params={"project_name": st.session_state.project_name})
        pdf_list = res.json().get("pdfs", []) if res.ok else []
    except Exception as e:
        st.error(f"Error fetching PDF list: {e}")
        pdf_list = []

    selected_pdf = st.selectbox("Select a PDF", pdf_list) if pdf_list else None

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"<div style='background:#222;padding:10px;text-align:right;color:#fff;border-radius:10px;margin-bottom:10px'><strong>You:</strong><br>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background:#333;padding:10px;color:#0ff;border-radius:10px;margin-bottom:10px'><strong>Assistant:</strong><br>{msg['content']}</div>", unsafe_allow_html=True)
            if msg.get("context"):
                with st.expander("Context Preview"):
                    for i, chunk in enumerate(msg["context"], 1):
                        st.markdown(f"**Chunk {i}:**\n{chunk}")

    st.markdown("---")

    def on_enter():
        question = st.session_state.question_text.strip()
        if question:
            st.session_state.chat_history.append({"role": "user", "content": question})
            try:
                params = {"q": question, "project_name": st.session_state.project_name}
                if selected_pdf:
                    params["pdf_name"] = selected_pdf
                res = requests.get(f"{API_BASE}/ask", params=params)
                if res.ok:
                    data = res.json()
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": data.get("answer", "No answer returned."),
                        "context": data.get("context_preview", [])
                    })
                else:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": "Sorry, I couldn't generate a response at the moment."
                    })
            except Exception as e:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"Error: {e}"
                })
            st.session_state.question_text = ""

    st.text_input(
        "Enter your question",
        key="question_text",
        on_change=on_enter,
        placeholder="Type your question and hit Enter"
    )

    st.markdown("---")

    if st.button("Upload your PDFs here!"):
        st.session_state.show_upload = not st.session_state.show_upload
        st.session_state.upload_success_message = ""

    if st.session_state.show_upload:
        uploaded_files = st.file_uploader("Choose up to 2 PDFs", type=["pdf"], accept_multiple_files=True)

        if uploaded_files:
            if len(uploaded_files) > 2:
                st.warning("Please upload only up to 2 PDFs.")
            else:
                if st.button("Upload PDFs", key="upload_button"):
                    st.session_state.is_uploading = True
                    show_upload_spinner(True)
                    files = [("files", (f.name, f, "application/pdf")) for f in uploaded_files]
                    try:
                        res = requests.post(
                            f"{API_BASE}/upload",
                            params={"project_name": st.session_state.project_name},
                            files=files
                        )
                        if res.ok:
                            st.session_state.upload_success_message = "✅ PDFs uploaded and indexed successfully!"
                        else:
                            st.session_state.upload_success_message = (
                                "❌ Upload failed: " + res.json().get("detail", "Unknown error")
                            )
                    except Exception as e:
                        st.session_state.upload_success_message = f"❌ Upload failed: {e}"
                    st.session_state.is_uploading = False
                    st.rerun()

        show_upload_spinner(st.session_state.is_uploading)

        if st.session_state.upload_success_message and not st.session_state.is_uploading:
            st.markdown(
                f"<div style='margin-top:10px; color:#0f0; font-weight:bold'>{st.session_state.upload_success_message}</div>",
                unsafe_allow_html=True
            )
