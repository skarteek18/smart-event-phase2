
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


# --------------------------------------------------
# ENUMS
# --------------------------------------------------

class UserRole(str, Enum):
    USER = "USER"
    ORGANIZER = "ORGANIZER"
    ADMIN = "ADMIN"


class EventStatus(str, Enum):
    UPCOMING = "UPCOMING"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class BookingStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TicketStatus(str, Enum):
    VALID = "VALID"
    USED = "USED"
    CANCELLED = "CANCELLED"


# --------------------------------------------------
# MODULE 7: USER AND AUTHENTICATION SCHEMAS
# --------------------------------------------------

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --------------------------------------------------
# MODULE 8: EVENT MANAGEMENT SCHEMAS
# --------------------------------------------------

class EventCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5)
    location: str = Field(..., min_length=2, max_length=255)

    start_date: datetime
    end_date: datetime

    ticket_price: float = Field(..., ge=0)
    total_tickets: int = Field(..., gt=0)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")
        return self


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=5)
    location: Optional[str] = Field(None, min_length=2, max_length=255)

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    ticket_price: Optional[float] = Field(None, ge=0)
    total_tickets: Optional[int] = Field(None, gt=0)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.end_date:
            if self.end_date <= self.start_date:
                raise ValueError("End date must be after start date")
        return self


class EventResponse(BaseModel):
    id: int
    title: str
    description: str
    location: str
    start_date: datetime
    end_date: datetime
    ticket_price: float
    total_tickets: int
    organizer_id: int
    event_status: EventStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------
# PHASE 1: BOOKING SCHEMAS
# --------------------------------------------------

class BookingCreate(BaseModel):
    event_id: int
    quantity: int = Field(..., gt=0)


class BookingResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    quantity: int
    total_amount: float
    status: BookingStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------
# PHASE 1: TICKET SCHEMAS
# --------------------------------------------------

class TicketResponse(BaseModel):
    id: int
    booking_id: int
    ticket_code: str
    status: TicketStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------
# PHASE 1: NOTIFICATION SCHEMAS
# --------------------------------------------------

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------
# MODULE 9: ORGANIZER ANALYTICS SCHEMAS
# --------------------------------------------------

class EventAnalytics(BaseModel):
    event_id: int
    event_title: str
    event_status: EventStatus
    total_tickets: int
    tickets_sold: int
    remaining_tickets: int
    booking_count: int
    total_revenue: float


class OrganizerAnalyticsResponse(BaseModel):
    total_events: int
    total_tickets_sold: int
    total_revenue: float
    events: list[EventAnalytics]


# --------------------------------------------------
# MODULE 11: ADMIN ANALYTICS SCHEMAS
# --------------------------------------------------

class AdminAnalyticsResponse(BaseModel):
    total_registered_users: int
    total_events_created: int
    total_tickets_sold: int
    total_bookings: int
    platform_revenue: float


class DailySalesResponse(BaseModel):
    date: str
    booking_count: int
    tickets_sold: int
    revenue: float


class MonthlyBookingResponse(BaseModel):
    month: str
    booking_count: int


class PopularEventResponse(BaseModel):
    event_id: int
    title: str
    booking_count: int
    tickets_sold: int


class TopRevenueEventResponse(BaseModel):
    event_id: int
    title: str
    revenue: float
