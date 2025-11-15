import streamlit as st
from streamlit_option_menu import option_menu
import time
from firebase_rest import get_firestore_docs, add_firestore_doc, update_firestore_doc
from streamlit_js_eval import streamlit_js_eval
from session_manager import init_session
from streamlit_cookies_manager import EncryptedCookieManager


# ======================================================
#  COOKIE MANAGER – KHỞI TẠO SỚM NHẤT
# ======================================================
cookies = EncryptedCookieManager(
    prefix="floodconnect_",
    password="super-secret-key-123",
)

if not cookies.ready():
    st.stop()


# ======================================================
#  KHỞI TẠO SESSION STATE (KHÔNG RESET)
# ======================================================
init_session()


# ======================================================
#  PHỤC HỒI TRẠNG THÁI TỪ COOKIE (SAU init_session)
# ======================================================
auth_token = cookies.get("auth_token")

if auth_token:
    st.session_state.logged_in = True
    st.session_state.user_id = cookies.get("user_id")
    st.session_state.user_name = cookies.get("user_name")
    st.session_state.user_role = cookies.get("user_role")
    st.session_state.user_email = cookies.get("user_email")


# ======================================================
#  ĐÃ ĐĂNG NHẬP → CHUYỂN TRANG
# ======================================================
if st.session_state.logged_in:
    st.switch_page("pages/Mạng xã hội mini.py")
    st.stop()


# ======================================================
#  PAGE CONFIG
# ======================================================
st.set_page_config(page_title="FloodConnect - Đăng nhập", layout="centered")


# ======================================================
#  UI + NỀN VIDEO
# ======================================================
VIDEO_URL = "https://res.cloudinary.com/dwrr9uwy1/video/upload/v1761737518/background_kou0uc.mp4"

st.markdown(f"""
    <style>
        * {{ box-sizing: border-box; }}
        .stApp {{
            font-family: 'Poppins', sans-serif;
        }}
        .background-video {{
            position: fixed; top: 0; left: 0;
            width: 100%; height: 100%;
            object-fit: cover;
            z-index: 0;
            filter: brightness(0.7);
        }}
        .login-banner {{
            width: 80%; max-width: 900px;
            margin: 0vh auto 0 auto;
            padding: 30px 50px;
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(18px);
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 8px 30px rgba(0,0,0,0.4);
            position: relative; z-index: 2;
            color: #d1e1ff;
        }}
        .login-banner h2 {{
            color: #eef1ff;
            font-size: 2.1em;
            margin-bottom: 0px;
            text-shadow: 0 0 12px rgba(0,0,0,0.6);
        }}
        input::placeholder {{ color: #a5b4fc; }}

        .stTextInput > div > div > input {{
            background: rgba(50, 65, 100, 0.35) !important;
            color: #dbeafe !important;
            border: 1px solid rgba(147, 197, 253, 0.4);
            border-radius: 12px; padding: 10px 15px;
        }}

        .stButton > button {{
            background: linear-gradient(135deg, #4ea7ff 0%, #2a65ff 100%);
            color: white; border: none; padding: 10px 28px;
            border-radius: 25px; width: 100%;
            margin-top: 1rem;
            transition: all 0.3s ease;
        }}
        .stButton > button:hover {{
            transform: scale(1.05);
        }}
    </style>

    <video autoplay loop muted playsinline preload="none" class="background-video">
        <source src="{VIDEO_URL}" type="video/mp4">
    </video>
""", unsafe_allow_html=True)


# ======================================================
#  MENU
# ======================================================
selected = option_menu(
    None,
    ["Đăng nhập", "Đăng ký tài khoản"],
    icons=["box-arrow-in-right", "person-plus"],
    default_index=0,
    orientation="horizontal",
)


# ======================================================
#  FORM ĐĂNG NHẬP
# ======================================================
if selected == "Đăng nhập":

    st.markdown("<div class='login-banner'><h2>🔐 Đăng nhập FloodConnect</h2>", unsafe_allow_html=True)

    email = st.text_input("📧 Email đăng nhập:")
    password = st.text_input("🔑 Mật khẩu:", type="password")

    if st.button("Đăng nhập"):

        users = get_firestore_docs("users")
        user = next((u for u in users if u.get("email") == email), None)

        if not user:
            st.error("⚠️ Không tìm thấy tài khoản!")
        elif user.get("password") != password:
            st.error("❌ Sai mật khẩu!")
        else:
            st.success("🎉 Đăng nhập thành công!")

            # Lưu session
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.session_state.user_role = user.get("role", "Ẩn danh")
            st.session_state.user_name = user.get("name") or user.get("username", "Người dùng")
            st.session_state.user_avatar = user.get("avatar", "")
            st.session_state.user_id = user["id"]

            # Lưu cookie
            cookies["auth_token"] = str(user["id"])
            cookies["user_id"] = user["id"]
            cookies["user_email"] = email
            cookies["user_name"] = st.session_state.user_name
            cookies["user_role"] = st.session_state.user_role
            cookies.save()

            time.sleep(0.2)
            st.switch_page("pages/Mạng xã hội mini.py")

    st.markdown("</div>", unsafe_allow_html=True)


# ======================================================
#  ĐĂNG KÝ TÀI KHOẢN
# ======================================================
else:
    st.markdown("<div class='login-banner'><h2>📝 Tạo tài khoản mới</h2>", unsafe_allow_html=True)

    email = st.text_input("📧 Nhập email:")
    username = st.text_input("🧑 Nhập tên:")
    password = st.text_input("🔒 Nhập mật khẩu:", type="password")
    role = st.selectbox("🎭 Vai trò", ["Nhà hảo tâm", "Tình nguyện viên", "Người dân vùng lũ"])

    if st.button("Tạo tài khoản"):
        if not email or not username or not password:
            st.warning("⚠️ Vui lòng nhập đầy đủ!")
        else:
            users = get_firestore_docs("users")
            if any(u.get("email") == email for u in users):
                st.error("🚫 Email đã tồn tại!")
            else:
                add_firestore_doc("users", {
                    "email": email,
                    "username": username,
                    "password": password,
                    "role": role
                })
                st.success("🎉 Tạo tài khoản thành công!")
                time.sleep(1.5)
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
