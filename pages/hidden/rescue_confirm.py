import streamlit as st
from datetime import datetime
from firebase_rest import get_firestore_docs, update_firestore_doc
from email_sender import send_email
from ban_do_embed import render_single_map  # bản đồ đã có popup với nút

st.set_page_config(page_title="Xác nhận cứu trợ")

# =============================
# LẤY QUERY PARAMS API
# =============================
params = st.query_params
rid = params.get("rid")
vid = params.get("vid")

if not rid or not vid:
    st.error("Thiếu thông tin. Vui lòng mở link xác nhận hợp lệ.")
    st.stop()

# =============================
# HÀM CHUYỂN FIRESTORE MAP → PYTHON DICT
# =============================
def parse_firestore_volunteer(v):
    if not isinstance(v, dict):
        return {}
    fields = v.get("fields") or {}
    def get_value(field):
        if "stringValue" in field:
            return field["stringValue"]
        elif "booleanValue" in field:
            return field["booleanValue"]
        elif "doubleValue" in field:
            return field["doubleValue"]
        elif "arrayValue" in field:
            return [get_value(x) for x in field["arrayValue"].get("values", [])]
        elif "mapValue" in field:
            return parse_firestore_volunteer(field["mapValue"])
        else:
            return None
    return {k: get_value(vv) for k, vv in fields.items()}

# =============================
# TÌM DOCUMENT RESCUE BY ID
# =============================
def find_rescue_request_by_id(rid):
    try:
        docs = get_firestore_docs("rescue_requests")
        for d in docs:
            if d.get("id") == rid or d.get("doc_id") == rid:
                return d
            name_path = d.get("name") or ""
            if name_path.endswith("/" + rid):
                return d
    except Exception as e:
        st.error("Lỗi khi đọc Firestore: " + str(e))
    return None

req = find_rescue_request_by_id(rid)
if not req:
    st.error("Không tìm thấy yêu cầu cứu trợ.")
    st.stop()

# =============================
# HIỂN THỊ THÔNG TIN
# =============================
st.title("🚨 Xác nhận tham gia cứu trợ")
st.markdown(f"**Người cần cứu trợ:** {req.get('name','Không rõ')}")
st.markdown(f"**Số điện thoại:** {req.get('phone','Không rõ')}")
st.markdown(f"**Địa chỉ:** {req.get('address','Không rõ')}")
st.markdown(f"**Ghi chú:** {req.get('note','')}")
st.markdown(f"**Tọa độ:** {req.get('lat','')}, {req.get('lng','')}")
lat = float(req.get("lat"))
lng = float(req.get("lng"))
api = "AIzaSyD4KVbyvfBHFpN_ZNn7RrmZG5Qw9C_VbgU"

# =============================
# HIỂN THỊ MAP VỚI POPUP
# =============================
image_url = req["images"][0] if req.get("images") else None
render_single_map(
    lat,
    lng,
    api,
    name=req.get("name", ""),
    phone=req.get("phone", ""),
    note=req.get("note", ""),
    image_url=image_url
)

st.markdown("---")
st.markdown(f"Bạn là tình nguyện viên ID: **{vid}**")
st.markdown("---")

# =============================
# GHI CẬP NHẬT FIRESTORE
# =============================
def write_req_updates(updates):
    try:
        update_firestore_doc("rescue_requests", rid, updates)
    except Exception as e:
        st.error("Lỗi khi cập nhật Firestore: " + str(e))

def normalize_volunteer(v):
    if isinstance(v, dict):
        if "mapValue" in v:
            return parse_firestore_volunteer(v["mapValue"])
        return v
    elif isinstance(v, str):
        return {"volunteer_id": v, "status": "pending"}
    else:
        return {}

# =============================
# GỬI EMAIL CHO NGƯỜI TIẾP THEO
# =============================
def send_to_next_volunteer(req_doc, current_vid):
    raw_notified = req_doc.get("notified_volunteers", [])
    notified = [normalize_volunteer(v) for v in raw_notified]

    pending = [v for v in notified if str(v.get("volunteer_id")) != str(current_vid)
               and v.get("status") != "accepted"]

    if not pending:
        return False, None

    next_vol = pending[0]
    next_vid = next_vol.get("volunteer_id")
    next_email = next_vol.get("volunteer_email") or next_vol.get("email")

    if not next_email:
        notified = [v for v in notified if str(v.get("volunteer_id")) != str(next_vid)]
        write_req_updates({"notified_volunteers": notified})
        req_doc["notified_volunteers"] = notified
        return send_to_next_volunteer(req_doc, current_vid)

    confirm_link = f"http://localhost:8501/rescue_confirm?rid={rid}&vid={next_vid}"
    subject = "🚨 Cứu trợ khẩn cấp — Xin bạn hỗ trợ"
    body = f"""
Xin chào,

Một yêu cầu cứu trợ khẩn cấp vừa được gửi:

• Người cần hỗ trợ: {req_doc.get('name')}
• Số điện thoại: {req_doc.get('phone')}
• Địa chỉ: {req_doc.get('address')}
• Tọa độ: ({req_doc.get('lat')}, {req_doc.get('lng')})
• Ghi chú: {req_doc.get('note')}

👉 Xác nhận tại: {confirm_link}

Nếu bạn không thể tham gia, hãy bỏ qua email này.
"""
    sent = send_email(next_email, subject, body)

    if sent:
        for v in notified:
            if str(v.get("volunteer_id")) == str(next_vid):
                v["status"] = "email_sent"
                v["last_email_sent_at"] = datetime.now().isoformat()
        write_req_updates({"notified_volunteers": notified})
        return True, next_vid
    else:
        notified = [v for v in notified if str(v.get("volunteer_id")) != str(next_vid)]
        write_req_updates({"notified_volunteers": notified})
        req_doc["notified_volunteers"] = notified
        return send_to_next_volunteer(req_doc, current_vid)

# =============================
# NÚT ACCEPT / DECLINE
# =============================
col1, col2 = st.columns(2)

with col1:
    if st.button("✅ Tôi nhận nhiệm vụ"):
        raw_notified = req.get("notified_volunteers", [])
        notified = [normalize_volunteer(v) for v in raw_notified]
        for v in notified:
            if str(v.get("volunteer_id")) == str(vid):
                v["status"] = "accepted"
                v["accepted_at"] = datetime.now().isoformat()

        write_req_updates({
            "status": "accepted",
            "accepted_by": vid,
            "accepted_at": datetime.now().isoformat(),
            "notified_volunteers": notified
        })
        st.success("Cảm ơn bạn! Bạn đã nhận nhiệm vụ.")
        st.stop()

with col2:
    if st.button("❌ Tôi không thể tham gia"):
        raw_notified = req.get("notified_volunteers", [])
        notified = [normalize_volunteer(v) for v in raw_notified]
        for v in notified:
            if str(v.get("volunteer_id")) == str(vid):
                v["status"] = "declined"

        write_req_updates({"notified_volunteers": notified})

        req_latest = find_rescue_request_by_id(rid)
        sent, next_vid = send_to_next_volunteer(req_latest, vid)

        if sent:
            st.success("Đã gửi yêu cầu đến tình nguyện viên tiếp theo.")
        else:
            write_req_updates({"status": "no_volunteer_available"})
            st.warning("Không còn tình nguyện viên nào để gửi tiếp.")
        st.stop()
