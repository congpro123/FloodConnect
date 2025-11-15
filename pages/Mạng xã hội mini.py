import streamlit as st
from datetime import datetime
import time
from firebase_rest import get_firestore_docs, add_firestore_doc, update_firestore_doc
import json
from streamlit_js_eval import streamlit_js_eval
from session_manager import init_session
from streamlit_cookies_manager import EncryptedCookieManager
from urllib.parse import urlparse, parse_qs
st.set_page_config(page_title="FloodConnect - Đăng nhập", layout="centered")
# ======================================================
#  COOKIE MANAGER
# ======================================================
cookies = EncryptedCookieManager(
    prefix="floodconnect_",
    password="super-secret-key-123",
)

if not cookies.ready():
    st.stop()


# ======================================================
#  1️⃣ INIT SESSION TRƯỚC (ĐỂ KHÔNG GHI ĐÈ COOKIE SAU)
# ======================================================
init_session()


# ======================================================
#  2️⃣ KHÔI PHỤC TỪ COOKIE
# ======================================================
auth_token = cookies.get("auth_token")

if auth_token:
    st.session_state.logged_in = True
    st.session_state.user_id = cookies.get("user_id")
    st.session_state.user_name = cookies.get("user_name")
    st.session_state.user_role = cookies.get("user_role")
    st.session_state.user_email = cookies.get("user_email")
# st.write("===== DEBUG SESSION =====")
# for k, v in st.session_state.items():
#     st.write(k, ":", v)

# st.write("===== DEBUG COOKIES =====")
# for key in ["auth_token","user_id","user_name","user_role","user_email"]:
#     st.write(key, ":", cookies.get(key))
# ======================================================
#  PAGE CONFIG
# ======================================================
st.set_page_config(page_title="Mạng Xã Hội Mini", layout="centered")

# ======================================================
#  KIỂM TRA LOGIN
# ======================================================
if not st.session_state.logged_in:
    st.warning("⚠️ Bạn chưa đăng nhập. Vui lòng quay lại trang đăng nhập.")
    st.stop()

# session info
username = st.session_state.get("user_name")
email = st.session_state.get("user_email")
avatar_url = "https://cdn-icons-png.flaticon.com/512/149/149071.png"

# === LẤY DỮ LIỆU NGƯỜI DÙNG ===
all_users = get_firestore_docs("users")
user_data = next((u for u in all_users if u.get("email") == email), {})  # tìm user theo email

# Tên hiển thị (fallback khi user chưa đặt name)
display_name = user_data.get("name") or user_data.get("username") or username or "Người dùng"

# ===== SIDEBAR =====
st.sidebar.markdown("## ⚙️ Cài đặt tài khoản")
tab = st.sidebar.radio("", ["Trang chủ", "Cài đặt"])


def logout(cookies: EncryptedCookieManager):
    # ===== 1️⃣ XÓA SESSION STATE =====
    keys_to_clear = [
        "logged_in",
        "user_id",
        "user_name",
        "user_role",
        "user_email",
        "user_avatar",
        "fcm_token",
        "profile_name",
        "profile_email",
        "lat_value",
        "lng_value",
        "pending_lat",
        "pending_lng",
    ]
    for k in keys_to_clear:
        if k in st.session_state:
            del st.session_state[k]

    # ===== 2️⃣ XÓA COOKIES QUAN TRỌNG =====
    cookies_to_clear = [
        "auth_token",
        "user_id",
        "user_name",
        "user_role",
        "user_email",
        "user_avatar",
        "EncryptedCookieManager.key_params",
    ]
    for ck in cookies_to_clear:
        cookies[ck] = ""
    cookies.save()

    # ===== 3️⃣ Rerun app → về trang đăng nhập =====
    st.rerun()
# ====== CÀI ĐẶT TÀI KHOẢN ======
if tab == "Cài đặt":
    if st.button("🔒 Đăng xuất"):
        logout(cookies)
    st.subheader("Chỉnh sửa thông tin cá nhân")

    # --- Khởi tạo state cơ bản nếu chưa có ---
    if "profile_name" not in st.session_state:
        st.session_state.profile_name = user_data.get("name", display_name)
    if "profile_email" not in st.session_state:
        st.session_state.profile_email = user_data.get("email", email)

    # Các key widget chính (lat_value/lng_value) lưu mặc định trước khi tạo widget
    if "lat_value" not in st.session_state:
        try:
            st.session_state.lat_value = float(user_data.get("lat", 0.0))
        except Exception:
            st.session_state.lat_value = 0.0
    if "lng_value" not in st.session_state:
        try:
            st.session_state.lng_value = float(user_data.get("lng", 0.0))
        except Exception:
            st.session_state.lng_value = 0.0

    # --- Nếu có pending tọa độ từ lần bấm trước, áp dụng NGAY LẬP TỨC trước khi tạo widget ---
    # (quan trọng: phải nằm ở đây, trước khi gọi st.number_input(..., key="lat_value"))
    if "pending_lat" in st.session_state and "pending_lng" in st.session_state:
        # Gán vào key widget trước khi widget được khởi tạo
        st.session_state.lat_value = float(st.session_state.pending_lat)
        st.session_state.lng_value = float(st.session_state.pending_lng)
        # Xoá pending để không lặp lại
        del st.session_state["pending_lat"]
        del st.session_state["pending_lng"]
        # Không cần gọi rerun ở đây — tiếp tục flow để widget dùng giá trị mới

    # --- Form nhập ---
    name = st.text_input("Tên hiển thị", key="profile_name")
    email_edit = st.text_input("Email", key="profile_email")
    st.number_input("Vĩ độ", key="lat_value", format="%.6f")
    st.number_input("Kinh độ", key="lng_value", format="%.6f")

    # --- Nút lấy toạ độ ---
    if st.button("📍 Lấy tọa độ hiện tại", key="btn_get_coords"):
        js = """
        new Promise((resolve) => {
            navigator.geolocation.getCurrentPosition(
                pos => resolve(JSON.stringify({
                    lat: pos.coords.latitude,
                    lng: pos.coords.longitude
                })),
                err => resolve("ERROR:" + err.message)
            );
        });
        """
        coords = streamlit_js_eval(js_expressions=js, key="get_coords")
        if coords and not str(coords).startswith("ERROR"):
            try:
                d = json.loads(coords)
                # LƯU VÀO pending — không chạm trực tiếp vào lat_value lúc này
                st.session_state["pending_lat"] = d["lat"]
                st.session_state["pending_lng"] = d["lng"]
                st.success(f"✅ Lấy vị trí thành công: ({d['lat']:.6f}, {d['lng']:.6f})")
                # Bắt buộc rerun để lần chạy kế tiếp gán pending -> widget trước khi render
                st.rerun()
            except Exception as e:
                st.warning(f"⚠️ Lỗi xử lý dữ liệu định vị: {e}")
        else:
            st.warning("⚠️ Không thể lấy vị trí. Hãy đảm bảo bạn đã cho phép quyền truy cập định vị trình duyệt.")

    st.markdown("### 🔔 Thông báo")
    # hiển thị token hiện có (nếu có trong user_data)
    current_token = user_data.get("fcm_token", None)
    if "fcm_token" in st.session_state:
        current_token = st.session_state.fcm_token

    if current_token:
        st.success("✅ Bạn đã bật thông báo (FCM token có).")
        st.write("FCM token (rút gọn):", (current_token[:8] + "...") if isinstance(current_token, str) else current_token)
        if st.button("Xóa token thông báo (tắt thông báo)"):
            # remove token from Firestore
            try:
                if user_data.get("id"):
                    update_firestore_doc("users", user_data["id"], {"fcm_token": ""})
                st.session_state.pop("fcm_token", None)
                st.success("Đã xóa token thông báo.")
                time.sleep(0.8)
                st.rerun()
            except Exception as e:
                st.error("Lỗi khi xóa token: " + str(e))
    else:
        st.info("Chưa cấp quyền thông báo hoặc chưa đăng ký token.")
        if st.button("Kích hoạt thông báo (bật push)"):
            # gọi JS function (firebase-messaging.js) requestNotificationPermission() — hàm này trả về token hoặc null
            try:
                js_code = "window.requestNotificationPermission && window.requestNotificationPermission()"
                token = streamlit_js_eval(js_expressions=js_code, key="request_fcm")
                # streamlit_js_eval trả về token (string) hoặc None
                if token and not str(token).startswith("ERROR"):
                    token_str = str(token)
                    st.session_state.fcm_token = token_str
                    st.success("✅ Lấy token thông báo thành công.")
                    # Lưu token lên Firestore (patch user doc)
                    try:
                        if user_data.get("id"):
                            update_firestore_doc("users", user_data["id"], {"fcm_token": token_str})
                            st.success("✅ Đã lưu token lên server.")
                        else:
                            st.warning("Không tìm thấy user_id để lưu token.")
                    except Exception as e:
                        st.error("Lỗi lưu token lên Firestore: " + str(e))
                else:
                    st.warning("⚠️ Không nhận được token (người dùng có thể đã từ chối).")
            except Exception as e:
                st.error("Lỗi khi gọi JS lấy token: " + str(e))

    st.markdown("---")

    # --- Lưu thay đổi ---
    if st.button("💾 Lưu thay đổi", key="btn_save_profile"):
        password_keep = user_data.get("password", "")
        role_keep = user_data.get("role", "Ẩn danh")
        avatar_keep = user_data.get("avatar", avatar_url)

        # gather values (use current session_state keys)
        lat_to_save = float(st.session_state.get("lat_value", 0.0))
        lng_to_save = float(st.session_state.get("lng_value", 0.0))
        name_to_save = st.session_state.get("profile_name", name)
        email_to_save = st.session_state.get("profile_email", email_edit)

        try:
            if user_data.get("id"):
                update_firestore_doc("users", user_data["id"], {
                    "name": name_to_save,
                    "email": email_to_save,
                    "lat": lat_to_save,
                    "lng": lng_to_save,
                    "avatar": avatar_keep,
                    "password": password_keep,
                    "role": role_keep,
                })
                # Đồng bộ session với thay đổi tên/email
                st.session_state.user_name = name_to_save
                st.session_state.user_email = email_to_save
                st.success("✅ Cập nhật thành công!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Không tìm thấy user_id để cập nhật.")
        except Exception as e:
            st.error("Lỗi khi cập nhật lên Firestore: " + str(e))

# ===== HEADER + LOGOUT =====
current_display_name = st.session_state.get("user_name", display_name)
avatar_url = "https://cdn-icons-png.flaticon.com/512/149/149071.png"


# ===== HEADER UI =====
st.markdown(
    f"""
    <div style='display: flex; justify-content: space-between; align-items: center;
                background-color: #1a73e8; padding: 10px 20px; border-radius: 10px;
                color: white;'>
        <div style='font-size: 24px; font-weight: bold;'>📘 Mạng Xã Hội Mini</div>
        <div style='display: flex; align-items: center; gap: 10px;'>
            <img src='{avatar_url}' width='40' height='40' style='border-radius:50%; border:2px solid white;' />
            <span style='font-size: 18px; font-weight: 500;'>{current_display_name}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# nhúng script để có window.requestNotificationPermission (file bạn đã tạo)
st.markdown(
    """
    <script src="/firebase-messaging.js"></script>
    """,
    unsafe_allow_html=True
)


st.markdown("---")

# ===== TRANG CHỦ =====
if tab == "Trang chủ":
    st.subheader("🖋️ Đăng bài mới")

    content = st.text_area("Bạn đang nghĩ gì?", placeholder="Chia sẻ cảm xúc của bạn...")

    if st.button("Đăng bài", key="btn_post"):
        if content.strip():
            try:
                add_firestore_doc("posts", {
                    "user": st.session_state.get("user_name") or display_name,
                    "email": st.session_state.get("user_email") or email,
                    "avatar": avatar_url,
                    "content": content.strip(),
                    "timestamp": datetime.now().isoformat(),
                })
                st.success("✅ Bài viết đã được đăng!")
                st.rerun()
            except Exception as e:
                st.error("Lỗi khi đăng bài: " + str(e))
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
                <div style='background-color: #8a02de; padding: 15px; border-radius: 12px; margin-bottom: 15px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1); color:white;' >
                    <div style='display: flex; align-items: center; gap: 10px;'>
                        <img src='{post.get("avatar", avatar_url)}' width='40' height='40' style='border-radius:50%; border:1px solid #ddd;' />
                        <div>
                            <strong>{post.get("user", "Ẩn danh")}</strong><br>
                            <span style='font-size:12px; color:#eee;'>{time_posted}</span>
                        </div>
                    </div>
                    <p style='margin-top:10px; font-size:16px;'>{post.get("content","")}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
