<template>
  <h1>Bulletin Board</h1>

  <!-- Pinned announcements -->
  <div v-if="pinnedAnnouncements.length" class="mb-24">
    <h2>Pinned</h2>
    <div v-for="ann in pinnedAnnouncements" :key="ann.id" class="bulletin-card pinned">
      <div class="bulletin-pin-icon">&#128204;</div>
      <div style="flex:1">
        <p class="bulletin-text">{{ ann.text }}</p>
        <div class="text-sm text-dim" style="margin-top:4px">{{ formatDate(ann.createdAt) }}</div>
      </div>
      <div v-if="store.isAdmin" class="flex gap-8">
        <button class="btn btn-sm" @click="toggleAnnouncementPin(ann.id)">Unpin</button>
        <button class="btn btn-sm btn-danger" @click="doRemoveAnnouncement(ann.id)">X</button>
      </div>
    </div>
  </div>

  <!-- Add announcement (admin) -->
  <div class="card" v-if="store.isAdmin">
    <h3>Post Announcement</h3>
    <div class="form-row">
      <div class="field" style="flex:1">
        <label>Announcement</label>
        <input v-model="newAnn" placeholder="Write an announcement..." style="width:100%" @keyup.enter="doAddAnnouncement" />
      </div>
      <label class="flex items-center gap-8" style="text-transform:none;font-size:13px;color:var(--text);cursor:pointer">
        <input type="checkbox" v-model="newAnnPinned" style="width:auto" /> Pin
      </label>
      <button class="btn btn-primary" @click="doAddAnnouncement">Post</button>
    </div>
  </div>

  <!-- All announcements -->
  <div v-if="regularAnnouncements.length" class="mb-24">
    <h2>Announcements</h2>
    <div v-for="ann in regularAnnouncements" :key="ann.id" class="bulletin-card">
      <div style="flex:1">
        <p class="bulletin-text">{{ ann.text }}</p>
        <div class="text-sm text-dim" style="margin-top:4px">{{ formatDate(ann.createdAt) }}</div>
      </div>
      <div v-if="store.isAdmin" class="flex gap-8">
        <button class="btn btn-sm" @click="toggleAnnouncementPin(ann.id)">Pin</button>
        <button class="btn btn-sm btn-danger" @click="doRemoveAnnouncement(ann.id)">X</button>
      </div>
    </div>
  </div>

  <!-- Completed events / Winners -->
  <div v-if="completedEvents.length" class="mb-24">
    <h2>Completed Events</h2>
    <div class="events-grid" style="grid-template-columns: repeat(auto-fill, minmax(220px, 1fr))">
      <router-link v-for="evt in completedEvents" :key="evt.id" :to="`/events/${evt.id}`" class="bulletin-winner-card">
        <div style="font-size:36px;margin-bottom:8px">{{ evt.icon }}</div>
        <div class="event-card-title">{{ evt.sport }}</div>
        <span class="badge badge-green">Completed</span>
      </router-link>
    </div>
  </div>

  <!-- Upcoming schedule preview -->
  <div v-if="upcomingSchedule.length">
    <h2>Coming Up Next</h2>
    <div class="card" v-for="item in upcomingSchedule" :key="item.id" style="margin-bottom:12px">
      <div class="flex items-center gap-12">
        <span style="font-size:22px">{{ item.icon }}</span>
        <div>
          <div class="flex items-center gap-8">
            <router-link :to="`/events/${item.eventId}`" class="event-name" style="text-decoration:none">{{ item.sport }}</router-link>
            <span class="text-dim">&mdash;</span>
            <span class="team-name">{{ item.title }}</span>
          </div>
          <div class="text-sm text-dim">
            {{ item.date }} <span v-if="item.time">at {{ item.time }}</span>
            <span v-if="item.venue"> &mdash; {{ item.venue }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="empty-state" v-if="!store.announcements?.length && !completedEvents.length && !upcomingSchedule.length">
    <div class="icon">&#128227;</div>
    <p>No announcements yet.</p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { store, addAnnouncement, removeAnnouncement, toggleAnnouncementPin } from '../stores/tournament.js'

const newAnn = ref('')
const newAnnPinned = ref(false)

const allAnnouncements = computed(() =>
  [...(store.announcements || [])].sort((a, b) => b.createdAt.localeCompare(a.createdAt))
)
const pinnedAnnouncements = computed(() => allAnnouncements.value.filter(a => a.pinned))
const regularAnnouncements = computed(() => allAnnouncements.value.filter(a => !a.pinned))

const completedEvents = computed(() => store.events.filter(e => e.status === 'completed'))

const upcomingSchedule = computed(() => {
  const items = []
  store.events.forEach((evt) => {
    evt.schedule.forEach((sch) => {
      if (sch.status === 'scheduled') {
        items.push({ ...sch, sport: evt.sport, icon: evt.icon, eventId: evt.id })
      }
    })
  })
  return items.sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time)).slice(0, 8)
})

function doAddAnnouncement() {
  if (!newAnn.value.trim()) return
  addAnnouncement(newAnn.value.trim(), newAnnPinned.value)
  newAnn.value = ''
  newAnnPinned.value = false
}

function doRemoveAnnouncement(id) {
  removeAnnouncement(id)
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>
