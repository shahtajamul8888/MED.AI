const API_BASE = "https://your-flask-domain.com"; // Replace with your backend URL

let isLoading = false;

// Hide intro overlay after 5 seconds and show main UI
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('year').textContent = new Date().getFullYear();
  setupEventListeners();
  setupAccessibility();

  setTimeout(() => {
    const intro = document.getElementById('intro-screen');
    if (intro) intro.style.display = 'none';
  }, 5000);
});

function setupEventListeners() {
  const askBtn = document.getElementById('askBtn');
  const queryInput = document.getElementById('queryInput');
  const suggestions = document.querySelectorAll('.suggestion');
  const navButtons = document.querySelectorAll('.nav-btn');

  askBtn.addEventListener('click', handleSearch);
  queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !isLoading) handleSearch();
  });
  suggestions.forEach(suggestion => {
    suggestion.addEventListener('click', () => {
      queryInput.value = suggestion.dataset.query;
      handleSearch();
    });
  });
  navButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      navButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });
}

function setupAccessibility() {
  const queryInput = document.getElementById('queryInput');
  queryInput.setAttribute('aria-describedby', 'search-help');
  const loading = document.getElementById('loading');
  const srOnly = document.createElement('span');
  srOnly.className = 'sr-only';
  srOnly.textContent = 'Searching for medical information...';
  loading.appendChild(srOnly);
}

// Handle AI search and image as before...
// All code for async search, loading state, debounce etc. from previous version
