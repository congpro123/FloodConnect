# streamlit page title: Trang chủ FloodConnect
import streamlit as st
import base64
import os
import streamlit.components.v1 as components
from streamlit.components.v1 import html
import pathlib

st.set_page_config(
    page_title="Mạng Xã Hội · FloodConnect",
    page_icon="🌐",
    layout="wide"
)
st.markdown("""
<script>
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/firebase-messaging-sw.js')
    .then(reg => {
        console.log('[SW] Registered:', reg);
        window.swRegistered = true;
    })
    .catch(err => console.error('[SW] Register failed:', err));
} else {
    console.warn('Service Worker not supported');
}
</script>
""", unsafe_allow_html=True)
# --- Caching hình ảnh ---
@st.cache_data(show_spinner=False)
def get_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()
# Serve service worker
sw_path = pathlib.Path("firebase-messaging-sw.js")
if sw_path.exists():
    with open(sw_path, "r") as f:
        sw_code = f.read()
    html(f"<script>{sw_code}</script>", height=0)
# --- Ảnh ---

# --- Video nền ---
VIDEO_URL = "https://res.cloudinary.com/dwrr9uwy1/video/upload/v1761737518/background_kou0uc.mp4"

# --- CSS giao diện ---
st.markdown(f"""
    <style>
        .block-container {{
            max-width: 100% !important;
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
            gap: 0px;
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
    <h1 class="title-text">Chào mừng bạn đến với FloodConnect!</h1>
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
        st.switch_page("pages/Đăng nhập.py")

with col3:
    if st.button("🏠 Người dân vùng lũ"):
        st.session_state["role"] = "flooded_guys"
        st.switch_page("pages/Đăng nhập.py")

with col4:
    if st.button("🆘 Tôi là người cần cứu trợ"):
        st.query_params["scroll"] = ["form"]
        st.switch_page("pages/Bản đồ.py")

st.markdown("<h2>ABOUT</h2>", unsafe_allow_html=True)

st.markdown(f"""
<div class="login-banner">
    <p>
        FloodConnect là nền tảng web và ứng dụng di động được thiết kế để hỗ trợ cộng đồng 
        và các lực lượng cứu trợ trong các vùng bị ảnh hưởng bởi lũ lụt tại Việt Nam. 
        Sử dụng bản đồ hành chính Việt Nam mới nhất, FloodConnect hiển thị trực quan các 
        khu vực đang chịu tác động của mưa lũ, giúp người dân, chính quyền và các tình nguyện viên 
        có thể nắm bắt tình hình nhanh chóng và chính xác.
    </p>
</div>

<style>
.login-banner {{
    width: 100%; max-width: 1000px;
    margin: 3vh auto 5vh auto;
    padding: 30px 50px;
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(18px);
    border-radius: 20px;
    text-align: center;
    box-shadow: 0 8px 30px rgba(0,0,0,0.4);
    position: relative; z-index: 2;
    color: #cce5ff; /* giống màu chữ tiêu đề */
    font-size: 1.1em;
    line-height: 1.6em;
}}
</style>
""", unsafe_allow_html=True)
