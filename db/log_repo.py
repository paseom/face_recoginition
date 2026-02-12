import mysql.connector
from utils.logger import Logger

class LogRepository:
    """Repository untuk tabel access_log"""

    def __init__(self, database, pegawai_repo=None):
        self.db = database
        self.pegawai_repo = pegawai_repo
        self._crowd_log_schema = None

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

    def _get_crowd_log_schema(self, cursor):
        """Cache crowd_log columns and nullability to support schema variants."""
        if self._crowd_log_schema is not None:
            return self._crowd_log_schema

        cursor.execute("SHOW COLUMNS FROM crowd_log")
        rows = cursor.fetchall()

        schema = {}
        for row in rows:
            # SHOW COLUMNS returns: Field, Type, Null, Key, Default, Extra
            field_name = row[0]
            allow_null = (str(row[2]).upper() == 'YES')
            schema[field_name] = allow_null

        self._crowd_log_schema = schema
        return schema

    def log_crowd_detection(self, id_pegawai, nama, nip, source_type):
        """Simpan log hasil crowd detection ke tabel crowd_log (compatible dengan variasi schema)."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        source_type = (source_type or "VIDEO").upper()
        if source_type not in ("IMAGE", "VIDEO", "WEBCAM"):
            source_type = "VIDEO"

        try:
            schema = self._get_crowd_log_schema(cursor)

            payload = {
                'id_pegawai': id_pegawai,
                'nama': nama,
                'nip': nip,
                'source_type': source_type
            }

            # Fill placeholders for columns that do not allow NULL.
            if 'nama' in schema and payload['nama'] is None and not schema['nama']:
                payload['nama'] = 'UNKNOWN'
            if 'nip' in schema and payload['nip'] is None and not schema['nip']:
                payload['nip'] = '-'
            if 'source_type' in schema and payload['source_type'] is None and not schema['source_type']:
                payload['source_type'] = 'VIDEO'

            columns = [col for col in ('id_pegawai', 'nama', 'nip', 'source_type') if col in schema]
            if not columns:
                Logger.error("Crowd log error: crowd_log tidak punya kolom yang didukung")
                return None

            values = [payload[col] for col in columns]
            placeholders = ', '.join(['%s'] * len(columns))
            sql = f"INSERT INTO crowd_log ({', '.join(columns)}) VALUES ({placeholders})"

            cursor.execute(sql, values)
            conn.commit()
            return cursor.lastrowid
        except mysql.connector.Error as e:
            Logger.error(f"Crowd log error: {e}")
            return None
        finally:
            cursor.close()
