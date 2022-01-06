from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import func
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import relationship
from sqlalchemy_json import NestedMutableJson

from hybot.data.base import Base

__all__ = "UserAddr",


class UserAddr(Base):
    __tablename__ = "user_addr"

    user_id = Column(Integer, ForeignKey("user.user_id", ondelete="CASCADE"), primary_key=True, index=True, nullable=False)
    addr_id = Column(Integer, ForeignKey("addr.addr_id", ondelete="CASCADE"), primary_key=True, index=True, nullable=False)
    tokens = relationship("Token", secondary="user_addr_token", back_populates="user_addrs", cascade="all, delete")
    date_create = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    date_change = Column(DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False, index=True)
    conf = Column(NestedMutableJson, nullable=False, index=True, default={})
    data = Column(NestedMutableJson, nullable=False, index=False, default={})
