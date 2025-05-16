# pageshus-email-webhook

## Overview

**pageshus-email-webhook** is a lightweight service that listens for incoming email webhooks, extracts online meeting links (Zoom & Google Meet), and automatically joins and records audio from those meetings.

The core components are:

* **webhook.py**: A Flask application that receives raw email data via POST, parses out Zoom and Google Meet URLs, and launches recorder scripts.
* **join\_and\_record.py**: A Pyppeteer + FFmpeg script that navigates to a Zoom meeting in the browser, joins via the “Join from your browser” flow, and records audio/video.
* **join\_and\_record\_meet.py** (to be implemented): A similar script for Google Meet.

## Features

* Auto-detects Zoom and Google Meet links in email bodies.
* Headless (or headed) browser automation via Pyppeteer.
* Audio/video recording using FFmpeg (X11 grab).
* Runs on a Linux server (e.g. Ubuntu) with Xvfb/VNC.
* Optional deploy-key–based GitHub integration.

## Prerequisites

* **Python 3.8+**
* **pipenv** or **venv** for a virtual environment
* **Chromium** (installed via `snap` or `apt`)
* **Xvfb** (for virtual display, e.g. `:99`)
* **xdotool** (to dismiss external prompts)
* **FFmpeg** (for recording)
* **Git** (optional, for version control)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/nycdan-n2p/zoomlogin.git
   cd pageshus-email-webhook
   ```

2. Create a Python virtual environment and install dependencies:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Install system packages:

   ```bash
   sudo apt update
   sudo apt install xvfb xdotool ffmpeg chromium-browser
   ```

## Configuration

* **DISPLAY**: The Xvfb display to use (default `:99`).
* **ZOOM\_TIMEOUT**: Navigation timeout for Zoom (ms).
* **RECORD\_DURATION**: How many seconds to record after joining.
* **NAME\_TO\_ENTER**: The display name to use when joining.

You can tweak these in the top section of `join_and_record.py` (and similarly for Meet script).

### GitHub Deploy Key (optional)

Use a deploy key to give this server push/pull access without user credentials. See [GitHub Deploy Keys](#) for setup instructions.

## Usage

1. Start Xvfb and VNC (if you need GUI debugging):

   ```bash
   Xvfb :99 -screen 0 1920x1080x24 &
   # optionally start a VNC server pointed at :99
   ```

2. Launch the webhook service:

   ```bash
   source venv/bin/activate
   python webhook.py
   ```

3. Configure your mail system or service to POST incoming emails to `http://<server>/webhook/email`.

4. When a matching Zoom or Meet invite arrives, the service will log the link and spawn `join_and_record.py <URL>`.

## Troubleshooting

* **Browser won’t launch**:  Ensure `chromium-browser` is installed and accessible. Check `!which chromium-browser`.
* **Permission denied on profile**: Use a fresh `--user-data-dir` or deploy key to avoid root profile locks.
* **Missing ALSA errors**: Install `alsa-utils` or configure dummy audio devices.
* **Webclient PWA hangs**: Increase timeouts or mirror console/network logs in the script via `page.on("console")` and `page.on("requestfailed")` handlers.

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Commit your changes (`git commit -m "Add feature X"`)
4. Push to your branch (`git push origin feat/my-feature`)
5. Open a Pull Request

## License

MIT © Your Name
