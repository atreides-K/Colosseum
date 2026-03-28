<template>
  <!-- ==================== VIEWER HOMEPAGE ==================== -->
  <template v-if="!store.isAdmin">
    <h1>{{ store.tournamentName }}</h1>

    <!-- Pinned announcements banner -->
    <div v-if="pinnedAnnouncements.length" class="announcement-banner">
      <span>&#128227;</span>
      <span v-for="(ann, i) in pinnedAnnouncements" :key="ann.id">
        {{ ann.text }}<span v-if="i < pinnedAnnouncements.length - 1" style="margin:0 12px;opacity:0.3">|</span>
      </span>
    </div>

    <!-- Today's / Upcoming schedule -->
    <div v-if="todaySchedule.length" class="mb-24">
      <h2>Today's Events</h2>
      <div v-for="item in todaySchedule" :key="item.id" class="schedule-row">
        <div class="schedule-time">{{ item.time || '--:--' }}</div>
        <router-link :to="`/events/${item.eventId}`" class="schedule-detail">
          <span class="schedule-icon">{{ item.icon }}</span>
          <div>
            <div class="schedule-sport">{{ item.sport }} <span class="text-dim">&mdash;</span> {{ item.title }}</div>
            <div class="schedule-venue">{{ item.venue }}</div>
          </div>
          <span class="badge" :class="item.status === 'completed' ? 'badge-green' : 'badge-upcoming'">{{ item.status }}</span>
        </router-link>
      </div>
    </div>

    <div v-if="nextDaysSchedule.length" class="mb-24">
      <h2>Coming Up</h2>
      <div v-for="item in nextDaysSchedule" :key="item.id" class="schedule-row">
        <div class="schedule-time">
          <div>{{ formatShortDate(item.date) }}</div>
          <div class="text-dim" style="font-size:11px">{{ item.time || '' }}</div>
        </div>
        <router-link :to="`/events/${item.eventId}`" class="schedule-detail">
          <span class="schedule-icon">{{ item.icon }}</span>
          <div>
            <div class="schedule-sport">{{ item.sport }} <span class="text-dim">&mdash;</span> {{ item.title }}</div>
            <div class="schedule-venue">{{ item.venue }}</div>
          </div>
        </router-link>
      </div>
    </div>

    <!-- Pinned events with full details -->
    <div v-for="evt in pinnedEventsData" :key="evt.id" class="pinned-detail-card mb-24">
      <div class="pinned-detail-header">
        <router-link :to="`/events/${evt.id}`" class="pinned-detail-title">
          <span class="pinned-detail-icon">{{ evt.icon }}</span>
          <span>{{ evt.sport }}</span>
        </router-link>
        <div class="flex gap-8 items-center">
          <span class="badge" :class="statusBadge(evt.status)">{{ evt.status }}</span>
          <button class="pin-btn pinned" @click="togglePinEvent(evt.id)" title="Unpin">&#128204;</button>
        </div>
      </div>

      <!-- Quick info row -->
      <div class="pinned-info-grid">
        <div v-if="evt.categories" class="pinned-info-item">
          <span class="pinned-info-label">Categories</span>
          <span>{{ evt.categories }}</span>
        </div>
        <div v-if="evt.venue && evt.venue !== 'TBA'" class="pinned-info-item">
          <span class="pinned-info-label">Venue</span>
          <span>{{ evt.venue }}</span>
        </div>
        <div v-if="evt.teamSize" class="pinned-info-item">
          <span class="pinned-info-label">Team Size</span>
          <span>{{ evt.teamSize }}</span>
        </div>
        <div v-if="evt.guestPlayers" class="pinned-info-item">
          <span class="pinned-info-label">Guest Players</span>
          <span>{{ evt.guestPlayers }}</span>
        </div>
        <div v-if="evt.registrationDeadline" class="pinned-info-item">
          <span class="pinned-info-label">Reg. Deadline</span>
          <span>{{ evt.registrationDeadline }}</span>
        </div>
      </div>

      <!-- Format -->
      <div v-if="evt.format" class="pinned-detail-section">
        <h3>Format &amp; Details</h3>
        <div class="pinned-detail-format" v-html="formatToHtml(evt.format)"></div>
      </div>

      <!-- Schedule -->
      <div v-if="eventSchedule(evt).length" class="pinned-detail-section">
        <h3>Schedule</h3>
        <div v-for="sch in eventSchedule(evt)" :key="sch.id" class="pinned-schedule-item">
          <span class="pinned-schedule-date">{{ formatShortDate(sch.date) }}</span>
          <span v-if="sch.time" class="text-dim">{{ sch.time }}</span>
          <span class="pinned-schedule-title">{{ sch.title }}</span>
          <span v-if="sch.venue" class="text-dim">— {{ sch.venue }}</span>
          <span class="badge btn-sm" :class="sch.status === 'completed' ? 'badge-green' : sch.status === 'cancelled' ? 'badge-red' : 'badge-upcoming'">{{ sch.status }}</span>
        </div>
      </div>

      <!-- Contacts -->
      <div v-if="evt.contacts && evt.contacts.length" class="pinned-detail-section">
        <h3>Contact</h3>
        <div class="pinned-detail-contacts">
          <span v-for="(c, i) in evt.contacts" :key="i" class="pinned-contact">
            <template v-if="c.name">{{ c.name }}</template>
            <template v-else>Organizer</template>
            <span v-if="c.phone" class="text-dim"> — {{ c.phone }}</span>
            <a v-if="c.email" :href="'mailto:' + c.email" class="contact-email">{{ c.email }}</a>
          </span>
        </div>
      </div>

      <!-- Action links -->
      <div class="pinned-detail-links">
        <a v-if="evt.registrationLink" :href="evt.registrationLink" target="_blank" rel="noopener" class="btn btn-primary">Register</a>
        <a v-if="evt.registrationLinkWomens" :href="evt.registrationLinkWomens" target="_blank" rel="noopener" class="btn btn-primary">Register (Women's)</a>
        <a v-if="evt.whatsappLink" :href="evt.whatsappLink" target="_blank" rel="noopener" class="btn btn-whatsapp">WhatsApp Group</a>
        <router-link :to="`/events/${evt.id}`" class="btn">Full Details &rarr;</router-link>
      </div>
    </div>

    <!-- All events as big tiles -->
    <h2>All Events</h2>
    <div class="big-tiles-grid">
      <router-link v-for="evt in unpinnedEvents" :key="evt.id" :to="`/events/${evt.id}`" class="big-tile">
        <button class="pin-btn" @click.prevent="togglePinEvent(evt.id)" title="Pin this event">&#128204;</button>
        <div class="big-tile-icon">{{ evt.icon }}</div>
        <div class="big-tile-name">{{ evt.sport }}</div>
        <span class="badge" :class="statusBadge(evt.status)">{{ evt.status }}</span>
        <div class="big-tile-info">{{ evt.type === 'team' ? 'Team' : 'Individual' }}</div>
      </router-link>
    </div>
  </template>

  <!-- ==================== ADMIN DASHBOARD ==================== -->
  <template v-else>
    <h1>{{ store.tournamentName }}</h1>

    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-number">{{ store.events.length }}</div>
        <div class="stat-label">Sports Events</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ participantCount }}</div>
        <div class="stat-label">Participants</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ volunteerCount }}</div>
        <div class="stat-label">Volunteers</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ ongoingCount }}</div>
        <div class="stat-label">Ongoing</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ completedCount }}</div>
        <div class="stat-label">Completed</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ upcomingCount }}</div>
        <div class="stat-label">Upcoming</div>
      </div>
    </div>

    <div class="card" v-if="ongoingEvents.length">
      <h2>Ongoing Events</h2>
      <div class="event-list">
        <router-link v-for="evt in ongoingEvents" :key="evt.id" :to="`/events/${evt.id}`" class="event-row">
          <span class="event-icon">{{ evt.icon }}</span>
          <span class="event-name">{{ evt.sport }}</span>
          <span class="badge badge-ongoing">Ongoing</span>
          <span class="text-dim text-sm">{{ eventParticipantLabel(evt) }}</span>
        </router-link>
      </div>
    </div>

    <div class="card" v-if="upcomingEvents.length">
      <h2>Upcoming Events</h2>
      <div class="event-list">
        <router-link v-for="evt in upcomingEvents" :key="evt.id" :to="`/events/${evt.id}`" class="event-row">
          <span class="event-icon">{{ evt.icon }}</span>
          <span class="event-name">{{ evt.sport }}</span>
          <span class="badge badge-upcoming">Upcoming</span>
          <span class="text-dim text-sm" v-if="nextScheduleDate(evt)">{{ nextScheduleDate(evt) }}</span>
        </router-link>
      </div>
    </div>

    <div class="card" v-if="completedEvents.length">
      <h2>Completed Events</h2>
      <div class="event-list">
        <router-link v-for="evt in completedEvents" :key="evt.id" :to="`/events/${evt.id}`" class="event-row">
          <span class="event-icon">{{ evt.icon }}</span>
          <span class="event-name">{{ evt.sport }}</span>
          <span class="badge badge-green">Completed</span>
        </router-link>
      </div>
    </div>
  </template>
</template>

<script setup>
import { computed } from 'vue'
import { store, totalParticipants, totalVolunteers, getEvent, isEventPinned, togglePinEvent } from '../stores/tournament.js'

const participantCount = computed(() => totalParticipants())
const volunteerCount = computed(() => totalVolunteers())

const ongoingEvents = computed(() => store.events.filter(e => e.status === 'ongoing'))
const upcomingEvents = computed(() => store.events.filter(e => e.status === 'upcoming'))
const completedEvents = computed(() => store.events.filter(e => e.status === 'completed'))

const ongoingCount = computed(() => ongoingEvents.value.length)
const upcomingCount = computed(() => upcomingEvents.value.length)
const completedCount = computed(() => completedEvents.value.length)

const pinnedEventsData = computed(() =>
  (store.pinnedEvents || []).map(id => getEvent(id)).filter(Boolean)
)

const unpinnedEvents = computed(() =>
  store.events.filter(e => !isEventPinned(e.id))
)

function formatToHtml(text) {
  if (!text) return ''
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n/g, '<br>')
}

function eventSchedule(evt) {
  return [...evt.schedule]
    .sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time))
}

const pinnedAnnouncements = computed(() =>
  (store.announcements || []).filter(a => a.pinned).sort((a, b) => b.createdAt.localeCompare(a.createdAt))
)

// Build schedule items from all events
const allScheduleItems = computed(() => {
  const items = []
  store.events.forEach((evt) => {
    evt.schedule.forEach((sch) => {
      items.push({ ...sch, sport: evt.sport, icon: evt.icon, eventId: evt.id })
    })
  })
  return items.sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time))
})

const today = computed(() => new Date().toISOString().slice(0, 10))

const todaySchedule = computed(() =>
  allScheduleItems.value.filter(s => s.date === today.value)
)

const nextDaysSchedule = computed(() =>
  allScheduleItems.value.filter(s => s.date > today.value && s.status === 'scheduled').slice(0, 6)
)

function formatShortDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
}

function eventParticipantLabel(evt) {
  if (evt.type === 'team') return `${evt.teams.length} teams`
  return `${evt.participants.length} participants`
}

function nextScheduleDate(evt) {
  const upcoming = evt.schedule.filter(s => s.status === 'scheduled').sort((a, b) => a.date.localeCompare(b.date))
  if (!upcoming.length) return ''
  return upcoming[0].date
}

function statusBadge(status) {
  if (status === 'completed') return 'badge-green'
  if (status === 'ongoing') return 'badge-ongoing'
  return 'badge-upcoming'
}
</script>
