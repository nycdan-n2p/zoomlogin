#!/usr/bin/env python3
import asyncio
import uuid
import sys
import os

from pyppeteer import launch
from pyppeteer.errors import TimeoutError, PageError

# ─────────────── Configuration ───────────────
DISPLAY           = ":99"
os.environ['DISPLAY'] = DISPLAY

MEET_TIMEOUT      = 15_000   # ms
RECORD_DURATION   = 60       # seconds
MAX_JOIN_ATTEMPTS = 3

async def join_and_record_meet(url: str):
    out = f"meet_recording_{uuid.uuid4().hex[:8]}.mp4"
    print(f"🎥 Will record to {out} AFTER joining for {RECORD_DURATION}s")

    browser = await launch({
        "headless": False,
        "args": [
            f"--display={DISPLAY}",
            "--no-sandbox", "--disable-setuid-sandbox",
            "--window-size=1920,1080",
            "--disable-features=ExternalProtocolDialog",
            "--use-fake-ui-for-media-stream",
            "--use-fake-device-for-media-stream"
        ]
    })
    page = await browser.newPage()
    await page.setViewport({"width": 1920, "height": 1080})

    # block any zoommtg:// requests just in case
    await page.setRequestInterception(True)
    page.on("request", lambda r: asyncio.create_task(
        r.abort() if r.url.startswith("zoommtg://") else r.continue_()
    ))

    try:
        print(f"🔗 Navigating to Meet URL…")
        try:
            # only wait for DOMContentLoaded
            await page.goto(url, {
                "timeout": MEET_TIMEOUT,
                "waitUntil": "domcontentloaded"
            })
        except (TimeoutError, PageError) as e:
            print(f"⚠️ page.goto error (continuing anyway): {e!r}")

        # give Meet some time to initialize
        await asyncio.sleep(4)

        # try to click the “Join now” / “Ask to join” button
        joined = False
        for i in range(1, MAX_JOIN_ATTEMPTS + 1):
            print(f"🖱 Attempt #{i} to click Meet’s join button…")
            # selectors for both variants
            for sel in [
                "button[aria-label^='Join now']",
                "button[aria-label^='Ask to join']",
                "//span[text()='Join now']/ancestor::button",
                "//span[text()='Ask to join']/ancestor::button"
            ]:
                try:
                    if sel.startswith("//"):
                        btns = await page.xpath(sel)
                        if btns:
                            await btns[0].click()
                            joined = True
                            print(f"✅ Clicked (XPath): {sel}")
                            break
                    else:
                        await page.waitForSelector(sel, {"visible": True, "timeout": 2000})
                        await page.click(sel)
                        joined = True
                        print(f"✅ Clicked (CSS): {sel}")
                        break
                except TimeoutError:
                    continue
            if joined:
                break
            await asyncio.sleep(2)

        if not joined:
            print("❌ Could not find any join-button; aborting.")
            return

        # let the in-call UI settle
        await asyncio.sleep(6)

        print("🎬 Starting FFmpeg capture…")
        ffmpeg = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y",
            "-f", "x11grab", "-video_size", "1920x1080", "-framerate", "25",
            "-i", f"{DISPLAY}.0+0,0",
            "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
            "-pix_fmt", "yuv420p", "-crf", "28", "-g", "50",
            out
        )
        await asyncio.sleep(RECORD_DURATION)
        print("🛑 Stopping recording…")
        ffmpeg.terminate()
        await asyncio.wait_for(ffmpeg.wait(), timeout=5)
        print(f"✅ Saved: {out}")

    finally:
        print("🔒 Closing browser…")
        await browser.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 join_and_record_meet.py <meet_url>")
        sys.exit(1)
    asyncio.run(join_and_record_meet(sys.argv[1]))