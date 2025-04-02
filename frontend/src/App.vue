<script setup lang="ts">
import { ref, nextTick } from 'vue';

const messages = ref<Array<{ id: number; text: string; sender: 'user' | 'ai' }>>([]);
const currentMessage = ref('');
const isLoading = ref(false);
const chatContainer = ref<HTMLElement | null>(null);
let messageIdCounter = 0;

const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    }
  });
};

const sendMessage = async () => {
  const text = currentMessage.value.trim();
  if (!text || isLoading.value) return; // Prevent sending empty or while loading

  // Add user message to chat
  messages.value.push({ id: messageIdCounter++, text, sender: 'user' });
  scrollToBottom();

  const userMessageToSend = currentMessage.value;
  currentMessage.value = ''; // Clear input
  isLoading.value = true;

  // Add placeholder for AI response
  const aiMessageIndex = messages.value.length;
  messages.value.push({ id: messageIdCounter++, text: '', sender: 'ai' });
  scrollToBottom();

  try {
    const eventSource = new EventSource(`http://localhost:5000/api/gemini?prompt=${encodeURIComponent(userMessageToSend)}`);

    eventSource.onmessage = (event) => {
      if (event.data === "[DONE]") {
        eventSource.close();
        isLoading.value = false;
        return;
      }
      
      // Append chunk to the AI message text
      messages.value[aiMessageIndex].text += event.data;
      scrollToBottom();
    };

    eventSource.onerror = (error) => {
      console.error('EventSource failed:', error);
      eventSource.close();
      isLoading.value = false;
      scrollToBottom();
    };
  } catch (error) {
    console.error('Failed to send message:', error);
    messages.value[aiMessageIndex].text = 'Failed to connect to the backend.';
    isLoading.value = false;
    scrollToBottom();
  }
};
</script>

<template>
  <div class="app-container">
    <header>
      <h1>Chat</h1>
    </header>
    <main class="chat-main">
      <div ref="chatContainer" class="chat-history">
        <div v-for="message in messages" :key="message.id" :class="['message', message.sender]">
          <p>{{ message.text }}</p>
        </div>
        <div v-if="isLoading" class="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
      <div class="chat-input-area">
        <input
          type="text"
          v-model="currentMessage"
          placeholder="Type your message..."
          :disabled="isLoading"
          @keyup.enter="sendMessage"
        />
        <button @click="sendMessage" :disabled="isLoading || !currentMessage.trim()">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </div>
    </main>
    <footer>
      <p>© {{ new Date().getFullYear() }} Simple Chat</p>
    </footer>
  </div>
</template>

<style>
:root {
  --primary-color: #4a76fd;
  --user-message-bg: #e3f2fd;
  --ai-message-bg: #f5f5f5;
  --border-radius: 18px;
  --box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  line-height: 1.6;
  color: #333;
  background-color: #f9f9f9;
  margin: 0;
  padding: 0;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.app-container {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: white;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
}

header {
  padding: 1rem;
  background-color: var(--primary-color);
  color: white;
  text-align: center;
  box-shadow: var(--box-shadow);
}

h1 {
  font-size: 1.5rem;
  font-weight: 500;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
}

.chat-history {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message {
  max-width: 60%;
  padding: 0.8rem 1rem;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  word-wrap: break-word;
}

.message.user {
  background-color: var(--user-message-bg);
  color: #333;
  align-self: flex-end;
  border-bottom-right-radius: 0;
}

.message.ai {
  background-color: var(--ai-message-bg);
  color: #333;
  align-self: flex-start;
  border-bottom-left-radius: 0;
}

@media (max-width: 768px) {
  .message {
    max-width: 80%;
  }
}

.message p {
  margin: 0;
}

.typing-indicator {
  align-self: flex-start;
  padding: 12px 16px;
  display: flex;
  align-items: center;
}

.typing-indicator span {
  height: 8px;
  width: 8px;
  margin: 0 2px;
  background-color: #bbb;
  border-radius: 50%;
  display: inline-block;
  animation: bounce 1.5s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.4s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.2s;
}

@keyframes bounce {
  0%, 80%, 100% { 
    transform: scale(0);
  } 
  40% { 
    transform: scale(1.0);
  }
}

.chat-input-area {
  display: flex;
  padding: 1rem;
  border-top: 1px solid #eee;
  background-color: white;
}

.chat-input-area input {
  flex: 1;
  padding: 0.8rem 1rem;
  border: 1px solid #ddd;
  border-radius: 24px;
  font-size: 1rem;
  outline: none;
  transition: border 0.3s;
}

.chat-input-area input:focus {
  border-color: var(--primary-color);
}

.chat-input-area button {
  margin-left: 0.5rem;
  width: 48px;
  height: 48px;
  border: none;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.3s, transform 0.2s;
}

.chat-input-area button:hover:not(:disabled) {
  background-color: #3a65e8;
  transform: scale(1.05);
}

.chat-input-area button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.chat-input-area button svg {
  width: 20px;
  height: 20px;
}

footer {
  padding: 0.8rem;
  text-align: center;
  color: #888;
  font-size: 0.8rem;
  border-top: 1px solid #eee;
}
</style>
