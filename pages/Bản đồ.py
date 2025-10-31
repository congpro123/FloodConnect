import streamlit as st
import json, os
import cloudinary, cloudinary.uploader
import firebase_admin
from firebase_admin import credentials, firestore
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Bản đồ cứu trợ", layout="wide")
st.title("🆘 BẢN ĐỒ CỨU TRỢ KHẨN CẤP")

# ==================== KẾT NỐI FIREBASE ====================
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# ==================== CẤU HÌNH CLOUDINARY ====================
cloudinary.config(
    cloud_name="dwrr9uwy1",
    api_key="258463696593724",
    api_secret="AQuiKKY9UekSC7TAgS9wggXe7CU",
    secure=True
)

# ==================== LẤY DỮ LIỆU FIRESTORE ====================
def get_all_requests():
    try:
        docs = db.collection("rescue_requests").get()
        data = []
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            data.append(d)
        st.success(f"✅ Đã tải {len(data)} yêu cầu cứu trợ từ Firestore.")
        return data
    except Exception as e:
        import traceback
        st.error("🔥 Lỗi khi tải dữ liệu Firestore:")
        st.code(traceback.format_exc())
        return []

# ==================== HIỂN THỊ BẢN ĐỒ ====================
data = get_all_requests()
center_lat = data[0]["lat"] if data else 10.762622
center_lng = data[0]["lng"] if data else 106.660172

api_key = "AIzaSyD4KVbyvfBHFpN_ZNn7RrmZG5Qw9C_VbgU"

html_template = f"""
<!DOCTYPE html>
<html>
  <head>
    <style>
      #map {{
        height: 600px;
        width: 100%;
        border-radius: 10px;
      }}
      .map-btn {{
        display:block;
        margin-top:5px;
        padding:6px 10px;
        background:#007bff;
        color:white;
        border:none;
        border-radius:5px;
        cursor:pointer;
        font-size:0.9em;
      }}
      .map-btn:hover {{ background:#0056b3; }}
      .uploaded-img {{
        width: 180px;
        border-radius: 8px;
        margin-top: 5px;
        box-shadow: 0 0 5px rgba(0,0,0,0.3);
      }}
      .popup-overlay {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.6);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
      }}
      .popup-content {{
        background: #fff;
        border-radius: 10px;
        padding: 15px;
        max-width: 600px;
        width: 90%;
        max-height: 90%;
        overflow-y: auto;
        box-shadow: 0 0 10px rgba(0,0,0,0.5);
        font-family: 'Segoe UI', sans-serif;
      }}
      .popup-content video {{
        width: 100%;
        border-radius: 10px;
        margin-top: 10px;
      }}
      .close-popup {{
        background: red;
        color: white;
        border: none;
        padding: 5px 10px;
        float: right;
        border-radius: 5px;
        cursor: pointer;
      }}
    </style>
  </head>
  <body>
    <div id="map"></div>

    <div id="popup" class="popup-overlay" style="display:none;">
      <div class="popup-content" id="popup-content"></div>
    </div>

    <script>
      function initMap() {{
        const center = {{ lat: {center_lat}, lng: {center_lng} }};
        const map = new google.maps.Map(document.getElementById("map"), {{
          zoom: 13,
          center: center,
        }});

        const locations = {json.dumps(data)};

        locations.forEach(loc => {{
          const marker = new google.maps.Marker({{
            position: {{ lat: loc.lat, lng: loc.lng }},
            map: map,
            icon: {{
              url: "https://maps.google.com/mapfiles/ms/icons/red-dot.png",
              scaledSize: new google.maps.Size(40, 40)
            }}
          }});

          const firstImg = loc.images && loc.images.length
              ? `<img src='${{loc.images[0]}}' class='uploaded-img'><br>` : "";

          const info = new google.maps.InfoWindow({{
              content: `
              <div style="font-family:'Segoe UI',sans-serif;max-width:230px;">
                <b style="font-size:1.1em;">${{loc.name}}</b><br>
                <span style="font-size:0.9em;">🏠 ${{loc.address || ""}}</span><br>
                ${{firstImg}}
                <div style="font-size:0.9em;color:#222;margin-top:4px;">${{loc.note || ""}}</div>
                <button class="map-btn" onclick="window.open('tel:${{loc.phone}}')">📞 Gọi ngay</button>
                <button class="map-btn" onclick="window.open('https://www.google.com/maps/dir/?api=1&destination=${{loc.lat}},${{loc.lng}}')">🧭 Đi đến cứu hộ</button>
                <button class="map-btn" onclick='showDetail(${{JSON.stringify(loc)}})'>ℹ️ Chi tiết</button>
              </div>`
          }});
          marker.addListener("click", () => info.open(map, marker));
        }});
      }}

      function showDetail(loc) {{
        let html = `
          <button class='close-popup' onclick='closePopup()'>Đóng</button>
          <h2>${{loc.name}}</h2>
          <p><b>🏠 Địa chỉ:</b> ${{loc.address || 'Không rõ'}}</p>
          <p><b>📞 SĐT:</b> <a href='tel:${{loc.phone}}'>${{loc.phone}}</a></p>
          <p><b>📝 Ghi chú:</b> ${{loc.note || ''}}</p>
        `;

        // ✅ Hiển thị ảnh upload
        if (loc.images && loc.images.length) {{
          html += `<div><b>📷 Hình ảnh:</b><br>`;
          loc.images.forEach(img => {{
            html += `<img src='${{img}}' style='width:100%;border-radius:10px;margin-top:5px;'>`;
          }});
          html += `</div>`;
        }}

        document.getElementById("popup-content").innerHTML = html;
        document.getElementById("popup").style.display = "flex";
      }}

      function closePopup() {{
        document.getElementById("popup").style.display = "none";
      }}
    </script>

    <script async src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap"></script>
  </body>
</html>
"""  # (Phần HTML bản đồ giữ nguyên như bạn gửi)

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
            img_urls = []
            for img in images[:3]:
                upload_result = cloudinary.uploader.upload(img, folder="rescue_uploads", resource_type="image")
                img_urls.append(upload_result["secure_url"])

            db.collection("rescue_requests").add({
                "name": name, "phone": phone, "note": note,
                "address": address, "lat": lat, "lng": lng, "images": img_urls
            })
            st.success("✅ Gửi yêu cầu thành công!")
            st.session_state.pop("lat", None)
            st.session_state.pop("lng", None)
            st.rerun()
