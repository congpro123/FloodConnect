# streamlit page title: Mạng Xã Hội Mini
import streamlit as st
from datetime import datetime
import time
from firebase_rest import get_firestore_docs, get_access_token
import requests
import json

# === CẤU HÌNH FIREBASE REST API ===
try:
    key = dict(st.secrets["firebase"])
except Exception:
    with open("firebase_key.json", "r") as f:
        key = json.load(f)

PROJECT_ID = key["project_id"]
BASE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"

# === HÀM TIỆN ÍCH GỬI YÊU CẦU REST ===
def firestore_add(collection, data):
    """Thêm tài liệu mới vào collection"""
    token = get_access_token()
    url = f"{BASE_URL}/{collection}"
    headers = {"Authorization": f"Bearer {token}"}
    body = {"fields": {k: {"stringValue": str(v)} for k, v in data.items()}}
    r = requests.post(url, headers=headers, json=body)
    if not r.ok:
        st.error(f"Lỗi ghi Firestore: {r.status_code} - {r.text}")
    return r.ok

def firestore_query(collection, order_by=None, direction="DESCENDING"):
    """Lấy tài liệu theo thứ tự thời gian"""
    token = get_access_token()
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents:runQuery"
    headers = {"Authorization": f"Bearer {token}"}
    body = {
        "structuredQuery": {
            "from": [{"collectionId": collection}],
            "orderBy": [
                {
                    "field": {"fieldPath": order_by or "timestamp"},
                    "direction": direction
                }
            ]
        }
    }
    r = requests.post(url, headers=headers, json=body)
    if not r.ok:
        st.error(f"Lỗi truy vấn Firestore: {r.status_code} - {r.text}")
        return []
    return [x["document"] for x in r.json() if "document" in x]

# === KIỂM TRA ĐĂNG NHẬP ===
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("⚠️ Vui lòng đăng nhập trước khi vào mạng xã hội.")
    st.stop()

# === LẤY THÔNG TIN NGƯỜI DÙNG ===
username = st.session_state.get("user_name")
email = st.session_state.get("user_email")
avatar_url = st.session_state.get(
    "user_avatar",
    "https://cdn-icons-png.flaticon.com/512/149/149071.png"
)

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
    for key_ in list(st.session_state.keys()):
        del st.session_state[key_]
    st.success("Đã đăng xuất. Quay lại trang đăng nhập...")
    time.sleep(1)
    st.switch_page("pages/login.py")

st.markdown("---")

# === GIAO DIỆN ĐĂNG BÀI ===
st.subheader("🖋️ Đăng bài mới")

content = st.text_area("Bạn đang nghĩ gì?", placeholder="Chia sẻ cảm xúc của bạn...")

if st.button("Đăng bài"):
    if content.strip():
        data = {
            "user": username,
            "email": email,
            "avatar": avatar_url,
            "content": content.strip(),
            "timestamp": datetime.now().isoformat(),
        }
        if firestore_add("posts", data):
            st.success("✅ Bài viết đã được đăng!")
            st.rerun()
    else:
        st.warning("⚠️ Nội dung bài viết không được để trống.")

st.markdown("---")

# === HIỂN THỊ BÀI VIẾT ===
st.subheader("📰 Bảng tin")

posts = firestore_query("posts", order_by="timestamp", direction="DESCENDING")

if not posts:
    st.info("Chưa có bài viết nào. Hãy là người đầu tiên đăng nhé!")
else:
    for p in posts:
        fields = p["fields"]
        user = fields["user"]["stringValue"]
        avatar = fields["avatar"]["stringValue"]
        content = fields["content"]["stringValue"]
        time_posted = fields["timestamp"]["stringValue"]
        # format lại thời gian nếu cần
        try:
            t = datetime.fromisoformat(time_posted)
            time_posted = t.strftime("%H:%M %d/%m/%Y")
        except:
            pass

        st.markdown(
            f"""
            <div style='background-color: #f8f9fa; padding: 15px; border-radius: 12px; margin-bottom: 15px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <div style='display: flex; align-items: center; gap: 10px;'>
                    <img src='{avatar}' width='40' height='40' style='border-radius:50%; border:1px solid #ddd;' />
                    <div>
                        <strong>{user}</strong><br>
                        <span style='font-size:12px; color:gray;'>{time_posted}</span>
                    </div>
                </div>
                <p style='margin-top:10px; font-size:16px;'>{content}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
