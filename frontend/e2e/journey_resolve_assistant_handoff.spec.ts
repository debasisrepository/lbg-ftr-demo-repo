import { test, expect } from '@playwright/test';

/**
 * End-to-end journey test for the Clear Path API contracts and data flow:
 * 1. Customer logs in through the form
 * 2. Customer can start a resolve session through the API
 * 3. Customer can request human help to create a Case
 * 4. Case appears in customer's My Cases list
 * 5. Colleague logs in and can view the Case in their worklist
 * 6. Thread continuity is maintained across customer and colleague views
 */

test.describe('Journey: Resolve → Assistant → Hand-off → Colleague Continuation', () => {
  test('API contract verification: customer resolve to colleague handoff', async ({ page }) => {
    // ========== PHASE 1: Customer logs in through the form ==========
    
    await page.goto('/login');
    await page.getByLabel('Email').fill('admin@example.com');
    await page.getByLabel('Password').fill('admin123');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Wait for redirect to home
    await page.waitForURL('/');
    
    const customerToken = await page.evaluate(() => {
      return localStorage.getItem('access_token');
    });
    expect(customerToken).toBeTruthy();
    
    console.log('✓ Customer logged in through form');
    
    // ========== PHASE 2: Customer starts resolve session ==========
    
    const resolveResponse = await page.request.post('/api/v1/resolve', {
      headers: {
        'Authorization': `Bearer ${customerToken}`,
      },
      data: {
        message_text: 'My card was declined and I need help understanding why.',
        status_context_shown: true,
      },
    });
    
    expect(resolveResponse.ok()).toBeTruthy();
    const resolveTurn = await resolveResponse.json();
    expect(resolveTurn.session_id).toBeTruthy();
    expect(resolveTurn.thread_id).toBeTruthy();
    expect(resolveTurn.ai_disclosure).toBeTruthy();
    expect(resolveTurn.human_path_shown).toBeTruthy();
    
    const sessionId = resolveTurn.session_id;
    console.log(`✓ Customer created resolve session: ${sessionId}`);
    
    // ========== PHASE 3: Customer requests human help ==========
    
    const humanRequestResponse = await page.request.post(`/api/v1/resolve/${sessionId}/human-request`, {
      headers: {
        'Authorization': `Bearer ${customerToken}`,
      },
      data: {},
    });
    
    if (!humanRequestResponse.ok()) {
      const errorText = await humanRequestResponse.text();
      console.error(`Human request failed with status ${humanRequestResponse.status()}: ${errorText}`);
    }
    expect(humanRequestResponse.ok()).toBeTruthy();
    const humanRequestData = await humanRequestResponse.json();
    expect(humanRequestData.case_ref).toBeTruthy();
    expect(humanRequestData.case_id).toBeTruthy();
    expect(humanRequestData.owner_team_display).toBeTruthy();
    expect(humanRequestData.expected_by_at).toBeTruthy();
    
    const caseRef = humanRequestData.case_ref;
    const caseId = humanRequestData.case_id;
    console.log(`✓ Customer created Case: ${caseRef} (ID: ${caseId})`);
    
    // Verify case_ref format: CP-YYYY-NNNNNN
    expect(caseRef).toMatch(/^CP-\d{4}-\d{6}$/);
    
    // ========== PHASE 4: Customer sees Case in My Cases list ==========
    
    const myCasesResponse = await page.request.get('/api/v1/cases', {
      headers: {
        'Authorization': `Bearer ${customerToken}`,
      },
    });
    
    expect(myCasesResponse.ok()).toBeTruthy();
    const myCasesData = await myCasesResponse.json();
    expect(myCasesData.items).toBeTruthy();
    expect(myCasesData.total).toBeGreaterThan(0);
    
    const customerCase = myCasesData.items.find((c: { case_ref: string }) => c.case_ref === caseRef);
    expect(customerCase).toBeTruthy();
    expect(customerCase.status).toBeTruthy();
    expect(customerCase.owner_team_display).toBeTruthy();
    
    console.log(`✓ Case ${caseRef} appears in customer's My Cases list`);
    
    // ========== PHASE 5: Colleague logs in through the form ==========
    
    await page.goto('/login');
    await page.getByLabel('Email').fill('colleague@example.com');
    await page.getByLabel('Password').fill('colleague123');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Wait for redirect to home
    await page.waitForURL('/');
    
    const colleagueToken = await page.evaluate(() => {
      return localStorage.getItem('access_token');
    });
    expect(colleagueToken).toBeTruthy();
    
    console.log('✓ Colleague logged in through form');
    
    // ========== PHASE 6: Colleague sees Case in worklist ==========
    
    const colleagueCasesResponse = await page.request.get('/api/v1/colleague/cases', {
      headers: {
        'Authorization': `Bearer ${colleagueToken}`,
      },
    });
    
    expect(colleagueCasesResponse.ok()).toBeTruthy();
    const colleagueCasesData = await colleagueCasesResponse.json();
    expect(colleagueCasesData.items).toBeTruthy();
    
    const colleagueCase = colleagueCasesData.items.find((c: { case_ref: string }) => c.case_ref === caseRef);
    expect(colleagueCase).toBeTruthy();
    
    console.log(`✓ Case ${caseRef} appears in colleague worklist`);
    
    // ========== PHASE 7: Colleague views hand-off pack ==========
    
    const handoffPackResponse = await page.request.get(`/api/v1/colleague/cases/${caseId}`, {
      headers: {
        'Authorization': `Bearer ${colleagueToken}`,
      },
    });
    
    expect(handoffPackResponse.ok()).toBeTruthy();
    const handoffPack = await handoffPackResponse.json();
    expect(handoffPack.case_ref).toBe(caseRef);
    expect(handoffPack.problem_statement).toBeTruthy();
    expect(handoffPack.classification_code).toBeTruthy();
    expect(handoffPack.handoff_summary_text).toBeTruthy();
    expect(handoffPack.owner_team_display).toBeTruthy();
    
    console.log(`✓ Colleague retrieved hand-off pack for ${caseRef}`);
    
    // ========== PHASE 8: Colleague views thread ==========
    
    const threadResponse = await page.request.get(`/api/v1/colleague/cases/${caseId}/thread`, {
      headers: {
        'Authorization': `Bearer ${colleagueToken}`,
      },
    });
    
    expect(threadResponse.ok()).toBeTruthy();
    const threadData = await threadResponse.json();
    expect(threadData.entries).toBeTruthy();
    expect(threadData.total).toBeGreaterThan(0);
    
    // Verify customer's original message is in transcript
    const customerEntry = threadData.entries.find((e: { role: string; content_text: string }) => 
      e.role === 'customer' && e.content_text.includes('card was declined')
    );
    expect(customerEntry).toBeTruthy();
    
    console.log(`✓ Colleague viewed thread with ${threadData.total} entries`);
    
    // ========== PHASE 9: Colleague posts a reply ==========
    
    const colleagueReplyText = 'Hi, I can help with your card decline. Let me check your account.';
    const replyResponse = await page.request.post(`/api/v1/colleague/cases/${caseId}/thread/entries`, {
      headers: {
        'Authorization': `Bearer ${colleagueToken}`,
      },
      data: {
        content_text: colleagueReplyText,
        visibility_scope: 'customer_visible',
      },
    });
    
    expect(replyResponse.ok()).toBeTruthy();
    const replyData = await replyResponse.json();
    expect(replyData.entry_id).toBeTruthy();
    expect(replyData.role).toBe('colleague');
    expect(replyData.content_text).toBe(colleagueReplyText);
    expect(replyData.visibility_scope).toBe('customer_visible');
    
    console.log(`✓ Colleague posted reply to ${caseRef}`);
    
    // ========== PHASE 10: Verify thread continuity ==========
    
    const updatedThreadResponse = await page.request.get(`/api/v1/colleague/cases/${caseId}/thread`, {
      headers: {
        'Authorization': `Bearer ${colleagueToken}`,
      },
    });
    
    expect(updatedThreadResponse.ok()).toBeTruthy();
    const updatedThread = await updatedThreadResponse.json();
    
    const colleagueReply = updatedThread.entries.find((e: { role: string; content_text: string }) => 
      e.role === 'colleague' && e.content_text === colleagueReplyText
    );
    expect(colleagueReply).toBeTruthy();
    expect(colleagueReply.visibility_scope).toBe('customer_visible');
    
    console.log(`✓ Journey complete: Customer → Resolve → Case ${caseRef} → Colleague → Reply → Thread continuity verified`);
  });
  
  test('contract verification: auth response matches frontend expectations', async ({ page }) => {
    // Log in through the form
    await page.goto('/login');
    await page.getByLabel('Email').fill('admin@example.com');
    await page.getByLabel('Password').fill('admin123');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Wait for redirect to home
    await page.waitForURL('/');
    
    const customerToken = await page.evaluate(() => {
      return localStorage.getItem('access_token');
    });
    expect(customerToken).toBeTruthy();
    
    console.log('✓ Logged in through form, have token');
    
    // Verify /me endpoint response shape
    const meResponse = await page.request.get('/api/v1/auth/me', {
      headers: {
        'Authorization': `Bearer ${customerToken}`,
      },
    });
    
    expect(meResponse.ok()).toBeTruthy();
    const userData = await meResponse.json();
    
    // Frontend expects these exact fields (from User interface)
    expect(userData.id).toBeTruthy();
    expect(userData.email).toBeTruthy();
    expect(typeof userData.is_active).toBe('boolean');
    expect(typeof userData.is_colleague).toBe('boolean');
    
    console.log('✓ User response matches frontend User interface');
  });
});
