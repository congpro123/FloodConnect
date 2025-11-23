# Ban_do_cuu_tro.py
import streamlit as st
import json, os, time
import pprint
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
        for d in docs:
            # chuẩn hoá images
            if isinstance(d.get("images"), str):
                try:
                    d["images"] = json.loads(d["images"].replace("'", '"'))
                except Exception:
                    d["images"] = []
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
raw_data = get_all_requests()
# chỉ giữ các doc có lat/lng
data = []
for d in raw_data:
    try:
        lat = float(d.get("lat"))
        lng = float(d.get("lng"))
    except Exception:
        continue
    doc = dict(d)  # copy
    doc["lat"] = lat
    doc["lng"] = lng
    # ensure images is a list
    imgs = doc.get("images") or []
    if isinstance(imgs, str):
        try:
            imgs = json.loads(imgs.replace("'", '"'))
        except Exception:
            imgs = []
    doc["images"] = imgs
    data.append(doc)

center_lat = float(data[0]["lat"]) if data else 10.762622
center_lng = float(data[0]["lng"]) if data else 106.660172
api_key = "AIzaSyD4KVbyvfBHFpN_ZNn7RrmZG5Qw9C_VbgU"
for d in data:
    imgs = d.get("images")
    if isinstance(imgs, dict) and "values" in imgs:
        # chuyển kiểu Firestore -> list URL
        imgs = [v.get("stringValue") for v in imgs["values"] if "stringValue" in v]
    elif isinstance(imgs, str):
        try:
            imgs = json.loads(imgs.replace("'", '"'))
        except Exception:
            imgs = []
    d["images"] = imgs
pprint.pprint(data[:2])  # in 2 bản ghi đầu tiên
# prepare json to embed in HTML
data_json = json.dumps(data, ensure_ascii=False)

html_template = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    body {{ margin:0; font-family: 'Segoe UI', sans-serif; }}
    #map {{ height: 600px; width: 100%; border-radius: 10px; }}

    .popup-overlay {{
      position: fixed;
      top: 0; left: 0;
      width:100%; height:100%;
      background:rgba(0,0,0,0.6);
      display:none;
      justify-content:center;
      align-items:center;
      z-index:9999;
    }}

    .popup-content {{
      background:#fff;
      border-radius:10px;
      padding:15px;
      max-width:700px;
      width:92%;
      max-height:90%;
      overflow-y:auto;
      box-shadow:0 0 10px rgba(0,0,0,0.5);
    }}

    .close-popup {{
      background:#d32f2f;
      color:white;
      border:none;
      padding:6px 10px;
      float:right;
      border-radius:6px;
      cursor:pointer;
    }}

    .popup-content h2 {{ margin-top:0; }}
    .popup-content img {{
      max-width:180px;
      display:block;
      margin-top:8px;
      border-radius:8px;
    }}

    .popup-btn {{
      display:inline-block;
      padding:6px 12px;
      border-radius:6px;
      color:white;
      text-decoration:none;
      font-weight:500;
      margin-top:10px;
      margin-right:8px;
      cursor:pointer;
    }}

    .popup-btn-call {{ background:#388e3c; }}
    .popup-btn-go {{ background:#1976d2; }}
  </style>
</head>
<body>
  <div id="map"></div>
  <div id="popup" class="popup-overlay">
    <div class="popup-content" id="popup-content"></div>
  </div>

  <script src="https://unpkg.com/@googlemaps/markerclusterer/dist/index.min.js"></script>
  <script>
    const CENTER = {{ lat: {center_lat}, lng: {center_lng} }};
    const LOCATIONS = {data_json};

    function initMap() {{
      const map = new google.maps.Map(document.getElementById("map"), {{
        zoom: 11,
        center: CENTER,
        mapTypeControl: false
      }});

      const markers = [];

      LOCATIONS.forEach(loc => {{
        const pos = {{ lat: loc.lat, lng: loc.lng }};
        const marker = new google.maps.Marker({{
          position: pos,
          icon: {{
            path: google.maps.SymbolPath.CIRCLE,
            scale: 7,
            fillColor: 'rgba(213, 45, 45, 0.45)',
            fillOpacity: 0.9,
            strokeWeight: 0
          }},
          title: loc.name || 'Yêu cầu cứu trợ'
        }});

        marker.addListener('click', () => {{
          showDetail(JSON.stringify(loc));
        }});

        markers.push(marker);
      }});

      const renderer = {{
        render: ({{ count, position }}) => {{
          const size = Math.max(28, Math.min(110, Math.round(24 + Math.log(count+1)*24)));
          const opacity = Math.max(0.75, Math.min(0.95, 0.75 + Math.log(count+1)*0.22));
          const fillColor = `rgba(213,45,45,${{opacity}})`;

          const svg = `
            <svg xmlns="http://www.w3.org/2000/svg" width="${{size}}" height="${{size}}">
              <circle cx="${{size/2}}" cy="${{size/2}}" r="${{size/2}}" fill="${{fillColor}}" />
              <text x="50%" y="50%" font-size="${{Math.round(size/2.6)}}" fill="#fff" font-weight="700" text-anchor="middle" dominant-baseline="middle">${{count}}</text>
            </svg>
          `;
          const url = 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(svg);
          return new google.maps.Marker({{
            position,
            icon: {{
              url: url,
              scaledSize: new google.maps.Size(size, size),
              anchor: new google.maps.Point(size/2, size/2)
            }},
            optimized: false
          }});
        }}
      }};

      new markerClusterer.MarkerClusterer({{ map, markers, renderer }});
    }}

    function showDetail(locStr) {{
      let loc;
      try {{ loc = JSON.parse(locStr); }} 
      catch(e) {{ loc = locStr; }}

      let html = `<button class='close-popup' onclick='closePopup()'>Đóng</button>
                  <h2>${{loc.name || 'Người cần cứu trợ'}}</h2>
                  <p><b>🏠 Địa chỉ:</b> ${{loc.address || 'Không rõ'}}</p>
                  <p><b>📞 SĐT:</b> ${{loc.phone || ''}}</p>
                  <p><b>📝 Ghi chú:</b> ${{loc.note || ''}}</p>`;

    if(loc.images && Array.isArray(loc.images) && loc.images.length) {{
        html += `<div><b>📷 Hình ảnh:</b><br>`;
        loc.images.forEach(img => {{
            html += `<img src="${{img}}" style="max-width:180px; margin-top:8px; border-radius:8px;">`;
        }});
        html += `</div>`;
    }}

      html += `<div>
                  <a href='tel:${{loc.phone || ""}}' class='popup-btn popup-btn-call'>📞 Gọi</a>
                  <a href='https://www.google.com/maps/dir/?api=1&destination=${{loc.lat}},${{loc.lng}}' target='_blank' class='popup-btn popup-btn-go'>🗺️ Đi tới</a>
               </div>`;

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
st.components.v1.html(html_template, height=650)

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
                    "notified_volunteers": [],  # Bắt buộc có array rỗng
                }
                doc = add_firestore_doc("rescue_requests", payload)
                # doc may return dict with 'id' or name ref
                if isinstance(doc, dict) and "id" in doc:
                    rescue_id = doc.get("id")
                elif isinstance(doc, dict) and "name" in doc:
                    rescue_id = doc["name"].split("/")[-1]
                else:
                    rescue_id = None
                st.success("✅ Gửi yêu cầu thành công!")
            except Exception as e:
                st.error("❌ Lỗi khi lưu yêu cầu: " + str(e))
                doc = None
                rescue_id = None

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
