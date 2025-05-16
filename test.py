import asyncio
import sys
import os
from pyppeteer import launch

ZOOM_TIMEOUT = 90000  # Timeout for page navigation

async def manual_zoom_walkthrough(zoom_url):
    print(f"🔗 Opening Zoom link for manual walkthrough: {zoom_url}")
    print("The browser window should appear on your local desktop if X11 forwarding is working.")
    print("Interact with it manually. To close, manually close the browser window or stop this script (Ctrl+C).")

    browser = None
    try:
        browser_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox", # Often needed when running as root or in certain environments
            "--window-size=1280,1024",
            "--disable-infobars",
            "--disable-notifications",
            # "--disable-features=ExternalProtocolDialog", # You can experiment with this
            "--autoplay-policy=no-user-gesture-required",
        ]
        # IMPORTANT: DO NOT explicitly set --display here if using SSH X11 forwarding.
        # SSH X11 forwarding should set the DISPLAY environment variable automatically.
        # # browser_args.append(f"--display=:XX") # Ensure this is commented out or removed

        browser = await launch({
            "headless": False,  # Makes the browser visible
            "args": browser_args,
            "ignoreHTTPSErrors": True,
            "dumpio": True      # Prints browser's console output to your terminal
        })
        page = await browser.newPage()
        await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36')
        await page.setViewport({"width": 1280, "height": 960})

        print(f"Navigating to {zoom_url}...")
        await page.goto(zoom_url, {"waitUntil": "networkidle0", "timeout": ZOOM_TIMEOUT})
        print("Navigation complete. Browser is ready for your interaction on your local screen.")
        print("You can now manually click buttons, open DevTools (usually F12 or right-click -> Inspect), etc.")
        
        # Keep the browser open for manual interaction
        await asyncio.sleep(1200) # 20 minutes

        print("Manual walkthrough period ended.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        if "Missing X server" in str(e) or "platform failed to initialize" in str(e):
            print("********************************************************************************")
            print("ERROR: Still missing X server or display. This means X11 forwarding is not working.")
            print("Please ensure:")
            print("1. You are connected to your server with 'ssh -X your_server' or 'ssh -Y your_server'.")
            print("2. If on Windows/macOS, your local X server (VcXsrv, Xming, XQuartz) is installed AND RUNNING.")
            print("3. You have 'xauth' installed on the server ('sudo apt-get install xauth').")
            print("4. Test with a simple X11 app like 'xeyes' on the server first.")
            print("********************************************************************************")
    finally:
        if browser:
            print("Closing browser...")
            await browser.close()
            print("Browser closed.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python your_script_name.py <zoom_url>")
        sys.exit(1)
    
    zoom_link_to_test = sys.argv[1]
    
    print("Starting manual walkthrough script...")
    # For Python 3.7+
    if sys.version_info >= (3, 7):
        asyncio.run(manual_zoom_walkthrough(zoom_link_to_test))
    else: # For older Python versions (like the one that gave the DeprecationWarning)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(manual_zoom_walkthrough(zoom_link_to_test))

