# scripts/init_db.py
from backend.database import engine, Base

def init_db():
    Base.metadata.create_all(bind=engine)
    print("✔️  Tablas creadas en la BD.")

if __name__ == "__main__":
    init_db()
