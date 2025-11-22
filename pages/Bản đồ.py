import streamlit as st
import json, os, time
import cloudinary, cloudinary.uploader
from email_sender import send_email
from firebase_rest import (
    get_firestore_docs,
    add_firestore_doc,
    update_firestore_doc,
    send_push_notification,
    distance_km
)
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Bản đồ cứu trợ", layout="wide")
st.title("🆘 BẢN ĐỒ CỨU TRỢ KHẨN CẤP")

# ==================== CLOUDINARY ====================
cloudinary.config(
    cloud_name="dwrr9uwy1",
    api_key="258463696593724",
    api_secret="AQuiKKY9UekSC7TAgS9wggXe7CU",
    secure=True
)

# ==================== FIRESTORE HỖ TRỢ ====================
def get_all_requests():
    try:
        docs = get_firestore_docs("rescue_requests")
        # parse images và notified_volunteers
        for d in docs:
            if isinstance(d.get("images"), str):
                d["images"] = json.loads(d["images"].replace("'", '"'))
            if "notified_volunteers" not in d or d["notified_volunteers"] is None:
                d["notified_volunteers"] = []
        return docs
    except Exception as e:
        import traceback
        st.error("🔥 Lỗi khi tải dữ liệu Firestore:")
        st.code(traceback.format_exc())
        return []

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

# ==================== HIỂN THỊ BẢN ĐỒ ====================
data = get_all_requests()
data = [d for d in data if "lat" in d and "lng" in d]
center_lat = float(data[0]["lat"]) if data else 10.762622
center_lng = float(data[0]["lng"]) if data else 106.660172
api_key = "AIzaSyD4KVbyvfBHFpN_ZNn7RrmZG5Qw9C_VbgU"

html_template = f"""
<!DOCTYPE html>
<html>
  <head>
    <style>
      #map {{ height: 600px; width: 100%; border-radius: 10px; }}
      .map-btn {{ display:block; margin-top:5px; padding:6px 10px; background:#007bff; color:white; border:none; border-radius:5px; cursor:pointer; font-size:0.9em; }}
      .map-btn:hover {{ background:#0056b3; }}
      .uploaded-img {{ width:180px; border-radius:8px; margin-top:5px; box-shadow:0 0 5px rgba(0,0,0,0.3); }}
      .popup-overlay {{ position: fixed; top: 0; left: 0; width:100%; height:100%; background:rgba(0,0,0,0.6); display:none; justify-content:center; align-items:center; z-index:9999; }}
      .popup-content {{ background:#fff; border-radius:10px; padding:15px; max-width:600px; width:90%; max-height:90%; overflow-y:auto; box-shadow:0 0 10px rgba(0,0,0,0.5); font-family:'Segoe UI', sans-serif; }}
      .close-popup {{ background:red; color:white; border:none; padding:5px 10px; float:right; border-radius:5px; cursor:pointer; }}
    </style>
  </head>
  <body>
    <div id="map"></div>
    <div id="popup" class="popup-overlay">
      <div class="popup-content" id="popup-content"></div>
    </div>
    <script>
      function initMap() {{
        const center = {{ lat: {center_lat}, lng: {center_lng} }};
        const map = new google.maps.Map(document.getElementById("map"), {{ zoom: 13, center: center }});
        const locations = {json.dumps(data)};
        locations.forEach(loc => {{
          const marker = new google.maps.Marker({{
            position: {{ lat: loc.lat, lng: loc.lng }},
            map: map,
            icon: {{ url: "https://maps.google.com/mapfiles/ms/icons/red-dot.png", scaledSize: new google.maps.Size(40,40) }}
          }});
          const firstImg = loc.images && loc.images.length ? `<img src='${{loc.images[0]}}' class='uploaded-img'><br>` : "";
          const info = new google.maps.InfoWindow({{
            content: `
              <div style="font-family:'Segoe UI',sans-serif;max-width:230px;">
                <b style="font-size:1.1em;">${{loc.name}}</b><br>
                <span style="font-size:0.9em;">🏠 ${{ loc.address || "" }}</span><br>
                ${{firstImg}}
                <div style="font-size:0.9em;color:#222;margin-top:4px;">${{ loc.note || "" }}</div>
                <button class="map-btn" onclick="window.open('tel:${{loc.phone}}')">📞 Gọi ngay</button>
                <button class="map-btn" onclick="window.open('https://www.google.com/maps/dir/?api=1&destination=${{loc.lat}},${{loc.lng}}')">🧭 Đi đến cứu hộ</button>
                <button class="map-btn" onclick='showDetail(${{JSON.stringify(loc)}})'>ℹ️ Chi tiết</button>
              </div>`
          }});
          marker.addListener("click", () => info.open(map, marker));
        }});
      }}
      function showDetail(loc) {{
        let html = `<button class='close-popup' onclick='closePopup()'>Đóng</button>
                    <h2>${{loc.name}}</h2>
                    <p><b>🏠 Địa chỉ:</b> ${{loc.address || 'Không rõ'}}</p>
                    <p><b>📞 SĐT:</b> <a href='tel:${{loc.phone}}'>${{loc.phone}}</a></p>
                    <p><b>📝 Ghi chú:</b> ${{loc.note || ''}}</p>`;
        if (loc.images && loc.images.length) {{
            html += `<div><b>📷 Hình ảnh:</b><br>`;
            loc.images.forEach(img => html += `<img src='${{img}}' style='width:100%;border-radius:10px;margin-top:5px;'>`);
            html += `</div>`;
        }}
        document.getElementById("popup-content").innerHTML = html;
        document.getElementById("popup").style.display = "flex";
      }}
      function closePopup() {{ document.getElementById("popup").style.display = "none"; }}
    </script>
    <script async src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap"></script>
  </body>
</html>
"""
st.components.v1.html(html_template, height=600)

# ==================== FORM GỬI YÊU CẦU ====================
st.markdown("### 🆘 Gửi yêu cầu cứu trợ")

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
                doc = add_firestore_doc("rescue_requests", {
                    "name": name,
                    "phone": phone,
                    "note": note,
                    "address": address,
                    "lat": lat,
                    "lng": lng,
                    "images": img_urls,
                    "status": "pending",
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "notified_volunteers": [],  # Bắt buộc có array rỗng
                })
                rescue_id = doc.get("id") if "id" in doc else doc["name"].split("/")[-1]
                st.success("✅ Gửi yêu cầu thành công!")
            except Exception as e:
                st.error("❌ Lỗi khi lưu yêu cầu: " + str(e))
                doc = None

            # ===== GỬI EMAIL TÌNH NGUYỆN VIÊN =====
            try:
                volunteers = get_all_volunteers()
                nearest_pairs = find_nearest_volunteers(lat, lng, volunteers, limit=3)
                notified = []

                for dist, vol in nearest_pairs:
                    volunteer_email = vol.get("email")
                    volunteer_name = vol.get("name") or vol.get("username") or volunteer_email
                    if not volunteer_email:
                        continue

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

                # ===== UPDATE CHỈ 2 FIELD KHÔNG GHI ĐÈ FIELD KHÁC =====
                if rescue_id:
                    update_firestore_doc(
                        "rescue_requests",
                        rescue_id,
                        {
                            "notified_volunteers": notified,  # list of dict
                            "status": "email_sent" if notified else "no_volunteer"
                        }
                    )

                st.success(f"📧 Đã gửi email tới {len(notified)} tình nguyện viên gần nhất!")

            except Exception as e:
                st.error("❌ Lỗi khi gửi email: " + str(e))
