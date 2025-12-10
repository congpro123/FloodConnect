# ban_do_map.py  
# Phần hiển thị bản đồ cứu trợ – giữ nguyên toàn bộ code bản đồ

import streamlit as st
import json, pprint
from firebase_rest import get_firestore_docs
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Bản đồ cứu trợ", page_icon="assets/logo.png", layout="wide")
st.title("🆘 BẢN ĐỒ CỨU TRỢ KHẨN CẤP")

def get_all_requests():
    try:
        docs = get_firestore_docs("rescue_requests")
        for d in docs:
            if isinstance(d.get("images"), str):
                try:
                    d["images"] = json.loads(d["images"].replace("'", '"'))
                except Exception:
                    d["images"] = []
            if "notified_volunteers" not in d or d["notified_volunteers"] is None:
                d["notified_volunteers"] = []
        return docs
    except Exception:
        return []

raw_data = get_all_requests()
data = []

for d in raw_data:
    try:
        lat = float(d.get("lat"))
        lng = float(d.get("lng"))
    except Exception:
        continue

    doc = dict(d)
    doc["lat"] = lat
    doc["lng"] = lng

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

# Chuẩn hóa trường images (Firestore mapValue → list)
for d in data:
    imgs = d.get("images")
    if isinstance(imgs, dict) and "values" in imgs:
        imgs = [v.get("stringValue") for v in imgs["values"] if "stringValue" in v]
    elif isinstance(imgs, str):
        try:
            imgs = json.loads(imgs.replace("'", '"'))
        except Exception:
            imgs = []
    d["images"] = imgs

pprint.pprint(data[:2])

data_json = json.dumps(data, ensure_ascii=False)

# ============================================================
# TẤT CẢ HTML/JS — có chỉnh sửa đổi màu marker theo status
# ============================================================

html_template = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
body {{
    margin:0;
    font-family: 'Segoe UI', sans-serif;
}}
#map {{
    height: 600px;
    width: 100%;
    border-radius: 10px;
}}
.popup-overlay {{
    position: fixed;
    top: 0;
    left: 0;
    width:100%;
    height:100%;
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
.popup-btn-go   {{ background:#1976d2; }}
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

        // --------------------------------------------------
        // 🌈 ĐỔI MÀU MARKER THEO TRẠNG THÁI
        // --------------------------------------------------
        let color = "rgba(0,128,255,0.9)";   // pending - xanh dương

        if (loc.status === "accepted") {{
            color = "rgba(0,200,0,0.9)";     // accepted - xanh lá
        }} else if (loc.status === "no_volunteer_available") {{
            color = "rgba(120,120,120,0.9)"; // không còn TNV – xám
        }}

        const marker = new google.maps.Marker({{
            position: pos,
            icon: {{
                path: google.maps.SymbolPath.CIRCLE,
                scale: 9,
                fillColor: color,
                fillOpacity: 1,
                strokeWeight: 0
            }},
            title: loc.name || 'Yêu cầu cứu trợ'
        }});

        marker.addListener('click', () => {{
            showDetail(JSON.stringify(loc));
        }});

        markers.push(marker);
    }});

    new markerClusterer.MarkerClusterer({{
        map,
        markers
    }});
}}

function showDetail(locStr) {{
    let loc;
    try {{ loc = JSON.parse(locStr); }}
    catch(e) {{ loc = locStr; }}

    let html = `
        <button class='close-popup' onclick='closePopup()'>Đóng</button>
        <h2>${{loc.name || 'Người cần cứu trợ'}}</h2>
        <p><b>🏠 Địa chỉ:</b> ${{loc.address || 'Không rõ'}}</p>
        <p><b>📞 SĐT:</b> ${{loc.phone || ''}}</p>
        <p><b>📝 Ghi chú:</b> ${{loc.note || ''}}</p>
    `;

    if(loc.images && Array.isArray(loc.images) && loc.images.length) {{
        html += "<div><b>📷 Hình ảnh:</b><br>";
        loc.images.forEach(img => {{
            html += `<img src="${{img}}">`;
        }});
        html += "</div>";
    }}

    html += `
        <div>
            <a href='tel:${{loc.phone || ""}}' class='popup-btn popup-btn-call'>📞 Gọi</a>
            <a href='https://www.google.com/maps/dir/?api=1&destination=${{loc.lat}},${{loc.lng}}' target='_blank' class='popup-btn popup-btn-go'>🗺️ Đi tới</a>
        </div>
    `;

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
