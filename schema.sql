-- =========================================================
-- Tourist Guide PWA - MySQL Database Script
-- Database: tourist_guide_db
-- Suitable for BCA Final Year Project & Cloud Deployment
-- =========================================================

-- Create Database if not exists
CREATE DATABASE IF NOT EXISTS tourist_guide_db;
USE tourist_guide_db;

-- ---------------------------------------------------------
-- Table: Users
-- Stores registered user information with secure password hashes
-- ---------------------------------------------------------
DROP TABLE IF EXISTS favorites;
DROP TABLE IF EXISTS tourist_places;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------
-- Table: Tourist_Places
-- Stores details about tourist locations
-- ---------------------------------------------------------
CREATE TABLE tourist_places (
    place_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    location VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    timings VARCHAR(100) DEFAULT '9:00 AM - 5:00 PM',
    entry_fee VARCHAR(100) DEFAULT 'Free / Nominal',
    image VARCHAR(255) DEFAULT 'default_place.jpg',
    category VARCHAR(50) DEFAULT 'Heritage',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------
-- Table: Favorites
-- Stores user bookmarked/favorite tourist places
-- ---------------------------------------------------------
CREATE TABLE favorites (
    favorite_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    place_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (place_id) REFERENCES tourist_places(place_id) ON DELETE CASCADE,
    UNIQUE KEY user_place_unique (user_id, place_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------
-- Insert Default Sample Users
-- Passwords are stored as secure Werkzeug scrypt hashes.
-- Plaintext password for both accounts is: user123
-- ---------------------------------------------------------
INSERT INTO users (name, email, password) VALUES 
('John Doe', 'john@example.com', 'scrypt:32768:8:1$l2VIkZ8UydQWMIKI$09d4944fbbdb0bb9076073865923951157f3c65af86218e524c2fa1092c36b9e2bd1f8445030c327a558d1334a5ca290d222aa7b8e5daca0c0783f152d5ba660'),
('Alice Smith', 'alice@example.com', 'scrypt:32768:8:1$l2VIkZ8UydQWMIKI$09d4944fbbdb0bb9076073865923951157f3c65af86218e524c2fa1092c36b9e2bd1f8445030c327a558d1334a5ca290d222aa7b8e5daca0c0783f152d5ba660');

-- ---------------------------------------------------------
-- Insert Rich Sample Tourist Places Data
-- ---------------------------------------------------------
INSERT INTO tourist_places (name, location, description, timings, entry_fee, image, category) VALUES
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
);
