import schedule
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import threading
import json
import os
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import smtplib
from legal_scrapers import LegalScraperManager
from database import LegalTextDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScrapingScheduler:
    """Automated scheduler for weekly legal text scraping"""
    
    def __init__(self, config_path: str = "scheduler_config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.scraper_manager = LegalScraperManager()
        self.is_running = False
        self.last_run_results = None
        
    def load_config(self) -> Dict:
        """Load scheduler configuration"""
        default_config = {
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
                "cleanup_enabled": True,
                "days_to_keep": 90,
                "backup_enabled": True
            },
            "monitoring": {
                "email_notifications": False,
                "webhook_url": None,
                "alert_thresholds": {
                    "min_success_rate": 0.7,
                    "max_error_count": 10
                }
            },
            "email": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "",
                "sender_password": "",
                "recipient_emails": []
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in loaded_config:
                            loaded_config[key] = value
                        elif isinstance(value, dict):
                            for subkey, subvalue in value.items():
                                if subkey not in loaded_config[key]:
                                    loaded_config[key][subkey] = subvalue
                    return loaded_config
            except Exception as e:
                logger.error(f"Error loading config: {e}. Using defaults.")
        
        # Save default config
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: Dict):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def run_scraping_job(self):
        """Execute the main scraping job"""
        job_start = datetime.now()
        logger.info("=== Starting scheduled scraping job ===")
        
        try:
            # Run all scrapers
            results = self.scraper_manager.run_all_scrapers(
                limit_per_scraper=self.config['scraping']['limit_per_scraper']
            )
            
            # Add job metadata
            results['job_start'] = job_start.isoformat()
            results['job_end'] = datetime.now().isoformat()
            results['config_used'] = self.config['scraping']
            
            # Store results
            self.last_run_results = results
            
            # Database cleanup if enabled
            if self.config['database']['cleanup_enabled']:
                deleted_count = self.scraper_manager.cleanup_old_data(
                    days_to_keep=self.config['database']['days_to_keep']
                )
                results['cleanup'] = {'deleted_records': deleted_count}
                logger.info(f"Database cleanup: {deleted_count} old records removed")
            
            # Calculate success metrics
            success_rate = results['total_saved'] / max(results['total_scraped'], 1)
            error_count = len(results['errors'])
            
            # Check alert thresholds
            alerts = []
            if success_rate < self.config['monitoring']['alert_thresholds']['min_success_rate']:
                alerts.append(f"Low success rate: {success_rate:.2%}")
            
            if error_count > self.config['monitoring']['alert_thresholds']['max_error_count']:
                alerts.append(f"High error count: {error_count}")
            
            results['alerts'] = alerts
            results['success_rate'] = success_rate
            
            # Send notifications
            if alerts and self.config['monitoring']['email_notifications']:
                self.send_email_notification(results, alerts)
            
            if self.config['monitoring']['webhook_url']:
                self.send_webhook_notification(results)
            
            # Save run log
            self.save_run_log(results)
            
            logger.info(f"Scraping job completed successfully. Scraped: {results['total_scraped']}, Saved: {results['total_saved']}")
            
            return results
            
        except Exception as e:
            error_msg = f"Scraping job failed: {e}"
            logger.error(error_msg)
            
            error_results = {
                'status': 'failed',
                'error': error_msg,
                'job_start': job_start.isoformat(),
                'job_end': datetime.now().isoformat()
            }
            
            self.last_run_results = error_results
            
            if self.config['monitoring']['email_notifications']:
                self.send_email_notification(error_results, [error_msg])
            
            return error_results
    
    def save_run_log(self, results: Dict):
        """Save run results to log file"""
        try:
            log_file = "scraping_runs.jsonl"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(results, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"Error saving run log: {e}")
    
    def send_email_notification(self, results: Dict, alerts: list):
        """Send email notification about scraping results"""
        try:
            email_config = self.config['email']
            if not email_config['sender_email'] or not email_config['recipient_emails']:
                logger.warning("Email configuration incomplete, skipping notification")
                return
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = email_config['sender_email']
            msg['To'] = ', '.join(email_config['recipient_emails'])
            
            if alerts:
                msg['Subject'] = "🚨 Legal Scraper Alert - Issues Detected"
                body = f"""
                Alerta do Sistema de Coleta de Dados Jurídicos
                
                Problemas detectados na execução de {datetime.now().strftime('%d/%m/%Y %H:%M')}:
                
                ALERTAS:
                {chr(10).join(f'• {alert}' for alert in alerts)}
                
                RESUMO DA EXECUÇÃO:
                • Total coletado: {results.get('total_scraped', 0)}
                • Total salvo: {results.get('total_saved', 0)}
                • Taxa de sucesso: {results.get('success_rate', 0):.2%}
                • Erros: {len(results.get('errors', []))}
                
                DETALHES POR FONTE:
                """
                
                for source, stats in results.get('scraper_results', {}).items():
                    body += f"\n• {source}: {stats['scraped']} coletados, {stats['saved']} salvos, {stats['errors']} erros"
                
            else:
                msg['Subject'] = "✅ Legal Scraper - Execução Bem-sucedida"
                body = f"""
                Relatório do Sistema de Coleta de Dados Jurídicos
                
                Execução bem-sucedida em {datetime.now().strftime('%d/%m/%Y %H:%M')}:
                
                RESUMO:
                • Total coletado: {results.get('total_scraped', 0)}
                • Total salvo: {results.get('total_saved', 0)}
                • Taxa de sucesso: {results.get('success_rate', 0):.2%}
                • Duração: {results.get('duration', 'N/A')}
                
                DETALHES POR FONTE:
                """
                
                for source, stats in results.get('scraper_results', {}).items():
                    body += f"\n• {source}: {stats['scraped']} coletados, {stats['saved']} salvos"
            
            msg.attach(MimeText(body, 'plain', 'utf-8'))
            
            # Send email
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['sender_email'], email_config['sender_password'])
            server.send_message(msg)
            server.quit()
            
            logger.info("Email notification sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    def send_webhook_notification(self, results: Dict):
        """Send webhook notification"""
        try:
            import requests
            
            webhook_url = self.config['monitoring']['webhook_url']
            payload = {
                'timestamp': datetime.now().isoformat(),
                'service': 'legal-scraper',
                'results': results
            }
            
            response = requests.post(webhook_url, json=payload, timeout=30)
            response.raise_for_status()
            
            logger.info("Webhook notification sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
    
    def schedule_jobs(self):
        """Set up the scheduled jobs"""
        schedule_config = self.config['schedule']
        
        # Schedule main scraping job
        getattr(schedule.every(), schedule_config['day_of_week']).at(
            schedule_config['time']
        ).do(self.run_scraping_job)
        
        # Schedule daily health check
        schedule.every().day.at("06:00").do(self.health_check)
        
        # Schedule weekly database maintenance
        schedule.every().sunday.at("01:00").do(self.database_maintenance)
        
        logger.info(f"Scheduled jobs: Main scraping on {schedule_config['day_of_week']} at {schedule_config['time']}")
    
    def health_check(self):
        """Perform daily health check"""
        try:
            logger.info("Running daily health check...")
            
            # Check database status
            stats = self.scraper_manager.get_scraping_stats()
            
            # Check recent activity
            recent_threshold = datetime.now() - timedelta(days=7)
            recent_docs = stats.get('recent_documents', 0)
            
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'database_status': 'healthy' if stats.get('total_documents', 0) > 0 else 'empty',
                'recent_activity': 'active' if recent_docs > 0 else 'inactive',
                'total_documents': stats.get('total_documents', 0),
                'recent_documents': recent_docs,
                'sources_active': len(stats.get('documents_by_source', {}))
            }
            
            # Log health status
            logger.info(f"Health check completed: {health_status}")
            
            # Save health log
            with open('health_checks.jsonl', 'a', encoding='utf-8') as f:
                f.write(json.dumps(health_status, ensure_ascii=False) + '\n')
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def database_maintenance(self):
        """Perform weekly database maintenance"""
        try:
            logger.info("Running weekly database maintenance...")
            
            # Cleanup old data
            deleted_count = self.scraper_manager.cleanup_old_data(
                days_to_keep=self.config['database']['days_to_keep']
            )
            
            # Backup database if configured
            backup_path = None
            if self.config['database']['backup_enabled']:
                backup_path = self.backup_database()
            
            maintenance_results = {
                'timestamp': datetime.now().isoformat(),
                'deleted_records': deleted_count,
                'backup_created': backup_path is not None,
                'backup_path': backup_path
            }
            
            logger.info(f"Database maintenance completed: {maintenance_results}")
            
            return maintenance_results
            
        except Exception as e:
            logger.error(f"Database maintenance failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def backup_database(self) -> Optional[str]:
        """Create database backup"""
        try:
            import shutil
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"legal_texts_backup_{timestamp}.db"
            backup_path = os.path.join('backups', backup_filename)
            
            # Create backups directory
            os.makedirs('backups', exist_ok=True)
            
            # Copy database file
            shutil.copy2('legal_texts.db', backup_path)
            
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return None
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        self.schedule_jobs()
        
        logger.info("Scheduler started successfully")
        
        # Run scheduler loop in separate thread
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        return scheduler_thread
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        logger.info("Scheduler stopped")
    
    def run_manual_scraping(self, limit_per_scraper: int = None) -> Dict:
        """Run scraping manually (outside of schedule)"""
        logger.info("Running manual scraping job...")
        
        if limit_per_scraper is None:
            limit_per_scraper = self.config['scraping']['limit_per_scraper']
        
        return self.run_scraping_job()
    
    def get_status(self) -> Dict:
        """Get current scheduler status"""
        return {
            'is_running': self.is_running,
            'next_run': str(schedule.next_run()) if schedule.jobs else None,
            'last_run_results': self.last_run_results,
            'config': self.config,
            'scheduled_jobs': len(schedule.jobs)
        }

# Command-line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Legal Text Scraping Scheduler")
    parser.add_argument('--start', action='store_true', help='Start the scheduler')
    parser.add_argument('--run-once', action='store_true', help='Run scraping once and exit')
    parser.add_argument('--health-check', action='store_true', help='Run health check')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--limit', type=int, help='Limit per scraper for manual run')
    
    args = parser.parse_args()
    
    # Initialize scheduler
    config_path = args.config or "scheduler_config.json"
    scheduler = ScrapingScheduler(config_path)
    
    if args.run_once:
        # Run scraping once
        results = scheduler.run_manual_scraping(args.limit)
        print(f"Scraping completed: {results['total_scraped']} scraped, {results['total_saved']} saved")
        
    elif args.health_check:
        # Run health check
        health = scheduler.health_check()
        print(f"Health check: {health}")
        
    elif args.start:
        # Start scheduler
        try:
            thread = scheduler.start()
            print("Scheduler started. Press Ctrl+C to stop.")
            
            # Keep main thread alive
            while scheduler.is_running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nStopping scheduler...")
            scheduler.stop()
            print("Scheduler stopped.")
    
    else:
        parser.print_help()