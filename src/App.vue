<template>
  <nav class="sidebar">
    <div class="brand">{{ store.tournamentName || 'Spectrum' }}</div>
    <router-link to="/"><span class="nav-icon">&#9776;</span> Dashboard</router-link>
    <router-link to="/events"><span class="nav-icon">&#127941;</span> Events</router-link>
    <router-link to="/schedule"><span class="nav-icon">&#128197;</span> Schedule</router-link>
    <router-link to="/bulletin"><span class="nav-icon">&#128227;</span> Bulletin</router-link>
    <router-link v-if="store.isAdmin" to="/settings"><span class="nav-icon">&#9881;</span> Settings</router-link>
    <div class="sidebar-spacer"></div>
    <button v-if="store.isAdmin" class="tour-trigger" @click="showTour = true" title="Show app tour">?</button>
    <button class="admin-toggle" :class="{ active: store.isAdmin }" @click="store.isAdmin = !store.isAdmin">
      <span class="nav-icon">{{ store.isAdmin ? '&#128275;' : '&#128274;' }}</span>
      {{ store.isAdmin ? 'Admin' : 'Viewer' }}
    </button>
  </nav>
  <div class="main">
    <router-view />
  </div>

  <!-- Onboarding Tour -->
  <OnboardingTour
    :steps="tourSteps"
    :show="showTour"
    @complete="onTourComplete"
    @skip="onTourComplete"
  />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { store } from './stores/tournament.js'
import OnboardingTour from './components/OnboardingTour.vue'

const showTour = ref(false)

const tourSteps = [
  {
    target: '.admin-toggle',
    title: 'Admin / Viewer Mode',
    text: 'Switch between Admin (full edit access) and Viewer (read-only for participants). Viewers see a simplified interface with big tiles and can pin their events.',
  },
  {
    target: '.sidebar a[href="#/events"]',
    title: 'Events Hub',
    text: 'All 19 sports live here. As admin, you can manage teams, participants, volunteers, schedules, logistics, and notes for each event.',
  },
  {
    target: '.sidebar a[href="#/schedule"]',
    title: 'Master Schedule',
    text: 'See every scheduled match, round, and final across all sports on one page, grouped by date.',
  },
  {
    target: '.sidebar a[href="#/bulletin"]',
    title: 'Bulletin Board',
    text: 'Post general announcements, view completed events and winners, and see upcoming fixtures. You can pin important announcements.',
  },
  {
    target: '.sidebar a[href="#/settings"]',
    title: 'Settings',
    text: 'Change the tournament name, export all data as JSON (for backup/sharing), import data, or reset everything.',
  },
  {
    target: '.tour-trigger',
    title: 'Replay Tour',
    text: 'Click the "?" button anytime to see this tour again. Share the app in Viewer mode for participants!',
  },
]

onMounted(() => {
  if (store.isAdmin && !store.tourSeen) {
    setTimeout(() => { showTour.value = true }, 600)
  }
})

function onTourComplete() {
  showTour.value = false
  store.tourSeen = true
}
</script>
