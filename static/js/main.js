/* ===================================================================
   MR EARN & CONNECT - CLIENT INTERACTION SCRIPT
   Malla Reddy Deemed to be University (MRDU), Tirupati
   =================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Navigation Toggle
  const mobileToggle = document.getElementById('navMobileToggle');
  const navMenu = document.getElementById('navMenu');

  if (mobileToggle && navMenu) {
    mobileToggle.addEventListener('click', () => {
      navMenu.classList.toggle('open');
      const isOpen = navMenu.classList.contains('open');
      mobileToggle.innerHTML = isOpen ? '✕' : '☰';
    });
  }

  // 2. Auto-dismiss Flash Alerts after 5 seconds
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      setTimeout(() => alert.remove(), 500);
    }, 5000);

    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        alert.remove();
      });
    }
  });

  // 3. Interactive Star Rating Picker
  const starContainers = document.querySelectorAll('.star-rating-input');
  starContainers.forEach(container => {
    const stars = container.querySelectorAll('.star');
    const input = container.querySelector('input[type="hidden"]');

    stars.forEach((star, index) => {
      star.addEventListener('click', () => {
        const ratingVal = index + 1;
        if (input) input.value = ratingVal;
        updateStars(stars, ratingVal);
      });

      star.addEventListener('mouseover', () => {
        updateStars(stars, index + 1);
      });

      star.addEventListener('mouseout', () => {
        const currentVal = input ? parseInt(input.value) || 5 : 5;
        updateStars(stars, currentVal);
      });
    });
  });

  function updateStars(stars, count) {
    stars.forEach((s, idx) => {
      if (idx < count) {
        s.style.color = '#fbbf24';
        s.innerHTML = '★';
      } else {
        s.style.color = '#4b5563';
        s.innerHTML = '☆';
      }
    });
  }

  // 4. Modal Triggers
  const modalTriggers = document.querySelectorAll('[data-modal-target]');
  modalTriggers.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = btn.getAttribute('data-modal-target');
      const targetModal = document.getElementById(targetId);
      if (targetModal) {
        targetModal.style.display = 'flex';
      }
    });
  });

  const modalCloses = document.querySelectorAll('[data-modal-close]');
  modalCloses.forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = btn.closest('.modal-backdrop');
      if (modal) modal.style.display = 'none';
    });
  });

  window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-backdrop')) {
      e.target.style.display = 'none';
    }
  });

  // 5. Quick Filter for Tables and Lists
  const liveFilterInputs = document.querySelectorAll('[data-live-filter]');
  liveFilterInputs.forEach(input => {
    const targetSelector = input.getAttribute('data-live-filter');
    const targets = document.querySelectorAll(targetSelector);

    input.addEventListener('input', () => {
      const term = input.value.toLowerCase().trim();
      targets.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(term) ? '' : 'none';
      });
    });
  });
});
