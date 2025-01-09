#!/usr/bin/env python3
import argparse
import json
import os
import sys
from typing import Optional, Dict, Any
from dotenv import load_dotenv, set_key, unset_key

def load_env() -> Dict[str, str]:
    load_dotenv()
    return dict(os.environ)

def validate_json(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        raise argparse.ArgumentTypeError(f"Invalid JSON: {str(e)}")

def format_value(value: str) -> str:
    try:
        # Try to parse as JSON for pretty printing
        parsed = json.loads(value)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError:
        return value

def handle_env_list(args: argparse.Namespace) -> None:
    env_vars = load_env()
    for key, value in env_vars.items():
        print(f"{key}={format_value(value)}")

def handle_env_get(args: argparse.Namespace) -> None:
    env_vars = load_env()
    value = env_vars.get(args.key)
    if value is None:
        print(f"Environment variable '{args.key}' not found")
        sys.exit(1)
    print(format_value(value))

def handle_env_set(args: argparse.Namespace) -> None:
    if args.key == "GITHUB_REPOSITORIES":
        # Validate repository configuration
        try:
            repos = json.loads(args.value)
            for repo in repos:
                required = ["owner", "name"]
                missing = [field for field in required if field not in repo]
                if missing:
                    raise ValueError(f"Missing required fields: {', '.join(missing)}")
        except json.JSONDecodeError:
            print("Error: GITHUB_REPOSITORIES must be a valid JSON array")
            sys.exit(1)
        except ValueError as e:
            print(f"Error: {str(e)}")
            sys.exit(1)

    set_key(".env", args.key, args.value)
    print(f"Set {args.key}={format_value(args.value)}")

def handle_env_delete(args: argparse.Namespace) -> None:
    unset_key(".env", args.key)
    print(f"Deleted {args.key}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Message Board CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # env command
    env_parser = subparsers.add_parser("env", help="Manage environment variables")
    env_subparsers = env_parser.add_subparsers(dest="env_command", help="Environment commands")

    # env list
    env_list_parser = env_subparsers.add_parser("list", help="List all environment variables")

    # env get
    env_get_parser = env_subparsers.add_parser("get", help="Get an environment variable")
    env_get_parser.add_argument("key", help="Environment variable name")

    # env set
    env_set_parser = env_subparsers.add_parser("set", help="Set an environment variable")
    env_set_parser.add_argument("key", help="Environment variable name")
    env_set_parser.add_argument("value", help="Environment variable value")

    # env delete
    env_delete_parser = env_subparsers.add_parser("delete", help="Delete an environment variable")
    env_delete_parser.add_argument("key", help="Environment variable name")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "env":
        if args.env_command == "list":
            handle_env_list(args)
        elif args.env_command == "get":
            handle_env_get(args)
        elif args.env_command == "set":
            handle_env_set(args)
        elif args.env_command == "delete":
            handle_env_delete(args)
        else:
            env_parser.print_help()
            sys.exit(1)

if __name__ == "__main__":
    main()
