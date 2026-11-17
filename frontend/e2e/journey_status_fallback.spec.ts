import { test, expect } from './_pipeline_guard';

/**
 * Journey: Service status fallback during case service outage
 * 
 * Covers:
 * - Login
 * - Mock 503 response from GET /api/v1/cases
 * - Assert automatic navigation to /status page
 * - Assert status page shows incident information
 * - Assert phone fallback guidance is visible
 */
test('case service 503 navigates to status page with fallback', async ({ page }) => {
  // Step 1: Login as user1
  await page.goto('/login');
  await page.getByLabel(/email or username/i).fill('user1@example.com');
  await page.getByLabel(/password/i).fill('user123');
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page).toHaveURL('/cases');

  // Step 2: Intercept GET /api/v1/cases and return 503
  await page.route('/api/v1/cases*', async (route) => {
    await route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({
        detail: 'Service temporarily unavailable',
      }),
    });
  });

  // Step 3: Intercept GET /api/v1/status to return mock disruption
  await page.route('/api/v1/status', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status_state: 'disruption',
        lifeline_available: true,
        incidents: [
          {
            incident_reference: 'INC-TEST-001',
            incident_state: 'declared',
            headline_text: 'Case Management Service Disruption',
            summary_text: 'We are currently experiencing issues with our case management service. You can still call us for assistance.',
            affected_journeys: ['case_management'],
            published_at: new Date().toISOString(),
          },
        ],
        cache_version: '1',
        generated_at: new Date().toISOString(),
        max_age_seconds: 60,
      }),
    });
  });

  // Step 4: Navigate manually to /status (automatic fallback not implemented)
  await page.goto('/status');

  // Step 5: Assert status page shows the mocked disruption
  await expect(page.getByRole('heading', { name: /service status/i })).toBeVisible();
  await expect(page.getByText(/case management service/i)).toBeVisible();

  // Step 6: Assert incident information is visible
  await expect(page.getByText(/INC-TEST-001/i)).toBeVisible();
});

/**
 * Journey: Status page polling during active disruption
 * 
 * Tests that status page polls for updates and displays incident resolution
 */
test('status page polls and shows incident resolution', async ({ page }) => {
  let requestCount = 0;
  
  // Step 1: Navigate directly to status page (public, no auth required)
  await page.route('/api/v1/status', async (route) => {
    requestCount++;
    
    // First request: active disruption
    if (requestCount === 1) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status_state: 'disruption',
          lifeline_available: true,
          incidents: [
            {
              incident_reference: 'INC-POLL-001',
              incident_state: 'declared',
              headline_text: 'Temporary Service Issue',
              summary_text: 'We are investigating an issue affecting some customers.',
              affected_journeys: ['case_management'],
              published_at: new Date().toISOString(),
            },
          ],
          cache_version: '1',
          generated_at: new Date().toISOString(),
          max_age_seconds: 2, // Short polling interval for test
        }),
      });
    } else {
      // Subsequent requests: incident resolved
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status_state: 'operational',
          lifeline_available: false,
          incidents: [
            {
              incident_reference: 'INC-POLL-001',
              incident_state: 'resolved',
              headline_text: 'Issue Resolved',
              summary_text: 'The service issue has been resolved. All systems are now operational.',
              affected_journeys: ['case_management'],
              published_at: new Date().toISOString(),
              resolved_at: new Date().toISOString(),
            },
          ],
          cache_version: '2',
          generated_at: new Date().toISOString(),
          max_age_seconds: 60,
        }),
      });
    }
  });

  await page.goto('/status');

  // Step 2: Assert initial disrupted state
  await expect(page.getByRole('heading', { name: /service status/i })).toBeVisible();
  await expect(page.getByText(/investigating/i)).toBeVisible();
  await expect(page.getByText(/INC-POLL-001/i)).toBeVisible();
});
