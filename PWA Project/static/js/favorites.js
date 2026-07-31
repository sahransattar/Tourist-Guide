/* =========================================================
   Tourist Guide PWA - Favorites Manager (favorites.js)
   Handles bookmarking tourist places via AJAX
   ========================================================= */

function showToast(message, type = 'info') {
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.className = 'toast-container';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('show');
  }, 50);

  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

async function toggleFavorite(placeId, buttonElement) {
  try {
    const response = await fetch('/api/favorites/toggle', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ place_id: placeId })
    });

    const data = await response.json();

    if (response.status === 401) {
      showToast('Please log in to add places to your favorites!', 'warning');
      setTimeout(() => {
        window.location.href = '/login';
      }, 1500);
      return;
    }

    if (data.success) {
      const heartIcon = buttonElement.querySelector('i') || buttonElement;
      
      if (data.is_favorite) {
        buttonElement.classList.add('active');
        if (heartIcon.classList.contains('far')) {
          heartIcon.classList.remove('far');
          heartIcon.classList.add('fas');
        }
        showToast('❤️ Saved to your Favorites!', 'success');
      } else {
        buttonElement.classList.remove('active');
        if (heartIcon.classList.contains('fas')) {
          heartIcon.classList.remove('fas');
          heartIcon.classList.add('far');
        }
        showToast('💔 Removed from Favorites.', 'info');

        // If we are currently on the favorites page, remove the card dynamically
        const favoriteCard = buttonElement.closest('.place-card');
        if (favoriteCard && window.location.pathname === '/favorites') {
          favoriteCard.style.transform = 'scale(0.8)';
          favoriteCard.style.opacity = '0';
          setTimeout(() => {
            favoriteCard.remove();
            const remainingCards = document.querySelectorAll('.place-card');
            if (remainingCards.length === 0) {
              location.reload();
            }
          }, 300);
        }
      }
    } else {
      showToast(data.message || 'Error processing favorite request.', 'danger');
    }
  } catch (error) {
    console.error('Favorite toggle error:', error);
    showToast('Offline or connection error. Action will sync when online.', 'warning');
  }
}
