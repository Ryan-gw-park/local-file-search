"""
Local Finder X v2.0 - Main Entry Point

Launches the application with PyQt6 UI.
"""

import sys


def main():
    """Application entry point."""
    print("=" * 50)
    print("Local Finder X v2.0")
    print("Explainable Hybrid Local Search Engine")
    print("=" * 50)
    
    # Try to launch GUI
    try:
        from src.ui.main_window import run_app, PYQT6_AVAILABLE
        
        if PYQT6_AVAILABLE:
            print("\nLaunching UI...")
            sys.exit(run_app())
        else:
            print("\nPyQt6 not installed. Running in CLI mode.")
            print("Install with: pip install PyQt6")
            _run_cli()
    except ImportError as e:
        print(f"\nImport error: {e}")
        print("Running in CLI mode...")
        _run_cli()


def _run_cli():
    """Run in CLI mode (fallback)."""
    print("\n" + "=" * 50)
    print("CLI Mode")
    print("=" * 50)
    
    from src.core.search_engine import SearchEngine, search
    from src.core.indexer import IndexingOrchestrator
    
    print("\nAvailable commands:")
    print("  index <path>  - Index a directory")
    print("  search <query> - Search indexed files")
    print("  quit          - Exit")
    
    engine = SearchEngine()
    orchestrator = IndexingOrchestrator()
    
    while True:
        try:
            cmd = input("\n> ").strip()
            
            if not cmd:
                continue
            
            parts = cmd.split(" ", 1)
            action = parts[0].lower()
            
            if action == "quit" or action == "exit":
                print("Goodbye!")
                break
            
            elif action == "index":
                if len(parts) < 2:
                    print("Usage: index <path>")
                    continue
                path = parts[1]
                print(f"Indexing {path}...")
                result = orchestrator.index_directories([path])
                print(f"Indexed {result.indexed_files} files")
            
            elif action == "search":
                if len(parts) < 2:
                    print("Usage: search <query>")
                    continue
                query = parts[1]
                print(f"Searching: {query}")
                response = search(query)
                print(f"Found {len(response.results)} results in {response.elapsed_ms}ms")
                for hit in response.results[:5]:
                    print(f"  - {hit.file.filename} ({hit.score:.2f})")
            
            else:
                print(f"Unknown command: {action}")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
