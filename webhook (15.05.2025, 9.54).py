from flask import Flask, request
import email
import re
import subprocess

app = Flask(__name__)
ZOOM_REGEX = r"https://[^\s]*zoom\.us/j/[^\s]+"

@app.route('/webhook/email', methods=['POST'])
def handle_email():
    raw = request.data
    msg = email.message_from_bytes(raw)

    subject = msg.get('Subject')
    from_email = msg.get('From')
    to_email = msg.get('To')

    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode(errors="ignore")
                break
    else:
        body = msg.get_payload(decode=True).decode(errors="ignore")

    print("🔁 Webhook triggered")
    print("📌 Subject:", subject)
    print("👤 From:", from_email)
    print("📬 To:", to_email)
    print("📝 Body:\n", body[:500])

    # Look for Zoom link
    match = re.search(ZOOM_REGEX, body)
    if match:
        zoom_url = match.group(0)
        print(f"📺 Found Zoom link: {zoom_url}")
        subprocess.Popen(["python3", "join_and_record.py", zoom_url])
    else:
        print("❌ No Zoom link found.")

    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)