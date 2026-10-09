# smart-event-phase2

SmartEvent – Phase 2

Role-Based Access Control, Event Management & Admin Analytics

1. Project Overview

SmartEvent is a full-stack Event Discovery and Ticket Booking System developed using FastAPI and React (Vite). Phase 2 enhances the existing Phase 1 application by introducing Role-Based Access Control (RBAC), Organizer Event Management, Organizer Booking Insights, Event Lifecycle Management, and an Admin Dashboard with Platform Analytics.

The platform supports three user roles: USER, ORGANIZER, and ADMIN, each with specific permissions and responsibilities.

2. Objectives

- Implement secure role-based authentication and authorization.
- Allow organizers to create and manage their own events.
- Provide ticket sales and revenue analytics for organizers.
- Manage event statuses throughout the event lifecycle.
- Develop an admin dashboard to monitor platform performance.
- Protect APIs using JWT authentication and role validation.
- Integrate the FastAPI backend with the React frontend.

3. Technology Stack

Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- JWT Authentication
- Passlib or pwdlib for password hashing
- SQLite / PostgreSQL / MySQL
- Uvicorn

Frontend

- React.js with Vite
- JavaScript
- Tailwind CSS
- React Router
- Axios
- Recharts for analytics charts

Development Tools

- Git and GitHub
- Swagger UI
- Postman
- Pytest

4. User Roles and Permissions

Feature| USER| ORGANIZER| ADMIN
Browse events| Yes| Yes| Yes
Book tickets| Yes| Yes| Yes
View personal bookings| Yes| Yes| Yes
Create events| No| Yes| Yes, if supported
Manage own events| No| Yes| Yes
View bookings for own events| No| Yes| Yes
View all users| No| No| Yes
View all bookings| No| No| Yes
Access platform analytics| No| No| Yes

5. Modules and Implementation

Module 7: Role-Based Access Control (RBAC)

Objective: Control access to APIs based on the authenticated user's role.

Features:

- Add a role field to the Users table.
- Include role information in JWT access tokens.
- Create reusable authentication and role-checking dependencies.
- Restrict protected endpoints to authorized roles.
- Return HTTP 401 for unauthenticated requests and HTTP 403 for insufficient permissions.

Suggested APIs:

- "POST /auth/register"
- "POST /auth/login"
- "GET /users/me"

Module 8: Organizer Event Management

Objective: Allow organizers to manage the events they create.

Features:

- Create new events.
- Update event information.
- Cancel events.
- Fetch events created by the logged-in organizer.
- View bookings associated with organizer-owned events.
- Validate event ownership before updates or cancellation.

Suggested APIs:

- "POST /organizer/events"
- "GET /organizer/events"
- "GET /organizer/events/{event_id}"
- "PUT /organizer/events/{event_id}"
- "PATCH /organizer/events/{event_id}/cancel"
- "GET /organizer/events/{event_id}/bookings"

Module 9: Organizer Booking Insights

Objective: Provide event-specific ticket sales and revenue information.

Features:

- Total tickets sold per event.
- Remaining ticket availability.
- Total revenue per event.
- Total booking count.
- Sales charts and revenue summaries.
- Event performance overview.

Suggested APIs:

- "GET /organizer/analytics/overview"
- "GET /organizer/analytics/events/{event_id}"
- "GET /organizer/analytics/sales"
- "GET /organizer/analytics/revenue"

Module 10: Event Status and Updates

Objective: Manage the event lifecycle and communicate important changes to users.

Event statuses:

- UPCOMING
- ONGOING
- COMPLETED
- CANCELLED

Features:

- Determine event status from the event's start and end dates.
- Allow organizers to cancel their own events.
- Notify affected users when an event is cancelled or updated.
- Display event status and cancellation notices on the frontend.
- Prevent new bookings for cancelled or completed events.

Suggested APIs:

- "GET /events"
- "GET /events/{event_id}"
- "PATCH /organizer/events/{event_id}/cancel"
- "GET /notifications"
- "PATCH /notifications/{notification_id}/read"

Module 11: Admin Dashboard and Platform Analytics

Objective: Give administrators centralized access to platform management and analytics.

Features:

- Total registered users.
- Total events created.
- Total tickets sold.
- Total bookings.
- Platform revenue summary.
- Daily ticket sales.
- Monthly booking trends.
- Most popular events.
- Top revenue-generating events.
- Date-based analytics filtering.
- User, event, and booking overviews.

Suggested APIs:

- "GET /admin/users"
- "GET /admin/events"
- "GET /admin/bookings"
- "GET /admin/analytics/overview"
- "GET /admin/analytics/daily-sales"
- "GET /admin/analytics/monthly-bookings"
- "GET /admin/analytics/popular-events"
- "GET /admin/analytics/top-revenue-events"

All admin endpoints must require ADMIN authorization.

6. Database Design

Users Table

- "id" – Primary key
- "name" – User's full name
- "email" – Unique email address
- "hashed_password" – Hashed password
- "role" – USER, ORGANIZER, or ADMIN
- "created_at" – Registration timestamp

Events Table

- "id" – Primary key
- "title" – Event title
- "description" – Event description
- "location" – Event location
- "start_date" – Event start date and time
- "end_date" – Event end date and time
- "ticket_price" – Price per ticket
- "total_tickets" – Total available tickets
- "organizer_id" – Foreign key referencing Users
- "event_status" – UPCOMING, ONGOING, COMPLETED, or CANCELLED
- "created_at" – Event creation timestamp

Existing Tables

Bookings

- Booking details, user reference, event reference, ticket quantity, total amount, booking status, and timestamps.

Tickets

- Ticket identifier, booking reference, ticket details, and ticket status.

Notifications

- User reference, notification message, read status, and creation timestamp.

Use SQLAlchemy relationships and foreign keys to maintain database integrity. Add migrations or update the database schema when introducing new fields.

7. Suggested Project Structure

SmartEvent/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── dependencies.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── events.py
│   │   ├── organizer.py
│   │   ├── organizer_analytics.py
│   │   ├── notifications.py
│   │   └── admin.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── Events.jsx
│   │   │   ├── CreateEvent.jsx
│   │   │   ├── ManageEvents.jsx
│   │   │   ├── EditEvent.jsx
│   │   │   ├── EventBookings.jsx
│   │   │   ├── OrganizerDashboard.jsx
│   │   │   ├── AdminDashboard.jsx
│   │   │   ├── PlatformAnalytics.jsx
│   │   │   ├── UsersOverview.jsx
│   │   │   ├── EventsOverview.jsx
│   │   │   └── BookingsOverview.jsx
│   │   ├── services/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md

8. Installation and Setup

Prerequisites

- Python 3.9 or higher
- Node.js and npm
- Git

Backend Setup

Open a terminal and run:

cd backend

python -m venv venv

Activate the virtual environment.

Windows:

venv\Scripts\activate

Linux/macOS:

source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Create a ".env" file using ".env.example" and configure the database URL, JWT secret, and token settings.

Start the backend:

uvicorn main:app --reload

Open Swagger UI:

"http://127.0.0.1:8000/docs"

Frontend Setup

Open another terminal:

cd frontend
npm install
npm run dev

Open the local URL displayed by Vite in your terminal.

9. Security Requirements

- Use JWT authentication for protected endpoints.
- Hash passwords securely.
- Validate roles on every restricted API.
- Verify organizer ownership before modifying events or viewing event bookings.
- Restrict platform-wide analytics and administrative operations to ADMIN.
- Validate request data using Pydantic schemas.
- Store secrets in environment variables.
- Never commit ".env", database credentials, or JWT secrets to GitHub.
- Validate ticket availability and booking quantities on the backend.
- Ensure cancelled events cannot accept new bookings.
- Calculate revenue from valid booking/payment records rather than trusting frontend values.

10. Testing

Test the following scenarios using Swagger UI, Postman, or Pytest:

- Successful registration and login.
- JWT authentication and role validation.
- USER cannot access organizer-only or admin-only endpoints.
- ORGANIZER can create events and manage only their own events.
- Unauthorized users cannot view another organizer's bookings.
- ADMIN can view users, events, bookings, and analytics.
- Event statuses change correctly according to event dates.
- Cancelled events reject new bookings.
- Analytics return correct ticket counts and revenue.
- Invalid input is rejected with appropriate HTTP status codes.

11. Expected Deliverables

- Fully functional RBAC system.
- Organizer event creation and management.
- Organizer booking insights and analytics dashboard.
- Event lifecycle and notification functionality.
- Admin dashboard with platform-wide analytics.
- Secure REST APIs.
- React frontend integrated with FastAPI.
- Updated database models and relationships.
- API testing and project documentation.

12. Conclusion

SmartEvent Phase 2 extends the existing event discovery and ticket booking platform with secure role-based access, organizer tools, event lifecycle management, and administrative analytics. The implementation provides a foundation for a scalable platform that supports users, event organizers, and administrators through clearly defined permissions and data-driven dashboards.
