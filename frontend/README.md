# CipherVault frontend

A responsive React interface for a locally run app backed by **your own Google Drive**. See the [root README](../readme.md) for OAuth credential setup, local server instructions, feature screenshots, and tests. No Vercel or Render setup is required.

Run `npm ci`, then `npm run dev` from this directory. Open http://127.0.0.1:5173. Start FastAPI from the repository root and connect your Google account as described in the main README.

Normal `/api` requests proxy to http://127.0.0.1:8000. `npm test` starts isolated offline test servers on ports 8001/5174, uses `.test-data/browser`, and never accesses your real Google account. Drive connection UI examples use mocked responses.
