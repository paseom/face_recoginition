from datetime import datetime

class Logger:
    """Helper untuk logging"""
    
    @staticmethod
    def info(message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] INFO: {message}")
    
    @staticmethod
    def warning(message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] WARNING: {message}")
    
    @staticmethod
    def error(message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ERROR: {message}")
    
    @staticmethod
    def success(message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] SUCCESS: {message}")