# ban_do_bao_cao.py
# Phần gửi yêu cầu cứu trợ và báo cáo tới tình nguyện viên

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

st.set_page_config(page_title="Gửi yêu cầu cứu trợ", layout="wide")
st.markdown("### 🆘 Gửi yêu cầu cứu trợ")

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

# ==================== FORM ====================
with st.form("rescue_form"):
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
        coords = streamlit_js_eval(js_expressions=js, key="get_coords")
        if coords and not str(coords).startswith("ERROR"):
            d = json.loads(coords)
            st.session_state["lat"] = d["lat"]
            st.session_state["lng"] = d["lng"]
            st.success(f"✅ Lấy vị trí: ({d['lat']:.6f}, {d['lng']:.6f})")
        else:
            st.warning("⚠️ Không thể lấy vị trí.")

    images = st.file_uploader("📸 Ảnh minh chứng (tối đa 3 ảnh):", accept_multiple_files=True)
    submitted = st.form_submit_button("✅ Gửi yêu cầu cứu trợ")

    if submitted:
        lat = st.session_state.get("lat")
        lng = st.session_state.get("lng")
        if not all([name.strip(), phone.strip(), address.strip()]) or lat is None or lng is None:
            st.warning("⚠️ Vui lòng nhập đủ thông tin & lấy tọa độ!")
        else:
            # ===== UPLOAD ẢNH =====
            img_urls = []
            try:
                for img in images[:3]:
                    upload_result = cloudinary.uploader.upload(img, folder="rescue_uploads", resource_type="image")
                    img_urls.append(upload_result["secure_url"])
            except Exception as e:
                st.warning("⚠️ Lỗi upload ảnh (bỏ qua ảnh). " + str(e))

            # ===== LƯU YÊU CẦU MỚI =====
            try:
                payload = {
                    "name": name,
                    "phone": phone,
                    "note": note,
                    "address": address,
                    "lat": lat,
                    "lng": lng,
                    "images": img_urls,
                    "status": "pending",
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "notified_volunteers": [],
                }
                doc = add_firestore_doc("rescue_requests", payload)
                rescue_id = doc.get("id") if isinstance(doc, dict) and "id" in doc else (doc.get("name").split("/")[-1] if doc.get("name") else None)
                st.success("✅ Gửi yêu cầu thành công!")
            except Exception as e:
                st.error("❌ Lỗi khi lưu yêu cầu: " + str(e))
                doc = rescue_id = None

            # ===== GỬI EMAIL TÌNH NGUYỆN VIÊN =====
            try:
                volunteers = get_all_volunteers()
                nearest_pairs = find_nearest_volunteers(lat, lng, volunteers, limit=3)
                notified = []

                for dist, vol in nearest_pairs:
                    volunteer_email = vol.get("email")
                    volunteer_name = vol.get("name") or vol.get("username") or volunteer_email
                    if not volunteer_email: continue

                    confirm_link = f"http://localhost:8501/rescue_confirm?rid={rescue_id}&vid={vol.get('id')}"
                    subject = "🚨 Cảnh báo cứu trợ khẩn cấp!"
                    body = f"""
Xin chào {volunteer_name},

Một yêu cầu cứu trợ vừa được gửi:

- Người cần hỗ trợ: {name}
- Số điện thoại: {phone}
- Địa chỉ: {address}
- Tọa độ: ({lat}, {lng})
- Ghi chú: {note}

👉 BẤM ĐỂ XÁC NHẬN: {confirm_link}

Trân trọng,
Hệ thống FloodConnect
"""
                    email_result = send_email(volunteer_email, subject, body)
                    notified.append({
                        "volunteer_id": vol.get("id"),
                        "volunteer_email": volunteer_email,
                        "volunteer_name": volunteer_name,
                        "dist_km": round(dist, 2),
                        "email_sent": email_result
                    })

                if rescue_id:
                    update_firestore_doc("rescue_requests", rescue_id, {
                        "notified_volunteers": notified,
                        "status": "email_sent" if notified else "no_volunteer"
                    })
                st.success(f"📧 Đã gửi email tới {len(notified)} tình nguyện viên gần nhất!")

            except Exception as e:
                st.error("❌ Lỗi khi gửi email: " + str(e))
