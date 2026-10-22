import { expect, test } from "@playwright/test";
import { mockApi } from "./mock-api";

test.beforeEach(async ({ page }) => {
  await mockApi(page);
});

test("renders the dashboard and interactive map", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: "Colombianos detenidos en el exterior" }),
  ).toBeVisible();

  await expect(page.locator(".maplibregl-canvas")).toBeVisible({ timeout: 10_000 });

  await expect(page.locator(".stat-card").first()).toContainText("28.732");
  await expect(page.locator(".error-banner")).toHaveCount(0);
});

test("selects a country from the URL", async ({ page }) => {
  await page.goto("/?pais=ESPAÑA");

  await expect(page.locator(".selected-name")).toHaveText("ESPAÑA");
  expect(page.url()).toContain("pais=");
});

test("updating a filter writes it to the URL", async ({ page }) => {
  await page.goto("/");

  await page.selectOption("#filter-delito", "NARCOTRÁFICO");
  await page.waitForURL(/delito=/);

  expect(page.url()).toContain("delito=");
});
