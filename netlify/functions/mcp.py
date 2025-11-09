# Netlify Python Function entrypoint (AWS Lambda style)
from mangum import Mangum
from http_mcp_oauth_bridge import app as fastapi_app

# If you used /mcp routes in your app, keep them. We'll route traffic there via redirects.
handler = Mangum(fastapi_app)
