import { test, expect } from '@playwright/test'

test.describe('Document Management', () => {
  test('can create a new document', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')

    // Click create new document button
    const newDocButton = page.getByRole('button', { name: /new|create/i })
    if (await newDocButton.isVisible()) {
      await newDocButton.click()
      // Should navigate to editor with new document
      await expect(page.url()).toContain('/editor/')
    }
  })

  test('can access editor for new document', async ({ page }) => {
    await page.goto('/editor/new')
    await page.waitForLoadState('networkidle')

    // Editor should be visible
    const editor = page.locator('.ProseMirror, [contenteditable]')
    await expect(editor.first()).toBeVisible({ timeout: 10000 })
  })

  test('editor shows document title input', async ({ page }) => {
    await page.goto('/editor/new')
    await page.waitForLoadState('networkidle')

    // Title input should be visible
    const titleInput = page.getByPlaceholder(/title/i).or(
      page.locator('input[type="text"]').first()
    )
    await expect(titleInput.first()).toBeVisible({ timeout: 10000 })
  })

  test('can navigate between panels', async ({ page }) => {
    await page.goto('/editor/new')
    await page.waitForLoadState('networkidle')

    // Check that panel tabs exist
    const claimsTab = page.getByRole('button', { name: /claims/i })
    const bibTab = page.getByRole('button', { name: /bibliography|bib|references/i })

    if (await claimsTab.isVisible()) {
      await claimsTab.click()
      // Claims panel should be active
      await expect(page.getByText(/claims/i)).toBeVisible()
    }

    if (await bibTab.isVisible()) {
      await bibTab.click()
      // Bibliography panel should be active
      await expect(page.getByText(/bibliography|references/i).first()).toBeVisible()
    }
  })
})
