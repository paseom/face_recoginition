import os
import pickle
import uuid

class EmbeddingRepository:
    """Repository untuk tabel face_embedding"""
    
    def __init__(self, database):
        self.db = database
        # folder to store embedding files
        self.storage_dir = os.path.join(os.path.dirname(__file__), "..", "embeddings")
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def save(self, id_pegawai, embedding):
        """Save embedding to file and store path in DB"""
        # prepare file path
        filename = f"{id_pegawai}_{uuid.uuid4().hex}.pkl"
        filepath = os.path.abspath(os.path.join(self.storage_dir, filename))

        # write embedding to file
        with open(filepath, "wb") as f:
            pickle.dump(embedding, f)

        # store the file path in the database
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO face_embedding (id_pegawai, embedding_vector) VALUES (%s, %s)",
                (id_pegawai, filepath)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            # if DB write failed, remove the saved file to avoid orphan files
            try:
                os.remove(filepath)
            except Exception:
                pass
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
                embedding = None
                # If DB contains a path (string), load from file
                if isinstance(embedding_blob, str):
                    path = embedding_blob
                    try:
                        with open(path, "rb") as f:
                            embedding = pickle.load(f)
                    except Exception:
                        embedding = None
                else:
                    # try to unpickle raw blob (backwards compatibility)
                    try:
                        embedding = pickle.loads(embedding_blob)
                    except Exception:
                        # if it's bytes representing a path, decode and try file
                        try:
                            path = embedding_blob.decode("utf-8")
                            with open(path, "rb") as f:
                                embedding = pickle.load(f)
                        except Exception:
                            embedding = None

                embeddings.append((id_pegawai, embedding))
            
            return embeddings
        finally:
            cursor.close()