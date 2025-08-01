from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

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
        'gemini_configured': model is not None
    })

if __name__ == '__main__':
    # For Google Colab, we need to run on all interfaces
    app.run(host='0.0.0.0', port=5000, debug=True)