# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 08-colleague-retrieval.spec.ts >> Colleague Case Retrieval >> colleague can access retrieval page after login
- Location: e2e/08-colleague-retrieval.spec.ts:4:3

# Error details

```
Error: expect(received).toBeTruthy()

Received: false
```

```
Error: API 422 GET /api/v1/auth/me - {"detail":[{"type":"missing","loc":["query","session_id"],"msg":"Field required","input":null}]} (2 API/browser error(s) in this test)
  - API 422 GET /api/v1/auth/me - {"detail":[{"type":"missing","loc":["query","session_id"],"msg":"Field required","input":null}]}
  - API 422 GET /api/v1/auth/me - {"detail":[{"type":"missing","loc":["query","session_id"],"msg":"Field required","input":null}]}
```

# Page snapshot

```yaml
- generic [ref=f1e5]:
  - heading "Sign in to LBG Clear Path" [level=1] [ref=f1e6]
  - generic [ref=f1e8]:
    - generic [ref=f1e9]:
      - generic [ref=f1e10]: Email or Username
      - generic [ref=f1e13]:
        - textbox "Email or Username" [ref=f1e14]: admin@example.com
        - alert [ref=f1e15]
    - generic [ref=f1e16]:
      - generic [ref=f1e17]: Password
      - generic [ref=f1e20]:
        - textbox "Password" [ref=f1e21]: admin123
        - alert [ref=f1e22]
    - button "Sign in" [ref=f1e23] [cursor=pointer]
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
      |           ^ Error: API 422 GET /api/v1/auth/me - {"detail":[{"type":"missing","loc":["query","session_id"],"msg":"Field required","input":null}]} (2 API/browser error(s) in this test)
  291 |       `${problems[0]} (${problems.length} API/browser error(s) in this test)\n` +
  292 |         problems.map((problem) => `  - ${problem}`).join('\n'),
  293 |     );
  294 |   },
  295 | });
  296 | 
```