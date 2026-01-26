class LogRepository:
    """Repository untuk tabel access_log"""
    
    def __init__(self, database):
        self.db = database
    
    def log_access(self, id_pegawai, status, reason):
        """Log access attempt"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO access_log (id_pegawai, status, reason) VALUES (%s, %s, %s)",
                (id_pegawai, status, reason)
            )
            conn.commit()
            return cursor.lastrowid
        except mysql.connector.Error as e:
            print(f"Log error: {e}")
        finally:
            cursor.close()