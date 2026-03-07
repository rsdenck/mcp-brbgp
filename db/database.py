from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Text,
    Index,
    ForeignKey,
)
from sqlalchemy.sql import func
from contextlib import asynccontextmanager
import os

Base = declarative_base()


class ASN(Base):
    __tablename__ = "asns"

    id = Column(Integer, primary_key=True)
    asn = Column(Integer, unique=True, index=True)
    name = Column(String(500))
    description = Column(String(1000))
    country = Column(String(2), index=True)
    created = Column(DateTime)
    updated = Column(DateTime)
    rimenet_prefixes_v4 = Column(Integer, default=0)
    rimenet_prefixes_v6 = Column(Integer, default=0)
    is_peeringdb_synced = Column(Boolean, default=False)
    is_ris_peer = Column(Boolean, default=False)

    __table_args__ = (
        Index("idx_asn_country", "asn", "country"),
        Index("idx_asn_updated", "updated"),
    )


class Prefix(Base):
    __tablename__ = "prefixes"

    id = Column(Integer, primary_key=True)
    prefix = Column(String(50), index=True)
    prefix_v6 = Column(String(100))
    asn_id = Column(Integer, ForeignKey("asns.id"))
    asn = Column(Integer, index=True)
    first_seen = Column(DateTime, default=func.now())
    last_seen = Column(DateTime, default=func.now(), onupdate=func.now())
    is_originated = Column(Boolean, default=False)
    is_transitive = Column(Boolean, default=False)
    is_announced = Column(Boolean, default=True)
    is_rpki_valid = Column(Boolean, default=None)
    is_rpki_origin = Column(String(20), default=None)

    __table_args__ = (
        Index("idx_prefix_asn", "prefix", "asn"),
        Index("idx_prefix_v6", "prefix_v6"),
    )


class ASRelationship(Base):
    __tablename__ = "as_relationships"

    id = Column(Integer, primary_key=True)
    source_asn = Column(Integer, ForeignKey("asns.asn"), index=True)
    target_asn = Column(Integer, ForeignKey("asns.asn"), index=True)
    relationship_type = Column(String(20), index=True)
    first_seen = Column(DateTime, default=func.now())
    last_seen = Column(DateTime, default=func.now(), onupdate=func.now())
    is_peeringdb = Column(Boolean, default=False)
    is_bgp_observed = Column(Boolean, default=False)

    __table_args__ = (Index("idx_rel_source_target", "source_asn", "target_asn"),)


class IX(Base):
    __tablename__ = "ixs"

    id = Column(Integer, primary_key=True)
    ix_id = Column(Integer, index=True)
    name = Column(String(200))
    name_long = Column(String(500))
    city = Column(String(100))
    country = Column(String(2))
    latitude = Column(Float)
    longitude = Column(Float)
    website = Column(String(500))
    tech_email = Column(String(200))
    status = Column(String(20), default="active")
    updated = Column(DateTime)

    __table_args__ = (Index("idx_ix_country", "country"),)


class IXMember(Base):
    __tablename__ = "ix_members"

    id = Column(Integer, primary_key=True)
    ix_id = Column(Integer, ForeignKey("ixs.id"))
    asn_id = Column(Integer, ForeignKey("asns.id"))
    asn = Column(Integer, index=True)
    name = Column(String(500))
    is_peeringdb = Column(Boolean, default=True)
    added = Column(DateTime, default=func.now())


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True)
    incident_id = Column(String(100), unique=True, index=True)
    incident_type = Column(String(50), index=True)
    asn = Column(Integer, index=True)
    prefix = Column(String(50))
    message = Column(Text)
    severity = Column(String(20))
    source = Column(String(50))
    raw_data = Column(Text)
    detected_at = Column(DateTime, default=func.now(), index=True)
    resolved_at = Column(DateTime, default=None)
    is_resolved = Column(Boolean, default=False)

    __table_args__ = (Index("idx_incident_type_time", "incident_type", "detected_at"),)


class IXStatus(Base):
    __tablename__ = "ix_status"

    id = Column(Integer, primary_key=True)
    ix_name = Column(String(200))
    status = Column(String(20))
    message = Column(String(500))
    affected_components = Column(Text)
    fetched_at = Column(DateTime, default=func.now(), index=True)


class RIBEntry(Base):
    __tablename__ = "rib_entries"

    id = Column(Integer, primary_key=True)
    prefix = Column(String(50), index=True)
    asn_path = Column(String(1000))
    origin_asn = Column(Integer, index=True)
    next_hop = Column(String(50))
    local_pref = Column(Integer)
    med = Column(Integer)
    community = Column(Text)
    collected_at = Column(DateTime, default=func.now(), index=True)
    collector = Column(String(100))

    __table_args__ = (
        Index("idx_rib_prefix_origin", "prefix", "origin_asn"),
        Index("idx_rib_collector_time", "collector", "collected_at"),
    )


import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = os.getenv(
    "DATABASE_URL", f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'brbgp.db')}"
)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with async_session() as session:
        yield session


@asynccontextmanager
async def get_db_context():
    async with async_session() as session:
        yield session
