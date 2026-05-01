# 🚀 PhishVision Production Deployment - Quick Guide

## Current Status

Your PhishVision system **WORKS PERFECTLY IN DEVELOPMENT**! ✅

For production, there are **4 key things to change**:

---

## 📋 Production Readiness Checklist

### 1️⃣ **Update Backend URL** (CRITICAL)
**File**: `.env`

```env
# DEVELOPMENT (Current)
BACKEND_URL=http://localhost:8000

# PRODUCTION (Change to)
BACKEND_URL=https://api.yourdomain.com
```

### 2️⃣ **Move Database to Persistent Location**
**File**: `.env`

```env
# DEVELOPMENT (Current)
DATABASE_PATH=./users.db

# PRODUCTION (Change to)
# Linux:
DATABASE_PATH=/var/lib/phishvision/users.db

# Windows Server:
DATABASE_PATH=C:\Data\PhishVision\users.db
```

**Important**: Ensure the directory exists and has read/write permissions!

### 3️⃣ **Enable HTTPS/SSL**
- Get SSL certificate (Let's Encrypt is free)
- Update `BACKEND_URL` to use `https://`
- Configure Nginx/Apache reverse proxy (see DEPLOYMENT.md)

### 4️⃣ **Restrict CORS Origins**
**File**: `.env`

```env
# DEVELOPMENT (Current)
CORS_ORIGINS=http://localhost:3000,http://localhost:8501,http://192.168.31.75:8501

# PRODUCTION (Change to)
CORS_ORIGINS=https://app.yourdomain.com,https://www.yourdomain.com
```

---

## 🔧 Installation for Production

### Linux (Ubuntu/Debian)

```bash
# 1. Clone project
cd /opt/phishvision

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 3. Install dependencies (includes python-dotenv now!)
pip install -r requirements.txt

# 4. Create data directory
sudo mkdir -p /var/lib/phishvision
sudo chown $USER:$USER /var/lib/phishvision

# 5. Create .env for production
cat > .env << EOF
BACKEND_URL=https://api.yourdomain.com
DATABASE_PATH=/var/lib/phishvision/users.db
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
CORS_ORIGINS=https://app.yourdomain.com
EOF

# 6. Test both services
python -m uvicorn api:app --host 0.0.0.0 --port 8000 &
streamlit run app.py --server.port 8501 &
```

### Windows Server

```powershell
# 1. Navigate to project
cd C:\PhishVision

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create data directory
mkdir C:\Data\PhishVision
mkdir C:\Data\PhishVision\logs

# 5. Create .env for production
@'
BACKEND_URL=https://api.yourdomain.com
DATABASE_PATH=C:\Data\PhishVision\users.db
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
CORS_ORIGINS=https://app.yourdomain.com
'@ | Out-File .env

# 6. Test services
python -m uvicorn api:app --host 0.0.0.0 --port 8000
streamlit run app.py --server.port 8501
```

### Docker (Easiest!)

```bash
# 1. Create Dockerfile (already prepared)
# 2. Build image
docker build -t phishvision:latest .

# 3. Run with environment variables
docker run \
  -e BACKEND_URL=https://api.yourdomain.com \
  -e DATABASE_PATH=/data/users.db \
  -e CORS_ORIGINS=https://app.yourdomain.com \
  -v /data/phishvision:/data \
  -p 8000:8000 \
  -p 8501:8501 \
  phishvision:latest
```

---

## ✅ Testing Checklist

Before going live:

- [ ] Change password of demo account (`admin@phishvision.ai`)
- [ ] Register new test account
- [ ] Verify login works with new account
- [ ] Logout and login again
- [ ] Change settings (name, password, theme)
- [ ] Verify database persists after restart
- [ ] Test from different devices/networks
- [ ] Verify HTTPS certificate is valid
- [ ] Check logs for errors

---

## 🎯 Summary

| Aspect | Development | Production |
|--------|------------|------------|
| Backend URL | `http://localhost:8000` | `https://api.yourdomain.com` |
| Frontend URL | `http://localhost:8501` | `https://app.yourdomain.com` |
| Database | `./users.db` (local) | `/var/lib/phishvision/users.db` (persistent) |
| HTTPS | ❌ No | ✅ Yes (Let's Encrypt) |
| CORS | `*` (all origins) | Restricted to your domain |
| Deployment | Single machine | Server/Docker/Cloud |

---

## 📊 What Stays The Same

✅ Authentication system works identically
✅ Database schema unchanged
✅ User profiles/theme preferences persist
✅ Password hashing is secure
✅ Settings updates synchronized

---

## ⚠️ Critical Security Notes

1. **Change demo account password** after deployment
2. **Enable HTTPS** - never send credentials over HTTP
3. **Back up database** regularly
4. **Restrict CORS** - don't use `*` in production
5. **Monitor logs** for suspicious activity
6. **Update dependencies** regularly for security patches

---

## 🆘 Troubleshooting Production Issues

### "Backend connection failed"
- Check if FastAPI is running
- Verify `BACKEND_URL` in `.env` matches actual backend address
- Check firewall rules allow traffic

### "Database error"
- Verify database directory exists and has write permissions
- Check disk space
- Ensure `DATABASE_PATH` is correct in `.env`

### "CORS error in browser"
- Verify frontend domain is in `CORS_ORIGINS`
- Must use exact protocol (`https://` vs `http://`)
- Restart API after changing CORS settings

### "SSL certificate error"
- Ensure certificate is valid and not expired
- Check certificate chain is complete
- Verify domain matches certificate

---

For detailed deployment guide, see **DEPLOYMENT.md** in project root.

**Questions?** Your system is production-ready! Just update the `.env` file and you're good to go! 🚀
