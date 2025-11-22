import streamlit as st

def render_single_map(lat, lng, api_key, name="", phone="", note="", image_url=None):
    # ===============================
    # Tạo HTML popup với ảnh nếu có
    # ===============================
    firstImg = f"<img src='{image_url}' class='uploaded-img'><br>" if image_url else ""

    popup_buttons_html = f"""
        <button class='map-btn' onclick="window.open('tel:{phone}')">📞 Gọi ngay</button>
        <button class='map-btn' onclick="window.open('https://www.google.com/maps/dir/?api=1&destination={lat},{lng}')">🧭 Đi đến cứu hộ</button>
        <button class='map-btn' onclick='showDetail({{"name":"{name}","phone":"{phone}","note":"{note}","image":"{image_url}"}})'>ℹ️ Chi tiết</button>
    """

    html_template = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <style>
          #map {{ height: 400px; width: 100%; border-radius: 10px; }}
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
            const map = new google.maps.Map(document.getElementById("map"), {{
              zoom: 13,
              center: {{ lat: {lat}, lng: {lng} }}
            }});

            const marker = new google.maps.Marker({{
              position: {{ lat: {lat}, lng: {lng} }},
              map: map,
              icon: {{ url: "https://maps.google.com/mapfiles/ms/icons/red-dot.png", scaledSize: new google.maps.Size(40,40) }}
            }});

            const info = new google.maps.InfoWindow({{
              content: `
                <div style="font-family:'Segoe UI',sans-serif;max-width:230px;">
                  <b style="font-size:1.1em;">{name}</b><br>
                  <span style="font-size:0.9em;">🏠 </span><br>
                  {firstImg}
                  <div style="font-size:0.9em;color:#222;margin-top:4px;">{note}</div>
                  {popup_buttons_html}
                </div>`
            }});

            marker.addListener("click", () => info.open(map, marker));
          }}

          function showDetail(loc) {{
            let html = `<button class='close-popup' onclick='closePopup()'>Đóng</button>
                        <h2>${{loc.name}}</h2>
                        <p><b>📞 SĐT:</b> <a href='tel:${{loc.phone}}'>${{loc.phone}}</a></p>
                        <p><b>📝 Ghi chú:</b> ${{loc.note}}</p>`;
            if (loc.image) {{
                html += `<div><b>📷 Hình ảnh:</b><br><img src='${{loc.image}}' style='width:100%;border-radius:10px;margin-top:5px;'></div>`;
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

    st.components.v1.html(html_template, height=400)
