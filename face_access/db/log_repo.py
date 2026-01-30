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
                # Jika status GRANTED, simpan nama terakhir secara lokal agar UI bisa mengaksesnya segera
                if status == 'GRANTED' and self.pegawai_repo is not None:
                    try:
                        emp = self.pegawai_repo.get_by_id(id_pegawai)
                        if emp and emp.get('nama'):
                            self.last_granted_name = emp.get('nama')
                    except Exception:
                        # jangan ganggu alur utama jika gagal
                        pass
            
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

    def get_last_granted_name(self):
        """Return nama pegawai dari entri access_log terakhir yang berstatus GRANTED"""
        conn = self.db.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT l.id_pegawai, p.nama FROM access_log l JOIN pegawai p ON l.id_pegawai = p.id_pegawai "
                "WHERE l.status = 'GRANTED' ORDER BY l.id DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row and row.get('nama'):
                return row.get('nama')
            return None
        except Exception as e:
            Logger.error(f"Error fetching last granted name: {e}")
            return None
        finally:
            cursor.close()