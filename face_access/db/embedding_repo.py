import pickle

class EmbeddingRepository:
    """Repository untuk tabel face_embedding"""
    
    def __init__(self, database):
        self.db = database
    
    def save(self, id_pegawai, embedding):
        """Save embedding"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            embedding_blob = pickle.dumps(embedding)
            cursor.execute(
                "INSERT INTO face_embedding (id_pegawai, embedding_vector) VALUES (%s, %s)",
                (id_pegawai, embedding_blob)
            )
            conn.commit()
            return cursor.lastrowid
        except mysql.connector.Error as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def get_all(self):
        """Get all embeddings"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id_pegawai, embedding_vector FROM face_embedding")
            results = cursor.fetchall()
            
            embeddings = []
            for id_pegawai, embedding_blob in results:
                embedding = pickle.loads(embedding_blob)
                embeddings.append((id_pegawai, embedding))
            
            return embeddings
        finally:
            cursor.close()