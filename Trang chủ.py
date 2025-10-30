# streamlit page title: Trang chủ FloodConnect
import streamlit as st
import base64
import os
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Mạng Xã Hội · FloodConnect",
    page_icon="🌐",
    layout="wide"
)

# --- Caching hình ảnh ---
@st.cache_data(show_spinner=False)
def get_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# --- Ảnh ---
left_img = get_base64_image("assets/left.png")
right_img = get_base64_image("assets/right.png")

# --- Video nền ---
VIDEO_URL = "https://res.cloudinary.com/dwrr9uwy1/video/upload/v1761737518/background_kou0uc.mp4"

# --- CSS giao diện ---
st.markdown(f"""
    <style>
        .block-container {{
            max-width: 89% !important;
            padding-left: 5rem !important;
            padding-right: 5rem !important;
            position: relative;
            z-index: 2;
        }}

        /* Video nền */
        .background-video {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            z-index: 0;
            filter: brightness(0.7);
        }}

        .stApp {{
            font-family: 'Poppins', sans-serif;
            color: #e6f0ff;
        }}

        /* --- Tiêu đề chính --- */
        .title-container {{
            display: flex;
            align-items: center;
            justify-content: center;
            margin-top: 0px;
            animation: fadeInDown 1.2s ease;
            z-index: 2;
            position: relative;
            gap: 20px;
            flex-wrap: nowrap;
        }}

        .title-container img {{
            width: 280px;
            height: auto;
            animation: float 4s ease-in-out infinite;
        }}

        .title-text {{
            font-size: 2.6em;
            color: #cce5ff;
            text-align: center;
            text-shadow: 0 0 8px rgba(0,0,0,0.8), 0 0 18px rgba(255,255,255,0.2);
            font-weight: 700;
            line-height: 1.3em;
            word-break: break-word;
            white-space: normal;
            margin: 0 0.5rem;
        }}

        h2 {{
            color: #b3d1ff;
            margin-top: -10px;
            text-align: center;
            text-shadow: 0 0 10px rgba(0,0,0,0.8);
            font-weight: 500;
        }}

        /* --- Nút --- */
        .stButton > button {{
            background: linear-gradient(135deg, #b3d1ff 0%, #80b3ff 100%);
            color: #001f4d;
            border: none;
            padding: 14px 32px;
            border-radius: 25px;
            font-size: 1.1em;
            margin: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            font-weight: 600;
        }}

        .stButton > button:hover {{
            background: linear-gradient(135deg, #99ccff 0%, #6699ff 100%);
            transform: scale(1.05);
            box-shadow: 0 6px 14px rgba(0,0,0,0.4);
        }}

        /* --- Hiệu ứng --- */
        @keyframes fadeInDown {{
            0% {{ opacity: 0; transform: translateY(-20px); }}
            100% {{ opacity: 1; transform: translateY(0); }}
        }}

        @keyframes float {{
            0% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-10px); }}
            100% {{ transform: translateY(0px); }}
        }}

        /* --- Responsive: Điện thoại & Tablet nhỏ --- */
        @media (max-width: 768px) {{
            .block-container {{
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                max-width: 100% !important;
            }}

            .title-container {{
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 10px;
                margin-top: 1.5rem;
            }}

            .title-container img {{
                width: 120px;
                margin: 5px auto;
                display: block;
            }}

            .title-text {{
                font-size: 1.3em;
                line-height: 1.2em;
                padding: 0 0.5rem;
                text-align: center;
                margin: 0.3rem 0;
            }}

            h2 {{
                font-size: 1em;
                margin-top: 0.8rem;
                padding: 0 0.5rem;
            }}

            .stButton > button {{
                font-size: 1em;
                padding: 10px 16px;
            }}
        }}
    </style>

    <video autoplay loop muted playsinline class="background-video">
        <source src="{VIDEO_URL}" type="video/mp4">
    </video>
""", unsafe_allow_html=True)

# --- Tiêu đề chính ---
st.markdown(f"""
<div class="title-container">
    <img src="data:image/png;base64,{left_img}">
    <h1 class="title-text">Chào mừng bạn đến với FloodConnect!</h1>
    <img src="data:image/png;base64,{right_img}">
</div>
""", unsafe_allow_html=True)

# --- Phụ đề ---
st.markdown("<h2>Trước tiên, hãy cho tôi biết — bạn là ai?</h2>", unsafe_allow_html=True)

# --- Các lựa chọn ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("💰 Nhà hảo tâm"):
        st.session_state["role"] = "RichKid"
        st.switch_page("pages/Đăng nhập.py")

with col2:
    if st.button("🤝 Tình nguyện viên"):
        st.session_state["role"] = "Supporter"
        st.switch_page("pages/Bản đồ.py")

with col3:
    if st.button("🏠 Người dân vùng lũ"):
        st.session_state["role"] = "flooded_guys"
        st.switch_page("pages/Đăng nhập.py")

with col4:
    if st.button("🆘 Tôi là người cần cứu trợ"):
        st.query_params["scroll"] = ["form"]
        st.switch_page("pages/Bản đồ.py")
