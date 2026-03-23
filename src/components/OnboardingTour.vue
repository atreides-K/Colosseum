<template>
  <div v-if="active" class="tour-overlay" @click.self="skip">
    <div class="tour-backdrop"></div>

    <!-- Highlight box -->
    <div v-if="targetRect" class="tour-highlight" :style="highlightStyle"></div>

    <!-- Bubble -->
    <div class="tour-bubble" :style="bubbleStyle" :class="bubblePosition">
      <div class="tour-bubble-arrow"></div>
      <div class="tour-step-count">{{ currentStep + 1 }} / {{ steps.length }}</div>
      <h3 class="tour-title">{{ steps[currentStep].title }}</h3>
      <p class="tour-text">{{ steps[currentStep].text }}</p>
      <div class="tour-actions">
        <button class="btn btn-sm" @click="skip">Skip Tour</button>
        <div class="flex gap-8">
          <button v-if="currentStep > 0" class="btn btn-sm" @click="prev">Back</button>
          <button v-if="currentStep < steps.length - 1" class="btn btn-sm btn-primary" @click="next">Next</button>
          <button v-else class="btn btn-sm btn-primary" @click="finish">Done!</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'

const props = defineProps({
  steps: { type: Array, required: true },
  show: { type: Boolean, default: false },
})

const emit = defineEmits(['complete', 'skip'])

const active = ref(false)
const currentStep = ref(0)
const targetRect = ref(null)
const bubblePosition = ref('bottom')

watch(() => props.show, (val) => {
  if (val) start()
})

onMounted(() => {
  if (props.show) start()
})

function start() {
  currentStep.value = 0
  active.value = true
  nextTick(() => updateTarget())
}

function next() {
  if (currentStep.value < props.steps.length - 1) {
    currentStep.value++
    nextTick(() => updateTarget())
  }
}

function prev() {
  if (currentStep.value > 0) {
    currentStep.value--
    nextTick(() => updateTarget())
  }
}

function skip() {
  active.value = false
  emit('skip')
}

function finish() {
  active.value = false
  emit('complete')
}

function updateTarget() {
  const step = props.steps[currentStep.value]
  if (!step?.target) {
    targetRect.value = null
    return
  }
  const el = document.querySelector(step.target)
  if (!el) {
    targetRect.value = null
    return
  }
  const rect = el.getBoundingClientRect()
  targetRect.value = rect

  // Determine bubble position
  const spaceBelow = window.innerHeight - rect.bottom
  const spaceAbove = rect.top
  const spaceRight = window.innerWidth - rect.right

  if (spaceBelow > 220) bubblePosition.value = 'bottom'
  else if (spaceAbove > 220) bubblePosition.value = 'top'
  else if (spaceRight > 350) bubblePosition.value = 'right'
  else bubblePosition.value = 'bottom'
}

const highlightStyle = computed(() => {
  if (!targetRect.value) return { display: 'none' }
  const r = targetRect.value
  const pad = 6
  return {
    top: (r.top - pad) + 'px',
    left: (r.left - pad) + 'px',
    width: (r.width + pad * 2) + 'px',
    height: (r.height + pad * 2) + 'px',
  }
})

const bubbleStyle = computed(() => {
  if (!targetRect.value) {
    return { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }
  }
  const r = targetRect.value
  const pos = bubblePosition.value

  if (pos === 'bottom') {
    return {
      top: (r.bottom + 16) + 'px',
      left: Math.max(16, Math.min(r.left + r.width / 2 - 160, window.innerWidth - 340)) + 'px',
    }
  }
  if (pos === 'top') {
    return {
      bottom: (window.innerHeight - r.top + 16) + 'px',
      left: Math.max(16, Math.min(r.left + r.width / 2 - 160, window.innerWidth - 340)) + 'px',
    }
  }
  if (pos === 'right') {
    return {
      top: Math.max(16, r.top + r.height / 2 - 80) + 'px',
      left: (r.right + 16) + 'px',
    }
  }
  return {}
})

let resizeHandler
onMounted(() => {
  resizeHandler = () => { if (active.value) updateTarget() }
  window.addEventListener('resize', resizeHandler)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeHandler)
})
</script>
