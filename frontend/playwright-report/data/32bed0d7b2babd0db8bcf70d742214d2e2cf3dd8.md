# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: wireframe_05_j01_s05.spec.ts >> Wireframe 05 - Payment Entry and Approval (FR-005) >> should show inline error when amount exceeds balance
- Location: e2e/wireframe_05_j01_s05.spec.ts:61:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('text=/Payment amount exceeds/i')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('text=/Payment amount exceeds/i') with timeout 5000ms
  - waiting for locator('text=/Payment amount exceeds/i')

```

```yaml
- banner:
  - button "Back to payees"
  - text: Your Bank
- main:
  - heading "Make a payment" [level=1]
  - paragraph: Jamie Clarke
  - paragraph: 04-00-04 · ****3746
  - text: From
  - textbox "From": Admin Current Account · 12-34-56 | ****1234
  - paragraph: Available balance £1,248.36
  - text: Amount
  - textbox "Amount": "1500.00"
  - paragraph: Payments are in pounds sterling (GBP).
  - text: Reference (optional)
  - textbox "Reference (optional)"
  - paragraph: Up to 18 characters.
  - status:
    - img "info icon"
    - text: You'll approve with Face ID Your approval is tied to Jamie Clarke and £1500.00. If you change either, you'll need to approve again.
  - status:
    - img "error icon"
    - text: Error Internal Server Error
  - button "Pay £1,500.00"
```

```
Error: API 500 POST /api/v1/payments/prepare - Internal Server Error (1 API/browser error(s) in this test)
  - API 500 POST /api/v1/payments/prepare - Internal Server Error
```

# Test source

```ts
  190 |         observeBody(state, status, url, `${request.method()} ${pathOf(url)}`, pending);
  191 |         return;
  192 |       }
  193 |       state.observed.push({
  194 |         status,
  195 |         url,
  196 |         describe: async () => {
  197 |           if (status === 401 && !(await request.headerValue('authorization'))) return null;
  198 |           let detail = '';
  199 |           try {
  200 |             detail = (await response.text()).replace(/\s+/g, ' ').trim().slice(0, 200);
  201 |           } catch {
  202 |             // The body can be gone once the page navigated; the status is enough.
  203 |           }
  204 |           return `API ${status} ${request.method()} ${pathOf(url)}${detail ? ` - ${detail}` : ''}`;
  205 |         },
  206 |       });
  207 |     });
  208 | 
  209 |     page.on('requestfailed', (request) => {
  210 |       const url = request.url();
  211 |       if (!isApi(url)) return;
  212 |       const reason = request.failure()?.errorText || 'no response';
  213 |       // Navigating away cancels in-flight requests; that is not an app defect.
  214 |       if (/ERR_ABORTED|NS_BINDING_ABORTED|cancelled/i.test(reason)) return;
  215 |       state.observed.push({
  216 |         status: 0,
  217 |         url,
  218 |         describe: async () =>
  219 |           `API request failed ${request.method()} ${pathOf(url)} - ${reason} (wrong base URL or CORS?)`,
  220 |       });
  221 |     });
  222 | 
  223 |     page.on('pageerror', (error) => {
  224 |       state.pageErrors.push(`Uncaught page error - ${error.message}`);
  225 |     });
  226 | 
  227 |     // `page.request` goes through Playwright's API client and fires none of the
  228 |     // page's events: a spec that polled a scan with `page.request.get` showed the
  229 |     // guard nothing while every poll said the scan had crashed. Wrapped once per
  230 |     // client; the state it reports to is this test's.
  231 |     const client = page.request as unknown as Record<string | symbol, unknown>;
  232 |     client[GUARD_STATE] = state;
  233 |     if (!client.__pipelineGuardWrapped) {
  234 |       client.__pipelineGuardWrapped = true;
  235 |       for (const method of ['get', 'post', 'put', 'patch', 'delete', 'head', 'fetch']) {
  236 |         const original = client[method];
  237 |         if (typeof original !== 'function') continue;
  238 |         client[method] = async (...args: unknown[]) => {
  239 |           const response = await (original as (...a: unknown[]) => Promise<any>).apply(page.request, args);
  240 |           const current = client[GUARD_STATE] as GuardState | undefined;
  241 |           const url: string = response.url();
  242 |           if (!current || !isApi(url)) return response;
  243 |           const status: number = response.status();
  244 |           const label = `${method === 'fetch' ? 'FETCH' : method.toUpperCase()} ${pathOf(url)} (page.request)`;
  245 |           if (status >= 400) {
  246 |             // A spec calling an authenticated endpoint without its token is a
  247 |             // spec mistake, not an app defect; every other status is reported.
  248 |             if (status === 401) return response;
  249 |             const detail = await response
  250 |               .text()
  251 |               .then((text: string) => text.replace(/\s+/g, ' ').trim().slice(0, 200))
  252 |               .catch(() => '');
  253 |             current.observed.push({
  254 |               status,
  255 |               url,
  256 |               describe: async () => `API ${status} ${label}${detail ? ` - ${detail}` : ''}`,
  257 |             });
  258 |           } else if (/json/i.test(response.headers()['content-type'] || '')) {
  259 |             observeBody(current, status, url, label, response.json().catch(() => null));
  260 |           }
  261 |           return response;
  262 |         };
  263 |       }
  264 |     }
  265 | 
  266 |     await use(page);
  267 | 
  268 |     const problems: string[] = [];
  269 |     for (const item of state.observed) {
  270 |       const permitted = item.crash
  271 |         ? false
  272 |         : item.failedState
  273 |           ? state.allowedFailedStates.some((urlPart) => item.url.includes(urlPart))
  274 |           : state.allowed.some(
  275 |               (rule) => rule.status === item.status && item.url.includes(rule.urlPart),
  276 |             );
  277 |       if (permitted) continue;
  278 |       const line = await item.describe().catch(() => `API ${item.status} ${pathOf(item.url)}`);
  279 |       if (line) problems.push(line);
  280 |     }
  281 |     problems.push(...state.pageErrors);
  282 |     if (problems.length === 0) return;
  283 | 
  284 |     await testInfo.attach('api-guard.json', {
  285 |       body: JSON.stringify({ problems, allowed: state.allowed }, null, 2),
  286 |       contentType: 'application/json',
  287 |     });
  288 |     // The first line is what the pipeline's failing-test list shows, so it names
  289 |     // the first problem rather than a count alone.
> 290 |     throw new Error(
      |           ^ Error: API 500 POST /api/v1/payments/prepare - Internal Server Error (1 API/browser error(s) in this test)
  291 |       `${problems[0]} (${problems.length} API/browser error(s) in this test)\n` +
  292 |         problems.map((problem) => `  - ${problem}`).join('\n'),
  293 |     );
  294 |   },
  295 | });
  296 | 
```