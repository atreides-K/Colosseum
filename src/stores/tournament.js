import { reactive, watch } from 'vue'
import defaultData from '../data/default-data.json'

const STORAGE_KEY = 'spectrum-tournament-data'

function loadData() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch (e) {
    console.warn('Failed to load saved data', e)
  }
  return null
}

function uid(prefix = 'id') {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`
}

// ---- SPORTS CONFIG ----
export const SPORTS = defaultData.events.map(e => ({ sport: e.sport, icon: e.icon, type: e.type }))

function defaultState() {
  return JSON.parse(JSON.stringify(defaultData))
}

// Always start fresh from default data (localStorage disabled for now)
localStorage.removeItem(STORAGE_KEY)
export const store = reactive(defaultState())

// Migrate old football-only data
if (store.teams && !store.events) {
  Object.assign(store, defaultState())
}

// Migrate: ensure all events have required operational fields + new info fields
if (store.events) {
  const defaults = defaultState()
  store.events.forEach(evt => {
    // Ensure operational arrays/objects exist
    if (!evt.teams) evt.teams = []
    if (!evt.participants) evt.participants = []
    if (!evt.volunteers) evt.volunteers = []
    if (!evt.schedule) evt.schedule = []
    if (!evt.notes) evt.notes = []
    if (!evt.bracket) evt.bracket = { generated: false, matches: [] }
    if (!evt.logistics) evt.logistics = { venue: evt.venue || 'TBA', equipment: '', notes: '' }
    // Migrate venue: top-level takes precedence
    if (evt.venue === undefined) evt.venue = evt.logistics?.venue || 'TBA'

    // Copy new info fields from defaults
    const defEvt = defaults.events.find(d => d.id === evt.id)
    if (defEvt) {
      for (const key of ['categories', 'teamSize', 'guestPlayers', 'format', 'registrationLink', 'registrationDeadline', 'whatsappLink', 'contacts', 'hasRules', 'registrationLinkWomens', 'venue']) {
        if (evt[key] === undefined && defEvt[key] !== undefined) {
          evt[key] = defEvt[key]
        }
      }
    }
  })
  // Add new events that don't exist yet (e.g. Kabaddi)
  defaults.events.forEach(defEvt => {
    if (!store.events.find(e => e.id === defEvt.id)) {
      store.events.push(JSON.parse(JSON.stringify(defEvt)))
    }
  })
}

// localStorage persistence disabled for now
// watch(
//   () => JSON.parse(JSON.stringify(store)),
//   (val) => {
//     localStorage.setItem(STORAGE_KEY, JSON.stringify(val))
//   },
//   { deep: true }
// )

// ---- CRUD helpers ----

export function resetData() {
  // Clear old key too
  localStorage.removeItem('football-tournament-data')
  Object.assign(store, defaultState())
}

export function getEvent(id) {
  return store.events.find((e) => e.id === id)
}

// -- Teams --
export function addTeam(eventId, team) {
  const evt = getEvent(eventId)
  if (!evt) return
  const id = uid('team')
  evt.teams.push({ id, name: team.name, members: team.members || [] })
  return id
}

export function removeTeam(eventId, teamId) {
  const evt = getEvent(eventId)
  if (!evt) return
  evt.teams = evt.teams.filter((t) => t.id !== teamId)
}

export function addTeamMember(eventId, teamId, memberName) {
  const evt = getEvent(eventId)
  if (!evt) return
  const team = evt.teams.find((t) => t.id === teamId)
  if (team) team.members.push(memberName)
}

export function removeTeamMember(eventId, teamId, index) {
  const evt = getEvent(eventId)
  if (!evt) return
  const team = evt.teams.find((t) => t.id === teamId)
  if (team) team.members.splice(index, 1)
}

// -- Participants --
export function addParticipant(eventId, participant) {
  const evt = getEvent(eventId)
  if (!evt) return
  const id = uid('part')
  evt.participants.push({ id, name: participant.name, department: participant.department || '', contact: participant.contact || '' })
  return id
}

export function removeParticipant(eventId, partId) {
  const evt = getEvent(eventId)
  if (!evt) return
  evt.participants = evt.participants.filter((p) => p.id !== partId)
}

// -- Volunteers --
export function addVolunteer(eventId, vol) {
  const evt = getEvent(eventId)
  if (!evt) return
  const id = uid('vol')
  evt.volunteers.push({ id, name: vol.name, role: vol.role || '', contact: vol.contact || '' })
  return id
}

export function removeVolunteer(eventId, volId) {
  const evt = getEvent(eventId)
  if (!evt) return
  evt.volunteers = evt.volunteers.filter((v) => v.id !== volId)
}

// -- Schedule --
export function addScheduleItem(eventId, item) {
  const evt = getEvent(eventId)
  if (!evt) return
  const id = uid('sch')
  evt.schedule.push({
    id, title: item.title, date: item.date, time: item.time || '',
    venue: item.venue || '', description: item.description || '', status: item.status || 'scheduled',
  })
  return id
}

export function removeScheduleItem(eventId, schId) {
  const evt = getEvent(eventId)
  if (!evt) return
  evt.schedule = evt.schedule.filter((s) => s.id !== schId)
}

// -- Notes --
export function addNote(eventId, text) {
  const evt = getEvent(eventId)
  if (!evt) return
  const id = uid('note')
  evt.notes.push({ id, text, createdAt: new Date().toISOString() })
  return id
}

export function removeNote(eventId, noteId) {
  const evt = getEvent(eventId)
  if (!evt) return
  evt.notes = evt.notes.filter((n) => n.id !== noteId)
}

// -- Event status --
export function setEventStatus(eventId, status) {
  const evt = getEvent(eventId)
  if (evt) evt.status = status
}

// -- Export / Import --
export function exportData() {
  const blob = new Blob([JSON.stringify(store, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${store.tournamentName.replace(/\s+/g, '_')}_data.json`
  a.click()
  URL.revokeObjectURL(url)
}

export function importData(jsonStr) {
  try {
    const data = JSON.parse(jsonStr)
    Object.assign(store, data)
    return true
  } catch {
    return false
  }
}

// -- Announcements --
export function addAnnouncement(text, pinned = false) {
  const id = uid('ann')
  if (!store.announcements) store.announcements = []
  store.announcements.push({ id, text, pinned, createdAt: new Date().toISOString() })
  return id
}

export function removeAnnouncement(annId) {
  store.announcements = store.announcements.filter((a) => a.id !== annId)
}

export function toggleAnnouncementPin(annId) {
  const ann = store.announcements.find((a) => a.id === annId)
  if (ann) ann.pinned = !ann.pinned
}

// -- Pinned Events (persisted separately in localStorage) --
const PINNED_KEY = 'spectrum-pinned-events'
try {
  const saved = localStorage.getItem(PINNED_KEY)
  if (saved) store.pinnedEvents = JSON.parse(saved)
} catch (e) { /* ignore */ }

export function togglePinEvent(eventId) {
  if (!store.pinnedEvents) store.pinnedEvents = []
  const idx = store.pinnedEvents.indexOf(eventId)
  if (idx >= 0) store.pinnedEvents.splice(idx, 1)
  else store.pinnedEvents.push(eventId)
  localStorage.setItem(PINNED_KEY, JSON.stringify(store.pinnedEvents))
}

export function isEventPinned(eventId) {
  return (store.pinnedEvents || []).includes(eventId)
}

// -- Bracket --
export function generateBracket(eventId) {
  const evt = getEvent(eventId)
  if (!evt) return

  // Gather seeds from teams or participants
  const seeds = evt.type === 'team'
    ? evt.teams.map(t => ({ id: t.id, name: t.name }))
    : evt.participants.map(p => ({ id: p.id, name: p.name }))

  if (seeds.length < 2) return

  // Shuffle seeds
  for (let i = seeds.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [seeds[i], seeds[j]] = [seeds[j], seeds[i]]
  }

  // Pad to next power of 2 with BYEs
  const totalSlots = Math.pow(2, Math.ceil(Math.log2(seeds.length)))
  while (seeds.length < totalSlots) seeds.push({ id: null, name: 'BYE' })

  const totalRounds = Math.log2(totalSlots)
  const matches = []

  // Create round 0 matches
  for (let i = 0; i < totalSlots / 2; i++) {
    matches.push({
      id: uid('bm'),
      round: 0,
      position: i,
      slots: [
        { seedId: seeds[i * 2].id, name: seeds[i * 2].name, score: null },
        { seedId: seeds[i * 2 + 1].id, name: seeds[i * 2 + 1].name, score: null },
      ],
      winnerId: null,
    })
  }

  // Create empty matches for later rounds
  for (let r = 1; r < totalRounds; r++) {
    const matchCount = totalSlots / Math.pow(2, r + 1)
    for (let p = 0; p < matchCount; p++) {
      matches.push({
        id: uid('bm'),
        round: r,
        position: p,
        slots: [
          { seedId: null, name: 'TBD', score: null },
          { seedId: null, name: 'TBD', score: null },
        ],
        winnerId: null,
      })
    }
  }

  // Auto-advance BYE matches in round 0
  matches.filter(m => m.round === 0).forEach(m => {
    const bye = m.slots.findIndex(s => s.seedId === null)
    if (bye !== -1) {
      const winner = m.slots[bye === 0 ? 1 : 0]
      m.winnerId = winner.seedId
      advanceWinner(matches, m, winner)
    }
  })

  evt.bracket = { generated: true, matches }
}

function advanceWinner(matches, match, winner) {
  const totalRounds = Math.max(...matches.map(m => m.round)) + 1
  if (match.round + 1 >= totalRounds) return
  const nextMatch = matches.find(m => m.round === match.round + 1 && m.position === Math.floor(match.position / 2))
  if (!nextMatch) return
  const slotIdx = match.position % 2
  nextMatch.slots[slotIdx] = { seedId: winner.seedId, name: winner.name, score: null }
}

function clearDownstream(matches, fromRound, seedId) {
  const totalRounds = Math.max(...matches.map(m => m.round)) + 1
  for (let r = fromRound; r < totalRounds; r++) {
    matches.filter(m => m.round === r).forEach(m => {
      const idx = m.slots.findIndex(s => s.seedId === seedId)
      if (idx !== -1) {
        if (m.winnerId === seedId) {
          clearDownstream(matches, r + 1, seedId)
          m.winnerId = null
        }
        m.slots[idx] = { seedId: null, name: 'TBD', score: null }
      }
    })
  }
}

export function setMatchWinner(eventId, matchId, winnerId) {
  const evt = getEvent(eventId)
  if (!evt?.bracket) return
  const match = evt.bracket.matches.find(m => m.id === matchId)
  if (!match) return
  const winner = match.slots.find(s => s.seedId === winnerId)
  if (!winner) return

  // If changing winner, clear old downstream
  if (match.winnerId && match.winnerId !== winnerId) {
    clearDownstream(evt.bracket.matches, match.round + 1, match.winnerId)
  }

  match.winnerId = winnerId
  advanceWinner(evt.bracket.matches, match, winner)
}

export function clearBracket(eventId) {
  const evt = getEvent(eventId)
  if (!evt) return
  evt.bracket = { generated: false, matches: [] }
}

// -- Stats --
export function totalParticipants() {
  return store.events.reduce((sum, evt) => {
    if (evt.type === 'team') {
      return sum + evt.teams.reduce((s, t) => s + t.members.length, 0)
    }
    return sum + evt.participants.length
  }, 0)
}

export function totalVolunteers() {
  const unique = new Set()
  store.events.forEach((evt) => evt.volunteers.forEach((v) => unique.add(v.name)))
  return unique.size
}
