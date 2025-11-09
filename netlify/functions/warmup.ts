import type { Handler } from "@netlify/functions";

const TARGET =
  process.env.PUBLIC_MCP_URL ||
  "https://zingy-profiterole-f31cb8.netlify.app/mcp";

export const handler: Handler = async () => {
  try {
    await fetch(TARGET, { method: "GET", headers: { "user-agent": "warmup" } });
  } catch {
    // best effort
  }
  return { statusCode: 200, body: "ok" };
};

