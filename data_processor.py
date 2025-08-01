import re
import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import google.generativeai as genai
import os
from database import LegalText, LegalTextDatabase
import json
import time
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegalTextProcessor:
    """Advanced processor for legal text cleaning and enhancement"""
    
    def __init__(self, gemini_api_key: str = None):
        self.gemini_api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        self.database = LegalTextDatabase()
        
        # Legal terms and patterns
        self.legal_stopwords = {
            'artigo', 'inciso', 'parágrafo', 'alínea', 'item', 'subitem',
            'lei', 'decreto', 'portaria', 'resolução', 'instrução',
            'normativa', 'medida', 'provisória'
        }
        
        self.legal_patterns = {
            'law_reference': re.compile(r'Lei\s+n[º°]\s*(\d+(?:\.\d+)*)[\/\-](\d{4})', re.IGNORECASE),
            'article_reference': re.compile(r'art(?:igo)?\s*\.?\s*(\d+)', re.IGNORECASE),
            'court_decision': re.compile(r'AC(?:ÓRDÃO)?\s*n[º°]\s*(\d+)', re.IGNORECASE),
            'process_number': re.compile(r'(\d{7})\-(\d{2})\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})', re.IGNORECASE),
            'citation': re.compile(r'(\w+)\s*,\s*(Rel\.|Relator)\s*Min\.\s*(\w+)', re.IGNORECASE)
        }
        
        # Configure Gemini if API key available
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
            logger.warning("Gemini API key not provided - AI features will be disabled")
    
    def clean_text(self, text: str) -> str:
        """Deep clean legal text content"""
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common document artifacts
        artifacts = [
            r'Documento assinado digitalmente.*?$',
            r'Este texto não substitui.*?$',
            r'Publicado no D\.?O\.?U\.?.*?$',
            r'Fonte:.*?$',
            r'Atualizado até.*?$',
            r'Visualização de impressão.*?$'
        ]
        
        for artifact in artifacts:
            text = re.sub(artifact, '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        # Normalize legal formatting
        text = self.normalize_legal_formatting(text)
        
        # Remove excessive line breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def normalize_legal_formatting(self, text: str) -> str:
        """Normalize legal document formatting"""
        # Standardize article references
        text = re.sub(r'Art\.?\s*(\d+)', r'Artigo \1', text, flags=re.IGNORECASE)
        
        # Standardize paragraph symbols
        text = re.sub(r'§\s*(\d+)', r'§\1º', text)
        
        # Standardize law references
        text = re.sub(r'Lei\s+n[º°]?\s*(\d+)[\/\-](\d{4})', r'Lei nº \1/\2', text, flags=re.IGNORECASE)
        
        # Normalize quotes
        text = re.sub(r'[""]', '"', text)
        text = re.sub(r'['']', "'", text)
        
        return text
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract legal entities from text"""
        entities = {
            'laws': [],
            'articles': [],
            'court_decisions': [],
            'process_numbers': [],
            'citations': []
        }
        
        # Extract law references
        for match in self.legal_patterns['law_reference'].finditer(text):
            entities['laws'].append(f"Lei nº {match.group(1)}/{match.group(2)}")
        
        # Extract article references
        for match in self.legal_patterns['article_reference'].finditer(text):
            entities['articles'].append(f"Artigo {match.group(1)}")
        
        # Extract court decisions
        for match in self.legal_patterns['court_decision'].finditer(text):
            entities['court_decisions'].append(f"Acórdão nº {match.group(1)}")
        
        # Extract process numbers
        for match in self.legal_patterns['process_number'].finditer(text):
            entities['process_numbers'].append(match.group(0))
        
        # Extract citations
        for match in self.legal_patterns['citation'].finditer(text):
            entities['citations'].append(match.group(0))
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    def categorize_text(self, text: str, title: str = "") -> str:
        """Categorize legal text by content analysis"""
        content = (title + " " + text).lower()
        
        categories = {
            'Constitucional': ['constituição', 'constitucional', 'supremo', 'stf', 'fundamental'],
            'Civil': ['civil', 'contrato', 'propriedade', 'responsabilidade', 'danos'],
            'Penal': ['penal', 'crime', 'criminoso', 'pena', 'delito', 'prisão'],
            'Trabalhista': ['trabalhista', 'emprego', 'salário', 'tst', 'trabalho', 'empregado'],
            'Administrativo': ['administrativo', 'servidor', 'público', 'licitação', 'concurso'],
            'Tributário': ['tributário', 'imposto', 'tributo', 'receita', 'fiscal', 'icms', 'ipi'],
            'Comercial': ['comercial', 'empresa', 'sociedade', 'falência', 'recuperação'],
            'Processual': ['processual', 'recurso', 'apelação', 'embargos', 'processo'],
            'Ambiental': ['ambiental', 'meio ambiente', 'poluição', 'recursos naturais'],
            'Consumidor': ['consumidor', 'fornecedor', 'produto', 'serviço', 'cdc']
        }
        
        scores = {}
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in content)
            if score > 0:
                scores[category] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return "Geral"
    
    def calculate_enhanced_quality_score(self, legal_text: LegalText) -> float:
        """Calculate enhanced quality score using multiple factors"""
        score = 0.0
        
        # Basic length scoring (25%)
        if legal_text.word_count > 1000:
            score += 0.25
        elif legal_text.word_count > 500:
            score += 0.20
        elif legal_text.word_count > 200:
            score += 0.15
        elif legal_text.word_count > 50:
            score += 0.10
        
        # Title quality (15%)
        if legal_text.title:
            if len(legal_text.title) > 20:
                score += 0.15
            elif len(legal_text.title) > 10:
                score += 0.10
            else:
                score += 0.05
        
        # Legal terminology density (25%)
        legal_terms = [
            'acórdão', 'sentença', 'despacho', 'decisão', 'recurso',
            'apelação', 'embargos', 'habeas corpus', 'mandado',
            'constitucional', 'civil', 'penal', 'trabalhista',
            'administrativo', 'tributário', 'comercial', 'artigo',
            'lei', 'decreto', 'código', 'jurisprudência'
        ]
        
        content_lower = legal_text.content.lower()
        term_count = sum(1 for term in legal_terms if term in content_lower)
        term_density = term_count / max(legal_text.word_count / 100, 1)
        score += min(term_density * 0.05, 0.25)
        
        # Source credibility (20%)
        source_lower = legal_text.source.lower()
        if any(court in source_lower for court in ['stf', 'stj', 'supremo', 'superior']):
            score += 0.20
        elif 'tribunal' in source_lower:
            score += 0.15
        elif 'gov.br' in legal_text.url:
            score += 0.12
        elif any(source in source_lower for source in ['conjur', 'migalhas']):
            score += 0.10
        else:
            score += 0.05
        
        # Structural quality (15%)
        if legal_text.date_published:
            score += 0.05
        
        # Check for proper legal structure
        if any(pattern.search(legal_text.content) for pattern in self.legal_patterns.values()):
            score += 0.10
        
        return min(score, 1.0)
    
    def enhance_with_ai(self, legal_text: LegalText) -> LegalText:
        """Enhance legal text using AI analysis"""
        if not self.model:
            logger.warning("AI enhancement skipped - Gemini API not available")
            return legal_text
        
        try:
            # Prepare AI prompt for analysis
            prompt = f"""
            Analise este texto jurídico brasileiro e forneça:
            1. Categoria principal (Constitucional, Civil, Penal, etc.)
            2. Tags relevantes (máximo 5)
            3. Score de qualidade (0-1) baseado em relevância jurídica
            4. Resumo em uma frase
            
            Texto: {legal_text.content[:2000]}...
            
            Responda em formato JSON:
            {{
                "categoria": "categoria_principal",
                "tags": ["tag1", "tag2", "tag3"],
                "qualidade": 0.85,
                "resumo": "resumo_do_texto"
            }}
            """
            
            # Add delay to respect API limits
            time.sleep(random.uniform(1, 2))
            
            response = self.model.generate_content(prompt)
            
            if response.text:
                try:
                    # Parse AI response
                    ai_analysis = json.loads(response.text.strip())
                    
                    # Update legal text with AI insights
                    if 'categoria' in ai_analysis:
                        legal_text.category = ai_analysis['categoria']
                    
                    if 'tags' in ai_analysis and isinstance(ai_analysis['tags'], list):
                        legal_text.tags.extend(ai_analysis['tags'])
                        legal_text.tags = list(set(legal_text.tags))  # Remove duplicates
                    
                    if 'qualidade' in ai_analysis:
                        ai_quality = float(ai_analysis['qualidade'])
                        # Combine with existing quality score
                        legal_text.quality_score = (legal_text.quality_score + ai_quality) / 2
                    
                    logger.info(f"AI enhancement completed for: {legal_text.title[:50]}...")
                    
                except json.JSONDecodeError:
                    logger.warning("Failed to parse AI response JSON")
                
        except Exception as e:
            logger.error(f"AI enhancement failed: {e}")
        
        return legal_text
    
    def process_text(self, legal_text: LegalText) -> LegalText:
        """Complete processing pipeline for a legal text"""
        logger.info(f"Processing text: {legal_text.title[:50]}...")
        
        # Step 1: Clean content
        legal_text.content = self.clean_text(legal_text.content)
        legal_text.title = self.clean_text(legal_text.title)
        
        # Step 2: Update word count
        legal_text.word_count = len(legal_text.content.split())
        
        # Step 3: Extract entities and add as tags
        entities = self.extract_entities(legal_text.content)
        for entity_type, entity_list in entities.items():
            if entity_list:
                legal_text.tags.extend([f"{entity_type}:{entity}" for entity in entity_list[:3]])
        
        # Step 4: Categorize if not already categorized
        if not legal_text.category or legal_text.category == "Geral":
            legal_text.category = self.categorize_text(legal_text.content, legal_text.title)
        
        # Step 5: Calculate enhanced quality score
        legal_text.quality_score = self.calculate_enhanced_quality_score(legal_text)
        
        # Step 6: AI enhancement (if available)
        legal_text = self.enhance_with_ai(legal_text)
        
        # Step 7: Mark as processed
        legal_text.is_processed = True
        
        logger.info(f"Text processed - Category: {legal_text.category}, Quality: {legal_text.quality_score:.2f}")
        
        return legal_text
    
    def process_unprocessed_texts(self, batch_size: int = 10) -> Dict:
        """Process all unprocessed texts in the database"""
        logger.info("Starting batch processing of unprocessed texts...")
        
        start_time = datetime.now()
        processed_count = 0
        error_count = 0
        errors = []
        
        try:
            # Get unprocessed texts
            unprocessed_texts = self.database.get_latest_texts(limit=1000)
            unprocessed_texts = [text for text in unprocessed_texts if not text.is_processed]
            
            logger.info(f"Found {len(unprocessed_texts)} unprocessed texts")
            
            # Process in batches
            for i in range(0, len(unprocessed_texts), batch_size):
                batch = unprocessed_texts[i:i + batch_size]
                
                for legal_text in batch:
                    try:
                        # Process text
                        processed_text = self.process_text(legal_text)
                        
                        # Update in database (need to implement update method)
                        # For now, we'll create a new record with processed data
                        if self.database.save_legal_text(processed_text):
                            processed_count += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing text {legal_text.id}: {e}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        error_count += 1
                
                # Progress logging
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(unprocessed_texts)-1)//batch_size + 1}")
                
                # Delay between batches to avoid overwhelming APIs
                if self.model:
                    time.sleep(2)
        
        except Exception as e:
            error_msg = f"Batch processing failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        end_time = datetime.now()
        
        results = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration': str(end_time - start_time),
            'processed_count': processed_count,
            'error_count': error_count,
            'errors': errors,
            'total_found': len(unprocessed_texts) if 'unprocessed_texts' in locals() else 0
        }
        
        logger.info(f"Batch processing completed: {processed_count} processed, {error_count} errors")
        
        return results
    
    def generate_training_data(self, limit: int = 100) -> List[Dict]:
        """Generate training data from processed legal texts"""
        logger.info(f"Generating training data from processed texts...")
        
        # Get high-quality processed texts
        processed_texts = self.database.get_latest_texts(limit=limit * 2)
        high_quality_texts = [
            text for text in processed_texts 
            if text.is_processed and text.quality_score > 0.7
        ][:limit]
        
        training_data = []
        
        for text in high_quality_texts:
            # Create training example
            training_example = {
                'input': text.content,
                'category': text.category,
                'quality_score': text.quality_score,
                'tags': text.tags,
                'source': text.source,
                'word_count': text.word_count,
                'processed_date': text.date_scraped.isoformat() if text.date_scraped else None
            }
            
            training_data.append(training_example)
        
        logger.info(f"Generated {len(training_data)} training examples")
        
        return training_data
    
    def get_processing_stats(self) -> Dict:
        """Get statistics about text processing"""
        stats = self.database.get_database_stats()
        
        # Add processing-specific stats
        processing_stats = {
            'total_documents': stats.get('total_documents', 0),
            'processed_documents': 0,  # Would need database query
            'average_quality': stats.get('average_quality_score', 0),
            'categories_distribution': {},  # Would need database query
            'ai_enhancement_available': self.model is not None
        }
        
        return processing_stats

# Command-line interface for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Legal Text Data Processor")
    parser.add_argument('--process-unprocessed', action='store_true', help='Process all unprocessed texts')
    parser.add_argument('--generate-training-data', type=int, help='Generate training data (specify limit)')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for processing')
    
    args = parser.parse_args()
    
    processor = LegalTextProcessor()
    
    if args.process_unprocessed:
        results = processor.process_unprocessed_texts(batch_size=args.batch_size)
        print(f"Processing completed: {results['processed_count']} processed, {results['error_count']} errors")
    
    elif args.generate_training_data:
        training_data = processor.generate_training_data(limit=args.generate_training_data)
        
        # Save training data
        with open('legal_training_data.json', 'w', encoding='utf-8') as f:
            json.dump(training_data, f, indent=2, ensure_ascii=False)
        
        print(f"Training data saved: {len(training_data)} examples")
    
    else:
        stats = processor.get_processing_stats()
        print(f"Processing stats: {stats}")