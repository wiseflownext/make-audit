import { useCallback, useEffect, useRef, useState } from 'react'

const MM_TO_PX = 96 / 25.4
const A4_PORTRAIT_W_MM = 210
const A4_PORTRAIT_H_MM = 297
const A4_LANDSCAPE_W_MM = 297
const A4_LANDSCAPE_H_MM = 210
const NOTE_EXTRA_PX = 48
/** Room for up to two A4 pages inside the iframe (scroll for page 2). */
const MAX_PAGES = 2

type Props = {
  src: string
  title: string
  className?: string
}

function pageDimensions(landscape: boolean) {
  return landscape
    ? { pageW: A4_LANDSCAPE_W_MM * MM_TO_PX, pageH: A4_LANDSCAPE_H_MM * MM_TO_PX + NOTE_EXTRA_PX }
    : { pageW: A4_PORTRAIT_W_MM * MM_TO_PX, pageH: A4_PORTRAIT_H_MM * MM_TO_PX + NOTE_EXTRA_PX }
}

/** Scales template preview iframe so a full A4 sheet is visible in the panel. */
export function FitPreviewFrame({ src, title, className = '' }: Props) {
  const wrapRef = useRef<HTMLDivElement>(null)
  const [landscape, setLandscape] = useState(false)
  const [layout, setLayout] = useState(() => {
    const { pageW, pageH } = pageDimensions(false)
    return { scale: 1, pageW, pageH: pageH * MAX_PAGES }
  })

  const updateLayout = useCallback((isLandscape: boolean) => {
    const el = wrapRef.current
    if (!el) return

    const { pageW, pageH: singlePageH } = pageDimensions(isLandscape)
    const iframeH = singlePageH * MAX_PAGES

    const cw = el.clientWidth
    const ch = el.clientHeight
    if (cw <= 0 || ch <= 0) return
    const scale = Math.min(cw / pageW, ch / singlePageH, 1)
    setLayout({ scale, pageW, pageH: iframeH })
  }, [])

  useEffect(() => {
    setLandscape(false)
    updateLayout(false)
  }, [src, updateLayout])

  useEffect(() => {
    updateLayout(landscape)
    const el = wrapRef.current
    if (!el) return
    const ro = new ResizeObserver(() => updateLayout(landscape))
    ro.observe(el)
    return () => ro.disconnect()
  }, [landscape, updateLayout])

  const onIframeLoad = useCallback((e: React.SyntheticEvent<HTMLIFrameElement>) => {
    try {
      const doc = e.currentTarget.contentDocument
      const isLandscape = !!doc?.querySelector('meta[name="x-preview-landscape"]')
      setLandscape(isLandscape)
      requestAnimationFrame(() => updateLayout(isLandscape))
    } catch {
      // ignore cross-origin or transient load errors
    }
  }, [updateLayout])

  const { scale, pageW, pageH } = layout
  const visualW = pageW * scale
  const visualH = pageH * scale

  return (
    <div ref={wrapRef} className={`preview-frame-fit-wrap${className ? ` ${className}` : ''}`}>
      <div
        className="preview-frame-fit-inner"
        style={{ width: visualW, height: visualH }}
      >
        <iframe
          src={src}
          title={title}
          className="preview-frame-fit-iframe"
          onLoad={onIframeLoad}
          style={{
            width: pageW,
            height: pageH,
            transform: `scale(${scale})`,
            transformOrigin: 'top left',
          }}
        />
      </div>
    </div>
  )
}
