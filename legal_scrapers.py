import requests
import logging
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import random
from urllib.parse import urljoin, urlparse
from database import LegalText, LegalTextDatabase
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseLegalScraper:
    """Base class for legal text scrapers"""
    
    def __init__(self, name: str, base_url: str, delay_range: tuple = (1, 3)):
        self.name = name
        self.base_url = base_url
        self.delay_range = delay_range
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.scraped_count = 0
        self.saved_count = 0
        self.errors = []
    
    def random_delay(self):
        """Add random delay between requests to be respectful"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
    
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page"""
        try:
            self.random_delay()
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            error_msg = f"Error fetching {url}: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common legal document artifacts
        text = re.sub(r'ACÓRDÃO.*?RELATÓRIO', 'RELATÓRIO', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'Documento assinado.*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        return text
    
    def extract_date(self, text: str) -> Optional[datetime]:
        """Extract date from text using common Brazilian date formats"""
        date_patterns = [
            r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})',
            r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})',
            r'(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})'
        ]
        
        months_pt = {
            'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
            'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
            'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
        }
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if 'de' in pattern:  # Portuguese date format
                        day, month_name, year = match.groups()
                        month = months_pt.get(month_name.lower(), 1)
                        return datetime(int(year), month, int(day))
                    else:  # Numeric date format
                        parts = match.groups()
                        if len(parts[0]) == 4:  # Year first
                            year, month, day = parts
                        else:  # Day first
                            day, month, year = parts
                        return datetime(int(year), int(month), int(day))
                except ValueError:
                    continue
        
        return None
    
    def calculate_quality_score(self, legal_text: LegalText) -> float:
        """Calculate quality score for legal text"""
        score = 0.0
        
        # Word count scoring (30%)
        if legal_text.word_count > 500:
            score += 0.3
        elif legal_text.word_count > 200:
            score += 0.2
        elif legal_text.word_count > 50:
            score += 0.1
        
        # Title quality (20%)
        if legal_text.title and len(legal_text.title) > 10:
            score += 0.2
        
        # Legal keywords presence (30%)
        legal_keywords = [
            'acórdão', 'sentença', 'despacho', 'decisão', 'recurso',
            'apelação', 'embargos', 'habeas corpus', 'mandado',
            'constitucional', 'civil', 'penal', 'trabalhista',
            'administrativo', 'tributário', 'comercial'
        ]
        
        content_lower = legal_text.content.lower()
        keyword_count = sum(1 for keyword in legal_keywords if keyword in content_lower)
        score += min(keyword_count * 0.05, 0.3)
        
        # Source credibility (20%)
        if 'stf' in legal_text.source.lower() or 'stj' in legal_text.source.lower():
            score += 0.2
        elif 'tribunal' in legal_text.source.lower():
            score += 0.15
        elif 'gov.br' in legal_text.url:
            score += 0.1
        
        return min(score, 1.0)
    
    def scrape(self, limit: int = 50) -> List[LegalText]:
        """Abstract method to be implemented by specific scrapers"""
        raise NotImplementedError("Subclasses must implement scrape method")

class STFScraper(BaseLegalScraper):
    """Scraper for Supreme Federal Court (STF) decisions"""
    
    def __init__(self):
        super().__init__(
            name="STF - Supremo Tribunal Federal",
            base_url="https://portal.stf.jus.br",
            delay_range=(2, 4)
        )
    
    def scrape(self, limit: int = 50) -> List[LegalText]:
        """Scrape recent decisions from STF"""
        legal_texts = []
        
        try:
            # Search for recent decisions
            search_url = f"{self.base_url}/jurisprudencia/"
            soup = self.get_page(search_url)
            
            if not soup:
                return legal_texts
            
            # Find decision links
            decision_links = soup.find_all('a', href=re.compile(r'decision|acordao|sentenca'))[:limit]
            
            for link in decision_links:
                try:
                    decision_url = urljoin(self.base_url, link.get('href'))
                    decision_soup = self.get_page(decision_url)
                    
                    if not decision_soup:
                        continue
                    
                    # Extract title
                    title_elem = decision_soup.find(['h1', 'h2', 'title'])
                    title = self.clean_text(title_elem.get_text()) if title_elem else "Decisão STF"
                    
                    # Extract content
                    content_selectors = [
                        '.decision-content', '.acordao-text', '.content-text',
                        '.main-content', '#content', 'main'
                    ]
                    
                    content = ""
                    for selector in content_selectors:
                        content_elem = decision_soup.select_one(selector)
                        if content_elem:
                            content = self.clean_text(content_elem.get_text())
                            break
                    
                    if not content:
                        # Fallback: get all text from body
                        body = decision_soup.find('body')
                        if body:
                            content = self.clean_text(body.get_text())
                    
                    if len(content) > 100:  # Minimum content length
                        legal_text = LegalText(
                            title=title,
                            content=content,
                            source=self.name,
                            url=decision_url,
                            category="Jurisprudência",
                            date_published=self.extract_date(content)
                        )
                        
                        legal_text.quality_score = self.calculate_quality_score(legal_text)
                        legal_texts.append(legal_text)
                        self.scraped_count += 1
                        
                        logger.info(f"Scraped STF decision: {title[:50]}...")
                    
                except Exception as e:
                    error_msg = f"Error processing STF decision: {e}"
                    logger.error(error_msg)
                    self.errors.append(error_msg)
        
        except Exception as e:
            error_msg = f"Error scraping STF: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
        
        return legal_texts

class STJScraper(BaseLegalScraper):
    """Scraper for Superior Justice Court (STJ) decisions"""
    
    def __init__(self):
        super().__init__(
            name="STJ - Superior Tribunal de Justiça",
            base_url="https://www.stj.jus.br",
            delay_range=(2, 4)
        )
    
    def scrape(self, limit: int = 50) -> List[LegalText]:
        """Scrape recent decisions from STJ"""
        legal_texts = []
        
        try:
            # Search for recent jurisprudence
            search_url = f"{self.base_url}/sites/portalp/Jurisprudencia"
            soup = self.get_page(search_url)
            
            if not soup:
                return legal_texts
            
            # Find jurisprudence links
            jurisprudence_links = soup.find_all('a', href=re.compile(r'acordao|decisao|jurisprudencia'))[:limit]
            
            for link in jurisprudence_links:
                try:
                    decision_url = urljoin(self.base_url, link.get('href'))
                    decision_soup = self.get_page(decision_url)
                    
                    if not decision_soup:
                        continue
                    
                    # Extract title
                    title_elem = decision_soup.find(['h1', 'h2', '.title'])
                    title = self.clean_text(title_elem.get_text()) if title_elem else "Decisão STJ"
                    
                    # Extract content
                    content_selectors = [
                        '.jurisprudencia-content', '.acordao-text', '.decision-text',
                        '.content-main', '#main-content'
                    ]
                    
                    content = ""
                    for selector in content_selectors:
                        content_elem = decision_soup.select_one(selector)
                        if content_elem:
                            content = self.clean_text(content_elem.get_text())
                            break
                    
                    if not content:
                        # Fallback
                        main_content = decision_soup.find('main') or decision_soup.find('body')
                        if main_content:
                            content = self.clean_text(main_content.get_text())
                    
                    if len(content) > 100:
                        legal_text = LegalText(
                            title=title,
                            content=content,
                            source=self.name,
                            url=decision_url,
                            category="Jurisprudência",
                            date_published=self.extract_date(content)
                        )
                        
                        legal_text.quality_score = self.calculate_quality_score(legal_text)
                        legal_texts.append(legal_text)
                        self.scraped_count += 1
                        
                        logger.info(f"Scraped STJ decision: {title[:50]}...")
                
                except Exception as e:
                    error_msg = f"Error processing STJ decision: {e}"
                    logger.error(error_msg)
                    self.errors.append(error_msg)
        
        except Exception as e:
            error_msg = f"Error scraping STJ: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
        
        return legal_texts

class ConsultorJuridicoScraper(BaseLegalScraper):
    """Scraper for Consultor Jurídico legal news"""
    
    def __init__(self):
        super().__init__(
            name="Consultor Jurídico",
            base_url="https://www.conjur.com.br",
            delay_range=(1, 2)
        )
    
    def scrape(self, limit: int = 50) -> List[LegalText]:
        """Scrape recent legal articles from Consultor Jurídico"""
        legal_texts = []
        
        try:
            # Get recent articles
            soup = self.get_page(self.base_url)
            
            if not soup:
                return legal_texts
            
            # Find article links
            article_links = soup.find_all('a', href=re.compile(r'/\d{4}-\w+-\d{2}'))[:limit]
            
            for link in article_links:
                try:
                    article_url = urljoin(self.base_url, link.get('href'))
                    article_soup = self.get_page(article_url)
                    
                    if not article_soup:
                        continue
                    
                    # Extract title
                    title_elem = article_soup.find(['h1', '.title', '.headline'])
                    title = self.clean_text(title_elem.get_text()) if title_elem else link.get_text()
                    
                    # Extract content
                    content_selectors = [
                        '.article-content', '.post-content', '.entry-content',
                        '.content', 'article'
                    ]
                    
                    content = ""
                    for selector in content_selectors:
                        content_elem = article_soup.select_one(selector)
                        if content_elem:
                            # Remove script and style elements
                            for script in content_elem(["script", "style"]):
                                script.decompose()
                            content = self.clean_text(content_elem.get_text())
                            break
                    
                    # Extract publication date
                    date_elem = article_soup.find(attrs={'class': re.compile(r'date|time')})
                    date_published = None
                    if date_elem:
                        date_published = self.extract_date(date_elem.get_text())
                    
                    if len(content) > 200:
                        legal_text = LegalText(
                            title=title,
                            content=content,
                            source=self.name,
                            url=article_url,
                            category="Notícias Jurídicas",
                            date_published=date_published,
                            tags=["notícias", "análise jurídica"]
                        )
                        
                        legal_text.quality_score = self.calculate_quality_score(legal_text)
                        legal_texts.append(legal_text)
                        self.scraped_count += 1
                        
                        logger.info(f"Scraped ConJur article: {title[:50]}...")
                
                except Exception as e:
                    error_msg = f"Error processing ConJur article: {e}"
                    logger.error(error_msg)
                    self.errors.append(error_msg)
        
        except Exception as e:
            error_msg = f"Error scraping ConJur: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
        
        return legal_texts

class MigalhasScraper(BaseLegalScraper):
    """Scraper for Migalhas legal news"""
    
    def __init__(self):
        super().__init__(
            name="Migalhas",
            base_url="https://www.migalhas.com.br",
            delay_range=(1, 2)
        )
    
    def scrape(self, limit: int = 50) -> List[LegalText]:
        """Scrape recent legal articles from Migalhas"""
        legal_texts = []
        
        try:
            soup = self.get_page(self.base_url)
            
            if not soup:
                return legal_texts
            
            # Find article links
            article_links = soup.find_all('a', href=re.compile(r'/noticia|/artigo'))[:limit]
            
            for link in article_links:
                try:
                    article_url = urljoin(self.base_url, link.get('href'))
                    article_soup = self.get_page(article_url)
                    
                    if not article_soup:
                        continue
                    
                    # Extract title
                    title_elem = article_soup.find(['h1', '.title', '.headline'])
                    title = self.clean_text(title_elem.get_text()) if title_elem else link.get_text()
                    
                    # Extract content
                    content_selectors = [
                        '.article-body', '.content-text', '.post-content',
                        '.entry-content', 'article'
                    ]
                    
                    content = ""
                    for selector in content_selectors:
                        content_elem = article_soup.select_one(selector)
                        if content_elem:
                            for script in content_elem(["script", "style"]):
                                script.decompose()
                            content = self.clean_text(content_elem.get_text())
                            break
                    
                    if len(content) > 200:
                        legal_text = LegalText(
                            title=title,
                            content=content,
                            source=self.name,
                            url=article_url,
                            category="Notícias Jurídicas",
                            date_published=self.extract_date(content),
                            tags=["migalhas", "notícias jurídicas"]
                        )
                        
                        legal_text.quality_score = self.calculate_quality_score(legal_text)
                        legal_texts.append(legal_text)
                        self.scraped_count += 1
                        
                        logger.info(f"Scraped Migalhas article: {title[:50]}...")
                
                except Exception as e:
                    error_msg = f"Error processing Migalhas article: {e}"
                    logger.error(error_msg)
                    self.errors.append(error_msg)
        
        except Exception as e:
            error_msg = f"Error scraping Migalhas: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
        
        return legal_texts

class LegalScraperManager:
    """Manager class to coordinate all legal scrapers"""
    
    def __init__(self, db_path: str = "legal_texts.db"):
        self.database = LegalTextDatabase(db_path)
        self.scrapers = [
            STFScraper(),
            STJScraper(),
            ConsultorJuridicoScraper(),
            MigalhasScraper()
        ]
    
    def run_all_scrapers(self, limit_per_scraper: int = 25) -> Dict:
        """Run all configured scrapers"""
        results = {
            'total_scraped': 0,
            'total_saved': 0,
            'scraper_results': {},
            'errors': []
        }
        
        start_time = datetime.now()
        
        for scraper in self.scrapers:
            logger.info(f"Starting scraper: {scraper.name}")
            scraper_start = datetime.now()
            
            try:
                # Reset scraper stats
                scraper.scraped_count = 0
                scraper.saved_count = 0
                scraper.errors = []
                
                # Scrape texts
                legal_texts = scraper.scrape(limit_per_scraper)
                
                # Save to database
                for legal_text in legal_texts:
                    if self.database.save_legal_text(legal_text):
                        scraper.saved_count += 1
                
                # Log scraping session
                scraper_end = datetime.now()
                self.database.log_scraping_session(
                    source=scraper.name,
                    start_time=scraper_start,
                    end_time=scraper_end,
                    status="completed",
                    items_scraped=scraper.scraped_count,
                    items_saved=scraper.saved_count,
                    errors=scraper.errors
                )
                
                results['scraper_results'][scraper.name] = {
                    'scraped': scraper.scraped_count,
                    'saved': scraper.saved_count,
                    'errors': len(scraper.errors)
                }
                
                results['total_scraped'] += scraper.scraped_count
                results['total_saved'] += scraper.saved_count
                results['errors'].extend(scraper.errors)
                
                logger.info(f"Completed {scraper.name}: {scraper.scraped_count} scraped, {scraper.saved_count} saved")
                
            except Exception as e:
                error_msg = f"Error running scraper {scraper.name}: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        end_time = datetime.now()
        results['duration'] = str(end_time - start_time)
        results['timestamp'] = end_time.isoformat()
        
        logger.info(f"Scraping completed: {results['total_scraped']} total scraped, {results['total_saved']} total saved")
        
        return results
    
    def get_scraping_stats(self) -> Dict:
        """Get statistics about scraping activities"""
        return self.database.get_database_stats()
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """Clean up old scraped data"""
        return self.database.cleanup_old_data(days_to_keep)