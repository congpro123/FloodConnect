import streamlit as st
from datetime import datetime
from firebase_rest import get_firestore_docs, add_firestore_doc
import time

st.set_page_config(page_title="MXH Mini", layout="wide")

# ===== KIỂM TRA ĐĂNG NHẬP =====
if not st.session_state.get("logged_in", False):
    st.warning("⚠️ Vui lòng đăng nhập trước!")
    st.stop()

# ===== HEADER =====
st.markdown(f"""
<div style='display:flex; justify-content:space-between; align-items:center;
            background-color:#1a73e8; padding:10px 20px; border-radius:10px;
            color:white;'>
    <div style='font-size:24px; font-weight:bold;'>📘 Mạng Xã Hội Mini</div>
    <div style='display:flex; align-items:center; gap:10px;'>
        <img src='{st.session_state.user_avatar}' width='40' height='40' style='border-radius:50%; border:2px solid white;'/>
        <span style='font-size:18px; font-weight:500;'>{st.session_state.user_name}</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ===== ĐĂNG BÀI =====
st.subheader("🖋️ Đăng bài mới")
content = st.text_area("Bạn đang nghĩ gì?", placeholder="Chia sẻ cảm xúc của bạn...")
if st.button("Đăng bài"):
    if content.strip():
        add_firestore_doc("posts", {
            "user": st.session_state.user_name,
            "email": st.session_state.user_email,
            "avatar": st.session_state.user_avatar,
            "content": content.strip(),
            "timestamp": datetime.now().isoformat()
        })
        st.success("✅ Bài viết đã được đăng!")
        st.experimental_rerun()
    else:
        st.warning("⚠️ Nội dung không được để trống.")

st.markdown("---")

# ===== HIỂN THỊ BÀI VIẾT =====
st.subheader("📰 Bảng tin")
posts = sorted(get_firestore_docs("posts"), key=lambda x: x.get("timestamp",""), reverse=True)
if not posts:
    st.info("Chưa có bài viết nào.")
else:
    for post in posts:
        time_posted = post.get("timestamp","")[:16].replace("T"," ")
        st.markdown(f"""
        <div style='background-color:#8a02de; padding:15px; border-radius:12px; margin-bottom:15px;
                    box-shadow:0 2px 4px rgba(0,0,0,0.1); color:white;'>
            <div style='display:flex; align-items:center; gap:10px;'>
                <img src='{post.get("avatar")}' width='40' height='40' style='border-radius:50%; border:1px solid #ddd;'/>
                <div><strong>{post.get("user")}</strong><br>
                <span style='font-size:12px; color:#eee;'>{time_posted}</span></div>
            </div>
            <p style='margin-top:10px; font-size:16px;'>{post.get("content")}</p>
        </div>
        """, unsafe_allow_html=True)
