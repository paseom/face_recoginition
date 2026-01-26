import mysql.connector

class Database:
    """MySQL database connection"""
    
    def __init__(self, config):
        self.config = config
        self.conn = None
    
    def connect(self):
        """Connect to database"""
        try:
            self.conn = mysql.connector.connect(**self.config)
            return True
        except mysql.connector.Error as e:
            print(f"Database connection error: {e}")
            return False
    
    def get_connection(self):
        """Get database connection"""
        if self.conn is None or not self.conn.is_connected():
            self.connect()
        return self.conn
    
    def close(self):
        """Close connection"""
        if self.conn is not None and self.conn.is_connected():
            self.conn.close()