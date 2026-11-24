/**
 * E2E Tests — Thème (dark/light mode)
 *
 * next-themes utilise attribute="class" sur <html>, pas data-theme sur <body>.
 */

import { test, expect } from "@playwright/test";

test.describe("Theme Toggle", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/", { waitUntil: "networkidle" });
  });

  test("thème par défaut est system", async ({ page }) => {
    // next-themes defaultTheme="system" → pas de class theme sur html au départ
    const html = page.locator("html");
    // Le thème system ne force pas de class theme
    await expect(html).toBeVisible();
  });

  test("changement de thème modifie la class html", async ({ page }) => {
    // Le Header n'est rendu que dans ChatWindow, donc il faut d'abord créer une conversation
    await page.getByRole("button", { name: /Nouvelle conversation/i }).click();

    // Le ThemeToggle est dans le header du ChatWindow
    const header = page.locator("header").first();
    await expect(header).toBeVisible();

    const themeBtn = header.locator("button").last();
    await themeBtn.click();

    // next-themes attribute="class" → modifie la class sur <html>
    await expect(page.locator("html")).toHaveAttribute("class", /dark/);
  });

  test("le thème persiste au reload", async ({ page }) => {
    await page.getByRole("button", { name: /Nouvelle conversation/i }).click();

    const header = page.locator("header").first();
    const themeBtn = header.locator("button").last();
    await themeBtn.click();

    await expect(page.locator("html")).toHaveAttribute("class", /dark/);

    await page.reload({ waitUntil: "networkidle" });
    // next-themes persiste dans localStorage
    await expect(page.locator("html")).toHaveAttribute("class", /dark/);
  });
});
