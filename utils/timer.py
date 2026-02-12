import time

class Timer:
    """Timer untuk real-time constraint"""
    
    def __init__(self, timeout):
        self.timeout = timeout
        self.start_time = None
    
    def start(self):
        """Start timer"""
        self.start_time = time.time()
    
    def elapsed(self):
        """Get elapsed time"""
        if self.start_time is None:
            return 0
        return time.time() - self.start_time
    
    def is_timeout(self):
        """Check if timeout reached"""
        return self.elapsed() >= self.timeout
    
    def remaining(self):
        """Get remaining time"""
        return max(0, self.timeout - self.elapsed())