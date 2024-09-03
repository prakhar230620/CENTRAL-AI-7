from flask import Flask, render_template, request, jsonify
from ai_manager import AIManager
from input_analyzer import InputAnalyzer
from junction import Junction
from ai_selector import AISelector
import logging
import speech_recognition as sr
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

ai_manager = AIManager()
input_analyzer = InputAnalyzer()
junction = Junction()
ai_selector = AISelector()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/ai_manager')
def ai_manager_page():
    all_ai = ai_manager.get_all_ai()
    return render_template('ai_manager.html', ais=all_ai)

@app.route('/add_ai')
def add_ai_page():
    return render_template('add_ai.html')

@app.route('/api/process_input', methods=['POST'])
def process_input():
    try:
        data = request.json
        user_input = data.get('input')
        input_type = data.get('type')

        if not user_input or not input_type:
            return jsonify({"error": "Invalid input"}), 400

        analyzed_input = input_analyzer.analyze(user_input, input_type)
        all_ai = ai_manager.get_all_ai()
        selected_ai_id = ai_selector.select_best_ai(analyzed_input, list(all_ai.values()))

        if selected_ai_id == "No AI connected to the program":
            return jsonify({"message": selected_ai_id}), 200

        selected_ai = all_ai.get(selected_ai_id)
        if not selected_ai:
            return jsonify({"error": "Selected AI not found"}), 404

        # Run the asynchronous process in a separate thread
        loop = asyncio.new_event_loop()
        with ThreadPoolExecutor() as pool:
            result = loop.run_until_complete(
                loop.run_in_executor(pool, asyncio.run, junction.process(selected_ai, analyzed_input))
            )

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing input: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/add_ai', methods=['POST'])
def add_ai():
    try:
        ai_data = request.json
        logger.info(f"Received AI data: {ai_data}")
        required_fields = ['name', 'type', 'description']

        if not all(field in ai_data for field in required_fields):
            missing_fields = [field for field in required_fields if field not in ai_data]
            logger.error(f"Missing required fields: {missing_fields}")
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        # Add additional validation based on AI type
        if ai_data['type'] == 'api':
            if 'api-key' not in ai_data or 'api-endpoint' not in ai_data:
                logger.error("Missing API key or endpoint for API type")
                return jsonify({"error": "Missing API key or endpoint"}), 400
        elif ai_data['type'] in ['bot', 'custom_ai']:
            if 'ai-file' not in ai_data:
                logger.error("Missing AI file for bot or custom_ai type")
                return jsonify({"error": "Missing AI file"}), 400
        elif ai_data['type'] == 'local_ai':
            if 'ai-command' not in ai_data:
                logger.error("Missing AI command for local_ai type")
                return jsonify({"error": "Missing AI command"}), 400

        unique_id = ai_manager.add_ai(ai_data)
        logger.info(f"AI added successfully with ID: {unique_id}")

        return jsonify({'id': unique_id, 'message': 'AI added successfully'})
    except Exception as e:
        logger.error(f"Error adding AI: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/speech_to_text', methods=['POST'])
def speech_to_text():
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files['audio']
        recognizer = sr.Recognizer()

        try:
            with sr.AudioFile(audio_file) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            return jsonify({"error": "Speech recognition could not understand the audio"}), 400
        except sr.RequestError as e:
            return jsonify({"error": f"Could not request results from speech recognition service; {e}"}), 500

        return jsonify({"text": text})
    except Exception as e:
        logger.error(f"Error processing speech to text: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True)