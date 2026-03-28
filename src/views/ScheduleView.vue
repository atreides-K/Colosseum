<template>
  <h1>Schedule</h1>

  <div class="flex justify-between items-center" style="flex-wrap:wrap;gap:8px;margin-bottom:16px">
    <div class="tabs" style="margin-bottom:0">
      <button class="tab" :class="{ active: filter === 'all' }" @click="filter = 'all'">All</button>
      <button class="tab" :class="{ active: filter === 'scheduled' }" @click="filter = 'scheduled'">Scheduled</button>
      <button class="tab" :class="{ active: filter === 'completed' }" @click="filter = 'completed'">Completed</button>
      <button class="tab" :class="{ active: filter === 'cancelled' }" @click="filter = 'cancelled'">Cancelled</button>
    </div>
    <div class="tabs" style="margin-bottom:0">
      <button class="tab" :class="{ active: viewMode === 'chrono' }" @click="viewMode = 'chrono'">By Date</button>
      <button class="tab" :class="{ active: viewMode === 'event' }" @click="viewMode = 'event'">By Event</button>
    </div>
  </div>

  <!-- ADD FORM (admin only) -->
  <div class="card" v-if="store.isAdmin" style="margin-bottom:24px">
    <h3 style="margin-bottom:8px">Add Schedule Entry</h3>
    <div class="form-row">
      <div class="field">
        <label>Event</label>
        <select v-model="newEntry.eventId" style="width:160px">
          <option value="" disabled>Select event</option>
          <option v-for="evt in store.events" :key="evt.id" :value="evt.id">{{ evt.icon }} {{ evt.sport }}</option>
        </select>
      </div>
      <div class="field">
        <label>Title</label>
        <input v-model="newEntry.title" placeholder="e.g. Semi-finals" @keyup.enter="doAdd" />
      </div>
      <div class="field">
        <label>Date</label>
        <input v-model="newEntry.date" type="date" />
      </div>
      <div class="field">
        <label>Time</label>
        <input v-model="newEntry.time" type="time" style="width:120px" />
      </div>
      <div class="field">
        <label>Venue</label>
        <input v-model="newEntry.venue" :placeholder="selectedEventVenue" />
      </div>
      <button class="btn btn-primary" @click="doAdd" :disabled="!newEntry.eventId || !newEntry.title || !newEntry.date">Add</button>
    </div>
    <div class="form-row">
      <div class="field" style="flex:1">
        <label>Description</label>
        <input v-model="newEntry.description" placeholder="Optional details" style="width:100%" @keyup.enter="doAdd" />
      </div>
    </div>
  </div>

  <!-- CHRONO VIEW (grouped by date) -->
  <template v-if="viewMode === 'chrono'">
    <div v-for="(group, date) in groupedByDate" :key="date" class="mb-24">
      <h2 style="position:sticky;top:0;background:var(--bg);padding:8px 0;z-index:1">{{ formatDateHeader(date) }}</h2>
      <div class="card" v-for="item in group" :key="item.id" style="margin-bottom:12px">
        <div class="flex justify-between items-center">
          <div class="flex items-center gap-12">
            <span style="font-size:22px">{{ item.icon }}</span>
            <div>
              <div class="flex items-center gap-8">
                <router-link :to="`/events/${item.eventId}`" class="event-name" style="text-decoration:none">{{ item.sport }}</router-link>
                <span class="text-dim">&mdash;</span>
                <span v-if="editing !== item.id" class="team-name">{{ item.title }}</span>
              </div>
              <div v-if="editing === item.id" class="form-row" style="margin-top:6px">
                <input v-model="editData.title" style="width:140px" />
                <input v-model="editData.date" type="date" style="width:140px" />
                <input v-model="editData.time" type="time" style="width:100px" />
                <input v-model="editData.venue" placeholder="Venue" style="width:140px" />
                <input v-model="editData.description" placeholder="Description" style="width:180px" />
                <button class="btn btn-sm btn-primary" @click="doSaveEdit(item)">Save</button>
                <button class="btn btn-sm" @click="editing = null">Cancel</button>
              </div>
              <template v-else>
                <div class="text-sm text-dim">
                  <span v-if="item.time">{{ item.time }}</span>
                  <span v-if="item.venue"> &mdash; {{ item.venue }}</span>
                </div>
                <div class="text-sm" v-if="item.description" style="margin-top:4px;color:var(--text)">{{ item.description }}</div>
              </template>
            </div>
          </div>
          <div class="flex gap-8 items-center">
            <span v-if="editing !== item.id" class="badge" :class="statusBadge(item.status)">{{ item.status }}</span>
            <template v-if="store.isAdmin && editing !== item.id">
              <select :value="item.status" @change="doChangeStatus(item, $event.target.value)" class="btn btn-sm" style="width:auto;cursor:pointer;padding:3px 6px;font-size:11px">
                <option value="scheduled">Scheduled</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
              <button class="btn btn-sm" @click="startEdit(item)" title="Edit">&#9998;</button>
              <button class="btn btn-sm btn-danger" @click="doRemove(item)">X</button>
            </template>
          </div>
        </div>
      </div>
    </div>
  </template>

  <!-- EVENT VIEW (grouped by sport) -->
  <template v-if="viewMode === 'event'">
    <div v-for="(group, sport) in groupedByEvent" :key="sport" class="mb-24">
      <h2 style="position:sticky;top:0;background:var(--bg);padding:8px 0;z-index:1">
        <router-link :to="`/events/${group[0].eventId}`" style="text-decoration:none;color:inherit">
          {{ group[0].icon }} {{ sport }}
        </router-link>
      </h2>
      <div class="card" v-for="item in group" :key="item.id" style="margin-bottom:12px">
        <div class="flex justify-between items-center">
          <div>
            <div v-if="editing === item.id" class="form-row">
              <input v-model="editData.title" style="width:140px" />
              <input v-model="editData.date" type="date" style="width:140px" />
              <input v-model="editData.time" type="time" style="width:100px" />
              <input v-model="editData.venue" placeholder="Venue" style="width:140px" />
              <input v-model="editData.description" placeholder="Description" style="width:180px" />
              <button class="btn btn-sm btn-primary" @click="doSaveEdit(item)">Save</button>
              <button class="btn btn-sm" @click="editing = null">Cancel</button>
            </div>
            <template v-else>
              <h3 style="margin-bottom:2px">{{ item.title }}</h3>
              <div class="text-sm text-dim">
                {{ item.date }} <span v-if="item.time">at {{ item.time }}</span>
                <span v-if="item.venue"> &mdash; {{ item.venue }}</span>
              </div>
              <div class="text-sm" v-if="item.description" style="margin-top:4px;color:var(--text)">{{ item.description }}</div>
            </template>
          </div>
          <div class="flex gap-8 items-center">
            <span v-if="editing !== item.id" class="badge" :class="statusBadge(item.status)">{{ item.status }}</span>
            <template v-if="store.isAdmin && editing !== item.id">
              <select :value="item.status" @change="doChangeStatus(item, $event.target.value)" class="btn btn-sm" style="width:auto;cursor:pointer;padding:3px 6px;font-size:11px">
                <option value="scheduled">Scheduled</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
              <button class="btn btn-sm" @click="startEdit(item)" title="Edit">&#9998;</button>
              <button class="btn btn-sm btn-danger" @click="doRemove(item)">X</button>
            </template>
          </div>
        </div>
      </div>
    </div>
  </template>

  <div class="empty-state" v-if="!allItems.length">
    <div class="icon">&#128197;</div>
    <p>No schedule entries yet.</p>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { store, addScheduleItem, removeScheduleItem, getEvent } from '../stores/tournament.js'

const filter = ref('all')
const viewMode = ref('chrono')
const editing = ref(null)
const editData = reactive({ title: '', date: '', time: '', venue: '', description: '' })

const newEntry = reactive({
  eventId: '', title: '', date: '', time: '', venue: '', description: '',
})

const selectedEventVenue = computed(() => {
  if (!newEntry.eventId) return 'Venue'
  const evt = getEvent(newEntry.eventId)
  return evt?.venue || 'Venue'
})

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

const groupedByDate = computed(() => {
  const groups = {}
  allItems.value.forEach((item) => {
    const date = item.date || 'TBD'
    if (!groups[date]) groups[date] = []
    groups[date].push(item)
  })
  return groups
})

const groupedByEvent = computed(() => {
  const groups = {}
  allItems.value.forEach((item) => {
    if (!groups[item.sport]) groups[item.sport] = []
    groups[item.sport].push(item)
  })
  return groups
})

function statusBadge(status) {
  return status === 'completed' ? 'badge-green' : status === 'cancelled' ? 'badge-red' : 'badge-upcoming'
}

function formatDateHeader(dateStr) {
  if (dateStr === 'TBD') return 'Date TBD'
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
}

function doAdd() {
  if (!newEntry.eventId || !newEntry.title || !newEntry.date) return
  addScheduleItem(newEntry.eventId, {
    title: newEntry.title,
    date: newEntry.date,
    time: newEntry.time,
    venue: newEntry.venue,
    description: newEntry.description,
  })
  newEntry.title = ''
  newEntry.date = ''
  newEntry.time = ''
  newEntry.venue = ''
  newEntry.description = ''
}

function doRemove(item) {
  removeScheduleItem(item.eventId, item.id)
}

function doChangeStatus(item, newStatus) {
  const evt = getEvent(item.eventId)
  if (!evt) return
  const sch = evt.schedule.find((s) => s.id === item.id)
  if (sch) sch.status = newStatus
}

function startEdit(item) {
  editing.value = item.id
  editData.title = item.title
  editData.date = item.date
  editData.time = item.time
  editData.venue = item.venue
  editData.description = item.description
}

function doSaveEdit(item) {
  const evt = getEvent(item.eventId)
  if (!evt) return
  const sch = evt.schedule.find((s) => s.id === item.id)
  if (sch) {
    sch.title = editData.title
    sch.date = editData.date
    sch.time = editData.time
    sch.venue = editData.venue
    sch.description = editData.description
  }
  editing.value = null
}
</script>
