<template>
  <div style="padding-bottom:72px">
  <h1>Schedule</h1>

  <!-- Filter tabs (inline, compact) -->
  <div class="schedule-filter-row">
    <button v-for="f in ['all','scheduled','completed','cancelled']" :key="f"
      class="schedule-filter-chip" :class="{ active: filter === f }" @click="filter = f">
      {{ f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1) }}
    </button>
  </div>

  <!-- Floating bottom bar for view mode -->
  <div class="schedule-float-bar">
    <button :class="{ active: viewMode === 'chrono' }" @click="viewMode = 'chrono'">
      <span class="float-icon">&#128197;</span><span class="float-label">By Date</span>
    </button>
    <button :class="{ active: viewMode === 'event' }" @click="viewMode = 'event'">
      <span class="float-icon">&#127941;</span><span class="float-label">By Event</span>
    </button>
    <button :class="{ active: viewMode === 'dept' }" @click="viewMode = 'dept'">
      <span class="float-icon">&#127963;</span><span class="float-label">By Dept</span>
    </button>
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

  <!-- CHRONO VIEW (grouped by date, then by sport+time) -->
  <template v-if="viewMode === 'chrono'">
    <div v-for="(group, date) in groupedByDate" :key="date" :ref="el => setDateRef(date, el)" class="mb-24">
      <h2 style="position:sticky;top:0;background:var(--bg);padding:8px 0;z-index:1">{{ formatDateHeader(date) }}</h2>
      <div class="card schedule-group-card" v-for="cluster in clusterGroup(group)" :key="cluster.key" style="margin-bottom:12px">
        <div class="schedule-group-header">
          <div class="flex items-center gap-12">
            <span style="font-size:22px">{{ cluster.icon }}</span>
            <div>
              <router-link :to="`/events/${cluster.eventId}`" class="event-name" style="text-decoration:none;font-weight:600">{{ cluster.sport }}</router-link>
              <div class="text-sm text-dim">
                <span v-if="cluster.time">{{ cluster.time }}</span>
                <span v-if="cluster.venue"> &mdash; {{ cluster.venue }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-for="item in cluster.items" :key="item.id" class="schedule-group-item">
          <div class="flex justify-between items-center">
            <div>
              <span class="team-name">{{ item.title }}</span>
              <span v-if="item.venue && item.venue !== cluster.venue" class="text-dim text-sm"> &mdash; {{ item.venue }}</span>
              <div class="text-sm" v-if="item.description" style="margin-top:2px;color:var(--text-dim)">{{ item.description }}</div>
            </div>
            <div class="flex gap-8 items-center">
              <span class="badge" :class="statusBadge(item.status)">{{ item.status }}</span>
              <template v-if="store.isAdmin">
                <select :value="item.status" @change="doChangeStatus(item, $event.target.value)" class="btn btn-sm" style="width:auto;cursor:pointer;padding:3px 6px;font-size:11px">
                  <option value="scheduled">Scheduled</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
                <button class="btn btn-sm btn-danger" @click="doRemove(item)">X</button>
              </template>
            </div>
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

  <!-- DEPT VIEW (grouped by department/team) -->
  <template v-if="viewMode === 'dept'">
    <div ref="deptTop"></div>
    <div style="margin-bottom:16px">
      <input v-model="deptSearch" placeholder="Search department or team name..." class="dept-picker-input" style="width:100%" />
    </div>
    <template v-if="deptSearch">
      <div v-for="(matches, dept) in filteredGroupedByDept" :key="dept" class="mb-24">
        <h2 style="position:sticky;top:0;background:var(--bg);padding:8px 0;z-index:1">{{ dept }} <span class="text-dim text-sm" style="font-weight:400">{{ matches.length }} matches</span></h2>
        <div class="card" v-for="item in matches" :key="item.id + item.eventId" style="margin-bottom:12px">
          <div class="flex justify-between items-center">
            <div>
              <div class="flex items-center gap-8" style="margin-bottom:2px">
                <span>{{ item.icon }}</span>
                <router-link :to="`/events/${item.eventId}`" style="text-decoration:none;font-weight:600;color:var(--text)">{{ item.sport }}</router-link>
              </div>
              <h3 style="margin-bottom:2px">{{ item.title }}</h3>
              <div class="text-sm text-dim">
                {{ formatDateHeader(item.date) }} <span v-if="item.time">at {{ item.time }}</span>
                <span v-if="item.venue"> &mdash; {{ item.venue }}</span>
              </div>
              <div class="text-sm" v-if="item.description" style="margin-top:4px;color:var(--text)">{{ item.description }}</div>
            </div>
            <span class="badge" :class="statusBadge(item.status)">{{ item.status }}</span>
          </div>
        </div>
      </div>
      <div class="empty-state" v-if="!Object.keys(filteredGroupedByDept).length">
        <p>No matches found for "{{ deptSearch }}".</p>
      </div>
    </template>
    <div v-else class="empty-state">
      <p>Type a department or team name to see their schedule across all sports.</p>
    </div>
  </template>

  <div class="empty-state" v-if="!allItems.length && viewMode !== 'dept'">
    <div class="icon">&#128197;</div>
    <p>No schedule entries yet.</p>
  </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { store, addScheduleItem, removeScheduleItem, getEvent } from '../stores/tournament.js'
import deptMapping from '../data/dept-mapping.json'

// Build alias → department lookup
const aliasToDept = {}
deptMapping.departments.forEach(dept => {
  dept.aliases.forEach(a => {
    aliasToDept[a.name.toLowerCase()] = dept.name
  })
})

const filter = ref('all')
const viewMode = ref('chrono')
const deptSearch = ref('')
const deptTop = ref(null)
const editing = ref(null)
const editData = reactive({ title: '', date: '', time: '', venue: '', description: '' })

const dateRefs = {}
function setDateRef(date, el) { if (el) dateRefs[date] = el }

onMounted(() => {
  // Delay auto-scroll slightly so the mobile rail doesn't hide from the scroll event
  setTimeout(() => {
    const today = new Date().toISOString().slice(0, 10)
    const dates = Object.keys(groupedByDate.value).sort()
    const target = dates.find(d => d >= today) || dates[dates.length - 1]
    if (target && dateRefs[target]) {
      const el = dateRefs[target]
      const y = el.getBoundingClientRect().top + window.scrollY - 80
      window.scrollTo({ top: Math.max(0, y), behavior: 'instant' })
    }
  }, 100)
})

watch(viewMode, () => {
  window.scrollTo({ top: 0, behavior: 'instant' })
})

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

// Extract team/dept names from match titles
function extractTeams(title) {
  // Remove common prefixes like "Pool 2:", "K1:", "Knockout 5:", "Stage 2:", "Final RR:", "M6:", "Round 1:"
  const cleaned = title.replace(/^(Pool\s*\d+|Knockout\s*\d+|Stage\s*\d+|Final\s*RR|Round\s*\d+|[KM]\d+)\s*:\s*/i, '').trim()
  // Split by " vs " or " v "
  const parts = cleaned.split(/\s+(?:vs?|VS?)\s+/)
  return parts.map(p => p.trim()).filter(Boolean)
}

// Resolve a team name to a department name via the mapping
function resolveDept(teamName) {
  const key = teamName.toLowerCase()
  return aliasToDept[key] || null
}

const groupedByDept = computed(() => {
  const groups = {}
  allItems.value.forEach(item => {
    const teams = extractTeams(item.title)
    teams.forEach(team => {
      if (!team || team.startsWith('Winner') || team.startsWith('TBD')) return
      const dept = resolveDept(team) || team // fallback to raw name if no mapping
      if (!groups[dept]) groups[dept] = []
      // Avoid duplicates (same match added via two aliases of same dept)
      if (!groups[dept].some(m => m.id === item.id && m.eventId === item.eventId)) {
        groups[dept].push(item)
      }
    })
  })
  const sorted = {}
  Object.keys(groups).sort().forEach(k => { sorted[k] = groups[k] })
  return sorted
})

// All department names for the picker
const allDeptNames = computed(() => Object.keys(groupedByDept.value))

const filteredGroupedByDept = computed(() => {
  if (!deptSearch.value) return {}
  const q = deptSearch.value.toLowerCase()
  const filtered = {}
  // Also match against dept codes and aliases
  const matchingDepts = new Set()
  deptMapping.departments.forEach(dept => {
    if (dept.name.toLowerCase().includes(q) || dept.code.toLowerCase().includes(q)) {
      matchingDepts.add(dept.name)
    }
    dept.aliases.forEach(a => {
      if (a.name.toLowerCase().includes(q)) matchingDepts.add(dept.name)
    })
  })
  Object.entries(groupedByDept.value).forEach(([dept, matches]) => {
    if (matchingDepts.has(dept) || dept.toLowerCase().includes(q)) {
      filtered[dept] = matches
    }
  })
  return filtered
})

// Group items within a date by sport + time
function clusterGroup(items) {
  const clusters = []
  const map = {}
  items.forEach(item => {
    const key = item.eventId + '|' + (item.time || '')
    if (!map[key]) {
      map[key] = { key, sport: item.sport, icon: item.icon, eventId: item.eventId, time: item.time, venue: item.venue, items: [] }
      clusters.push(map[key])
    }
    map[key].items.push(item)
  })
  return clusters
}

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
