/**
 * E2E Tests — Chat Interface
 */

import { test, expect } from "@playwright/test";

test.describe("Chat — Message Input", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/", { waitUntil: "networkidle" });
    await page.getByRole("button", { name: /Nouvelle conversation/i }).click();
  });

  test("textarea de message est visible", async ({ page }) => {
    const textarea = page.locator("textarea[aria-label='Message']");
    await expect(textarea).toBeVisible();
  });

  test("placeholder du textarea", async ({ page }) => {
    const textarea = page.locator("textarea[aria-label='Message']");
    await expect(textarea).toHaveAttribute("placeholder", /Écrivez votre message/);
  });

  test("le textarea accepte la saisie", async ({ page }) => {
    const textarea = page.locator("textarea[aria-label='Message']");
    await textarea.fill("Hello world");
    await expect(textarea).toHaveValue("Hello world");
  });
});

test.describe("Chat — Message Display", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/", { waitUntil: "networkidle" });
    await page.getByRole("button", { name: /Nouvelle conversation/i }).click();
  });

  test("le chat est dans un conteneur flex", async ({ page }) => {
    const main = page.locator("main");
    await expect(main).toHaveClass(/flex/);
  });
});
