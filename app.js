async function sendMessage() {
  let input = document.getElementById("user-input");
  let message = input.value.trim();
  if (!message) return;

  // Show user message
  let chatBox = document.getElementById("chat-box");
  let userMsg = document.createElement("div");
  userMsg.className = "message user";
  userMsg.innerText = message;
  chatBox.appendChild(userMsg);
  chatBox.scrollTop = chatBox.scrollHeight;

  input.value = "";

  // Call Flask API
  let response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: message })
  });

  let data = await response.json();

  // Show bot reply
  let botMsg = document.createElement("div");
  botMsg.className = "message bot";
  botMsg.innerText = data.reply;
  chatBox.appendChild(botMsg);
  chatBox.scrollTop = chatBox.scrollHeight;
}