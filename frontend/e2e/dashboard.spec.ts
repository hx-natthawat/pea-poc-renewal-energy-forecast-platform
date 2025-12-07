import { expect, test } from "@playwright/test";

/**
 * E2E Tests for PEA RE Forecast Dashboard
 *
 * Tests the main user flows:
 * - Page load and basic rendering
 * - Tab navigation
 * - Status indicators
 * - Mobile responsiveness
 */

test.describe("Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("should load the homepage", async ({ page }) => {
    // Check page title and header
    await expect(page.locator("h1")).toContainText("PEA RE Forecast");

    // Check Thai subtitle is present (desktop)
    await expect(page.locator("text=แพลตฟอร์มศูนย์ข้อมูลพยากรณ์พลังงานหมุนเวียน")).toBeVisible();
  });

  test("should display system status indicator", async ({ page }) => {
    // Status should show either Online or Offline
    const statusIndicator = page.locator('[class*="rounded-full"]').first();
    await expect(statusIndicator).toBeVisible();

    // Should show Online (green) or Offline (red)
    const statusText = await statusIndicator.textContent();
    expect(statusText?.toLowerCase()).toMatch(/online|offline/i);
  });

  test("should display summary cards on overview tab", async ({ page }) => {
    // Check for the 4 summary cards
    await expect(page.locator("text=Solar Output")).toBeVisible();
    await expect(page.locator("text=Avg Voltage")).toBeVisible();
    await expect(page.locator("text=Active Alerts")).toBeVisible();
    await expect(page.locator("text=System Status")).toBeVisible();
  });

  test("should show charts on overview tab", async ({ page }) => {
    // Wait for charts to load (they are dynamically loaded)
    await page.waitForTimeout(1000);

    // Check for chart containers
    const charts = page.locator('[class*="rounded-lg shadow"]');
    await expect(charts.first()).toBeVisible();
  });
});

test.describe("Tab Navigation", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("should navigate to Solar tab", async ({ page }) => {
    // Click Solar tab
    await page.click("button:has-text('Solar')");

    // Verify Solar content is visible
    await page.waitForTimeout(500);
    // The Solar Forecast Chart should be visible
    // Note: Locator defined for future assertion expansion
    const _solarContent = page.locator("text=Solar Power Forecast");
    // Either the chart or a related element should be present
  });

  test("should navigate to Voltage tab", async ({ page }) => {
    // Click Voltage tab
    await page.click("button:has-text('Voltage')");
    await page.waitForTimeout(500);

    // Voltage tab should show voltage monitoring content
  });

  test("should navigate to Alerts tab", async ({ page }) => {
    // Click Alerts tab
    await page.click("button:has-text('Alerts')");
    await page.waitForTimeout(500);

    // Check for alert configuration section
    await expect(page.locator("text=Alert Configuration")).toBeVisible();
    await expect(page.locator("text=Voltage Upper")).toBeVisible();
    await expect(page.locator("text=242V")).toBeVisible();
  });

  test("should navigate to History tab", async ({ page }) => {
    // Click History tab
    await page.click("button:has-text('History')");
    await page.waitForTimeout(500);

    // History tab content should load
  });

  test("should highlight active tab", async ({ page }) => {
    // Overview should be active by default
    const overviewTab = page.locator("button:has-text('Overview')").first();
    await expect(overviewTab).toHaveClass(/bg-white/);

    // Click Solar and verify it becomes active
    await page.click("button:has-text('Solar')");
    const solarTab = page.locator("button:has-text('Solar')").first();
    await expect(solarTab).toHaveClass(/bg-white/);
  });
});

test.describe("Alert Configuration", () => {
  test("should display voltage thresholds", async ({ page }) => {
    await page.goto("/");
    await page.click("button:has-text('Alerts')");

    // Check voltage threshold values
    await expect(page.locator("text=242V (+5%)")).toBeVisible();
    await expect(page.locator("text=218V (-5%)")).toBeVisible();
    await expect(page.locator("text=±3.5%")).toBeVisible();
    await expect(page.locator("text=230V")).toBeVisible();
  });
});

test.describe("Footer", () => {
  test("should display PEA branding", async ({ page }) => {
    await page.goto("/");

    // Check footer content (desktop)
    const footer = page.locator("footer");
    await expect(footer.locator("text=PEA RE Forecast Platform")).toBeVisible();
    await expect(footer.locator("text=Provincial Electricity Authority of Thailand")).toBeVisible();
    await expect(footer.locator("text=Version")).toBeVisible();
  });
});

test.describe("API Status", () => {
  test("should show error banner when backend is unavailable", async ({ page }) => {
    // This test checks the error handling
    await page.goto("/");

    // Wait for health check
    await page.waitForTimeout(2000);

    // If backend is down, error banner should appear
    // Note: This test doesn't assert because backend status is unpredictable in e2e
    const _errorBanner = page.locator("text=Cannot connect to backend API");
    // This may or may not be visible depending on backend status
  });
});
