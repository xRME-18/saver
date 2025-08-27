import sys
from .core import CaptureEngine
from .storage.sqlite_handler import StorageHandler


def interactive_search():
    """Interactive search console"""
    storage = StorageHandler()
    
    print("🔍 Saver Interactive Search Console")
    print("Commands:")
    print("  <search query>     - Search your captures")
    print("  :limit <number>    - Set result limit (default: 10)")
    print("  :app <name>        - Filter by app name")
    print("  :clear             - Clear filters")
    print("  :stats             - Show database statistics")
    print("  :recent [limit]    - Show recent captures")
    print("  :help              - Show this help")
    print("  :quit              - Exit console")
    print("=" * 60)
    
    limit = 10
    app_filter = None
    
    while True:
        try:
            # Show current filters
            filter_info = []
            if limit != 10:
                filter_info.append(f"limit={limit}")
            if app_filter:
                filter_info.append(f"app={app_filter}")
            
            prompt = "search"
            if filter_info:
                prompt += f" ({', '.join(filter_info)})"
            prompt += "> "
            
            query = input(prompt).strip()
            
            if not query:
                continue
                
            # Handle commands
            if query.startswith(':'):
                command_parts = query[1:].split()
                command = command_parts[0].lower()
                
                if command == "quit" or command == "exit":
                    print("👋 Goodbye!")
                    break
                elif command == "help":
                    print("\nCommands:")
                    print("  <search query>     - Search your captures")
                    print("  :limit <number>    - Set result limit (default: 10)")
                    print("  :app <name>        - Filter by app name")
                    print("  :clear             - Clear filters")
                    print("  :stats             - Show database statistics")
                    print("  :recent [limit]    - Show recent captures")
                    print("  :help              - Show this help")
                    print("  :quit              - Exit console")
                elif command == "limit":
                    if len(command_parts) > 1:
                        try:
                            limit = int(command_parts[1])
                            print(f"✓ Result limit set to {limit}")
                        except ValueError:
                            print("❌ Invalid number format")
                    else:
                        print(f"Current limit: {limit}")
                elif command == "app":
                    if len(command_parts) > 1:
                        app_filter = command_parts[1]
                        print(f"✓ Filtering by app: {app_filter}")
                    else:
                        if app_filter:
                            print(f"Current app filter: {app_filter}")
                        else:
                            print("No app filter set")
                elif command == "clear":
                    limit = 10
                    app_filter = None
                    print("✓ Filters cleared")
                elif command == "stats":
                    stats = storage.get_statistics()
                    print(f"\n📊 Database Statistics:")
                    print(f"   Total captures: {stats.get('total_captures', 0)}")
                    print(f"   Unique apps: {stats.get('unique_apps', 0)}")
                    print(f"   Total characters: {stats.get('total_characters', 0):,}")
                    print(f"   Total words: {stats.get('total_words', 0):,}")
                    if stats.get('top_apps'):
                        print(f"   Top apps:")
                        for app in stats['top_apps'][:3]:
                            print(f"     - {app['app']}: {app['captures']} captures")
                elif command == "recent":
                    recent_limit = 5
                    if len(command_parts) > 1:
                        try:
                            recent_limit = int(command_parts[1])
                        except ValueError:
                            print("❌ Invalid number format, using default (5)")
                    
                    recent = storage.get_recent_captures(recent_limit)
                    print(f"\n📋 {len(recent)} Most Recent Captures:")
                    for i, capture in enumerate(recent, 1):
                        content_preview = capture['content'][:80]
                        if len(capture['content']) > 80:
                            content_preview += "..."
                        print(f"   {i}. [{capture['app_name']}] {content_preview}")
                        print(f"      {capture['created_at']}")
                else:
                    print(f"❌ Unknown command: {command}")
                
                print()  # Add spacing after command output
                continue
            
            # Regular search
            print(f"\n🔍 Searching for: '{query}'...")
            results = storage.fuzzy_search(query, limit=limit, app_filter=app_filter)
            
            if not results:
                print(f"❌ No results found for '{query}'")
                # Suggest alternatives
                if app_filter:
                    print(f"💡 Try removing the app filter (:clear) or search different terms")
                else:
                    print(f"💡 Try different search terms or check :recent to see available content")
            else:
                print(f"✅ Found {len(results)} results:")
                print("-" * 60)
                
                for i, result in enumerate(results, 1):
                    # Highlight the app name and score
                    app_color = "🟢" if result['relevance_score'] > 0.8 else "🟡" if result['relevance_score'] > 0.5 else "🟠"
                    print(f"{i:2d}. {app_color} [{result['app_name']}] Score: {result['relevance_score']:.3f}")
                    
                    # Show snippet with better formatting
                    snippet = result['snippet'].replace('\n', ' ').strip()
                    print(f"     {snippet}")
                    
                    # Show creation time in a more readable format
                    created_at = result['created_at']
                    if 'T' in created_at:
                        date_part, time_part = created_at.split('T')
                        time_part = time_part.split('.')[0]  # Remove microseconds
                        print(f"     📅 {date_part} ⏰ {time_part}")
                    else:
                        print(f"     📅 {created_at}")
                    
                    print()  # Add spacing between results
            
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


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
        elif command == "console" or command == "interactive":
            interactive_search()
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
            print("  saver console   # Interactive search console")
            print("  saver rebuild-index  # Rebuild search index")
            print("  saver help      # Show this help")
            return
    
    # Default action: start capturing
    engine = CaptureEngine()
    engine.start()


if __name__ == "__main__":
    main()