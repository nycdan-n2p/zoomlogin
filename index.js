const express = require('express');
const { simpleParser } = require('mailparser');

const app = express();
const PORT = 3000;

// Manually collect raw body bytes to avoid any parser interference
app.use((req, res, next) => {
  const chunks = [];

  req.on('data', chunk => {
    chunks.push(chunk);
  });

  req.on('end', () => {
    req.body = Buffer.concat(chunks);
    next();
  });
});

// Email handler
app.post('/email', async (req, res) => {
  try {
    console.log('📬 Incoming email webhook');
    console.log('🧾 Method:', req.method);
    console.log('🧾 Content-Type:', req.get('content-type'));
    console.log('🧾 Headers:', JSON.stringify(req.headers, null, 2));
    console.log('📥 Raw body length:', req.body.length);

    const parsed = await simpleParser(req.body);

    console.log('✅ Parsed email');
    console.log(`📌 Subject: ${parsed.subject}`);
    console.log(`👤 From: ${parsed.from.text}`);
    console.log(`📧 To: ${parsed.to.text}`);
    console.log(`📝 Body: ${parsed.text?.substring(0, 200)}...`);

    res.status(200).send('Received');
  } catch (err) {
    console.error('❌ Error parsing email:', err.message);
    res.status(500).send('Failed to parse email');
  }
});

// Fallback 404 route
app.use((req, res) => {
  res.status(404).send('Not Found');
});

// Start the server
app.listen(PORT, () => {
  console.log(`✅ Webhook server listening on port ${PORT}`);
});