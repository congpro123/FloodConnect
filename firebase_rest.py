import json
import requests
import time
import os
import google.auth.crypt
import google.auth.jwt

try:
    import streamlit as st
except ImportError:
    st = None

# ======================================================
# 1) TẢI SERVICE ACCOUNT KEY
# ======================================================
def load_firebase_key():
    """
    Ưu tiên:
    - firebase_key.json (file local)
    - st.secrets["firebase"] (Streamlit Cloud)
    """
    if os.path.exists("firebase_key.json"):
        with open("firebase_key.json", "r", encoding="utf-8") as f:
            return json.load(f)

    if st and "firebase" in st.secrets:
        return dict(st.secrets["firebase"])

    raise FileNotFoundError("❌ Không tìm thấy firebase_key.json hoặc st.secrets['firebase'].")


_key_cache = None

def get_key():
    global _key_cache
    if _key_cache is None:
        _key_cache = load_firebase_key()
    return _key_cache


# ======================================================
# 2) TẠO ACCESS TOKEN CHO FIRESTORE
# ======================================================
def get_access_token():
    key = get_key()
    signer = google.auth.crypt.RSASigner.from_service_account_info(key)
    now = int(time.time())

    payload = {
        "iss": key["client_email"],
        "scope": "https://www.googleapis.com/auth/cloud-platform",
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now,
        "exp": now + 3600,
    }

    jwt_ = google.auth.jwt.encode(signer, payload)
    jwt_str = jwt_.decode("utf-8") if isinstance(jwt_, bytes) else jwt_

    r = requests.post(
        "https://oauth2.googleapis.com/token",
        data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": jwt_str},
    )

    data = r.json()
    if "access_token" not in data:
        raise RuntimeError(f"❌ Không tạo được access_token: {data}")

    return data["access_token"]


# ======================================================
# 3) FIRESTORE → LẤY COLLECTION
# ======================================================
def get_firestore_docs(collection: str):
    key = get_key()
    token = get_access_token()

    url = f"https://firestore.googleapis.com/v1/projects/{key['project_id']}/databases/(default)/documents/{collection}"
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"})

    if not r.ok:
        raise RuntimeError(f"❌ Lỗi truy cập Firestore: {r.status_code} - {r.text}")

    data = r.json()
    docs = []

    for doc in data.get("documents", []):
        fields = doc["fields"]
        parsed = {}
        for k, v in fields.items():
            parsed[k] = list(v.values())[0]
        parsed["id"] = doc["name"].split("/")[-1]
        docs.append(parsed)

    return docs


# ======================================================
# Chuyển Python object sang Firestore field value
# ======================================================
def convert_to_firestore_value(v):
    """Chuyển Python object sang Firestore field value Firestore"""
    if isinstance(v, str):
        return {"stringValue": v}
    elif isinstance(v, bool):
        return {"booleanValue": v}
    elif isinstance(v, (int, float)):
        return {"doubleValue": v}
    elif isinstance(v, list):
        return {"arrayValue": {"values": [convert_to_firestore_value(x) for x in v]}}
    elif isinstance(v, dict):
        return {"mapValue": {"fields": {k: convert_to_firestore_value(val) for k, val in v.items()}}}
    else:
        # fallback: lưu dưới dạng string
        return {"stringValue": str(v)}

# ======================================================
# FIRESTORE → THÊM DOCUMENT (AUTO-ID)
# ======================================================
def add_firestore_doc(collection: str, data: dict):
    key = get_key()
    token = get_access_token()

    url = f"https://firestore.googleapis.com/v1/projects/{key['project_id']}/databases/(default)/documents/{collection}"

    fields = {k: convert_to_firestore_value(v) for k, v in data.items()}

    r = requests.post(url, headers={"Authorization": f"Bearer {token}"}, json={"fields": fields})

    if not r.ok:
        raise RuntimeError(f"❌ Lỗi thêm tài liệu: {r.status_code} - {r.text}")

    return r.json()

# ======================================================
# FIRESTORE → UPDATE DOCUMENT (PATCH)
# ======================================================
def update_firestore_doc(collection: str, doc_id: str, data: dict):
    key = get_key()
    token = get_access_token()

    url = f"https://firestore.googleapis.com/v1/projects/{key['project_id']}/databases/(default)/documents/{collection}/{doc_id}"

    fields = {k: convert_to_firestore_value(v) for k, v in data.items()}
    field_paths = "&".join(f"updateMask.fieldPaths={k}" for k in data.keys())

    r = requests.patch(f"{url}?{field_paths}", headers={"Authorization": f"Bearer {token}"}, json={"fields": fields})

    if not r.ok:
        raise RuntimeError(f"❌ Lỗi cập nhật tài liệu: {r.status_code} - {r.text}")

    return r.json()

# ======================================================
# 6) FIREBASE CLOUD MESSAGING – PUSH NOTIFICATION
# ======================================================
def send_push_notification(fcm_token: str, title: str, body: str, click_url: str = "/"):
    """
    Gửi thông báo trực tiếp đến client (volunteer).
    Yêu cầu:
        - Client phải đăng ký FCM token từ firebase-messaging.js
        - Bạn cần tạo key "server_key" trong firebase_key.json hoặc st.secrets
    """

    key = get_key()
    server_key = key.get("fcm_server_key")

    if not server_key:
        raise RuntimeError("❌ Bạn chưa có 'fcm_server_key' trong firebase_key.json!")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"key={server_key}",
    }

    payload = {
        "to": fcm_token,
        "notification": {
            "title": title,
            "body": body,
            "click_action": click_url,
            "icon": "/rescue-icon.png"
        },
        "data": {
            "url": click_url
        }
    }

    r = requests.post("https://fcm.googleapis.com/fcm/send", headers=headers, json=payload)

    if not r.ok:
        raise RuntimeError(f"❌ FCM lỗi: {r.status_code} - {r.text}")

    return r.json()


# ======================================================
# 7) TÍNH KHOẢNG CÁCH (CHO PHÂN TÍCH NGƯỜI GẦN NHẤT)
# ======================================================
from math import radians, sin, cos, sqrt, atan2

def distance_km(lat1, lng1, lat2, lng2):
    """Tính khoảng cách giữa 2 tọa độ (Haversine)"""
    R = 6371  # bán kính Trái Đất (km)

    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])

    dlat = lat2 - lat1
    dlng = lng2 - lng1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c
