# 🚀 Deployment Guide - Legal Text Scraping System

Complete setup instructions for the Brazilian Legal Text Correction System with automated data collection.

## 📋 Prerequisites

### Required Software
- Python 3.8+ 
- Git
- Internet connection for API access and web scraping

### Required API Keys
- **Google Gemini API Key** (Required)
  - Get free key at: https://makersuite.google.com/app/apikey
  - Follow Google AI Studio setup instructions

### Optional (for production)
- **Email SMTP credentials** (for notifications)
- **Webhook URL** (for monitoring alerts)
- **ngrok account** (for public access)

## 🏗️ Installation Options

### Option 1: Google Colab (Recommended for Testing)

1. **Clone/Download the repository**
2. **Upload files to Google Colab**:
   - `app.py`
   - `database.py`
   - `legal_scrapers.py`
   - `data_processor.py`
   - `scheduler.py`
   - `setup_colab.py`
   - `templates/` folder

3. **Set up API Key**:
   ```python
   import os
   os.environ['GEMINI_API_KEY'] = 'your-gemini-api-key-here'
   ```

4. **Run the setup script**:
   ```python
   exec(open('setup_colab.py').read())
   ```

5. **Access the applications**:
   - Click the generated ngrok URL for the main app
   - Add `/api/admin/dashboard` for admin interface

### Option 2: Local Development

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd legal-text-corrector
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**:
   ```bash
   # On Windows:
   set GEMINI_API_KEY=your-gemini-api-key-here
   
   # On macOS/Linux:
   export GEMINI_API_KEY=your-gemini-api-key-here
   ```

5. **Run the application**:
   ```bash
   # Start the main Flask server
   python app.py
   ```

6. **Start the scheduler (optional, in another terminal)**:
   ```bash
   python scheduler.py --start
   ```

7. **Access the applications**:
   - Main app: http://localhost:5000
   - Admin dashboard: http://localhost:5000/api/admin/dashboard

### Option 3: Production Deployment

1. **Server Setup** (Ubuntu/Debian):
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv nginx
   ```

2. **Clone and setup**:
   ```bash
   git clone <your-repo-url>
   cd legal-text-corrector
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Create systemd service for the main app**:
   ```bash
   sudo nano /etc/systemd/system/legal-corrector.service
   ```
   
   Add this content:
   ```ini
   [Unit]
   Description=Legal Text Corrector Flask App
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/path/to/legal-text-corrector
   Environment=GEMINI_API_KEY=your-gemini-api-key-here
   ExecStart=/path/to/legal-text-corrector/venv/bin/python app.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

4. **Create systemd service for the scheduler**:
   ```bash
   sudo nano /etc/systemd/system/legal-scheduler.service
   ```
   
   Add this content:
   ```ini
   [Unit]
   Description=Legal Text Scraper Scheduler
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/path/to/legal-text-corrector
   Environment=GEMINI_API_KEY=your-gemini-api-key-here
   ExecStart=/path/to/legal-text-corrector/venv/bin/python scheduler.py --start
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

5. **Start services**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable legal-corrector
   sudo systemctl enable legal-scheduler
   sudo systemctl start legal-corrector
   sudo systemctl start legal-scheduler
   ```

6. **Configure Nginx (optional)**:
   ```bash
   sudo nano /etc/nginx/sites-available/legal-corrector
   ```
   
   Add this content:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```
   
   Enable the site:
   ```bash
   sudo ln -s /etc/nginx/sites-available/legal-corrector /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:
```env
# Required
GEMINI_API_KEY=your-gemini-api-key-here

# Optional - Scheduler auto-start
AUTO_START_SCHEDULER=true

# Optional - Email notifications
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
RECIPIENT_EMAILS=admin@yourcompany.com,lawyer@yourcompany.com

# Optional - Webhook alerts
WEBHOOK_URL=https://hooks.slack.com/your-webhook-url
```

### Scheduler Configuration

The scheduler can be configured by editing `scheduler_config.json`:
```json
{
  "schedule": {
    "day_of_week": "monday",
    "time": "02:00",
    "timezone": "America/Sao_Paulo"
  },
  "scraping": {
    "limit_per_scraper": 50,
    "max_retries": 3,
    "retry_delay_minutes": 30
  },
  "database": {
    "cleanup_enabled": true,
    "days_to_keep": 90,
    "backup_enabled": true
  },
  "monitoring": {
    "email_notifications": true,
    "webhook_url": "https://your-webhook-url",
    "alert_thresholds": {
      "min_success_rate": 0.7,
      "max_error_count": 10
    }
  }
}
```

## 🎯 Usage Instructions

### Main Legal Text Correction App

1. **Access**: http://localhost:5000 (or your domain)
2. **Usage**:
   - Paste legal text in the textarea
   - Click "Corrigir Texto" 
   - View original and corrected versions
   - Use enhanced mode for context-aware corrections

### Admin Dashboard

1. **Access**: http://localhost:5000/api/admin/dashboard
2. **Features**:
   - **Statistics**: View database stats, scheduler status
   - **Manual Controls**: Run scraping, process texts, generate training data
   - **Database Search**: Search collected legal texts
   - **System Monitoring**: Real-time logs and alerts
   - **Maintenance**: Database cleanup, scheduler control

### Command Line Tools

```bash
# Manual scraping
python scheduler.py --run-once

# Process unprocessed texts
python data_processor.py --process-unprocessed

# Generate training data
python data_processor.py --generate-training-data 100

# Health check
python scheduler.py --health-check
```

### API Endpoints

#### Text Correction
```bash
# Basic correction
curl -X POST http://localhost:5000/api/correct \
  -H "Content-Type: application/json" \
  -d '{"text": "O cara não fez o que prometeu no contrato"}'

# Enhanced correction with database context
curl -X POST http://localhost:5000/api/correct/enhanced \
  -H "Content-Type: application/json" \
  -d '{"text": "O cara não fez o que prometeu no contrato"}'
```

#### Admin Operations
```bash
# Get system stats
curl http://localhost:5000/api/admin/stats

# Run manual scraping
curl -X POST http://localhost:5000/api/admin/scrape/manual \
  -H "Content-Type: application/json" \
  -d '{"limit": 25}'

# Search database
curl "http://localhost:5000/api/admin/database/search?q=contrato&limit=10"
```

## 🔧 Troubleshooting

### Common Issues

1. **"Gemini API not configured"**
   - Ensure `GEMINI_API_KEY` environment variable is set
   - Verify the API key is valid and active

2. **"No response from Gemini API"**
   - Check internet connection
   - Verify API quotas and limits
   - Check API key permissions

3. **Scraping errors**
   - Some sites may block requests - this is normal
   - Check logs in admin dashboard for specific errors
   - Scrapers have built-in retry mechanisms

4. **Database locked errors**
   - Ensure only one instance of the app is running
   - Restart the application if needed

5. **Port already in use**
   - Change port in `app.py`: `app.run(port=5001)`
   - Or kill process using the port: `sudo fuser -k 5000/tcp`

### Monitoring

- **Logs**: Check `scraper_scheduler.log` for detailed logs
- **Health checks**: Available at `/api/health`
- **Database stats**: Monitor via admin dashboard
- **Email alerts**: Configure for automatic notifications

### Performance Tips

1. **Database optimization**:
   - Regular cleanup of old data (automated)
   - Monitor database size
   - Use search indexes efficiently

2. **Scraping optimization**:
   - Adjust delay ranges in scrapers
   - Monitor success rates
   - Respect websites' robots.txt

3. **Memory management**:
   - Restart services weekly
   - Monitor memory usage
   - Clean temporary files

## 📊 System Architecture

```
┌─────────────────────────────────────────┐
│           Web Interfaces                │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ Main App    │  │ Admin Dashboard │   │
│  │ (Correction)│  │ (Management)    │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│              Flask Server               │
│            (app.py - Port 5000)         │
│  ┌─────────────────────────────────────┐ │
│  │ API Endpoints & Database Integration│ │
│  └─────────────────────────────────────┘ │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│           Background Services           │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ Scheduler   │  │ Data Processor  │   │
│  │(Weekly Auto)│  │ (AI Enhancement)│   │
│  └─────────────┘  └─────────────────┘   │
│  ┌─────────────────────────────────────┐ │
│  │        Web Scrapers                 │ │
│  │ STF │ STJ │ ConJur │ Migalhas       │ │
│  └─────────────────────────────────────┘ │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│            SQLite Database              │
│  ┌─────────────────────────────────────┐ │
│  │ Legal Texts │ Logs │ Metrics       │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## 🎉 Success Checklist

After deployment, verify these features work:

- [ ] Main correction app loads at root URL
- [ ] Admin dashboard accessible at `/api/admin/dashboard`
- [ ] Text correction produces results
- [ ] Enhanced correction uses database context
- [ ] Manual scraping works from admin panel
- [ ] Database search returns results
- [ ] Scheduler status shows correctly
- [ ] System logs are updating
- [ ] API endpoints respond correctly
- [ ] Email notifications configured (if enabled)

## 📞 Support

If you encounter issues:

1. Check the logs in `scraper_scheduler.log`
2. Use the admin dashboard health checks
3. Verify all environment variables are set
4. Ensure API quotas are not exceeded
5. Check firewall and port access

The system is designed to be robust and self-healing, with automatic retries and error recovery mechanisms built in.