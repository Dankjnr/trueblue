# TrueBlue

A cleaning-service management platform for three roles — Customer, Cleaner,
Admin — covering request intake, cleaner matching, admin-controlled
assignment, and post-acceptance job packets, with an audit trail throughout.

## Stack

- **Backend**: Django + Django REST Framework, PostgreSQL, JWT auth
  (`djangorestframework-simplejwt`), OTP login, field-level encryption for
  access codes.
- **Frontend**: React (Vite), Tailwind CSS, Framer Motion.
- **Notifications**: Termii (SMS) + Firebase Cloud Messaging (push), both
  behind a thin provider interface in `backend/notifications/services.py`.

## How the workflow maps to the code

| Workflow step | Where |
|---|---|
| Request intake (app or admin phone-in) | `jobs.views.JobViewSet.create`, `JobCreateSerializer` |
| Blocklist + gender + same-day-availability filtering | `jobs.matching.eligible_cleaners` |
| Ranked shortlist (proximity, workload, rating, availability) | `jobs.matching.build_shortlist` |
| Admin reviews shortlist, assigns or overrides | `JobViewSet.shortlist` / `JobViewSet.assign` |
| SMS + push offer, accept/decline | `notifications.services.notify_job_offer`, `JobViewSet.respond` |
| Post-acceptance detail packet, access code reveal | `JobViewSet.packet`, `Job.access_code_visible_to` |
| Colour-coded (red/orange/green) dashboard | `Job.urgency` property, `AdminDashboard.jsx` |
| Audit log | `audit` app — every sensitive action calls `audit.utils.log_action` |

## Getting started

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in DJANGO_SECRET_KEY, DB_*, FIELD_ENCRYPTION_KEY
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Generate the field-encryption key referenced in `.env`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://localhost:8000`, so run the
backend first (or edit `vite.config.js` if it's hosted elsewhere).

## Security notes

- Every endpoint checks `request.user.role` server-side — role is never
  trusted from the client, and object-level ownership is enforced in each
  viewset's `get_queryset`/`get_permissions` (see `common/permissions.py`).
- Access codes are stored via `common.encryption.EncryptedTextField`
  (Fernet/AES) and only decrypt into API responses when
  `Job.access_code_visible_to()` says so — accepted-but-not-completed, and
  only for the assigned cleaner or an admin. Every admin read of a code also
  writes an audit entry (`JobViewSet.access_code`).
- Login lockout after repeated failures lives in `common/lockout.py`, wired
  into both the password and OTP login views.
- `jobs.management.commands.backup_database` wraps `pg_dump` for scheduled,
  pruned backups — hook it up with cron or your platform's scheduler.

## What's scaffolded vs. what needs finishing

This is a working, end-to-end skeleton — real models, real endpoints, real
status transitions — rather than a mockup. Two things intentionally need
your input before production use:

1. **SMS "CONFIRM" replies**: `notifications/services.py` sends the offer;
   wiring an inbound webhook from Termii into `JobViewSet.respond` (so a
   text reply — not just the app — can accept a job) is a small addition
   once you have a Termii account and webhook URL.
2. **Real coordinates**: proximity ranking in `jobs/matching.py` expects
   `latitude`/`longitude` on both jobs and cleaners; geocode the
   `location_summary` on intake (or collect coordinates from the app's map
   picker) to get real distance-based ranking instead of the 0.5 neutral
   fallback.
