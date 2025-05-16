export default {
  async email(message, env, ctx) {
    const rawMime = await message.raw;

    try {
      const response = await fetch("http://hook.pagesh.us/webhook/email", {
  method: "POST",
  headers: {
    "Content-Type": "application/octet-stream",
    "User-Agent": "cloudflare-worker"
  },
  body: rawMime
});

      const text = await response.text();
      console.log(`✅ Webhook responded with: ${response.status} – ${text}`);
    } catch (err) {
      console.error("❌ Failed to forward email to webhook:", err);
    }

    return new Response("OK", { status: 200 });
  },

  async fetch(request, env, ctx) {
    return new Response("Cloudflare Email Worker is active.", {
      status: 200,
      headers: { "Content-Type": "text/plain" }
    });
  }
};
