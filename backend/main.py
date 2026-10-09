
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import Base, engine, get_db
from models import User, Event, Booking
from auth import get_current_user

# --------------------------------------------------
# APPLICATION SETUP
# --------------------------------------------------

app = FastAPI(
    title="SmartEvent API",
    description="Phase 2 - RBAC, Organizer Management and Admin Analytics",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# For development only. Use database migrations in production.
Base.metadata.create_all(bind=engine)


# --------------------------------------------------
# AUTHORIZATION HELPERS
# --------------------------------------------------

def require_role(*roles: str):
    def role_checker(
        current_user: User = Depends(get_current_user),
    ):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this resource.",
            )
        return current_user

    return role_checker


def update_event_status(event: Event):
    """Derive the lifecycle status from the event dates."""
    if event.event_status == "CANCELLED":
        return event.event_status

    now = datetime.now(timezone.utc)

    start = event.start_date
    end = event.end_date

    # Support database datetimes that may be timezone-naive.
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)

    if now < start:
        event.event_status = "UPCOMING"
    elif now < end:
        event.event_status = "ONGOING"
    else:
        event.event_status = "COMPLETED"

    return event.event_status


def verify_event_owner(event: Event, user: User):
    if event.organizer_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="You can manage only your own events.",
        )


def get_event_or_404(db: Session, event_id: int):
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return event


# --------------------------------------------------
# GENERAL ENDPOINTS
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Welcome to SmartEvent Phase 2 API",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# --------------------------------------------------
# MODULE 7: ROLE-BASED ACCESS CONTROL
# --------------------------------------------------

@app.get("/users/me")
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
    }


# --------------------------------------------------
# MODULE 8: ORGANIZER EVENT MANAGEMENT
# --------------------------------------------------

@app.post("/organizer/events", status_code=201)
def create_event(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ORGANIZER", "ADMIN")),
):
    required_fields = [
        "title",
        "description",
        "location",
        "start_date",
        "end_date",
        "ticket_price",
        "total_tickets",
    ]

    missing = [field for field in required_fields if field not in payload]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing fields: {', '.join(missing)}",
        )

    try:
        start = datetime.fromisoformat(
            str(payload["start_date"]).replace("Z", "+00:00")
        )
        end = datetime.fromisoformat(
            str(payload["end_date"]).replace("Z", "+00:00")
        )
        price = float(payload["ticket_price"])
        total_tickets = int(payload["total_tickets"])
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=422,
            detail="Invalid dates, ticket price, or ticket quantity.",
        )

    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)

    if end <= start:
        raise HTTPException(
            status_code=422,
            detail="Event end date must be after its start date.",
        )

    if start <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=422,
            detail="New events must have a future start date.",
        )

    if price < 0 or total_tickets <= 0:
        raise HTTPException(
            status_code=422,
            detail="Ticket price cannot be negative and ticket quantity must be positive.",
        )

    event = Event(
        title=payload["title"],
        description=payload["description"],
        location=payload["location"],
        start_date=start,
        end_date=end,
        ticket_price=price,
        total_tickets=total_tickets,
        organizer_id=current_user.id,
        event_status="UPCOMING",
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "message": "Event created successfully",
        "event_id": event.id,
        "organizer_id": event.organizer_id,
        "event_status": event.event_status,
    }


@app.get("/organizer/events")
def get_organizer_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ORGANIZER", "ADMIN")),
):
    query = db.query(Event)

    if current_user.role == "ORGANIZER":
        query = query.filter(Event.organizer_id == current_user.id)

    events = query.all()

    for event in events:
        update_event_status(event)

    db.commit()

    return events


@app.put("/organizer/events/{event_id}")
def update_event(
    event_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ORGANIZER", "ADMIN")),
):
    event = get_event_or_404(db, event_id)
    verify_event_owner(event, current_user)

    if event.event_status in ("CANCELLED", "COMPLETED"):
        raise HTTPException(
            status_code=400,
            detail="Cancelled or completed events cannot be updated.",
        )

    allowed_fields = {
        "title",
        "description",
        "location",
        "start_date",
        "end_date",
        "ticket_price",
        "total_tickets",
    }

    for field, value in payload.items():
        if field not in allowed_fields:
            raise HTTPException(
                status_code=422,
                detail=f"Field '{field}' cannot be updated.",
            )

        if field in ("start_date", "end_date"):
            try:
                value = datetime.fromisoformat(
                    str(value).replace("Z", "+00:00")
                )
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid {field}.",
                )

            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)

        elif field == "ticket_price":
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=422,
                    detail="Invalid ticket price.",
                )

            if value < 0:
                raise HTTPException(
                    status_code=422,
                    detail="Ticket price cannot be negative.",
                )

        elif field == "total_tickets":
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=422,
                    detail="Invalid ticket quantity.",
                )

            if value <= 0:
                raise HTTPException(
                    status_code=422,
                    detail="Ticket quantity must be positive.",
                )

        setattr(event, field, value)

    if event.end_date <= event.start_date:
        raise HTTPException(
            status_code=422,
            detail="Event end date must be after its start date.",
        )

    if event.start_date <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=422,
            detail="Event start date must remain in the future.",
        )

    update_event_status(event)
    db.commit()
    db.refresh(event)

    return {"message": "Event updated successfully", "event_id": event.id}


@app.patch("/organizer/events/{event_id}/cancel")
def cancel_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ORGANIZER", "ADMIN")),
):
    event = get_event_or_404(db, event_id)
    verify_event_owner(event, current_user)

    if event.event_status == "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail="Completed events cannot be cancelled.",
        )

    if event.event_status == "CANCELLED":
        return {"message": "Event is already cancelled"}

    event.event_status = "CANCELLED"
    db.commit()

    # TODO: Create notifications for users with bookings for this event.

    return {"message": "Event cancelled successfully"}


@app.get("/organizer/events/{event_id}/bookings")
def get_event_bookings(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ORGANIZER", "ADMIN")),
):
    event = get_event_or_404(db, event_id)
    verify_event_owner(event, current_user)

    bookings = (
        db.query(Booking)
        .filter(Booking.event_id == event_id)
        .all()
    )

    return bookings


# --------------------------------------------------
# MODULE 9: ORGANIZER BOOKING INSIGHTS
# --------------------------------------------------

@app.get("/organizer/analytics/overview")
def organizer_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ORGANIZER", "ADMIN")),
):
    query = db.query(Event)

    if current_user.role == "ORGANIZER":
        query = query.filter(Event.organizer_id == current_user.id)

    events = query.all()
    results = []

    for event in events:
        update_event_status(event)

        bookings = (
            db.query(Booking)
            .filter(Booking.event_id == event.id)
            .all()
        )

        # Adjust the status value to match your Booking model.
        valid_bookings = [
            booking
            for booking in bookings
            if str(booking.status).upper() in ("CONFIRMED", "COMPLETED")
        ]

        tickets_sold = sum(
            int(booking.quantity) for booking in valid_bookings
        )

        revenue = sum(
            float(booking.total_amount) for booking in valid_bookings
        )

        results.append({
            "event_id": event.id,
            "event_title": event.title,
            "event_status": event.event_status,
            "total_tickets": event.total_tickets,
            "tickets_sold": tickets_sold,
            "remaining_tickets": max(
                0, event.total_tickets - tickets_sold
            ),
            "booking_count": len(valid_bookings),
            "total_revenue": revenue,
        })

    db.commit()

    return {
        "total_events": len(events),
        "total_tickets_sold": sum(
            item["tickets_sold"] for item in results
        ),
        "total_revenue": sum(
            item["total_revenue"] for item in results
        ),
        "events": results,
    }


# --------------------------------------------------
# MODULE 10: EVENT STATUS MANAGEMENT
# --------------------------------------------------

@app.get("/events")
def get_public_events(
    db: Session = Depends(get_db),
):
    events = db.query(Event).all()

    for event in events:
        update_event_status(event)

    db.commit()

    return events


@app.get("/events/{event_id}")
def get_public_event(
    event_id: int,
    db: Session = Depends(get_db),
):
    event = get_event_or_404(db, event_id)
    update_event_status(event)
    db.commit()
    return event


# --------------------------------------------------
# MODULE 11: ADMIN DASHBOARD AND ANALYTICS
# --------------------------------------------------

@app.get("/admin/users")
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    users = db.query(User).all()

    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        }
        for user in users
    ]


@app.get("/admin/events")
def get_all_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    events = db.query(Event).all()

    for event in events:
        update_event_status(event)

    db.commit()
    return events


@app.get("/admin/bookings")
def get_all_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    return db.query(Booking).all()


@app.get("/admin/analytics/overview")
def admin_analytics_overview(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(require_role("ADMIN")),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date must be before end_date.",
        )

    total_users = db.query(func.count(User.id)).scalar() or 0
    total_events = db.query(func.count(Event.id)).scalar() or 0

    bookings_query = db.query(Booking)

    if start_date:
        bookings_query = bookings_query.filter(
            Booking.created_at >= start_date
        )

    if end_date:
        bookings_query = bookings_query.filter(
            Booking.created_at <= end_date
        )

    bookings = bookings_query.all()

    valid_bookings = [
        booking for booking in bookings
        if str(booking.status).upper() in ("CONFIRMED", "COMPLETED")
    ]

    total_bookings = len(valid_bookings)
    total_tickets_sold = sum(
        int(booking.quantity) for booking in valid_bookings
    )
    platform_revenue = sum(
        float(booking.total_amount) for booking in valid_bookings
    )

    return {
        "total_registered_users": total_users,
        "total_events_created": total_events,
        "total_tickets_sold": total_tickets_sold,
        "total_bookings": total_bookings,
        "platform_revenue": platform_revenue,
        "date_range": {
            "start_date": start_date,
            "end_date": end_date,
        },
    }


@app.get("/admin/analytics/daily-sales")
def admin_daily_sales(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    bookings = db.query(Booking).all()
    sales = {}

    for booking in bookings:
        if str(booking.status).upper() not in (
            "CONFIRMED", "COMPLETED"
        ):
            continue

        day = booking.created_at.date().isoformat()
        sales.setdefault(day, {"booking_count": 0, "tickets_sold": 0, "revenue": 0.0})

        sales[day]["booking_count"] += 1
        sales[day]["tickets_sold"] += int(booking.quantity)
        sales[day]["revenue"] += float(booking.total_amount)

    return [
        {"date": day, **values}
        for day, values in sorted(sales.items())
    ]


@app.get("/admin/analytics/monthly-bookings")
def admin_monthly_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    bookings = db.query(Booking).all()
    trends = {}

    for booking in bookings:
        if str(booking.status).upper() not in (
            "CONFIRMED", "COMPLETED"
        ):
            continue

        month = booking.created_at.strftime("%Y-%m")
        trends[month] = trends.get(month, 0) + 1

    return [
        {"month": month, "booking_count": count}
        for month, count in sorted(trends.items())
    ]


@app.get("/admin/analytics/popular-events")
def popular_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    events = db.query(Event).all()
    results = []

    for event in events:
        bookings = (
            db.query(Booking)
            .filter(
                Booking.event_id == event.id,
                Booking.status.in_(["CONFIRMED", "COMPLETED"]),
            )
            .all()
        )

        results.append({
            "event_id": event.id,
            "title": event.title,
            "booking_count": len(bookings),
            "tickets_sold": sum(
                int(booking.quantity) for booking in bookings
            ),
        })

    return sorted(
        results,
        key=lambda item: item["tickets_sold"],
        reverse=True,
    )


@app.get("/admin/analytics/top-revenue-events")
def top_revenue_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    events = db.query(Event).all()
    results = []

    for event in events:
        bookings = (
            db.query(Booking)
            .filter(
                Booking.event_id == event.id,
                Booking.status.in_(["CONFIRMED", "COMPLETED"]),
            )
            .all()
        )

        results.append({
            "event_id": event.id,
            "title": event.title,
            "revenue": sum(
                float(booking.total_amount) for booking in bookings
            ),
        })

    return sorted(
        results,
        key=lambda item: item["revenue"],
        reverse=True,
    )
