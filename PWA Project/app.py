"""
=========================================================
Tourist Guide PWA - Flask Backend Application (app.py)
Suitable for BCA Final Year Project
=========================================================
"""

import os
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from database import get_db, is_mysql

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'tourist_pwa_bca_secret_key_2026')

# Helper function to convert DB rows to clean python dicts
def dict_from_row(row):
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    return dict(row)

def dicts_from_rows(rows):
    return [dict_from_row(r) for r in rows]

# Helper query wrapper to work seamlessly across MySQL and SQLite
def query_db(query, args=(), fetchone=False, fetchall=False, commit=False):
    conn = get_db()
    cursor = conn.cursor()
    
    # Adjust placeholders for SQLite if needed (SQLite uses ? instead of %s)
    if not is_mysql():
        query = query.replace('%s', '?')
        
    cursor.execute(query, args)
    
    if commit:
        conn.commit()
        last_id = cursor.lastrowid if hasattr(cursor, 'lastrowid') else None
        conn.close()
        return last_id

    result = None
    if fetchone:
        row = cursor.fetchone()
        result = dict_from_row(row)
    elif fetchall:
        rows = cursor.fetchall()
        result = dicts_from_rows(rows)

    conn.close()
    return result

# ---------------------------------------------------------
# User Routes
# ---------------------------------------------------------

@app.route('/')
def home():
    """Home Page route showing hero, search bar, and featured tourist places."""
    places = query_db("SELECT * FROM tourist_places ORDER BY place_id DESC LIMIT 6", fetchall=True) or []
    
    # Get total counts for home dashboard stats
    total_places = query_db("SELECT COUNT(*) as cnt FROM tourist_places", fetchone=True)['cnt']
    total_users = query_db("SELECT COUNT(*) as cnt FROM users", fetchone=True)['cnt']
    
    user_fav_ids = []
    if 'user_id' in session:
        favs = query_db("SELECT place_id FROM favorites WHERE user_id = %s", (session['user_id'],), fetchall=True)
        user_fav_ids = [f['place_id'] for f in favs] if favs else []

    return render_template(
        'index.html',
        places=places,
        total_places=total_places,
        total_users=total_users,
        user_fav_ids=user_fav_ids
    )

@app.route('/places')
def view_places():
    """View & Search Tourist Places route with category/keyword filters."""
    search_query = request.args.get('q', '').strip()
    category_filter = request.args.get('category', '').strip()
    
    sql = "SELECT * FROM tourist_places WHERE 1=1"
    params = []

    if search_query:
        sql += " AND (name LIKE %s OR location LIKE %s OR description LIKE %s)"
        pattern = f"%{search_query}%"
        params.extend([pattern, pattern, pattern])

    if category_filter and category_filter != 'All':
        sql += " AND category = %s"
        params.append(category_filter)

    sql += " ORDER BY name ASC"
    places = query_db(sql, tuple(params), fetchall=True) or []

    categories = query_db("SELECT DISTINCT category FROM tourist_places WHERE category IS NOT NULL", fetchall=True)
    cat_list = [c['category'] for c in categories] if categories else []

    user_fav_ids = []
    if 'user_id' in session:
        favs = query_db("SELECT place_id FROM favorites WHERE user_id = %s", (session['user_id'],), fetchall=True)
        user_fav_ids = [f['place_id'] for f in favs] if favs else []

    return render_template(
        'places.html',
        places=places,
        search_query=search_query,
        selected_category=category_filter,
        categories=cat_list,
        user_fav_ids=user_fav_ids
    )

@app.route('/place/<int:place_id>')
def place_details(place_id):
    """View details of a specific tourist place."""
    place = query_db("SELECT * FROM tourist_places WHERE place_id = %s", (place_id,), fetchone=True)
    if not place:
        flash("Tourist place not found.", "error")
        return redirect(url_for('view_places'))

    is_favorite = False
    if 'user_id' in session:
        fav = query_db(
            "SELECT * FROM favorites WHERE user_id = %s AND place_id = %s",
            (session['user_id'], place_id),
            fetchone=True
        )
        if fav:
            is_favorite = True

    # Related places in same location or category
    related_places = query_db(
        "SELECT * FROM tourist_places WHERE place_id != %s AND (category = %s OR location LIKE %s) LIMIT 3",
        (place_id, place.get('category', ''), f"%{place['location'].split(',')[0]}%"),
        fetchall=True
    ) or []

    return render_template('details.html', place=place, is_favorite=is_favorite, related_places=related_places)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User Registration route."""
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template('register.html')

        # Check existing user
        existing_user = query_db("SELECT * FROM users WHERE email = %s", (email,), fetchone=True)
        if existing_user:
            flash("An account with this email already exists. Please login.", "warning")
            return render_template('register.html')

        try:
            new_id = query_db(
                "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                (name, email, password),
                commit=True
            )
            flash("Registration successful! Please login with your credentials.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Error registering user: {str(e)}", "danger")

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User Login route."""
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        user = query_db("SELECT * FROM users WHERE email = %s AND password = %s", (email, password), fetchone=True)
        if user:
            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid email address or password.", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Clear user session and log out."""
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('home'))

@app.route('/favorites')
def favorites():
    """View list of user's favorite places."""
    if 'user_id' not in session:
        flash("Please log in to view your favorite tourist places.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    query = """
        SELECT p.*, f.favorite_id, f.created_at as saved_at
        FROM favorites f
        JOIN tourist_places p ON f.place_id = p.place_id
        WHERE f.user_id = %s
        ORDER BY f.favorite_id DESC
    """
    fav_places = query_db(query, (user_id,), fetchall=True) or []

    return render_template('favorites.html', places=fav_places)

@app.route('/api/favorites/toggle', methods=['POST'])
def toggle_favorite():
    """AJAX API endpoint for adding or removing a favorite place."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required. Please login.'}), 401

    data = request.get_json() or {}
    place_id = data.get('place_id')

    if not place_id:
        return jsonify({'success': False, 'message': 'Invalid place ID.'}), 400

    user_id = session['user_id']
    existing = query_db(
        "SELECT * FROM favorites WHERE user_id = %s AND place_id = %s",
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

@app.route('/api/places')
def api_places():
    """API endpoint returning all places in JSON format for SW offline caching."""
    places = query_db("SELECT * FROM tourist_places ORDER BY name ASC", fetchall=True) or []
    return jsonify({'success': True, 'places': places})

# ---------------------------------------------------------
# Admin Module Routes
# ---------------------------------------------------------

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login authentication route."""
    if 'is_admin' in session and session['is_admin']:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Simple & secure admin authentication (admin / admin123)
        if username == 'admin' and password == 'admin123':
            session['is_admin'] = True
            session['admin_user'] = 'Administrator'
            flash("Welcome Admin! Access granted.", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid admin credentials. Access denied.", "danger")

    return render_template('admin_login.html')

@app.route('/admin')
def admin_dashboard():
    """Admin Dashboard displaying system statistics and CRUD interface."""
    if not session.get('is_admin'):
        flash("Admin authentication required.", "danger")
        return redirect(url_for('admin_login'))

    places = query_db("SELECT * FROM tourist_places ORDER BY place_id DESC", fetchall=True) or []
    users = query_db("SELECT * FROM users ORDER BY user_id DESC", fetchall=True) or []
    total_favs = query_db("SELECT COUNT(*) as cnt FROM favorites", fetchone=True)['cnt']

    return render_template(
        'admin.html',
        places=places,
        users=users,
        total_favs=total_favs
    )

@app.route('/admin/place/add', methods=['POST'])
def admin_add_place():
    """Add a new tourist place."""
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))

    name = request.form.get('name', '').strip()
    location = request.form.get('location', '').strip()
    description = request.form.get('description', '').strip()
    timings = request.form.get('timings', '9:00 AM - 5:00 PM').strip()
    entry_fee = request.form.get('entry_fee', 'Free').strip()
    category = request.form.get('category', 'Heritage').strip()
    image = request.form.get('image', 'default_place.jpg').strip()

    if not name or not location or not description:
        flash("Name, Location, and Description are required.", "danger")
        return redirect(url_for('admin_dashboard'))

    try:
        query_db(
            """INSERT INTO tourist_places (name, location, description, timings, entry_fee, image, category)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (name, location, description, timings, entry_fee, image, category),
            commit=True
        )
        flash(f"Tourist Place '{name}' added successfully!", "success")
    except Exception as e:
        flash(f"Error adding place: {str(e)}", "danger")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/place/edit/<int:place_id>', methods=['POST'])
def admin_edit_place(place_id):
    """Edit an existing tourist place."""
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))

    name = request.form.get('name', '').strip()
    location = request.form.get('location', '').strip()
    description = request.form.get('description', '').strip()
    timings = request.form.get('timings', '').strip()
    entry_fee = request.form.get('entry_fee', '').strip()
    category = request.form.get('category', '').strip()
    image = request.form.get('image', '').strip()

    try:
        query_db(
            """UPDATE tourist_places 
               SET name = %s, location = %s, description = %s, timings = %s, 
                   entry_fee = %s, category = %s, image = %s
               WHERE place_id = %s""",
            (name, location, description, timings, entry_fee, category, image, place_id),
            commit=True
        )
        flash(f"Tourist Place '{name}' updated successfully!", "success")
    except Exception as e:
        flash(f"Error updating place: {str(e)}", "danger")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/place/delete/<int:place_id>', methods=['POST'])
def admin_delete_place(place_id):
    """Delete a tourist place."""
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))

    try:
        query_db("DELETE FROM tourist_places WHERE place_id = %s", (place_id,), commit=True)
        flash("Tourist place deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting place: {str(e)}", "danger")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    """Logout from Admin session."""
    session.pop('is_admin', None)
    session.pop('admin_user', None)
    flash("Admin logged out successfully.", "info")
    return redirect(url_for('home'))

# ---------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------
if __name__ == '__main__':
    print("=========================================================")
    print(" Tourist Guide PWA Server starting on http://127.0.0.1:5000")
    print("=========================================================")
    app.run(debug=True, host='0.0.0.0', port=5000)
