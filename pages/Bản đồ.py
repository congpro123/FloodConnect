# streamlit page title: Bản đồ - Những nơi cần cứu trợ
import streamlit as st
import os

# Hiển thị lời chào
role = st.session_state.get("role", "Khách")
st.sidebar.success(f"Xin chào, {role.capitalize()} 👋")
if st.sidebar.button("🏠 Quay lại màn hình chính"):
    st.switch_page("Trang chủ.py")

st.title("🗺️ Google Map hiển thị từ file TXT")

# --- phần đọc file data.txt ---
file_path = os.path.join(os.path.dirname(__file__), "data.txt")
coordinates = []
with open(file_path, "r") as f:
    for line in f:
        if line.strip():
            lat, lng = map(float, line.strip().split(","))
            coordinates.append({"lat": lat, "lng": lng})

center_lat = sum(p["lat"] for p in coordinates) / len(coordinates)
center_lng = sum(p["lng"] for p in coordinates) / len(coordinates)

# --- phần HTML bản đồ ---
html_code = f"""
<!DOCTYPE html>
<html>
  <head>
    <style>
      #map {{
        height: 600px;
        width: 100%;
        border-radius: 10px;
      }}
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

        const locations = {coordinates};

        locations.forEach(loc => {{
          new google.maps.Marker({{
            position: loc,
            map: map,
            icon: {{
              url: "https://maps.google.com/mapfiles/ms/icons/red-dot.png",
              scaledSize: new google.maps.Size(40, 40)
            }}
          }});
        }});
      }}
    </script>
    <script async
      src="https://maps.googleapis.com/maps/api/js?key=AIzaSyD4KVbyvfBHFpN_ZNn7RrmZG5Qw9C_VbgU&callback=initMap">
    </script>
  </body>
</html>
"""

st.components.v1.html(html_code, height=600)
