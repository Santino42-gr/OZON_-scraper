# Production Deployment Checklist

## 📋 Pre-Deployment Checklist

### ✅ Code Quality & Testing

- [ ] **All tests passing**
  ```bash
  cd backend
  python3 test_comparison_service.py  # Unit tests
  python3 test_comparison_api.py      # Integration tests (requires running backend)
  ```
  - Expected: 75%+ success rate for unit tests
  - Expected: 100% success rate for integration tests

- [ ] **Code review completed**
  - No hardcoded credentials
  - No commented-out debug code
  - Consistent code style
  - No TODO comments in critical paths

- [ ] **Linting passed**
  ```bash
  cd backend
  flake8 . --max-line-length=120
  black --check .
  ```

- [ ] **Type checking (optional but recommended)**
  ```bash
  mypy backend/services --ignore-missing-imports
  ```

---

### 🔐 Security

- [ ] **Environment variables configured**
  - [ ] All sensitive data in .env (not in code)
  - [ ] `.env` added to `.gitignore`
  - [ ] Production `.env` stored securely (password manager, AWS Secrets Manager, etc.)

- [ ] **Secret keys rotated**
  ```bash
  # Generate new SECRET_KEY
  openssl rand -hex 32
  ```
  - [ ] `SECRET_KEY` changed from default
  - [ ] `API_SECRET_KEY` changed from default
  - [ ] Supabase keys are production keys (not development)

- [ ] **CORS properly configured**
  ```env
  CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
  ```
  - No wildcards (*) in production
  - Only necessary origins listed

- [ ] **Rate limiting enabled**
  ```python
  # backend/config.py
  OZON_RATE_LIMIT=30  # requests per minute
  ```

- [ ] **SQL injection protection verified**
  - All queries use parameterized statements
  - No string concatenation in SQL

- [ ] **HTTPS enabled**
  - [ ] SSL certificate installed
  - [ ] HTTP → HTTPS redirect configured
  - [ ] Certificate auto-renewal configured (Let's Encrypt)

- [ ] **Supabase RLS (Row Level Security)**
  - [ ] RLS policies enabled for all tables
  - [ ] Tested with different user roles
  - [ ] Service role key only in backend (never in frontend)

---

### 🗄️ Database

- [ ] **All migrations applied**
  ```sql
  -- Check in Supabase Dashboard → Database → Migrations
  -- or run locally:
  -- psql -h db.xxx.supabase.co -U postgres -d postgres -c "\dt"
  ```
  - [ ] 001_initial_schema.sql
  - [ ] 002_price_history.sql
  - [ ] 003_spp_metrics.sql
  - [ ] 004_reports_system.sql
  - [ ] 005_indexes.sql
  - [ ] 006_comparison_groups.sql
  - [ ] 007_comparison_metrics.sql
  - [ ] 008_comparison_snapshots.sql

- [ ] **Database indexes created**
  - Critical queries < 100ms
  - Check with EXPLAIN ANALYZE

- [ ] **Backup strategy configured**
  - [ ] Automatic daily backups (Supabase Pro has this)
  - [ ] Backup retention policy set (7-30 days)
  - [ ] Restore procedure tested

- [ ] **Database connection pooling**
  - Supabase handles this automatically

---

### ⚙️ Backend Configuration

- [ ] **Environment set to production**
  ```env
  ENVIRONMENT=production
  ```

- [ ] **Logging configured**
  ```env
  LOG_LEVEL=INFO  # not DEBUG in production
  LOG_FILE=/var/log/ozon-scraper/backend.log
  ```
  - [ ] Log rotation configured (daily)
  - [ ] Log retention set (7-30 days)
  - [ ] Disk space monitored

- [ ] **Scheduler configured correctly**
  - [ ] Timezone set correctly
  ```python
  # backend/services/scheduler.py
  scheduler = AsyncIOScheduler(timezone=timezone('Europe/Moscow'))
  ```
  - [ ] Cron jobs timing verified
    - update_comparison_snapshots: 03:00
    - update_price_history: 04:00

- [ ] **Error tracking enabled (Sentry)**
  ```bash
  pip install sentry-sdk
  ```
  ```python
  # backend/main.py
  import sentry_sdk
  sentry_sdk.init(dsn="your-production-dsn")
  ```

- [ ] **Health checks working**
  ```bash
  curl http://localhost:8000/health
  curl http://localhost:8000/api/v1/comparison/health
  ```

---

### 🎨 Frontend Configuration

- [ ] **Environment variables set**
  ```env
  NEXT_PUBLIC_API_URL=https://api.yourdomain.com
  NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
  NEXT_PUBLIC_SUPABASE_ANON_KEY=xxx
  NODE_ENV=production
  ```

- [ ] **Build successful**
  ```bash
  cd frontend
  npm run build
  ```
  - No errors
  - No critical warnings
  - Bundle size acceptable (< 500KB initial)

- [ ] **Performance optimized**
  - [ ] Images optimized (Next.js Image component)
  - [ ] Code splitting enabled
  - [ ] Lazy loading for heavy components
  - [ ] Lighthouse score > 90

- [ ] **SEO configured**
  - [ ] Meta tags present
  - [ ] Open Graph tags
  - [ ] Sitemap.xml
  - [ ] Robots.txt

---

### 🚀 Deployment Infrastructure

- [ ] **Server provisioned**
  - [ ] CPU: 2+ cores
  - [ ] RAM: 4+ GB
  - [ ] Disk: 20+ GB SSD
  - [ ] OS: Ubuntu 22.04 LTS (or similar)

- [ ] **Firewall configured**
  ```bash
  sudo ufw allow 22   # SSH
  sudo ufw allow 80   # HTTP
  sudo ufw allow 443  # HTTPS
  sudo ufw enable
  ```

- [ ] **Systemd services created**
  - [ ] `/etc/systemd/system/ozon-backend.service`
  - [ ] `/etc/systemd/system/ozon-frontend.service`
  - [ ] Services enabled: `systemctl enable ozon-backend`

- [ ] **Nginx configured**
  - [ ] Reverse proxy for backend
  - [ ] Reverse proxy for frontend
  - [ ] SSL/TLS configured
  - [ ] Gzip compression enabled
  - [ ] Security headers added

- [ ] **Monitoring setup**
  - [ ] Server monitoring (CPU, RAM, Disk)
  - [ ] Application monitoring (Sentry, New Relic, etc.)
  - [ ] Uptime monitoring (UptimeRobot, Pingdom)
  - [ ] Log aggregation (optional: ELK, Loki)

---

### 📊 Monitoring & Alerting

- [ ] **Health check endpoints**
  - [ ] `/health` returns 200
  - [ ] `/api/v1/comparison/health` returns 200
  - [ ] Database connection verified

- [ ] **Error tracking**
  - [ ] Sentry DSN configured
  - [ ] Error notifications enabled
  - [ ] Team members added to Sentry project

- [ ] **Uptime monitoring**
  - [ ] External monitor configured (UptimeRobot)
  - [ ] Alerts to Slack/Email
  - [ ] Check every 5 minutes

- [ ] **Performance monitoring**
  - [ ] Response time < 200ms for API
  - [ ] Page load < 2s for frontend
  - [ ] Database queries < 100ms

- [ ] **Disk space monitoring**
  ```bash
  df -h
  ```
  - [ ] Alert when > 80% full
  - [ ] Log rotation configured

---

### 🔄 CI/CD (Optional but Recommended)

- [ ] **GitHub Actions configured**
  - [ ] Tests run on every PR
  - [ ] Auto-deploy on merge to main
  - [ ] Rollback capability

- [ ] **Deployment pipeline**
  ```yaml
  # .github/workflows/deploy.yml
  # 1. Run tests
  # 2. Build
  # 3. Deploy to staging
  # 4. Run smoke tests
  # 5. Deploy to production
  ```

---

### 📚 Documentation

- [ ] **README.md updated**
  - [ ] New comparison feature documented
  - [ ] Installation instructions
  - [ ] API examples

- [ ] **API documentation**
  - [ ] Swagger UI accessible at `/docs`
  - [ ] All endpoints documented
  - [ ] Examples provided

- [ ] **Deployment guide complete**
  - [ ] See DEPLOYMENT_GUIDE.md

- [ ] **Manual test plan available**
  - [ ] See MANUAL_TEST_PLAN.md

---

### 🧪 Final Testing

- [ ] **Smoke tests in production**
  ```bash
  # 1. Health check
  curl https://api.yourdomain.com/health

  # 2. Create comparison
  curl -X POST https://api.yourdomain.com/api/v1/comparison/quick-compare \
    -H "Content-Type: application/json" \
    -d '{"own_article_number": "123", "competitor_article_number": "456", ...}'

  # 3. Get comparison history
  curl https://api.yourdomain.com/api/v1/comparison/groups/{id}/history

  # 4. Frontend loads
  # Open https://yourdomain.com in browser
  ```

- [ ] **Performance test**
  - [ ] Load test with 100 concurrent users
  - [ ] API response time < 200ms
  - [ ] No memory leaks

- [ ] **Security scan**
  ```bash
  # OWASP ZAP or similar
  # Check for common vulnerabilities
  ```

---

### 📞 Post-Deployment

- [ ] **Monitor for first 24 hours**
  - [ ] Check error logs every 2 hours
  - [ ] Monitor CPU/RAM usage
  - [ ] Watch for unexpected traffic

- [ ] **Rollback plan ready**
  - [ ] Previous version tagged in git
  - [ ] Database backup taken before migration
  - [ ] Rollback steps documented

- [ ] **Team notified**
  - [ ] Deployment announcement
  - [ ] New features documented
  - [ ] Support team briefed

---

## 🚨 Emergency Rollback Plan

If something goes wrong after deployment:

### 1. Quick Rollback (< 5 minutes)

```bash
# Stop services
sudo systemctl stop ozon-backend
sudo systemctl stop ozon-frontend

# Revert code
cd /path/to/OZON_scraper
git reset --hard <previous-commit-hash>

# Restart services
sudo systemctl start ozon-backend
sudo systemctl start ozon-frontend
```

### 2. Database Rollback (if migrations failed)

```sql
-- Restore from backup (Supabase Dashboard)
-- Or manually revert migrations
```

### 3. Verify

```bash
curl https://api.yourdomain.com/health
```

---

## ✅ Sign-off

**Deployment completed by:** _________________

**Date:** _________________

**Environment:** Production

**Version deployed:** _________________

**All checklist items completed:** [ ] Yes [ ] No

**Notes:**
_________________
_________________
_________________

**Approved by:** _________________

---

**Remember:**
- 🔒 Security first
- 📊 Monitor everything
- 🔄 Always have a rollback plan
- 📝 Document all changes

**Good luck with your deployment! 🚀**
