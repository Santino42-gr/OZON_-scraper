# Fix Recommendations - OZON Scraper System

**Date:** 2025-11-05
**Priority Levels:** 🔴 Critical | 🟡 High | 🟢 Medium | 🔵 Low

---

## 🟡 Issue #1: Telegram Bot Instance Conflict

### Problem
Bot fails to start with error:
```
TelegramConflictError: Conflict: terminated by other getUpdates request;
make sure that only one bot instance is running
```

### Root Cause
Multiple bot instances are trying to use the same Telegram bot token simultaneously, or a webhook is configured while trying to run in polling mode.

### Solution

#### Step 1: Find and Kill Existing Bot Instance
```bash
# Find running bot process
ps aux | grep -E "bot.*python|python.*bot/main" | grep -v grep

# If found, kill it
kill <PID>

# Or force kill if needed
kill -9 <PID>
```

#### Step 2: Clear Telegram Webhook
```bash
# Replace <TOKEN> with your actual bot token
curl -X POST "https://api.telegram.org/bot<TOKEN>/deleteWebhook?drop_pending_updates=true"

# Verify webhook is deleted
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

#### Step 3: Restart Bot Properly
```bash
cd /Users/sasha/Library/Mobile\ Documents/com~apple~CloudDocs/AIronLab/Cursor/OZON_\ scraper/bot

# Start bot
python3 main.py

# Or run in background
nohup python3 main.py > bot.log 2>&1 &

# Check logs
tail -f bot.log
```

#### Step 4: Implement Process Management (Recommended)
Create a systemd service (Linux) or launchd service (macOS):

**macOS launchd example:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ozon.telegram.bot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/path/to/bot/main.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/path/to/bot</string>
    <key>StandardOutPath</key>
    <string>/var/log/ozon-bot.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/ozon-bot-error.log</string>
</dict>
</plist>
```

### Verification
```bash
# Bot should show these logs:
# ✅ Backend API connected: http://localhost:8000
# ✅ Bot mode: POLLING
# ✅ Environment: development
# (No conflict errors)
```

### Prevention
- Only run one bot instance at a time
- Use process management tools
- Monitor bot status in production
- Implement health checks

---

## 🟢 Issue #2: Frontend Not Running

### Problem
Admin panel is not accessible because the frontend service is not running.

### Solution

#### Option 1: Development Mode (Quick Start)
```bash
cd /Users/sasha/Library/Mobile\ Documents/com~apple~CloudDocs/AIronLab/Cursor/OZON_\ scraper/frontend

# Install dependencies (if needed)
npm install

# Start development server
npm run dev

# Should output:
# VITE v4.x.x  ready in xxx ms
# ➜  Local:   http://localhost:5173/
# ➜  Network: http://192.168.x.x:5173/
```

#### Option 2: Production Build
```bash
cd frontend

# Build for production
npm run build

# Serve with simple HTTP server
npx serve -s dist -p 5173

# Or use nginx/caddy for production
```

#### Option 3: Docker (Recommended for Production)
```bash
cd /Users/sasha/Library/Mobile\ Documents/com~apple~CloudDocs/AIronLab/Cursor/OZON_\ scraper

# Start all services with Docker Compose
docker-compose up -d

# Check frontend container
docker logs ozon-frontend

# Access at http://localhost:5173
```

### Verification
```bash
# Check port is listening
lsof -i :5173

# Should show:
# COMMAND   PID  USER   FD   TYPE  DEVICE SIZE/OFF NODE NAME
# node    xxxxx sasha   xx   IPv4  xxxxxx      0t0  TCP *:5173 (LISTEN)

# Test in browser
curl http://localhost:5173

# Should return HTML
```

### Environment Configuration
Verify `.env` file in frontend directory:
```env
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://kknxajmrtexzzlqgvlxg.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGci...
```

---

## 🟡 Issue #3: CORS Configuration

### Problem
CORS headers not properly configured for OPTIONS requests, may block browser API calls from frontend.

### Current State
```
❌ Access-Control-Allow-Origin: Not set for all origins
❌ Access-Control-Allow-Methods: Not properly configured
❌ Access-Control-Allow-Headers: Not set
```

### Solution

#### Update Backend CORS Configuration
Edit `/backend/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="OZON Bot API",
    description="API for OZON price monitoring bot",
    version="1.0.0"
)

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# ... rest of the app
```

#### Update Environment Variables
Edit `.env`:
```env
# Development
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Production (update when deployed)
# CORS_ORIGINS=https://your-domain.com,https://admin.your-domain.com
```

### Verification
```bash
# Test OPTIONS request
curl -X OPTIONS http://localhost:8000/api/v1/articles/ \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: GET" \
  -v

# Should return:
# < HTTP/1.1 200 OK
# < access-control-allow-origin: http://localhost:5173
# < access-control-allow-methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
# < access-control-allow-headers: *
# < access-control-allow-credentials: true
```

### Test from Frontend
```javascript
// In browser console (on http://localhost:5173)
fetch('http://localhost:8000/api/v1/articles/')
  .then(r => r.json())
  .then(data => console.log('Success:', data))
  .catch(err => console.error('CORS Error:', err));

// Should succeed without CORS errors
```

---

## 🟢 Issue #4: Article Creation with Test SKU

### Problem
Cannot create articles with fake/test SKUs because API validates with real OZON.

### Current Behavior
```json
{
  "error": "Товар не найден в OZON",
  "status_code": 404
}
```

### Solutions

#### Option 1: Use Real OZON SKUs (Recommended)
Find currently available OZON products:

```bash
# Test with known good SKUs
# Example: Popular electronics, books, etc.
# Visit OZON.ru and copy article number from URL

# URL format: https://www.ozon.ru/product/name-ARTICLE/
# Example: https://www.ozon.ru/product/iphone-15-1234567890/
# Article: 1234567890
```

**Test Articles (verify they exist first):**
- Search OZON for popular products
- Copy article number from URL
- Use in API tests

#### Option 2: Mock Mode for Testing (Development Only)
Add environment variable for mock mode:

Edit `/backend/.env`:
```env
ENABLE_MOCK_MODE=true  # Only for development/testing
```

Edit `/backend/routers/articles.py`:
```python
import os

MOCK_MODE = os.getenv("ENABLE_MOCK_MODE", "false").lower() == "true"

@router.post("/", response_model=ArticleResponse)
async def create_article(article: ArticleCreate):
    if MOCK_MODE and article.article_number.startswith("TEST-"):
        # Return mock data for test articles
        return {
            "id": str(uuid.uuid4()),
            "article_number": article.article_number,
            "name": "Test Product",
            "price": 1000.0,
            "normal_price": 1200.0,
            "ozon_card_price": 950.0,
            # ... other mock fields
        }

    # Normal validation continues...
    ozon = get_ozon_service()
    product_info = await ozon.get_product_info(article.article_number)
    # ...
```

**⚠️ WARNING:** Disable mock mode in production!

#### Option 3: Use Existing Articles
Query database for existing articles:

```bash
curl http://localhost:8000/api/v1/articles/ | python3 -m json.tool

# Use existing article IDs for testing:
# - GET /api/v1/articles/{article_id}
# - PATCH /api/v1/articles/{article_id}
# - DELETE /api/v1/articles/{article_id}
```

---

## 🔵 Issue #5: Docker Not Used

### Problem
Services running directly with Python instead of Docker, creating environment inconsistency.

### Benefits of Docker
- Consistent environment (dev = prod)
- Easy deployment
- Service isolation
- Automatic restart on failure
- Log management

### Solution: Use Docker Compose

#### Start All Services
```bash
cd /Users/sasha/Library/Mobile\ Documents/com~apple~CloudDocs/AIronLab/Cursor/OZON_\ scraper

# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

#### Individual Service Management
```bash
# Restart backend
docker-compose restart backend

# View backend logs
docker-compose logs -f backend

# Rebuild after code changes
docker-compose up -d --build backend
```

#### Production Deployment
```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Scale services (if needed)
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

### Verification
```bash
# All containers should be running
docker-compose ps

# Should show:
# NAME              COMMAND                  STATUS         PORTS
# ozon-backend      "uvicorn main:app..."    Up 2 minutes   0.0.0.0:8000->8000/tcp
# ozon-bot          "python main.py"         Up 2 minutes
# ozon-frontend     "nginx -g daemon..."     Up 2 minutes   0.0.0.0:5173->80/tcp
# ozon-redis        "redis-server"           Up 2 minutes   0.0.0.0:6379->6379/tcp
```

---

## 🟢 Issue #6: API Authentication Not Verified

### Problem
No authentication observed on tested endpoints. Some endpoints should be protected.

### Recommended Implementation

#### Option 1: JWT Authentication (Recommended)
```python
# backend/services/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": user_id}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Use in protected routes:
@router.get("/api/v1/articles/")
async def get_articles(user: dict = Depends(get_current_user)):
    # Only authenticated users can access
    pass
```

#### Option 2: API Key Authentication (Simpler)
```python
# backend/middlewares/api_key.py
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
import os

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != os.getenv("API_SECRET_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

# Use in protected routes:
@router.get("/api/v1/articles/")
async def get_articles(api_key: str = Depends(verify_api_key)):
    pass
```

#### Public vs Protected Endpoints
```python
# Public (no auth needed):
- GET /health
- GET /docs
- POST /api/v1/users/register (initial registration)

# Protected (auth required):
- All article endpoints
- All user management (except register)
- All reports endpoints
- All statistics endpoints
- All comparison endpoints
```

### Update Frontend to Send Auth
```javascript
// frontend/src/lib/api.ts
const API_BASE = import.meta.env.VITE_API_URL;

async function fetchWithAuth(url: string, options = {}) {
  const token = localStorage.getItem('auth_token');

  return fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });
}
```

---

## 🔵 Issue #7: Rate Limiting Not Verified

### Problem
API rate limiting not configured or tested.

### Solution: Implement Rate Limiting

#### Using SlowAPI
```bash
# Install
cd backend
pip install slowapi
```

```python
# backend/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to routes
@app.get("/api/v1/articles/")
@limiter.limit("10/minute")
async def get_articles(request: Request):
    pass
```

#### Rate Limit Configuration
```env
# .env
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100
RATE_LIMIT_PER_DAY=1000
```

### Verification
```bash
# Test rate limiting
for i in {1..15}; do
  curl http://localhost:8000/api/v1/articles/
  sleep 1
done

# After 10 requests, should return:
# HTTP 429 Too Many Requests
# {"error": "Rate limit exceeded"}
```

---

## Quick Fix Checklist

### Immediate (< 30 minutes)
- [ ] Kill existing bot process
- [ ] Clear Telegram webhook
- [ ] Restart bot in polling mode
- [ ] Start frontend service (`npm run dev`)
- [ ] Test basic functionality

### Short-term (< 2 hours)
- [ ] Configure CORS properly
- [ ] Test with real OZON SKUs
- [ ] Verify all endpoints with Postman/curl
- [ ] Check bot commands work
- [ ] Test frontend → backend integration

### Before Production (< 1 week)
- [ ] Implement authentication (JWT or API key)
- [ ] Add rate limiting
- [ ] Set up monitoring (Sentry, etc.)
- [ ] Configure production Docker setup
- [ ] SSL/HTTPS configuration
- [ ] Backup procedures
- [ ] Load testing
- [ ] Security audit

---

## Testing After Fixes

### 1. Backend API
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy", "database": "connected"}
```

### 2. Frontend
```bash
open http://localhost:5173
# Should load admin panel
```

### 3. Bot
```
Send /start to bot in Telegram
# Should receive welcome message
```

### 4. Integration
```
1. Register user via bot
2. Add article via bot
3. View article in admin panel
4. Check price updates
```

---

## Need Help?

### Logs to Check
```bash
# Backend logs
tail -f /Users/sasha/Library/Mobile\ Documents/com~apple~CloudDocs/AIronLab/Cursor/OZON_\ scraper/backend/logs/*.log

# Bot logs
tail -f /tmp/bot_output.log

# Docker logs (if using Docker)
docker-compose logs -f
```

### Health Checks
```bash
# Backend
curl http://localhost:8000/health

# Database (via backend)
curl http://localhost:8000/health | grep "database"

# Frontend
curl -I http://localhost:5173
```

---

**Last Updated:** 2025-11-05
**Next Review:** After implementing fixes
