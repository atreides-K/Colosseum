<template>
  <h1>Schedule</h1>

  <div class="tabs">
    <button class="tab" :class="{ active: filter === 'all' }" @click="filter = 'all'">All</button>
    <button class="tab" :class="{ active: filter === 'scheduled' }" @click="filter = 'scheduled'">Scheduled</button>
    <button class="tab" :class="{ active: filter === 'completed' }" @click="filter = 'completed'">Completed</button>
    <button class="tab" :class="{ active: filter === 'cancelled' }" @click="filter = 'cancelled'">Cancelled</button>
  </div>

  <div v-for="(group, date) in groupedSchedule" :key="date" class="mb-24">
    <h2 style="position:sticky;top:0;background:var(--bg);padding:8px 0;z-index:1">{{ formatDateHeader(date) }}</h2>
    <div class="card" v-for="item in group" :key="item.id" style="margin-bottom:12px">
      <div class="flex justify-between items-center">
        <div class="flex items-center gap-12">
          <span style="font-size:22px">{{ item.icon }}</span>
          <div>
            <div class="flex items-center gap-8">
              <router-link :to="`/events/${item.eventId}`" class="event-name" style="text-decoration:none">{{ item.sport }}</router-link>
              <span class="text-dim">&mdash;</span>
              <span class="team-name">{{ item.title }}</span>
            </div>
            <div class="text-sm text-dim">
              <span v-if="item.time">{{ item.time }}</span>
              <span v-if="item.venue"> &mdash; {{ item.venue }}</span>
            </div>
            <div class="text-sm" v-if="item.description" style="margin-top:4px;color:var(--text)">{{ item.description }}</div>
          </div>
        </div>
        <span class="badge" :class="item.status === 'completed' ? 'badge-green' : item.status === 'cancelled' ? 'badge-red' : 'badge-upcoming'">
          {{ item.status }}
        </span>
      </div>
    </div>
  </div>

  <div class="empty-state" v-if="!allItems.length">
    <div class="icon">&#128197;</div>
    <p>No schedule entries yet.</p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { store } from '../stores/tournament.js'

const filter = ref('all')

const allItems = computed(() => {
  const items = []
  store.events.forEach((evt) => {
    evt.schedule.forEach((sch) => {
      if (filter.value !== 'all' && sch.status !== filter.value) return
      items.push({ ...sch, sport: evt.sport, icon: evt.icon, eventId: evt.id })
    })
  })
  return items.sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time))
})

const groupedSchedule = computed(() => {
  const groups = {}
  allItems.value.forEach((item) => {
    const date = item.date || 'TBD'
    if (!groups[date]) groups[date] = []
    groups[date].push(item)
  })
  return groups
})

function formatDateHeader(dateStr) {
  if (dateStr === 'TBD') return 'Date TBD'
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
}
</script>
