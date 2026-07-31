# BCA Final Year Project Report: Tourist Guide Progressive Web Application (PWA)

---

## 1. ABSTRACT

In the modern digital era, travel and tourism applications have become indispensable tools for trip planning, destination discovery, and heritage exploration. However, many conventional web applications depend heavily on active, high-speed internet connections, leading to broken experiences when travelers visit remote locations or areas with unstable network connectivity. 

This project presents the design and implementation of a **Tourist Guide Progressive Web Application (PWA)**, engineered to deliver seamless travel information access online and offline. Developed using HTML5, CSS3, JavaScript, Python (Flask), and MySQL, the application leverages Service Workers, Web App Manifests, and the Cache API to enable full offline browsing of visited destinations and saved user favorites. The system is divided into a **User Module** for destination discovery and bookmarking, and an **Admin Module** for centralized place management and content administration.

---

## 2. PROJECT OBJECTIVES

* **Offline First Accessibility**: Utilize PWA Service Worker caching to store core static assets, HTML templates, and destination details for offline usability.
* **Responsive & Intuitive Interface**: Implement a modern dark glassmorphism design system adaptable across desktop computers, tablets, and smartphones.
* **Centralized Content Management**: Provide administrators with a secure portal to perform Create, Read, Update, and Delete (CRUD) operations on tourist destinations.
* **Personalized User Experience**: Enable registered users to maintain a personal collection of favorite tourist spots saved across sessions.
* **Installable Application**: Enable one-click installation on mobile devices and desktop operating systems without requiring native app store downloads.

---

## 3. SYSTEM REQUIREMENTS

### 3.1 Software Requirements
* **Operating System**: Windows 10/11, macOS, or Linux.
* **Programming Language**: Python 3.8 or higher.
* **Web Framework**: Flask 2.3+.
* **Database Management System**: MySQL 8.0 / PyMySQL (with automatic SQLite 3 fallback mode).
* **Front-End Technologies**: HTML5, CSS3, JavaScript (ES6+), FontAwesome 6.
* **Web Browser**: Google Chrome, Microsoft Edge, Safari, or Mozilla Firefox with PWA support.

### 3.2 Hardware Requirements
* **Processor**: Dual-Core Intel/AMD CPU @ 2.0 GHz or higher.
* **RAM**: 4 GB minimum (8 GB recommended).
* **Storage**: 500 MB available disk space.
* **Network**: Internet connection required for initial load and online updates.

---

## 4. SYSTEM ARCHITECTURE & DATA FLOW

```
                          +-------------------------+
                          |   User / Admin Browser  |
                          +------------+------------+
                                       |
                   +-------------------+-------------------+
                   | (HTTP Request)                        | (Offline Fallback)
                   v                                       v
        +----------------------+                +----------------------+
        |    Service Worker    | -------------> |     Cache Storage    |
        +----------+-----------+                |   (HTML, CSS, JS)    |
                   |                            +----------------------+
                   | (Online)
                   v
        +----------------------+
        | Flask App Controller |
        |      (app.py)        |
        +----------+-----------+
                   |
                   v
        +----------------------+
        | MySQL / SQLite Database|
        |   (database.py)      |
        +----------------------+
```

1. The client sends HTTP requests through the browser.
2. The **Service Worker** intercepts network requests:
   - If online: Fetches live data from the **Flask App Controller** and updates the cache.
   - If offline: Intercepts network failure and serves cached resources from **Cache Storage**.
3. The **Flask App Controller** executes business logic and retrieves data from the **MySQL Database**.

---

## 5. DATABASE DESIGN & SCHEMA

The system utilizes three core relational database tables: `users`, `tourist_places`, and `favorites`.

### 5.1 Table: `users`
Stores registered user accounts and authentication credentials.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `user_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique identifier for each user |
| `name` | VARCHAR(100) | NOT NULL | Full name of the user |
| `email` | VARCHAR(100) | UNIQUE, NOT NULL | User email address (login credential) |
| `password` | VARCHAR(255) | NOT NULL | Encrypted/Hashed user password |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Account creation timestamp |

### 5.2 Table: `tourist_places`
Stores information regarding tourist destinations.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `place_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique identifier for each destination |
| `name` | VARCHAR(150) | NOT NULL | Name of the tourist place |
| `location` | VARCHAR(150) | NOT NULL | City and State location |
| `description` | TEXT | NOT NULL | Detailed history and visitor overview |
| `timings` | VARCHAR(100) | DEFAULT '9:00 AM - 5:00 PM' | Visitor opening and closing hours |
| `entry_fee` | VARCHAR(100) | DEFAULT 'Free' | Ticket price details |
| `image` | VARCHAR(255) | DEFAULT 'default_place.jpg' | Image filename stored in static assets |
| `category` | VARCHAR(50) | DEFAULT 'Heritage' | Category tag (e.g., Heritage, Beach) |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |

### 5.3 Table: `favorites`
Junction table mapping saved places to registered users.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `favorite_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique favorite record ID |
| `user_id` | INT | FOREIGN KEY (users.user_id) | Associated user ID |
| `place_id` | INT | FOREIGN KEY (tourist_places.place_id)| Associated tourist place ID |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Bookmark creation timestamp |

---

## 6. MODULE DESCRIPTION

### 6.1 User Module
1. **User Registration & Authentication**: Users create an account specifying name, email, and password. Sessions are maintained via Flask secure cookies.
2. **Home Dashboard**: Displays a high-impact hero header, live stats counters, quick search bar, and featured destination cards.
3. **Search & Filter**: Allows users to perform real-time text matching against destination names, locations, and descriptions, or filter by category tags.
4. **Destination Details View**: Displays full-resolution hero photography, complete historical summaries, ticket prices, timings, and Google Maps location links.
5. **Favorites Collection**: Users can toggle favorite status via AJAX without reloading the page. Bookmarked places are saved to the user's account and cached for offline access.

### 6.2 Admin Module
1. **Admin Authentication**: Secure login gate (`admin` / `admin123`).
2. **Management Dashboard**: Provides high-level metrics including total destinations, registered user count, and total favorites saved.
3. **Create Place**: Modal form allowing administrators to add new destinations with location, category, timings, entry fees, description, and image filenames.
4. **Edit Place**: Dynamic modal dialog populated with existing place details for quick updates.
5. **Delete Place**: Removes a destination from the system with cascading foreign key deletion of linked favorites.

---

## 7. PWA IMPLEMENTATION & CACHING STRATEGIES

### 7.1 Web App Manifest (`manifest.json`)
The Web App Manifest defines metadata required for standalone mobile installation:
- `name`: "Explore India - Tourist Guide PWA"
- `display`: "standalone" (removes browser URL bar when launched)
- `theme_color`: "#0284c7"
- `icons`: 192x192 and 512x512 PNG app icons.

### 7.2 Service Worker Strategies (`service-worker.js`)
The Service Worker implements three distinct caching strategies based on request type:
1. **Pre-Caching App Shell (Cache First)**: During the `install` phase, core static assets (`style.css`, `main.js`, `favorites.js`, `manifest.json`, default images) are saved to Cache Storage.
2. **Dynamic HTML Page Caching (Network First, Cache Fallback)**: Navigation requests attempt to fetch live content from the network first. If successful, a clone of the response is stored in cache. If offline, the cached HTML page is served. If no cache exists, the user is redirected to `offline.html`.
3. **API Endpoints (Network First, Cache Fallback)**: `/api/places` responses are cached dynamically for offline client-side rendering.

---

## 8. TEST CASES AND VERIFICATION RESULTS

| Test Case ID | Feature Tested | Input / Condition | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC-01** | User Registration | Valid name, email, password | Account created in DB, redirected to login | **PASS** |
| **TC-02** | User Login | Valid credentials | Session initialized, redirected to Home | **PASS** |
| **TC-03** | Place Search | Keyword "Taj" | Returns Taj Mahal place card | **PASS** |
| **TC-04** | Toggle Favorite | Click heart icon on place card | Place added/removed in DB via AJAX, toast shown | **PASS** |
| **TC-05** | Admin Login | `admin` / `admin123` | Access granted to Admin Dashboard | **PASS** |
| **TC-06** | Admin Add Place | Fill modal form & submit | New place record created, appears in table | **PASS** |
| **TC-07** | Service Worker Reg | Load page in Chrome | SW registered successfully in DevTools | **PASS** |
| **TC-08** | Offline Browsing | Set DevTools to Offline | Visited pages & favorites render from Cache Storage | **PASS** |

---

## 9. CONCLUSION & FUTURE ENHANCEMENTS

### 9.1 Conclusion
The **Tourist Guide Progressive Web Application (PWA)** successfully demonstrates how modern web standards, service workers, and lightweight backend frameworks can be combined to solve network dependency challenges in travel applications. The project fulfills all functional requirements for a Final Year BCA Project, offering a complete, secure, responsive, and installable application.

### 9.2 Future Enhancements
* **GPS Geolocation & Nearby Places**: Detect the user's real-time GPS coordinates and list tourist places sorted by physical distance.
* **Audio Tour Guides**: Integrate text-to-speech audio narration for offline place guides.
* **Push Notifications**: Notify users about nearby cultural festivals, weather alerts, or special entry fee discounts using Web Push API.
* **Multi-Language Support**: Provide multi-lingual localization for international and regional travelers.
