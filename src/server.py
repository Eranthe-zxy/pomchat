import http.server
import json
import os
import datetime
import logging
import uuid
from typing import Optional, Dict, Any
from urllib.parse import parse_qs, urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In-memory storage for messages
messages = []

class MessageHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Set up static file serving
        static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
        super().__init__(*args, directory=static_dir, **kwargs)

    def do_GET(self):
        try:
            if self.path.startswith('/messages'):
                self.handle_get_messages()
            else:
                super().do_GET()
        except Exception as e:
            logger.error(f"Error handling GET request: {str(e)}")
            self.send_error_response(500, str(e))

    def do_POST(self):
        try:
            if self.path == '/messages':
                self.handle_post_message()
            elif self.path.startswith('/messages/') and self.path.endswith('/reactions'):
                self.handle_post_reaction()
            else:
                self.send_error_response(404, "Invalid endpoint")
        except Exception as e:
            logger.error(f"Error handling POST request: {str(e)}")
            self.send_error_response(500, str(e))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def handle_get_messages(self):
        try:
            # Get the most recent messages
            recent_messages = messages[-100:] if messages else []

            self.send_json_response({
                "status": "success",
                "messages": recent_messages
            })
        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}")
            self.send_error_response(500, str(e))

    def handle_post_message(self):
        try:
            data = self.get_json_body()
            if not data:
                return

            message_text = data.get('message', '').strip()
            if not message_text:
                self.send_error_response(400, "Message cannot be empty")
                return

            # Create new message
            message = {
                'id': str(uuid.uuid4()),
                'content': message_text,
                'author': data.get('author', 'Anonymous').strip() or 'Anonymous',
                'timestamp': datetime.datetime.now().isoformat(),
                'repository': data.get('repository', 'local').strip() or 'local',
                'github_url': None,
                'reactions': {}
            }

            messages.append(message)
            self.send_json_response({
                "status": "success",
                "messages": [message]
            })
        except Exception as e:
            logger.error(f"Error posting message: {str(e)}")
            self.send_error_response(500, str(e))

    def handle_post_reaction(self):
        try:
            # Get message ID from path
            parts = self.path.split('/')
            if len(parts) < 3:
                self.send_error_response(400, "Invalid message ID")
                return
            
            message_id = parts[2]
            data = self.get_json_body()
            if not data:
                return

            reaction = data.get('reaction')
            if not reaction:
                self.send_error_response(400, "Reaction type required")
                return

            # Find message
            message = next((m for m in messages if m['id'] == message_id), None)
            if not message:
                self.send_error_response(404, "Message not found")
                return

            # Update reaction count
            if 'reactions' not in message:
                message['reactions'] = {}
            
            current_count = message['reactions'].get(reaction, 0)
            message['reactions'][reaction] = current_count + 1

            self.send_json_response({
                "status": "success",
                "data": {
                    "count": message['reactions'][reaction]
                }
            })
        except Exception as e:
            logger.error(f"Error handling reaction: {str(e)}")
            self.send_error_response(500, str(e))

    def get_json_body(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error_response(400, "Empty request body")
                return None

            post_data = self.rfile.read(content_length)
            return json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError:
            self.send_error_response(400, "Invalid JSON")
            return None
        except Exception as e:
            self.send_error_response(500, str(e))
            return None

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_error_response(self, code: int, message: str):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "error",
            "message": message
        }).encode())

def run(port=8080):
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, MessageHandler)
    logger.info(f"Starting server on port {port}")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
