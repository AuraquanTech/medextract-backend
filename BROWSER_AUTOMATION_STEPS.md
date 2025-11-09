# Browser Automation Steps for Auth0 + Netlify Deployment

This document provides step-by-step instructions for an AI assistant using browser automation tools to configure Auth0 and deploy to Netlify.

---

## Part 1: Configure Auth0 (Create App + API)

### Step 1: Navigate to Auth0 Dashboard
1. Open browser and navigate to: `https://manage.auth0.com/`
2. If not logged in, click "Log In" and authenticate
3. Wait for dashboard to load

### Step 2: Create a Regular Web Application
1. In the left sidebar, click **"Applications"**
2. Click **"Create Application"** button (usually top right)
3. In the modal:
   - **Name**: Enter `cursor-mcp-oauth` (or your preferred name)
   - **Application Type**: Select **"Regular Web Application"**
   - Click **"Create"**
4. Wait for application to be created and details page to load

### Step 3: Note Application Credentials
1. On the application details page, find:
   - **Client ID** - Copy this value (you'll need it for ChatGPT connector)
   - **Client Secret** - Click "Show" and copy this value (you'll need it for ChatGPT connector)
2. Save these values securely (you'll paste them into ChatGPT connector later)

### Step 4: Create an API
1. In the left sidebar, click **"APIs"**
2. Click **"Create API"** button (usually top right)
3. In the modal:
   - **Name**: Enter `Cursor MCP Server` (or your preferred name)
   - **Identifier**: Enter `https://cursor-mcp` (this is your AUTH_AUDIENCE)
   - **Signing Algorithm**: Select **"RS256"** (default)
   - Click **"Create"**
4. Wait for API to be created and details page to load

### Step 5: Authorize Application to Access API
1. On the API details page, click the **"Machine to Machine Applications"** tab
2. Find your application (`cursor-mcp-oauth`) in the list
3. Toggle the switch next to it to **"Authorized"** (enabled)
4. If prompted, select scopes (you can leave default or add custom scopes like `mcp.invoke`)
5. Click **"Update"** if there's an update button

### Step 6: Note Auth0 Configuration Values
1. In the left sidebar, click **"Settings"** (under your tenant name at the top)
2. Find **"Domain"** - This is your tenant domain (e.g., `YOUR-TENANT.us.auth0.com`)
3. Note these values for deployment:
   - **AUTH_ISSUER** = `https://YOUR-TENANT.us.auth0.com/` (add trailing slash)
   - **AUTH_AUDIENCE** = `https://cursor-mcp` (the API Identifier)
   - **AUTH_JWKS_URL** = `https://YOUR-TENANT.us.auth0.com/.well-known/jwks.json`

### Step 7: Configure Allowed Callback URLs (Temporary - Will Update Later)
1. Go back to **"Applications"** → Select your application (`cursor-mcp-oauth`)
2. Scroll to **"Application URIs"** section
3. In **"Allowed Callback URLs"**, add:
   - `https://chatgpt.com/*`
   - `https://chat.openai.com/*`
   - (We'll add the actual ChatGPT redirect URL after creating the connector)
4. Click **"Save Changes"**

---

## Part 2: Deploy to Netlify

### Step 1: Navigate to Netlify Dashboard
1. Open browser and navigate to: `https://app.netlify.com/`
2. If not logged in, click "Log in" and authenticate (GitHub, GitLab, Bitbucket, or Email)
3. Wait for dashboard to load

### Step 2: Create New Site from Git
1. Click **"Add new site"** button (usually top right or in the main area)
2. Select **"Import an existing project"** or **"Deploy manually"**
3. If deploying from Git:
   - Choose your Git provider (GitHub, GitLab, Bitbucket)
   - Authorize Netlify if prompted
   - Select your repository (`cursor-mcp-server`)
   - Click **"Next"** or **"Deploy site"**
4. If deploying manually:
   - Click **"Deploy manually"**
   - Drag and drop your project folder or use the CLI

### Step 3: Configure Build Settings (if deploying from Git)
1. On the deploy configuration page:
   - **Build command**: `pip install -r requirements.txt` (or leave empty if using Netlify Functions)
   - **Publish directory**: `.` (or leave empty)
   - Click **"Deploy site"**

### Step 4: Set Environment Variables
1. After site is created, go to **Site settings** (gear icon or Settings in left sidebar)
2. Click **"Environment variables"** in the left menu
3. Click **"Add variable"** and add each of the following:

   **Variable 1:**
   - Key: `AUTH_ISSUER`
   - Value: `https://YOUR-TENANT.us.auth0.com/` (replace with your actual Auth0 domain)
   - Scope: All scopes (or Production if you prefer)
   - Click **"Save"**

   **Variable 2:**
   - Key: `AUTH_AUDIENCE`
   - Value: `https://cursor-mcp`
   - Scope: All scopes
   - Click **"Save"**

   **Variable 3:**
   - Key: `AUTH_JWKS_URL`
   - Value: `https://YOUR-TENANT.us.auth0.com/.well-known/jwks.json` (replace with your actual Auth0 domain)
   - Scope: All scopes
   - Click **"Save"`

   **Variable 4:**
   - Key: `WORKSPACE_DIR`
   - Value: `/workspace` (or your preferred workspace path)
   - Scope: All scopes
   - Click **"Save"`

   **Variable 5:**
   - Key: `MCP_HTTP_REQUIRE_ORIGIN`
   - Value: `true`
   - Scope: All scopes
   - Click **"Save"`

   **Variable 6:**
   - Key: `ALLOWED_ORIGINS`
   - Value: `https://chatgpt.com,https://chat.openai.com`
   - Scope: All scopes
   - Click **"Save"**

### Step 5: Configure Netlify Functions (if using serverless)
1. In Site settings, click **"Functions"** in the left menu
2. Ensure **"Functions directory"** is set to: `netlify/functions`
3. If deploying as a regular app (not serverless), skip this step

### Step 6: Trigger Deployment
1. If deploying from Git, push a commit to trigger automatic deployment
2. If deploying manually:
   - Go to **"Deploys"** tab
   - Click **"Trigger deploy"** → **"Deploy site"**
3. Wait for deployment to complete (watch the deploy log)

### Step 7: Get Your Site URL
1. After deployment completes, go to **"Site overview"**
2. Find your site URL (e.g., `https://your-site-name.netlify.app`)
3. Copy this URL - you'll need it for the ChatGPT connector
4. Your MCP endpoint will be: `https://your-site-name.netlify.app/mcp`

### Step 8: Test the Deployment
1. Open a new browser tab
2. Navigate to: `https://your-site-name.netlify.app/mcp/health`
3. You should see an error (401 Unauthorized) - this is expected without a token
4. If you see a 404, check your Netlify Functions configuration
5. If you see a 500 error, check the deploy logs for issues

---

## Part 3: Alternative - Deploy to Render.com

### Step 1: Navigate to Render Dashboard
1. Open browser and navigate to: `https://dashboard.render.com/`
2. If not logged in, click "Log in" and authenticate (GitHub, GitLab, or Email)
3. Wait for dashboard to load

### Step 2: Create New Web Service
1. Click **"New +"** button (usually top right)
2. Select **"Web Service"**
3. If connecting a repository:
   - Choose your Git provider
   - Authorize Render if prompted
   - Select your repository (`cursor-mcp-server`)
   - Click **"Connect"**

### Step 3: Configure Service Settings
1. **Name**: `cursor-mcp-oauth` (or your preferred name)
2. **Environment**: Select **"Python 3"**
3. **Region**: Choose closest region
4. **Branch**: `main` or `master` (your default branch)
5. **Root Directory**: Leave empty (or specify if your files are in a subdirectory)
6. **Build Command**: `pip install -r requirements.txt`
7. **Start Command**: `uvicorn http_mcp_oauth_bridge:app --host 0.0.0.0 --port $PORT`
8. Click **"Create Web Service"**

### Step 4: Set Environment Variables (Render)
1. After service is created, go to **"Environment"** tab
2. Click **"Add Environment Variable"** and add each:

   - `AUTH_ISSUER` = `https://YOUR-TENANT.us.auth0.com/`
   - `AUTH_AUDIENCE` = `https://cursor-mcp`
   - `AUTH_JWKS_URL` = `https://YOUR-TENANT.us.auth0.com/.well-known/jwks.json`
   - `WORKSPACE_DIR` = `/workspace`
   - `MCP_HTTP_REQUIRE_ORIGIN` = `true`
   - `ALLOWED_ORIGINS` = `https://chatgpt.com,https://chat.openai.com`

3. Click **"Save Changes"** after each variable

### Step 5: Deploy on Render
1. Render will automatically start deploying
2. Watch the deploy logs in the **"Logs"** tab
3. Wait for deployment to complete (status should show "Live")
4. Your service URL will be: `https://cursor-mcp-oauth.onrender.com` (or your custom domain)
5. Your MCP endpoint will be: `https://your-service-url.onrender.com/mcp`

---

## Part 4: Alternative - Deploy to Fly.io

### Step 1: Install Fly CLI
1. Open terminal/command prompt
2. Run: `curl -L https://fly.io/install.sh | sh` (Linux/Mac) or download from https://fly.io/docs/getting-started/installing-flyctl/
3. Verify installation: `flyctl version`

### Step 2: Login to Fly.io
1. Run: `flyctl auth login`
2. Browser will open for authentication
3. Complete authentication in browser
4. Return to terminal

### Step 3: Initialize Fly.io App
1. Navigate to your project directory: `cd /path/to/cursor-mcp-server`
2. Run: `flyctl launch`
3. Follow prompts:
   - App name: `cursor-mcp-oauth` (or your preferred name)
   - Region: Choose closest region
   - PostgreSQL: No (unless you need it)
   - Redis: No (unless you need it)
4. This creates `fly.toml` (already exists in your repo)

### Step 4: Set Secrets (Environment Variables)
1. Run: `flyctl secrets set AUTH_ISSUER=https://YOUR-TENANT.us.auth0.com/`
2. Run: `flyctl secrets set AUTH_AUDIENCE=https://cursor-mcp`
3. Run: `flyctl secrets set AUTH_JWKS_URL=https://YOUR-TENANT.us.auth0.com/.well-known/jwks.json`
4. Run: `flyctl secrets set WORKSPACE_DIR=/workspace`
5. Run: `flyctl secrets set MCP_HTTP_REQUIRE_ORIGIN=true`
6. Run: `flyctl secrets set ALLOWED_ORIGINS=https://chatgpt.com,https://chat.openai.com`

### Step 5: Deploy to Fly.io
1. Run: `flyctl deploy`
2. Wait for deployment to complete
3. Your service URL will be: `https://cursor-mcp-oauth.fly.dev` (or your custom domain)
4. Your MCP endpoint will be: `https://your-app-name.fly.dev/mcp`

---

## Verification Checklist

After deployment, verify:

- [ ] Auth0 application created with Client ID and Secret noted
- [ ] Auth0 API created with Identifier `https://cursor-mcp`
- [ ] Application authorized to access API
- [ ] Environment variables set in deployment platform
- [ ] Deployment completed successfully
- [ ] Service URL accessible (should return 401 without token, not 404)
- [ ] `/mcp/health` endpoint exists (returns 401, not 404)

---

## Next Steps (After Deployment)

1. **Add Connector in ChatGPT** (see `README_OAUTH.md`)
2. **Update Auth0 Callback URL** with the actual ChatGPT redirect URL
3. **Test the connector** with `get_diagnostics`, `list_files`, etc.

---

## Troubleshooting

### Auth0 Issues
- **"Invalid token"**: Check AUTH_ISSUER, AUTH_AUDIENCE match your Auth0 config
- **"Forbidden origin"**: Verify ALLOWED_ORIGINS includes ChatGPT domains
- **"Application not authorized"**: Ensure app is authorized in API's Machine to Machine tab

### Deployment Issues
- **404 on /mcp**: Check Netlify Functions configuration or start command
- **500 Error**: Check deploy logs for Python errors or missing dependencies
- **Environment variables not working**: Ensure variables are set in correct scope (Production/Preview)

### Netlify-Specific
- **Functions not working**: Ensure `netlify/functions/mcp.py` exists and uses Mangum
- **Build failing**: Check Python version in `netlify.toml` matches your requirements

