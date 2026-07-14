#!/usr/bin/env python3
"""
Water Meter Leak Detection - Flask Backend
Main entry point for Raspberry Pi deployment.
"""

import os
import logging
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import components
from firebase_listener import FirebaseListener
from ml_inference import LeakDetector
from alert_engine import AlertEngine


# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-change-in-production')


# Initialize components
logger.info("Initializing components...")

# Firebase Listener
listener = FirebaseListener(
    firebase_config_path='firebase_config.json',
    email=os.getenv('FIREBASE_EMAIL'),
    password=os.getenv('FIREBASE_PASSWORD'),
    device_id=os.getenv('DEVICE_ID', 'wm_001')
)

# ML Detector
detector = LeakDetector(
    xgb_path='models/xgboost_model.json',
    iforest_path='models/isolation_forest.pkl',
    scaler_path='models/scaler.pkl',
    threshold_path='models/iso_threshold.pkl',
    confidence_threshold=float(os.getenv('CONFIDENCE_THRESHOLD', '0.80'))
)

# Alert Engine
alert_engine = AlertEngine()

# Warm up detector
detector.warm_up()

# Start Firebase listener in background
logger.info("Starting Firebase listener...")
listener.start()


# Routes
@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/alerts')
def alerts_page():
    """Alerts history page"""
    return render_template('alerts.html')


@app.route('/api/latest')
def api_latest():
    """Get latest sensor reading"""
    latest = listener.get_latest_reading()
    if latest:
        return jsonify(latest)
    return jsonify({'error': 'No data available'}), 404


@app.route('/api/alerts')
def api_alerts():
    """Get recent alerts"""
    limit = request.args.get('limit', 20, type=int)
    alerts = listener.get_recent_alerts(limit=limit)
    return jsonify(alerts if alerts else [])


@app.route('/api/predict', methods=['POST'])
def api_predict():
    """Run ML inference on provided features"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Extract features from request
        features = extract_features_from_request(data)
        
        # Run inference
        result = detector.predict(features)
        
        return jsonify(result)
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/command', methods=['POST'])
def api_command():
    """Send command to ESP32 via Firebase"""
    try:
        data = request.get_json()
        if not data or 'command' not in data:
            return jsonify({'error': 'Missing command'}), 400
        
        command = data['command']
        listener.send_command(command)
        
        return jsonify({'status': 'sent', 'command': command})
    
    except Exception as e:
        logger.error(f"Command error: {e}")
        return jsonify({'error': 'Failed to send command'}), 500


@app.route('/api/model_info')
def api_model_info():
    """Get model metadata"""
    try:
        import json
        with open('models/metadata.json') as f:
            metadata = json.load(f)
        return jsonify(metadata)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'firebase_connected': listener.is_connected() if hasattr(listener, 'is_connected') else True,
        'model_loaded': detector.model_loaded,
        'uptime_seconds': get_uptime()
    })


def extract_features_from_request(data: dict) -> list:
    """
    Extract 9 features from request data.
    Expected format matches training feature engineering.
    """
    # This is a simplified version - in production, match training exactly
    # Features: [flow_rate, duration, hour, day, fixture_id, inlet_ratio, rate_variance, is_night, pulse_trend]
    
    features = [
        data.get('flow_rate', 0.0),
        data.get('duration', 0),
        data.get('hour', 12),
        data.get('day', 1),
        data.get('fixture_id', 1),
        data.get('inlet_ratio', 1.0),
        data.get('rate_variance', 0.0),
        data.get('is_night', 0),
        data.get('pulse_trend', 0.0)
    ]
    
    return features


def get_uptime():
    """Get system uptime in seconds"""
    try:
        with open('/proc/uptime', 'r') as f:
            return float(f.read().split()[0])
    except:
        return 0


# Template filters
@app.template_filter('datetime')
def format_datetime(value):
    """Format ISO timestamp for display"""
    if not value:
        return 'N/A'
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return value


# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal error: {e}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Development server
    port = int(os.getenv('PORT', '5000'))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    
    logger.info(f"Starting Flask server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)