// Minimal GitHub App helper for PR-only writes
import fetch from "node-fetch";

type CreateBlobResp = { sha: string };
type CreateTreeResp = { sha: string };
type CreateCommitResp = { sha: string };

const GH_API = "https://api.github.com";

export type GitHubCtx = {
  repo: string;            // "owner/name"
  baseBranch: string;      // e.g., "main"
  prBranchPrefix: string;  // e.g., "mcp/batch"
  token: string;           // GitHub App installation token or PAT (installation token preferred)
};

export async function ensureBranch(ctx: GitHubCtx): Promise<{ baseSha: string; branch: string }> {
  const headers = ghHeaders(ctx.token);
  const refResp = await fetch(`${GH_API}/repos/${ctx.repo}/git/ref/heads/${ctx.baseBranch}`, { headers });
  if (!refResp.ok) throw new Error(`Failed get base ref: ${refResp.status}`);
  const refJson = await refResp.json() as any;
  const baseSha = refJson.object.sha;
  const branch = `${ctx.prBranchPrefix}/${Date.now()}`;
  const createRef = await fetch(`${GH_API}/repos/${ctx.repo}/git/refs`, {
    method: "POST",
    headers,
    body: JSON.stringify({ ref: `refs/heads/${branch}`, sha: baseSha }),
  });
  if (!createRef.ok) throw new Error(`Failed create branch: ${createRef.status}`);
  return { baseSha, branch };
}

export async function createFilesCommit(ctx: GitHubCtx, branch: string, baseSha: string, files: { path: string; content: string }[], message: string) {
  const headers = ghHeaders(ctx.token);
  // 1) blobs
  const blobs = await Promise.all(files.map(async f => {
    const r = await fetch(`${GH_API}/repos/${ctx.repo}/git/blobs`, {
      method: "POST",
      headers,
      body: JSON.stringify({ content: f.content, encoding: "utf-8" })
    });
    if (!r.ok) throw new Error(`blob failed for ${f.path}: ${r.status}`);
    return { path: f.path, sha: (await r.json() as CreateBlobResp).sha, mode: "100644", type: "blob" };
  }));
  // 2) tree
  const treeResp = await fetch(`${GH_API}/repos/${ctx.repo}/git/trees`, {
    method: "POST",
    headers,
    body: JSON.stringify({ base_tree: baseSha, tree: blobs }),
  });
  if (!treeResp.ok) throw new Error(`tree failed: ${treeResp.status}`);
  const treeSha = (await treeResp.json() as CreateTreeResp).sha;
  // 3) commit
  const commitResp = await fetch(`${GH_API}/repos/${ctx.repo}/git/commits`, {
    method: "POST",
    headers,
    body: JSON.stringify({ message, tree: treeSha, parents: [baseSha] })
  });
  if (!commitResp.ok) throw new Error(`commit failed: ${commitResp.status}`);
  const commitSha = (await commitResp.json() as CreateCommitResp).sha;
  // 4) update ref
  const refResp = await fetch(`${GH_API}/repos/${ctx.repo}/git/refs/heads/${branch}`, {
    method: "PATCH",
    headers,
    body: JSON.stringify({ sha: commitSha, force: false })
  });
  if (!refResp.ok) throw new Error(`update ref failed: ${refResp.status}`);
}

export async function openPullRequest(ctx: GitHubCtx, branch: string, title: string, body: string) {
  const headers = ghHeaders(ctx.token);
  const pr = await fetch(`${GH_API}/repos/${ctx.repo}/pulls`, {
    method: "POST",
    headers,
    body: JSON.stringify({ title, head: branch, base: ctx.baseBranch, body }),
  });
  if (!pr.ok) throw new Error(`PR failed: ${pr.status}`);
  return pr.json();
}

function ghHeaders(token: string) {
  return {
    "authorization": `Bearer ${token}`,
    "accept": "application/vnd.github+json",
    "user-agent": "nexusmcp-bridge"
  };
}

