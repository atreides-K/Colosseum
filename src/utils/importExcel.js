import * as XLSX from 'xlsx'

/**
 * Parse an Excel or CSV file and return rows as objects.
 * Accepts a File object (from <input type="file">).
 */
export function parseSpreadsheet(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target.result)
        const wb = XLSX.read(data, { type: 'array' })
        const sheets = {}
        wb.SheetNames.forEach((name) => {
          sheets[name] = XLSX.utils.sheet_to_json(wb.Sheets[name], { defval: '' })
        })
        resolve(sheets)
      } catch (err) {
        reject(err)
      }
    }
    reader.onerror = reject
    reader.readAsArrayBuffer(file)
  })
}

/**
 * Expected sheet formats:
 *
 * "Teams" sheet:   name, group
 * "Players" sheet: name, team, number, position
 * "Matches" sheet: home, away, homeGoals, awayGoals, stage
 *
 * Returns { teams, players, matches } ready to merge into store.
 */
export function normalizeImport(sheets) {
  const result = { teams: [], players: [], matches: [] }

  // teams
  const teamsSheet = sheets['Teams'] || sheets['teams'] || Object.values(sheets)[0] || []
  const teamNameMap = {}
  teamsSheet.forEach((row) => {
    const name = (row.name || row.Name || row.team || row.Team || '').toString().trim()
    if (!name) return
    const id = `team-${name.toLowerCase().replace(/\s+/g, '-')}`
    teamNameMap[name.toLowerCase()] = id
    result.teams.push({ id, name, group: (row.group || row.Group || '').toString().trim() })
  })

  // players
  const playersSheet = sheets['Players'] || sheets['players'] || []
  playersSheet.forEach((row) => {
    const name = (row.name || row.Name || '').toString().trim()
    const teamName = (row.team || row.Team || '').toString().trim()
    if (!name) return
    const teamId = teamNameMap[teamName.toLowerCase()] || ''
    result.players.push({
      id: `player-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      name,
      teamId,
      number: (row.number || row.Number || row['#'] || '').toString(),
      position: (row.position || row.Position || row.pos || row.Pos || '').toString(),
    })
  })

  // matches
  const matchesSheet = sheets['Matches'] || sheets['matches'] || []
  matchesSheet.forEach((row) => {
    const homeName = (row.home || row.Home || '').toString().trim()
    const awayName = (row.away || row.Away || '').toString().trim()
    if (!homeName || !awayName) return
    const homeId = teamNameMap[homeName.toLowerCase()] || ''
    const awayId = teamNameMap[awayName.toLowerCase()] || ''
    const hg = row.homeGoals ?? row['Home Goals'] ?? row.home_goals ?? null
    const ag = row.awayGoals ?? row['Away Goals'] ?? row.away_goals ?? null
    const played = hg !== null && hg !== '' && ag !== null && ag !== ''
    result.matches.push({
      id: `match-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      homeId,
      awayId,
      homeGoals: played ? Number(hg) : null,
      awayGoals: played ? Number(ag) : null,
      stage: (row.stage || row.Stage || 'group').toString().trim(),
      events: [],
      played,
    })
  })

  return result
}
