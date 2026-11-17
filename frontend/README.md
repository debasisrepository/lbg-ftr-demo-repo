# LBG Clear Path - Frontend

React + TypeScript + Vite frontend for the LBG Clear Path customer case management system.

## Purpose

Single-page application (SPA) providing authenticated mobile-app embedded experiences for:
- Customer case list and detail views
- Case history and continuity
- Service status and lifeline guidance
- Notification management
- Protected action workflows

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Carbon Design System** - IBM Carbon components and design tokens
- **Tailwind CSS** - Utility-first styling
- **React Router v6** - Client-side routing
- **Vitest** - Unit testing
- **Playwright** - End-to-end testing

## Structure

```
frontend/
├── src/
│   ├── lib/                    # Foundation modules (created before pages)
│   │   ├── api-client.ts       # Centralized API client
│   │   ├── auth-context.tsx    # Auth state and session management
│   │   ├── host-config.ts      # Brand configuration
│   │   └── utils.ts            # Utility functions (cn, formatters, badge colors)
│   ├── types/
│   │   └── api.ts              # TypeScript interfaces mirroring backend schemas
│   ├── components/
│   │   └── auth/
│   │       └── RequireAuth.tsx # Route guard
│   ├── routes/
│   │   └── login.tsx           # Login page
│   ├── app-router.tsx          # Route configuration
│   ├── main.tsx                # Application entry point
│   ├── index.css               # Global styles (Tailwind + Carbon)
│   └── vite-env.d.ts           # Vite type definitions
├── e2e/                        # Playwright E2E tests
│   └── smoke_login.spec.ts
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── postcss.config.js
├── playwright.config.ts
└── README.md
```

## Setup

### Prerequisites

- Node.js 20.19+ or 22.12+
- npm 9+

### Installation

```bash
cd frontend
npm install
```

## Development

### Run Development Server

From the frontend directory:

```bash
npm run dev
```

The dev server starts on port 5173 (or next available port) and proxies `/api` requests to the backend.

**Note:** The backend must be running for the frontend to authenticate and fetch data.

### Full Stack Development

Run both backend and frontend from the repository root:

```bash
./start.sh
```

This starts both servers with automatic port detection and proxy configuration.

## Testing

### Unit Tests

```bash
npm test
```

Runs Vitest tests for components and utilities.

### End-to-End Tests

```bash
npm run e2e
```

Runs Playwright tests. The Playwright config automatically starts both backend and frontend servers.

### Linting

```bash
npm run lint
```

## Build

### Production Build

```bash
npm run build
```

Outputs optimized static files to `dist/`.

### Preview Production Build

```bash
npm run preview
```

Serves the production build locally for verification.

## Configuration

### Environment Variables

- `VITE_API_URL` - API base URL (defaults to relative `/api` for same-origin)

See `.env.example` for details.

### Shared Configuration

The `shared_config.json` at the repository root defines:
- API base path (`/v1`)
- Auth endpoints and field names
- Pagination wrapper structure
- Token storage keys

## Auth Flow

1. User navigates to any protected route
2. `RequireAuth` guard checks for valid token
3. If no token, redirects to `/login`
4. Login form pre-filled with seed credentials: `admin@example.com` / `admin123`
5. On successful login, token stored in localStorage
6. User redirected to originally requested route (or `/cases` by default)

## API Integration

All API calls go through `src/lib/api-client.ts`:
- Base URL: `import.meta.env.VITE_API_URL ?? '/api'`
- Automatic Bearer token attachment
- 401 handling with redirect to login
- Consistent error shape

## Carbon Design System

The frontend uses IBM Carbon Design System:
- Components from `@carbon/react`
- Icons from `@carbon/icons-react`
- Design tokens from `@carbon/styles`

Carbon styles are imported in `src/index.css` and apply globally.

## Deployment

The frontend is built as a static SPA and can be:
- Served by nginx with `/api` proxy to backend
- Embedded in Lloyds and Bank of Scotland mobile apps
- Deployed to CDN with API on same origin or CORS-enabled separate origin

## Known Issues

None at this time.

## Contributing

Follow the repository's commit conventions and ensure all tests pass before committing.
