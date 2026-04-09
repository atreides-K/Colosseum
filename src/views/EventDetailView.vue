<template>
  <div v-if="evt">
    <div class="flex items-center gap-12 mb-24">
      <span style="font-size:36px">{{ evt.icon }}</span>
      <div>
        <h1 style="margin-bottom:4px">{{ evt.sport }}</h1>
        <div class="flex gap-8 items-center">
          <span class="badge" :class="statusBadge(evt.status)">{{ evt.status }}</span>
          <span class="text-dim text-sm">{{ evt.type === 'team' ? 'Team' : evt.type === 'both' ? 'Individual + Team' : 'Individual' }}</span>
          <span class="text-dim text-sm">{{ evt.venue }}</span>
        </div>
      </div>
      <div style="margin-left:auto" class="flex gap-8 items-center">
        <transition name="save-fade">
          <span v-if="store.isAdmin && dirty" class="save-indicator">
            <span class="save-dot"></span> Unsaved changes &mdash; auto-saving...
          </span>
        </transition>
        <button v-if="!store.isAdmin" class="btn btn-sm" :class="{ 'btn-primary': isPinned }" @click="togglePinEvent(evt.id)">
          &#128204; {{ isPinned ? 'Pinned' : 'Pin Event' }}
        </button>
        <select v-if="store.isAdmin" v-model="evt.status" class="btn btn-sm" style="cursor:pointer" @change="flashSaved">
          <option value="upcoming">Upcoming</option>
          <option value="ongoing">Ongoing</option>
          <option value="completed">Completed</option>
        </select>
      </div>
    </div>

    <!-- Event info card (both modes — editable in admin) -->
    <div class="event-info-card">
      <div class="info-summary">
        <p class="info-para">
          <span class="info-label-inline">Venue:</span>
          <template v-if="store.isAdmin">
            <input v-model="evt.venue" class="info-input-inline" placeholder="Enter venue" @input="flashSaved" />
          </template>
          <template v-else>
            <span>{{ evt.venue || 'TBD' }}</span>
          </template>
          <span class="info-sep">&bull;</span>
          <span class="info-label-inline">{{ evt.type === 'team' ? 'Teams' : 'Participants' }}:</span>
          <span>{{ evt.type === 'team' ? evt.teams.length + ' teams' : evt.participants.length + ' registered' }}</span>
          <template v-if="nextScheduleItem">
            <span class="info-sep">&bull;</span>
            <span class="info-label-inline">Next Up:</span>
            <span>{{ nextScheduleItem.title }} &mdash; {{ nextScheduleItem.date }} <span v-if="nextScheduleItem.time">at {{ nextScheduleItem.time }}</span></span>
          </template>
        </p>
        <p class="info-para">
          <span class="info-label-inline">Contact:</span>
          <template v-if="evt.contacts && evt.contacts.length">
            <span v-for="(c, i) in evt.contacts.slice(0, 2)" :key="i">
              <span v-if="i > 0"> &bull; </span>
              {{ c.name || 'Organizer' }}<span v-if="c.phone" class="text-dim"> &mdash; {{ c.phone }}</span>
            </span>
          </template>
          <template v-else-if="evt.volunteers.length">
            <span>{{ evt.volunteers[0].name }}<span v-if="evt.volunteers[0].contact" class="text-dim"> &mdash; {{ evt.volunteers[0].contact }}</span></span>
          </template>
          <span v-else class="text-dim">Not assigned</span>
        </p>
        <div class="info-notes-block" v-if="latestNote">
          <p class="info-note-text">
            <span style="opacity:0.5">Latest:</span> {{ latestNote }}
          </p>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button class="tab" :class="{ active: tab === 'info' }" @click="tab = 'info'">Info</button>
      <button v-if="eventRules" class="tab" :class="{ active: tab === 'rules' }" @click="tab = 'rules'">Rules</button>
      <button class="tab" :class="{ active: tab === 'participants' }" @click="tab = 'participants'">
        {{ evt.type === 'team' ? 'Teams' : 'Participants' }}
      </button>
      <button class="tab" :class="{ active: tab === 'schedule' }" @click="tab = 'schedule'">Schedule</button>
      <button class="tab" :class="{ active: tab === 'standings' }" @click="tab = 'standings'">Standings</button>
      <button class="tab" :class="{ active: tab === 'notes' }" @click="tab = 'notes'">Notes</button>
    </div>

    <!-- INFO TAB -->
    <div v-if="tab === 'info'">
      <div class="event-info-layout" :class="{ 'has-poster': eventPoster }">
        <div class="card event-detail-info">
          <div class="info-grid">
            <div class="info-item" v-if="evt.categories">
              <span class="info-label">Categories</span>
              <span>{{ evt.categories }}</span>
            </div>
            <div class="info-item" v-if="evt.teamSize">
              <span class="info-label">Team Size</span>
              <span>{{ evt.teamSize }}</span>
            </div>
            <div class="info-item" v-if="evt.guestPlayers">
              <span class="info-label">Guest Players</span>
              <span>{{ evt.guestPlayers }}</span>
            </div>
            <div class="info-item" v-if="evt.registrationDeadline">
              <span class="info-label">Registration Deadline</span>
              <span>{{ evt.registrationDeadline }}</span>
            </div>
          </div>
          <div class="format-block" v-if="evt.format">
            <h3>Format &amp; Details</h3>
            <div class="format-text" v-html="formatToHtml(evt.format)"></div>
          </div>
          <div class="event-links">
            <a v-if="evt.registrationLink" :href="evt.registrationLink" target="_blank" rel="noopener" class="btn btn-primary">Register</a>
            <a v-if="evt.registrationLinkWomens" :href="evt.registrationLinkWomens" target="_blank" rel="noopener" class="btn btn-primary">Register (Women's)</a>
            <a v-if="evt.whatsappLink" :href="evt.whatsappLink" target="_blank" rel="noopener" class="btn btn-whatsapp">WhatsApp Group</a>
            <button v-if="eventRules" class="btn" @click="tab = 'rules'">View Rulebook</button>
          </div>
        </div>
        <div v-if="eventPoster" class="event-poster-side">
          <img :src="eventPoster" :alt="evt.sport + ' poster'" />
        </div>
      </div>
    </div>

    <!-- RULES TAB -->
    <div v-if="tab === 'rules' && eventRules">
      <div class="rules-pdf-links">
        <template v-if="props.id === 'evt-chess'">
          <a href="rules/chess-individual.pdf" target="_blank" rel="noopener" class="btn btn-sm">Individual Rules PDF</a>
          <a href="rules/chess-team.pdf" target="_blank" rel="noopener" class="btn btn-sm">Team Rules PDF</a>
        </template>
        <a v-else :href="`rules/${props.id.replace('evt-', '')}.pdf`" target="_blank" rel="noopener" class="btn btn-sm">Download Rules PDF</a>
      </div>
      <div class="card rules-content" v-html="renderedRules"></div>
    </div>

    <!-- TEAMS TAB (team sports) -->
    <div v-if="tab === 'participants' && evt.type === 'team'">
      <div class="card" v-if="store.isAdmin">
        <h3>Add Team</h3>
        <div class="form-row">
          <div class="field">
            <label>Team Name</label>
            <input v-model="newTeam.name" placeholder="e.g. CSE Football" @keyup.enter="doAddTeam" />
          </div>
          <button class="btn btn-primary" @click="doAddTeam">Add Team</button>
        </div>
      </div>

      <div class="card" v-for="team in evt.teams" :key="team.id">
        <div class="flex justify-between items-center mb-8">
          <h3 style="margin-bottom:0">{{ team.name }}</h3>
          <div class="flex gap-8">
            <span class="text-dim text-sm">{{ team.members.length }} members</span>
            <button v-if="store.isAdmin" class="btn btn-sm btn-danger" @click="doRemoveTeam(team.id)">Remove</button>
          </div>
        </div>
        <div class="flex flex-wrap gap-8 mb-8">
          <span v-for="(member, mi) in team.members" :key="mi" class="member-chip">
            {{ member }}
            <button v-if="store.isAdmin" class="chip-x" @click="doRemoveMember(team.id, mi)">&times;</button>
          </span>
        </div>
        <div class="form-row" v-if="store.isAdmin">
          <div class="field">
            <label>Add Member</label>
            <input v-model="newMember[team.id]" placeholder="Player name" @keyup.enter="doAddMember(team.id)" />
          </div>
          <button class="btn btn-sm" @click="doAddMember(team.id)">Add</button>
        </div>
      </div>

      <div class="empty-state" v-if="!evt.teams.length">
        <p>No teams registered yet.</p>
      </div>
    </div>

    <!-- PARTICIPANTS TAB (individual sports) -->
    <div v-if="tab === 'participants' && evt.type === 'individual'">
      <div class="card" v-if="store.isAdmin">
        <h3>Add Participant</h3>
        <div class="form-row">
          <div class="field">
            <label>Name</label>
            <input v-model="newPart.name" placeholder="Participant name" @keyup.enter="doAddParticipant" />
          </div>
          <div class="field">
            <label>Department</label>
            <input v-model="newPart.department" placeholder="e.g. CSE" style="width:100px" @keyup.enter="doAddParticipant" />
          </div>
          <div class="field">
            <label>Contact</label>
            <input v-model="newPart.contact" placeholder="Phone/Email" @keyup.enter="doAddParticipant" />
          </div>
          <button class="btn btn-primary" @click="doAddParticipant">Add</button>
        </div>
      </div>

      <div class="card" v-if="evt.participants.length">
        <table class="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Name</th>
              <th>Department</th>
              <th>Contact</th>
              <th v-if="store.isAdmin" style="width:60px"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(p, i) in evt.participants" :key="p.id">
              <td class="num">{{ i + 1 }}</td>
              <td class="team-name">{{ p.name }}</td>
              <td>{{ p.department }}</td>
              <td class="text-dim">{{ p.contact || '-' }}</td>
              <td v-if="store.isAdmin">
                <button class="btn btn-sm btn-danger" @click="doRemoveParticipant(p.id)">X</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="empty-state" v-if="!evt.participants.length">
        <p>No participants registered yet.</p>
      </div>
    </div>

    <!-- SCHEDULE TAB -->
    <div v-if="tab === 'schedule'">
      <div class="card" v-if="store.isAdmin">
        <h3>Add Schedule Entry</h3>
        <div class="form-row">
          <div class="field">
            <label>Title</label>
            <input v-model="newSch.title" placeholder="e.g. Semi-finals" />
          </div>
          <div class="field">
            <label>Date</label>
            <input v-model="newSch.date" type="date" />
          </div>
          <div class="field">
            <label>Time</label>
            <input v-model="newSch.time" type="time" style="width:120px" />
          </div>
          <div class="field">
            <label>Venue</label>
            <input v-model="newSch.venue" :placeholder="evt.venue || 'Venue'" />
          </div>
          <button class="btn btn-primary" @click="doAddSchedule">Add</button>
        </div>
        <div class="form-row">
          <div class="field" style="flex:1">
            <label>Description</label>
            <input v-model="newSch.description" placeholder="Optional details" style="width:100%" />
          </div>
        </div>
      </div>

      <table class="schedule-table" v-if="sortedSchedule.length">
        <thead><tr><th>Date</th><th>Time</th><th>Match</th><th>Venue</th><th>Result</th><th>Status</th></tr></thead>
        <tbody>
          <tr v-for="sch in sortedSchedule" :key="sch.id">
            <td class="text-dim" style="white-space:nowrap">{{ sch.date }}</td>
            <td class="text-dim" style="white-space:nowrap">{{ sch.time || '—' }}</td>
            <td><strong>{{ sch.title }}</strong></td>
            <td class="text-dim">{{ sch.venue || '' }}</td>
            <td class="text-sm">{{ sch.description || '' }}</td>
            <td>
              <span class="badge" :class="sch.status === 'completed' ? 'badge-green' : sch.status === 'cancelled' ? 'badge-red' : 'badge-upcoming'">
                {{ sch.status }}
              </span>
              <template v-if="store.isAdmin">
                <select v-model="sch.status" class="btn btn-sm" style="width:auto;cursor:pointer;padding:3px 6px;font-size:11px;margin-left:4px" @change="flashSaved">
                  <option value="scheduled">Scheduled</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
                <button class="btn btn-sm btn-danger" @click="doRemoveSchedule(sch.id)" style="margin-left:4px">X</button>
              </template>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="empty-state" v-if="!evt.schedule.length">
        <p>No schedule entries yet.</p>
      </div>
    </div>

    <!-- NOTES TAB -->
    <div v-if="tab === 'notes'">
      <div class="card" v-if="store.isAdmin">
        <h3>Add Note</h3>
        <div class="form-row">
          <div class="field" style="flex:1">
            <label>Note</label>
            <input v-model="newNote" placeholder="Quick note..." style="width:100%" @keyup.enter="doAddNote" />
          </div>
          <button class="btn btn-primary" @click="doAddNote">Add</button>
        </div>
      </div>

      <div class="card" v-for="note in sortedNotes" :key="note.id">
        <div class="flex justify-between items-center">
          <div style="flex:1">
            <p>{{ note.text }}</p>
            <div class="text-sm text-dim" style="margin-top:4px">{{ formatDate(note.createdAt) }}</div>
          </div>
          <button v-if="store.isAdmin" class="btn btn-sm btn-danger" @click="doRemoveNote(note.id)">X</button>
        </div>
      </div>

      <div class="empty-state" v-if="!evt.notes.length">
        <p>No notes yet.</p>
      </div>
    </div>

    <!-- STANDINGS TAB -->
    <div v-if="tab === 'standings'">
      <!-- Podium results (individual events) -->
      <div v-if="evt.podium && evt.podium.length" class="podium-list">
        <div v-for="cat in evt.podium" :key="cat.category" class="card podium-card">
          <h3>{{ cat.category }}</h3>
          <div class="podium-rows">
            <div class="podium-row podium-1">
              <span class="podium-rank">1st</span>
              <span class="podium-name">{{ cat.first }}</span>
            </div>
            <div class="podium-row podium-2">
              <span class="podium-rank">2nd</span>
              <span class="podium-name">{{ cat.second }}</span>
            </div>
            <div class="podium-row podium-3">
              <span class="podium-rank">3rd</span>
              <span class="podium-name">{{ cat.third }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Pool/Group Standings Tables -->
      <div v-if="evt.standings && evt.standings.length" class="standings-pools">
        <div v-for="pool in evt.standings" :key="pool.pool" class="card standings-pool-card">
          <h3>{{ pool.pool }}</h3>
          <table class="data-table standings-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Team</th>
                <th>P</th>
                <th>W</th>
                <th>D</th>
                <th>L</th>
                <th>Pts</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in pool.table" :key="row.team">
                <td class="num">{{ i + 1 }}</td>
                <td class="team-name">{{ row.team }}</td>
                <td class="num">{{ row.p }}</td>
                <td class="num">{{ row.w }}</td>
                <td class="num">{{ row.d }}</td>
                <td class="num">{{ row.l }}</td>
                <td class="num" style="font-weight:700">{{ row.pts }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- BRACKET (inside standings or standalone) -->
    <div v-if="tab === 'standings'">
      <!-- Generate / Reset controls -->
      <div class="card" v-if="store.isAdmin">
        <div class="flex justify-between items-center">
          <div>
            <h3 style="margin-bottom:4px">Knockout Bracket</h3>
            <p class="text-dim text-sm" v-if="!evt.bracket?.generated">
              Generate a single-elimination bracket from {{ evt.type === 'team' ? evt.teams.length + ' teams' : evt.participants.length + ' participants' }}
            </p>
          </div>
          <div class="flex gap-8">
            <button v-if="!evt.bracket?.generated" class="btn btn-primary" :disabled="seedCount < 2" @click="doGenerateBracket">
              Generate Bracket
            </button>
            <template v-else>
              <button class="btn btn-danger" @click="doResetBracket">Reset Bracket</button>
            </template>
          </div>
        </div>
        <p v-if="seedCount < 2" class="text-dim text-sm" style="margin-top:8px">
          Need at least 2 {{ evt.type === 'team' ? 'teams' : 'participants' }} to generate a bracket.
        </p>
        <p v-if="evt.bracket?.generated && store.isAdmin" class="text-dim text-sm" style="margin-top:8px">
          Click on a team/player name to mark them as the winner of that match.
        </p>
      </div>

      <!-- Bracket tree -->
      <div v-if="evt.bracket?.generated" class="bracket-container card">
        <div class="bracket">
          <div v-for="(round, ri) in bracketRounds" :key="ri" class="bracket-round">
            <div class="bracket-round-title">{{ roundLabel(ri, bracketRounds.length) }}</div>
            <div class="bracket-round-matches" :style="{ gap: (24 * Math.pow(2, ri)) + 'px' }">
              <div v-for="match in round" :key="match.id" class="bracket-match" :class="{ decided: match.winnerId }">
                <div
                  v-for="(slot, si) in match.slots"
                  :key="si"
                  class="bracket-team"
                  :class="{
                    winner: match.winnerId && match.winnerId === slot.seedId,
                    loser: match.winnerId && match.winnerId !== slot.seedId,
                    clickable: store.isAdmin && slot.seedId && !slot.seedId?.startsWith?.('bye') && bothSlotsFilled(match),
                    bye: !slot.seedId
                  }"
                  @click="store.isAdmin && slot.seedId && bothSlotsFilled(match) && doSetWinner(match.id, slot.seedId)"
                >
                  <span class="bracket-team-name">{{ slot.name }}</span>
                  <span v-if="match.winnerId && match.winnerId === slot.seedId" class="bracket-winner-mark">&#10003;</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Champion -->
          <div v-if="champion" class="bracket-champion">
            <div style="font-size:40px;margin-bottom:4px">&#127942;</div>
            <div class="bracket-champion-name">{{ champion }}</div>
            <div class="text-dim text-sm">Champion</div>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div class="empty-state" v-if="!evt.bracket?.generated && !store.isAdmin && (!evt.standings || !evt.standings.length) && (!evt.podium || !evt.podium.length)">
        <p>Standings not yet available.</p>
      </div>
    </div>
  </div>

  <div v-else class="empty-state">
    <div class="icon">&#128533;</div>
    <p>Event not found.</p>
    <router-link to="/" class="btn" style="margin-top:12px">Back to Events</router-link>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import {
  store, getEvent,
  addTeam, removeTeam, addTeamMember, removeTeamMember,
  addParticipant, removeParticipant,
  addScheduleItem, removeScheduleItem,
  addNote, removeNote,
  togglePinEvent, isEventPinned,
  generateBracket, setMatchWinner, clearBracket,
} from '../stores/tournament.js'
import { getRules } from '../data/rules.js'
import { renderMarkdown } from '../utils/markdown.js'
import posterFiles from '../data/posters.json'

const props = defineProps({ id: String })
const evt = computed(() => getEvent(props.id))
const isPinned = computed(() => isEventPinned(props.id))
const tab = ref('info')

const eventRules = computed(() => getRules(props.id))
const renderedRules = computed(() => eventRules.value ? renderMarkdown(eventRules.value) : '')

const eventPoster = computed(() => {
  const slug = props.id.replace('evt-', '').replace(/-/g, '')
  const match = posterFiles.find(f => {
    const name = f.replace(/\.[^.]+$/, '').toLowerCase()
    return name === slug || name === props.id.replace('evt-', '')
  })
  return match ? `posters/${match}` : null
})

function formatToHtml(text) {
  if (!text) return ''
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n/g, '<br>')
}
const dirty = ref(false)
let saveTimer = null

function flashSaved() {
  dirty.value = true
  clearTimeout(saveTimer)
  saveTimer = setTimeout(() => {
    dirty.value = false
  }, 1500)
}

const nextScheduleItem = computed(() => {
  if (!evt.value) return null
  const upcoming = evt.value.schedule
    .filter(s => s.status === 'scheduled')
    .sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time))
  return upcoming[0] || null
})

const latestNote = computed(() => {
  if (!evt.value?.notes.length) return ''
  const sorted = [...evt.value.notes].sort((a, b) => b.createdAt.localeCompare(a.createdAt))
  return sorted[0].text
})

// -- Teams --
const newTeam = reactive({ name: '' })
const newMember = reactive({})

function doAddTeam() {
  if (!newTeam.name.trim()) return
  addTeam(props.id, { name: newTeam.name.trim() })
  newTeam.name = ''
  flashSaved()
}
function doRemoveTeam(teamId) {
  if (confirm('Remove this team?')) { removeTeam(props.id, teamId); flashSaved() }
}
function doAddMember(teamId) {
  const name = (newMember[teamId] || '').trim()
  if (!name) return
  addTeamMember(props.id, teamId, name)
  newMember[teamId] = ''
  flashSaved()
}
function doRemoveMember(teamId, index) {
  removeTeamMember(props.id, teamId, index)
  flashSaved()
}

// -- Participants --
const newPart = reactive({ name: '', department: '', contact: '' })

function doAddParticipant() {
  if (!newPart.name.trim()) return
  addParticipant(props.id, { name: newPart.name.trim(), department: newPart.department.trim(), contact: newPart.contact.trim() })
  newPart.name = ''
  newPart.department = ''
  newPart.contact = ''
  flashSaved()
}
function doRemoveParticipant(partId) {
  removeParticipant(props.id, partId)
  flashSaved()
}

// -- Schedule --
const newSch = reactive({ title: '', date: '', time: '', venue: '', description: '' })
const sortedSchedule = computed(() =>
  [...(evt.value?.schedule || [])].sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time))
)

function doAddSchedule() {
  if (!newSch.title.trim() || !newSch.date) return
  addScheduleItem(props.id, { ...newSch, venue: newSch.venue || evt.value?.venue || '' })
  newSch.title = ''
  newSch.date = ''
  newSch.time = ''
  newSch.venue = ''
  newSch.description = ''
  flashSaved()
}
function doRemoveSchedule(schId) {
  removeScheduleItem(props.id, schId)
  flashSaved()
}

// -- Notes --
const newNote = ref('')
const sortedNotes = computed(() =>
  [...(evt.value?.notes || [])].sort((a, b) => b.createdAt.localeCompare(a.createdAt))
)

function doAddNote() {
  if (!newNote.value.trim()) return
  addNote(props.id, newNote.value.trim())
  newNote.value = ''
  flashSaved()
}
function doRemoveNote(noteId) {
  removeNote(props.id, noteId)
  flashSaved()
}

function formatDate(iso) {
  return new Date(iso).toLocaleString()
}

function statusBadge(status) {
  if (status === 'completed') return 'badge-green'
  if (status === 'ongoing') return 'badge-ongoing'
  return 'badge-upcoming'
}

// -- Bracket --
const seedCount = computed(() => {
  if (!evt.value) return 0
  return evt.value.type === 'team' ? evt.value.teams.length : evt.value.participants.length
})

const bracketRounds = computed(() => {
  if (!evt.value?.bracket?.matches?.length) return []
  const maxRound = Math.max(...evt.value.bracket.matches.map(m => m.round))
  const rounds = []
  for (let r = 0; r <= maxRound; r++) {
    rounds.push(
      evt.value.bracket.matches
        .filter(m => m.round === r)
        .sort((a, b) => a.position - b.position)
    )
  }
  return rounds
})

const champion = computed(() => {
  if (!bracketRounds.value.length) return null
  const finalRound = bracketRounds.value[bracketRounds.value.length - 1]
  if (finalRound.length !== 1) return null
  const finalMatch = finalRound[0]
  if (!finalMatch.winnerId) return null
  const winner = finalMatch.slots.find(s => s.seedId === finalMatch.winnerId)
  return winner?.name || null
})

function roundLabel(ri, totalRounds) {
  const fromEnd = totalRounds - 1 - ri
  if (fromEnd === 0) return 'Final'
  if (fromEnd === 1) return 'Semi-finals'
  if (fromEnd === 2) return 'Quarter-finals'
  const matchesInRound = Math.pow(2, totalRounds - 1 - ri)
  return 'Round of ' + (matchesInRound * 2)
}

function bothSlotsFilled(match) {
  return match.slots[0].seedId && match.slots[1].seedId
}

function doGenerateBracket() {
  generateBracket(props.id)
  flashSaved()
}

function doResetBracket() {
  if (confirm('Reset the bracket? All match results will be lost.')) {
    clearBracket(props.id)
    flashSaved()
  }
}

function doSetWinner(matchId, seedId) {
  setMatchWinner(props.id, matchId, seedId)
  flashSaved()
}
</script>
