import streamlit as st
import sqlite3
import json
import os
from pathlib import Path
from streamlit_js_eval import streamlit_js_eval
import cloudinary
import cloudinary.uploader

# ==================== CÀI ĐẶT BAN ĐẦU ====================
st.set_page_config(page_title="Bản đồ cứu trợ", layout="wide")
st.title("🆘 BẢN ĐỒ CỨU TRỢ KHẨN CẤP")

DB_PATH = "rescue.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==================== CẤU HÌNH CLOUDINARY ====================
cloudinary.config(
    cloud_name="dwrr9uwy1",     # 🔁 Thay bằng tên Cloudinary thật của bạn
    api_key="258463696593724",
    api_secret="AQuiKKY9UekSC7TAgS9wggXe7CU",
    secure=True
)

# ==================== KHỞI TẠO DATABASE ====================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS rescue_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            note TEXT,
            address TEXT,
            lat REAL,
            lng REAL,
            images TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ==================== HÀM LẤY DỮ LIỆU ====================
def get_all_requests():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, phone, note, address, lat, lng, images FROM rescue_requests")
    rows = c.fetchall()
    conn.close()
    return [
        {
            "name": r[0],
            "phone": r[1],
            "note": r[2],
            "address": r[3],
            "lat": r[4],
            "lng": r[5],
            "images": json.loads(r[6]) if r[6] else []
        }
        for r in rows
    ]

# ==================== HIỂN THỊ BẢN ĐỒ ====================
st.subheader("🗺️ Bản đồ cứu trợ")

data = get_all_requests()
center_lat = data[0]["lat"] if data else 10.762622
center_lng = data[0]["lng"] if data else 106.660172

# === CSS ===
st.markdown("""
<style>
button.map-btn {
  display:block;
  margin-top:5px;
  padding:6px 10px;
  background:#007bff;
  color:white;
  border:none;
  border-radius:5px;
  cursor:pointer;
  font-size:0.9em;
}
button.map-btn:hover { background:#0056b3; }

.uploaded-img {
  width: 180px;
  border-radius: 8px;
  margin-top: 5px;
  box-shadow: 0 0 5px rgba(0,0,0,0.3);
}
</style>
""", unsafe_allow_html=True)

# === HTML bản đồ có popup chi tiết ===
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
"""

st.components.v1.html(html_template, height=600)

# ==================== FORM GỬI YÊU CẦU ====================
st.markdown('<div id="rescue-form"></div>', unsafe_allow_html=True)
st.markdown("### 🆘 Gửi yêu cầu cứu trợ")

with st.form("rescue_form"):
    name = st.text_input("👤 Họ và tên:")
    phone = st.text_input("📞 Số điện thoại:")
    address = st.text_input("🏠 Địa chỉ (hoặc mô tả vị trí):")
    note = st.text_area("📝 Tình trạng cần cứu trợ (có thể dán link video minh chứng):")

    get_loc = st.form_submit_button("📍 Lấy tọa độ vị trí hiện tại")

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
            try:
                d = json.loads(coords)
                st.session_state["lat"] = d["lat"]
                st.session_state["lng"] = d["lng"]
                st.success(f"✅ Lấy vị trí thành công: ({d['lat']:.6f}, {d['lng']:.6f})")
            except:
                st.warning("⚠️ Lỗi khi đọc dữ liệu vị trí.")
        else:
            st.warning("⚠️ Không thể lấy vị trí (hãy thử lại vài lần).")

    images = st.file_uploader("📸 Ảnh minh chứng (tối đa 3 ảnh):", accept_multiple_files=True)
    submitted = st.form_submit_button("✅ Gửi yêu cầu cứu trợ")

    if submitted:
        lat = st.session_state.get("lat")
        lng = st.session_state.get("lng")

        if not all([name.strip(), phone.strip(), address.strip()]) or lat is None or lng is None:
            st.warning("⚠️ Vui lòng nhập đầy đủ thông tin và lấy tọa độ trước khi gửi!")
        else:
            img_urls = []
            for img in images[:3]:
                upload_result = cloudinary.uploader.upload(
                    img,
                    folder="rescue_uploads",
                    resource_type="image"
                )
                img_urls.append(upload_result["secure_url"])

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""
                INSERT INTO rescue_requests (name, phone, note, address, lat, lng, images)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, phone, note, address, lat, lng, json.dumps(img_urls)))
            conn.commit()
            conn.close()

            st.success("✅ Gửi yêu cầu cứu trợ thành công! Bản đồ sẽ cập nhật sau vài giây.")
            st.session_state.pop("lat", None)
            st.session_state.pop("lng", None)
            st.rerun()
