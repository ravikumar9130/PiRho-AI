# piRho SaaS Backend

FastAPI backend for the piRho Trading Bot SaaS platform.

## Features

- JWT Authentication with refresh tokens
- Supabase PostgreSQL database
- Encrypted API key storage (AES-256)
- Stripe billing integration
- In-memory caching and rate limiting
- Sentry error monitoring

## Setup

### 1. Install Dependencies

```bash
cd saas-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and fill in your values:

```bash
cp env.example.txt .env
```

Required environment variables:
- `SECRET_KEY` - App secret key
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Supabase anon key
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `JWT_SECRET_KEY` - JWT signing key (min 32 chars)
- `STRIPE_SECRET_KEY` - Stripe secret key
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook secret
- `STRIPE_PRICE_*` - Stripe price IDs for each plan
- `ENCRYPTION_KEY` - Fernet key for API key encryption

Generate an encryption key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Set Up Database

Run the schema in your Supabase SQL Editor:

```bash
cat supabase_schema.sql
# Copy and paste into Supabase SQL Editor
```

### 4. Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

When running in development mode (DEBUG=true), access:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

## Testing

```bash
pytest tests/ -v
```

## Deployment

### Koyeb (Recommended)

See the main [KOYEB_DEPLOYMENT.md](../KOYEB_DEPLOYMENT.md) guide for detailed instructions.

Quick steps:
1. Push your code to GitHub/GitLab
2. Create a new service in Koyeb dashboard
3. Select your repository and set root directory to `piRho-backend`
4. Configure as **Web Service** with port `8000`
5. Set all environment variables from `env.example.txt`
6. Deploy!

### Railway (Alternative)

1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Railway will auto-detect the Python app and deploy

## Project Structure

```
saas-backend/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/
│   │   │   ├── auth.py      # Authentication
│   │   │   ├── users.py     # User management
│   │   │   ├── bots.py      # Trading bots
│   │   │   ├── trades.py    # Trade history
│   │   │   └── billing.py   # Stripe billing
│   │   ├── deps.py          # Dependencies
│   │   └── router.py        # API router
│   ├── core/
│   │   ├── cache.py         # In-memory cache
│   │   ├── database.py      # Supabase client
│   │   └── security.py      # Auth & encryption
│   ├── models/              # Pydantic schemas
│   ├── config.py            # Settings
│   └── main.py              # FastAPI app
├── tests/                   # Test suite
├── requirements.txt
└── supabase_schema.sql      # Database schema
```

