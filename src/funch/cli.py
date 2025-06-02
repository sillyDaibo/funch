import argparse
import sys
from typing import Optional
from funch.version import __version__
from funch.llm import LLMClient

def read_stdin_prompt() -> str:
    """Read prompt from stdin with user hint."""
    print("Enter your prompt (Ctrl+D to finish):")
    try:
        return "\n".join(line for line in sys.stdin)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="funch command line interface")
    parser.add_argument(
        "-v", "--version", 
        action="store_true",
        help="Show package version"
    )
    parser.add_argument(
        "-m", "--model",
        default="deepseek-chat",
        help="LLM model to use (default: deepseek-chat)"
    )
    parser.add_argument(
        "--ask",
        nargs="?",
        const="",
        help="Prompt to send to the LLM (read from stdin if not provided)"
    )
    
    args = parser.parse_args()
    
    if args.version:
        print(f"funch version {__version__}")
    elif args.ask is not None:
        prompt = args.ask if args.ask else read_stdin_prompt()
        client = LLMClient(model=args.model)
        response = client.invoke(prompt)
        print(response)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
