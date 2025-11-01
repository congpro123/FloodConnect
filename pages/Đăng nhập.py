import streamlit as st
from streamlit_option_menu import option_menu
import time
from firebase_rest import get_firestore_docs, add_firestore_doc

st.set_page_config(page_title="FloodConnect - Đăng nhập", layout="centered")

VIDEO_URL = "https://res.cloudinary.com/dwrr9uwy1/video/upload/v1761737518/background_kou0uc.mp4"

# --- CSS & video nền ---
st.markdown(f"""
    <style>
        * {{ box-sizing: border-box; }}
        .stApp {{
            font-family: 'Poppins', sans-serif;
        }}
        .background-video {{
            position: fixed;
            top: 0; left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            z-index: 0;
            filter: brightness(0.7);
        }}
        .login-banner {{
            width: 80%;
            max-width: 900px;
            margin: 0vh auto 0 auto;
            padding: 30px 50px;
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(18px);
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 8px 30px rgba(0,0,0,0.4);
            position: relative;
            z-index: 2;
            color: #d1e1ff;
        }}
        .login-banner h2 {{
            color: #eef1ff;
            font-size: 2.1em;
            margin-bottom: 0px;
            text-shadow: 0 0 12px rgba(0,0,0,0.6);
        }}
        .stTextInput > label, .stSelectbox > label {{
            color: #c7d2fe !important;
            font-weight: 500;
            margin-bottom: 4px;
        }}
        .stTextInput > div > div > input,
        .stSelectbox > div > div {{
            background: rgba(50, 65, 100, 0.35);
            color: #dbeafe;
            border-radius: 12px;
            border: 1px solid rgba(147, 197, 253, 0.4);
            padding: 10px 15px;
            transition: all 0.25s ease;
        }}
        input::placeholder {{
            color: #a5b4fc;
        }}
        .stButton > button {{
            background: linear-gradient(135deg, #4ea7ff 0%, #2a65ff 100%);
            color: white;
            border: none;
            padding: 10px 28px;
            border-radius: 25px;
            font-size: 1em;
            margin-top: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}
        .stButton > button:hover {{
            background: linear-gradient(135deg, #66b6ff 0%, #4a7fff 100%);
            transform: scale(1.05);
        }}
    </style>

    <video autoplay loop muted playsinline preload="none" class="background-video">
        <source src="{VIDEO_URL}" type="video/mp4">
    </video>
""", unsafe_allow_html=True)

with st.container():
    selected = option_menu(
        None, ["Đăng nhập", "Đăng ký tài khoản"],
        icons=["box-arrow-in-right", "person-plus"],
        menu_icon=None, default_index=0,
        orientation="horizontal",
    )

# --- Đăng nhập ---
if selected == "Đăng nhập":
    st.markdown("<div class='login-banner'><h2>🔐 Đăng nhập FloodConnect</h2>", unsafe_allow_html=True)
    email = st.text_input("📧 Email đăng nhập:")
    password = st.text_input("🔑 Mật khẩu:", type="password")

    if st.button("Đăng nhập"):
        if not email or not password:
            st.warning("⚠️ Vui lòng nhập đầy đủ thông tin!")
        else:
            users = get_firestore_docs("users")
            user_data = next((u for u in users if u.get("email") == email), None)
            if user_data:
                if user_data["password"] == password:
                    st.success("✅ Đăng nhập thành công!")
                    st.session_state.update({
                        "logged_in": True,
                        "user_email": email,
                        "user_role": user_data.get("role", "Ẩn danh"),
                        "user_name": user_data.get("username", "Người dùng"),
                        "user_avatar": user_data.get("avatar", "https://cdn-icons-png.flaticon.com/512/149/149071.png"),
                    })
                    time.sleep(1)
                    st.switch_page("pages/Mạng xã hội mini.py")
                else:
                    st.error("❌ Sai mật khẩu!")
            else:
                st.error("⚠️ Không tìm thấy tài khoản với email này!")
    st.markdown("</div>", unsafe_allow_html=True)

# --- Đăng ký ---
else:
    st.markdown("<div class='login-banner'><h2>📝 Tạo tài khoản mới</h2>", unsafe_allow_html=True)
    email = st.text_input("📧 Nhập email của bạn:")
    username = st.text_input("🧑 Nhập tên của bạn:")
    password = st.text_input("🔒 Nhập mật khẩu:", type="password")
    role = st.selectbox("🎭 Vai trò", ["Nhà hảo tâm", "Tình nguyện viên", "Người dân vùng lũ"])

    if st.button("Tạo tài khoản"):
        if not email or not username or not password:
            st.warning("⚠️ Vui lòng nhập đầy đủ thông tin!")
        else:
            users = get_firestore_docs("users")
            if any(u.get("email") == email for u in users):
                st.error("🚫 Email này đã được đăng ký!")
            else:
                add_firestore_doc("users", {
                    "email": email,
                    "username": username,
                    "password": password,
                    "role": role
                })
                st.success("✅ Tạo tài khoản thành công! Hãy quay lại đăng nhập.")
                time.sleep(2)
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
