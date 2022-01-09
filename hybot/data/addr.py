from __future__ import annotations
import enum
from typing import Optional, Tuple
import binascii

from attrdict import AttrDict
from hydra.rpc.hydra_rpc import HydraRPC, BaseRPC
from sqlalchemy import Column, String, Enum, BigInteger
from sqlalchemy.orm import relationship

from .base import *

__all__ = "Addr",


@dictattrs("pkid", "addr_tp", "addr_hx", "addr_hy", "date_create", "date_update", "info", "data", "users")
class Addr(DbPkidMixin, DbDateMixin, Base):
    __tablename__ = "addr"

    class Type(enum.Enum):
        H = "HYDRA"
        S = "smart contract"
        T = "token"

        @staticmethod
        def by_len(address: str) -> Optional[Addr.Type]:
            length = len(address)

            return (
                Addr.Type.H if length == 34 else
                Addr.Type.S if length == 40 else
                None
            )

    addr_tp = Column(Enum(Type, validate_strings=True), nullable=False, index=True)
    addr_hx = Column(String(40), nullable=False, unique=True, index=True)
    addr_hy = Column(String(34), nullable=False, unique=True, index=True)

    info = DbInfoColumn()
    data = DbDataColumn()

    users = relationship("User", secondary="user_addr", back_populates="addrs", passive_deletes=True)

    @staticmethod
    async def validate_address(db, address: str):
        return await type(db).run_in_executor(Addr._validate_address, db, address)

    @staticmethod
    def _validate_address(db, address: str):
        return db.rpc.validateaddress(address)

    @staticmethod
    async def addr_normalize(db, address: str) -> Tuple[Addr.Type, str, str]:
        return await type(db).run_in_executor(Addr._addr_normalize, db, address)

    @staticmethod
    def _addr_normalize(db, address: str) -> Tuple[Addr.Type, str, str]:
        """Normalize an input address into a tuple of (Addr.Type, addr_hex, addr_hydra).
        Or raise ValueError.
        """

        by_len = Addr.Type.by_len(address)

        if by_len is None:
            raise ValueError(f"Invalid HYDRA or smart contract address '{address}' (bad length)")

        if by_len == Addr.Type.H:

            valid = db.rpc.validateaddress(address)

            if not valid.isvalid:
                raise ValueError(f"Invalid HYDRA or smart contract address '{address}' (validation failed)")

            addr_hy = valid.address
            addr_hx = db.rpc.gethexaddress(address)

        elif by_len == Addr.Type.S:

            addr_hx = hex(int(address, 16))[2:].rjust(40, "0")  # ValueError on int() fail
            addr_hy = db.rpc.fromhexaddress(addr_hx)

        else:
            raise ValueError(f"Invalid HYDRA or smart contract address '{address}' (bad type)")

        return by_len, addr_hx, addr_hy

    @staticmethod
    async def validate_contract(db, addr_hx: str) -> Tuple[Addr.Type, AttrDict]:
        return await type(db).run_in_executor(Addr._validate_contract, db, addr_hx)

    @staticmethod
    def _validate_contract(db, addr_hx: str) -> Tuple[Addr.Type, AttrDict]:

        sci = AttrDict()
        addr_tp = Addr.Type.S

        try:
            # Raises BaseRPC.Exception if address does not exist
            r = db.rpc.callcontract(addr_hx, "06fdde03")  # name()
        except BaseRPC.Exception:
            # Safest assumption is that this is actually a HYDRA address
            return Addr.Type.H, sci

        if r.executionResult.excepted == "None":
            sci.name = Addr.__sc_out_str(
                r.executionResult.output[128:]
            )

        r = db.rpc.callcontract(addr_hx, "95d89b41")  # symbol()

        if r.executionResult.excepted == "None":
            sci.sym = Addr.__sc_out_str(
                r.executionResult.output[128:]
            )

            r = db.rpc.callcontract(addr_hx, "313ce567")  # decimals()

            if r.executionResult.excepted == "None":
                sci.dec = int(r.executionResult.output, 16)

                r = db.rpc.callcontract(addr_hx, "18160ddd")  # totalSupply()

                if r.executionResult.excepted == "None":
                    sci.tot = int(r.executionResult.output, 16)
                    addr_tp = Addr.Type.T

        return addr_tp, sci

    @staticmethod
    def __sc_out_str(val):
        return binascii.unhexlify(val).replace(b"\x00", b"").decode("utf-8")
