from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from pydantic import BaseModel
from typing import List, Optional

# --- 1. Konfigurasi SQLAlchemy (SQLite) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./items.db"
# Untuk SQLite, check_same_thread=False diperlukan jika menggunakan FastAPI dependencies
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. Model Database SQLAlchemy ---
class ItemDB(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True, nullable=True)

# Membuat tabel di database (jika belum ada)
Base.metadata.create_all(bind=engine)

# --- 3. Model Validasi Pydantic (Output) ---
class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True  # Untuk kompatibilitas Pydantic v2 dengan SQLAlchemy (sebelumnya orm_mode = True)

# --- 4. Aplikasi FastAPI ---
app = FastAPI(
    title="Simple Items API",
    description="Implementasi GET /items/ dan GET /items/{id} menggunakan FastAPI dan SQLAlchemy",
    version="1.0.0"
)

# Dependency untuk mendapatkan session database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Fungsi Seed Database (Opsional: Agar ada data awal saat testing) ---
def seed_data():
    db = SessionLocal()
    if db.query(ItemDB).count() == 0:
        initial_items = [
            ItemDB(name="Laptop", description="Laptop gaming asus"),
            ItemDB(name="Mouse", description="Mouse wireless logitech"),
            ItemDB(name="Keyboard", description="Mechanical keyboard"),
        ]
        db.add_all(initial_items)
        db.commit()
    db.close()

# Jalankan seeder
seed_data()

# --- 5. Implementasi Endpoints ---

@app.get("/items/", response_model=List[Item])
def get_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    Mengambil semua data item.
    """
    items = db.query(ItemDB).offset(skip).limit(limit).all()
    return items

@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int, db: Session = Depends(get_db)):
    """
    Mengambil data item berdasarkan ID.
    """
    item = db.query(ItemDB).filter(ItemDB.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")
    return item
