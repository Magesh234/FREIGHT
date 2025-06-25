# FreightLink Development Log

This document details the development progress of the FreightLink system, which includes both the frontend (HTML/JS) and backend (Django REST API).

---

## May 15–16, 2025
- Project setup for FreightLink initiated.
- Defined the project scope: truck booking and bidding system.
- Initialized Django backend project (`freightlink_backend`).
- Created app folders: `accounts`, `bids`, `bookings`, `trucks`.

---

## May 17–18, 2025
- Set up core models and serializers for accounts and bookings.
- Started working on the HTML structure for:
  - `index.html`
  - `login.html`
  - `register.html`

---

## May 19–20, 2025
- Built initial frontend structure for:
  - `dashboard.html`, `settings.html`, `mylisting.html`
- Completed basic forms and layout with HTML/CSS.

---

## May 21–22, 2025
- Added additional pages:
  - `messages.html`, `notifications.html`, `help&support.html`, `payments.html`
- Began developing backend views for user registration and authentication.

---

## May 23–24, 2025
- Created booking APIs and tested endpoints using Postman.
- Wrote database migrations for bookings and trucks.

---

## May 25–26, 2025
- Started working on frontend and backend messaging features.
- Created `support` and `messaging` Django apps.

---

## May 27–28, 2025
- Completed initial API logic for submitting bids and receiving responses.
- Connected static frontend pages to real backend routes.

---

## May 29–30, 2025
- Worked on the `tasks.py` for asynchronous features.
- Improved logging system with `freight_app.log` and `freight_errors.log`.

---

## May 31–June 1, 2025
- Designed and tested truck model APIs.
- Refined booking and truck linkage logic.

---

## June 2–3, 2025
- Frontend: improved layout responsiveness.
- Backend: added permissions and validation to serializers.

---

## June 4–5, 2025
- Created bid filter views and integrated with frontend JavaScript.
- Finalized API for accepting/rejecting bids.

---

## June 6–7, 2025
- Built new pages: `ordering6.html`, `history.html`, and `profile.html`.
- Refactored backend views for modularity and reuse.

---

## June 8–9, 2025
- Cleaned up form structure and JavaScript input validation.
- Finalized frontend routes for user interaction.

---

## June 10–11, 2025
- Backend: tested full booking-to-bid cycle.
- Implemented status updates for ongoing bids.

---

## June 12–13, 2025
- Integrated success/error messages into frontend forms.
- Backend bug fixes on booking submissions.

---

## June 14–15, 2025
- Completed layout and styling of all pages.
- Started testing full workflow from login to truck booking.

---

## June 16–17, 2025
- Fixed CSRF token issues on POST requests from the frontend.
- Enhanced authentication flow using Django sessions.

---

## June 18–19, 2025
- Connected booking form to API endpoints.
- Created truck listing page and integrated with truck models.

---

## June 20, 2025
- Final testing and validation of HTML inputs and backend responses.
- Prepared full repo for GitHub structure and documentation.
  
---
## June 22, 2025
- Migrated the database from sqlite to PostgreSQL
- Facing some minor challenges in migration 

--
## June 23, 2025
- Intergrated the payment system
- Applied for daraja Credentials
