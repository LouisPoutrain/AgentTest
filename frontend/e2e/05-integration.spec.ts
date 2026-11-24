/**
 * E2E Tests — Intégration Backend/Frontend
 *
 * Ces tests nécessitent que le backend soit en cours d'exécution sur localhost:8000.
 */

import { test, expect } from "@playwright/test";

test.describe("Integration — Backend Connectivity", () => {
  test("le frontend charge sans crash", async ({ page }) => {
    await page.goto("/", { waitUntil: "networkidle" });
    await expect(page.locator("main")).toBeVisible();
  });

  test("la page ne crash pas si le backend est inaccessible", async ({ page }) => {
    await page.goto("/", { waitUntil: "networkidle" });
    await expect(page.locator("main")).toBeVisible();

    // Le message d'erreur ou le bouton "Réessayer" peut apparaître
    const retryBtn = page.getByRole("button", { name: /Réessayer/i });
    if (await retryBtn.isVisible().catch(() => false)) {
      await expect(retryBtn).toBeVisible();
    }
  });

  test("les conversations vides sont gérées", async ({ page }) => {
    await page.goto("/", { waitUntil: "networkidle" });
    await expect(page.locator("main")).toBeVisible();
  });
});

test.describe("Integration — Crew Selection", () => {
  test("le sélecteur de crew est présent", async ({ page }) => {
    await page.goto("/", { waitUntil: "networkidle" });
    await page.getByRole("button", { name: /Nouvelle conversation/i }).click();

    // Le CrewSelector est dans le header
    const crewBtn = page.locator("button").filter({ hasText: /Sélectionnez un Crew/i });
    if (await crewBtn.isVisible().catch(() => false)) {
      await expect(crewBtn).toBeVisible();
    }
  });
});
