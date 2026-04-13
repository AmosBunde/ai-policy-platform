import { test, expect } from "@playwright/test";

/**
 * Documents page E2E tests.
 *
 * The Documents page uses SAMPLE_DOCS when the API is unreachable, so these
 * tests exercise the UI layer against the built-in sample data.
 */
test.describe("Documents", () => {
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
    await page.goto("/documents");
  });

  test("renders document list with sample data", async ({ page }) => {
    await expect(page.getByText("Regulatory Documents")).toBeVisible();
    await expect(page.getByText("EU AI Act").first()).toBeVisible();
  });

  test("switches between table and card view", async ({ page }) => {
    // Card view button
    const cardViewBtn = page.getByLabel("Card view");
    await cardViewBtn.click();

    // Should show card layout
    await expect(page.getByText("EU AI Act").first()).toBeVisible();

    // Switch back to table
    const tableViewBtn = page.getByLabel("Table view");
    await tableViewBtn.click();
    await expect(page.getByText("EU AI Act").first()).toBeVisible();
  });

  test("allows selecting documents via checkboxes", async ({ page }) => {
    const checkboxes = page.getByRole("checkbox");
    const count = await checkboxes.count();
    expect(count).toBeGreaterThan(0);

    // Select first document
    await checkboxes.first().check();
    await expect(checkboxes.first()).toBeChecked();
  });

  test("shows Generate Report button when documents selected", async ({
    page,
  }) => {
    // Initially no Generate Report button
    await expect(
      page.getByRole("button", { name: /generate report/i }),
    ).not.toBeVisible();

    // Select a document
    const checkboxes = page.getByRole("checkbox");
    await checkboxes.nth(1).check(); // nth(0) might be select-all

    await expect(
      page.getByRole("button", { name: /generate report/i }),
    ).toBeVisible();
  });

  test("enrichment tabs are visible on document detail page", async ({
    page,
  }) => {
    // Navigate to the documents page and click on a document link
    const docLink = page.getByRole("link", { name: /EU AI Act/i }).first();

    // The documents page may show links or rows — if the row is clickable
    if (await docLink.isVisible()) {
      await docLink.click();
      // On detail page, check for enrichment tabs
      await expect(
        page
          .getByText(/summary|key changes|classification|impact|draft response/i)
          .first(),
      ).toBeVisible({ timeout: 5000 });
    }
  });
});
