import mysql.connector
from utils.logger import Logger

class LogRepository:
    """Repository untuk tabel access_log"""
    
    def __init__(self, database, pegawai_repo=None):
        self.db = database
        self.pegawai_repo = pegawai_repo
    
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
            
            # Get employee info untuk display
            if id_pegawai:
                self._display_log_info(id_pegawai, status)
            
            return cursor.lastrowid
        except mysql.connector.Error as e:
            Logger.error(f"Log error: {e}")
        finally:
            cursor.close()
    
    def _display_log_info(self, id_pegawai, status):
        """Display informasi log dengan nama pegawai"""
        if self.pegawai_repo is None:
            return
        
        try:
            employee = self.pegawai_repo.get_by_id(id_pegawai)
            if employee:
                nama = employee.get('nama', 'Unknown')
                Logger.info(f"Log: ID={id_pegawai}, Nama={nama}, Status={status}")
        except Exception as e:
            Logger.error(f"Error getting employee info: {e}")