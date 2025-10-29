import streamlit as st
import requests

API_BASE = "http://localhost:8000/pdf"

# === Page Configuration ===
st.set_page_config(page_title="PDF QA Assistant", layout="wide")

# === Initialize Session State ===
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
            width: 40px;
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


set_background("https://images.wallpapersden.com/image/download/darth-vader-4k_bGpnbGeUmZqaraWkpJRobWllrWdma2U.jpg")


left, center, right = st.columns([1, 2, 1])

with center:
    st.markdown("### Your Jedi Chat")

    project_name = st.text_input(
        "Enter your Project Name (new session starts with a new name)",
        value=st.session_state.project_name,
        help="Project name scopes your uploads and queries, isolating data."
    )
    if project_name.strip() != st.session_state.project_name:
        st.session_state.project_name = project_name.strip()
        st.session_state.chat_history = []
        st.session_state.upload_success_message = ""

    if not st.session_state.project_name:
        st.warning("Please enter a Project Name.")
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

    # Callback function for Enter key press
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
            # Clear input after processing
            st.session_state.question_text = ""

    st.text_input(
        "Enter your question",
        key="question_text",
        on_change=on_enter,
        placeholder="Type your question and hit Enter"
    )

    st.markdown("---")

    if st.button("Upload your PDFs here, Padawan!"):
        st.session_state.show_upload = not st.session_state.show_upload
        st.session_state.upload_success_message = ""

    if st.session_state.show_upload:
        uploaded_files = st.file_uploader("Choose up to 2 PDFs", type=["pdf"], accept_multiple_files=True)

        if uploaded_files:
            if len(uploaded_files) > 2:
                st.warning("Please upload only up to 2 PDFs.")
            else:
                if st.button("Upload PDFs", key="upload_button"):
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
                            st.session_state.upload_success_message = "❌ Upload failed: " + res.json().get("detail", "Unknown error")
                    except Exception as e:
                        st.session_state.upload_success_message = f"❌ Upload failed: {e}"

        if st.session_state.upload_success_message:
            st.markdown(f"<div style='margin-top:10px; color:#0f0; font-weight:bold'>{st.session_state.upload_success_message}</div>", unsafe_allow_html=True)
