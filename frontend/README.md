# Frontend - Receivables & Collections Application

React + TypeScript + Vite frontend for the Intelligent Receivables and Collections Application.

## Tech Stack

- **Framework**: React 18.3
- **Build Tool**: Vite 6
- **Language**: TypeScript 5.6
- **Styling**: Tailwind CSS 3.4
- **Router**: React Router 6
- **Testing**: Vitest + React Testing Library + Playwright

## Project Structure

```
frontend/
├── src/
│   ├── main.tsx                 # Entry point
│   ├── App.tsx                  # Route configuration
│   ├── lib/
│   │   ├── api-client.ts        # Centralized API client (base /api)
│   │   ├── auth-context.tsx     # Auth state provider
│   │   └── format.ts            # Formatting utilities
│   ├── components/
│   │   ├── auth/
│   │   │   └── RequireAuth.tsx  # Route guard
│   │   └── layout/
│   │       ├── AppShell.tsx     # Main layout wrapper
│   │       ├── Header.tsx       # Top navigation
│   │       └── Sidebar.tsx      # Side navigation
│   ├── pages/
│   │   └── SignInPage.tsx       # Login page
│   ├── types/
│   │   ├── auth.ts              # Auth type definitions
│   │   └── common.ts            # Common types
│   └── __tests__/               # Unit tests
├── e2e/                         # End-to-end tests
│   └── smoke_login.spec.ts
├── vite.config.ts               # Vite configuration with /api proxy
├── vitest.config.ts             # Vitest configuration
├── playwright.config.ts         # Playwright configuration
└── tailwind.config.js           # Tailwind theme
```

## Development

### Prerequisites

- Node.js 20.19+ or 22.12+
- Backend running on port 9000 (or set BACKEND_PORT env var)

### Setup

```bash
npm install
```

### Run Dev Server

```bash
npm run dev
```

Frontend will be available at http://localhost:5173

### Build

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Testing

### Unit Tests

```bash
npm test
```

### Type Check

```bash
npm run type-check
```

### Lint

```bash
npm run lint
```

### End-to-End Tests

```bash
# Install Playwright browsers (first time only)
npx playwright install chromium

# Run e2e tests
npx playwright test
```

## API Integration

- **API Base**: `/api` (proxied to backend in dev, forwarded by nginx in production)
- **Auth**: Bearer token stored in localStorage (`access_token` key)
- **Error Handling**: 401 responses clear token and redirect to /login

## Environment Variables

- `VITE_API_URL`: Optional. Defaults to `/api` for same-origin proxying
- `BACKEND_PORT`: Used by vite.config.ts proxy (read from process.env via start.sh)

## Demo Credentials

- Analyst: `analyst1` / `analyst123`
- Reviewer: `reviewer1` / `reviewer123`
