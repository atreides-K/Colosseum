<template>
  <nav class="sidebar" :class="{ collapsed: sidebarCollapsed }">
    <button class="sidebar-collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed" :title="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'">
      {{ sidebarCollapsed ? '&#9654;' : '&#9664;' }}
    </button>
    <div class="sidebar-top">
      <div class="brand">
        <img src="/icons/logo-original.jpg" alt="Spectrum" class="brand-logo" />
        <span class="brand-full">SPECTRUM 2026</span>
        <span class="brand-short">S</span>
      </div>
      <router-link to="/"><span class="nav-icon">&#127941;</span> <span class="nav-label">Events</span></router-link>
      <router-link to="/home"><span class="nav-icon">&#127968;</span> <span class="nav-label">Home</span></router-link>
      <router-link to="/schedule"><span class="nav-icon">&#128197;</span> <span class="nav-label">Schedule</span></router-link>
    </div>
    <div class="sidebar-events">
      <template v-if="pinnedEvents.length">
        <div class="sidebar-divider"></div>
        <div class="sidebar-section-label">Pinned</div>
        <div v-for="evt in pinnedEvents" :key="'pin-' + evt.id" class="sidebar-event-row">
          <router-link :to="`/events/${evt.id}`" class="sidebar-event pinned" :title="evt.sport">
            <span class="nav-icon">{{ evt.icon }}</span> <span class="nav-label">{{ evt.sport }}</span>
          </router-link>
          <button class="sidebar-pin-btn active" @click="togglePinEvent(evt.id)" title="Unpin">&#128204;</button>
        </div>
      </template>
      <div class="sidebar-divider"></div>
      <div class="sidebar-section-label">{{ pinnedEvents.length ? 'All Events' : 'Events' }}</div>
      <div v-for="evt in unpinnedEvents" :key="evt.id" class="sidebar-event-row">
        <router-link :to="`/events/${evt.id}`" class="sidebar-event" :title="evt.sport">
          <span class="nav-icon">{{ evt.icon }}</span> <span class="nav-label">{{ evt.sport }}</span>
        </router-link>
        <button class="sidebar-pin-btn" @click="togglePinEvent(evt.id)" title="Pin">&#128204;</button>
      </div>
    </div>
  </nav>
  <div class="main">
    <router-view />
  </div>

  <!-- Mobile Side Nav — minimal right-side icon rail -->
  <nav class="mobile-rail" :class="{ hidden: scrollingDown }">
    <router-link to="/" exact-active-class="active" title="Events">&#127941;</router-link>
    <router-link to="/schedule" active-class="active" title="Schedule">&#128197;</router-link>
    <router-link to="/home" active-class="active" title="Home">&#127968;</router-link>
    <template v-if="pinnedEvents.length">
      <div class="mobile-rail-divider"></div>
      <router-link v-for="evt in pinnedEvents" :key="evt.id" :to="`/events/${evt.id}`" active-class="active" :title="evt.sport">{{ evt.icon }}</router-link>
    </template>
  </nav>

  <!-- PWA Install Banner -->
  <transition name="slide-up">
    <div v-if="showInstallBanner" class="pwa-install-banner" @click="doInstall">
      <img src="/icons/logo-original.jpg" alt="" class="pwa-install-icon" />
      <div class="pwa-install-text">
        <strong>Install Spectrum 2026</strong>
        <span>Add to home screen for quick access</span>
      </div>
      <button class="btn btn-primary btn-sm" @click.stop="doInstall">Install</button>
      <button class="pwa-install-close" @click.stop="dismissInstall">&times;</button>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { store, isEventPinned, togglePinEvent } from './stores/tournament.js'

const route = useRoute()

const sidebarCollapsed = ref(false)
const scrollingDown = ref(false)

// Hide rail on scroll down, show on scroll up (ignore first 500ms after mount/nav)
let lastScrollY = 0
let scrollEnabled = false
let scrollTimer = null
function enableScrollAfterDelay() {
  scrollEnabled = false
  clearTimeout(scrollTimer)
  scrollTimer = setTimeout(() => { scrollEnabled = true }, 500)
}
function onScroll() {
  if (!scrollEnabled) { lastScrollY = window.scrollY; return }
  const y = window.scrollY
  scrollingDown.value = y > lastScrollY && y > 50
  lastScrollY = y
}

// PWA Install prompt
const deferredPrompt = ref(null)
const showInstallBanner = ref(false)

function onBeforeInstallPrompt(e) {
  e.preventDefault()
  deferredPrompt.value = e
  // Show banner unless user dismissed in the last session (not permanently — show each visit)
  const dismissed = sessionStorage.getItem('pwa-install-dismissed')
  if (!dismissed) {
    showInstallBanner.value = true
  }
}

function doInstall() {
  if (!deferredPrompt.value) return
  deferredPrompt.value.prompt()
  deferredPrompt.value.userChoice.then(result => {
    deferredPrompt.value = null
    showInstallBanner.value = false
  })
}

function dismissInstall() {
  showInstallBanner.value = false
  sessionStorage.setItem('pwa-install-dismissed', '1')
}

onMounted(() => {
  window.addEventListener('beforeinstallprompt', onBeforeInstallPrompt)
  window.addEventListener('appinstalled', () => { showInstallBanner.value = false })
  window.addEventListener('scroll', onScroll, { passive: true })
  enableScrollAfterDelay()
})

watch(() => route.path, () => {
  scrollingDown.value = false
  enableScrollAfterDelay()
})
onUnmounted(() => {
  window.removeEventListener('beforeinstallprompt', onBeforeInstallPrompt)
  window.removeEventListener('scroll', onScroll)
})

const pinnedEvents = computed(() =>
  store.events.filter(e => isEventPinned(e.id))
)
const unpinnedEvents = computed(() =>
  store.events.filter(e => !isEventPinned(e.id))
)
</script>
