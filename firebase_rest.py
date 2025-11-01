import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

# Lấy key từ st.secrets
firebase_key = st.secrets["firebase"]

# Khởi tạo Firestore
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_key)
    firebase_admin.initialize_app(cred)
db = firestore.client()
