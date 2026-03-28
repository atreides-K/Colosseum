<template>
  <h1>Events</h1>

  <!-- Filter tabs -->
  <div class="tabs">
    <button class="tab" :class="{ active: filter === 'all' }" @click="filter = 'all'">All ({{ store.events.length }})</button>
    <button class="tab" :class="{ active: filter === 'ongoing' }" @click="filter = 'ongoing'">Ongoing</button>
    <button class="tab" :class="{ active: filter === 'upcoming' }" @click="filter = 'upcoming'">Upcoming</button>
    <button class="tab" :class="{ active: filter === 'completed' }" @click="filter = 'completed'">Completed</button>
    <button class="tab" :class="{ active: filter === 'team' }" @click="filter = 'team'">Team Sports</button>
    <button class="tab" :class="{ active: filter === 'individual' }" @click="filter = 'individual'">Individual</button>
  </div>

  <!-- Viewer: big tiles -->
  <template v-if="!store.isAdmin">
    <!-- Pinned events first -->
    <div v-if="pinnedFiltered.length" class="mb-24">
      <h2>Your Events</h2>
      <div class="big-tiles-grid">
        <router-link v-for="evt in pinnedFiltered" :key="evt.id" :to="`/events/${evt.id}`" class="big-tile pinned">
          <button class="pin-btn pinned" @click.prevent="togglePinEvent(evt.id)" title="Unpin event">&#128204;</button>
          <div class="big-tile-icon">{{ evt.icon }}</div>
          <div class="big-tile-name">{{ evt.sport }}</div>
          <span class="badge" :class="statusBadge(evt.status)">{{ evt.status }}</span>
          <div class="big-tile-info">
            <span>{{ evt.type === 'team' ? 'Team' : evt.type === 'both' ? 'Individual + Team' : 'Individual' }}</span>
            <span v-if="evt.venue && evt.venue !== 'TBA'"> &bull; {{ evt.venue }}</span>
          </div>
          <div v-if="evt.categories" class="big-tile-note">{{ evt.categories }}</div>
        </router-link>
      </div>
    </div>

    <h2 v-if="pinnedFiltered.length">All Events</h2>
    <div class="big-tiles-grid">
      <router-link v-for="evt in unpinnedFiltered" :key="evt.id" :to="`/events/${evt.id}`" class="big-tile">
        <button class="pin-btn" @click.prevent="togglePinEvent(evt.id)" title="Pin this event">&#128204;</button>
        <div class="big-tile-icon">{{ evt.icon }}</div>
        <div class="big-tile-name">{{ evt.sport }}</div>
        <span class="badge" :class="statusBadge(evt.status)">{{ evt.status }}</span>
        <div class="big-tile-info">
          <span>{{ evt.type === 'team' ? 'Team' : evt.type === 'both' ? 'Individual + Team' : 'Individual' }}</span>
          <span v-if="evt.venue && evt.venue !== 'TBA'"> &bull; {{ evt.venue }}</span>
        </div>
        <div v-if="evt.categories" class="big-tile-note">{{ evt.categories }}</div>
      </router-link>
    </div>
  </template>

  <!-- Admin: compact cards -->
  <template v-else>
    <div class="events-grid">
      <router-link
        v-for="evt in filteredEvents"
        :key="evt.id"
        :to="`/events/${evt.id}`"
        class="event-card"
      >
        <div class="event-card-icon">{{ evt.icon }}</div>
        <div class="event-card-body">
          <div class="event-card-title">{{ evt.sport }}</div>
          <div class="event-card-meta">
            <span class="badge" :class="statusBadge(evt.status)">{{ evt.status }}</span>
            <span class="text-dim text-sm">{{ evt.type === 'team' ? 'Team' : evt.type === 'both' ? 'Individual + Team' : 'Individual' }}</span>
          </div>
          <div class="event-card-stats text-sm text-dim">
            <span v-if="evt.type === 'team'">{{ evt.teams.length }} teams</span>
            <span v-else>{{ evt.participants.length }} participants</span>
            <span v-if="evt.venue && evt.venue !== 'TBA'">{{ evt.venue }}</span>
            <span v-else>{{ evt.volunteers.length }} volunteers</span>
          </div>
        </div>
        <div class="event-card-status-dot" :class="evt.status"></div>
      </router-link>
    </div>
  </template>
</template>

<script setup>
import { ref, computed } from 'vue'
import { store, togglePinEvent, isEventPinned } from '../stores/tournament.js'

const filter = ref('all')

const filteredEvents = computed(() => {
  if (filter.value === 'all') return store.events
  if (filter.value === 'team') return store.events.filter(e => e.type === 'team' || e.type === 'both')
  if (filter.value === 'individual') return store.events.filter(e => e.type === 'individual' || e.type === 'both')
  return store.events.filter(e => e.status === filter.value)
})

const pinnedFiltered = computed(() => filteredEvents.value.filter(e => isEventPinned(e.id)))
const unpinnedFiltered = computed(() => filteredEvents.value.filter(e => !isEventPinned(e.id)))

function statusBadge(status) {
  if (status === 'completed') return 'badge-green'
  if (status === 'ongoing') return 'badge-ongoing'
  return 'badge-upcoming'
}

function latestNote(evt) {
  if (!evt.notes.length) return ''
  const sorted = [...evt.notes].sort((a, b) => b.createdAt.localeCompare(a.createdAt))
  const text = sorted[0].text
  return text.length > 60 ? text.slice(0, 57) + '...' : text
}
</script>
