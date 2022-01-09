from typing import Tuple

from attrdict import AttrDict
from hydra import log
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import lazyload
import random

from hybot.data.base import *

__all__ = "UserPkid",


@dictattrs("pkid", "name")
class UserPkid(DbPkidMixin, Base):
    __tablename__ = "user_pkid"

    name = Column(String, default=lambda: UserPkid.make_name(), nullable=False, unique=True, index=True)

    @staticmethod
    def make_name():
        return str(random.random())  # TODO: (Placeholder)


class DbUserPkidMixin:

    pkid = lambda: Column(Integer, ForeignKey("user_pkid.pkid"), nullable=False, unique=True, primary_key=True, index=True)
    name = lambda: Column(String, ForeignKey("user_pkid.name"), nullable=False, unique=True, primary_key=True, index=True)
