<template>
  <div class="chat-container">
    <div class="input-container">
      <input 
        v-model="prompt" 
        type="text" 
        placeholder="Ask me anything..."
        @keyup.enter="sendPrompt"
      >
      <button @click="sendPrompt" :disabled="isLoading">
        {{ isLoading ? 'Sending...' : 'Send' }}
      </button>
    </div>
    
    <div v-if="response" class="response-container">
      <h3>Response:</h3>
      <p class="response-text">{{ response }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const prompt = ref('')
const response = ref('')
const isLoading = ref(false)

async function sendPrompt() {
  if (!prompt.value.trim()) return
  
  isLoading.value = true
  try {
    const res = await fetch('http://localhost:3000/api/ollama', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt: prompt.value
      })
    })
    
    const data = await res.json()
    response.value = data
    prompt.value = '' // Clear input after successful response
  } catch (error) {
    console.error('Error:', error)
    response.value = 'Error occurred while fetching response'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.chat-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.input-container {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

button {
  padding: 10px 20px;
  background-color: #42b883;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

button:disabled {
  background-color: #88d4b2;
  cursor: not-allowed;
}

.response-text {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 16px;
  color: #333;
}

.response-container {
  padding: 20px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

h3 {
  margin-top: 0;
  color: #42b883;
}
</style>
