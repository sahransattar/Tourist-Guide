# Explore India - Tourist Guide Progressive Web Application (PWA)

A full-stack **Tourist Guide Progressive Web Application (PWA)** developed with Python (Flask), MySQL, HTML5, Vanilla CSS3 (Glassmorphism design system), and JavaScript (ES6+). Engineered for reliable local execution, robust security, and cloud deployment on serverless platforms such as Vercel.

**Live Deployment:** https://tourist-guide-mu.vercel.app/  
**Academic Level:** BCA Final-Year Academic Project  
**Repository Working Directory:** `c:\PWA Project`

---

## 🌟 Key Features & Functional Modules

### 👤 1. User & Traveler Module
* **Secure Registration & Authentication**: User account registration with Werkzeug cryptographic password hashing (`scrypt`).
* **Transparent Password Migration**: Seamlessly upgrades legacy plaintext passwords to secure hashes upon login without locking out existing accounts.
* **Interactive Home Dashboard**: Hero banner, system statistics, category pill shortcuts, and featured destinations.
* **Search, Filtering, Sorting & Pagination**:
  * Multi-field search querying across destination name, location, and description.
  * Category filtering (Heritage, Palace, Beach, Nature, Spiritual, Adventure).
  * Dynamic sorting: Name (A-Z), Name (Z-A), Newest Added, and Oldest First.
  * Responsive client-side and server-side pagination with previous/next controls.
* **Extensive Destination Database (90+ Curated Places)**:
  * Over 90 authentic, verified Indian destinations spanning all major states and union territories.
  * Real GPS coordinates, visiting hours, ticket prices, and categories.
  * Hybrid image URL resolver supporting local files and remote CDN/Unsplash photography with graceful fallback.
* **Destination Details Page**:
  * Semantic breadcrumb navigation.
  * Geographic GPS coordinates display.
  * Real-time Google Maps integration ("Get Directions").
  * Web Share API integration with automatic fallback to clipboard copy.
  * Visitor guidelines (visiting hours, entry fee structure, travel category, photography rules).
  * Context-aware related destinations recommendation.
* **Favorites Management**:
  * One-click AJAX bookmarking with animated heart indicators.
  * Strictly isolated to the authenticated user's session.
  * Dynamic card removal on the favorites view with graceful empty state.

### 🗺️ 2. Trip Planner & Multi-Day Itinerary Builder
* **Custom Travel Itinerary Creation**: Users can create personalized travel plans with trip titles, descriptions, and travel date ranges.
* **Multi-Day Stop Organization**: Add destination stops to any day (Day 1, Day 2, Day 3) along with personalized visit notes directly from destination cards or detail pages.
* **Multi-Stop Google Maps Route Generation**: Automatically chains all stops in an itinerary into a unified Google Maps navigation link (`origin`, `destination`, and intermediate `waypoints`).
* **Print & Export Ready**: Specially designed `@media print` CSS stylesheet generates clean, paper/PDF-ready travel vouchers hiding navigation headers and floating banners.
* **Global Quick Add Modal**: Add any destination to any existing trip in one click from browse cards or detail views without leaving the page.

### 📍 3. Geolocation & Proximity Detection Module
* **Haversine Distance Formula**: Python backend computes great-circle distance between two geographic coordinates:
  $$d = 2r \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)}\right)$$
* **Voluntary Geolocation API**: Browser requests user location access voluntarily; denies gracefully if permission is withheld.
* **Nearby API Endpoint (`/api/nearby`)**: Accepts `lat` and `lng` query parameters, calculates distance in kilometers to each tourist attraction, and returns results sorted from nearest to farthest.

### 🛡️ 3. Security, Authorization & Hardening
* **Server-Side Admin Control**: Centralized `@admin_required` decorator guarding all admin views and mutations.
* **Zero Hardcoded Credentials**: Administrative credentials and Flask secret keys are loaded exclusively from environment variables (`ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`, `SECRET_KEY`).
* **Session-Bound CSRF Protection**: Cryptographic token generation (`secrets.token_hex(32)`) and validation on all state-changing HTTP requests (`POST`, `PUT`, `DELETE`).
* **Brute-Force Rate Limiting**: In-memory sliding-window limiter on `/login` and `/admin/login` (maximum 5 failed attempts per 5-minute window per IP).
* **Session Security**: Session cookies configured with `HttpOnly`, `SameSite='Lax'`, and dynamic `Secure` in production environments. Sessions are cleared on login and logout to defeat session fixation.
* **Parameterized SQL Queries**: All database queries use parameter placeholders (`%s` for MySQL, `?` for SQLite) to prevent SQL Injection attacks.
* **Safe Error Handling**: Polished custom 404 (`templates/404.html`) and 500 (`templates/500.html`) pages. Zero exposure of internal stack traces, connection strings, or credentials to client browsers.

### ⚡ 4. PWA Capabilities & Offline Reliability
* **Service Worker Caching (v2.0)**: Pre-caches critical app shell, stylesheets, icons, and destination photography.
* **Cache-First for Static Assets**: Ultra-fast loading of CSS, JavaScript, and imagery from Cache Storage.
* **Network-First for Dynamic Data**: Tourist places data updates gracefully with cache fallbacks.
* **Sensitive Route Caching Bypass**: Authenticated pages (`/admin`, `/login`, `/register`, `/logout`, `/favorites`, `/api/favorites`) bypass service worker caches to prevent credential leakage and stale state.
* **Offline Fallback Page**: Custom offline template displayed when network requests fail while completely disconnected.
* **Installable Application**: Web App Manifest (`manifest.json`) enabling home screen installation on Android, iOS, Windows, and macOS.
* **Real-Time Network Status**: Live visual indicator in the navbar (`● Online` / `⚡ Offline Mode`).

---

## 🛠️ Technology Stack Architecture

| Layer | Component | Technologies |
| :--- | :--- | :--- |
| **Frontend** | User Interface & Presentation | HTML5, CSS3 (Glassmorphism design tokens, CSS Grid, Flexbox), Vanilla JavaScript (ES6+), FontAwesome 6, Google Fonts |
| **PWA** | Offline & Client Storage | Web App Manifest, Service Worker API, Cache Storage API |
| **Backend** | Application Server & REST API | Python 3, Flask framework, Werkzeug security |
| **Database** | Persistent Data Storage | PyMySQL, Cryptography (`caching_sha2_password`), Managed MySQL in Production (TiDB Cloud / Aiven) + SQLite for local development |
| **Deployment**| Cloud Hosting | Vercel Serverless Functions (`vercel.json`) |

---

## 📁 Project Directory Structure

```text
TouristGuide/ (c:\PWA Project)
├── static/
│   ├── css/
│   │   └── style.css            # Glassmorphism design system, responsive styles, pagination
│   ├── js/
│   │   ├── main.js              # Navbar toggle, alert dismiss, modals, table search, geolocation, Web Share
│   │   ├── favorites.js         # Favorite add/remove AJAX handler with CSRF header
│   │   └── pwa.js               # Service Worker registration & install prompt handler
│   ├── images/                  # Destination photography & PWA icons
│   │   ├── icon-192.png
│   │   ├── icon-512.png
│   │   └── *.jpg                # Taj Mahal, Jaipur, Goa, Kerala, Varanasi, Pangong
│   ├── manifest.json            # PWA Web App Manifest configuration
│   ├── service-worker.js        # Offline caching strategy with sensitive route bypass (v2.0)
│   └── offline.html             # Offline fallback page
├── templates/
│   ├── base.html                # Master layout template (CSRF meta tag, navbar, PWA floating card, add-to-trip modal)
│   ├── index.html               # Home page (Hero, stats, categories, nearby widget, featured grid)
│   ├── places.html              # Browse, filter, sort, and paginate 90+ destinations
│   ├── details.html             # Place details view (Directions, GPS coords, Web Share, visitor guide, add-to-trip)
│   ├── favorites.html           # Saved favorites page
│   ├── itinerary.html           # Trip planner dashboard (Create trips, list active itineraries)
│   ├── itinerary_detail.html    # Itinerary day-by-day plan, print voucher, multi-stop Google Maps route
│   ├── login.html               # User login form
│   ├── register.html            # User registration form
│   ├── admin_login.html         # Admin login form
│   ├── admin.html               # Admin dashboard (Instant search, Add/Edit with coords, Delete)
│   ├── 404.html                 # Custom 404 Not Found error page
│   └── 500.html                 # Custom 500 Internal Server Error page
├── tests/
│   └── test_app.py              # Automated test suite (27 unit tests covering auth, CRUD, nearby, CSRF, itineraries)
├── app.py                       # Flask server & routes with CSRF, rate limiting, and Haversine API
├── database.py                  # Database abstraction (Production MySQL & Local SQLite fallback)
├── seed_destinations.py         # Curated 91-destination seed script for database expansion
├── schema.sql                   # MySQL database creation & seed data script with GPS coordinates
├── generate_images.py           # Sample asset generator script
├── requirements.txt             # Python dependencies
├── vercel.json                  # Vercel deployment configuration
└── README.md                    # Project documentation & deployment guide
```

---

## 🔐 Environment Variables Specification

Never commit passwords or secret tokens into Git. Configure these variables in your hosting provider (Vercel) or local environment:

| Variable | Required in Production? | Description | Example / Generator |
| :--- | :---: | :--- | :--- |
| `SECRET_KEY` | **Yes** | Flask session encryption key | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ADMIN_USERNAME` | **Yes** | Admin portal username | `admin` |
| `ADMIN_PASSWORD_HASH` | **Yes** | Werkzeug secure hash of admin password | `python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('StrongPassword123!'))"` |
| `DATABASE_URL` | Optional | Complete MySQL connection URI | `mysql://user:pass@host:4000/db?ssl-mode=REQUIRED` |
| `MYSQL_HOST` | **Yes** (if no `DATABASE_URL`) | Hostname of MySQL server | `gateway01.ap-southeast-1.prod.aws.tidbcloud.com` |
| `MYSQL_PORT` | No (default `3306`) | Port of MySQL server | `4000` or `3306` |
| `MYSQL_USER` | **Yes** (if no `DATABASE_URL`) | Database username | `your_user` |
| `MYSQL_PASSWORD` | **Yes** (if no `DATABASE_URL`) | Database password | `your_password` |
| `MYSQL_DB` | **Yes** (if no `DATABASE_URL`) | Database name | `tourist_guide_db` |
| `MYSQL_SSL` | Optional | Enforce SSL / TLS connection | `true` |

---

## 💻 Local Development Setup

### 1. Prerequisites
* Python 3.9+
* pip

### 2. Install Dependencies
```bash
cd "c:\PWA Project"
python -m pip install -r requirements.txt
```

### 3. Seed Expanded Destinations (90+ Places)
```bash
python seed_destinations.py
```

### 4. Run Automated Test Suite
Run the 27 automated unit tests:
```bash
python -m unittest tests/test_app.py
```

### 5. Start Local Development Server
```bash
python app.py
```
```
Open **`http://127.0.0.1:5000`** in any web browser.

---

## 🚀 Cloud Production Deployment (Vercel)

### Why Vercel requires an external database:
Vercel serverless functions execute inside ephemeral Docker containers where the filesystem is **read-only (`/var/task`)**. Storing an embedded SQLite file causes runtime write exceptions (`attempt to write a readonly database`) whenever a user registers or saves a favorite. A managed external MySQL database solves this permanently.

### Step 1: Provision a Free Cloud MySQL Database
1. Go to [TiDB Cloud](https://tidbcloud.com/) (or [Aiven](https://aiven.io/)) and create a free Serverless Tier cluster.
2. Select your closest AWS or Google Cloud region.
3. Note your connection details (Host, Port, User, Password, Database Name).

### Step 2: Configure Environment Variables in Vercel
1. Log into your [Vercel Dashboard](https://vercel.com/) and open the **`tourist-guide`** project.
2. Go to **Settings** -> **Environment Variables**.
3. Add the following variables:
   * `SECRET_KEY` = `<your_hex_secret>`
   * `ADMIN_USERNAME` = `admin`
   * `ADMIN_PASSWORD_HASH` = `<your_generated_scrypt_hash>`
   * `MYSQL_HOST` = `<your_cloud_host>`
   * `MYSQL_PORT` = `4000` (or `3306`)
   * `MYSQL_USER` = `<your_db_username>`
   * `MYSQL_PASSWORD` = `<your_db_password>`
   * `MYSQL_DB` = `tourist_guide_db`
   * `MYSQL_SSL` = `true`

### Step 3: Redeploy and Verify Health
1. In Vercel, go to the **Deployments** tab and click **Redeploy**.
2. Once complete, visit the health monitoring endpoint:
   `https://tourist-guide-mu.vercel.app/api/health`
3. Verify that the response returns HTTP 200 with `connected: true`:
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

---

## 🎓 BCA Academic Viva-Voce & Presentation Guide

### Frequently Asked Questions by Project Examiners

#### Q1: What is a Progressive Web Application (PWA) and why is it beneficial for tourism?
> **Answer**: A Progressive Web Application is a web application that utilizes modern browser APIs—primarily Web App Manifest and Service Workers—to deliver native-app-like experiences. In tourism, travelers often experience intermittent or non-existent cellular connectivity in remote heritage areas or mountain regions. Explore India PWA caches destination descriptions, coordinates, visiting hours, and imagery, allowing tourists to access vital guide information completely offline without having to download a large native app from an app store.

#### Q2: What caused the registration bug on Vercel and how did you resolve it?
> **Answer**: The live registration failure was caused by Vercel's serverless architecture, which enforces a strictly read-only filesystem (`/var/task`). The original codebase attempted to write user registrations to an embedded SQLite file on this read-only disk, triggering the exception `attempt to write a readonly database`. We resolved this by re-architecting the database layer in `database.py` to connect to a managed external cloud MySQL database using SSL/TLS encryption in production while maintaining a convenient SQLite fallback for offline local development.

#### Q3: How is user password security handled?
> **Answer**: Plaintext passwords are never stored. Passwords are cryptographically salted and hashed using Werkzeug's `scrypt` algorithm (`generate_password_hash` and `check_password_hash`). To preserve user accounts without disruption, we implemented a transparent migration routine: on their next successful login, legacy plaintext accounts are automatically upgraded to secure hashes in the database.

#### Q4: How does the "Nearby Destinations" feature compute distances?
> **Answer**: The feature uses the mathematical **Haversine formula** implemented in Python (`haversine(lat1, lon1, lat2, lon2)`). When the user voluntarily permits browser Geolocation (`navigator.geolocation.getCurrentPosition`), their latitude and longitude are submitted to `/api/nearby`. The server calculates the spherical distance in kilometers between the user's coordinates and all tourist places, returning the closest attractions sorted in ascending distance order.

#### Q5: How is CSRF (Cross-Site Request Forgery) mitigated?
> **Answer**: We implemented session-bound cryptographic CSRF tokens using `secrets.token_hex(32)`. Every state-changing HTML form includes a hidden `csrf_token` input field, and AJAX requests transmit the token via the `X-CSRFToken` HTTP header. The `@app.before_request` hook validates the submitted token against the active session's expected token using timing-safe comparison (`secrets.compare_digest`).

#### Q6: How does the Trip Planner & Itinerary Builder function?
> **Answer**: The Trip Planner is a relational database module comprising `itineraries` and `itinerary_items` linked by foreign keys with cascading deletions. Authenticated users can create trips and add destination stops categorized by day numbers with personal notes. The application dynamically compiles these stops and generates a multi-point Google Maps navigation URL (`origin`, `destination`, and `waypoints`) so travelers can execute their daily routes with live turn-by-turn navigation.

#### Q7: How does the PWA installation prompt avoid degrading user experience?
> **Answer**: Rather than displaying a full-width fixed banner that blocks navigation menus, footers, and interactive controls, Explore India uses a floating, responsive card (`.pwa-floating-card`) anchored to the bottom-right corner. It listens for the browser's `beforeinstallprompt` event and includes a clear dismiss action with `sessionStorage` persistence, preventing repetitive intrusive prompts across page navigations.
