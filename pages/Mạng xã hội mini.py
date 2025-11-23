# FloodConnect Mini - Streamlit
import streamlit as st
from datetime import datetime
import time
import json
from firebase_rest import (
    get_firestore_docs,
    add_firestore_doc,
    update_firestore_doc,
    delete_firestore_doc
)
from streamlit_js_eval import streamlit_js_eval
from session_manager import init_session
from streamlit_cookies_manager import EncryptedCookieManager
import cloudinary
import cloudinary.uploader

# ==========================
# CLOUDINARY CONFIG
# ==========================
cloudinary.config(
    cloud_name="dwrr9uwy1",
    api_key="258463696593724",
    api_secret="AQuiKKY9UekSC7TAgS9wggXe7CU",
    secure=True
)

# ==========================
# PAGE CONFIG
# ==========================
st.set_page_config(page_title="FloodConnect - Mạng Xã Hội Mini", layout="centered")

# ==========================
# COOKIE MANAGER
# ==========================
cookies = EncryptedCookieManager(
    prefix="floodconnect_",
    password="super-secret-key-123",
)
if not cookies.ready():
    st.stop()

# ==========================
# INIT SESSION
# ==========================
init_session()

# ==========================
# KHÔI PHỤC COOKIE
# ==========================
auth_token = cookies.get("auth_token")
if auth_token:
    st.session_state.logged_in = True
    st.session_state.user_id = cookies.get("user_id")
    st.session_state.user_name = cookies.get("user_name")
    st.session_state.user_role = cookies.get("user_role")
    st.session_state.user_email = cookies.get("user_email")

# ==========================
# LOGIN CHECK
# ==========================
if not st.session_state.get("logged_in", False):
    st.warning("⚠️ Bạn chưa đăng nhập. Vui lòng quay lại trang đăng nhập.")
    st.stop()

# ==========================
# USER INFO
# ==========================
email = st.session_state.get("user_email")
avatar_url = "https://cdn-icons-png.flaticon.com/512/149/149071.png"

# ==========================
# LẤY USER FIRESTORE
# ==========================
all_users = get_firestore_docs("users")
user_data = next((u for u in all_users if u.get("email") == email), {})
username_display = (
    user_data.get("name") or
    user_data.get("username") or
    st.session_state.get("user_name") or
    "Người dùng"
)

# ==========================
# SIDEBAR
# ==========================
st.sidebar.markdown("## ⚙️ Cài đặt tài khoản")
tab = st.sidebar.radio("", ["Trang chủ", "Cài đặt"])

# ==========================
# HÀM ĐĂNG XUẤT
# ==========================
def logout(cookies: EncryptedCookieManager):
    keys_to_clear = [
        "logged_in", "user_id", "user_name", "user_role",
        "user_email", "user_avatar", "fcm_token",
        "profile_name", "profile_email", "lat_value",
        "lng_value", "pending_lat", "pending_lng",
    ]
    for k in keys_to_clear:
        st.session_state.pop(k, None)

    for ck in ["auth_token","user_id","user_name","user_role","user_email","user_avatar"]:
        cookies[ck] = ""

    cookies.save()
    st.rerun()

# ==========================
# CÀI ĐẶT TÀI KHOẢN
# ==========================
if tab == "Cài đặt":
    if st.button("🔒 Đăng xuất"):
        logout(cookies)

    st.subheader("Chỉnh sửa thông tin cá nhân")

    if "profile_name" not in st.session_state:
        st.session_state.profile_name = user_data.get("name", username_display)

    if "profile_email" not in st.session_state:
        st.session_state.profile_email = user_data.get("email", email)

    if "lat_value" not in st.session_state:
        st.session_state.lat_value = float(user_data.get("lat", 0.0) or 0)

    if "lng_value" not in st.session_state:
        st.session_state.lng_value = float(user_data.get("lng", 0.0) or 0)

    # áp dụng pending lat/lng
    if "pending_lat" in st.session_state:
        st.session_state.lat_value = float(st.session_state.pending_lat)
        st.session_state.lng_value = float(st.session_state.pending_lng)
        del st.session_state["pending_lat"]
        del st.session_state["pending_lng"]

    name = st.text_input("Tên hiển thị", key="profile_name")
    email_edit = st.text_input("Email", key="profile_email")
    st.number_input("Vĩ độ", key="lat_value", format="%.6f")
    st.number_input("Kinh độ", key="lng_value", format="%.6f")

    # Lấy tọa độ hiện tại
    if st.button("📍 Lấy tọa độ hiện tại"):
        js = """
        new Promise((resolve) => {
            navigator.geolocation.getCurrentPosition(
                pos => resolve(JSON.stringify({lat: pos.coords.latitude, lng: pos.coords.longitude})),
                err => resolve("ERROR:" + err.message)
            );
        });
        """
        coords = streamlit_js_eval(js_expressions=js)
        if coords and not str(coords).startswith("ERROR"):
            d = json.loads(coords)
            st.session_state.pending_lat = d["lat"]
            st.session_state.pending_lng = d["lng"]
            st.success("Đã lấy vị trí!")
            st.rerun()
        else:
            st.warning("Không lấy được vị trí.")

    st.markdown("---")

    if st.button("💾 Lưu thay đổi"):
        try:
            update_firestore_doc("users", user_data["id"], {
                "name": st.session_state.profile_name,
                "email": st.session_state.profile_email,
                "lat": float(st.session_state.lat_value),
                "lng": float(st.session_state.lng_value),
                "avatar": user_data.get("avatar", avatar_url),
                "password": user_data.get("password"),
                "role": user_data.get("role", "Ẩn danh"),
            })
            st.session_state.user_name = st.session_state.profile_name
            st.session_state.user_email = st.session_state.profile_email
            st.success("Cập nhật thành công!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error("Lỗi cập nhật: " + str(e))

# ==========================
# HEADER
# ==========================
st.markdown(
    f"""
    <div style='display:flex;justify-content:space-between;align-items:center;
    background-color:#1a73e8;padding:10px 20px;border-radius:10px;color:white;'>
        <div style='font-size:24px;font-weight:bold;'>📘 Mạng Xã Hội Mini</div>
        <div style='display:flex;align-items:center;gap:10px;'>
            <img src='{avatar_url}' width='40' height='40' style='border-radius:50%;border:2px solid white;' />
            <span style='font-size:18px;font-weight:500;'>{username_display}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("---")

# ==========================
# TRANG CHỦ
# ==========================
if tab == "Trang chủ":
    st.subheader("🖋️ Đăng bài mới")
    content = st.text_area("Bạn đang nghĩ gì?", placeholder="Chia sẻ cảm xúc của bạn...")
    uploaded_image = st.file_uploader("📷 Chọn ảnh để đăng (tuỳ chọn)", type=["jpg","jpeg","png"])

    if st.button("Đăng bài"):
        if content.strip() or uploaded_image:
            image_url = ""
            if uploaded_image:
                try:
                    upload = cloudinary.uploader.upload(uploaded_image)
                    image_url = upload.get("secure_url")
                except Exception as e:
                    st.error("Lỗi upload ảnh: " + str(e))
            add_firestore_doc("posts", {
                "user": username_display,
                "email": email,
                "avatar": avatar_url,
                "content": content.strip(),
                "image": image_url,
                "timestamp": datetime.now().isoformat(),
            })
            st.success("Đăng bài thành công!")
            st.rerun()
        else:
            st.warning("Nội dung bài viết trống.")

    st.markdown("---")
    st.subheader("📰 Bảng tin")

    # ===== Vòng lặp bài viết =====
    posts = sorted(get_firestore_docs("posts"), key=lambda x: x.get("timestamp",""), reverse=True)
    if not posts:
        st.info("Chưa có bài viết nào.")
    else:
        for post in posts:
            post_id = post.get("id")
            is_owner = post.get("email") == email
            time_posted = post.get("timestamp","")[:16].replace("T"," ")

            # Header bài viết + nút xoá
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                st.markdown(f"""
                    <div style='display:flex;align-items:center;gap:10px;'>
                        <img src='{post.get("avatar", avatar_url)}' width='50' height='50'
                            style='border-radius:50%;border:2px solid #1a73e8;' />
                        <div>
                            <strong style='font-size:16px;'>{post.get("user")}</strong><br>
                            <span style='font-size:12px;color:#555;'>{time_posted}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                if is_owner:
                    if st.button("🗑️", key=f"del_{post_id}", help="Xoá bài"):
                        delete_firestore_doc("posts", post_id)
                        st.success("Đã xoá bài!")
                        st.rerun()

            # Nội dung bài
            st.markdown(f"<div style='font-size:15px;line-height:1.4;margin-top:5px;'>{post.get('content','')}</div>", unsafe_allow_html=True)

            # Hình ảnh
            if post.get("image"):
                st.markdown(f"<img src='{post['image']}' style='width:100%;margin-top:10px;border-radius:12px;' />", unsafe_allow_html=True)

            # Bình luận
            comments = sorted(get_firestore_docs("comments"), key=lambda x: x.get("timestamp",""))
            post_comments = [c for c in comments if c.get("post_id")==post_id]
            for c in post_comments:
                comment_time = c.get("timestamp","")[:16].replace("T"," ")
                st.markdown(f"""
                    <div style='display:flex;align-items:flex-start;gap:10px;margin-top:10px;'>
                        <img src='{c.get("avatar", avatar_url)}' width='30' height='30'
                            style='border-radius:50%;border:1px solid #1a73e8;' />
                        <div style='background:#064c80;padding:5px 10px;border-radius:10px;'>
                            <strong style='font-size:14px;'>{c.get("user")}</strong> 
                            <span style='font-size:10px;color:#ffffff;'>{comment_time}</span>
                            <div style='font-size:14px;margin-top:2px;'>{c.get("content","")}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            # Input bình luận
            new_comment_key = f"new_comment_{post_id}"
            new_comment = st.text_input("💬 Viết bình luận...", key=new_comment_key)
            if st.button("Gửi", key=f"send_comment_{post_id}") and new_comment.strip():
                add_firestore_doc("comments", {
                    "post_id": post_id,
                    "user": username_display,
                    "email": email,
                    "avatar": avatar_url,
                    "content": new_comment.strip(),
                    "timestamp": datetime.now().isoformat(),
                })
                st.success("Đã gửi bình luận!")
                st.rerun()

            st.markdown("<hr style='margin:15px 0;' />", unsafe_allow_html=True)
