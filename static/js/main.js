/* =========================================================
   Tourist Guide PWA - Global Main JavaScript (main.js)
   UI Interactions, Navigation Toggle, Modals, Search
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
    document.getElementById('edit-place-id').value = placeData.place_id;
    document.getElementById('edit-name').value = placeData.name;
    document.getElementById('edit-location').value = placeData.location;
    document.getElementById('edit-category').value = placeData.category || 'Heritage';
    document.getElementById('edit-timings').value = placeData.timings || '';
    document.getElementById('edit-entry-fee').value = placeData.entry_fee || '';
    document.getElementById('edit-image').value = placeData.image || 'default_place.jpg';
    document.getElementById('edit-description').value = placeData.description || '';

    const form = document.getElementById('edit-place-form');
    if (form) {
      form.action = `/admin/place/edit/${placeData.place_id}`;
    }

    openModal('modal-edit-place');
  };
});
