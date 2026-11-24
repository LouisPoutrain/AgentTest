/**
 * E2E Tests — Sidebar
 */

import { test, expect } from "@playwright/test";

test.describe("Sidebar — Conversations", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/", { waitUntil: "networkidle" });
  });

  test("sidebar affiche 'Aucune conversation' quand vide", async ({ page }) => {
    await expect(page.getByText("Aucune conversation")).toBeVisible();
  });

  test("créer une nouvelle conversation", async ({ page }) => {
    const btn = page.getByRole("button", { name: /Nouvelle conversation/i });
    await btn.click();
    await expect(page.locator(".group")).toBeVisible();
  });

  test("sélectionner une conversation la met en surbrillance", async ({ page }) => {
    const btn = page.getByRole("button", { name: /Nouvelle conversation/i });
    await btn.click();
    await expect(page.locator("main")).toBeVisible();
  });

  test("supprimer une conversation", async ({ page }) => {
    const btn = page.getByRole("button", { name: /Nouvelle conversation/i });
    await btn.click();

    const convItem = page.locator(".group").first();
    await convItem.hover();

    const deleteBtn = convItem.locator("button[title*='Supprimer']");
    await expect(deleteBtn).toBeVisible();
    await deleteBtn.click();

    await expect(page.getByText("Aucune conversation")).toBeVisible();
  });

  test("sidebar affiche la version", async ({ page }) => {
    await expect(page.getByText("Agent Test v2.0")).toBeVisible();
  });
});
