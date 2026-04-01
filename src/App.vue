<template>
  <nav class="sidebar" :class="{ collapsed: sidebarCollapsed }">
    <button class="sidebar-collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed" :title="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'">
      {{ sidebarCollapsed ? '&#9654;' : '&#9664;' }}
    </button>
    <div class="sidebar-top">
      <div class="brand">
        <span class="brand-full">SPECTRUM 2026</span>
        <span class="brand-short">S</span>
      </div>
      <router-link to="/"><span class="nav-icon">&#127941;</span> <span class="nav-label">Events</span></router-link>
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
</template>

<script setup>
import { ref, computed } from 'vue'
import { store, isEventPinned, togglePinEvent } from './stores/tournament.js'

const sidebarCollapsed = ref(false)

const pinnedEvents = computed(() =>
  store.events.filter(e => isEventPinned(e.id))
)
const unpinnedEvents = computed(() =>
  store.events.filter(e => !isEventPinned(e.id))
)
</script>
