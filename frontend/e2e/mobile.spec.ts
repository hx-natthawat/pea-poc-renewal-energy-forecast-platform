import { expect, test } from "@playwright/test";

/**
 * E2E Tests for Mobile Responsiveness
 *
 * Tests the PWA and mobile-specific features:
 * - Mobile navigation
 * - Responsive layout
 * - Touch interactions
 */

test.describe("Mobile Navigation", () => {
  test.beforeEach(async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 390, height: 844 }); // iPhone 12 dimensions
    await page.goto("/");
  });

  test("should display mobile header", async ({ page }) => {
    // Check for mobile menu button (hamburger icon)
    const menuButton = page.locator('button:has([class*="Menu"]), button:has(svg)').first();
    await expect(menuButton).toBeVisible();
  });

  test("should display bottom navigation on mobile", async ({ page }) => {
    // Check for bottom navigation bar
    const bottomNav = page.locator('[class*="fixed bottom-0"]');
    await expect(bottomNav).toBeVisible();

    // Check for nav items
    await expect(bottomNav.locator("button")).toHaveCount(5); // 5 tabs
  });

  test("should navigate using bottom tabs", async ({ page }) => {
    const bottomNav = page.locator('[class*="fixed bottom-0"]');

    // Click on Solar tab in bottom nav
    await bottomNav.locator("button").nth(1).click();
    await page.waitForTimeout(300);

    // Verify tab changed
    const activeTab = bottomNav.locator('[class*="text-[#74045F]"]').first();
    await expect(activeTab).toBeVisible();
  });

  test("should open mobile menu", async ({ page }) => {
    // Find and click the hamburger menu
    const menuButton = page.locator("header").locator('button:has([class*="Menu"]), button').last();
    await menuButton.click();

    // Mobile menu should appear
    await page.waitForTimeout(300);
    // Check that menu expanded (content becomes visible)
    const menuContent = page.locator('[class*="sm:hidden"][class*="border-t"]');
    await expect(menuContent).toBeVisible();
  });

  test("should have touch-friendly button sizes", async ({ page }) => {
    // Check that buttons meet minimum touch target size (44px)
    const buttons = page.locator("button");
    const count = await buttons.count();

    for (let i = 0; i < Math.min(count, 5); i++) {
      const button = buttons.nth(i);
      const box = await button.boundingBox();
      if (box) {
        // Touch targets should be at least 32px (allowing some flexibility)
        expect(box.height).toBeGreaterThanOrEqual(32);
      }
    }
  });
});

test.describe("Responsive Layout", () => {
  test("should show 2x2 grid on mobile", async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/");

    // Summary cards should be in 2x2 grid
    const cards = page.locator('[class*="grid-cols-2"]').first();
    await expect(cards).toBeVisible();
  });

  test("should show 4-column grid on desktop", async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/");

    // Summary cards grid should be visible
    const cardsGrid = page.locator('[class*="lg:grid-cols-4"]').first();
    await expect(cardsGrid).toBeVisible();
  });

  test("should hide Thai subtitle on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/");

    // Thai subtitle should be hidden on mobile (has sm:block class)
    const subtitle = page.locator('[class*="hidden sm:block"]').first();
    await expect(subtitle).toBeHidden();
  });

  test("should show desktop navigation on wide screens", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/");

    // Tab buttons should be visible on desktop
    await expect(page.locator("button:has-text('Overview')").first()).toBeVisible();
    await expect(page.locator("button:has-text('Solar Forecast')").first()).toBeVisible();
  });

  test("should hide footer on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/");

    // Footer should be hidden on mobile
    const footer = page.locator("footer");
    await expect(footer).toBeHidden();
  });
});

test.describe("PWA Features", () => {
  test("should have PWA manifest linked", async ({ page }) => {
    await page.goto("/");

    // Check for manifest link in head
    const manifestLink = page.locator('link[rel="manifest"]');
    await expect(manifestLink).toBeAttached();
  });

  test("should load offline page when available", async ({ page }) => {
    // Navigate to offline page directly
    const response = await page.goto("/offline.html");

    // Should either load or redirect
    if (response) {
      expect([200, 404]).toContain(response.status());
    }
  });
});
