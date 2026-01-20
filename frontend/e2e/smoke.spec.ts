import { test, expect } from '@playwright/test'

test.describe('Smoke Tests', () => {
  test('home page loads', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle(/Scribe/)
  })

  test('dashboard is accessible', async ({ page }) => {
    await page.goto('/dashboard')
    // Wait for the page to load
    await page.waitForLoadState('networkidle')
    // Dashboard should show documents section
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  })

  test('knowledge base is accessible', async ({ page }) => {
    await page.goto('/knowledge')
    await page.waitForLoadState('networkidle')
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  })

  test('data page is accessible', async ({ page }) => {
    await page.goto('/data')
    await page.waitForLoadState('networkidle')
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  })
})
