# Git-Backed Message Board

A web-based messaging application that stores messages both locally in SQLite and remotely in GitHub repositories.

## Features

- Store and retrieve messages from both local SQLite database and GitHub repositories
- Clean, modern web interface with auto-refresh
- Command-line interface for environment management
- Support for multiple GitHub repositories
- Real-time message updates
- Responsive design

## Requirements

- Python 3.7+
- Required Python packages (see requirements.txt)
- GitHub Personal Access Token with repo scope

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pomchat.git
cd pomchat
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Using the CLI tool
./src/cli.py env set GITHUB_TOKEN your_token_here
./src/cli.py env set GITHUB_REPOSITORIES '[{"owner": "username", "name": "repo", "branch": "main"}]'
./src/cli.py env set SERVER_PORT 8000
```

## Usage

### Starting the Server

```bash
python src/server.py
```

The server will start on http://localhost:8000 (or the port specified in SERVER_PORT).

### Using the Web Interface

1. Open http://localhost:8000 in your browser
2. Enter your message in the form
3. Optionally specify:
   - Author name (defaults to "Anonymous")
   - Target repository (defaults to local storage)
4. Click Submit to post your message

Messages will automatically refresh every 30 seconds.

### Using the CLI

The CLI tool provides commands for managing environment variables:

```bash
# List all environment variables
./src/cli.py env list

# Get a specific variable
./src/cli.py env get GITHUB_TOKEN

# Set a variable
./src/cli.py env set GITHUB_TOKEN your_token_here
./src/cli.py env set GITHUB_REPOSITORIES '[{"owner": "user", "name": "repo"}]'

# Delete a variable
./src/cli.py env delete OLD_VAR
```

## Project Structure

```
project/
├── src/
│   ├── server.py           # Main HTTP server
│   ├── db.py              # Database operations
│   ├── repository_manager.py   # GitHub operations
│   └── cli.py             # Command-line interface
├── static/
│   ├── index.html         # Web interface
│   └── js/
│       └── messages.js    # Message handling logic
├── .env                  # Environment variables
└── requirements.txt     # Python dependencies
```

## Environment Variables

- `GITHUB_TOKEN`: Your GitHub Personal Access Token
- `SERVER_PORT`: Port for the web server (default: 8000)
- `GITHUB_REPOSITORIES`: JSON array of repository configurations:
  ```json
  [
    {
      "owner": "username",
      "name": "repository",
      "branch": "main",
      "message_path": "messages"
    }
  ]
  ```
