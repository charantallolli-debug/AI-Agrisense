"""
Application entry point and server launcher.
Run this file to start the Flask development server.

Usage:
    python run.py                    # Development server
    FLASK_ENV=production python run.py  # Production server
"""
import os
import sys
import logging

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create app with appropriate config
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    logger.info(f"Starting Flask app in {config_name} mode")
    
    port = int(os.environ.get('PORT', 5000))
    # Development settings
    if config_name == 'development':
        # Disable reloader on macOS — TensorFlow + fork causes segfaults
        use_reloader = sys.platform != 'darwin'
        app.run(
            host='0.0.0.0',
            port=port,
            debug=True,
            use_reloader=use_reloader
        )
    else:
        # Production settings (use proper WSGI server in production)
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False
        )
