# 🚀 RAG Project - Automatic Startup Configuration

## ✅ SETUP COMPLETE!

Your RAG project is now fully configured for **automatic startup** when the VM is turned on. All services will start automatically and be available within 2-3 minutes of boot.

---

## 🔧 Configured Services

The following systemd services are now **enabled** and will start automatically:

### Core Services
- ✅ **`qdrant.service`** - Vector database (Foundation)
- ✅ **`rag-mistral.service`** - Mistral AI Server (Port 8001)
- ✅ **`rag-fastapi.service`** - FastAPI Classification Server (Port 8000)
- ✅ **`rag-sharepoint.service`** - SharePoint Document Automation
- ✅ **`cloudflared.service`** - Cloudflare Tunnel (External Access)

### Service Dependencies
Services start in the correct order:
1. **Qdrant** (Vector Database) - Starts first
2. **Mistral AI** - Starts after network + GPU ready
3. **FastAPI** - Starts after Qdrant + Mistral
4. **SharePoint** - Starts after FastAPI + Mistral ready
5. **Cloudflare** - Independent tunnel service

---

## 🌐 Access URLs

### After VM Restart, Access Via:

**External URLs (Always Available):**
- 🌍 **Mistral AI Server**: https://arandia-rag.ggunifiedtech.com
- 🌍 **FastAPI Server**: https://arandia-fastapi.ggunifiedtech.com

**Local URLs (Within VM):**
- 🏠 **FastAPI Server**: http://localhost:8000
- 🏠 **Mistral AI Server**: http://localhost:8001

---

## ⏰ Startup Timeline

After VM restart, expect this timeline:

1. **0-30 seconds**: System boot, network initialization
2. **30-60 seconds**: Qdrant database starts
3. **60-120 seconds**: Mistral AI loads (GPU initialization)
4. **90-150 seconds**: FastAPI server starts
5. **120-180 seconds**: SharePoint automation begins
6. **180+ seconds**: All services fully operational

**🕐 Total startup time: ~3 minutes**

---

## 🧪 Validation Commands

### Quick Service Check:
```bash
# Check all service status
sudo systemctl status qdrant rag-mistral rag-fastapi rag-sharepoint cloudflared

# Quick status check
sudo systemctl is-active qdrant rag-mistral rag-fastapi rag-sharepoint cloudflared
```

### Test Endpoints:
```bash
# Test local FastAPI
curl http://localhost:8000/

# Test local Mistral
curl http://localhost:8001/health

# Test external URL
curl https://arandia-rag.ggunifiedtech.com/health
```

### Run Validation Script:
```bash
# Quick service check
bash /home/azureuser/rag_project/scripts/deployment/check_services.sh

# Full validation
bash /home/azureuser/rag_project/scripts/deployment/validate_startup.sh
```

---

## 🛠️ Manual Service Management

### Start/Stop/Restart Services:
```bash
# Restart all services
sudo systemctl restart qdrant rag-mistral rag-fastapi rag-sharepoint

# Stop all services
sudo systemctl stop rag-sharepoint rag-fastapi rag-mistral qdrant

# Start all services
sudo systemctl start qdrant rag-mistral rag-fastapi rag-sharepoint
```

### View Service Logs:
```bash
# FastAPI logs
sudo journalctl -u rag-fastapi -f

# Mistral AI logs
sudo journalctl -u rag-mistral -f

# SharePoint automation logs
sudo journalctl -u rag-sharepoint -f

# All services
sudo journalctl -u qdrant -u rag-mistral -u rag-fastapi -u rag-sharepoint -f
```

---

## 🔍 Troubleshooting

### If Services Don't Start:

1. **Check Service Status:**
   ```bash
   sudo systemctl status rag-mistral rag-fastapi rag-sharepoint
   ```

2. **Check Service Logs:**
   ```bash
   sudo journalctl -u rag-mistral -n 50
   sudo journalctl -u rag-fastapi -n 50
   ```

3. **Manual Restart:**
   ```bash
   sudo systemctl restart rag-mistral
   sudo systemctl restart rag-fastapi
   sudo systemctl restart rag-sharepoint
   ```

4. **Check GPU:**
   ```bash
   nvidia-smi
   ```

5. **Check Conda Environment:**
   ```bash
   source /home/azureuser/miniconda3/bin/activate rag
   python --version
   ```

---

## 📋 Service File Locations

- **Service Files**: `/etc/systemd/system/rag-*.service`
- **Cloudflare Config**: `/etc/cloudflared/config.yml`
- **Project Directory**: `/home/azureuser/rag_project/`
- **Logs**: `/home/azureuser/rag_project/logs/application/`

---

## 🎯 Key Features

✅ **Zero Manual Intervention**: Everything starts automatically  
✅ **GPU Acceleration**: Mistral AI uses NVIDIA A10-4Q  
✅ **External Access**: Available via ggunifiedtech.com URLs  
✅ **Automatic Recovery**: Services restart if they crash  
✅ **Proper Dependencies**: Services start in correct order  
✅ **Comprehensive Logging**: All activity is logged  

---

## 🚨 IMPORTANT NOTES

1. **First Boot**: Allow 3-5 minutes for complete initialization
2. **GPU Requirement**: Mistral AI requires NVIDIA GPU to be ready
3. **Internet Required**: Cloudflare tunnel needs internet connectivity  
4. **Conda Environment**: All services use the `rag` conda environment
5. **SharePoint Auth**: May require re-authentication after extended downtime

---

## ✅ FINAL VALIDATION

**Your RAG project is now production-ready with automatic startup!**

🎉 **Turn off the VM, turn it back on, and everything will work automatically!**

**Main URL**: https://arandia-rag.ggunifiedtech.com  
**System Status**: 100% Automated ✅  
**Document Processing**: Fully Operational ✅  
**GPU Acceleration**: Active ✅
