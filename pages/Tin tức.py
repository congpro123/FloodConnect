import streamlit as st
import feedparser
import re
from datetime import datetime, timedelta
import time

RSS_FEEDS = [
    "https://vnexpress.net/rss/thoi-su.rss",
    "https://thanhnien.vn/rss/thoi-su.rss",
    "https://tuoitre.vn/rss/thoi-su.rss"
]

KEYWORDS = ["bão", "lũ", "lụt", "thiên tai", "mưa", "áp thấp",
            "ngập", "sạt lở", "động đất", "khô hạn"]

st.set_page_config(
    page_title="🌧️ Tin tức Thiên tai tại Việt Nam",
    page_icon="assets/logo.png",     # Favicon
)

# --- Bộ lọc thời gian ---
filter_option = st.selectbox(
    "📅 Lọc theo thời gian:",
    ["Tất cả", "Hôm nay", "24 giờ qua", "7 ngày qua"]
)

def extract_content(summary_html):
    """Tách mô tả và ảnh"""
    img_match = re.search(r'<img[^>]+src="([^"]+)"', summary_html)
    img_url = img_match.group(1) if img_match else None
    description = re.sub(r'<[^>]+>', '', summary_html).strip()
    return description, img_url

def parse_time(entry):
    """Trả về datetime chuẩn từ RSS"""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6])
    return None

def time_relative(dt):
    """Trả về dạng 'x giờ trước'"""
    if not dt:
        return "Không rõ thời gian"
    now = datetime.now()
    diff = now - dt

    if diff.total_seconds() < 60:
        return "Vừa xong"
    elif diff.total_seconds() < 3600:
        return f"{int(diff.total_seconds() // 60)} phút trước"
    elif diff.total_seconds() < 86400:
        return f"{int(diff.total_seconds() // 3600)} giờ trước"
    elif diff.days < 7:
        return f"{diff.days} ngày trước"
    else:
        return dt.strftime("%d/%m/%Y")

def pass_filter(dt):
    """Lọc theo thời gian người dùng chọn"""
    if not dt:
        return True

    now = datetime.now()
    if filter_option == "Tất cả":
        return True
    elif filter_option == "Hôm nay":
        return dt.date() == now.date()
    elif filter_option == "24 giờ qua":
        return dt >= now - timedelta(hours=24)
    elif filter_option == "7 ngày qua":
        return dt >= now - timedelta(days=7)

    return True

# --- Lấy & lọc tin ---
news_list = []

for url in RSS_FEEDS:
    feed = feedparser.parse(url)
    for entry in feed.entries:
        text = (entry.title + " " + entry.get("summary", "")).lower()
        if any(k in text for k in KEYWORDS):
            dt = parse_time(entry)
            if pass_filter(dt):
                news_list.append((dt, entry))

# Sắp xếp theo thời gian mới nhất
news_list.sort(key=lambda x: (x[0] is not None, x[0]), reverse=True)

# --- Hiển thị ---
if not news_list:
    st.warning("Không có tin nào phù hợp.")
else:
    for dt, entry in news_list:
        st.subheader(entry.title)

        # thời gian tương đối
        st.caption(f"🕒 {time_relative(dt)}")

        description, img_url = extract_content(entry.summary)
        st.write(description)

        if img_url:
            st.image(img_url, use_container_width=True)

        st.markdown(f"[🔗 Đọc bài gốc]({entry.link})")

        st.divider()
