import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    try:
        conn = psycopg2.connect(
            host="db",
            database="testdb",
            user="postgres",
            password="postgres"
        )
        cur = conn.cursor()
        
        # Scenarios tablosunu oluştur
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scenarios (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                content TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                status VARCHAR(50) NOT NULL
            )
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info("Tablolar başarıyla oluşturuldu")
    except Exception as e:
        logger.error(f"Tablo oluşturulurken hata: {str(e)}")
        raise e

if __name__ == "__main__":
    create_tables() 