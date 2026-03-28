import rules from './rules-data.json'

export { rules }

export function getRules(eventId) {
  return rules[eventId] || null
}
