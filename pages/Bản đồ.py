# streamlit page title: Bản đồ - Những nơi cần cứu trợ
import streamlit as st
import os
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Bản đồ cứu trợ", page_icon="🗺️", layout="wide")

# === Sidebar ===
role = st.session_state.get("role", "Khách")
st.sidebar.success(f"Xin chào, {role.capitalize()} 👋")
if st.sidebar.button("🏠 Quay lại màn hình chính"):
    st.switch_page("Trang chủ.py")

st.title("🗺️ Bản đồ - Những nơi cần cứu trợ")

# === File chứa dữ liệu toạ độ ===
file_path = os.path.join(os.path.dirname(__file__), "data.txt")

# === Đọc danh sách toạ độ đã lưu ===
coordinates = []
if os.path.exists(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    lat, lng, name = line.strip().split(",")
                    coordinates.append({"lat": float(lat), "lng": float(lng), "name": name})
                except:
                    pass

# === Tính trung tâm bản đồ ===
if coordinates:
    center_lat = sum(p["lat"] for p in coordinates) / len(coordinates)
    center_lng = sum(p["lng"] for p in coordinates) / len(coordinates)
else:
    center_lat, center_lng = 10.762622, 106.660172  # TP. Hồ Chí Minh mặc định

# === Giao diện gửi yêu cầu cứu trợ ===
st.markdown("---")
st.subheader("🆘 Gửi yêu cầu cứu trợ")

if "show_form" not in st.session_state:
    st.session_state["show_form"] = False

if not st.session_state["show_form"]:
    if st.button("🆘 Tôi cần cứu trợ"):
        st.session_state["show_form"] = True
        st.rerun()
else:
    st.info("👉 Hãy nhập thông tin để đội cứu trợ có thể tìm đến bạn nhanh nhất.")

    name = st.text_input("👤 Họ và tên của bạn")
    phone = st.text_input("📞 Số điện thoại liên hệ")

    # --- Lấy vị trí tự động ---
    if st.button("📍 Lấy vị trí hiện tại"):
        coords = streamlit_js_eval(
            js_expressions="await new Promise((resolve, reject) => navigator.geolocation.getCurrentPosition(p => resolve([p.coords.latitude, p.coords.longitude]), err => reject(err)));",
            key="get_location"
        )
        if coords:
            st.session_state["lat"] = coords[0]
            st.session_state["lng"] = coords[1]
            st.success(f"✅ Lấy được vị trí: ({coords[0]:.6f}, {coords[1]:.6f})")
        else:
            st.warning("⚠️ Không thể lấy vị trí (có thể bạn đã từ chối GPS).")

    lat = st.number_input("📍 Vĩ độ (latitude)", format="%.6f", value=st.session_state.get("lat", 0.0))
    lng = st.number_input("📍 Kinh độ (longitude)", format="%.6f", value=st.session_state.get("lng", 0.0))
    note = st.text_area("📝 Ghi chú thêm (tình trạng, số người, v.v.)")

    if st.button("✅ Gửi thông tin cứu trợ"):
        if name.strip() and phone.strip() and lat and lng:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(f"{lat},{lng},{name}\n")
            st.success("✅ Thông tin cứu trợ đã được gửi thành công! ❤️")
            # reset form
            st.session_state["show_form"] = False
            st.session_state.pop("lat", None)
            st.session_state.pop("lng", None)
            st.rerun()
        else:
            st.warning("⚠️ Vui lòng nhập đầy đủ thông tin!")

st.markdown("---")

# === Hiển thị bản đồ ===
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
          const marker = new google.maps.Marker({{
            position: {{ lat: loc.lat, lng: loc.lng }},
            map: map,
            icon: {{
              url: "https://maps.google.com/mapfiles/ms/icons/red-dot.png",
              scaledSize: new google.maps.Size(40, 40)
            }}
          }});
          const info = new google.maps.InfoWindow({{
            content: `<b>${{loc.name}}</b>`
          }});
          marker.addListener("click", () => info.open(map, marker));
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
