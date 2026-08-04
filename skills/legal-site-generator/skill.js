import fs from "fs";
import path from "path";

function sanitize(text) {
  return text.replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function layout(title, content, appName) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${sanitize(title)} - ${sanitize(appName)}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<h1>${sanitize(title)}</h1>
${content}
<hr>
<p style="font-size:12px;color:#666;">
Last Updated: ${new Date().toISOString().split("T")[0]}
</p>
</body>
</html>`;
}

function generatePrivacy(input) {
  return layout(
    "Privacy Policy",
    `
<h2>Overview</h2>
<p>${sanitize(input.appName)} respects your privacy and is committed to protecting your personal information.</p>

<h2>Data We Collect</h2>
<p>We collect only minimal data necessary to provide the service. 
We do not collect precise location data. 
We do not use advertising SDKs. 
We do not sell personal data.</p>

<h2>GDPR Rights</h2>
<p>If you are located in the European Economic Area, you have the right to access, correct, or request deletion of your personal data.</p>

<h2>CCPA Rights</h2>
<p>California residents may request disclosure or deletion of personal information. We do not sell personal data.</p>

<h2>Data Retention</h2>
<p>We retain data only as long as necessary to provide our services.</p>

<h2>Contact</h2>
<p>For privacy inquiries, contact: ${sanitize(input.contactEmail)}</p>
`,
    input.appName
  );
}

function generateTerms(input) {
  return layout(
    "Terms of Service",
    `
<h2>Acceptance of Terms</h2>
<p>By using ${sanitize(input.appName)}, you agree to these Terms.</p>

<h2>Use of Service</h2>
<p>You agree to use the app lawfully and not misuse its features.</p>

<h2>Limitation of Liability</h2>
<p>${sanitize(input.companyName)} is not liable for indirect damages resulting from use of the app.</p>

<h2>Termination</h2>
<p>We reserve the right to terminate access for violations of these terms.</p>

<h2>Contact</h2>
<p>${sanitize(input.contactEmail)}</p>
`,
    input.appName
  );
}

function generateSupport(input) {
  return layout(
    "Support",
    `
<h2>Customer Support</h2>
<p>If you need assistance, contact us at:</p>
<p><strong>${sanitize(input.contactEmail)}</strong></p>

<h2>Response Time</h2>
<p>We aim to respond within 3 business days.</p>
`,
    input.appName
  );
}

function generateDelete(input) {
  return layout(
    "Account & Data Deletion",
    `
<h2>Request Deletion</h2>
<p>Users may request account or data deletion by contacting:</p>
<p><strong>${sanitize(input.contactEmail)}</strong></p>

<h2>Processing Time</h2>
<p>All eligible data will be permanently deleted within 7 days of confirmation.</p>
`,
    input.appName
  );
}

function generateIndex(input) {
  return layout(
    input.appName,
    `
<p>Welcome to the official legal and support site for ${sanitize(input.appName)}.</p>
<ul>
<li><a href="privacy.html">Privacy Policy</a></li>
<li><a href="terms.html">Terms of Service</a></li>
<li><a href="support.html">Support</a></li>
<li><a href="delete-account.html">Account Deletion</a></li>
</ul>
`,
    input.appName
  );
}

export default {
  type: "tool",

  name: "legal-site-generator",

  description:
    "Generate App Store compliant legal website for Cloudflare Pages deployment.",

  schema: {
    type: "object",
    properties: {
      appName: {
        type: "string",
        description: "App display name"
      },
      companyName: {
        type: "string",
        description: "Company legal name"
      },
      contactEmail: {
        type: "string",
        description: "Support email"
      }
    },
    required: ["appName", "companyName", "contactEmail"]
  },

  handler: async ({ input, log }) => {
    const fs = await import("fs");
    const path = await import("path");

    const distDir = path.join(process.cwd(), "dist");
    if (!fs.existsSync(distDir)) {
      fs.mkdirSync(distDir);
    }

    const html = `
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>${input.appName}</title>
</head>
<body>
<h1>${input.appName}</h1>
<p>Privacy Policy and Terms placeholder.</p>
<p>Contact: ${input.contactEmail}</p>
</body>
</html>
`;

    fs.writeFileSync(path.join(distDir, "index.html"), html);

    log("Site generated.");

    return "Legal site generated in ./dist";
  }
};