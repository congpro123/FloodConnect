# streamlit page title: Mạng Xã Hội Mini
import streamlit as st
from google.cloud import firestore
from datetime import datetime
import time

# === KHỞI TẠO FIREBASE ===
db = firestore.Client.from_service_account_json("firebase_key.json")

# === KIỂM TRA ĐĂNG NHẬP ===
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("⚠️ Vui lòng đăng nhập trước khi vào mạng xã hội.")
    st.stop()

# === LẤY THÔNG TIN TỪ PHIÊN (SESSION) ===
username = st.session_state.get("user_name")
email = st.session_state.get("user_email")
avatar_url = st.session_state.get(
    "user_avatar",
    "https://cdn-icons-png.flaticon.com/512/149/149071.png"
)

# === DỰ PHÒNG: nếu thiếu dữ liệu thì truy Firestore ===
if not username or not email:
    user_doc = db.collection("users").where("email", "==", email or "").limit(1).get()
    if user_doc:
        user_data = user_doc[0].to_dict()
        username = user_data.get("name", "Người dùng")
        avatar_url = user_data.get(
            "avatar",
            "https://cdn-icons-png.flaticon.com/512/149/149071.png",
        )
    else:
        username = "Người dùng"

# === THANH TRÊN (HEADER) ===
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

# === XỬ LÝ ĐĂNG XUẤT ===
if "logout" in st.query_params:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.success("Đã đăng xuất. Quay lại trang đăng nhập...")
    time.sleep(1)
    st.switch_page("pages/login.py")

st.markdown("---")

# === GIAO DIỆN ĐĂNG BÀI ===
st.subheader("🖋️ Đăng bài mới")

content = st.text_area("Bạn đang nghĩ gì?", placeholder="Chia sẻ cảm xúc của bạn...")

if st.button("Đăng bài"):
    if content.strip():
        db.collection("posts").add(
            {
                "user": username,
                "email": email,
                "avatar": avatar_url,
                "content": content.strip(),
                "timestamp": datetime.now(),
            }
        )
        st.success("✅ Bài viết đã được đăng!")
        st.experimental_rerun()
    else:
        st.warning("⚠️ Nội dung bài viết không được để trống.")

st.markdown("---")

# === HIỂN THỊ BÀI VIẾT ===
st.subheader("📰 Bảng tin")

posts = db.collection("posts").order_by("timestamp", direction=firestore.Query.DESCENDING).get()

if not posts:
    st.info("Chưa có bài viết nào. Hãy là người đầu tiên đăng nhé!")
else:
    for post in posts:
        data = post.to_dict()
        time_posted = data["timestamp"].strftime("%H:%M %d/%m/%Y")

        st.markdown(
            f"""
            <div style='background-color: #f8f9fa; padding: 15px; border-radius: 12px; margin-bottom: 15px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <div style='display: flex; align-items: center; gap: 10px;'>
                    <img src='{data["avatar"]}' width='40' height='40' style='border-radius:50%; border:1px solid #ddd;' />
                    <div>
                        <strong>{data["user"]}</strong><br>
                        <span style='font-size:12px; color:gray;'>{time_posted}</span>
                    </div>
                </div>
                <p style='margin-top:10px; font-size:16px;'>{data["content"]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
