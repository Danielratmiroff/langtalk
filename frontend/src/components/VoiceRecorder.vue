<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const isRecording = ref(false)
const mediaRecorder = ref<MediaRecorder | null>(null)
const audioChunks = ref<Blob[]>([])
const recordingTime = ref(0)
const timerInterval = ref<number | null>(null)
const recordings = ref<{ id: string; url: string; timestamp: Date }[]>([])

const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder.value = new MediaRecorder(stream)
    audioChunks.value = []

    mediaRecorder.value.ondataavailable = (event) => {
      audioChunks.value.push(event.data)
    }

    mediaRecorder.value.onstop = () => {
      const audioBlob = new Blob(audioChunks.value, { type: 'audio/wav' })
      const audioUrl = URL.createObjectURL(audioBlob)
      recordings.value.push({
        id: Date.now().toString(),
        url: audioUrl,
        timestamp: new Date(),
      })
      audioChunks.value = []
      stopTimer()
    }

    mediaRecorder.value.start()
    isRecording.value = true
    startTimer()
  } catch (error) {
    console.error('Error accessing microphone:', error)
    alert('Could not access microphone. Please ensure you have granted microphone permissions.')
  }
}

const stopRecording = () => {
  if (mediaRecorder.value && isRecording.value) {
    mediaRecorder.value.stop()
    mediaRecorder.value.stream.getTracks().forEach((track) => track.stop())
    isRecording.value = false
  }
}

const startTimer = () => {
  recordingTime.value = 0
  timerInterval.value = window.setInterval(() => {
    recordingTime.value++
  }, 1000)
}

const stopTimer = () => {
  if (timerInterval.value) {
    clearInterval(timerInterval.value)
    timerInterval.value = null
  }
}

const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const deleteRecording = (id: string) => {
  const recording = recordings.value.find((r) => r.id === id)
  if (recording) {
    URL.revokeObjectURL(recording.url)
    recordings.value = recordings.value.filter((r) => r.id !== id)
  }
}

onUnmounted(() => {
  stopTimer()
  if (mediaRecorder.value) {
    mediaRecorder.value.stream.getTracks().forEach((track) => track.stop())
  }
  recordings.value.forEach((recording) => URL.revokeObjectURL(recording.url))
})
</script>

<template>
  <div class="voice-recorder">
    <div class="recording-controls">
      <button
        class="record-button"
        :class="{ recording: isRecording }"
        @click="isRecording ? stopRecording() : startRecording()"
        :aria-label="isRecording ? 'Stop recording' : 'Start recording'"
      >
        <span class="button-icon">{{ isRecording ? '⏹' : '🎤' }}</span>
      </button>
      <div v-if="isRecording" class="recording-time">
        {{ formatTime(recordingTime) }}
      </div>
    </div>

    <div class="recordings-list">
      <h2>Your Recordings</h2>
      <div v-if="recordings.length === 0" class="no-recordings">
        No recordings yet. Click the microphone button to start recording.
      </div>
      <div v-else class="recordings-grid">
        <div v-for="recording in recordings" :key="recording.id" class="recording-card">
          <audio :src="recording.url" controls class="audio-player"></audio>
          <div class="recording-info">
            <span class="timestamp">{{ recording.timestamp.toLocaleString() }}</span>
            <button
              class="delete-button"
              @click="deleteRecording(recording.id)"
              aria-label="Delete recording"
            >
              🗑️
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.voice-recorder {
  background: var(--card-background);
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.recording-controls {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.record-button {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: none;
  background: var(--primary-color);
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(98, 0, 238, 0.3);
}

.record-button:hover {
  transform: scale(1.05);
  background: var(--primary-light);
}

.record-button.recording {
  background: var(--danger-color);
  animation: pulse 1.5s infinite;
}

.button-icon {
  font-size: 2rem;
}

.recording-time {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--danger-color);
}

.recordings-list {
  margin-top: 2rem;
}

.recordings-list h2 {
  margin-bottom: 1rem;
  color: var(--text-color);
  font-size: 1.5rem;
}

.no-recordings {
  text-align: center;
  color: #6c757d;
  padding: 2rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.recordings-grid {
  display: grid;
  gap: 1rem;
}

.recording-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
}

.audio-player {
  width: 100%;
  margin-bottom: 0.5rem;
}

.recording-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  color: #6c757d;
}

.delete-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.delete-button:hover {
  background-color: rgba(220, 53, 69, 0.1);
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}
</style>
