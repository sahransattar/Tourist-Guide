# Explore India - Tourist Guide Progressive Web Application (PWA)

A complete, modern, and beginner-friendly **Tourist Guide Progressive Web Application (PWA)** developed for final-year BCA (Bachelor of Computer Applications) projects. Built with **Python (Flask)** backend, **MySQL** database, HTML5, CSS3, Vanilla JavaScript, and **PWA Cache API & Service Workers**.

---

## 🌟 Key Features

### 👤 User Module
* **User Registration & Login**: Account creation with session-based authentication.
* **Interactive Home Dashboard**: Hero search banner, system statistics, and featured destinations.
* **Browse & Search Places**: Filter tourist destinations by keywords or category (Heritage, Palace, Beach, Nature, Spiritual, Adventure).
* **Detailed View**: View place history, visiting timings, ticket entry fees, category tags, and direct Google Maps links.
* **Favorites Management**: Save favorite destinations to a personal collection with one-click AJAX toggling.

### 🛡️ Admin Module
* **Admin Portal**: Secure login (`admin` / `admin123`).
* **Manage Tourist Destinations**: Full CRUD capabilities — Add new tourist places, edit existing place details, and delete entries.
* **User Directory**: View registered user accounts and system usage metrics.

### ⚡ PWA Capabilities & Offline Support
* **Service Worker Caching**: Caches static assets (CSS, JS, Images) and visited HTML pages.
* **Offline Favorites & Details**: Saved places remain accessible even without an active internet connection.
* **Offline Fallback Page**: Custom offline template displayed when network requests fail.
* **Web App Manifest**: Installable on Android, iOS, and Desktop as a native standalone app.
* **Offline Status Badge**: Real-time indicator displaying network status (`Online` / `Offline Mode`).

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | HTML5, Vanilla CSS3 (Glassmorphism design system), JavaScript (ES6+) |
| **Backend** | Python 3, Flask framework, PyMySQL |
| **Database** | MySQL (`tourist_guide_db`) + Automatic SQLite fallback (`tourist_guide.db`) |
| **PWA** | Web App Manifest, Service Worker API, Cache Storage API |
| **Icons & Fonts** | FontAwesome 6, Google Fonts (Plus Jakarta Sans & Playfair Display) |

---

## 📁 Project Folder Structure

```text
TouristGuide/ (c:\PWA Project)
├── static/
│   ├── css/
│   │   └── style.css            # Glassmorphism theme, animations, responsive design
│   ├── js/
│   │   ├── main.js              # Navbar toggle, auto-dismiss alerts, admin modals
│   │   ├── favorites.js         # Favorite add/remove AJAX handler & toast alerts
│   │   └── pwa.js               # Service Worker registration & install prompt
│   ├── images/                  # Tourist place images & PWA icons
│   │   ├── icon-192.png
│   │   ├── icon-512.png
│   │   └── places/              # Destination images
│   ├── manifest.json            # PWA Web App Manifest configuration
│   ├── service-worker.js        # Offline caching strategy & SW lifecycle
│   └── offline.html             # Offline fallback page
├── templates/
│   ├── base.html                # Main master layout template
│   ├── index.html               # Home page
│   ├── places.html              # Browse & Filter Tourist Places
│   ├── details.html             # Place details view
│   ├── favorites.html           # Saved favorites page
│   ├── login.html               # User login form
│   ├── register.html            # User registration form
│   ├── admin_login.html         # Admin login form
│   └── admin.html               # Admin dashboard (CRUD operations)
├── app.py                       # Flask application server & routing logic
├── database.py                  # Database connection layer (MySQL + SQLite fallback)
├── schema.sql                   # MySQL database creation & sample data script
├── generate_images.py           # Sample asset generator script
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation & setup instructions
```

---

## 🚀 Installation & Setup Instructions

### Prerequisites
* **Python 3.8+** installed on your system.
* **MySQL Server** (Optional if using default SQLite fallback mode).

### Step 1: Clone / Navigate to Project Directory
```bash
cd "c:\PWA Project"
```

### Step 2: Install Python Dependencies
```bash
python -m pip install -r requirements.txt
```

### Step 3: Database Setup

#### Option A: Using MySQL Database (Recommended for Project Submission)
1. Open MySQL Workbench or Command Line Client.
2. Run the `schema.sql` script to create the database and sample tables:
   ```sql
   SOURCE c:/PWA Project/schema.sql;
   ```
3. Set your MySQL credentials as environment variables or in `database.py`:
   * `MYSQL_HOST` (default: `localhost`)
   * `MYSQL_USER` (default: `root`)
   * `MYSQL_PASSWORD` (default: ``)
   * `MYSQL_DB` (default: `tourist_guide_db`)

#### Option B: Automatic SQLite Mode (Zero-Config Test Drive)
* If MySQL is not running on your machine, `database.py` automatically detects it and creates an embedded `tourist_guide.db` SQLite database populated with all tables and sample tourist places!

---

## 🏃 Running the Application

1. Start the Flask server:
   ```bash
   python app.py
   ```
2. Open your web browser and navigate to:
   ```text
   http://127.0.0.1:5000
   ```

---

## 🔑 Default User Credentials

| Role | Username / Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Full Dashboard & CRUD |
| **User** | `john@example.com` | `user123` | Browse, Search, Favorites |

---

## 📱 Testing PWA Offline Support & Installation

1. **Install App to Home Screen / Desktop**:
   * Click the **"Install Now"** banner at the bottom of the page or the install icon in your browser's address bar.
2. **Offline Testing via Chrome DevTools**:
   * Press `F12` to open Developer Tools.
   * Go to the **Application** tab -> **Service Workers**.
   * Check the **Offline** checkbox.
   * Reload the page or click around. Notice how visited places, favorites, and static styles load seamlessly offline!
