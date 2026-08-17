# Password Hygiene Tracker

A full-stack Flask app that helps you keep track of when you last updated the password for each of your accounts, reminds you to periodically review account security, and includes a standalone password strength & breach checker to help you evaluate a current or candidate password.

**No password is ever stored or sent to the backend, including candidate passwords being tested.**

## Purpose

- **Account tracker (CRUD):** Add accounts (e.g. "Gmail," "Bank"), view them on a dashboard, edit them, or delete them.

- **Two-clock review system:** Each account tracks two separate timestamps:

  - `last_updated` - the last time you confirmed that you actually changed the password
  - `last_reviewed` - the last time you explicitly reviewed the account's password security or dismissed its review reminder

  These are intentionally separate. A status badge (`ok` / `review-soon` / `review-recommended`) is driven by `last_reviewed`, not `last_updated`. See Why two timesamps below.

- **Password strength & breach checker:** A standalone tool for evaluating candidate passwords when choosing or changing a password:

  - Real-time strength scoring as you type, powered by [zxcvbn](https://github.com/dropbox/zxcvbn)
  - Breach checking against [Have I Been Pwned's Pwned Passwords API](https://haveibeenpwned.com/API/v3#PwnedPasswords), using k-anonymity so the full password or hash never leaves the browser


## Why no passwords are stored

This was feature was a deliberate design constraint. The account tracker's database schema has no password field, no password-hash field, and no breach-check history containing password-derived data. The checker is stateless so that nothing it processes is written to the database.

Design choices making that possible:

1. **The breach check is client-side.**
   The candidate password is hashed with SHA-1 in the browser using the Web Crypto API. Only the **first 5 characters** of that hash are sent to HIBP's Pwned Passwords API.

   HIBP returns the suffixes of hashes sharing that prefix, and the comparison against the remaining hash characters happens locally in the browser. HIBP therefore never receives the full hash or plaintext password.

   This is the k-anonymity model used by the Pwned Passwords range API.

   **SHA-1 is used here only because it is part of HIBP's lookup protocol - it is never used by this application to store or authenticate passwords.**

2. **The strength calculation stays in the browser.**
   zxcvbn is a JavaScript password-strength estimator loaded from a CDN and executed client-side. The candidate password is evaluated locally rather than being sent to this app's backend for strength scoring.

When an account review is recorded, the backend receives only the account identifier and the fact that the account was reviewed. No password or password-derived data is included. That event is used solely to update `last_reviewed`.

## Why two timestamps

The original design used a single "last updated" timestamp and an "overdue" badge based on a set rotation interval of 90 days.

That approach conflicts with current [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html) guidance, which advises against requiring periodic password changes. NIST recommends that password changes occure when there is evidence that an authenticator has been compromised.

The app therefore treats its status badge as a **reminder to review an account**, and does not urge a password be changed.

That distinction is why the two timestamps are kept separate:

- `last_reviewed` resets when accounts password security is checked for breaches, or when the reminder is dismissed by user
- `last_updated` when user confirms actually updating their password

Reaching the review threshold does not require a password change. The user can review the account's security and, if they want to, use the standalone checker while choosing a new password, or explicitly dismiss the reminder.

Both review actions reset `last_reviewed`. Only confirming that a password was actually changed resets `last_updated`.

Actions that reset a reminder require an explicit confirmation step using a JavaScript `confirm()` dialog so an accidental click cannot automatically reset it if it was accidentally clicked.

`last_updated` remains visible on the dashboard independently of the review badge, so the user can still see how long it has been since the password was actually changed.

## Tech stack

| Layer | Technology |
| --- | --- |
| Backend | Flask, Flask-SQLAlchemy |
| Database | SQLite |
| Templates | Jinja2 |
| Styling | Sass/SCSS (gets compiled to CSS) |
| Strength checking | [zxcvbn](https://github.com/dropbox/zxcvbn) - client-side JavaScript |
| Breach checking | [HIBP Pwned Passwords API](https://haveibeenpwned.com/API/v3#PwnedPasswords) - public range endpoint |
| Client-side hashing | Web Crypto API (`crypto.subtle.digest`) |

## Run instructions

```bash
# clone the repo
git clone <repo-url>
cd <repo-folder>

# set up a virtual environment
python -m venv env

source env/bin/activate   # macOS/Linux
# env\Scripts\activate    # Windows

# install dependencies
pip install -r requirements.txt

# run the app
python app.py
```

The app runs on `http://127.0.0.1:5000` by default (if port `5000` conflicts with another local service, change port under "#runner and debugger" at the end of "app.py"). The SQLite database is created automatically on first run.


## Known limitations  

- **No user authentication.** This is currently a single shared dataset with no login, so anyone accessing the app can see and modify the same account list. This is a deliberate scope boundary planned for future implimentation. A multi-user deployment would require a `User` model, session-based authentication, and account queries scoped to the authenticated user.

- **Timezone display.** Timestamps are stored and computed in UTC. Converting displayed timestamps to the viewer's local timezone using browser side localization is planned. 

## Data sources & attribution

The project intentionally does not implement its own password-strength algorithm.

Password rules that require one uppercase letter, one number, and one symbol are a poor substitute for estimating how resistant a password is to realistic guessing strategies. This project uses [zxcvbn](https://github.com/dropbox/zxcvbn), a password strength estimator originally developed by Dropbox that checks passwords based on pattern matching and dictionaries. 

Breached password checking is provided through [Have I Been Pwned's Pwned Passwords API](https://haveibeenpwned.com/API/v3#PwnedPasswords) using its k-anonymity range-search model.
