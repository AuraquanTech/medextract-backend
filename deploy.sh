#!/bin/bash
# Non-interactive deployment script for Netlify MCP Server
# Run: ./deploy.sh

echo "=== Netlify MCP Server Deployment ==="
echo ""

# Step 1: Verify dependencies
echo "Step 1: Verifying dependencies..."
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install --silent
else
    echo "✅ Dependencies already installed"
fi

# Verify minimatch
if npm list minimatch > /dev/null 2>&1; then
    echo "✅ minimatch found"
else
    echo "⚠️  minimatch not found, installing..."
    npm install minimatch --silent
fi

# Step 2: Build TypeScript
echo ""
echo "Step 2: Building TypeScript..."
if [ -f "tsconfig.json" ]; then
    npm run build > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ TypeScript build successful"
    else
        echo "❌ TypeScript build failed"
        exit 1
    fi
else
    echo "⚠️  tsconfig.json not found, skipping build"
fi

# Step 3: Check environment variables
echo ""
echo "Step 3: Checking environment variables..."
echo "⚠️  IMPORTANT: Set these in Netlify Dashboard → Site settings → Environment:"
echo "   ALLOWED_ORIGINS=https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com"
echo "   MCP_HTTP_REQUIRE_ORIGIN=true"
echo "   RATE_LIMIT_WINDOW_MS=60000"
echo "   RATE_LIMIT_MAX_REQ=300"
echo ""

# Step 4: Deploy
echo "Step 4: Deploying to Netlify..."
echo "⚠️  Note: This requires Netlify CLI to be installed and authenticated"
echo "   Install: npm install -g netlify-cli"
echo "   Login: netlify login"
echo ""

# Check if netlify CLI is available
if command -v netlify &> /dev/null; then
    echo "✅ Netlify CLI found"
    echo "Deploying..."
    netlify deploy --prod --dir . --functions netlify/functions
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Deployment successful!"
        echo ""
        echo "Next steps:"
        echo "1. Test: curl -i 'https://your-site.netlify.app/mcp'"
        echo "2. Connect in ChatGPT with Server URL: https://your-site.netlify.app/mcp"
    else
        echo "❌ Deployment failed"
        exit 1
    fi
else
    echo "⚠️  Netlify CLI not found"
    echo ""
    echo "To deploy manually:"
    echo "1. Install Netlify CLI: npm install -g netlify-cli"
    echo "2. Login: netlify login"
    echo "3. Deploy: netlify deploy --prod"
    echo ""
    echo "Or push to GitHub if auto-deploy is enabled"
fi

echo ""
echo "=== Deployment Script Complete ==="

