// Chat sending logic
async function sendMessage() {
  const input = document.getElementById("user-input");
  let message = input.value.trim();
  if (!message) return;

  showMessage(message, "user");
  input.value = "";
  showTyping(true);
  try {
    let response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });
    let data = await response.json();
    showMessage(data.reply, "bot");
  } catch (err) {
    showMessage("Error connecting to server. Please try again.", "bot");
  }
  showTyping(false);
}

// Show message in chat box
function showMessage(text, sender) {
  const chatBox = document.getElementById("chat-box");
  const msgDiv = document.createElement("div");
  msgDiv.className = "message " + sender;
  msgDiv.innerText = text;
  chatBox.appendChild(msgDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Typing animation
function showTyping(show) {
  document.getElementById("typing-indicator").classList.toggle("hidden", !show);
}

// Quick question shortcut
function quickAsk(text) {
  document.getElementById("user-input").value = text;
  sendMessage();
}

// Generate medical image and explanation
async function generateImage() {
  showTyping(true);
  let input = document.getElementById("user-input").value.trim();
  try {
    let response = await fetch("/api/generate_image", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: input || "medical diagram" })
    });
    let data = await response.json();
    showMessage("Diagram Explanation: " + (data.explanation || "See diagram below."), "bot");
    if (data.imageUrl) {
      let chatBox = document.getElementById("chat-box");
      let img = document.createElement("img");
      img.src = data.imageUrl;
      img.alt = "AI-generated diagram";
      img.style.maxWidth = "95%";
      img.style.display = "block";
      img.style.margin = "10px auto";
      chatBox.appendChild(img);
    }
  } catch (err) {
    showMessage("Could not generate image. Try again.", "bot");
  }
  showTyping(false);
}

// Dummy Contact Form Submission
function handleContact(event) {
  event.preventDefault();
  document.getElementById("contact-status").innerText = "Message sent! We'll get back soon.";
  event.target.reset();
}

