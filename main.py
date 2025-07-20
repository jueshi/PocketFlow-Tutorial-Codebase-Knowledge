import dotenv
import sys
import os
import io
import argparse
from pocketflow import Flow
import nodes

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', errors='replace')  
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # Ensure script dir is in sys.path

# Default file patterns
DEFAULT_INCLUDE_PATTERNS = {
    "*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.go", "*.java", "*.pyi", "*.pyx",
    "*.c", "*.cc", "*.cpp", "*.h", "*.md", "*.rst", "Dockerfile",
    "Makefile", "*.yaml", "*.yml",
}

DEFAULT_EXCLUDE_PATTERNS = {
    "venv/*", ".venv/*", "*test*", "tests/*", "docs/*", "examples/*", "v1/*",
    "dist/*", "build/*", "experimental/*", "deprecated/*",
    "legacy/*", ".git/*", ".github/*", ".next/*", ".vscode/*", "obj/*", "bin/*", "node_modules/*", "*.log"
}

def run_flow(args):
    # Load environment variables
    dotenv.load_dotenv()

    # Initialize shared state
    shared = {
        "repo_url": args.repo,
        "directory": args.dir,  # Pass the directory path
        "single_file": args.file,
        "project_name": args.name, # Can be None, FetchRepo will derive it
        "github_token": args.token or os.environ.get('GITHUB_TOKEN'),
        "output_dir": args.output, # Base directory for CombineTutorial output

        # Add include/exclude patterns and max file size
        "include_patterns": set(args.include) if args.include else DEFAULT_INCLUDE_PATTERNS,
        "exclude_patterns": set(args.exclude) if args.exclude else DEFAULT_EXCLUDE_PATTERNS,
        "max_file_size": args.max_size,

        # Add language for multi-language support
        "language": args.language,

        # Outputs will be populated by the nodes
        "files": [],
        "abstractions": [],
        "relationships": {},
        "chapter_order": [],
        "chapters": [],
        "final_output_dir": None
    }

    # Display starting message with repository/directory and language
    print(f"Starting tutorial generation for: {args.repo or args.dir} in {args.language.capitalize()} language")

    # Create the tutorial generation flow
    # Initialize the first node
    start_node = nodes.FetchRepo()
    
    # Connect nodes in sequence
    start_node >> nodes.IdentifyAbstractions() >> nodes.AnalyzeRelationships() >> nodes.OrderChapters() >> nodes.WriteChapters() >> nodes.CombineTutorial()
    
    # Create the flow with the start node
    tutorial_flow = Flow(start=start_node)

    # Run the flow with enhanced error handling
    try:
        tutorial_flow.run(shared)
    except Exception as e:
        import traceback
        from google.genai.errors import ServerError, ClientError

        print(f"An error occurred during tutorial generation: {e}")
        traceback.print_exc()
        shared['error'] = str(e)

    # Print the final state of the shared dictionary for debugging
    if args.debug:
        print("\n--- Final Shared State ---")
        for key, value in shared.items():
            if isinstance(value, (str, int, float, bool)):
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: {type(value).__name__} object")

    # If there was an error, exit with a non-zero status code
    if 'error' in shared:
        print(f"\nTutorial generation failed. See error details above.")
        # The function will return the shared dictionary, so the caller can decide how to handle the exit.

    return shared

def main():
    # Argument parser
    parser = argparse.ArgumentParser(description="Generate a tutorial for a GitHub codebase or local directory.")

    # Create mutually exclusive group for source
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--repo", help="URL of the public GitHub repository.")
    source_group.add_argument("--dir", help="Path to local directory.")
    source_group.add_argument("--file", help="Path to a single input file (e.g., PDF or other document).")
    source_group.add_argument("--url", help="URL to a web page or document.")

    parser.add_argument("-n", "--name", help="Project name (optional, derived from repo/directory if omitted).")
    parser.add_argument("-t", "--token", help="GitHub personal access token (optional, reads from GITHUB_TOKEN env var if not provided).")
    parser.add_argument("-o", "--output", default="output", help="Base directory for output (default: ./output).")
    parser.add_argument("-i", "--include", nargs="+", help="Include file patterns (e.g. '*.py' '*.js'). Defaults to common code files if not specified.")
    parser.add_argument("-e", "--exclude", nargs="+", help="Exclude file patterns (e.g. 'tests/*' 'docs/*'). Defaults to test/build directories if not specified.")
    parser.add_argument("-s", "--max-size", type=int, default=100000, help="Maximum file size in bytes (default: 100000, about 100KB).")
    # Add language parameter for multi-language support
    parser.add_argument("--language", default="english", help="Language for the generated tutorial (default: english)")
    parser.add_argument("--debug", action="store_true", help="Print the final state of the shared dictionary for debugging.")

    args = parser.parse_args()
    run_flow(args)

if __name__ == "__main__":
    main()
