import streamlit as st
import sqlite3
import json
import os
from streamlit_js_eval import streamlit_js_eval

# ==================== CÀI ĐẶT BAN ĐẦU ====================
st.set_page_config(page_title="Bản đồ cứu trợ", layout="wide")
# --- Tự động cuộn xuống phần gửi cứu trợ nếu có tham số ---
params = st.query_params

if params.get("scroll") == ["form"]:
    st.components.v1.html("""
        <script>
        window.addEventListener("load", () => {
            setTimeout(() => {
                const form = document.getElementById("rescue-form");
                if (form) {
                    form.scrollIntoView({behavior: "smooth", block: "center"});
                    form.style.transition = "box-shadow 0.3s ease";
                    form.style.boxShadow = "0 0 20px gold";
                    setTimeout(() => form.style.boxShadow = "none", 1500);
                }
            }, 600);
        });
        </script>
    """, height=0)
DB_PATH = "rescue.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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

# chạy ngay lập tức để đảm bảo có bảng
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
api_key = "AIzaSyD4KVbyvfBHFpN_ZNn7RrmZG5Qw9C_VbgU"  # 🔑 thay bằng API key thật

html_template = f"""
<!DOCTYPE html>
<html>
  <head>
    <style>
      #map {{ height: 600px; width: 100%; border-radius: 10px; }}
      img.marker-img {{ width: 180px; border-radius: 8px; margin-top: 5px; }}
      button.map-btn {{
        display: block; margin-top: 5px; padding: 6px 10px;
        background: #007bff; color: white; border: none;
        border-radius: 5px; cursor: pointer;
      }}
      button.map-btn:hover {{ background: #0056b3; }}
    </style>
  </head>
  <body>
    <div id="map"></div>
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
              ? `<img src="uploads/${{loc.images[0]}}" class='marker-img'><br>` : "";
          const info = new google.maps.InfoWindow({{
              content: `
                <b>${{loc.name}}</b><br>
                🏠 ${{loc.address || ""}}<br>
                ${{firstImg}}
                ${{loc.note || ""}}<br>
                <button class="map-btn" onclick="window.open('tel:${{loc.phone}}')">📞 Gọi ngay</button>
                <button class="map-btn" onclick="window.open('https://www.google.com/maps/dir/?api=1&destination=${{loc.lat}},${{loc.lng}}')">🧭 Đi đến cứu hộ</button>
                ${{loc.images && loc.images.length > 1 ? `<button class='map-btn' onclick='showImages("uploads", ${{JSON.stringify(loc.images)}})'>📷 Xem thêm ảnh</button>` : ""}}
              `
          }});
          marker.addListener("click", () => info.open(map, marker));
        }});
      }}

      function showImages(basePath, images) {{
        let html = images.map(img => `<img src='${{basePath}}/${{img}}' style='width:100%;border-radius:10px;margin-bottom:5px;'>`).join('');
        const w = window.open('', '_blank', 'width=400,height=600,scrollbars=yes');
        w.document.write(`<title>Ảnh cứu trợ</title><body style='margin:10px;font-family:sans-serif;'>${{html}}</body>`);
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
    note = st.text_area("📝 Tình trạng cần cứu trợ:")

    # --- Nút lấy tọa độ tự động ---
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
            st.warning("⚠️ Không thể lấy vị trí (Hãy thử bấm liên tục thật nhanh).")

    images = st.file_uploader("📸 Ảnh minh chứng (tối đa 3 ảnh):", accept_multiple_files=True)
    submitted = st.form_submit_button("✅ Gửi yêu cầu cứu trợ")

    if submitted:
        lat = st.session_state.get("lat", None)
        lng = st.session_state.get("lng", None)

        if not all([name.strip(), phone.strip(), address.strip()]) or lat is None or lng is None:
            st.warning("⚠️ Vui lòng nhập đầy đủ thông tin và lấy tọa độ trước khi gửi!")
        else:
            img_paths = []
            for img in images[:3]:
                path = os.path.join(UPLOAD_DIR, img.name)
                with open(path, "wb") as f:
                    f.write(img.getbuffer())
                img_paths.append(img.name)

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""
                INSERT INTO rescue_requests (name, phone, note, address, lat, lng, images)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, phone, note, address, lat, lng, json.dumps(img_paths)))
            conn.commit()
            conn.close()

            st.success("✅ Gửi yêu cầu cứu trợ thành công! Bản đồ sẽ cập nhật sau vài giây.")
            st.session_state.pop("lat", None)
            st.session_state.pop("lng", None)
            st.rerun()
