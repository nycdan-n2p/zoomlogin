#!/usr/bin/env python3
import asyncio, uuid, sys, os, tempfile
from pyppeteer import launch, errors

DISPLAY = ":99"
os.environ['DISPLAY'] = DISPLAY
ZOOM_TIMEOUT = 7_000
RECORD_DURATION = 60
NAME = "Altius"
MAX_ATTEMPTS = 3

async def cancel_xdg(label="xdg"):
    proc = await asyncio.create_subprocess_exec("xdotool", "key", "Escape")
    await asyncio.wait_for(proc.wait(), timeout=3)

async def click_xpath(page, xp, desc, timeout=10_000):
    await page.waitForXPath(xp, {"visible": True, "timeout": timeout})
    btn = (await page.xpath(xp))[0]
    await btn.click()
    print(f"✅ {desc}")

async def join_zoom(url):
    profile = tempfile.mkdtemp()
    browser = await launch({
      "executablePath": "/usr/bin/chromium-browser",
      "headless": False,
      "dumpio": True,
      "userDataDir": profile,
      "args": [
        f"--display={DISPLAY}",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--auto-open-devtools-for-tabs",
        "--window-size=1920,1080",
        "--disable-features=ExternalProtocolDialog,ServiceWorker"
      ]
    })
    page = await browser.newPage()
    await page.setViewport({"width":1920,"height":1080})
    # 1) grant mic/cam
    client = await page.target.createCDPSession()
    await client.send("Browser.grantPermissions", {
      "origin": "https://app.zoom.us",
      "permissions": ["audioCapture","videoCapture","notifications"]
    })
    # 2) desktop UA
    await page.setUserAgent(
      "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    )
    try:
      print("🔗 goto", url)
      await page.goto(url, {"timeout": ZOOM_TIMEOUT})
    except errors.TimeoutError:
      print("⚠️ initial goto timed out")
    await cancel_xdg("initial")
    # click Launch Meeting / Join from browser
    joined = False
    for i in range(1, MAX_ATTEMPTS+1):
      try:
        await click_xpath(page,
          "//div[@role='button' and normalize-space(text())='Launch Meeting']",
          f"Launch Meeting (#{i})"
        )
      except Exception:
        continue
      await cancel_xdg(f"after launch {i}")
      if not await page.querySelectorEval(
           "button[aria-label='Join from your browser'],"
           "[role=button]:contains('Join from your browser')",
           "()=>true"
         ):
        continue
      await page.click("button[aria-label='Join from your browser'],"
                       "[role=button]:contains('Join from your browser')")
      # find the PWA tab
      for _ in range(15):
        all_pages = await browser.pages()
        pwa = next((p for p in all_pages if p.url.startswith("https://app.zoom.us/wc/join/")), None)
        if pwa:
          page = pwa
          await page.bringToFront()
          joined = True
          print("✅ switched to PWA:", page.url)
          break
        await asyncio.sleep(1)
      if joined:
        break

    if not joined:
      print("❌ failed to join via browser"); return

    # wait for PWA to settle
    print("⏳ waiting for PWA networkidle2…")
    try:
      await page.waitForNavigation({
        "waitUntil": ["domcontentloaded","networkidle2"],
        "timeout": 60_000
      })
    except errors.TimeoutError:
      print("⚠️ PWA networkidle2 timed out")

    # click “I Agree” + enter name
    try:
      await click_xpath(page, "//button[normalize-space(text())='I Agree']","I Agree",30000)
      inp = await page.waitForSelector("input[type=text]",{"visible":True,"timeout":10000})
      await inp.click({"clickCount":3})
      await page.keyboard.type(NAME,{"delay":100})
      await page.keyboard.press("Enter")
      print("✅ name entered")
    except errors.TimeoutError:
      print("❌ could not agree or type name")
      return

    # finally start recording…
    out = f"zoom_recording_{uuid.uuid4().hex[:8]}.mp4"
    proc = await asyncio.create_subprocess_exec(
      "ffmpeg","-y","-f","x11grab","-video_size","1920x1080","-framerate","25",
      "-i",f"{DISPLAY}.0+0,0","-c:v","libx264","-preset","ultrafast","-tune","zerolatency",
      "-pix_fmt","yuv420p","-crf","28","-g","50",out
    )
    await asyncio.sleep(RECORD_DURATION)
    proc.terminate(); await proc.wait()
    print("✅ saved", out)

    await browser.close()

if __name__=="__main__":
    if len(sys.argv)!=2:
      print("Usage: join_and_record.py <url>"); sys.exit(1)
    asyncio.run(join_zoom(sys.argv[1]))