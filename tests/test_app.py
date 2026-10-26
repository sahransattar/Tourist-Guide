"""
=========================================================
Tourist Guide PWA - Automated Test Suite (tests/test_app.py)
Verifies Registration, Auth, Security, CSRF, Admin & Database
=========================================================
"""

import os
import re
import unittest
from werkzeug.security import generate_password_hash, check_password_hash

# Ensure test runs in development / test mode with isolated test SQLite db
os.environ['FLASK_ENV'] = 'testing'
os.environ.pop('VERCEL', None)
os.environ['ADMIN_USERNAME'] = 'testadmin'
os.environ['ADMIN_PASSWORD_HASH'] = generate_password_hash('SuperSecretAdminPass123!')
os.environ['SECRET_KEY'] = 'test_secret_key_9999_xyz'

import app as flask_app
import database


class TouristGuideAppTestCase(unittest.TestCase):

    def setUp(self):
        self.app = flask_app.app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = True
        self.client = self.app.test_client()

        # Clear login rate-limiting cache before each test
        flask_app.login_attempts.clear()

        # Ensure database is freshly initialized and test users cleaned up
        database.db_instance.use_mysql = False
        database.db_instance._init_sqlite_schema()
        database.query_db(
            "DELETE FROM users WHERE email NOT IN ('john@example.com', 'alice@example.com')",
            commit=True
        )
        database.query_db("DELETE FROM favorites", commit=True)
        database.query_db("DELETE FROM itinerary_items", commit=True)
        database.query_db("DELETE FROM itineraries", commit=True)

    def get_csrf_token(self, response_data):
        """Helper to extract CSRF token from HTML response."""
        html = response_data.decode('utf-8')
        match = re.search(r'name=["\']csrf_token["\']\s+value=["\']([a-f0-9]+)["\']', html)
        if match:
            return match.group(1)
        match_meta = re.search(r'<meta\s+name=["\']csrf-token["\']\s+content=["\']([a-f0-9]+)["\']', html)
        if match_meta:
            return match_meta.group(1)
        return None

    # -----------------------------------------------------
    # 1. Registration Tests
    # -----------------------------------------------------

    def test_registration_success(self):
        """Verify that a new user can register successfully with password hashing."""
        get_res = self.client.get('/register')
        csrf_token = self.get_csrf_token(get_res.data)
        self.assertIsNotNone(csrf_token)

        post_data = {
            'csrf_token': csrf_token,
            'name': 'Test Traveler',
            'email': 'newtraveler@example.com',
            'password': 'SecurePassword456!'
        }
        res = self.client.post('/register', data=post_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Registration successful', res.data)

        # Verify password is saved as HASH and NOT plaintext in database
        user = database.query_db("SELECT * FROM users WHERE email = %s", ('newtraveler@example.com',), fetchone=True)
        self.assertIsNotNone(user)
        self.assertEqual(user['name'], 'Test Traveler')
        self.assertNotEqual(user['password'], 'SecurePassword456!')
        self.assertTrue(check_password_hash(user['password'], 'SecurePassword456!'))

    def test_registration_duplicate_email(self):
        """Verify that duplicate email registrations are handled gracefully."""
        get_res = self.client.get('/register')
        csrf_token = self.get_csrf_token(get_res.data)

        # Try registering existing demo user
        post_data = {
            'csrf_token': csrf_token,
            'name': 'Duplicate Person',
            'email': 'john@example.com',
            'password': 'SomePassword123'
        }
        res = self.client.post('/register', data=post_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'already exists', res.data)

    def test_registration_validation_rules(self):
        """Verify missing fields, invalid email format, and short passwords are rejected."""
        get_res = self.client.get('/register')
        csrf_token = self.get_csrf_token(get_res.data)

        # Short password (< 6 chars)
        res = self.client.post('/register', data={
            'csrf_token': csrf_token,
            'name': 'Bob',
            'email': 'bob@example.com',
            'password': '123'
        }, follow_redirects=True)
        self.assertIn(b'at least 6 characters', res.data)

        # Invalid email format
        res = self.client.post('/register', data={
            'csrf_token': csrf_token,
            'name': 'Bob',
            'email': 'not-an-email',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'valid email address', res.data)

    def test_registration_csrf_protection(self):
        """Verify that registration requests missing a CSRF token are blocked."""
        res = self.client.post('/register', data={
            'name': 'Attacker',
            'email': 'attacker@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        # Should be rejected
        self.assertIn(b'expired', res.data)
        user = database.query_db("SELECT * FROM users WHERE email = %s", ('attacker@example.com',), fetchone=True)
        self.assertIsNone(user)

    # -----------------------------------------------------
    # 2. Authentication & Backward-Compatible Migration Tests
    # -----------------------------------------------------

    def test_user_login_success(self):
        """Verify that a registered user can log in with hashed password."""
        get_res = self.client.get('/login')
        csrf_token = self.get_csrf_token(get_res.data)

        # Log in as demo user john@example.com (password: user123)
        res = self.client.post('/login', data={
            'csrf_token': csrf_token,
            'email': 'john@example.com',
            'password': 'user123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Welcome back', res.data)

        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('user_email'), 'john@example.com')

    def test_user_login_invalid_credentials(self):
        """Verify that incorrect credentials fail."""
        get_res = self.client.get('/login')
        csrf_token = self.get_csrf_token(get_res.data)

        res = self.client.post('/login', data={
            'csrf_token': csrf_token,
            'email': 'john@example.com',
            'password': 'WrongPassword999'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email address or password', res.data)

    def test_login_rate_limiting(self):
        """Verify that repeated failed login attempts trigger brute-force rate limiting."""
        get_res = self.client.get('/login')
        csrf_token = self.get_csrf_token(get_res.data)

        # Trigger 5 failed attempts
        for _ in range(5):
            self.client.post('/login', data={
                'csrf_token': csrf_token,
                'email': 'john@example.com',
                'password': 'WrongPassword123'
            })

        # 6th attempt should be rate-limited
        res = self.client.post('/login', data={
            'csrf_token': csrf_token,
            'email': 'john@example.com',
            'password': 'WrongPassword123'
        }, follow_redirects=True)
        self.assertIn(b'Too many failed login attempts', res.data)

    def test_legacy_plaintext_password_migration(self):
        """Verify that legacy plaintext passwords are automatically migrated to Werkzeug hashes on login."""
        # Insert a user with legacy plaintext password
        database.query_db(
            "INSERT OR REPLACE INTO users (name, email, password) VALUES (?, ?, ?)",
            ('Legacy User', 'legacy@example.com', 'plaintextpassword123'),
            commit=True
        )

        # Confirm user starts with plaintext
        u_before = database.query_db("SELECT * FROM users WHERE email = %s", ('legacy@example.com',), fetchone=True)
        self.assertEqual(u_before['password'], 'plaintextpassword123')

        # User logs in with that password
        get_res = self.client.get('/login')
        csrf_token = self.get_csrf_token(get_res.data)
        res = self.client.post('/login', data={
            'csrf_token': csrf_token,
            'email': 'legacy@example.com',
            'password': 'plaintextpassword123'
        }, follow_redirects=True)
        self.assertIn(b'Welcome back', res.data)

        # Verify password in database was transparently migrated to a hash!
        u_after = database.query_db("SELECT * FROM users WHERE email = %s", ('legacy@example.com',), fetchone=True)
        self.assertNotEqual(u_after['password'], 'plaintextpassword123')
        self.assertTrue(check_password_hash(u_after['password'], 'plaintextpassword123'))

    def test_logout_clears_session(self):
        """Verify that logout invalidates the user session."""
        # Log in first
        get_res = self.client.get('/login')
        csrf_token = self.get_csrf_token(get_res.data)
        self.client.post('/login', data={
            'csrf_token': csrf_token,
            'email': 'john@example.com',
            'password': 'user123'
        })
        with self.client.session_transaction() as sess:
            self.assertIsNotNone(sess.get('user_id'))

        # Log out
        res = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'logged out successfully', res.data)
        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get('user_id'))

    # -----------------------------------------------------
    # 3. Admin Security & Access Control Tests
    # -----------------------------------------------------

    def test_admin_login_success(self):
        """Verify that configured admin credentials work."""
        get_res = self.client.get('/admin/login')
        csrf_token = self.get_csrf_token(get_res.data)

        res = self.client.post('/admin/login', data={
            'csrf_token': csrf_token,
            'username': 'testadmin',
            'password': 'SuperSecretAdminPass123!'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Welcome Admin', res.data)

        with self.client.session_transaction() as sess:
            self.assertTrue(sess.get('is_admin'))
            self.assertEqual(sess.get('admin_user'), 'testadmin')

    def test_admin_login_failure(self):
        """Verify that invalid admin credentials fail."""
        get_res = self.client.get('/admin/login')
        csrf_token = self.get_csrf_token(get_res.data)

        res = self.client.post('/admin/login', data={
            'csrf_token': csrf_token,
            'username': 'testadmin',
            'password': 'WrongPassword123'
        }, follow_redirects=True)
        self.assertIn(b'Invalid admin credentials', res.data)

        with self.client.session_transaction() as sess:
            self.assertFalse(sess.get('is_admin', False))

    def test_unauthorized_user_cannot_access_admin_dashboard(self):
        """Verify that an unauthenticated visitor is redirected away from /admin."""
        res = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b'Admin authentication required', res.data)

    def test_normal_user_cannot_perform_admin_crud(self):
        """Verify that a logged-in regular user cannot perform administrative actions."""
        # Log in as normal user
        get_res = self.client.get('/login')
        csrf_token = self.get_csrf_token(get_res.data)
        self.client.post('/login', data={
            'csrf_token': csrf_token,
            'email': 'john@example.com',
            'password': 'user123'
        })

        home_res = self.client.get('/')
        user_csrf = self.get_csrf_token(home_res.data)

        # Attempt to add a place via POST to /admin/place/add
        res = self.client.post('/admin/place/add', data={
            'csrf_token': user_csrf,
            'name': 'Hacked Monument',
            'location': 'Nowhere',
            'description': 'Malicious entry'
        }, follow_redirects=True)
        self.assertIn(b'Admin authentication required', res.data)

        # Verify place was NOT added
        hacked = database.query_db("SELECT * FROM tourist_places WHERE name = %s", ('Hacked Monument',), fetchone=True)
        self.assertIsNone(hacked)

    def test_admin_crud_authorized(self):
        """Verify that an authorized admin can Add, Edit, and Delete places."""
        # 1. Admin login
        get_res = self.client.get('/admin/login')
        csrf_token = self.get_csrf_token(get_res.data)
        self.client.post('/admin/login', data={
            'csrf_token': csrf_token,
            'username': 'testadmin',
            'password': 'SuperSecretAdminPass123!'
        })

        # Fetch dashboard to obtain the new post-login session CSRF token
        dash_res = self.client.get('/admin')
        admin_csrf = self.get_csrf_token(dash_res.data)
        self.assertIsNotNone(admin_csrf)

        # 2. Add Place
        res_add = self.client.post('/admin/place/add', data={
            'csrf_token': admin_csrf,
            'name': 'Mysore Palace',
            'location': 'Mysuru, Karnataka',
            'description': 'A historic palace and a royal residence.',
            'category': 'Palace',
            'timings': '10:00 AM - 5:30 PM',
            'entry_fee': '₹100',
            'image': 'mysore_palace.jpg'
        }, follow_redirects=True)
        self.assertIn(b'added successfully', res_add.data)

        added = database.query_db("SELECT * FROM tourist_places WHERE name = %s", ('Mysore Palace',), fetchone=True)
        self.assertIsNotNone(added)
        place_id = added['place_id']

        # 3. Edit Place
        res_edit = self.client.post(f'/admin/place/edit/{place_id}', data={
            'csrf_token': admin_csrf,
            'name': 'Mysore Palace (Updated)',
            'location': 'Mysuru, Karnataka',
            'description': 'Updated palace description.',
            'category': 'Palace',
            'timings': '10:00 AM - 5:30 PM',
            'entry_fee': '₹120',
            'image': 'mysore_palace.jpg'
        }, follow_redirects=True)
        self.assertIn(b'updated successfully', res_edit.data)

        updated = database.query_db("SELECT * FROM tourist_places WHERE place_id = %s", (place_id,), fetchone=True)
        self.assertEqual(updated['name'], 'Mysore Palace (Updated)')

        # 4. Delete Place
        res_del = self.client.post(f'/admin/place/delete/{place_id}', data={
            'csrf_token': admin_csrf
        }, follow_redirects=True)
        self.assertIn(b'deleted successfully', res_del.data)

        deleted = database.query_db("SELECT * FROM tourist_places WHERE place_id = %s", (place_id,), fetchone=True)
        self.assertIsNone(deleted)

    # -----------------------------------------------------
    # 4. Favorites & ID Isolation Tests
    # -----------------------------------------------------

    def test_favorites_requires_auth(self):
        """Verify that anonymous users cannot toggle favorites."""
        get_res = self.client.get('/')
        csrf_token = self.get_csrf_token(get_res.data)
        res = self.client.post(
            '/api/favorites/toggle',
            headers={'X-CSRFToken': csrf_token},
            json={'place_id': 1}
        )
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertFalse(data['success'])
        self.assertIn('Authentication required', data['message'])

    def test_favorites_toggle_isolated_to_session_user(self):
        """Verify that favorites are strictly tied to the logged-in session user."""
        # Log in as John
        get_res = self.client.get('/login')
        csrf_token = self.get_csrf_token(get_res.data)
        self.client.post('/login', data={
            'csrf_token': csrf_token,
            'email': 'john@example.com',
            'password': 'user123'
        })

        home_res = self.client.get('/')
        user_csrf = self.get_csrf_token(home_res.data)

        # Toggle favorite for place 1
        res = self.client.post(
            '/api/favorites/toggle',
            headers={'X-CSRFToken': user_csrf},
            json={'place_id': 1}
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_favorite'])

        # Verify favorite in DB belongs to John (user_id=1)
        fav = database.query_db("SELECT * FROM favorites WHERE user_id = 1 AND place_id = 1", fetchone=True)
        self.assertIsNotNone(fav)

    # -----------------------------------------------------
    # 5. Search & Health Check Tests
    # -----------------------------------------------------

    def test_places_search_and_filter(self):
        """Verify that search and category filtering work correctly."""
        res_search = self.client.get('/places?q=Taj')
        self.assertEqual(res_search.status_code, 200)
        self.assertIn(b'Taj Mahal', res_search.data)

        res_cat = self.client.get('/places?category=Beach')
        self.assertEqual(res_cat.status_code, 200)
        self.assertIn(b'Goa Beaches', res_cat.data)

    def test_health_check_endpoint(self):
        """Verify that /api/health provides safe diagnostic status."""
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertTrue(data['database']['connected'])

    # -----------------------------------------------------
    # 6. Geolocation & Haversine Proximity Tests
    # -----------------------------------------------------

    def test_nearby_places_api_validation(self):
        """Verify /api/nearby requires numeric lat and lng query params."""
        res_missing = self.client.get('/api/nearby')
        self.assertEqual(res_missing.status_code, 400)
        data = res_missing.get_json()
        self.assertFalse(data['success'])

        res_invalid = self.client.get('/api/nearby?lat=abc&lng=xyz')
        self.assertEqual(res_invalid.status_code, 400)

    def test_nearby_places_api_distance_ordering(self):
        """Verify /api/nearby returns destinations ordered by proximity (Haversine formula)."""
        # Agra coordinates: 27.1751, 78.0421 (Taj Mahal)
        res = self.client.get('/api/nearby?lat=27.1751&lng=78.0421&limit=3')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertTrue(len(data['places']) > 0)
        # Closest destination to Agra coordinates should be Taj Mahal
        first_place = data['places'][0]
        self.assertEqual(first_place['name'], 'Taj Mahal')
        self.assertLess(first_place['distance_km'], 1.0)

    # -----------------------------------------------------
    # 7. Sorting & Pagination Tests
    # -----------------------------------------------------

    def test_places_sorting_and_pagination(self):
        """Verify sorting by name descending and pagination controls."""
        res_desc = self.client.get('/places?sort_by=name_desc')
        self.assertEqual(res_desc.status_code, 200)
        self.assertIn(b'Varanasi', res_desc.data)

        res_page = self.client.get('/places?page=1')
        self.assertEqual(res_page.status_code, 200)
        self.assertIn(b'Showing', res_page.data)

    # -----------------------------------------------------
    # 8. Custom Error Handling Tests
    # -----------------------------------------------------

    def test_custom_404_error_page(self):
        """Verify non-existent place and URL returns custom 404 template with 404 status."""
        res_place = self.client.get('/place/999999')
        self.assertEqual(res_place.status_code, 404)
        self.assertIn(b'Destination Not Found', res_place.data)

        res_route = self.client.get('/unknown-page-route')
        self.assertEqual(res_route.status_code, 404)
        self.assertIn(b'Destination Not Found', res_route.data)

    def test_admin_add_place_with_coordinates(self):
        """Verify admin can add destination with geographic GPS coordinates."""
        login_res = self.client.get('/admin/login')
        csrf_token = self.get_csrf_token(login_res.data)
        self.client.post('/admin/login', data={
            'csrf_token': csrf_token,
            'username': 'testadmin',
            'password': 'SuperSecretAdminPass123!'
        })

        admin_res = self.client.get('/admin')
        admin_csrf = self.get_csrf_token(admin_res.data)

        new_place_data = {
            'csrf_token': admin_csrf,
            'name': 'Hampi Ruins',
            'location': 'Hampi, Karnataka',
            'description': 'Ancient capital of Vijayanagara empire.',
            'category': 'Heritage',
            'timings': '6:00 AM - 6:00 PM',
            'entry_fee': '₹40',
            'image': 'default_place.jpg',
            'latitude': '15.3350',
            'longitude': '76.4600'
        }
        res = self.client.post('/admin/place/add', data=new_place_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        place = database.query_db("SELECT * FROM tourist_places WHERE name = 'Hampi Ruins'", fetchone=True)
        self.assertIsNotNone(place)
        self.assertAlmostEqual(float(place['latitude']), 15.3350, places=3)
        self.assertAlmostEqual(float(place['longitude']), 76.4600, places=3)

        # Cleanup
        database.query_db("DELETE FROM tourist_places WHERE name = 'Hampi Ruins'", commit=True)

    # -----------------------------------------------------
    # 9. Expanded Destinations & Image URL Filter Tests
    # -----------------------------------------------------

    def test_expanded_destinations_count_and_coordinates(self):
        """Verify that destination database contains at least 60 verified destinations with GPS coordinates."""
        row = database.query_db("SELECT COUNT(*) as cnt FROM tourist_places", fetchone=True)
        count = row['cnt'] if row else 0
        self.assertGreaterEqual(count, 60, f"Expected at least 60 destinations, found {count}")

        # Verify GPS coordinates coverage
        places_with_coords = database.query_db(
            "SELECT COUNT(*) as cnt FROM tourist_places WHERE latitude IS NOT NULL AND longitude IS NOT NULL",
            fetchone=True
        )
        self.assertGreaterEqual(places_with_coords['cnt'], 60)

        # Verify diversity of categories
        categories = database.query_db("SELECT DISTINCT category FROM tourist_places", fetchall=True)
        cat_set = {c['category'] for c in categories}
        for expected_cat in ['Heritage', 'Palace', 'Beach', 'Nature', 'Spiritual']:
            self.assertIn(expected_cat, cat_set)

    def test_image_url_jinja_filter(self):
        """Verify image_url filter handles remote URLs, local filenames, and empty fallbacks correctly."""
        with self.app.test_request_context():
            # Remote URLs must be returned untouched
            remote_url = "https://images.unsplash.com/photo-1564507592333-c60657eea523"
            self.assertEqual(flask_app.image_url_filter(remote_url), remote_url)

            remote_http = "http://example.com/tourist.jpg"
            self.assertEqual(flask_app.image_url_filter(remote_http), remote_http)

            # Local filenames must be prefixed with /static/images/
            self.assertEqual(flask_app.image_url_filter("taj_mahal.jpg"), "/static/images/taj_mahal.jpg")

            # Empty or None must return default placeholder
            self.assertEqual(flask_app.image_url_filter(None), "/static/images/default_place.jpg")
            self.assertEqual(flask_app.image_url_filter(""), "/static/images/default_place.jpg")

    # -----------------------------------------------------
    # 10. Trip Planner / Itinerary Builder Workflow Tests
    # -----------------------------------------------------

    def test_itinerary_full_workflow(self):
        """Verify trip creation, adding stops, viewing itinerary, and deletion."""
        # Step 1: Login as demo user john@example.com
        login_res = self.client.get('/login')
        csrf_token = self.get_csrf_token(login_res.data)
        self.client.post('/login', data={
            'csrf_token': csrf_token,
            'email': 'john@example.com',
            'password': 'user123'
        }, follow_redirects=True)

        # Step 2: Access /itineraries page
        itin_page = self.client.get('/itineraries')
        self.assertEqual(itin_page.status_code, 200)
        self.assertIn(b'My Trip Itineraries', itin_page.data)

        # Step 3: Create a new Itinerary
        itin_csrf = self.get_csrf_token(itin_page.data)
        create_res = self.client.post('/api/itinerary/create', data={
            'csrf_token': itin_csrf,
            'title': 'Test Golden Triangle Tour',
            'description': '3-day exploration of heritage marvels',
            'start_date': '2026-11-01',
            'end_date': '2026-11-03'
        }, follow_redirects=True)
        self.assertEqual(create_res.status_code, 200)
        self.assertIn(b'Test Golden Triangle Tour', create_res.data)

        # Fetch created itinerary ID
        itin_row = database.query_db(
            "SELECT itinerary_id FROM itineraries WHERE title = %s",
            ('Test Golden Triangle Tour',),
            fetchone=True
        )
        self.assertIsNotNone(itin_row)
        itin_id = itin_row['itinerary_id']

        # Step 4: Add a destination stop to this itinerary
        place = database.query_db("SELECT place_id, name FROM tourist_places LIMIT 1", fetchone=True)
        self.assertIsNotNone(place)

        fresh_csrf = self.get_csrf_token(create_res.data)
        add_stop_res = self.client.post('/api/itinerary/add_place', json={
            'csrf_token': fresh_csrf,
            'itinerary_id': itin_id,
            'place_id': place['place_id'],
            'day_number': 1,
            'notes': 'Sunrise view at opening time'
        }, headers={'X-CSRFToken': fresh_csrf})
        self.assertEqual(add_stop_res.status_code, 200)
        add_json = add_stop_res.get_json()
        self.assertTrue(add_json['success'])

        # Step 5: View itinerary detail page
        detail_res = self.client.get(f'/itinerary/{itin_id}')
        self.assertEqual(detail_res.status_code, 200)
        self.assertIn(b'Day 1', detail_res.data)
        self.assertIn(place['name'].encode('utf-8'), detail_res.data)

        # Step 6: Delete the itinerary
        del_csrf = self.get_csrf_token(detail_res.data)
        del_res = self.client.post(
            f'/api/itinerary/delete/{itin_id}',
            data={'csrf_token': del_csrf},
            headers={'X-CSRFToken': del_csrf},
            follow_redirects=True
        )
        self.assertEqual(del_res.status_code, 200)
        self.assertIn(b'deleted successfully', del_res.data)


class DatabaseProductionBehaviorTestCase(unittest.TestCase):

    def test_production_without_mysql_raises_config_error(self):
        """Verify that in production (Vercel), missing MySQL raises DatabaseConfigurationError without silent SQLite fallback."""
        import importlib
        os.environ['VERCEL'] = '1'
        os.environ['REQUIRE_EXTERNAL_DB'] = '1'
        os.environ.pop('MYSQL_HOST', None)
        os.environ.pop('DATABASE_URL', None)
        os.environ.pop('MYSQL_URL', None)

        import database as db_mod
        importlib.reload(db_mod)

        # In production without MySQL config, getting DB connection must raise DatabaseConfigurationError
        with self.assertRaises(db_mod.DatabaseConfigurationError):
            db_mod.get_db()

        # Check status reflects production error
        status = db_mod.check_db_status()
        self.assertEqual(status['environment'], 'production')
        self.assertFalse(status['connected'])
        self.assertIn('Production database is not configured', status['error'])

        # Cleanup environment
        os.environ.pop('VERCEL', None)
        os.environ.pop('REQUIRE_EXTERNAL_DB', None)
        importlib.reload(db_mod)


if __name__ == '__main__':
    unittest.main()
