from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import create_engine, Column, String, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

SQLALCHEMY_DATABASE_URL = "sqlite:///./nails.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TransactionModel(Base):
    __tablename__ = "transactions"
    id = Column(String, primary_key=True, index=True)
    type = Column(String)
    who = Column(String, nullable=True)
    amt = Column(Float)
    cat = Column(String)
    desc = Column(String, nullable=True)
    date = Column(String)
    seña = Column(Float, default=0.0)
    metodo_pago = Column(String, default="Efectivo")
    client_name = Column(String, default="General")

class DebtModel(Base):
    __tablename__ = "debts"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    total = Column(Float)
    paid = Column(Float, default=0.0)
    min = Column(Float, default=0.0)
    day = Column(Integer, default=0)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mis Cuentas Nails API", version="6.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Transaction(BaseModel):
    id: str
    type: str
    who: Optional[str] = "yo"
    amt: float
    cat: str
    desc: Optional[str] = ""
    date: str
    seña: Optional[float] = 0.0
    metodo_pago: Optional[str] = "Efectivo"
    client_name: Optional[str] = "General"

    class Config:
        from_attributes = True

class Debt(BaseModel):
    id: str
    name: str
    total: float
    paid: float = 0.0
    min: Optional[float] = 0.0
    day: Optional[int] = 0

    class Config:
        from_attributes = True

class DebtUpdate(BaseModel):
    paid: float

# Ruta para servir la página visual (index.html) directamente desde Render
@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Falta el archivo index.html en el repositorio</h1>"

@app.get("/api/transactions", response_model=List[Transaction])
def get_transactions(db: Session = Depends(get_db)):
    return db.query(TransactionModel).all()

@app.post("/api/transactions", response_model=Transaction)
def add_transaction(tx: Transaction, db: Session = Depends(get_db)):
    db_tx = TransactionModel(**tx.dict())
    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)
    return db_tx

@app.delete("/api/transactions/{tx_id}")
def delete_transaction(tx_id: str, db: Session = Depends(get_db)):
    db_tx = db.query(TransactionModel).filter(TransactionModel.id == tx_id).first()
    if not db_tx:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    db.delete(db_tx)
    db.commit()
    return {"status": "success", "message": "Movimiento eliminado con éxito"}

@app.get("/api/debts", response_model=List[Debt])
def get_debts(db: Session = Depends(get_db)):
    return db.query(DebtModel).all()

@app.post("/api/debts", response_model=Debt)
def add_debt(debt: Debt, db: Session = Depends(get_db)):
    db_debt = DebtModel(**debt.dict())
    db.add(db_debt)
    db.commit()
    db.refresh(db_debt)
    return db_debt

@app.delete("/api/debts/{debt_id}")
def delete_debt(debt_id: str, db: Session = Depends(get_db)):
    db_debt = db.query(DebtModel).filter(DebtModel.id == debt_id).first()
    if not db_debt:
        raise HTTPException(status_code=404, detail="Deuda no encontrada")
    db.delete(db_debt)
    db.commit()
    return {"status": "success", "message": "Deuda eliminada con éxito"}

@app.put("/api/debts/{debt_id}", response_model=Debt)
def update_debt(debt_id: str, debt_upd: DebtUpdate, db: Session = Depends(get_db)):
    db_debt = db.query(DebtModel).filter(DebtModel.id == debt_id).first()
    if not db_debt:
        raise HTTPException(status_code=404, detail="Deuda no encontrada")
    db_debt.paid = debt_upd.paid
    db.commit()
    db.refresh(db_debt)
    return db_debt
