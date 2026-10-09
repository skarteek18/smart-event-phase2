

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import User, Event, Booking
from auth import get_current_user

router = APIRouter(
    prefix="/admin",
    tags=["Admin Dashboard"],
)


# --------------------------------------------------
# ADMIN AUTHORIZATION
# --------------------------------------------------

def require_admin(
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Admin access required.",
        )
    return current_user


# --------------------------------------------------
# HELPER: CONFIRMED BOOKINGS
# --------------------------------------------------

def confirmed_bookings_query(db: Session):
    return db.query(Booking).filter(
        Booking.status.in_(["CONFIRMED", "COMPLETED"])
    )


# --------------------------------------------------
# VIEW ALL USERS
# --------------------------------------------------

@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    users = db.query(User).order_by(User.id.desc()).all()

    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at,
        }
        for user in users
    ]


# --------------------------------------------------
# VIEW ALL EVENTS
# --------------------------------------------------

@router.get("/events")
def get_all_events(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    events = db.query(Event).order_by(Event.id.desc()).all()

    return [
        {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "location": event.location,
            "start_date": event.start_date,
            "end_date": event.end_date,
            "ticket_price": event.ticket_price,
            "total_tickets": event.total_tickets,
            "organizer_id": event.organizer_id,
            "event_status": event.event_status,
            "created_at": event.created_at,
        }
        for event in events
    ]


# --------------------------------------------------
# VIEW ALL BOOKINGS
# --------------------------------------------------

@router.get("/bookings")
def get_all_bookings(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    bookings = db.query(Booking).order_by(
        Booking.created_at.desc()
    ).all()

    return [
        {
            "id": booking.id,
            "user_id": booking.user_id,
            "event_id": booking.event_id,
            "quantity": booking.quantity,
            "total_amount": booking.total_amount,
            "status": booking.status,
            "created_at": booking.created_at,
        }
        for booking in bookings
    ]


# --------------------------------------------------
# ADMIN DASHBOARD OVERVIEW
# --------------------------------------------------

@router.get("/analytics/overview")
def admin_analytics_overview(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date must be before end_date.",
        )

    total_users = db.query(func.count(User.id)).scalar() or 0
    total_events = db.query(func.count(Event.id)).scalar() or 0

    query = confirmed_bookings_query(db)

    if start_date:
        query = query.filter(Booking.created_at >= start_date)

    if end_date:
        query = query.filter(Booking.created_at <= end_date)

    bookings = query.all()

    return {
        "total_registered_users": total_users,
        "total_events_created": total_events,
        "total_tickets_sold": sum(
            booking.quantity for booking in bookings
        ),
        "total_bookings": len(bookings),
        "platform_revenue": sum(
            float(booking.total_amount) for booking in bookings
        ),
        "start_date": start_date,
        "end_date": end_date,
    }


# --------------------------------------------------
# DAILY TICKET SALES
# --------------------------------------------------

@router.get("/analytics/daily-sales")
def daily_ticket_sales(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    query = confirmed_bookings_query(db)

    if start_date:
        query = query.filter(Booking.created_at >= start_date)

    if end_date:
        query = query.filter(Booking.created_at <= end_date)

    bookings = query.all()
    daily_data = {}

    for booking in bookings:
        day = booking.created_at.date().isoformat()

        if day not in daily_data:
            daily_data[day] = {
                "date": day,
                "booking_count": 0,
                "tickets_sold": 0,
                "revenue": 0.0,
            }

        daily_data[day]["booking_count"] += 1
        daily_data[day]["tickets_sold"] += booking.quantity
        daily_data[day]["revenue"] += float(
            booking.total_amount
        )

    return [
        daily_data[day]
        for day in sorted(daily_data)
    ]


# --------------------------------------------------
# MONTHLY BOOKING TRENDS
# --------------------------------------------------

@router.get("/analytics/monthly-bookings")
def monthly_booking_trends(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    query = confirmed_bookings_query(db)

    if start_date:
        query = query.filter(Booking.created_at >= start_date)

    if end_date:
        query = query.filter(Booking.created_at <= end_date)

    bookings = query.all()
    monthly_data = {}

    for booking in bookings:
        month = booking.created_at.strftime("%Y-%m")
        monthly_data[month] = monthly_data.get(month, 0) + 1

    return [
        {
            "month": month,
            "booking_count": monthly_data[month],
        }
        for month in sorted(monthly_data)
    ]


# --------------------------------------------------
# MOST POPULAR EVENTS
# --------------------------------------------------

@router.get("/analytics/popular-events")
def popular_events(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    events = db.query(Event).all()
    results = []

    for event in events:
        bookings = (
            confirmed_bookings_query(db)
            .filter(Booking.event_id == event.id)
            .all()
        )

        results.append({
            "event_id": event.id,
            "title": event.title,
            "booking_count": len(bookings),
            "tickets_sold": sum(
                booking.quantity for booking in bookings
            ),
        })

    results.sort(
        key=lambda item: item["tickets_sold"],
        reverse=True,
    )

    return results[:limit]


# --------------------------------------------------
# TOP REVENUE-GENERATING EVENTS
# --------------------------------------------------

@router.get("/analytics/top-revenue-events")
def top_revenue_events(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    events = db.query(Event).all()
    results = []

    for event in events:
        bookings = (
            confirmed_bookings_query(db)
            .filter(Booking.event_id == event.id)
            .all()
        )

        results.append({
            "event_id": event.id,
            "title": event.title,
            "revenue": sum(
                float(booking.total_amount)
                for booking in bookings
            ),
        })

    results.sort(
        key=lambda item: item["revenue"],
        reverse=True,
    )

    return results[:limit]
