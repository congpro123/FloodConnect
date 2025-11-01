import json
import requests
import time
import os
import google.auth.crypt
import google.auth.jwt

# Streamlit chỉ import khi thực sự cần (tránh lỗi khi chạy độc lập)
try:
    import streamlit as st
except ImportError:
    st = None


# ==============================
# 1️⃣ Tải khóa Firebase
# ==============================
def load_firebase_key():
    """
    Ưu tiên đọc file firebase_key.json nếu tồn tại.
    Nếu không, đọc từ st.secrets["firebase"].
    """
    if os.path.exists("firebase_key.json"):
        with open("firebase_key.json", "r", encoding="utf-8") as f:
            return json.load(f)

    if st and "firebase" in st.secrets:
        return dict(st.secrets["firebase"])

    raise FileNotFoundError(
        "Không tìm thấy firebase_key.json và cũng không có st.secrets['firebase']."
    )


# Cache khóa để không phải đọc lại nhiều lần
_key_cache = None


def get_key():
    global _key_cache
    if _key_cache is None:
        _key_cache = load_firebase_key()
    return _key_cache


# ==============================
# 2️⃣ Lấy access token từ Service Account
# ==============================
def get_access_token():
    """Tạo access token OAuth 2.0 từ service account key"""
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
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": jwt_str,
        },
    )

    result = r.json()
    if "access_token" not in result:
        raise RuntimeError(f"Không nhận được access_token: {result}")
    return result["access_token"]


# ==============================
# 3️⃣ Hàm đọc Firestore (REST API)
# ==============================
def get_firestore_docs(collection: str):
    """Lấy danh sách tài liệu trong một collection Firestore"""
    key = get_key()
    token = get_access_token()
    url = f"https://firestore.googleapis.com/v1/projects/{key['project_id']}/databases/(default)/documents/{collection}"

    r = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    if not r.ok:
        raise RuntimeError(f"Lỗi truy cập Firestore: {r.status_code} - {r.text}")

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


# ==============================
# 4️⃣ Hàm thêm tài liệu (nếu cần)
# ==============================
def add_firestore_doc(collection: str, data: dict):
    """Thêm tài liệu vào collection"""
    key = get_key()
    token = get_access_token()
    url = f"https://firestore.googleapis.com/v1/projects/{key['project_id']}/databases/(default)/documents/{collection}"

    # chuyển sang định dạng Firestore field
    fields = {k: {"stringValue": str(v)} for k, v in data.items()}

    r = requests.post(url, headers={"Authorization": f"Bearer {token}"}, json={"fields": fields})
    if not r.ok:
        raise RuntimeError(f"Lỗi thêm tài liệu: {r.status_code} - {r.text}")
    return r.json()
