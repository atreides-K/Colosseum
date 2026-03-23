import { toPng } from 'html-to-image'

/**
 * Capture a DOM element as a PNG and trigger download or share.
 */
export async function captureElement(el, filename = 'colosseum-share.png') {
  const dataUrl = await toPng(el, {
    backgroundColor: '#1a1a2e',
    pixelRatio: 2,
    style: {
      padding: '24px',
    },
  })
  return dataUrl
}

export async function downloadImage(el, filename = 'colosseum-share.png') {
  const dataUrl = await captureElement(el, filename)
  const a = document.createElement('a')
  a.href = dataUrl
  a.download = filename
  a.click()
}

export async function shareImage(el, title = 'Tournament Stats', filename = 'colosseum-share.png') {
  const dataUrl = await captureElement(el, filename)
  const blob = await (await fetch(dataUrl)).blob()
  const file = new File([blob], filename, { type: 'image/png' })

  if (navigator.share && navigator.canShare?.({ files: [file] })) {
    await navigator.share({ title, files: [file] })
  } else {
    // fallback: download
    const a = document.createElement('a')
    a.href = dataUrl
    a.download = filename
    a.click()
  }
}
