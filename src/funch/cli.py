import argparse
from funch.version import __version__

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="funch command line interface")
    parser.add_argument(
        "-v", "--version", 
        action="store_true",
        help="Show package version"
    )
    
    args = parser.parse_args()
    
    if args.version:
        print(f"funch version {__version__}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
