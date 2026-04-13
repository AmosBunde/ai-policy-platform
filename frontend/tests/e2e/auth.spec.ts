import { test, expect } from "@playwright/test";

test.describe("Authentication", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
  });

  test("shows login form with email and password fields", async ({ page }) => {
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
    await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();
  });

  test("rejects invalid credentials with error message", async ({ page }) => {
    await page.getByLabel("Email").fill("invalid@test.com");
    await page.getByLabel("Password").fill("WrongPassword1");
    await page.getByRole("button", { name: /sign in/i }).click();

    await expect(
      page.getByText(/invalid|error|failed/i).first(),
    ).toBeVisible({ timeout: 5000 });
  });

  test("validates empty form submission", async ({ page }) => {
    await page.getByRole("button", { name: /sign in/i }).click();

    // Form validation should prevent submission or show errors
    await expect(page.locator("[role='alert'], .text-danger").first()).toBeVisible({
      timeout: 3000,
    });
  });

  test("navigates to register page", async ({ page }) => {
    await page.getByRole("link", { name: /register/i }).click();
    await expect(page).toHaveURL(/register/);
    await expect(page.getByLabel("Full Name")).toBeVisible();
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
    await expect(page.getByLabel("Confirm Password")).toBeVisible();
  });

  test("navigates to forgot password page", async ({ page }) => {
    await page.getByRole("link", { name: /forgot password/i }).click();
    await expect(page).toHaveURL(/forgot-password/);
    await expect(page.getByText("Reset Password")).toBeVisible();
  });

  test("register form shows password strength indicator", async ({ page }) => {
    await page.goto("/register");
    await page.getByLabel("Password").fill("MyStr0ng!Pass");
    await expect(page.getByText(/strong/i)).toBeVisible();
  });

  test("register form validates password confirmation mismatch", async ({
    page,
  }) => {
    await page.goto("/register");
    await page.getByLabel("Full Name").fill("Test User");
    await page.getByLabel("Email").fill("test@example.com");
    await page.getByLabel("Password").fill("SecurePass1!");
    await page.getByLabel("Confirm Password").fill("DifferentPass1!");
    await page.getByRole("button", { name: /create account|register|sign up/i }).click();

    await expect(
      page.getByText(/match|mismatch/i).first(),
    ).toBeVisible({ timeout: 3000 });
  });

  test("redirects unauthenticated users to login", async ({ page }) => {
    await page.goto("/documents");
    await expect(page).toHaveURL(/login/);
  });

  test("session persistence — login state reflected in URL", async ({
    page,
  }) => {
    // Unauthenticated user hitting a protected page should get redirected
    await page.goto("/settings");
    await expect(page).toHaveURL(/login/);
    // returnUrl should be preserved
    const url = page.url();
    expect(url).toContain("returnUrl");
  });
});
