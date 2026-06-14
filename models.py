from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import datetime
import uuid

Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    merchant = Column(String, nullable=False)
    city = Column(String, nullable=False)
    category = Column(String, nullable=False)
    device_type = Column(String, nullable=True, default="WEB")
    ip_address = Column(String, nullable=True, default="0.0.0.0")
    
    alerts = relationship("Alert", back_populates="transaction")

class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String, ForeignKey('transactions.id'), nullable=False, index=True)
    risk_score = Column(Integer, nullable=False)
    flagged_rules = Column(String, nullable=False) # JSON array stored via json.dumps()
    ai_insight = Column(String, nullable=True)     # To be populated by Gemini async
    status = Column(String, nullable=False, default="PENDING")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    transaction = relationship("Transaction", back_populates="alerts")

# Connection setup suitable for 4GB RAM requirement (lightweight)
SQLALCHEMY_DATABASE_URL = "sqlite:///./fraudshield.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
