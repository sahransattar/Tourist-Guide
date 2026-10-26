# Explore India - Tourist Guide Progressive Web Application (PWA)

A full-stack **Tourist Guide Progressive Web Application (PWA)** developed with Python (Flask), MySQL, HTML5, Vanilla CSS3 (Glassmorphism theme), and JavaScript. Engineered for reliable local execution and production deployment on cloud platforms such as Vercel.

---

## 🌟 Key Features

### 👤 User Module
* **Secure Registration & Login**: Account creation with Werkzeug secure password hashing (`scrypt`) and session authentication.
* **Legacy Password Migration**: Transparently upgrades legacy plaintext passwords to secure hashes upon login without locking out existing accounts.
* **Interactive Home Dashboard**: Search hero banner, system statistics, and featured destinations.
* **Browse & Search Places**: Filter tourist destinations by keyword or category (Heritage, Palace, Beach, Nature, Spiritual, Adventure).
* **Detailed Destination View**: Historical descriptions, timings, entry fees, category tags, and direct Google Maps links.
* **Favorites Management**: Save favorite destinations with real-time AJAX bookmarking and per-user session isolation.

### 🛡️ Admin Module & Security
* **Protected Admin Portal**: Centralized `@admin_required` server-side access control.
* **Zero Hardcoded Secrets**: Admin credentials and session keys configured via environment variables.
* **Brute-Force Rate Limiting**: Built-in sliding-window rate limiter protecting login endpoints against brute-force attacks.
* **Full CRUD Management**: Add new destinations, edit existing details, and delete destinations with cascading foreign key cleanup.
* **User Directory**: View registered user accounts and system metrics.
* **CSRF Protection**: Token validation on all state-changing forms and AJAX API requests.

### ⚡ PWA Capabilities & Offline Support
* **Service Worker Caching**: Pre-caches static assets (CSS, JS, images) and dynamically caches visited public destinations.
* **Sensitive Route Protection**: Never caches authenticated sessions, admin pages, passwords, or user credentials.
* **Offline Fallback Page**: Custom offline template displayed when network requests fail.
* **Web App Manifest**: Installable on Android, iOS, and Desktop as a standalone application.
* **Network Status Badge**: Real-time indicator displaying network status (`● Online` / `⚡ Offline Mode`).

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | HTML5, Vanilla CSS3 (Glassmorphism design system), JavaScript (ES6+) |
| **Backend** | Python 3, Flask framework, PyMySQL, Cryptography, Werkzeug |
| **Database** | Persistent MySQL in Production (`tourist_guide_db`) + Local SQLite fallback for development |
| **PWA** | Web App Manifest, Service Worker API, Cache Storage API |
| **Icons & Fonts** | FontAwesome 6, Google Fonts (Plus Jakarta Sans & Playfair Display) |

---

## 📁 Project Folder Structure

```text
TouristGuide/ (c:\PWA Project)
├── static/
│   ├── css/
│   │   └── style.css            # Custom CSS design system (Glassmorphism, animations)
│   ├── js/
│   │   ├── main.js              # Navbar toggle, auto-dismiss alerts, admin modals
│   │   ├── favorites.js         # Favorite add/remove AJAX handler with CSRF header
│   │   └── pwa.js               # Service Worker registration & install prompt
│   ├── images/                  # Tourist place images & PWA icons
│   │   ├── icon-192.png
│   │   ├── icon-512.png
│   │   └── places/              # Destination photography
│   ├── manifest.json            # PWA Web App Manifest configuration
│   ├── service-worker.js        # Offline caching strategy with sensitive route bypass
│   └── offline.html             # Offline fallback page
├── templates/
│   ├── base.html                # Master layout template (CSRF meta tag, navbar, footer)
│   ├── index.html               # Home page
│   ├── places.html              # Browse & Filter Tourist Places
│   ├── details.html             # Place details view
│   ├── favorites.html           # Saved favorites page
│   ├── login.html               # User login form
│   ├── register.html            # User registration form
│   ├── admin_login.html         # Admin login form
│   └── admin.html               # Admin dashboard (Add/Edit/Delete modals)
├── tests/
│   └── test_app.py              # Automated test suite (Registration, Auth, Admin, CSRF, PWA)
├── app.py                       # Flask server & routes with CSRF and rate limiting
├── database.py                  # Database abstraction (Production MySQL & Local SQLite fallback)
├── schema.sql                   # MySQL database creation & seed data script
├── generate_images.py           # Sample asset generator script
├── requirements.txt             # Python dependencies
├── vercel.json                  # Vercel deployment configuration
└── README.md                    # Project documentation & deployment guide
```

---

## 🔐 Required Environment Variables

Never commit real passwords or secret keys into source code or Git. Configure these variables in your local environment or in Vercel:

| Environment Variable | Required in Production? | Description | Example / Placeholder |
| :--- | :---: | :--- | :--- |
| `SECRET_KEY` | **Yes** | Flask session encryption key | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ADMIN_USERNAME` | **Yes** | Admin portal username | `admin` |
| `ADMIN_PASSWORD_HASH` | **Yes** | Werkzeug secure hash of admin password | `scrypt:32768:8:1$...` |
| `DATABASE_URL` | Optional (or use `MYSQL_*`) | Single connection URL for cloud MySQL | `mysql://user:pass@host.region.provider.com:3306/db?ssl-mode=REQUIRED` |
| `MYSQL_HOST` | **Yes** (if no `DATABASE_URL`) | MySQL hostname | `gateway01.ap-southeast-1.prod.aws.tidbcloud.com` |
| `MYSQL_PORT` | No (default `3306`) | MySQL port | `4000` or `3306` |
| `MYSQL_USER` | **Yes** (if no `DATABASE_URL`) | MySQL database username | `your_db_username` |
| `MYSQL_PASSWORD` | **Yes** (if no `DATABASE_URL`) | MySQL database password | `your_db_password` |
| `MYSQL_DB` | **Yes** (if no `DATABASE_URL`) | MySQL database name | `tourist_guide_db` |
| `MYSQL_SSL` | Optional | Enable TLS/SSL connection (required by most cloud providers) | `true` |

---

## 🛠️ Generating Secrets and Password Hashes

Run these commands in your terminal to generate secure production values:

### 1. Generate Flask `SECRET_KEY`
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Generate `ADMIN_PASSWORD_HASH`
Replace `YourStrongPasswordHere` with your chosen admin password:
```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('YourStrongPasswordHere'))"
```
Copy the printed output (e.g., `scrypt:32768:8:1$...`) and set it as `ADMIN_PASSWORD_HASH`.

---

## 💻 Local Development Setup

### 1. Install Dependencies
```bash
cd "c:\PWA Project"
python -m pip install -r requirements.txt
```

### 2. Start Local Server
By default, the application runs locally using an embedded SQLite database (`tourist_guide.db`) pre-seeded with sample destinations:
```bash
python app.py
```
Visit **`http://127.0.0.1:5000`** in your browser.

### 3. Run Automated Tests
```bash
python -m unittest tests/test_app.py
```

---

## 🚀 Vercel Production Deployment Guide

Vercel functions run in serverless containers with a **read-only filesystem**. Storing a local SQLite database file in the project folder will cause `attempt to write a readonly database` errors whenever a user registers. A persistent external database is required in production.

### Step 1: Create a Free Cloud MySQL Database
You can obtain a free, managed cloud MySQL database from any of the following providers:
* **TiDB Cloud** (Free Serverless Tier — Recommended, 5GB storage, 99.99% uptime, built-in SSL)
* **Aiven for MySQL** (Free tier)
* **Clever Cloud** or **Railway** (Free MySQL addon)

### Step 2: Initialize Database Tables
Run the [`schema.sql`](file:///c:/PWA%20Project/schema.sql) script in your cloud database provider's web SQL console, or allow the application to automatically create tables on first run via `database.py`.

### Step 3: Configure Environment Variables in Vercel
1. Log into your [Vercel Dashboard](https://vercel.com/).
2. Select your **`tourist-guide`** project.
3. Navigate to **Settings** -> **Environment Variables**.
4. Add the following variables:
   * `SECRET_KEY` = `<your_generated_hex_secret>`
   * `ADMIN_USERNAME` = `admin`
   * `ADMIN_PASSWORD_HASH` = `<your_generated_scrypt_hash>`
   * `DATABASE_URL` = `mysql://<user>:<password>@<host>:<port>/<dbname>?ssl-mode=REQUIRED`
     *(Or individually: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`, `MYSQL_SSL=true`)*

### Step 4: Redeploy on Vercel
1. In Vercel Dashboard, go to the **Deployments** tab.
2. Click **Redeploy** on the latest deployment (or push a new commit to your connected GitHub repository).
3. Once the deployment finishes, visit:
   `https://tourist-guide-mu.vercel.app/api/health`
4. Confirm the response:
   ```json
   {
     "status": "healthy",
     "database": {
       "active_engine": "mysql",
       "configured_engine": "mysql",
       "connected": true,
       "environment": "production",
       "is_vercel": true
     }
   }
   ```

### Step 5: Troubleshooting & Inspecting Logs
If registration or database operations ever encounter an issue:
1. In the Vercel Dashboard, navigate to **Deployments** -> Click on your active deployment -> **Functions** (or **Logs**).
2. Filter by `[DATABASE ERROR]` or `[SECURITY WARNING]`.
3. The server logs provide safe, detailed diagnostic information without exposing user passwords or sensitive tokens.
