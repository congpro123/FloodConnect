import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email_config import EMAIL_SENDER, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT


def send_email(to_email, subject, message):
    """
    Gửi email cho 1 người nhận.
    Trả về:
        True  → nếu gửi thành công
        False → nếu thất bại
    """
    try:
        # Tạo object email
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = to_email
        msg["Subject"] = subject

        # Gắn nội dung dạng text
        msg.attach(MIMEText(message, "plain", "utf-8"))

        # Kết nối server Gmail
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Mã hoá kết nối

        # Đăng nhập Gmail bằng App Password
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)

        # Gửi email
        server.sendmail(EMAIL_SENDER, to_email, msg.as_string())

        # Đóng kết nối
        server.quit()

        return True

    except Exception as e:
        print("EMAIL ERROR:", e)
        return False
