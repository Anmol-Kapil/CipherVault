import { Buffer } from "node:buffer";
import { test, expect } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

const screenshotDir = path.resolve("../docs/screenshots");
const password = "local-demo-password";

test("local vault feature walkthrough and screenshots", async ({
  page,
  request,
}) => {
  await fs.mkdir(screenshotDir, { recursive: true });
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const shot = (name) =>
    page.screenshot({
      path: path.join(screenshotDir, `${name}.png`),
      fullPage: true,
      animations: "disabled",
    });
  const nav = (label) =>
    page.getByRole("navigation").getByRole("button", { name: label });
  const seedIds = [];
  const examples = [
    [
      "Travel checklist.txt",
      "Packing list\nPassport copy\nTravel insurance\n",
      "anmol",
    ],
    [
      "Project notes.md",
      "# CipherVault\nA calmer home for important files.\n",
      "anmol",
    ],
    [
      "Reading list.csv",
      "title,status\nThe Design of Everyday Things,to read\n",
      "personal",
    ],
  ];
  // Only synthetic data is created; clean up only these IDs after the test.
  try {
    const health = await (await request.get("/api/")).json();
    expect(
      health.storage.backend,
      "Run the screenshot walkthrough with CIPHERVAULT_STORAGE=local and a separate CIPHERVAULT_DATA_DIR; it never uses your real Google Drive.",
    ).toBe("local");
    for (const [filename, content, username] of examples) {
      const response = await request.post("/api/upload", {
        multipart: {
          file: {
            name: filename,
            mimeType: "text/plain",
            buffer: Buffer.from(content),
          },
          username,
          password,
        },
      });
      expect(response.status()).toBe(201);
      const { access_id, file_id } = await response.json();
      seedIds.push(file_id);
      expect(access_id).toBeTruthy();
    }
    await page.goto("/");
    await expect(
      page.getByText("Offline demo", { exact: true }).first(),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Your files. Your space." }),
    ).toBeVisible();
    await shot("01-overview");
    await nav("Upload file").click();
    await page.getByLabel("Choose a file").setInputFiles({
      name: "Weekend ideas.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("Visit the bookstore. Take the long way home.\n"),
    });
    await page.getByLabel("Owner name").fill("anmol");
    await page.getByLabel("File password", { exact: false }).fill(password);
    await shot("02-upload");
    const uploadResponse = page.waitForResponse(
      (response) =>
        response.url().endsWith("/api/upload") &&
        response.request().method() === "POST",
    );
    await page.getByRole("button", { name: "Encrypt & save file" }).click();
    const uploaded = await (await uploadResponse).json();
    const uploadedId = uploaded.file_id;
    seedIds.push(uploadedId);
    await expect(page.getByRole("dialog")).toBeVisible();
    await expect(page.locator(".access-code code")).toHaveText(
      uploaded.access_id,
    );
    await page
      .context()
      .grantPermissions(["clipboard-read", "clipboard-write"]);
    await page.getByRole("button", { name: "Copy access ID" }).click();
    await expect(page.getByRole("dialog").getByRole("status")).toContainText(
      "copied",
    );
    expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(
      uploaded.access_id,
    );
    await page.keyboard.press("Shift+Tab");
    await expect(
      page.getByRole("button", { name: /saved my ID/ }),
    ).toBeFocused();
    await page.keyboard.press("Tab");
    await expect(
      page.getByRole("button", { name: "Copy access ID" }),
    ).toBeFocused();
    await shot("03-access-id");
    await page.getByRole("button", { name: /saved my ID/ }).click();
    await expect(
      page.getByRole("heading", { name: /Your file collection/ }),
    ).toBeVisible();
    await shot("04-files");
    await page.getByLabel("Search filenames").fill("Weekend");
    await page.getByLabel("Filter by owner").selectOption("anmol");
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await shot("05-search-and-filter");
    await nav("Retrieve file").click();
    await page
      .getByLabel("Access ID", { exact: true })
      .fill(uploaded.access_id);
    await page
      .getByLabel("File password", { exact: true })
      .fill("incorrect-password");
    await page.getByRole("button", { name: "Decrypt & download" }).click();
    await expect(page.getByRole("alert")).toContainText("Incorrect password");
    await shot("06-password-validation");
    await page.getByRole("button", { name: "Dismiss notification" }).click();
    await page.getByLabel("File password", { exact: true }).fill(password);
    await shot("07-retrieve");
    const downloadEvent = page.waitForEvent("download");
    await page.getByRole("button", { name: "Decrypt & download" }).click();
    const download = await downloadEvent;
    expect(download.suggestedFilename()).toBe("Weekend ideas.txt");
    expect(await fs.readFile(await download.path(), "utf8")).toBe(
      "Visit the bookstore. Take the long way home.\n",
    );
    await expect(page.getByRole("status")).toContainText(
      "File decrypted successfully",
    );
    await shot("08-download-success");
    await nav("My files").click();
    await page
      .getByRole("button", { name: "Delete Weekend ideas.txt", exact: true })
      .click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.getByRole("dialog").getByLabel("File password").fill(password);
    await shot("09-delete-confirmation");
    await page
      .getByRole("button", { name: "Delete permanently", exact: true })
      .click();
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(page.getByRole("status")).toContainText("permanently deleted");
    seedIds.splice(seedIds.indexOf(uploadedId), 1);
    await nav("Overview").click();
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(
      page.getByRole("heading", { name: "Your files. Your space." }),
    ).toBeVisible();
    await shot("10-mobile");
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    await nav("Upload file").click();
    await expect(
      page.getByRole("button", { name: "Encrypt & save file" }),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    await page.route("**/api/files", (route) => route.abort());
    await page.reload();
    await expect(
      page.getByText("Backend offline", { exact: true }),
    ).toBeVisible();
    expect(errors).toEqual([]);
  } finally {
    for (const id of seedIds)
      await request.delete(`/api/files/${id}`, { data: { password } });
  }
});

test("Drive setup and connection states are distinct from backend offline", async ({
  page,
}) => {
  let configured = false;
  await page.route("**/api/", (route) =>
    route.fulfill({
      json: {
        status: "ok",
        storage: {
          backend: "drive",
          configured,
          verified: false,
          message: configured
            ? "OAuth credentials found."
            : "Connect your Google Drive using the README.",
        },
      },
    }),
  );
  await page.route("**/api/files", (route) => route.fulfill({ json: [] }));
  await page.goto("/");
  await expect(
    page.getByText("Drive setup needed", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: /Google Drive setup guide/ }),
  ).toBeVisible();
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Upload file" })
    .click();
  await expect(
    page.getByRole("button", { name: "Encrypt & save file" }),
  ).toBeDisabled();
  await page.screenshot({
    path: path.join(screenshotDir, "11-drive-setup.png"),
    fullPage: true,
  });
  configured = true;
  await page.reload();
  await expect(
    page.getByText("Drive configured", { exact: true }),
  ).toBeVisible();
  await page.route("**/api/storage/check", (route) =>
    route.fulfill({
      json: {
        backend: "drive",
        configured: true,
        verified: true,
        message: "Google Drive connection verified.",
      },
    }),
  );
  await page.getByRole("button", { name: "Check Drive connection" }).click();
  await expect(
    page.getByText("Drive connected", { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: path.join(screenshotDir, "12-drive-connection.png"),
    fullPage: true,
  });
});
