const API_BASE = "https://your-flask-domain.com"; // Set your backend, or keep blank for static demo

let isLoading = false;

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('year').textContent = new Date().getFullYear();
  setupEventListeners();

  setTimeout(() => {
    const intro = document.getElementById('intro-screen');
    if (intro) {
      intro.classList.add('fade-out');
      setTimeout(() => { intro.style.display = 'none'; }, 1200);
    }
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

function handleSearch() {
  // Yahan apna fetch/AI logic daalna hai -- jaise pehle diya tha.
  // Agar local ya static chahiye, to placeholder text laa sakte ho.
}
