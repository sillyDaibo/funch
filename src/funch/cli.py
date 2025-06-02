import argparse
import json
import sys
from typing import Optional
from funch.version import __version__
from funch.llm import LLMClient
from funch.workflow import BasicWorkflow

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
        default="deepseek/deepseek-chat",
        help="LLM model to use (default: deepseek-chat)"
    )
    parser.add_argument(
        "--ask",
        nargs="?",
        const="",
        help="Prompt to send to the LLM (read from stdin if not provided)"
    )
    parser.add_argument(
        "--workflow",
        choices=["basic"],
        default="basic",
        help="Workflow to use when template file is provided (default: basic)"
    )
    parser.add_argument(
        "template_file",
        nargs="?", 
        default=None,
        help="Template file to use with workflow if --ask is not set"
    )
    parser.add_argument(
        "--score-input",
        default=None,
        help="Score input as JSON string (e.g. '5' or '{\"key\":\"value\"}')"
    )
    parser.add_argument(
        "--score-input-file",
        type=argparse.FileType('r'),
        default=None,
        help="File containing Python code returning input value"
    )
    parser.add_argument(
        "--run-tag",
        default=None,
        help="Tag of the function to run (default: first found)"
    )
    
    args = parser.parse_args()
    
    if args.version:
        print(f"funch version {__version__}")
    elif args.ask is not None:
        prompt = args.ask if args.ask else read_stdin_prompt()
        client = LLMClient(model=args.model)
        response = client.invoke(prompt)
        print(response)
    elif args.template_file:
        if args.workflow == "basic":
            score_input = None
            if args.score_input:
                try:
                    score_input = json.loads(args.score_input)
                except json.JSONDecodeError:
                    print("Error: Invalid JSON input")
                    return
            elif args.score_input_file:
                try:
                    namespace = {}
                    exec(args.score_input_file.read(), namespace)
                    score_input = namespace.get('return_value')
                    args.score_input_file.close()
                except Exception as e:
                    print(f"Error loading input file: {e}")
                    return
            
            workflow = BasicWorkflow(
                args.template_file, 
                args.model,
                tag=args.run_tag,
                score_input=score_input
            )
            result, is_valid, score = workflow.generate()
            print(f"Generated function:\n{result}")
            print(f"Validation: {'✅' if is_valid else '❌'}")
            if score is not None:
                print(f"Score: {score}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
