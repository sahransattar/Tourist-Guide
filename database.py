"""
=========================================================
Tourist Guide PWA - Database Layer (database.py)
Supports Production MySQL (cloud/self-hosted) & Local SQLite
Suitable for BCA Final Year Project
=========================================================
"""

import os
import re
import ssl
import shutil
import logging
import sqlite3
import urllib.parse
from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

# Try importing pymysql for MySQL support
try:
    import pymysql
    import pymysql.cursors
    pymysql.install_as_MySQLdb()
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    logger.warning("PyMySQL is not installed. MySQL functionality will be disabled.")


# Environment Detection
IS_VERCEL = bool(os.environ.get('VERCEL'))
IS_PRODUCTION = (
    IS_VERCEL
    or os.environ.get('FLASK_ENV', '').lower() == 'production'
    or os.environ.get('ENVIRONMENT', '').lower() == 'production'
    or os.environ.get('ENV', '').lower() == 'production'
)

SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tourist_guide.db')


def get_sqlite_runtime_path():
    """
    Returns the appropriate path for the SQLite database.
    In serverless environments (Vercel / Lambda), copies the bundled database
    to /tmp if not already present so that writes succeed on the ephemeral disk.
    """
    bundled_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tourist_guide.db')
    if (IS_VERCEL or os.environ.get('AWS_LAMBDA_FUNCTION_NAME')) and os.name != 'nt':
        tmp_db = '/tmp/tourist_guide.db'
        if not os.path.exists(tmp_db) and os.path.exists(bundled_path):
            try:
                shutil.copyfile(bundled_path, tmp_db)
                logger.info("[DATABASE] Copied bundled tourist_guide.db to writable /tmp/tourist_guide.db")
            except Exception as e:
                logger.warning("[DATABASE] Could not copy to /tmp: %s. Using bundled DB read-only.", e)
                return bundled_path
        if os.path.exists(tmp_db):
            return tmp_db
    return bundled_path


class DatabaseError(Exception):
    """Base exception for database errors."""
    pass


class DatabaseConfigurationError(DatabaseError):
    """Raised when required production database configuration is missing."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


def parse_database_config():
    """
    Parses database settings from DATABASE_URL / MYSQL_URL or individual MYSQL_* environment variables.
    Never exposes passwords or secret credentials in logs.
    """
    db_url = os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL')
    if db_url:
        try:
            parsed = urllib.parse.urlparse(db_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            ssl_mode = query_params.get('ssl-mode', [''])[0].lower()
            ssl_required = (
                'ssl' in query_params
                or ssl_mode in ('required', 'verify-ca', 'verify-full', 'true', '1')
                or os.environ.get('MYSQL_SSL', '').lower() in ('true', '1', 'required')
            )
            return {
                'configured': True,
                'host': parsed.hostname or 'localhost',
                'port': int(parsed.port or 3306),
                'user': urllib.parse.unquote(parsed.username or 'root'),
                'password': urllib.parse.unquote(parsed.password or ''),
                'db': parsed.path.lstrip('/') or 'tourist_guide_db',
                'ssl': ssl_required,
                'source': 'DATABASE_URL'
            }
        except Exception as e:
            logger.error("Failed to parse DATABASE_URL: %s", str(e))

    mysql_host = os.environ.get('MYSQL_HOST')
    if mysql_host:
        ssl_required = os.environ.get('MYSQL_SSL', '').lower() in ('true', '1', 'required')
        return {
            'configured': True,
            'host': mysql_host.strip(),
            'port': int(os.environ.get('MYSQL_PORT', 3306)),
            'user': os.environ.get('MYSQL_USER', 'root').strip(),
            'password': os.environ.get('MYSQL_PASSWORD', ''),
            'db': os.environ.get('MYSQL_DB', 'tourist_guide_db').strip(),
            'ssl': ssl_required,
            'source': 'MYSQL_HOST'
        }

    return {
        'configured': False,
        'host': None,
        'port': 3306,
        'user': None,
        'password': '',
        'db': None,
        'ssl': False,
        'source': None
    }


class DatabaseManager:
    """
    Manages persistent MySQL connections for production and SQLite for local development.
    Prevents silent fallback to read-only/ephemeral SQLite in production serverless environments.
    """

    def __init__(self):
        self.use_mysql = False
        self._initialized = False
        self._last_error = None
        self._check_and_init()

    def _check_and_init(self):
        config = parse_database_config()

        if IS_PRODUCTION:
            if config['configured'] and MYSQL_AVAILABLE:
                try:
                    conn = self._create_mysql_connection(config, connect_timeout=5)
                    self._init_mysql_schema(conn)
                    conn.close()
                    self.use_mysql = True
                    self._initialized = True
                    self._last_error = None
                    logger.info("[DATABASE] Connected successfully to production MySQL database at %s:%d",
                                config['host'], config['port'])
                    return
                except Exception as e:
                    self.use_mysql = False
                    self._last_error = f"MySQL connection failed: {str(e)}"
                    logger.error("[DATABASE ERROR] Failed to connect to production MySQL at %s:%d: %s",
                                 config['host'], config['port'], str(e), exc_info=True)

            # Fallback to embedded SQLite database in production if MySQL not configured or reachable
            sqlite_path = get_sqlite_runtime_path()
            if os.path.exists(sqlite_path) and not os.environ.get('REQUIRE_EXTERNAL_DB'):
                self.use_mysql = False
                self._init_sqlite_schema()
                self._initialized = True
                self._last_error = None
                logger.info("[DATABASE] Using embedded SQLite database (%s) on production", sqlite_path)
                return

            if not config['configured']:
                msg = (
                    "Production environment detected (e.g. Vercel), but no external MySQL database "
                    "is configured. Please configure MYSQL_HOST (or DATABASE_URL) in your Vercel Project Settings."
                )
                self._last_error = msg
                logger.error("[DATABASE CONFIG ERROR] %s", msg)
                self.use_mysql = False
                return

            if not MYSQL_AVAILABLE:
                msg = "PyMySQL is not installed. Cannot connect to production MySQL database."
                self._last_error = msg
                logger.error("[DATABASE ERROR] %s", msg)
                return
        else:
            # Development mode: prefer MySQL if configured and reachable; otherwise use local SQLite.
            if config['configured'] and MYSQL_AVAILABLE:
                try:
                    conn = self._create_mysql_connection(config, connect_timeout=3)
                    self._init_mysql_schema(conn)
                    conn.close()
                    self.use_mysql = True
                    self._initialized = True
                    self._last_error = None
                    logger.info("[DATABASE] Connected to development MySQL database at %s:%d",
                                config['host'], config['port'])
                    return
                except Exception as e:
                    logger.warning("[DATABASE] Development MySQL connection failed (%s). Falling back to SQLite.", e)

            # Local SQLite development mode
            self.use_mysql = False
            self._init_sqlite_schema()
            self._initialized = True
            self._last_error = None
            logger.info("[DATABASE] Using local SQLite development database (%s)", SQLITE_DB_PATH)

    def _create_mysql_connection(self, config, connect_timeout=5):
        connect_kwargs = {
            'host': config['host'],
            'user': config['user'],
            'password': config['password'],
            'database': config['db'],
            'port': config['port'],
            'charset': 'utf8mb4',
            'connect_timeout': connect_timeout,
            'read_timeout': 10,
            'write_timeout': 10,
            'cursorclass': pymysql.cursors.DictCursor,
            'autocommit': False
        }

        # Auto-detect or apply SSL if requested or if host is a known cloud database
        host_lower = config['host'].lower()
        cloud_hosts = ('tidbcloud.com', 'aivencloud.com', 'psdb.cloud', 'rds.amazonaws.com', 'cleardb.net')
        if config['ssl'] or any(ch in host_lower for ch in cloud_hosts):
            ssl_ctx = ssl.create_default_context()
            ca_path = os.environ.get('MYSQL_SSL_CA')
            if ca_path and os.path.exists(ca_path):
                ssl_ctx.load_verify_locations(ca_path)
            elif os.environ.get('MYSQL_SSL_VERIFY', '').lower() in ('false', '0', 'no'):
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE
            connect_kwargs['ssl'] = ssl_ctx

        return pymysql.connect(**connect_kwargs)

    def get_connection(self):
        """
        Returns a newly established database connection.
        Raises DatabaseConnectionError if connection cannot be created.
        """
        config = parse_database_config()

        if IS_PRODUCTION:
            if self.use_mysql and config['configured']:
                try:
                    return self._create_mysql_connection(config, connect_timeout=5)
                except Exception as e:
                    logger.error("Production MySQL connection failed: %s", str(e), exc_info=True)
                    sqlite_path = get_sqlite_runtime_path()
                    if not os.path.exists(sqlite_path) or os.environ.get('REQUIRE_EXTERNAL_DB'):
                        raise DatabaseConnectionError(
                            "Failed to connect to production database. Please verify your database host, credentials, and network access."
                        ) from e

            # Fallback to embedded SQLite database in production if MySQL not configured
            sqlite_path = get_sqlite_runtime_path()
            if os.path.exists(sqlite_path) and not os.environ.get('REQUIRE_EXTERNAL_DB'):
                conn = sqlite3.connect(sqlite_path, timeout=10.0)
                conn.row_factory = sqlite3.Row
                return conn

            if not config['configured']:
                raise DatabaseConfigurationError(
                    "Production database is not configured. Please set MYSQL_HOST or DATABASE_URL in Vercel environment variables."
                )
            if not MYSQL_AVAILABLE:
                raise DatabaseConfigurationError("PyMySQL library is not installed.")

            try:
                return self._create_mysql_connection(config, connect_timeout=5)
            except Exception as e:
                logger.error("Production MySQL connection failed: %s", str(e), exc_info=True)
                raise DatabaseConnectionError(
                    "Failed to connect to production database. Please verify your database host, credentials, and network access."
                ) from e
        else:
            if self.use_mysql and config['configured']:
                try:
                    return self._create_mysql_connection(config, connect_timeout=3)
                except Exception as e:
                    logger.warning("MySQL connection failed; switching to local SQLite: %s", e)
                    self.use_mysql = False

            # Local SQLite connection
            conn = sqlite3.connect(get_sqlite_runtime_path(), timeout=10.0)
            conn.row_factory = sqlite3.Row
            return conn

    def _init_mysql_schema(self, conn):
        """Ensures MySQL tables exist and seeds sample places and users if new."""
        with conn.cursor() as cursor:
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            ''')

            # Tourist_Places table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tourist_places (
                    place_id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(150) NOT NULL,
                    location VARCHAR(150) NOT NULL,
                    description TEXT NOT NULL,
                    timings VARCHAR(100) DEFAULT '9:00 AM - 5:00 PM',
                    entry_fee VARCHAR(100) DEFAULT 'Free / Nominal',
                    image VARCHAR(255) DEFAULT 'default_place.jpg',
                    category VARCHAR(50) DEFAULT 'Heritage',
                    latitude DECIMAL(10, 7) NULL,
                    longitude DECIMAL(10, 7) NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            ''')

            # Migration: Ensure latitude and longitude columns exist in MySQL
            try:
                cursor.execute("SHOW COLUMNS FROM tourist_places LIKE 'latitude'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE tourist_places ADD COLUMN latitude DECIMAL(10, 7) NULL")
                    cursor.execute("ALTER TABLE tourist_places ADD COLUMN longitude DECIMAL(10, 7) NULL")
            except Exception as e:
                logger.warning("Error checking/migrating MySQL coordinates columns: %s", e)

            # Favorites table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS favorites (
                    favorite_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    place_id INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (place_id) REFERENCES tourist_places(place_id) ON DELETE CASCADE,
                    UNIQUE KEY user_place_unique (user_id, place_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            ''')

            # Itineraries table (Trip Planner)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS itineraries (
                    itinerary_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(150) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            ''')

            # Itinerary Items table (Stops along a trip)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS itinerary_items (
                    item_id INT AUTO_INCREMENT PRIMARY KEY,
                    itinerary_id INT NOT NULL,
                    place_id INT NOT NULL,
                    day_number INT DEFAULT 1,
                    order_index INT DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (itinerary_id) REFERENCES itineraries(itinerary_id) ON DELETE CASCADE,
                    FOREIGN KEY (place_id) REFERENCES tourist_places(place_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            ''')

            # Seed places if empty or less than 60 destinations
            cursor.execute("SELECT COUNT(*) AS cnt FROM tourist_places")
            res = cursor.fetchone()
            count = res['cnt'] if isinstance(res, dict) else res[0]
            if count < 60:
                try:
                    import seed_destinations
                    seed_destinations.seed_database()
                except Exception as seed_err:
                    logger.warning("Auto-seed encountered: %s", seed_err)
            else:
                self._sync_seed_coordinates(cursor, is_sqlite=False)

            # Seed demo users if empty (with secure Werkzeug password hashes)
            cursor.execute("SELECT COUNT(*) AS cnt FROM users")
            res = cursor.fetchone()
            user_count = res['cnt'] if isinstance(res, dict) else res[0]
            if user_count == 0:
                demo_hash = generate_password_hash('user123')
                cursor.execute(
                    "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                    ('John Doe', 'john@example.com', demo_hash)
                )
                cursor.execute(
                    "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                    ('Alice Smith', 'alice@example.com', demo_hash)
                )

            # Ensure primary user account exists
            cursor.execute("SELECT user_id FROM users WHERE email = 'sahransatt12@gmail.com'")
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                    ('Sahran Sattar', 'sahransatt12@gmail.com', 'scrypt:32768:8:1$51OejXoPB0sC1p3r$5ca95959ad0f04df591d8480db89d53b9f67a637504ba42cb233b8a36fa17578ec0949d8544f8615e4785b9b736bca487b9b008d6c70b6d6101967a57a5e8486')
                )

        conn.commit()

    def _init_sqlite_schema(self):
        """Initializes SQLite tables and seeds sample data for local development."""
        try:
            conn = sqlite3.connect(get_sqlite_runtime_path())
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

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
                    latitude REAL NULL,
                    longitude REAL NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Migration: Ensure latitude and longitude columns exist in SQLite
            cursor.execute("PRAGMA table_info(tourist_places)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'latitude' not in columns:
                cursor.execute("ALTER TABLE tourist_places ADD COLUMN latitude REAL NULL")
            if 'longitude' not in columns:
                cursor.execute("ALTER TABLE tourist_places ADD COLUMN longitude REAL NULL")

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

            # Itineraries table (Trip Planner)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS itineraries (
                    itinerary_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')

            # Itinerary Items table (Stops along a trip)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS itinerary_items (
                    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    itinerary_id INTEGER NOT NULL,
                    place_id INTEGER NOT NULL,
                    day_number INTEGER DEFAULT 1,
                    order_index INTEGER DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (itinerary_id) REFERENCES itineraries(itinerary_id) ON DELETE CASCADE,
                    FOREIGN KEY (place_id) REFERENCES tourist_places(place_id) ON DELETE CASCADE
                )
            ''')

            cursor.execute("SELECT COUNT(*) FROM tourist_places")
            place_cnt = cursor.fetchone()[0]
            if place_cnt < 60:
                try:
                    import seed_destinations
                    seed_destinations.seed_database()
                except Exception as seed_err:
                    logger.warning("Auto-seed encountered: %s", seed_err)
            else:
                self._sync_seed_coordinates(cursor, is_sqlite=True)

            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                demo_hash = generate_password_hash('user123')
                cursor.execute(
                    "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                    ('John Doe', 'john@example.com', demo_hash)
                )
                cursor.execute(
                    "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                    ('Alice Smith', 'alice@example.com', demo_hash)
                )

            # Ensure primary user account exists
            cursor.execute("SELECT user_id FROM users WHERE email = 'sahransatt12@gmail.com'")
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                    ('Sahran Sattar', 'sahransatt12@gmail.com', 'scrypt:32768:8:1$51OejXoPB0sC1p3r$5ca95959ad0f04df591d8480db89d53b9f67a637504ba42cb233b8a36fa17578ec0949d8544f8615e4785b9b736bca487b9b008d6c70b6d6101967a57a5e8486')
                )

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Failed to initialize SQLite database: %s", e)

    def _seed_places(self, cursor, is_sqlite=False):
        sample_places = [
            (
                'Taj Mahal',
                'Agra, Uttar Pradesh',
                'An immense mausoleum of white marble, built in Agra between 1631 and 1648 by order of the Mughal emperor Shah Jahan in memory of his favourite wife. Taj Mahal is one of the Seven Wonders of the World.',
                '6:00 AM - 6:30 PM (Closed on Fridays)',
                '₹50 for Indians, ₹1100 for Foreigners',
                'taj_mahal.jpg',
                'Heritage',
                27.1751,
                78.0421
            ),
            (
                'Jaipur City Palace',
                'Jaipur, Rajasthan',
                'A majestic palace complex located in the heart of the Pink City. Built by Maharaja Sawai Jai Singh II, it features a unique blend of Rajput, Mughal, and European architectural styles with stunning courtyards and museums.',
                '9:30 AM - 5:00 PM',
                '₹200 for Indians, ₹700 for Foreigners',
                'jaipur_palace.jpg',
                'Palace',
                26.9258,
                75.8237
            ),
            (
                'Goa Beaches & Fort Aguada',
                'North Goa',
                'Famous for pristine golden sands, vibrant beach shacks, water sports, and historic 17th-century Portuguese Fort Aguada offering panoramic views of the Arabian Sea.',
                '24 Hours Open (Fort: 9:30 AM - 6:00 PM)',
                'Free Entry (Fort: ₹25)',
                'goa_beach.jpg',
                'Beach',
                15.4920,
                73.7737
            ),
            (
                'Kerala Backwaters (Alleppey)',
                'Alleppey, Kerala',
                'A tranquil network of interconnected canals, rivers, lakes, and inlets lined with lush palm trees and traditional houseboats. Known as the Venice of the East.',
                'Best visited 6:00 AM - 7:00 PM',
                'Houseboat rentals from ₹3,000/day',
                'kerala_backwaters.jpg',
                'Nature',
                9.4981,
                76.3388
            ),
            (
                'Varanasi Ghats & Kashi Vishwanath',
                'Varanasi, Uttar Pradesh',
                'One of the oldest continuously inhabited cities in the world. The famous riverfront ghats along the sacred Ganges river host daily evening Ganga Aarti ceremonies and rich cultural heritage.',
                '24 Hours Open (Ganga Aarti: 6:45 PM)',
                'Free Entry',
                'varanasi_ghats.jpg',
                'Spiritual',
                25.3109,
                83.0104
            ),
            (
                'Pangong Lake & Nubra Valley',
                'Leh Ladakh, Jammu & Kashmir',
                'A breathtaking high-altitude endorheic lake in the Himalayas situated at an elevation of 4,225 meters. Famous for its color-changing crystal clear blue waters and serene mountain backdrop.',
                'May to October (Daytime)',
                'Inner Line Permit (₹400 approx)',
                'pangong_lake.jpg',
                'Adventure',
                33.7595,
                78.6674
            )
        ]
        sql = '''
            INSERT INTO tourist_places (name, location, description, timings, entry_fee, image, category, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''' if is_sqlite else '''
            INSERT INTO tourist_places (name, location, description, timings, entry_fee, image, category, latitude, longitude)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        cursor.executemany(sql, sample_places)

    def _sync_seed_coordinates(self, cursor, is_sqlite=False):
        """Backfills latitude and longitude coordinates for seed destinations if currently NULL."""
        coords_map = {
            'Taj Mahal': (27.1751, 78.0421),
            'Jaipur City Palace': (26.9258, 75.8237),
            'Goa Beaches & Fort Aguada': (15.4920, 73.7737),
            'Kerala Backwaters (Alleppey)': (9.4981, 76.3388),
            'Varanasi Ghats & Kashi Vishwanath': (25.3109, 83.0104),
            'Pangong Lake & Nubra Valley': (33.7595, 78.6674),
        }
        update_sql = '''
            UPDATE tourist_places SET latitude = ?, longitude = ? WHERE name = ? AND latitude IS NULL
        ''' if is_sqlite else '''
            UPDATE tourist_places SET latitude = %s, longitude = %s WHERE name = %s AND latitude IS NULL
        '''
        for name, (lat, lng) in coords_map.items():
            cursor.execute(update_sql, (lat, lng, name))


# Singleton database manager instance
db_instance = DatabaseManager()


def get_db():
    """Returns an active database connection."""
    return db_instance.get_connection()


def is_mysql():
    """Returns True if MySQL is active."""
    return db_instance.use_mysql


def check_db_status():
    """
    Returns a safe dictionary describing database health.
    Never exposes passwords or sensitive credentials.
    """
    config = parse_database_config()
    status = {
        'environment': 'production' if IS_PRODUCTION else 'development',
        'is_vercel': IS_VERCEL,
        'configured_engine': 'mysql' if config['configured'] else 'sqlite',
        'active_engine': 'mysql' if db_instance.use_mysql else 'sqlite',
        'connected': False,
        'error': None
    }
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        status['connected'] = True
    except Exception as e:
        status['connected'] = False
        status['error'] = str(e)
    return status


def dict_from_row(row):
    """Converts a database row into a standard Python dict."""
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    return dict(row)


def dicts_from_rows(rows):
    """Converts an iterable of database rows into a list of dicts."""
    return [dict_from_row(r) for r in rows]


def query_db(query, args=(), fetchone=False, fetchall=False, commit=False):
    """
    Executes a database query safely with guaranteed resource cleanup and transaction rollback.
    Adapts SQL placeholders for MySQL (%s) and SQLite (?).
    """
    conn = get_db()
    cursor = conn.cursor()

    # Determine whether active connection is MySQL or SQLite
    using_mysql = is_mysql()

    if not using_mysql:
        # Replace MySQL %s with SQLite ? placeholder
        query = query.replace('%s', '?')

    try:
        cursor.execute(query, args)
        if commit:
            conn.commit()
            last_id = cursor.lastrowid if hasattr(cursor, 'lastrowid') else None
            return last_id

        if fetchone:
            row = cursor.fetchone()
            return dict_from_row(row)
        elif fetchall:
            rows = cursor.fetchall()
            return dicts_from_rows(rows)
    except Exception as e:
        if commit:
            try:
                conn.rollback()
            except Exception:
                pass
        raise e
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
