import sys
from .core import CaptureEngine
from .storage.sqlite_handler import StorageHandler


def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "status":
            engine = CaptureEngine()
            engine.get_statistics()
            return
        elif command == "search":
            if len(sys.argv) < 3:
                print("Usage: saver search <query> [limit]")
                return
                
            query = sys.argv[2]
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            
            storage = StorageHandler()
            results = storage.fuzzy_search(query, limit=limit)
            
            print(f"\nFound {len(results)} results for '{query}':\n")
            
            for i, result in enumerate(results, 1):
                print(f"{i}. [{result['app_name']}] Score: {result['relevance_score']:.3f}")
                print(f"   {result['snippet']}")
                print(f"   Created: {result['created_at']}")
                print()
                
            return
        elif command == "rebuild-index":
            storage = StorageHandler()
            storage.rebuild_fts_index()
            return
        elif command == "help":
            print("Saver - App-based text capture system")
            print("Usage:")
            print("  saver           # Start capturing")
            print("  saver status    # Show statistics")
            print("  saver search <query> [limit]  # Search captured content")
            print("  saver rebuild-index  # Rebuild search index")
            print("  saver help      # Show this help")
            return
    
    # Default action: start capturing
    engine = CaptureEngine()
    engine.start()


if __name__ == "__main__":
    main()