# Clear Path Frontend

React + TypeScript + Vite frontend for the Clear Path MVP.

## Tech Stack

- **React 18**: UI library
- **TypeScript**: Type safety
- **Vite**: Build tool and dev server
- **Tailwind CSS**: Utility-first styling
- **React Router**: Client-side routing
- **Vitest**: Unit testing
- **Playwright**: E2E testing

## Setup

### Prerequisites

- Node.js 20.19+ or 22.12+
- npm 9+

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

Access at http://localhost:5173

## Scripts

```bash
# Development
npm run dev              # Start dev server with HMR
npm run build            # Build for production
npm run preview          # Preview production build

# Testing
npm test                 # Run unit tests (watch mode)
npm test -- --run        # Run unit tests (once)
npm run type-check       # TypeScript type checking
npm run lint             # ESLint

# E2E Tests
npx playwright install   # Install browsers (first time)
npx playwright test      # Run all E2E tests
npx playwright test --ui # Run with UI mode
npx playwright test --headed  # Run with browser visible
```

## Project Structure

```
src/
├── components/
│   ├── auth/            # Login, RequireAuth guard
│   ├── cases/           # Case list, detail, confirmation
│   ├── colleague/       # Colleague view components
│   ├── layout/          # Header, Sidebar, Layout
│   └── resolve/         # Resolve Assistant UI
├── lib/
│   ├── api-client.ts    # Centralized API client
│   ├── auth-context.tsx # Auth state management
│   └── utils.ts         # Utility functions
├── pages/
│   ├── CaseConfirmationPage.tsx
│   ├── CaseDetailPage.tsx
│   ├── ColleagueCasePage.tsx
│   ├── LoginPage.tsx
│   ├── MyCasesPage.tsx
│   ├── ResolvePage.tsx
│   └── ResolveSessionPage.tsx
├── types/
│   ├── auth.ts          # Auth types
│   ├── cases.ts         # Case types
│   ├── colleague.ts     # Colleague view types
│   └── resolve.ts       # Resolve types
├── App.tsx              # Root component with routing
├── main.tsx             # Application entry point
└── index.css            # Global styles
```

## Routing

```
/login                   - Login page
/                        - Dashboard (protected)
/resolve                 - Resolve Assistant intake (protected)
/resolve/:sessionId      - Resolve session conversation (protected)
/cases                   - My Cases list (protected)
/cases/:caseId           - Case detail (protected)
/case-confirmation       - Case confirmation screen (protected)
/colleague/cases         - Colleague worklist (protected, colleague role)
/colleague/cases/:caseId - Colleague hand-off pack (protected, colleague role)
```

## API Integration

### API Client

The frontend uses a centralized API client (`src/lib/api-client.ts`) that:
- Uses relative `/api` base URL (proxied by Vite dev server)
- Attaches JWT token from localStorage to all requests
- Handles 401 responses by redirecting to login
- Provides typed methods for all endpoints

### Authentication Flow

1. User submits login form
2. Frontend calls `POST /api/v1/auth/login`
3. Backend returns JWT token and user info
4. Frontend stores token in localStorage
5. API client attaches token to all subsequent requests
6. On 401 response, token is cleared and user redirected to login

### Example API Calls

```typescript
import { apiClient } from '@/lib/api-client';

// Login
const response = await apiClient.login('admin@example.com', 'admin123');

// Start resolve session
const session = await apiClient.startResolve({
  message_text: 'My card was declined',
  entry_context_type: null,
  entry_context_ref: null,
  status_context_shown: false
});

// List cases
const cases = await apiClient.listCases(0, 10);
```

## Styling

### Tailwind Configuration

Design tokens are extracted from wireframes and configured in `tailwind.config.js`:

- **Colors**: `--ink`, `--primary`, `--surface`, `--paper`, `--accent`, `--error`, `--warning`, `--success`
- **Spacing**: `--s1` through `--s6` (4px to 96px)
- **Typography**: System fonts with fallbacks

### CSS Custom Properties

Additional design tokens in `src/index.css`:

```css
:root {
  --ink: #1a1a1a;
  --primary: #0066cc;
  --surface: #f5f5f5;
  --paper: #ffffff;
  /* ... */
}
```

### Component Styling Patterns

```typescript
// Use Tailwind utilities with cn() helper
import { cn } from '@/lib/utils';

<div className={cn(
  "p-4 rounded-lg",
  isActive && "bg-primary text-white",
  isDisabled && "opacity-50 cursor-not-allowed"
)}>
  {children}
</div>
```

## Testing

### Unit Tests (Vitest + React Testing Library)

```typescript
// src/__tests__/ResolvePage.test.tsx
import { render, screen } from '@testing-library/react';
import { ResolvePage } from '@/pages/ResolvePage';

test('renders intake form', () => {
  render(<ResolvePage />);
  expect(screen.getByRole('textbox')).toBeInTheDocument();
});
```

Run tests:
```bash
npm test -- --run
npm test src/__tests__/ResolvePage.test.tsx -- --run
```

### E2E Tests (Playwright)

```typescript
// e2e/smoke_login.spec.ts
import { test, expect } from '@playwright/test';

test('successful login redirects to dashboard', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'admin@example.com');
  await page.fill('[name="password"]', 'admin123');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('/');
});
```

Run E2E tests:
```bash
npx playwright test
npx playwright test e2e/smoke_login.spec.ts
npx playwright test --ui
```

## Default Credentials

**Customer:**
- Email: `admin@example.com`
- Password: `admin123`

**Colleague:**
- Email: `colleague@example.com`
- Password: `colleague123`

## Environment Variables

The frontend does NOT require environment variables for local development. The API client uses relative URLs (`/api`) which are proxied by the Vite dev server.

For production, the nginx configuration in the Docker image handles proxying `/api` to the backend service.

## Build & Deploy

### Development Build

```bash
npm run build
npm run preview  # Serve production build locally
```

### Docker Build

```bash
# Build image
docker build -t clear-path-frontend .

# Run container
docker run -p 80:80 \
  -e BACKEND_HOST=backend \
  clear-path-frontend
```

### Production Build

The production build:
- Minifies JavaScript and CSS
- Optimizes assets
- Generates source maps
- Uses nginx to serve static files and proxy API requests

## Development Tips

### Hot Module Replacement (HMR)

Vite provides fast HMR. Changes to components are reflected instantly without full page reload.

### Type Checking

Run type check before committing:
```bash
npm run type-check
```

### Linting

Fix linting issues:
```bash
npm run lint
```

### API Proxy

The Vite dev server proxies `/api` requests to the backend. Configure the backend port in `vite.config.ts` or set `BACKEND_PORT` environment variable before starting the dev server.

### Browser DevTools

- React DevTools: Install browser extension for component inspection
- Redux DevTools: Not used in this project (using Context API)

## Troubleshooting

### Port Already in Use

```bash
# Use different port
npm run dev -- --port 3000
```

### API Connection Issues

Ensure backend is running:
```bash
cd ../backend
uvicorn app.main:app --reload --port 9000
```

Check proxy configuration in `vite.config.ts`.

### Build Errors

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
```

### TypeScript Errors

```bash
# Rebuild TypeScript
npm run type-check

# Update TypeScript
npm install -D typescript@latest
```

## Wireframe Implementation

The frontend implements four wireframes:

1. **Wireframe 01**: Resolve Assistant intake screen
2. **Wireframe 02**: Assistant turn response with findings and proposals
3. **Wireframe 03**: Case confirmation with hero section and three-panel info
4. **Wireframe 04**: Colleague hand-off pack with three-column layout

Each wireframe is implemented to match the exact HTML structure, CSS, layout, colors, spacing, and content from the design artifacts.
