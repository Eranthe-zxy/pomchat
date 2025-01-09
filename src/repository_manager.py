import aiohttp
import json
from typing import List, Dict, Optional
from datetime import datetime
from db import Message

class RepositoryManager:
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_messages(self, repo_config: Dict[str, str]) -> List[Message]:
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)

        try:
            # Get the tree
            tree_url = f"https://api.github.com/repos/{repo_config['owner']}/{repo_config['name']}/git/trees/{repo_config['branch']}?recursive=1"
            async with self.session.get(tree_url) as response:
                if response.status == 404:
                    return []
                response.raise_for_status()
                tree = await response.json()

            messages = []
            message_path = repo_config.get('message_path', 'messages')
            
            for item in tree['tree']:
                if not item['path'].startswith(message_path):
                    continue
                if not item['path'].endswith('.json'):
                    continue

                # Get the blob content
                blob_url = f"https://api.github.com/repos/{repo_config['owner']}/{repo_config['name']}/git/blobs/{item['sha']}"
                async with self.session.get(blob_url) as response:
                    response.raise_for_status()
                    blob = await response.json()
                    content = json.loads(blob['content'])
                    
                    messages.append(Message(
                        content=content['content'],
                        author=content.get('author', 'Anonymous'),
                        timestamp=datetime.fromisoformat(content['timestamp']),
                        repository=f"{repo_config['owner']}/{repo_config['name']}",
                        commit_url=content.get('github_url')
                    ))

            return messages

        except aiohttp.ClientError as e:
            # Log the error and return empty list
            print(f"Error fetching messages from GitHub: {str(e)}")
            return []

    async def store_message(self, message: Message, repo_config: Dict[str, str]) -> Optional[str]:
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)

        try:
            message_data = {
                "content": message.content,
                "author": message.author,
                "timestamp": message.timestamp.isoformat(),
                "repository": message.repository
            }

            # Create file path
            timestamp = message.timestamp.strftime("%Y%m%d%H%M%S")
            file_path = f"{repo_config.get('message_path', 'messages')}/{timestamp}.json"
            
            # Convert content to base64
            content = json.dumps(message_data, indent=2)
            
            # Create or update file
            url = f"https://api.github.com/repos/{repo_config['owner']}/{repo_config['name']}/contents/{file_path}"
            data = {
                "message": f"Add message from {message.author}",
                "content": content,
                "branch": repo_config['branch']
            }

            async with self.session.put(url, json=data) as response:
                response.raise_for_status()
                result = await response.json()
                return result['content']['html_url']

        except aiohttp.ClientError as e:
            print(f"Error storing message to GitHub: {str(e)}")
            return None
