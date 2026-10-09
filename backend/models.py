
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    Boolean,
    Enum,
)
from sqlalchemy.orm import relationship

from database import Base


# --------------------------------------------------
# MODULE 7: USERS AND ROLE-BASED ACCESS CONTROL
# --------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    role = Column(
        Enum("USER", "ORGANIZER", "ADMIN", name="user_roles"),
        default="USER",
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    events = relationship(
        "Event",
        back_populates="organizer",
        foreign_keys="Event.organizer_id",
    )

    bookings = relationship("Booking", back_populates="user")

    notifications = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
    )


# --------------------------------------------------
# MODULES 8 AND 10: EVENT MANAGEMENT AND EVENT STATUS
# --------------------------------------------------

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(255), nullable=False)

    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)

    ticket_price = Column(Float, nullable=False, default=0.0)
    total_tickets = Column(Integer, nullable=False)

    organizer_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    event_status = Column(
        Enum(
            "UPCOMING",
            "ONGOING",
            "COMPLETED",
            "CANCELLED",
            name="event_statuses",
        ),
        default="UPCOMING",
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    organizer = relationship(
        "User",
        back_populates="events",
        foreign_keys=[organizer_id],
    )

    bookings = relationship("Booking", back_populates="event")


# --------------------------------------------------
# PHASE 1: BOOKINGS
# --------------------------------------------------

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    event_id = Column(
        Integer,
        ForeignKey("events.id"),
        nullable=False,
        index=True,
    )

    quantity = Column(Integer, nullable=False)
    total_amount = Column(Float, nullable=False)

    status = Column(
        Enum(
            "PENDING",
            "CONFIRMED",
            "COMPLETED",
            "CANCELLED",
            name="booking_statuses",
        ),
        default="PENDING",
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="bookings")
    event = relationship("Event", back_populates="bookings")

    tickets = relationship(
        "Ticket",
        back_populates="booking",
        cascade="all, delete-orphan",
    )


# --------------------------------------------------
# PHASE 1: TICKETS
# --------------------------------------------------

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)

    booking_id = Column(
        Integer,
        ForeignKey("bookings.id"),
        nullable=False,
        index=True,
    )

    ticket_code = Column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    status = Column(
        Enum(
            "VALID",
            "USED",
            "CANCELLED",
            name="ticket_statuses",
        ),
        default="VALID",
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship
    booking = relationship("Booking", back_populates="tickets")


# --------------------------------------------------
# PHASE 1: NOTIFICATIONS
# --------------------------------------------------

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    message = Column(Text, nullable=False)

    is_read = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship
    user = relationship("User", back_populates="notifications")
