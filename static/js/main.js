/* =========================================================
   Tourist Guide PWA - Global Main JavaScript (main.js)
   UI Interactions, Navigation Toggle, Modals, Geolocation,
   Admin Quick Search & Web Share API
   ========================================================= */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Navigation Toggle
  const navToggle = document.getElementById('nav-toggle');
  const navMenu = document.getElementById('nav-menu');

  if (navToggle && navMenu) {
    navToggle.addEventListener('click', () => {
      navMenu.classList.toggle('active');
      navToggle.classList.toggle('active');
    });
  }

  // 2. Auto-dismiss Flash Alert Messages after 5 seconds
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach((alert) => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      setTimeout(() => alert.remove(), 400);
    }, 4500);
  });

  // 3. Admin Modal Dialog Handlers
  window.openModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
  };

  window.closeModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('active');
      document.body.style.overflow = 'auto';
    }
  };

  // Close modal when clicking outside content area
  document.querySelectorAll('.modal-overlay').forEach((overlay) => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        overlay.classList.remove('active');
        document.body.style.overflow = 'auto';
      }
    });
  });

  // 4. Edit Place Modal Population (Admin)
  window.populateEditModal = function (placeData) {
    document.getElementById('edit-place-id').value = placeData.place_id || '';
    document.getElementById('edit-name').value = placeData.name || '';
    document.getElementById('edit-location').value = placeData.location || '';
    document.getElementById('edit-category').value = placeData.category || 'Heritage';
    document.getElementById('edit-timings').value = placeData.timings || '';
    document.getElementById('edit-entry-fee').value = placeData.entry_fee || '';
    document.getElementById('edit-image').value = placeData.image || 'default_place.jpg';
    document.getElementById('edit-description').value = placeData.description || '';
    
    const latField = document.getElementById('edit-latitude');
    if (latField) latField.value = (placeData.latitude !== null && placeData.latitude !== undefined) ? placeData.latitude : '';
    
    const lngField = document.getElementById('edit-longitude');
    if (lngField) lngField.value = (placeData.longitude !== null && placeData.longitude !== undefined) ? placeData.longitude : '';

    const form = document.getElementById('edit-place-form');
    if (form) {
      form.action = `/admin/place/edit/${placeData.place_id}`;
    }

    openModal('modal-edit-place');
  };

  // 5. Admin Table Quick Filter Search
  window.filterPlacesTable = function () {
    const input = document.getElementById('admin-place-filter');
    if (!input) return;
    const filter = input.value.toLowerCase();
    const table = document.getElementById('places-table');
    if (!table) return;
    const rows = table.getElementsByTagName('tr');

    for (let i = 1; i < rows.length; i++) {
      const row = rows[i];
      const text = row.textContent || row.innerText;
      if (text.toLowerCase().indexOf(filter) > -1) {
        row.style.display = '';
      } else {
        row.style.display = 'none';
      }
    }
  };

  // 6. Voluntary Geolocation Nearby Destinations Discovery
  window.locateNearbyPlaces = function () {
    if (!navigator.geolocation) {
      if (typeof showToast === 'function') {
        showToast('Geolocation is not supported by your browser.', 'warning');
      } else {
        alert('Geolocation is not supported by your browser.');
      }
      return;
    }

    if (typeof showToast === 'function') {
      showToast('Detecting your GPS location...', 'info');
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;

        try {
          const res = await fetch(`/api/nearby?lat=${lat}&lng=${lng}&limit=6`);
          const data = await res.json();

          if (data.success && data.places && data.places.length > 0) {
            const container = document.getElementById('nearby-container');
            const grid = document.getElementById('nearby-grid');
            if (!container || !grid) return;

            const resolveImg = (img) => {
              if (!img) return '/static/images/default_place.jpg';
              if (img.startsWith('http://') || img.startsWith('https://')) return img;
              return '/static/images/' + img;
            };

            grid.innerHTML = data.places.map((place) => `
              <div class="place-card">
                <div class="card-img-wrapper">
                  <img src="${resolveImg(place.image)}" alt="${place.name}" class="card-img" onerror="this.onerror=null; this.src='/static/images/default_place.jpg';">
                  <span class="category-pill">${place.category || 'Heritage'}</span>
                  <span class="distance-badge"><i class="fas fa-location-arrow"></i> ${place.distance_km} km away</span>
                </div>
                <div class="card-body">
                  <h3 class="place-title">${place.name}</h3>
                  <div class="place-location"><i class="fas fa-location-dot"></i> ${place.location}</div>
                  <p class="place-desc">${place.description}</p>
                  <div class="card-info-row">
                    <span class="info-item"><i class="far fa-clock" style="color: var(--primary);"></i> ${place.timings}</span>
                    <span class="info-item" style="margin-left: auto;"><i class="fas fa-ticket" style="color: var(--accent);"></i> ${place.entry_fee}</span>
                  </div>
                  <div style="display: flex; gap: 0.5rem; margin-top: 0.75rem;">
                    <a href="/place/${place.place_id}" class="btn btn-outline" style="flex: 1;">
                      Details <i class="fas fa-chevron-right"></i>
                    </a>
                    <button type="button" onclick="openAddToTripModal(${place.place_id}, '${place.name.replace(/'/g, "\\'")}')" class="btn btn-outline btn-sm" title="Add to Trip Itinerary" style="color: var(--primary); border-color: rgba(6, 182, 212, 0.4);">
                      <i class="fas fa-route"></i> + Trip
                    </button>
                  </div>
                </div>
              </div>
            `).join('');

            container.style.display = 'block';
            container.scrollIntoView({ behavior: 'smooth', block: 'start' });

            if (typeof showToast === 'function') {
              showToast(`Found ${data.places.length} destinations near your location!`, 'success');
            }
          } else {
            if (typeof showToast === 'function') {
              showToast('No nearby destinations found for your coordinates.', 'info');
            }
          }
        } catch (err) {
          console.error('Error fetching nearby places:', err);
          if (typeof showToast === 'function') {
            showToast('Failed to retrieve nearby destinations.', 'danger');
          }
        }
      },
      (error) => {
        let msg = 'Unable to retrieve your location.';
        if (error.code === error.PERMISSION_DENIED) {
          msg = 'Location permission was denied. You can still search manually above.';
        }
        if (typeof showToast === 'function') {
          showToast(msg, 'warning');
        } else {
          alert(msg);
        }
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  // 7. Web Share API & Clipboard Copy
  window.shareDestination = async function (name, location) {
    const shareData = {
      title: `${name} - Tourist Guide PWA`,
      text: `Check out ${name} in ${location} on Explore India!`,
      url: window.location.href
    };

    if (navigator.share) {
      try {
        await navigator.share(shareData);
        return;
      } catch (err) {
        // User cancelled or share error; fallback to clipboard
      }
    }

    try {
      await navigator.clipboard.writeText(window.location.href);
      if (typeof showToast === 'function') {
        showToast('Link copied to clipboard!', 'success');
      } else {
        alert('Link copied to clipboard!');
      }
    } catch (err) {
      if (typeof showToast === 'function') {
        showToast('Please copy the URL from your address bar.', 'info');
      }
    }
  };

  // 8. Add Destination to Trip Itinerary Modal
  window.openAddToTripModal = async function (placeId, placeName) {
    const modal = document.getElementById('modal-add-to-trip');
    if (!modal) return;

    document.getElementById('trip-modal-place-id').value = placeId;
    document.getElementById('trip-modal-place-name').textContent = placeName;

    const select = document.getElementById('trip-select-itinerary');
    select.innerHTML = '<option value="">Loading your trips...</option>';

    try {
      const res = await fetch('/api/user/itineraries');
      if (res.status === 401) {
        if (typeof showToast === 'function') {
          showToast('Please log in to add places to your trip itinerary.', 'warning');
        }
        setTimeout(() => window.location.href = '/login', 1500);
        return;
      }
      const data = await res.json();
      if (data.success && data.itineraries && data.itineraries.length > 0) {
        select.innerHTML = '<option value="">-- Choose an Itinerary --</option>' +
          data.itineraries.map(t => `<option value="${t.itinerary_id}">${t.title}</option>`).join('');
      } else {
        select.innerHTML = '<option value="">No trips found. Click below to create one!</option>';
      }
    } catch (err) {
      select.innerHTML = '<option value="">Error loading trips</option>';
    }

    openModal('modal-add-to-trip');
  };

  window.submitAddToTrip = async function (e) {
    e.preventDefault();
    const placeId = document.getElementById('trip-modal-place-id').value;
    const itineraryId = document.getElementById('trip-select-itinerary').value;
    const dayNumber = document.getElementById('trip-modal-day').value;
    const notes = document.getElementById('trip-modal-notes').value;

    if (!itineraryId) {
      if (typeof showToast === 'function') {
        showToast('Please select a trip itinerary first, or create a new one.', 'warning');
      }
      return;
    }

    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';

    try {
      const res = await fetch('/api/itinerary/add_place', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
          place_id: placeId,
          itinerary_id: itineraryId,
          day_number: dayNumber,
          notes: notes,
          csrf_token: csrfToken
        })
      });
      const data = await res.json();
      if (data.success) {
        if (typeof showToast === 'function') {
          showToast(data.message || 'Added to your trip itinerary!', 'success');
        }
        closeModal('modal-add-to-trip');
      } else {
        if (typeof showToast === 'function') {
          showToast(data.message || 'Could not add stop.', 'danger');
        }
      }
    } catch (err) {
      if (typeof showToast === 'function') {
        showToast('Error connecting to trip planner.', 'danger');
      }
    }
  };
});
