"""
=========================================================
Tourist Guide PWA - Database Layer (database.py)
Supports MySQL (tourist_guide_db) with SQLite fallback mode
Suitable for BCA Final Year Project
=========================================================
"""

import os
import sqlite3

# Try importing pymysql or mysql.connector for MySQL support
try:
    import pymysql
    pymysql.install_as_MySQLdb()
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

# Database configuration settings
MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
MYSQL_DB = os.environ.get('MYSQL_DB', 'tourist_guide_db')
MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))

SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), 'tourist_guide.db')


class Database:
    def __init__(self):
        self.use_mysql = False
        self._check_connection()

    def _check_connection(self):
        """Attempts to connect to MySQL. If unavailable, falls back to SQLite."""
        if MYSQL_AVAILABLE:
            try:
                conn = pymysql.connect(
                    host=MYSQL_HOST,
                    user=MYSQL_USER,
                    password=MYSQL_PASSWORD,
                    database=MYSQL_DB,
                    port=MYSQL_PORT,
                    connect_timeout=3
                )
                conn.close()
                self.use_mysql = True
                print("[DATABASE] Successfully connected to MySQL database!")
                return
            except Exception as e:
                print(f"[DATABASE] MySQL connection failed ({e}). Falling back to SQLite mode.")

        self.use_mysql = False
        print(f"[DATABASE] Using SQLite database engine ({SQLITE_DB_PATH})")
        self._init_sqlite_db()

    def get_connection(self):
        """Returns an active database connection."""
        if self.use_mysql:
            return pymysql.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB,
                port=MYSQL_PORT,
                cursorclass=pymysql.cursors.DictCursor
            )
        else:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            conn.row_factory = sqlite3.Row
            return conn

    def _init_sqlite_db(self):
        """Initializes SQLite tables and seeds sample data if database is new."""
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tourist_Places table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tourist_places (
                place_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT NOT NULL,
                timings TEXT DEFAULT '9:00 AM - 5:00 PM',
                entry_fee TEXT DEFAULT 'Free / Nominal',
                image TEXT DEFAULT 'default_place.jpg',
                category TEXT DEFAULT 'Heritage',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Favorites table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                favorite_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                place_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (place_id) REFERENCES tourist_places(place_id) ON DELETE CASCADE,
                UNIQUE(user_id, place_id)
            )
        ''')

        # Check if sample places exist, if not seed them
        cursor.execute("SELECT COUNT(*) FROM tourist_places")
        if cursor.fetchone()[0] == 0:
            sample_places = [
                (
                    'Taj Mahal',
                    'Agra, Uttar Pradesh',
                    'An immense mausoleum of white marble, built in Agra between 1631 and 1648 by order of the Mughal emperor Shah Jahan in memory of his favourite wife. Taj Mahal is one of the Seven Wonders of the World.',
                    '6:00 AM - 6:30 PM (Closed on Fridays)',
                    '₹50 for Indians, ₹1100 for Foreigners',
                    'taj_mahal.jpg',
                    'Heritage'
                ),
                (
                    'Jaipur City Palace',
                    'Jaipur, Rajasthan',
                    'A majestic palace complex located in the heart of the Pink City. Built by Maharaja Sawai Jai Singh II, it features a unique blend of Rajput, Mughal, and European architectural styles with stunning courtyards and museums.',
                    '9:30 AM - 5:00 PM',
                    '₹200 for Indians, ₹700 for Foreigners',
                    'jaipur_palace.jpg',
                    'Palace'
                ),
                (
                    'Goa Beaches & Fort Aguada',
                    'North Goa',
                    'Famous for pristine golden sands, vibrant beach shacks, water sports, and historic 17th-century Portuguese Fort Aguada offering panoramic views of the Arabian Sea.',
                    '24 Hours Open (Fort: 9:30 AM - 6:00 PM)',
                    'Free Entry (Fort: ₹25)',
                    'goa_beach.jpg',
                    'Beach'
                ),
                (
                    'Kerala Backwaters (Alleppey)',
                    'Alleppey, Kerala',
                    'A tranquil network of interconnected canals, rivers, lakes, and inlets lined with lush palm trees and traditional houseboats. Known as the Venice of the East.',
                    'Best visited 6:00 AM - 7:00 PM',
                    'Houseboat rentals from ₹3,000/day',
                    'kerala_backwaters.jpg',
                    'Nature'
                ),
                (
                    'Varanasi Ghats & Kashi Vishwanath',
                    'Varanasi, Uttar Pradesh',
                    'One of the oldest continuously inhabited cities in the world. The famous riverfront ghats along the sacred Ganges river host daily evening Ganga Aarti ceremonies and rich cultural heritage.',
                    '24 Hours Open (Ganga Aarti: 6:45 PM)',
                    'Free Entry',
                    'varanasi_ghats.jpg',
                    'Spiritual'
                ),
                (
                    'Pangong Lake & Nubra Valley',
                    'Leh Ladakh, Jammu & Kashmir',
                    'A breathtaking high-altitude endorheic lake in the Himalayas situated at an elevation of 4,225 meters. Famous for its color-changing crystal clear blue waters and serene mountain backdrop.',
                    'May to October (Daytime)',
                    'Inner Line Permit (₹400 approx)',
                    'pangong_lake.jpg',
                    'Adventure'
                )
            ]
            cursor.executemany('''
                INSERT INTO tourist_places (name, location, description, timings, entry_fee, image, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', sample_places)

            # Insert sample users
            cursor.execute("INSERT OR IGNORE INTO users (name, email, password) VALUES (?, ?, ?)",
                           ('John Doe', 'john@example.com', 'user123'))
            cursor.execute("INSERT OR IGNORE INTO users (name, email, password) VALUES (?, ?, ?)",
                           ('Alice Smith', 'alice@example.com', 'user123'))

        conn.commit()
        conn.close()

# Singleton DB helper instance
db_instance = Database()

def get_db():
    """Helper method to get database connection."""
    return db_instance.get_connection()

def is_mysql():
    """Returns True if MySQL is active."""
    return db_instance.use_mysql
