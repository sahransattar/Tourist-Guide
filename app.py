"""
=========================================================
Tourist Guide PWA - Flask Backend Application (app.py)
Suitable for BCA Final Year Project
=========================================================
"""

import os
import re
import math
import time
import secrets
import logging
from collections import defaultdict
from functools import wraps
from urllib.parse import urlparse, urljoin, parse_qs, urlencode

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

from database import (
    get_db, is_mysql, query_db, check_db_status,
    IS_PRODUCTION, DatabaseError, DatabaseConfigurationError, DatabaseConnectionError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# WSGI middleware to normalize PATH_INFO for Vercel serverless rewrites
class VercelPathMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get('QUERY_STRING', '')
        if '__path' in query_string:
            params = parse_qs(query_string, keep_blank_values=True)
            if '__path' in params:
                dest = params.pop('__path')[0].lstrip('/')
                environ['PATH_INFO'] = '/' + dest
                environ['QUERY_STRING'] = urlencode(params, doseq=True)
        elif environ.get('PATH_INFO') in ('/api/index', '/api/index.py'):
            environ['PATH_INFO'] = '/'
        return self.wsgi_app(environ, start_response)

# Apply both ProxyFix (for HTTPS headers behind Vercel edge) and VercelPathMiddleware
app.wsgi_app = ProxyFix(VercelPathMiddleware(app.wsgi_app), x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Configure Secret Key: use environment variable, with a deterministic production fallback
# so that all serverless containers and cold starts share the same session encryption key.
configured_secret = os.environ.get('SECRET_KEY')
if configured_secret:
    app.secret_key = configured_secret
else:
    app.secret_key = '7f5c2b9a4d8e1f0c3b5a7d9e2f4a6b8c1d3e5f7a9b0c2d4e6f8a1b3c5d7e9f0a'

# Session Cookie Security Configuration
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
if IS_PRODUCTION:
    app.config['SESSION_COOKIE_SECURE'] = True


# In-memory Rate Limiting for Authentication (Brute-force protection)
login_attempts = defaultdict(list)


def is_rate_limited(ip_address, max_attempts=5, window_seconds=300):
    """Checks if an IP address has exceeded the allowed login failure threshold."""
    now = time.time()
    attempts = [t for t in login_attempts[ip_address] if now - t < window_seconds]
    login_attempts[ip_address] = attempts
    return len(attempts) >= max_attempts


def record_failed_attempt(ip_address):
    """Records a failed authentication attempt timestamp."""
    login_attempts[ip_address].append(time.time())


def clear_failed_attempts(ip_address):
    """Clears failed attempts on successful login."""
    login_attempts.pop(ip_address, None)


# Safe Redirect Validator (Prevents Open Redirect Vulnerabilities)
def is_safe_url(target):
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two coordinates on Earth
    using the Haversine formula. Returns distance in kilometers.
    """
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371.0  # Earth's radius in kilometers
    return c * r


# CSRF Protection Helpers
def get_csrf_token():
    """Generates or retrieves a secure random CSRF token tied to the current session."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


@app.template_filter('image_url')
def image_url_filter(image_name):
    """
    Resolves image source URL.
    Returns remote URL directly if starting with http(s)://,
    otherwise resolves to local static/images/ path.
    """
    if not image_name:
        return url_for('static', filename='images/default_place.jpg')
    image_str = str(image_name).strip()
    if image_str.startswith(('http://', 'https://')):
        return image_str
    return url_for('static', filename='images/' + image_str)


@app.context_processor
def inject_template_helpers():
    """Injects csrf_token and image_url helpers into all Jinja2 templates."""
    return dict(csrf_token=get_csrf_token, image_url=image_url_filter)


@app.before_request
def validate_csrf():
    """
    Validates CSRF token on all state-changing HTTP methods (POST, PUT, DELETE, PATCH).
    Accepts token via 'csrf_token' form field or 'X-CSRFToken' HTTP header.
    """
    if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
        # Allow health checks and read-only APIs without CSRF
        if request.endpoint in ('static',):
            return None

        json_body = request.get_json(silent=True) if request.is_json else None
        submitted_token = (
            request.headers.get('X-CSRFToken') or
            request.form.get('csrf_token') or
            (json_body.get('csrf_token') if json_body else None)
        )
        expected_token = session.get('_csrf_token')

        if not expected_token or not submitted_token or not secrets.compare_digest(str(submitted_token), str(expected_token)):
            logger.warning("CSRF validation failed on %s from %s", request.path, request.remote_addr)
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'CSRF token missing or invalid.'}), 403
            flash("Your session or security token expired. Please try submitting again.", "danger")
            return redirect(request.referrer or url_for('home'))


# Admin Authentication Helpers
DEV_DEFAULT_ADMIN_HASH = 'scrypt:32768:8:1$r9kjnZTPSHKFCZ14$b622f3c6db204c8c482a05f460b92a12739e5f8fd6b93ff58c141f83b976147fb023ee9fa9f6f9d4692e63d0e6f257f2773c08f28fe53589fa47238f9d99cb76'


def verify_admin_credentials(username, password):
    """
    Verifies admin credentials securely against environment variables.
    Supports ADMIN_PASSWORD_HASH or ADMIN_PASSWORD, and ADMIN_USERNAME.
    Falls back safely to default credentials ('admin' / 'admin123') if unset.
    """
    if not username or not password:
        return False

    expected_username = os.environ.get('ADMIN_USERNAME', 'admin').strip()
    if not secrets.compare_digest(username.strip(), expected_username):
        return False

    # Check for pre-hashed admin password in environment
    admin_password_hash = os.environ.get('ADMIN_PASSWORD_HASH')
    if admin_password_hash:
        try:
            return check_password_hash(admin_password_hash.strip(), password)
        except Exception as e:
            logger.error("Error verifying ADMIN_PASSWORD_HASH: %s", e)
            return False

    # Check for plaintext admin password in environment
    admin_password_plain = os.environ.get('ADMIN_PASSWORD')
    if admin_password_plain:
        return secrets.compare_digest(password, admin_password_plain)

    # Safe fallback to default admin credentials ('admin' / 'admin123')
    return check_password_hash(DEV_DEFAULT_ADMIN_HASH, password)


def admin_required(f):
    """Decorator ensuring that only authenticated administrators can access protected endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin') or not session.get('admin_user'):
            flash("Admin authentication required. Please log in.", "danger")
            return redirect(url_for('admin_login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function


# ---------------------------------------------------------
# Public & User Routes
# ---------------------------------------------------------

@app.route('/')
@app.route('/api/index')
def home():
    """Home Page route showing hero, search bar, and featured tourist places."""
    try:
        places = query_db("SELECT * FROM tourist_places ORDER BY place_id DESC LIMIT 6", fetchall=True) or []
        places_count_row = query_db("SELECT COUNT(*) as cnt FROM tourist_places", fetchone=True)
        users_count_row = query_db("SELECT COUNT(*) as cnt FROM users", fetchone=True)
        total_places = places_count_row['cnt'] if places_count_row else 0
        total_users = users_count_row['cnt'] if users_count_row else 0
    except DatabaseError as de:
        logger.error("Database error on home page: %s", de)
        places = []
        total_places = 0
        total_users = 0
    except Exception as e:
        logger.error("Unexpected error on home page: %s", e)
        places = []
        total_places = 0
        total_users = 0

    user_fav_ids = []
    if 'user_id' in session:
        try:
            favs = query_db("SELECT place_id FROM favorites WHERE user_id = %s", (session['user_id'],), fetchall=True)
            user_fav_ids = [f['place_id'] for f in favs] if favs else []
        except Exception as e:
            logger.error("Error retrieving user favorites on home: %s", e)

    return render_template(
        'index.html',
        places=places,
        total_places=total_places,
        total_users=total_users,
        user_fav_ids=user_fav_ids
    )


@app.route('/places')
def view_places():
    """View & Search Tourist Places route with category/keyword filters, sorting, and pagination."""
    search_query = request.args.get('q', '').strip()
    category_filter = request.args.get('category', '').strip()
    sort_by = request.args.get('sort_by', 'name_asc').strip()

    try:
        page = max(1, int(request.args.get('page', 1)))
    except (ValueError, TypeError):
        page = 1

    per_page = 9

    # Base WHERE clause
    where_sql = " WHERE 1=1"
    params = []

    if search_query:
        where_sql += " AND (name LIKE %s OR location LIKE %s OR description LIKE %s)"
        pattern = f"%{search_query}%"
        params.extend([pattern, pattern, pattern])

    if category_filter and category_filter != 'All':
        where_sql += " AND category = %s"
        params.append(category_filter)

    # Sorting
    sort_map = {
        'name_asc': 'name ASC',
        'name_desc': 'name DESC',
        'newest': 'place_id DESC',
        'oldest': 'place_id ASC'
    }
    order_by = sort_map.get(sort_by, 'name ASC')

    try:
        # Count total matching places
        count_sql = "SELECT COUNT(*) as cnt FROM tourist_places" + where_sql
        cnt_row = query_db(count_sql, tuple(params), fetchone=True)
        total_items = cnt_row['cnt'] if cnt_row else 0
        total_pages = max(1, math.ceil(total_items / per_page))

        if page > total_pages and total_items > 0:
            page = total_pages

        offset = (page - 1) * per_page

        # Fetch paginated places
        data_sql = f"SELECT * FROM tourist_places{where_sql} ORDER BY {order_by} LIMIT {per_page} OFFSET {offset}"
        places = query_db(data_sql, tuple(params), fetchall=True) or []

        categories = query_db("SELECT DISTINCT category FROM tourist_places WHERE category IS NOT NULL", fetchall=True)
        cat_list = [c['category'] for c in categories] if categories else []
    except Exception as e:
        logger.error("Error retrieving places list: %s", e)
        places = []
        cat_list = []
        total_items = 0
        total_pages = 1

    user_fav_ids = []
    if 'user_id' in session:
        try:
            favs = query_db("SELECT place_id FROM favorites WHERE user_id = %s", (session['user_id'],), fetchall=True)
            user_fav_ids = [f['place_id'] for f in favs] if favs else []
        except Exception:
            pass

    return render_template(
        'places.html',
        places=places,
        total_places=total_items,
        page=page,
        total_pages=total_pages,
        has_prev=(page > 1),
        has_next=(page < total_pages),
        prev_num=page - 1,
        next_num=page + 1,
        search_query=search_query,
        selected_category=category_filter,
        sort_by=sort_by,
        categories=cat_list,
        user_fav_ids=user_fav_ids
    )


@app.route('/place/<int:place_id>')
def place_details(place_id):
    """View details of a specific tourist place."""
    try:
        place = query_db("SELECT * FROM tourist_places WHERE place_id = %s", (place_id,), fetchone=True)
    except Exception as e:
        logger.error("Error fetching place_id=%s: %s", place_id, e)
        place = None

    if not place:
        return render_template('404.html'), 404

    is_favorite = False
    if 'user_id' in session:
        try:
            fav = query_db(
                "SELECT * FROM favorites WHERE user_id = %s AND place_id = %s",
                (session['user_id'], place_id),
                fetchone=True
            )
            if fav:
                is_favorite = True
        except Exception:
            pass

    related_places = []
    try:
        related_places = query_db(
            "SELECT * FROM tourist_places WHERE place_id != %s AND (category = %s OR location LIKE %s) LIMIT 3",
            (place_id, place.get('category', ''), f"%{place['location'].split(',')[0]}%"),
            fetchall=True
        ) or []
    except Exception:
        pass

    return render_template('details.html', place=place, is_favorite=is_favorite, related_places=related_places)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    User Registration route.
    Validates input, securely hashes passwords, and handles database errors gracefully.
    """
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        # 1. Validation: Required fields
        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template('register.html')

        if len(name) < 2 or len(name) > 100:
            flash("Full Name must be between 2 and 100 characters.", "danger")
            return render_template('register.html')

        # 2. Validation: Email format
        email_regex = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        if not email_regex.match(email) or len(email) > 100:
            flash("Please enter a valid email address.", "danger")
            return render_template('register.html')

        # 3. Validation: Password strength
        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template('register.html')

        # 4. Check for existing user account
        try:
            existing_user = query_db("SELECT user_id FROM users WHERE email = %s", (email,), fetchone=True)
            if existing_user:
                flash("An account with this email address already exists. Please login.", "warning")
                return render_template('register.html')
        except DatabaseConfigurationError as dce:
            logger.error("Registration aborted due to database configuration: %s", dce)
            flash("Registration is currently unavailable. Database configuration is required.", "danger")
            return render_template('register.html')
        except Exception as e:
            logger.error("Error checking existing user for email=%s: %s", email, e, exc_info=True)
            flash("Registration is temporarily unavailable. Please try again later.", "danger")
            return render_template('register.html')

        # 5. Secure password hashing
        password_hash = generate_password_hash(password)

        # 6. Database insertion
        try:
            query_db(
                "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                (name, email, password_hash),
                commit=True
            )
            logger.info("New user registered successfully: email=%s", email)
            flash("Registration successful! Please login with your credentials.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            # Check for unique constraint violation
            error_str = str(e).lower()
            if 'unique' in error_str or 'duplicate' in error_str:
                logger.warning("Duplicate registration attempt for email=%s", email)
                flash("An account with this email address already exists. Please login.", "warning")
                return render_template('register.html')

            logger.error("Database insert failed during user registration for email=%s: %s", email, e, exc_info=True)
            flash("Registration is temporarily unavailable. Please try again later.", "danger")

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    User Login route.
    Verifies secure hashes and seamlessly upgrades legacy plaintext passwords.
    """
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        client_ip = request.remote_addr or 'unknown'

        if is_rate_limited(client_ip):
            flash("Too many failed login attempts. Please wait 5 minutes before trying again.", "danger")
            return render_template('login.html')

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template('login.html')

        try:
            user = query_db("SELECT * FROM users WHERE email = %s", (email,), fetchone=True)
        except Exception as e:
            logger.error("Database error during login query for email=%s: %s", email, e, exc_info=True)
            flash("Authentication service is temporarily unavailable. Please try again later.", "danger")
            return render_template('login.html')

        if user:
            stored_password = user.get('password', '')
            is_valid = False
            needs_rehash = False

            # Verify Werkzeug password hash
            try:
                if check_password_hash(stored_password, password):
                    is_valid = True
            except Exception:
                pass

            # Safe backward-compatibility: detect legacy plaintext password
            if not is_valid and stored_password == password:
                is_valid = True
                needs_rehash = True

            if is_valid:
                clear_failed_attempts(client_ip)

                # Transparently upgrade legacy plaintext password to secure Werkzeug hash
                if needs_rehash:
                    try:
                        new_hash = generate_password_hash(password)
                        query_db(
                            "UPDATE users SET password = %s WHERE user_id = %s",
                            (new_hash, user['user_id']),
                            commit=True
                        )
                        logger.info("Migrated legacy plaintext password to secure hash for user_id=%s", user['user_id'])
                    except Exception as rehash_err:
                        logger.warning("Failed to auto-upgrade password hash for user_id=%s: %s", user['user_id'], rehash_err)

                # Reset session to prevent session fixation attacks
                session.clear()
                session['user_id'] = user['user_id']
                session['user_name'] = user['name']
                session['user_email'] = user['email']

                flash(f"Welcome back, {user['name']}!", "success")
                next_url = request.args.get('next')
                if is_safe_url(next_url):
                    return redirect(next_url)
                return redirect(url_for('home'))

        record_failed_attempt(client_ip)
        logger.warning("Failed login attempt for email=%s from IP=%s", email, client_ip)
        flash("Invalid email address or password.", "danger")

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Clear session data and log out regular user."""
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('home'))


@app.route('/favorites')
def favorites():
    """View list of user's favorite places."""
    if 'user_id' not in session:
        flash("Please log in to view your favorite tourist places.", "warning")
        return redirect(url_for('login', next=request.path))

    user_id = session['user_id']
    query = """
        SELECT p.*, f.favorite_id, f.created_at as saved_at
        FROM favorites f
        JOIN tourist_places p ON f.place_id = p.place_id
        WHERE f.user_id = %s
        ORDER BY f.favorite_id DESC
    """
    try:
        fav_places = query_db(query, (user_id,), fetchall=True) or []
    except Exception as e:
        logger.error("Error retrieving favorites for user_id=%s: %s", user_id, e)
        fav_places = []

    return render_template('favorites.html', places=fav_places)


@app.route('/api/favorites/toggle', methods=['POST'])
def toggle_favorite():
    """
    AJAX API endpoint for adding or removing a favorite place.
    Enforces user authorization strictly from verified session.
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required. Please login.'}), 401

    data = request.get_json(silent=True) or {}
    place_id = data.get('place_id')

    if not place_id:
        return jsonify({'success': False, 'message': 'Invalid place ID.'}), 400

    try:
        place_id = int(place_id)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Place ID must be an integer.'}), 400

    user_id = session['user_id']

    try:
        existing = query_db(
            "SELECT favorite_id FROM favorites WHERE user_id = %s AND place_id = %s",
            (user_id, place_id),
            fetchone=True
        )

        if existing:
            query_db("DELETE FROM favorites WHERE user_id = %s AND place_id = %s", (user_id, place_id), commit=True)
            return jsonify({
                'success': True,
                'is_favorite': False,
                'message': 'Removed from your favorites.'
            })
        else:
            query_db("INSERT INTO favorites (user_id, place_id) VALUES (%s, %s)", (user_id, place_id), commit=True)
            return jsonify({
                'success': True,
                'is_favorite': True,
                'message': 'Added to your favorites!'
            })
    except Exception as e:
        logger.error("Error toggling favorite for user_id=%s, place_id=%s: %s", user_id, place_id, e)
        return jsonify({'success': False, 'message': 'Database error occurred. Please try again.'}), 500


# ---------------------------------------------------------
# Trip Planner / Itinerary Builder Routes
# ---------------------------------------------------------

@app.route('/itineraries')
@app.route('/itinerary')
def itineraries():
    """View list of user's custom travel itineraries."""
    if 'user_id' not in session:
        flash("Please log in to plan trips and view your travel itineraries.", "info")
        return redirect(url_for('login', next=request.path))

    user_id = session['user_id']
    query = """
        SELECT i.*, COUNT(it.item_id) as total_stops
        FROM itineraries i
        LEFT JOIN itinerary_items it ON i.itinerary_id = it.itinerary_id
        WHERE i.user_id = %s
        GROUP BY i.itinerary_id
        ORDER BY i.itinerary_id DESC
    """
    try:
        user_itineraries = query_db(query, (user_id,), fetchall=True) or []
    except Exception as e:
        logger.error("Error retrieving itineraries for user_id=%s: %s", user_id, e)
        user_itineraries = []

    return render_template('itinerary.html', itineraries=user_itineraries)


@app.route('/itinerary/<int:itinerary_id>')
def itinerary_detail(itinerary_id):
    """View a specific trip plan with day-by-day stops and multi-stop map routing."""
    if 'user_id' not in session:
        flash("Please log in to view this trip itinerary.", "warning")
        return redirect(url_for('login', next=request.path))

    user_id = session['user_id']
    try:
        trip = query_db("SELECT * FROM itineraries WHERE itinerary_id = %s AND user_id = %s", (itinerary_id, user_id), fetchone=True)
    except Exception as e:
        logger.error("Error fetching itinerary_id=%s: %s", itinerary_id, e)
        trip = None

    if not trip:
        flash("Trip itinerary not found or access denied.", "warning")
        return redirect(url_for('itineraries'))

    items_query = """
        SELECT it.*, p.name as place_name, p.location, p.category, p.image, p.timings, p.entry_fee, p.latitude, p.longitude
        FROM itinerary_items it
        JOIN tourist_places p ON it.place_id = p.place_id
        WHERE it.itinerary_id = %s
        ORDER BY it.day_number ASC, it.order_index ASC, it.item_id ASC
    """
    try:
        items = query_db(items_query, (itinerary_id,), fetchall=True) or []
    except Exception as e:
        logger.error("Error fetching items for itinerary_id=%s: %s", itinerary_id, e)
        items = []

    # Group items by day_number
    days_dict = defaultdict(list)
    for itm in items:
        days_dict[itm['day_number']].append(itm)
    sorted_days = sorted(days_dict.items(), key=lambda x: x[0])

    # Build multi-stop Google Maps directions link if coordinates available
    coords_list = [f"{itm['latitude']},{itm['longitude']}" for itm in items if itm.get('latitude') and itm.get('longitude')]
    google_maps_route = None
    if coords_list:
        if len(coords_list) == 1:
            google_maps_route = f"https://www.google.com/maps/dir/?api=1&destination={coords_list[0]}"
        else:
            origin = coords_list[0]
            destination = coords_list[-1]
            waypoints = '|'.join(coords_list[1:-1])
            google_maps_route = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}"
            if waypoints:
                google_maps_route += f"&waypoints={waypoints}"

    return render_template('itinerary_detail.html', trip=trip, days=sorted_days, total_stops=len(items), google_maps_route=google_maps_route)


@app.route('/api/itinerary/create', methods=['POST'])
def api_itinerary_create():
    """Creates a new trip itinerary for authenticated user."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required. Please login.'}), 401

    data = request.get_json(silent=True) or request.form
    title = (data.get('title') or '').strip()
    description = (data.get('description') or '').strip()

    if not title:
        return jsonify({'success': False, 'message': 'Trip title is required.'}), 400

    user_id = session['user_id']
    try:
        itinerary_id = query_db(
            "INSERT INTO itineraries (user_id, title, description) VALUES (%s, %s, %s)",
            (user_id, title, description),
            commit=True
        )
        if request.is_json:
            return jsonify({'success': True, 'itinerary_id': itinerary_id, 'message': f"Trip '{title}' created!"})
        flash(f"Trip '{title}' created successfully!", "success")
        return redirect(url_for('itinerary_detail', itinerary_id=itinerary_id))
    except Exception as e:
        logger.error("Error creating itinerary for user_id=%s: %s", user_id, e)
        if request.is_json:
            return jsonify({'success': False, 'message': 'Failed to create trip.'}), 500
        flash("Could not create trip. Please try again.", "danger")
        return redirect(url_for('itineraries'))


@app.route('/api/itinerary/add_place', methods=['POST'])
def api_itinerary_add_place():
    """Adds a tourist destination stop to an itinerary."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required. Please login.'}), 401

    data = request.get_json(silent=True) or request.form
    try:
        itinerary_id = int(data.get('itinerary_id'))
        place_id = int(data.get('place_id'))
        day_number = max(1, int(data.get('day_number', 1)))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Valid itinerary_id and place_id are required.'}), 400

    notes = (data.get('notes') or '').strip()
    user_id = session['user_id']

    # Verify ownership of itinerary
    try:
        trip = query_db("SELECT itinerary_id FROM itineraries WHERE itinerary_id = %s AND user_id = %s", (itinerary_id, user_id), fetchone=True)
        if not trip:
            return jsonify({'success': False, 'message': 'Itinerary not found or access denied.'}), 403

        query_db(
            """INSERT INTO itinerary_items (itinerary_id, place_id, day_number, notes)
               VALUES (%s, %s, %s, %s)""",
            (itinerary_id, place_id, day_number, notes),
            commit=True
        )
        return jsonify({'success': True, 'message': 'Destination added to trip itinerary!'})
    except Exception as e:
        logger.error("Error adding stop to itinerary_id=%s: %s", itinerary_id, e)
        return jsonify({'success': False, 'message': 'Could not add destination.'}), 500


@app.route('/api/itinerary/remove_item', methods=['POST'])
def api_itinerary_remove_item():
    """Removes a stop from an itinerary."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    data = request.get_json(silent=True) or request.form
    try:
        item_id = int(data.get('item_id'))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Valid item_id is required.'}), 400

    user_id = session['user_id']
    try:
        item = query_db(
            """SELECT it.item_id, it.itinerary_id 
               FROM itinerary_items it 
               JOIN itineraries i ON it.itinerary_id = i.itinerary_id 
               WHERE it.item_id = %s AND i.user_id = %s""",
            (item_id, user_id),
            fetchone=True
        )
        if not item:
            return jsonify({'success': False, 'message': 'Stop not found or access denied.'}), 403

        query_db("DELETE FROM itinerary_items WHERE item_id = %s", (item_id,), commit=True)
        return jsonify({'success': True, 'message': 'Stop removed from itinerary.'})
    except Exception as e:
        logger.error("Error removing item_id=%s: %s", item_id, e)
        return jsonify({'success': False, 'message': 'Could not remove stop.'}), 500


@app.route('/api/itinerary/delete/<int:itinerary_id>', methods=['POST'])
def api_itinerary_delete(itinerary_id):
    """Deletes an entire itinerary."""
    if 'user_id' not in session:
        flash("Authentication required.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    try:
        query_db("DELETE FROM itineraries WHERE itinerary_id = %s AND user_id = %s", (itinerary_id, user_id), commit=True)
        flash("Trip itinerary deleted successfully.", "success")
    except Exception as e:
        logger.error("Error deleting itinerary_id=%s: %s", itinerary_id, e)
        flash("Could not delete itinerary.", "danger")

    return redirect(url_for('itineraries'))


@app.route('/api/user/itineraries')
def api_user_itineraries():
    """Returns active user's itineraries in JSON for quick destination addition modals."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'itineraries': []})
    try:
        trips = query_db("SELECT itinerary_id, title FROM itineraries WHERE user_id = %s ORDER BY itinerary_id DESC", (session['user_id'],), fetchall=True) or []
        return jsonify({'success': True, 'itineraries': trips})
    except Exception as e:
        logger.error("Error fetching user itineraries: %s", e)
        return jsonify({'success': False, 'itineraries': []})


@app.route('/api/places')
def api_places():
    """Public API endpoint returning all places in JSON format for offline caching."""
    try:
        places = query_db("SELECT * FROM tourist_places ORDER BY name ASC", fetchall=True) or []
        return jsonify({'success': True, 'places': places})
    except Exception as e:
        logger.error("Error in api_places: %s", e)
        return jsonify({'success': False, 'places': [], 'error': 'Could not fetch places.'}), 500


@app.route('/api/nearby')
def api_nearby():
    """
    Returns tourist destinations sorted by proximity to the provided lat and lng coordinates.
    Voluntary browser Geolocation API consumes this endpoint.
    """
    try:
        lat = float(request.args.get('lat', ''))
        lng = float(request.args.get('lng', ''))
    except (ValueError, TypeError):
        return jsonify({
            'success': False,
            'message': 'Valid numeric lat and lng query parameters are required.'
        }), 400

    limit = request.args.get('limit', 6, type=int)

    try:
        places = query_db(
            "SELECT * FROM tourist_places WHERE latitude IS NOT NULL AND longitude IS NOT NULL",
            fetchall=True
        ) or []

        nearby_places = []
        for p in places:
            try:
                p_lat = float(p['latitude'])
                p_lng = float(p['longitude'])
                dist_km = haversine(lat, lng, p_lat, p_lng)
                p_copy = dict(p)
                p_copy['distance_km'] = round(dist_km, 1)
                nearby_places.append(p_copy)
            except (ValueError, TypeError):
                continue

        # Sort ascending by distance
        nearby_places.sort(key=lambda x: x['distance_km'])

        return jsonify({
            'success': True,
            'places': nearby_places[:limit]
        })
    except Exception as e:
        logger.error("Error calculating nearby places for (%s, %s): %s", lat, lng, e)
        return jsonify({'success': False, 'message': 'Failed to calculate nearby destinations.'}), 500


@app.route('/api/health')
def api_health():
    """
    Safe health check endpoint for monitoring deployment status and database connectivity.
    Never exposes passwords, tokens, or sensitive credentials.
    """
    db_status = check_db_status()
    is_healthy = db_status['connected']
    return jsonify({
        'status': 'healthy' if is_healthy else 'degraded',
        'database': db_status
    }), (200 if is_healthy else 503)


# ---------------------------------------------------------
# Admin Module Routes
# ---------------------------------------------------------

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login authentication route with brute-force rate limiting."""
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        client_ip = request.remote_addr or 'unknown'

        if is_rate_limited(client_ip):
            flash("Too many failed login attempts. Please wait 5 minutes before trying again.", "danger")
            return render_template('admin_login.html')

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template('admin_login.html')

        if verify_admin_credentials(username, password):
            clear_failed_attempts(client_ip)
            session.clear()
            session['is_admin'] = True
            session['admin_user'] = username
            logger.info("Admin successfully authenticated: username=%s from IP=%s", username, client_ip)
            flash("Welcome Admin! Access granted.", "success")
            next_url = request.args.get('next')
            if is_safe_url(next_url):
                return redirect(next_url)
            return redirect(url_for('admin_dashboard'))
        else:
            record_failed_attempt(client_ip)
            logger.warning("Failed admin authentication for username=%s from IP=%s", username, client_ip)
            flash("Invalid admin credentials. Access denied.", "danger")

    return render_template('admin_login.html')


@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin Dashboard displaying system statistics and CRUD interface."""
    try:
        places = query_db("SELECT * FROM tourist_places ORDER BY place_id DESC", fetchall=True) or []
        users = query_db("SELECT user_id, name, email, created_at FROM users ORDER BY user_id DESC", fetchall=True) or []
        favs_row = query_db("SELECT COUNT(*) as cnt FROM favorites", fetchone=True)
        total_favs = favs_row['cnt'] if favs_row else 0
        itin_row = query_db("SELECT COUNT(*) as cnt FROM itineraries", fetchone=True)
        total_itineraries = itin_row['cnt'] if itin_row else 0
    except Exception as e:
        logger.error("Error loading admin dashboard data: %s", e)
        places = []
        users = []
        total_favs = 0
        total_itineraries = 0
        flash("Could not load dashboard data from database.", "warning")

    return render_template(
        'admin.html',
        places=places,
        users=users,
        total_favs=total_favs,
        total_itineraries=total_itineraries
    )


@app.route('/admin/place/add', methods=['POST'])
@admin_required
def admin_add_place():
    """Add a new tourist destination with optional coordinates."""
    name = request.form.get('name', '').strip()
    location = request.form.get('location', '').strip()
    description = request.form.get('description', '').strip()
    timings = request.form.get('timings', '9:00 AM - 5:00 PM').strip()
    entry_fee = request.form.get('entry_fee', 'Free').strip()
    category = request.form.get('category', 'Heritage').strip()
    image = request.form.get('image', 'default_place.jpg').strip() or 'default_place.jpg'

    lat_raw = request.form.get('latitude', '').strip()
    lng_raw = request.form.get('longitude', '').strip()
    try:
        latitude = float(lat_raw) if lat_raw else None
    except ValueError:
        latitude = None
    try:
        longitude = float(lng_raw) if lng_raw else None
    except ValueError:
        longitude = None

    if not name or not location or not description:
        flash("Name, Location, and Description are required.", "danger")
        return redirect(url_for('admin_dashboard'))

    try:
        query_db(
            """INSERT INTO tourist_places (name, location, description, timings, entry_fee, image, category, latitude, longitude)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (name, location, description, timings, entry_fee, image, category, latitude, longitude),
            commit=True
        )
        logger.info("Admin %s added place '%s'", session.get('admin_user'), name)
        flash(f"Tourist destination '{name}' added successfully!", "success")
    except Exception as e:
        logger.error("Error adding place '%s': %s", name, e)
        flash("Error adding tourist destination. Please check database logs.", "danger")

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/place/edit/<int:place_id>', methods=['POST'])
@admin_required
def admin_edit_place(place_id):
    """Edit an existing tourist destination."""
    name = request.form.get('name', '').strip()
    location = request.form.get('location', '').strip()
    description = request.form.get('description', '').strip()
    timings = request.form.get('timings', '').strip()
    entry_fee = request.form.get('entry_fee', '').strip()
    category = request.form.get('category', '').strip()
    image = request.form.get('image', '').strip() or 'default_place.jpg'

    lat_raw = request.form.get('latitude', '').strip()
    lng_raw = request.form.get('longitude', '').strip()
    try:
        latitude = float(lat_raw) if lat_raw else None
    except ValueError:
        latitude = None
    try:
        longitude = float(lng_raw) if lng_raw else None
    except ValueError:
        longitude = None

    if not name or not location or not description:
        flash("Name, Location, and Description are required.", "danger")
        return redirect(url_for('admin_dashboard'))

    try:
        query_db(
            """UPDATE tourist_places 
               SET name = %s, location = %s, description = %s, timings = %s, 
                   entry_fee = %s, category = %s, image = %s, latitude = %s, longitude = %s
               WHERE place_id = %s""",
            (name, location, description, timings, entry_fee, category, image, latitude, longitude, place_id),
            commit=True
        )
        logger.info("Admin %s updated place_id=%s ('%s')", session.get('admin_user'), place_id, name)
        flash(f"Tourist destination '{name}' updated successfully!", "success")
    except Exception as e:
        logger.error("Error updating place_id=%s: %s", place_id, e)
        flash("Error updating tourist destination.", "danger")

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/place/delete/<int:place_id>', methods=['POST'])
@admin_required
def admin_delete_place(place_id):
    """Delete a tourist destination."""
    try:
        query_db("DELETE FROM tourist_places WHERE place_id = %s", (place_id,), commit=True)
        logger.info("Admin %s deleted place_id=%s", session.get('admin_user'), place_id)
        flash("Tourist destination deleted successfully.", "success")
    except Exception as e:
        logger.error("Error deleting place_id=%s: %s", place_id, e)
        flash("Error deleting tourist destination.", "danger")

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/logout')
def admin_logout():
    """Logout from Admin session."""
    admin_user = session.get('admin_user', 'Admin')
    session.clear()
    logger.info("Admin %s logged out", admin_user)
    flash("Admin logged out successfully.", "info")
    return redirect(url_for('home'))


# ---------------------------------------------------------
# Custom HTTP Error Handlers
# ---------------------------------------------------------

@app.errorhandler(404)
def not_found_error(error):
    """Polished 404 Page Not Found error handler."""
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'message': 'API endpoint not found.'}), 404
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(error):
    """Polished 500 Internal Server Error handler."""
    logger.error("Internal Server Error on %s: %s", request.path, error, exc_info=True)
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'message': 'Internal server error occurred.'}), 500
    return render_template('500.html'), 500


@app.errorhandler(403)
def forbidden_error(error):
    """403 Forbidden handler."""
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'message': 'Access forbidden or CSRF validation failed.'}), 403
    flash("Access forbidden or security token expired. Please try again.", "danger")
    return redirect(url_for('home'))


# ---------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------
if __name__ == '__main__':
    print("=========================================================")
    print(" Tourist Guide PWA Server starting on http://127.0.0.1:5000")
    print("=========================================================")
    app.run(debug=True, host='0.0.0.0', port=5000)
