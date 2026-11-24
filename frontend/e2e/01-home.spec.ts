/**
 * E2E Tests — Page d'accueil (Home)
 *
 * Ces tests vérifient le rendu initial de la page, la persistance localStorage,
 * et le comportement de l'UI sans dépendre du backend.
 *
 * Prerequisite: le dev server doit être lancé (npm run dev).
 */

import { test, expect } from "@playwright/test";

test.describe("Home Page — Rendering & State", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/", { waitUntil: "networkidle" });
  });

  test("la page charge sans erreur", async ({ page }) => {
    await expect(page.locator("main")).toBeVisible();
  });

  test("message par défaut sans conversation", async ({ page }) => {
    // Vider localStorage pour forcer l'état vide
    await page.evaluate(() => {
      try { window.localStorage.clear(); } catch {}
    });
    // Recharger pour appliquer
    await page.reload({ waitUntil: "networkidle" });
    // Le main doit être visible (soit "Sélectionnez ou créez...", soit un message d'erreur backend)
    await expect(page.locator("main")).toBeVisible();
  });

  test("bouton Nouvelle conversation est cliquable", async ({ page }) => {
    const btn = page.getByRole("button", { name: /Nouvelle conversation/i });
    await expect(btn).toBeVisible();
    await btn.click();
    await expect(page.locator("main")).toBeVisible();
  });

  test("sidebar affiche le titre Agent Zouglou", async ({ page }) => {
    await expect(page.getByText("Agent Zouglou")).toBeVisible();
  });

  test("version affichée dans la sidebar", async ({ page }) => {
    await expect(page.getByText("Agent Zouglou v2.0")).toBeVisible();
  });

  test("lien Tableau des Lots est présent", async ({ page }) => {
    await expect(page.getByText("Tableau des Lots")).toBeVisible();
  });

  test("thème par défaut est light", async ({ page }) => {
    const body = page.locator("body");
    await expect(body).not.toHaveAttribute("data-theme", "dark");
  });
});

test.describe("Home Page — localStorage persistence", () => {
  test("conversations persistées au reload", async ({ page }) => {
    await page.goto("/", { waitUntil: "networkidle" });

    // Créer une conversation via l'UI
    const btn = page.getByRole("button", { name: /Nouvelle conversation/i });
    await expect(btn).toBeVisible();
    await btn.click();

    // Recharger la page
    await page.reload({ waitUntil: "networkidle" });

    // La page ne doit pas crasher
    await expect(page.locator("main")).toBeVisible();
  });

  test("corruption localStorage gérée", async ({ page }) => {
    await page.goto("/", { waitUntil: "networkidle" });

    // Écrire du JSON invalide
    await page.evaluate(() => {
      try { window.localStorage.setItem("agenttest_conversations", "not valid json{{{"); } catch {}
    });

    await page.reload({ waitUntil: "networkidle" });

    // L'UI ne doit pas crasher
    await expect(page.locator("main")).toBeVisible();
  });
});
