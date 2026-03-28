/**
 * Minimal markdown-to-HTML renderer for rules content.
 * Handles: headers, bold, italic, lists, tables, links, horizontal rules, paragraphs.
 */
export function renderMarkdown(md) {
  if (!md) return ''

  const lines = md.split('\n')
  const html = []
  let inList = false
  let listType = ''
  let inTable = false
  let tableRows = []

  function flushTable() {
    if (!inTable) return
    inTable = false
    if (tableRows.length < 2) return
    const headers = tableRows[0]
    const rows = tableRows.slice(2) // skip separator row
    let t = '<table class="rules-table"><thead><tr>'
    headers.forEach(h => { t += `<th>${inline(h.trim())}</th>` })
    t += '</tr></thead><tbody>'
    rows.forEach(row => {
      t += '<tr>'
      row.forEach(cell => { t += `<td>${inline(cell.trim())}</td>` })
      t += '</tr>'
    })
    t += '</tbody></table>'
    html.push(t)
    tableRows = []
  }

  function flushList() {
    if (!inList) return
    html.push(listType === 'ol' ? '</ol>' : '</ul>')
    inList = false
    listType = ''
  }

  function inline(text) {
    return text
      .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="rules-img" />')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/`(.+?)`/g, '<code>$1</code>')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]

    // Table row
    if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
      flushList()
      if (!inTable) inTable = true
      const cells = line.trim().slice(1, -1).split('|')
      tableRows.push(cells)
      continue
    } else {
      flushTable()
    }

    // Empty line
    if (!line.trim()) {
      flushList()
      continue
    }

    // Headers
    const headerMatch = line.match(/^(#{1,4})\s+(.+)/)
    if (headerMatch) {
      flushList()
      const level = headerMatch[1].length
      html.push(`<h${level}>${inline(headerMatch[2])}</h${level}>`)
      continue
    }

    // Horizontal rule
    if (/^---+$/.test(line.trim())) {
      flushList()
      html.push('<hr>')
      continue
    }

    // Unordered list
    const ulMatch = line.match(/^(\s*)[-*]\s+(.+)/)
    if (ulMatch) {
      if (!inList || listType !== 'ul') {
        flushList()
        html.push('<ul>')
        inList = true
        listType = 'ul'
      }
      html.push(`<li>${inline(ulMatch[2])}</li>`)
      continue
    }

    // Ordered list
    const olMatch = line.match(/^(\s*)\d+\.\s+(.+)/)
    if (olMatch) {
      if (!inList || listType !== 'ol') {
        flushList()
        html.push('<ol>')
        inList = true
        listType = 'ol'
      }
      html.push(`<li>${inline(olMatch[2])}</li>`)
      continue
    }

    // Paragraph
    flushList()
    html.push(`<p>${inline(line)}</p>`)
  }

  flushList()
  flushTable()

  return html.join('\n')
}
