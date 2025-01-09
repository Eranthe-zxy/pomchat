import http.server
import json
import os
import sys
import logging
import webbrowser
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import parse_qs, urlparse
from dotenv import load_dotenv
from db import DatabaseManager, Message
from repository_manager import RepositoryManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class MessageHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        try:
            self.db = DatabaseManager()
            self.github_token = os.getenv('GITHUB_TOKEN')
            self.repo_configs = json.loads(os.getenv('GITHUB_REPOSITORIES', '[]'))
            
            # Set up static file serving
            static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')
            logger.info(f"Static directory path: {static_dir}")
            
            # Initialize parent class with static directory
            super().__init__(*args, directory=static_dir, **kwargs)
            
        except Exception as e:
            logger.error(f"Error initializing handler: {str(e)}")
            raise

    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format%args}")

    def log_error(self, format, *args):
        logger.error(f"{self.address_string()} - {format%args}")

    def translate_path(self, path):
        """Override to ensure proper static file handling"""
        # Log the requested path for debugging
        logger.info(f"Translating path: {path}")
        
        # Handle root path
        if path == '/':
            path = '/index.html'
        
        # Get the translated path from parent class
        translated_path = super().translate_path(path)
        logger.info(f"Translated path: {translated_path}")
        
        # Check if file exists
        if os.path.exists(translated_path):
            logger.info(f"File exists: {translated_path}")
        else:
            logger.error(f"File not found: {translated_path}")
        
        return translated_path

    def do_GET(self):
        try:
            parsed_path = urlparse(self.path)
            logger.info(f"GET request for path: {parsed_path.path}")
            
            if parsed_path.path == '/messages':
                self.handle_get_messages(parse_qs(parsed_path.query))
            else:
                # For all other paths, try to serve static files
                return super().do_GET()
                
        except Exception as e:
            logger.error(f"Error handling GET request: {str(e)}")
            self.send_error_response(500, f"Internal server error: {str(e)}")

    def do_POST(self):
        try:
            if self.path == '/messages':
                self.handle_post_message()
            else:
                self.send_error(404)
        except Exception as e:
            logger.error(f"Error handling POST request: {str(e)}")
            self.send_error_response(500, f"Internal server error: {str(e)}")

    def handle_get_messages(self, query_params: Dict[str, list]):
        try:
            limit = int(query_params.get('limit', ['100'])[0])
            messages = self.db.get_messages(limit=limit)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            response = {
                "messages": [
                    {
                        "content": msg.content,
                        "author": msg.author,
                        "timestamp": msg.timestamp.isoformat(),
                        "github_url": msg.commit_url,
                        "repository": msg.repository,
                        "id": msg.message_id
                    }
                    for msg in messages
                ]
            }
            
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}")
            self.send_error_response(500, str(e))

    def handle_post_message(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error_response(400, "Empty request body")
                return

            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)

            message = Message(
                content=data['message'],
                author=data.get('author', 'Anonymous'),
                timestamp=datetime.now(),
                repository=data.get('repository', 'local')
            )

            # Store in database
            message_id = self.db.add_message(message)
            message.message_id = str(message_id)

            # Store in GitHub if repository is specified
            github_url = None
            if message.repository != 'local' and self.github_token:
                repo_config = next(
                    (rc for rc in self.repo_configs if f"{rc['owner']}/{rc['name']}" == message.repository),
                    None
                )
                if repo_config:
                    with RepositoryManager(self.github_token) as repo_manager:
                        github_url = repo_manager.store_message(message, repo_config)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response = {
                "status": "success",
                "data": {
                    "content": message.content,
                    "author": message.author,
                    "timestamp": message.timestamp.isoformat(),
                    "github_url": github_url,
                    "repository": message.repository,
                    "id": message.message_id
                }
            }
            
            self.wfile.write(json.dumps(response).encode())

        except KeyError as e:
            logger.error(f"Missing required field: {str(e)}")
            self.send_error_response(400, f"Missing required field: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON format")
            self.send_error_response(400, "Invalid JSON format")
        except Exception as e:
            logger.error(f"Error posting message: {str(e)}")
            self.send_error_response(500, str(e))

    def send_error_response(self, code: int, message: str, details: Optional[Dict[str, Any]] = None):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response = {
            "status": "error",
            "message": message
        }
        if details:
            response["details"] = details
            
        self.wfile.write(json.dumps(response).encode())

def open_browser(port: int):
    """Open browser after a short delay to ensure server is running"""
    def _open_browser():
        webbrowser.open(f'http://localhost:{port}')
    
    browser_thread = threading.Thread(target=_open_browser)
    browser_thread.daemon = True
    browser_thread.start()

def run_server(port: int = 8080):
    try:
        server_address = ('', port)
        httpd = http.server.HTTPServer(server_address, MessageHandler)
        logger.info(f"Server starting on port {port}")
        
        # Open browser in a separate thread
        open_browser(port)
        
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        port = int(os.getenv('SERVER_PORT', 8080))
        run_server(port)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
