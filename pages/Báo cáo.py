# ban_do_bao_cao.py
# Phần gửi yêu cầu cứu trợ & gửi NHỜ báo cáo

import streamlit as st
import time, json
import cloudinary, cloudinary.uploader
from email_sender import send_email
from firebase_rest import (
    get_firestore_docs,
    add_firestore_doc,
    update_firestore_doc,
    distance_km
)
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Gửi yêu cầu cứu trợ", page_icon="assets/logo.png", layout="wide")
st.markdown("### 🆘 Hệ thống báo cáo cứu trợ")

# ==================== CLOUDINARY ====================
cloudinary.config(
    cloud_name="dwrr9uwy1",
    api_key="258463696593724",
    api_secret="AQuiKKY9UekSC7TAgS9wggXe7CU",
    secure=True
)

# ==================== FIRESTORE HỖ TRỢ ====================
def get_all_volunteers():
    try:
        users = get_firestore_docs("users")
        volunteers = [u for u in users if (u.get("role") == "Tình nguyện viên")]
        if volunteers:
            return volunteers
    except Exception:
        pass
    try:
        return get_firestore_docs("volunteers")
    except Exception:
        return []

def find_nearest_volunteers(lat, lng, volunteers, limit=3):
    lst = []
    for v in volunteers:
        try:
            v_lat = float(v.get("lat", 0))
            v_lng = float(v.get("lng", 0))
            dist = distance_km(lat, lng, v_lat, v_lng)
            lst.append((dist, v))
        except Exception:
            continue
    lst.sort(key=lambda x: x[0])
    return lst[:limit]


# ==================== XỬ LÝ GỬI YÊU CẦU / BÁO CÁO ====================
def handle_rescue_submission(name, phone, address, note, lat, lng, images):
    if not all([name.strip(), phone.strip(), address.strip()]):
        st.warning("⚠️ Vui lòng nhập đầy đủ thông tin!")
        return

    # ===== UPLOAD ẢNH =====
    img_urls = []
    try:
        for img in images[:3]:
            upload_result = cloudinary.uploader.upload(
                img, folder="rescue_uploads", resource_type="image"
            )
            img_urls.append(upload_result["secure_url"])
    except Exception as e:
        st.warning("⚠️ Lỗi upload ảnh, bỏ qua ảnh. " + str(e))

    # ===== LƯU FIRESTORE =====
    try:
        payload = {
            "name": name,
            "phone": phone,
            "address": address,
            "note": note,
            "lat": lat,
            "lng": lng,
            "images": img_urls,
            "status": "pending",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "notified_volunteers": [],
        }

        doc = add_firestore_doc("rescue_requests", payload)
        rescue_id = doc.get("id") if isinstance(doc, dict) else None
        st.success("✅ Đã gửi yêu cầu thành công!")
    except Exception as e:
        st.error("❌ Lỗi khi lưu yêu cầu: " + str(e))
        return

    # ===== GỬI EMAIL =====
    try:
        volunteers = get_all_volunteers()
        nearest_pairs = find_nearest_volunteers(lat, lng, volunteers, limit=3)
        notified = []

        for dist, vol in nearest_pairs:
            volunteer_email = vol.get("email")
            volunteer_name = vol.get("name") or vol.get("username") or volunteer_email
            if not volunteer_email:
                continue

            confirm_link = f"http://floodconnect.streamlit.app/hidden/rescue_confirm?rid={rescue_id}&vid={vol.get('id')}"

            subject = "🚨 Cảnh báo cứu trợ khẩn cấp!"
            body = f"""
Một trường hợp cứu trợ vừa được báo:

- Người gặp nạn: {name}
- Số điện thoại: {phone}
- Địa chỉ: {address}
- Tọa độ: ({lat}, {lng})
- Ghi chú: {note}

👉 Xác nhận xử lý: {confirm_link}
"""

            email_result = send_email(volunteer_email, subject, body)
            notified.append({
                "volunteer_id": vol.get("id"),
                "volunteer_email": volunteer_email,
                "volunteer_name": volunteer_name,
                "dist_km": round(dist, 2),
                "email_sent": email_result
            })

        update_firestore_doc("rescue_requests", rescue_id, {
            "notified_volunteers": notified,
            "status": "email_sent" if notified else "no_volunteer"
        })

        st.success(f"📧 Đã gửi email tới {len(notified)} tình nguyện viên gần nhất!")
    except Exception as e:
        st.error("❌ Lỗi khi gửi email: " + str(e))



# ==================== GIAO DIỆN TAB ====================
tab1, tab2 = st.tabs(["🆘 Gửi yêu cầu cứu trợ", "📞 Gửi NHỜ báo cáo (người thân)"])



# =====================================================
#  TAB 1 — GỬI YÊU CẦU CỨU TRỢ
# =====================================================
with tab1:
    with st.form("rescue_form"):
        st.subheader("🆘 Gửi yêu cầu cứu trợ")

        name = st.text_input("👤 Họ và tên:")
        phone = st.text_input("📞 Số điện thoại:")
        address = st.text_input("🏠 Địa chỉ:")
        note = st.text_area("📝 Ghi chú:")

        get_loc = st.form_submit_button("📍 Lấy tọa độ hiện tại")

        if get_loc:
            js = """
            new Promise((resolve) => {
                navigator.geolocation.getCurrentPosition(
                    pos => resolve(JSON.stringify({ lat: pos.coords.latitude, lng: pos.coords.longitude })),
                    err => resolve("ERROR:" + err.message)
                );
            });
            """
            coords = streamlit_js_eval(js_expressions=js, key="get_coords_1")
            if coords and not str(coords).startswith("ERROR"):
                d = json.loads(coords)
                st.session_state["lat"] = d["lat"]
                st.session_state["lng"] = d["lng"]
                st.success(f"📍 Vị trí: ({d['lat']:.6f}, {d['lng']:.6f})")
            else:
                st.warning("⚠️ Không thể lấy vị trí.")

        images = st.file_uploader("📸 Ảnh minh chứng (tối đa 3 ảnh):", accept_multiple_files=True)

        submitted = st.form_submit_button("🚨 Gửi yêu cầu cứu trợ")

        if submitted:
            lat = st.session_state.get("lat")
            lng = st.session_state.get("lng")
            if lat is None or lng is None:
                st.warning("⚠️ Vui lòng nhấn 'Lấy tọa độ hiện tại' trước!")
            else:
                handle_rescue_submission(name, phone, address, note, lat, lng, images)



# =====================================================
#  TAB 2 — GỬI NHỜ BÁO CÁO (NGƯỜI THÂN GỬI HỘ)
# =====================================================
with tab2:
    with st.form("proxy_form"):
        st.subheader("📞 Người thân gửi NHỜ báo cáo")

        reporter = st.text_input("👤 Tên người gửi báo cáo:")
        victim_name = st.text_input("🆘 Tên người gặp nạn:")
        phone = st.text_input("📞 Số điện thoại nạn nhân:")
        address = st.text_input("🏠 Địa chỉ nơi gặp nạn:")

        col1, col2 = st.columns(2)
        with col1:
            lat = st.text_input("🌐 Vĩ độ (Latitude) (nếu có):")
        with col2:
            lng = st.text_input("🌐 Kinh độ (Longitude) (nếu có):")

        auto_loc = st.form_submit_button("📍 Lấy tọa độ GPS (nếu người thân đang tại hiện trường)")

        if auto_loc:
            js = """
            new Promise((resolve) => {
                navigator.geolocation.getCurrentPosition(
                    pos => resolve(JSON.stringify({ lat: pos.coords.latitude, lng: pos.coords.longitude })),
                    err => resolve("ERROR:" + err.message)
                );
            });
            """
            coords = streamlit_js_eval(js_expressions=js, key="get_coords_2")
            if coords and not str(coords).startswith("ERROR"):
                d = json.loads(coords)
                lat = str(d["lat"])
                lng = str(d["lng"])
                st.success(f"📍 Vị trí người thân: ({lat}, {lng})")
            else:
                st.warning("⚠️ Không thể lấy vị trí.")

        note = st.text_area("📝 Ghi chú thêm:")

        images = st.file_uploader("📸 Ảnh minh chứng:", accept_multiple_files=True)

        submitted2 = st.form_submit_button("📨 Gửi NHỜ báo cáo")

        if submitted2:
            try:
                lat_val = float(lat)
                lng_val = float(lng)
            except:
                st.error("⚠️ Tọa độ không hợp lệ!")
                st.stop()

            final_note = f"[Nhờ báo cáo bởi: {reporter}]\n{note}"

            handle_rescue_submission(victim_name, phone, address, final_note, lat_val, lng_val, images)
