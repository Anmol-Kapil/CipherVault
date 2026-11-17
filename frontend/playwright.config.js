import { defineConfig } from "@playwright/test";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import process from "node:process";

const root = fileURLToPath(new URL("..", import.meta.url));
const venvPython = path.join(
  root,
  ".venv",
  process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
);
const python = existsSync(venvPython) ? venvPython : "python";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60000,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:5174",
    viewport: { width: 1440, height: 1000 },
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: `"${python}" -m uvicorn backend.main:app --host 127.0.0.1 --port 8001`,
      cwd: root,
      url: "http://127.0.0.1:8001/",
      reuseExistingServer: false,
      env: {
        CIPHERVAULT_STORAGE: "local",
        CIPHERVAULT_DATA_DIR: ".test-data/browser",
        GOOGLE_TOKEN_FILE: ".test-data/no-token.json",
      },
    },
    {
      command:
        "node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5174",
      cwd: path.join(root, "frontend"),
      url: "http://127.0.0.1:5174",
      reuseExistingServer: false,
      env: { CIPHERVAULT_API_TARGET: "http://127.0.0.1:8001" },
    },
  ],
});
