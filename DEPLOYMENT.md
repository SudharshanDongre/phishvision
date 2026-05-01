# PhishVision Deployment Checklist

## 🚀 PRODUCTION DEPLOYMENT GUIDE

### ✅ Before Deployment

#### 1. **Backend (FastAPI) Configuration**
- [ ] Update `BACKEND_URL` in `.env` to your actual server domain
  - Development: `http://localhost:8000`
  - Production: `https://api.yourdomain.com`
  
- [ ] Move database to persistent location
  - Development: `./users.db` (app directory)
  - Production: `/var/lib/phishvision/users.db` (Linux) or `C:\Data\PhishVision\users.db` (Windows)
  - **Important**: Database directory needs read/write permissions
  
- [ ] Enable HTTPS (SSL/TLS)
  - Use Let's Encrypt or your certificate provider
  - Update API to use HTTPS
  - Set `ENABLE_HTTPS=true` in `.env`
  
- [ ] Restrict CORS in `api.py`
  ```python
  # Change from: allow_origins=["*"]
  # To:
  allow_origins=[
      "https://yourdomain.com",
      "https://app.yourdomain.com",
      "https://www.yourdomain.com"
  ]
  ```

#### 2. **Frontend (Streamlit) Configuration**
- [ ] Update Streamlit config file (`~/.streamlit/config.toml`):
  ```toml
  [server]
  headless = true
  port = 8501
  enableXsrfProtection = true
  enableCORS = false
  
  [client]
  showErrorDetails = false
  ```

- [ ] Set backend URL via environment variable
  - The app will use `BACKEND_URL` from `.env`
  - Make sure it points to production backend

#### 3. **Security Hardening**
- [ ] Change demo account password
  ```bash
  # The demo account "admin@phishvision.ai" will be created with default password
  # Change it after first login in production
  ```

- [ ] Enable database backups
  - Backup `users.db` daily
  - Store backups securely

- [ ] Add rate limiting (optional, in api.py)
  ```python
  from slowapi import Limiter
  limiter = Limiter(key_func=get_remote_address)
  @app.post("/auth/login")
  @limiter.limit("5/minute")  # Max 5 login attempts per minute
  ```

- [ ] Add SSL certificate renewal
  - If using Let's Encrypt, set up certbot auto-renewal

#### 4. **Deployment Options**

##### **Option A: Docker Deployment (Recommended)**
Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
EXPOSE 8000 8501
CMD ["sh", "-c", "python -m uvicorn api:app --host 0.0.0.0 --port 8000 & streamlit run app.py --server.port 8501"]
```

##### **Option B: Linux Server (Ubuntu/Debian)**
```bash
# 1. Install Python 3.11+
sudo apt-get install python3.11 python3.11-venv

# 2. Clone/upload project
cd /opt/phishvision

# 3. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Setup systemd services for auto-restart
# Create /etc/systemd/system/phishvision-api.service
# Create /etc/systemd/system/phishvision-app.service
```

##### **Option C: Cloud Platforms**
- **Heroku**: Deploy both services in separate dynos
- **AWS EC2**: Run on Ubuntu instance with Nginx reverse proxy
- **Azure**: Use App Service for Streamlit + API Management
- **DigitalOcean**: Simple VPS with Docker Compose

#### 5. **Reverse Proxy Setup (Nginx - Recommended)**
```nginx
# Frontend
server {
    listen 443 ssl;
    server_name app.yourdomain.com;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}

# Backend API
server {
    listen 443 ssl;
    server_name api.yourdomain.com;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 6. **Environment Variables for Production**
```bash
export BACKEND_URL=https://api.yourdomain.com
export DATABASE_PATH=/var/lib/phishvision/users.db
export STREAMLIT_SERVER_HEADLESS=true
export CORS_ORIGINS=https://app.yourdomain.com
```

#### 7. **Testing Before Going Live**
- [ ] Test login/registration flow
- [ ] Verify database persistence (create account, restart, login again)
- [ ] Test settings updates (name, password, theme changes)
- [ ] Verify theme switching works
- [ ] Test from different devices/browsers
- [ ] Load testing (simulate multiple users)

#### 8. **Monitoring & Maintenance**
- [ ] Setup logging to file or ELK stack
- [ ] Monitor disk space (database growth)
- [ ] Monitor API response times
- [ ] Setup error alerts
- [ ] Regular security updates for dependencies

---

## 🔧 Current Development Setup Issues

### Issue 1: Hardcoded Backend URL
**Current Code:**
```python
BACKEND_URL = "http://localhost:8000"
```
**Fix:**
```python
import os
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
```

### Issue 2: Database in App Directory
**Current Code:**
```python
DATABASE_FILE = "users.db"
```
**Fix:**
```python
import os
DATABASE_PATH = os.getenv("DATABASE_PATH", "./users.db")
DATABASE_FILE = DATABASE_PATH
```

### Issue 3: CORS Allows Everything
**Current Code (api.py):**
```python
allow_origins=["*"]
```
**Fix:**
```python
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8501").split(",")
allow_origins=cors_origins
```

---

## ⚠️ Common Deployment Mistakes to Avoid

1. ❌ Using `localhost` in production (won't resolve from other machines)
2. ❌ Running with `--reload` flag in production (causes crashes)
3. ❌ Storing database in temp directory (data lost on restart)
4. ❌ Allowing all CORS origins (security risk)
5. ❌ No SSL/HTTPS (credentials transmitted in plain text)
6. ❌ Not backing up user database
7. ❌ Debug mode enabled in production
8. ❌ Default passwords kept in production

---

## 📋 Summary

**Development (Current)**: ✅ Works perfectly
- Runs locally on `localhost:8501` and `localhost:8000`
- Database stored locally
- No HTTPS needed

**Production**: ⚠️ Needs Configuration
- Must update `BACKEND_URL` environment variable
- Must move database to persistent location with backups
- Should enable HTTPS/SSL
- Should restrict CORS origins
- Should use systemd/Docker for auto-restart
- Should add monitoring and logging

**Bottom Line**: With the configuration changes in this checklist, your system will work perfectly in production! 🚀
