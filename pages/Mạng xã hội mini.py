# Mạng xã hội mini — FloodConnect (single-file, full features, comment hiển thị)
import streamlit as st
from datetime import datetime
import time
import json
from typing import List, Dict, Any
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

# ---------------------------
# CONFIGS
# ---------------------------
cloudinary.config(
    cloud_name="dwrr9uwy1",
    api_key="258463696593724",
    api_secret="AQuiKKY9UekSC7TAgS9wggXe7CU",
    secure=True
)

st.set_page_config(page_title="FloodConnect - Mạng Xã Hội Mini", layout="wide")

# ---------------------------
# COOKIE + SESSION
# ---------------------------
cookies = EncryptedCookieManager(prefix="floodconnect_", password="super-secret-key-123")
if not cookies.ready():
    st.stop()
init_session()

# restore session from cookies
auth_token = cookies.get("auth_token")
if auth_token:
    st.session_state.logged_in = True
    st.session_state.user_id = cookies.get("user_id")
    st.session_state.user_name = cookies.get("user_name")
    st.session_state.user_email = cookies.get("user_email")
    st.session_state.user_role = cookies.get("user_role")
    st.session_state.user_avatar = cookies.get("user_avatar")

if not st.session_state.get("logged_in", False):
    st.warning("⚠️ Bạn chưa đăng nhập. Vui lòng quay lại trang đăng nhập.")
    st.stop()

# ---------------------------
# USER INFO
# ---------------------------
email = st.session_state.get("user_email")
default_avatar = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
all_users = get_firestore_docs("users")
user_data = next((u for u in all_users if u.get("email") == email), {}) if isinstance(all_users, list) else {}
username_display = user_data.get("name") or user_data.get("username") or st.session_state.get("user_name") or "Người dùng"
avatar_url = user_data.get("avatar") or st.session_state.get("user_avatar") or default_avatar

# ---------------------------
# HELPERS
# ---------------------------
def safe_comments(raw) -> List[Dict[str,Any]]:
    """Chuẩn hoá field comments: trả về list của dict, bỏ qua item không phải dict"""
    if not raw:
        return []
    if isinstance(raw, list):
        cleaned = []
        for item in raw:
            if isinstance(item, dict):
                cleaned.append(item)
            else:
                try:
                    parsed = json.loads(item)
                    if isinstance(parsed, dict):
                        cleaned.append(parsed)
                except:
                    continue
        return cleaned
    if isinstance(raw, dict):
        vals = raw.get("values") or raw.get("arrayValue", {}).get("values")
        if isinstance(vals, list):
            parsed = []
            for v in vals:
                if isinstance(v, dict):
                    if "mapValue" in v and "fields" in v["mapValue"]:
                        fields = v["mapValue"]["fields"]
                        obj = {}
                        for k, vv in fields.items():
                            if "stringValue" in vv:
                                obj[k] = vv["stringValue"]
                            else:
                                obj[k] = vv
                        parsed.append(obj)
                    elif "stringValue" in v:
                        try:
                            obj = json.loads(v["stringValue"])
                            if isinstance(obj, dict):
                                parsed.append(obj)
                        except:
                            continue
                    else:
                        parsed.append(v)
            return parsed
    return []

def add_comment_to_post(post_id: str, post_obj: Dict[str,Any], comment_obj: Dict[str,Any]):
    old_comments = safe_comments(post_obj.get("comments", []))
    updated = old_comments + [comment_obj]
    update_firestore_doc("posts", post_id, {"comments": updated})

def delete_comment_in_post(post_id: str, post_obj: Dict[str,Any], idx: int):
    old_comments = safe_comments(post_obj.get("comments", []))
    if 0 <= idx < len(old_comments):
        old_comments.pop(idx)
        update_firestore_doc("posts", post_id, {"comments": old_comments})

def format_time(ts: str) -> str:
    if not ts:
        return ""
    s = ts[:19]
    return s.replace("T", " ")

# ---------------------------
# HEADER
# ---------------------------
st.markdown(f"""
<div style='display:flex;justify-content:space-between;align-items:center;
background-color:#1a73e8;padding:10px 20px;border-radius:10px;color:white;margin-bottom:10px;'>
    <div style='font-size:22px;font-weight:700;'>📘 FloodConnect Mini</div>
    <div style='display:flex;align-items:center;gap:12px;'>
        <img src='{avatar_url}' width='36' height='36' style='border-radius:50%;border:2px solid white;'/>
        <div style='font-weight:600'>{username_display}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------
# SIDEBAR
# ---------------------------
st.sidebar.markdown("## ⚙️ Cài đặt tài khoản")
tab = st.sidebar.radio("Điều hướng", ["Trang chủ", "Cài đặt"])

def logout(cookies_obj: EncryptedCookieManager):
    keys = ["logged_in","user_id","user_name","user_email","user_role","user_avatar","auth_token"]
    for k in keys:
        st.session_state.pop(k, None)
        cookies_obj[k] = ""
    cookies_obj.save()
    st.rerun()

# ---------------------------
# SETTINGS
# ---------------------------
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

    if "pending_lat" in st.session_state:
        st.session_state.lat_value = float(st.session_state.pending_lat)
        st.session_state.lng_value = float(st.session_state.pending_lng)
        st.session_state.pop("pending_lat", None)
        st.session_state.pop("pending_lng", None)

    st.text_input("Tên hiển thị", key="profile_name")
    st.text_input("Email", key="profile_email")
    st.number_input("Vĩ độ", key="lat_value", format="%.6f")
    st.number_input("Kinh độ", key="lng_value", format="%.6f")
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
            update_firestore_doc("users", user_data.get("id"), {
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
    st.stop()

# ---------------------------
# TRANG CHỦ - Đăng bài
# ---------------------------
st.subheader("🖋️ Đăng bài mới")
with st.form(key="new_post_form", clear_on_submit=True):
    post_text = st.text_area("Bạn đang nghĩ gì?", placeholder="Chia sẻ cảm xúc...", height=120)
    uploaded_image = st.file_uploader("📷 Chọn ảnh (tùy chọn)", type=["jpg","jpeg","png"])
    submitted = st.form_submit_button("Đăng bài")
    if submitted:
        image_url = ""
        if uploaded_image:
            try:
                up = cloudinary.uploader.upload(uploaded_image)
                image_url = up.get("secure_url", "")
            except Exception as e:
                st.error("Lỗi upload ảnh: " + str(e))
        post_obj = {
            "user": username_display,
            "email": email,
            "avatar": avatar_url,
            "content": post_text.strip(),
            "image": image_url,
            "timestamp": datetime.now().isoformat(),
            "comments": []
        }
        add_firestore_doc("posts", post_obj)
        st.success("Đăng bài thành công!")
        st.rerun()

# ---------------------------
# BẢNG TIN
# ---------------------------
st.markdown("---")
st.subheader("📰 Bảng tin")
posts = sorted(get_firestore_docs("posts"), key=lambda x: x.get("timestamp",""), reverse=True)

if not posts:
    st.info("Chưa có bài viết nào.")
else:
    for post in posts:
        post_id = post.get("id")
        is_owner = (post.get("email") == email)
        time_posted = format_time(post.get("timestamp", "")) or ""
        post_user = post.get("user", "Người dùng")
        post_avatar = post.get("avatar", default_avatar)
        post_content = post.get("content", "")
        post_image = post.get("image", "")
        post_comments = safe_comments(post.get("comments", []))

        # Bài viết background xanh dương đậm
        st.markdown(f"""
        <div style='background:#0d47a1;color:white;padding:12px;border-radius:12px;margin-bottom:12px;'>
            <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
                <div style='display:flex;gap:10px;align-items:center;'>
                    <img src="{post_avatar}" width="50" height="50" style='border-radius:50%;border:2px solid #64b5f6;'/>
                    <div>
                        <div style='font-weight:700'>{post_user}</div>
                        <div style='color:#cfd8dc;font-size:12px'>{time_posted}</div>
                    </div>
                </div>
            </div>
            <div style='margin-top:10px;font-size:15px;line-height:1.4;'>{post_content}</div>
            {f"<img src='{post_image}' style='width:100%;margin-top:10px;border-radius:8px;' />" if post_image else ""}
        </div>
        """, unsafe_allow_html=True)

        # Delete post button
        if is_owner:
            if st.button("🗑️ Xoá bài", key=f"del_post_{post_id}"):
                try:
                    delete_firestore_doc("posts", post_id)
                    st.success("Đã xoá bài!")
                except Exception as e:
                    st.error("Lỗi xoá bài: " + str(e))
                st.rerun()

        # ====================
        # COMMENTS
        # ====================
        st.markdown("**💬 Bình luận**")
        if post_comments:
            for idx, c in enumerate(post_comments):
                c_user = c.get("user", "Người dùng")
                c_avatar = c.get("avatar", default_avatar)
                c_content = c.get("content", "")
                c_time = format_time(c.get("timestamp", ""))

                cols = st.columns([0.0, 0.86, 0.05])
                with cols[0]:
                    st.image(c_avatar, width=100)
                with cols[1]:
                    st.markdown(f"""
                    <div style='background:#2196f3;padding:6px 10px;border-radius:8px;color:white;'>
                        <strong>{c_user}</strong> <span style='font-size:12px;color:#e0e0e0'>{c_time}</span>
                        <div style='margin-top:2px;font-size:14px;'>{c_content}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with cols[2]:
                    can_delete = (c.get("email") == email) or is_owner
                    if can_delete:
                        if st.button("🗑️", key=f"del_cmt_{post_id}_{idx}"):
                            try:
                                delete_comment_in_post(post_id, post, idx)
                                st.success("Đã xoá bình luận")
                            except Exception as e:
                                st.error("Lỗi xoá bình luận: " + str(e))
                            st.rerun()
        else:
            st.markdown("_Chưa có bình luận nào._")

        # Add comment input
        c_input_key = f"comment_input_{post_id}"
        comment_text = st.text_input("Viết bình luận...", key=c_input_key)
        if st.button("Gửi", key=f"send_comment_{post_id}") and comment_text.strip():
            comment_obj = {
                "user": username_display,
                "email": email,
                "avatar": avatar_url,
                "content": comment_text.strip(),
                "timestamp": datetime.now().isoformat()
            }
            try:
                add_comment_to_post(post_id, post, comment_obj)
                st.success("Đã gửi bình luận!")
            except Exception as e:
                st.error("Lỗi gửi bình luận: " + str(e))
            st.rerun()

        st.markdown("---")
