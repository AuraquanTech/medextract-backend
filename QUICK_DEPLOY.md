# Quick Deployment Guide

## Open a NEW Terminal Window

1. **Open PowerShell or Command Prompt** (new window)
2. **Navigate to the project:**
   ```powershell
   cd "C:\Users\Q3Trab\cursor-mcp-server"
   ```

## Option 1: Use the Batch Script (Easiest)

Double-click `DEPLOY_NETLIFY.bat` or run:
```cmd
DEPLOY_NETLIFY.bat
```

## Option 2: Manual Deployment

### Step 1: Check Netlify CLI
```powershell
netlify --version
```

If not installed:
```powershell
npm install -g netlify-cli
netlify login
```

### Step 2: Install Dependencies
```powershell
npm install
```

### Step 3: Deploy
```powershell
netlify deploy --prod --dir . --functions netlify/functions
```

## Step 4: Set Environment Variables in Netlify Dashboard

Go to: **Netlify Dashboard → Site Settings → Environment Variables**

Add these:
- `ALLOWED_ORIGINS` = `https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com`
- `MCP_HTTP_REQUIRE_ORIGIN` = `true`
- `RATE_LIMIT_WINDOW_MS` = `60000`
- `RATE_LIMIT_MAX_REQ` = `300`

## Step 5: Test the Deployment

```bash
curl -i https://your-site.netlify.app/mcp
```

Should return `200 OK` with the MCP manifest.

## Step 6: Connect in ChatGPT

1. Go to **ChatGPT → Settings → Developer Mode → MCP Servers**
2. Add new server:
   - **Server URL:** `https://your-site.netlify.app/mcp`
   - **Authentication:** None

## Troubleshooting

If you get "403 Forbidden":
- Check that environment variables are set correctly
- Verify `ALLOWED_ORIGINS` includes the ChatGPT origin
- Check Netlify function logs in the dashboard

If deployment fails:
- Make sure `netlify/functions/mcp.ts` exists
- Verify `netlify.toml` is in the root directory
- Check that `package.json` has `@netlify/functions` and `minimatch` dependencies

