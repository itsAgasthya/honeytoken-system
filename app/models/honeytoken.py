from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel

class TokenType(enum.Enum):
    CREDENTIAL = "credential"
    CUSTOMER_RECORD = "customer_record"
    FINANCIAL_DATA = "financial_data"
    SYSTEM_CONFIG = "system_config"

class AccessType(enum.Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"

class Honeytoken(BaseModel):
    """Model for storing honeytoken information."""
    __tablename__ = "honeytokens"

    token_type = Column(Enum(TokenType), nullable=False)
    token_value = Column(Text, nullable=False)
    description = Column(String(255))
    is_active = Column(Integer, default=1)
    token_metadata = Column(JSON)
    
    # Relationships
    access_logs = relationship("HoneytokenAccess", back_populates="honeytoken")

class HoneytokenAccess(BaseModel):
    """Model for logging honeytoken access attempts."""
    __tablename__ = "honeytoken_access_logs"

    token_id = Column(Integer, ForeignKey('honeytokens.id'), nullable=False)
    access_time = Column(DateTime, nullable=False)
    user_id = Column(String(255))
    ip_address = Column(String(45))
    access_type = Column(Enum(AccessType), nullable=False)
    query_text = Column(Text)
    session_data = Column(JSON)
    user_agent = Column(String(255))
    request_headers = Column(JSON)
    
    # Relationships
    honeytoken = relationship("Honeytoken", back_populates="access_logs")

class AlertConfig(BaseModel):
    """Model for storing alert configuration."""
    __tablename__ = "alert_configs"

    token_id = Column(Integer, ForeignKey('honeytokens.id'), nullable=False)
    alert_threshold = Column(Integer, default=1)
    cooldown_period = Column(Integer, default=300)  # seconds
    alert_channels = Column(JSON)  # ['email', 'slack', etc.]
    alert_message_template = Column(Text)
    is_active = Column(Integer, default=1) 