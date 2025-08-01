from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai
import os
import logging
from datetime import datetime, timedelta
from database import LegalTextDatabase, LegalText
from legal_scrapers import LegalScraperManager
from data_processor import LegalTextProcessor
from scheduler import ScrapingScheduler
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize components
database = LegalTextDatabase()
scraper_manager = LegalScraperManager()
text_processor = LegalTextProcessor()
scheduler = ScrapingScheduler()

# Configure Gemini API
def configure_gemini():
    """Configure Gemini API with the provided API key"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable not set")
        return None
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    return model

def get_correction_prompt():
    """Return the prompt for legal text correction"""
    return """Você é um assistente especializado em escrita jurídica brasileira. Sua tarefa é melhorar a gramática e coesão do texto fornecido, mantendo:

1. O significado legal intacto
2. A estrutura jurídica apropriada
3. Tom formal e profissional adequado para documentos legais brasileiros
4. Terminologia jurídica correta

Corrija apenas:
- Erros gramaticais
- Problemas de coesão e fluxo lógico
- Tom inadequado (transforme linguagem informal em formal jurídica)
- Estrutura de frases para maior clareza

NÃO ALTERE:
- O conteúdo legal substantivo
- Os fatos apresentados
- As conclusões jurídicas

Retorne apenas a versão corrigida do texto:

Texto para correção:
"""

@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('index.html')

@app.route('/api/correct', methods=['POST'])
def correct_text():
    """API endpoint to correct legal text using Gemini"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
        
        original_text = data['text'].strip()
        if not original_text:
            return jsonify({'error': 'Empty text provided'}), 400
        
        # Configure Gemini
        model = configure_gemini()
        if not model:
            return jsonify({'error': 'Gemini API not configured. Please set GEMINI_API_KEY environment variable.'}), 500
        
        # Prepare the prompt
        full_prompt = get_correction_prompt() + original_text
        
        # Generate correction
        logger.info("Sending text to Gemini for correction")
        response = model.generate_content(full_prompt)
        
        if not response.text:
            return jsonify({'error': 'No response from Gemini API'}), 500
        
        corrected_text = response.text.strip()
        
        # Return both original and corrected versions
        return jsonify({
            'original': original_text,
            'corrected': corrected_text,
            'success': True
        })
    
    except Exception as e:
        logger.error(f"Error in text correction: {str(e)}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    model = configure_gemini()
    return jsonify({
        'status': 'healthy',
        'gemini_configured': model is not None,
        'database_stats': database.get_database_stats(),
        'scheduler_status': scheduler.get_status()
    })

# New API endpoints for scraper management

@app.route('/api/admin/dashboard')
def admin_dashboard():
    """Serve admin dashboard"""
    return render_template('admin_dashboard.html')

@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    """Get comprehensive admin statistics"""
    try:
        stats = {
            'database': database.get_database_stats(),
            'scheduler': scheduler.get_status(),
            'processing': text_processor.get_processing_stats(),
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/scrape/manual', methods=['POST'])
def run_manual_scraping():
    """Run manual scraping job"""
    try:
        data = request.get_json() or {}
        limit = data.get('limit', 25)
        
        # Run scraping in background thread
        def run_scraping():
            results = scheduler.run_manual_scraping(limit_per_scraper=limit)
            logger.info(f"Manual scraping completed: {results}")
        
        thread = threading.Thread(target=run_scraping, daemon=True)
        thread.start()
        
        return jsonify({
            'message': 'Manual scraping started',
            'limit_per_scraper': limit
        })
    except Exception as e:
        logger.error(f"Error starting manual scraping: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/process/texts', methods=['POST'])
def process_unprocessed_texts():
    """Process unprocessed texts"""
    try:
        data = request.get_json() or {}
        batch_size = data.get('batch_size', 10)
        
        # Run processing in background thread
        def run_processing():
            results = text_processor.process_unprocessed_texts(batch_size=batch_size)
            logger.info(f"Text processing completed: {results}")
        
        thread = threading.Thread(target=run_processing, daemon=True)
        thread.start()
        
        return jsonify({
            'message': 'Text processing started',
            'batch_size': batch_size
        })
    except Exception as e:
        logger.error(f"Error starting text processing: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/scheduler/start', methods=['POST'])
def start_scheduler():
    """Start the automated scheduler"""
    try:
        scheduler.start()
        return jsonify({'message': 'Scheduler started successfully'})
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """Stop the automated scheduler"""
    try:
        scheduler.stop()
        return jsonify({'message': 'Scheduler stopped successfully'})
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/database/search', methods=['GET'])
def search_database():
    """Search legal texts in database"""
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 50))
        
        if not query:
            # Get latest texts if no query
            texts = database.get_latest_texts(limit)
        else:
            # Search texts
            texts = database.search_texts(query, limit)
        
        # Convert to JSON-serializable format
        results = []
        for text in texts:
            results.append({
                'id': text.id,
                'title': text.title,
                'content': text.content[:300] + '...' if len(text.content) > 300 else text.content,
                'source': text.source,
                'category': text.category,
                'quality_score': text.quality_score,
                'word_count': text.word_count,
                'date_scraped': text.date_scraped.isoformat() if text.date_scraped else None,
                'is_processed': text.is_processed,
                'tags': text.tags
            })
        
        return jsonify({
            'results': results,
            'total': len(results),
            'query': query
        })
    except Exception as e:
        logger.error(f"Error searching database: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/database/cleanup', methods=['POST'])
def cleanup_database():
    """Clean up old database records"""
    try:
        data = request.get_json() or {}
        days_to_keep = data.get('days_to_keep', 90)
        
        deleted_count = database.cleanup_old_data(days_to_keep)
        
        return jsonify({
            'message': f'Database cleanup completed',
            'deleted_records': deleted_count,
            'days_to_keep': days_to_keep
        })
    except Exception as e:
        logger.error(f"Error cleaning up database: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/training-data/generate', methods=['POST'])
def generate_training_data():
    """Generate training data from processed texts"""
    try:
        data = request.get_json() or {}
        limit = data.get('limit', 100)
        
        training_data = text_processor.generate_training_data(limit)
        
        return jsonify({
            'message': 'Training data generated successfully',
            'examples_count': len(training_data),
            'training_data': training_data[:10]  # Return first 10 examples
        })
    except Exception as e:
        logger.error(f"Error generating training data: {e}")
        return jsonify({'error': str(e)}), 500

# Enhanced correction endpoint with database integration
@app.route('/api/correct/enhanced', methods=['POST'])
def correct_text_enhanced():
    """Enhanced text correction using database insights"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
        
        original_text = data['text'].strip()
        if not original_text:
            return jsonify({'error': 'Empty text provided'}), 400
        
        # Configure Gemini
        model = configure_gemini()
        if not model:
            return jsonify({'error': 'Gemini API not configured'}), 500
        
        # Search for similar texts in database for context
        similar_texts = database.search_texts(original_text[:100], limit=5)
        
        # Enhanced prompt with database context
        context_examples = ""
        if similar_texts:
            context_examples = "\n\nExemplos de textos similares bem escritos:\n"
            for text in similar_texts[:2]:
                if text.quality_score > 0.7:
                    context_examples += f"- {text.content[:200]}...\n"
        
        enhanced_prompt = get_correction_prompt() + context_examples + "\n\nTexto para correção:\n" + original_text
        
        # Generate correction
        logger.info("Sending text to Gemini for enhanced correction")
        response = model.generate_content(enhanced_prompt)
        
        if not response.text:
            return jsonify({'error': 'No response from Gemini API'}), 500
        
        corrected_text = response.text.strip()
        
        # Save the correction example to database for future reference
        legal_text = LegalText(
            title="Exemplo de Correção",
            content=f"Original: {original_text}\n\nCorrigido: {corrected_text}",
            source="Correção Manual",
            url="internal://correction",
            category="Exemplo",
            tags=["correção", "exemplo"]
        )
        database.save_legal_text(legal_text)
        
        return jsonify({
            'original': original_text,
            'corrected': corrected_text,
            'enhanced': True,
            'context_used': len(similar_texts) > 0,
            'success': True
        })
    
    except Exception as e:
        logger.error(f"Error in enhanced text correction: {str(e)}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    # Start scheduler in background if configured
    try:
        if os.getenv('AUTO_START_SCHEDULER', '').lower() == 'true':
            scheduler.start()
            logger.info("Scheduler started automatically")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
    
    # For Google Colab, we need to run on all interfaces
    app.run(host='0.0.0.0', port=5000, debug=True)