import signal
import sys
import time
import threading
from datetime import datetime
from typing import Optional

from ..monitors.key_listener import KeyListener
from ..monitors.app_monitor import AppMonitor
from .buffer_manager import BufferManager
from ..storage.sqlite_handler import StorageHandler
from .config import Config


class CaptureEngine:
    """Core capture engine that coordinates all components"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = Config(config_path)
        self.buffer_manager = BufferManager()
        self.storage_handler = StorageHandler(self.config.get_database_path())
        self.key_listener = KeyListener(self._on_key_press)
        self.app_monitor = AppMonitor(self._on_app_change)
        
        self.running = False
        self.save_timer: Optional[threading.Timer] = None
        
        # Register signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        print("\nShutting down gracefully...")
        self.stop()
        sys.exit(0)
        
    def _on_key_press(self, char: str):
        current_app = self.app_monitor.get_current_app()
        
        if current_app and self.config.should_capture_app(current_app):
            self.buffer_manager.add_text(current_app, char)
            
    def _on_app_change(self, new_app: str):
        should_capture = self.config.should_capture_app(new_app)
        print(f"App changed to: {new_app} (capturing: {should_capture})")
        
    def _save_buffers(self):
        if not self.running:
            return
            
        print("Saving buffers...")
        captures = self.buffer_manager.flush_all_buffers()
        
        # Filter out captures that are too short
        min_chars = self.config.get_min_chars_threshold()
        filtered_captures = {
            app: capture for app, capture in captures.items()
            if len(capture["content"].strip()) >= min_chars
        }
        
        if filtered_captures:
            saved_count = self.storage_handler.save_multiple_captures(filtered_captures)
            print(f"Saved {saved_count} captures")
            
        # Schedule next save
        if self.running:
            interval = self.config.get_save_interval()
            self.save_timer = threading.Timer(interval, self._save_buffers)
            self.save_timer.daemon = True
            self.save_timer.start()
            
    def start(self):
        if not self.config.is_capture_enabled():
            print("Capture is disabled in config")
            return
            
        print("Starting Saver...")
        print("Press Ctrl+C to stop")
        
        self.running = True
        
        # Start monitoring active application
        self.app_monitor.start()
        
        # Start key listener
        self.key_listener.start()
        
        # Start periodic save timer
        interval = self.config.get_save_interval()
        self.save_timer = threading.Timer(interval, self._save_buffers)
        self.save_timer.daemon = True
        self.save_timer.start()
        
        print(f"Saver started! Saving every {interval} seconds")
        
        try:
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
            
    def stop(self):
        if not self.running:
            return
            
        print("Stopping Saver...")
        self.running = False
        
        # Cancel the save timer
        if self.save_timer:
            self.save_timer.cancel()
            
        # Stop components
        self.key_listener.stop()
        self.app_monitor.stop()
        
        # Final save
        print("Performing final save...")
        captures = self.buffer_manager.flush_all_buffers()
        if captures:
            saved_count = self.storage_handler.save_multiple_captures(captures)
            print(f"Final save completed: {saved_count} captures")
            
            # Show what was captured in each app
            print("\n=== Captured Content by App ===")
            for app_name, capture_info in captures.items():
                content_preview = capture_info["content"][:100] + "..." if len(capture_info["content"]) > 100 else capture_info["content"]
                print(f"\n{app_name}:")
                print(f"  Characters: {capture_info['char_count']}")
                print(f"  Words: {capture_info['word_count']}")
                print(f"  Content: {repr(content_preview)}")
        else:
            print("No new content to save")
            
        print("Saver stopped")
        
    def get_statistics(self):
        stats = self.storage_handler.get_statistics()
        current_buffers = self.buffer_manager.get_all_apps()
        
        print("\n=== Saver Status ===")
        print(f"Total captures: {stats.get('total_captures', 0)}")
        print(f"Unique apps: {stats.get('unique_apps', 0)}")
        print(f"Total characters: {stats.get('total_characters', 0):,}")
        print(f"Total words: {stats.get('total_words', 0):,}")
        print(f"Active buffers: {len(current_buffers)}")
        
        if stats.get('top_apps'):
            print("\nTop apps by capture count:")
            for app_info in stats['top_apps']:
                print(f"  {app_info['app']}: {app_info['captures']} captures")
                
        if current_buffers:
            print(f"\nActive apps with buffers: {', '.join(current_buffers)}")