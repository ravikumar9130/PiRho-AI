# piRho SaaS Frontend

Next.js 14 dashboard for the piRho Trading Bot SaaS platform.

## Features

- Next.js 14 App Router with TypeScript
- Tailwind CSS styling
- NextAuth.js authentication
- Recharts for data visualization
- Sentry error monitoring
- Responsive dashboard UI

## Setup

### 1. Install Dependencies

```bash
cd saas-frontend
npm install
```

### 2. Configure Environment

Copy the example environment file:

```bash
cp env.local.example .env.local
```

Required environment variables:
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXTAUTH_URL` - Your app URL
- `NEXTAUTH_SECRET` - NextAuth secret (min 32 chars)
- `NEXT_PUBLIC_SENTRY_DSN` - Sentry DSN (optional)

### 3. Run Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## Testing

```bash
npm test
```

## Deployment (Vercel)

1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Vercel will auto-deploy on push

## Project Structure

```
saas-frontend/
├── src/
│   ├── app/
│   │   ├── (auth)/          # Auth pages
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── api/auth/        # NextAuth API
│   │   ├── dashboard/       # Dashboard pages
│   │   │   ├── bots/
│   │   │   ├── positions/
│   │   │   ├── history/
│   │   │   ├── billing/
│   │   │   └── settings/
│   │   ├── pricing/
│   │   ├── layout.tsx
│   │   ├── page.tsx         # Landing page
│   │   └── globals.css
│   ├── components/
│   │   └── dashboard/
│   │       ├── Sidebar.tsx
│   │       └── Header.tsx
│   ├── lib/
│   │   ├── api.ts           # API client
│   │   └── utils.ts         # Utilities
│   └── middleware.ts        # Auth middleware
├── __tests__/               # Test suite
├── tailwind.config.ts
├── next.config.js
└── package.json
```

## Pages

| Route | Description |
|-------|-------------|
| `/` | Landing page |
| `/login` | Sign in |
| `/register` | Sign up |
| `/pricing` | Pricing plans |
| `/dashboard` | Overview stats |
| `/dashboard/bots` | Manage trading bots |
| `/dashboard/positions` | Active positions |
| `/dashboard/history` | Trade history |
| `/dashboard/billing` | Subscription management |
| `/dashboard/settings` | API keys & settings |

