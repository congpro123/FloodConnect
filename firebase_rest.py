import json
import requests
import google.auth.crypt
import google.auth.jwt
import time
import streamlit as st

# Lấy key Firebase từ st.secrets (hoặc fallback nếu chạy local)
try:
    key = dict(st.secrets["firebase"])
except Exception:
    # fallback cho local dev (nếu chưa có secrets.toml)
    with open("firebase_key.json", "r") as f:
        key = json.load(f)

def get_access_token():
    """Tạo access token OAuth 2.0 từ service account key"""
    try:
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
            raise ValueError(f"Không nhận được access_token: {result}")
        return result["access_token"]
    except Exception as e:
        raise RuntimeError(f"🔥 Lỗi khi tạo access_token: {e}\nPhản hồi: {r.text if 'r' in locals() else 'Không có phản hồi'}")

def get_firestore_docs(collection):
    """Lấy danh sách tài liệu trong collection Firestore"""
    token = get_access_token()
    url = f"https://firestore.googleapis.com/v1/projects/{key['project_id']}/databases/(default)/documents/{collection}"
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    if not r.ok:
        raise RuntimeError(f"⚠️ Lỗi truy cập Firestore: {r.status_code} - {r.text}")

    data = r.json()
    docs = []
    for doc in data.get("documents", []):
        fields = doc.get("fields", {})
        parsed = {k: list(v.values())[0] for k, v in fields.items()}
        parsed["id"] = doc["name"].split("/")[-1]
        docs.append(parsed)
    return docs
