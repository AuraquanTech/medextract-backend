# Netlify MCP Server Deployment Checklist

## Prerequisites

- [ ] **Install Netlify CLI** (if not already installed)
  ```powershell
  npm install -g netlify-cli
  ```

- [ ] **Login to Netlify** (if not already logged in)
  ```powershell
  netlify login
  ```
  This will open a browser window for authentication.

## Deployment Steps

### Step 1: Install Dependencies
```powershell
cd "C:\Users\Q3Trab\cursor-mcp-server"
npm install
```

### Step 2: Deploy to Netlify
```powershell
netlify deploy --prod --dir . --functions netlify/functions
```

**Note:** If this is your first deployment, Netlify will ask:
- "Create & configure a new site?" → Type `Y` and press Enter
- "Team:" → Select your team (usually just press Enter)
- "Site name:" → Press Enter for auto-generated name, or type a custom name

### Step 3: Get Your Site URL
After deployment, Netlify will show your site URL. It will look like:
```
https://your-site-name.netlify.app
```

**Save this URL** - you'll need it for the next steps.

### Step 4: Set Environment Variables in Netlify Dashboard

1. Go to [Netlify Dashboard](https://app.netlify.com)
2. Click on your site
3. Go to **Site settings** → **Environment variables**
4. Click **Add variable** and add each of these:

   | Variable Name | Value |
   |--------------|-------|
   | `ALLOWED_ORIGINS` | `https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com` |
   | `MCP_HTTP_REQUIRE_ORIGIN` | `true` |
   | `RATE_LIMIT_WINDOW_MS` | `60000` |
   | `RATE_LIMIT_MAX_REQ` | `300` |

5. Click **Save** after adding each variable

### Step 5: Redeploy (to apply environment variables)
```powershell
netlify deploy --prod --dir . --functions netlify/functions
```

### Step 6: Test the Deployment

Test the MCP endpoint:
```powershell
curl -i https://your-site-name.netlify.app/mcp
```

**Expected response:** `200 OK` with JSON manifest

Test the health endpoint:
```powershell
curl -i https://your-site-name.netlify.app/mcp/health
```

**Expected response:** `200 OK` with `{"ok": true}`

### Step 7: Connect in ChatGPT

1. Open **ChatGPT** (chat.openai.com)
2. Go to **Settings** (gear icon) → **Developer Mode** → **MCP Servers**
3. Click **Add server** or **New server**
4. Fill in:
   - **Server URL:** `https://your-site-name.netlify.app/mcp`
   - **Authentication:** None (leave blank)
5. Click **Save** or **Connect**

### Step 8: Verify Connection

In ChatGPT, try using an MCP tool like:
- `list_files` (to see workspace files)
- `read_file` (to read a file)
- `get_diagnostics` (to check server status)

## Troubleshooting

### If you get "403 Forbidden":
- ✅ Check that all environment variables are set correctly
- ✅ Verify `ALLOWED_ORIGINS` includes the ChatGPT origin
- ✅ Check Netlify function logs: **Site settings** → **Functions** → **View logs**

### If deployment fails:
- ✅ Make sure `netlify/functions/mcp.ts` exists
- ✅ Verify `netlify.toml` is in the root directory
- ✅ Check that `package.json` has dependencies:
  - `@netlify/functions`
  - `minimatch`

### If ChatGPT can't connect:
- ✅ Test the endpoint with `curl` first (Step 6)
- ✅ Check that the URL is exactly: `https://your-site-name.netlify.app/mcp`
- ✅ Verify no trailing slash
- ✅ Check Netlify function logs for errors

## Quick Reference

**Project Directory:**
```
C:\Users\Q3Trab\cursor-mcp-server
```

**Key Files:**
- `netlify/functions/mcp.ts` - Main function
- `netlify.toml` - Netlify configuration
- `package.json` - Dependencies

**Deploy Command:**
```powershell
netlify deploy --prod --dir . --functions netlify/functions
```

**Test Commands:**
```powershell
# Test manifest
curl -i https://your-site-name.netlify.app/mcp

# Test health
curl -i https://your-site-name.netlify.app/mcp/health
```

