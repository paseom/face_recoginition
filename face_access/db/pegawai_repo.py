import mysql
class PegawaiRepository:
    """Repository untuk tabel pegawai"""
    
    def __init__(self, database):
        self.db = database
    
    def create(self, nama, nip):
        """Insert pegawai baru"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO pegawai (nama, nip) VALUES (%s, %s)",
                (nama, nip)
            )
            conn.commit()
            return cursor.lastrowid
        except mysql.connector.Error as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def get_by_id(self, id_pegawai):
        """Get pegawai by ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute(
                "SELECT * FROM pegawai WHERE id_pegawai = %s",
                (id_pegawai,)
            )
            return cursor.fetchone()
        finally:
            cursor.close()