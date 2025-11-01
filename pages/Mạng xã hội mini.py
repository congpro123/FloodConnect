import streamlit as st
from datetime import datetime
import time
from firebase_rest import get_firestore_docs, add_firestore_doc

st.set_page_config(page_title="Mạng Xã Hội Mini", layout="centered")

# === KIỂM TRA ĐĂNG NHẬP ===
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("⚠️ Vui lòng đăng nhập trước khi vào mạng xã hội.")
    st.stop()

username = st.session_state.get("user_name")
email = st.session_state.get("user_email")
avatar_url = st.session_state.get("user_avatar", "https://cdn-icons-png.flaticon.com/512/149/149071.png")

st.markdown(
    f"""
    <div style='display: flex; justify-content: space-between; align-items: center;
                background-color: #1a73e8; padding: 10px 20px; border-radius: 10px;
                color: white;'>
        <div style='font-size: 24px; font-weight: bold;'>📘 Mạng Xã Hội Mini</div>
        <div style='display: flex; align-items: center; gap: 10px;'>
            <img src='{avatar_url}' width='40' height='40' style='border-radius:50%; border:2px solid white;' />
            <span style='font-size: 18px; font-weight: 500;'>{username}</span>
            <form action="?logout=true" method="get">
                <button type="submit" style='background-color:#fff; color:#1a73e8;
                    border:none; border-radius:8px; padding:6px 12px; cursor:pointer; font-weight:600;'>
                    Đăng xuất
                </button>
            </form>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# === ĐĂNG XUẤT ===
if "logout" in st.query_params:
    st.session_state.clear()
    st.success("Đã đăng xuất. Quay lại trang đăng nhập...")
    time.sleep(1)
    st.switch_page("pages/Đăng nhập.py")

st.markdown("---")

# === ĐĂNG BÀI ===
st.subheader("🖋️ Đăng bài mới")

content = st.text_area("Bạn đang nghĩ gì?", placeholder="Chia sẻ cảm xúc của bạn...")

if st.button("Đăng bài"):
    if content.strip():
        add_firestore_doc("posts", {
            "user": username,
            "email": email,
            "avatar": avatar_url,
            "content": content.strip(),
            "timestamp": datetime.now().isoformat(),
        })
        st.success("✅ Bài viết đã được đăng!")
        st.rerun()
    else:
        st.warning("⚠️ Nội dung bài viết không được để trống.")

st.markdown("---")

# === HIỂN THỊ BÀI VIẾT ===
st.subheader("📰 Bảng tin")

posts = sorted(get_firestore_docs("posts"), key=lambda x: x.get("timestamp", ""), reverse=True)

if not posts:
    st.info("Chưa có bài viết nào. Hãy là người đầu tiên đăng nhé!")
else:
    for post in posts:
        time_posted = post.get("timestamp", "")[:16].replace("T", " ")
        st.markdown(
            f"""
            <div style='background-color: #f8f9fa; padding: 15px; border-radius: 12px; margin-bottom: 15px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <div style='display: flex; align-items: center; gap: 10px;'>
                    <img src='{post.get("avatar", avatar_url)}' width='40' height='40' style='border-radius:50%; border:1px solid #ddd;' />
                    <div>
                        <strong>{post.get("user", "Ẩn danh")}</strong><br>
                        <span style='font-size:12px; color:gray;'>{time_posted}</span>
                    </div>
                </div>
                <p style='margin-top:10px; font-size:16px;'>{post.get("content","")}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
