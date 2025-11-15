import streamlit as st
from streamlit_option_menu import option_menu
import time
from firebase_rest import get_firestore_docs, add_firestore_doc, update_firestore_doc
from streamlit_js_eval import streamlit_js_eval
import json

st.set_page_config(page_title="FloodConnect - Đăng nhập", layout="centered")

# ===================================================
# ⭐ THÊM MỚI: GIỮ ĐĂNG NHẬP SAU KHI REFRESH
# ===================================================
if "logged_in" in st.session_state and st.session_state.logged_in is True:
    st.switch_page("pages/Mạng xã hội mini.py")
    st.stop()

# ===================================================
# TOKEN FIREBASE
# ===================================================
if "fcm_token" not in st.session_state:
    st.session_state.fcm_token = None

st.markdown("""
<script>
window.addEventListener("message", (event) => {
    if (event.data && event.data.fcm_token) {
        const ev = new CustomEvent("streamlit:setComponentValue", {
            detail: event.data.fcm_token
        });
        window.dispatchEvent(ev);
    }
});
</script>
""", unsafe_allow_html=True)

token_holder = st.text_input("fcm_token", key="fcm_token", label_visibility="collapsed")


# ===================================================
# CSS
# ===================================================
VIDEO_URL = "https://res.cloudinary.com/dwrr9uwy1/video/upload/v1761737518/background_kou0uc.mp4"

st.markdown(f"""
<style>
    * {{ box-sizing: border-box; }}
    .stApp {{ font-family: 'Poppins', sans-serif; }}
    .background-video {{
        position: fixed; top: 0; left: 0;
        width: 100%; height: 100%;
        object-fit: cover; z-index: 0;
        filter: brightness(0.7);
    }}
    .login-banner {{
        width: 80%; max-width: 900px;
        margin: 0vh auto;
        padding: 30px 50px;
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(18px);
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 8px 30px rgba(0,0,0,0.4);
        z-index: 2; color: #d1e1ff;
    }}
    .login-banner h2 {{
        color: #eef1ff; font-size: 2.1em;
    }}
</style>

<video autoplay loop muted playsinline preload="none" class="background-video">
    <source src="{VIDEO_URL}" type="video/mp4">
</video>
""", unsafe_allow_html=True)


# ===================================================
# MENU
# ===================================================
with st.container():
    selected = option_menu(
        None,
        ["Đăng nhập", "Đăng ký tài khoản"],
        icons=["box-arrow-in-right", "person-plus"],
        menu_icon=None,
        default_index=0,
        orientation="horizontal",
    )


# ===================================================
# ĐĂNG NHẬP
# ===================================================
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
            st.success("✅ Đăng nhập thành công!")

            # ⭐ LƯU TRẠNG THÁI ĐĂNG NHẬP
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.session_state.user_role = user.get("role", "Ẩn danh")
            st.session_state.user_name = user.get("name") or user.get("username", "Người dùng")
            st.session_state.user_avatar = user.get("avatar", "https://cdn-icons-png.flaticon.com/512/149/149071.png")
            st.session_state.user_id = user["id"]

            # Lấy FCM token
            streamlit_js_eval(
                code=""" ... (giữ nguyên toàn bộ mã firebase của bạn) ... """,
                key="fcm_get_token"
            )

            if st.session_state.fcm_token:
                update_firestore_doc("users", user["id"], {
                    "fcm_token": st.session_state.fcm_token
                })

            time.sleep(1)
            st.switch_page("pages/Mạng xã hội mini.py")

    st.markdown("</div>", unsafe_allow_html=True)
