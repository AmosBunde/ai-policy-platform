import { test, expect } from "@playwright/test";

/**
 * Reports wizard E2E tests.
 *
 * Exercises the 4-step report creation wizard using sample data.
 */
test.describe("Reports Wizard", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.evaluate(() => {
      sessionStorage.setItem(
        "regulatorai_user",
        JSON.stringify({
          id: "00000000-0000-0000-0000-000000000001",
          email: "test@test.com",
          fullName: "Test User",
          role: "analyst",
          organization: null,
        }),
      );
    });
    await page.goto("/reports");
  });

  test("renders reports page with report list", async ({ page }) => {
    await expect(page.getByText("Compliance Reports")).toBeVisible();
    // Sample reports should be visible
    await expect(
      page.getByText(/Q4 2024|NIST Framework|Multi-Jurisdiction/i).first(),
    ).toBeVisible();
  });

  test("opens wizard when New Report button clicked", async ({ page }) => {
    await page.getByRole("button", { name: /new report/i }).click();

    // Step 1: document selection should appear
    await expect(page.getByText("Select Documents")).toBeVisible();
    await expect(
      page.getByPlaceholder(/search documents/i).or(page.getByLabel(/search documents/i)),
    ).toBeVisible();
  });

  test("wizard step 1: select documents and advance", async ({ page }) => {
    await page.getByRole("button", { name: /new report/i }).click();

    // Next should be disabled initially
    const nextBtn = page.getByRole("button", { name: /next/i });
    await expect(nextBtn).toBeDisabled();

    // Select a document
    const checkboxes = page.getByRole("checkbox");
    await checkboxes.first().check();

    // Next should now be enabled
    await expect(nextBtn).toBeEnabled();
    await nextBtn.click();

    // Step 2: template selection
    await expect(page.getByText("Standard")).toBeVisible();
    await expect(page.getByText("Executive")).toBeVisible();
    await expect(page.getByText("Detailed")).toBeVisible();
  });

  test("wizard step 2: choose template and advance", async ({ page }) => {
    await page.getByRole("button", { name: /new report/i }).click();

    // Step 1: select doc
    await page.getByRole("checkbox").first().check();
    await page.getByRole("button", { name: /next/i }).click();

    // Step 2: click Executive template
    await page.getByText("Executive").click();
    await page.getByRole("button", { name: /next/i }).click();

    // Step 3: configure form
    await expect(page.getByLabel("Report Title")).toBeVisible();
  });

  test("wizard step 3: validates title required", async ({ page }) => {
    await page.getByRole("button", { name: /new report/i }).click();

    // Navigate to step 3
    await page.getByRole("checkbox").first().check();
    await page.getByRole("button", { name: /next/i }).click();
    await page.getByRole("button", { name: /next/i }).click();

    // Try to advance without title
    await page.getByRole("button", { name: /next/i }).click();
    await expect(page.getByText(/title is required/i)).toBeVisible();
  });

  test("wizard full flow: select -> template -> configure -> generate", async ({
    page,
  }) => {
    await page.getByRole("button", { name: /new report/i }).click();

    // Step 1: select document
    await page.getByRole("checkbox").first().check();
    await page.getByRole("button", { name: /next/i }).click();

    // Step 2: choose template
    await page.getByRole("button", { name: /next/i }).click();

    // Step 3: fill configuration
    await page.getByLabel("Report Title").fill("E2E Test Report");
    await page.getByRole("button", { name: /next/i }).click();

    // Step 4: review
    await expect(page.getByText("E2E Test Report")).toBeVisible();
    await expect(page.getByText("Generate Report")).toBeVisible();

    // Generate
    await page.getByRole("button", { name: "Generate Report" }).click();

    // Wizard should close and new report should appear in the list
    await expect(page.getByText("E2E Test Report")).toBeVisible();
  });

  test("filter controls are accessible", async ({ page }) => {
    await page.getByRole("button", { name: /filters/i }).click();

    // Filter dropdowns should appear
    await expect(page.locator("#status-filter")).toBeVisible();
    await expect(page.locator("#template-filter")).toBeVisible();
    await expect(page.locator("#date-filter")).toBeVisible();
  });
});
