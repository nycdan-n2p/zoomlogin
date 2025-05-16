#!/usr/bin/env python3
from flask import Flask, request
import email
import re
import subprocess
import sys

app = Flask(__name__)

# ─────────────── Link‐matching regexes ───────────────
ZOOM_REGEX         = r"https://[^\s]*zoom\.us/j/[^\s]+"
GOOGLE_MEET_REGEX  = r"(?:https?://)?meet\.google\.com/[a-z0-9-]+"

@app.route('/webhook/email', methods=['POST'])
def handle_email():
    raw = request.data
    msg = email.message_from_bytes(raw)

    subject    = msg.get('Subject')
    from_email = msg.get('From')
    to_email   = msg.get('To')

    # Extract plaintext body
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode(errors="ignore")
                break
    else:
        body = msg.get_payload(decode=True).decode(errors="ignore")

    # Log incoming email
    print("🔁 Webhook triggered")
    print("📌 Subject:", subject)
    print("👤 From:",  from_email)
    print("📬 To:",    to_email)
    print("📝 Body:\n", body[:500].replace("\n", " "))

    # 1) Try Zoom
    zoom_match = re.search(ZOOM_REGEX, body)
    if zoom_match:
        zoom_url = zoom_match.group(0)
        print(f"📺 Found Zoom link: {zoom_url}")
        subprocess.Popen(["python3", "join_and_record.py", zoom_url])
        return "OK", 200

    # 2) Try Google Meet
    gm_match = re.search(GOOGLE_MEET_REGEX, body, re.IGNORECASE)
    if gm_match:
        meet_url = gm_match.group(0)
        # ensure proper scheme
        if not meet_url.startswith("http"):
            meet_url = "https://" + meet_url
        print(f"📺 Found Google Meet link: {meet_url}")
        subprocess.Popen(["python3", "join_and_record_meet.py", meet_url])
        return "OK", 200

    # 3) Nothing recognized
    print("❌ No recognized meeting link found.")
    return "OK", 200

if __name__ == "__main__":
    # allow optional port override
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    app.run(host="0.0.0.0", port=port)