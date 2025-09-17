const API_BASE = "https://your-backend-url.com"; // Change to your Flask backend URL

async function loadArticles() {
  const query = document.getElementById("searchInput").value.trim();
  let url = `${API_BASE}/api/articles`;
  if (query) {
    url += `?tag=${encodeURIComponent(query)}`;
  }

  const res = await fetch(url);
  const data = await res.json();
  const container = document.getElementById("articles");
  container.innerHTML = "";

  if (data.count === 0) {
    container.innerHTML = "<p>No articles found.</p>";
    return;
  }

  data.items.forEach(a => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <h2>${a.title}</h2>
      <div class="meta">${new Date(a.created_at).toDateString()} · Tags: ${a.tags.join(", ")}</div>
      <p>${a.summary || ""}</p>
      <a href="${API_BASE}/articles/${a.slug}" target="_blank">Read More →</a>
    `;
    container.appendChild(card);
  });
}

// Initial load
window.onload = () => {
  loadArticles();
  document.getElementById("year").textContent = new Date().getFullYear();
};
