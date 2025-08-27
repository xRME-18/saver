import sys
from .core import CaptureEngine


def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "status":
            engine = CaptureEngine()
            engine.get_statistics()
            return
        elif command == "help":
            print("Saver - App-based text capture system")
            print("Usage:")
            print("  saver         # Start capturing")
            print("  saver status  # Show statistics")
            print("  saver help    # Show this help")
            return
    
    # Default action: start capturing
    engine = CaptureEngine()
    engine.start()


if __name__ == "__main__":
    main()