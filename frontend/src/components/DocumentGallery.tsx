import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { FitPreviewFrame } from './FitPreviewFrame'
import { previewUrl, type PreviewFile } from '../api'

type Props = {
  files: PreviewFile[]
  selected: Set<string>
  onToggle: (filename: string) => void
  onOpenPreview: (index: number) => void
}

function LazyThumbnail({
  file,
  selected,
  onToggle,
  onOpen,
}: {
  file: PreviewFile
  selected: boolean
  onToggle: () => void
  onOpen: () => void
}) {
  const ref = useRef<HTMLDivElement>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
          io.disconnect()
        }
      },
      { rootMargin: '120px' },
    )
    io.observe(el)
    return () => io.disconnect()
  }, [])

  return (
    <div
      ref={ref}
      className={`doc-gallery-item${selected ? ' doc-gallery-item-selected' : ''}`}
    >
      <button
        type="button"
        className={`doc-gallery-check${selected ? ' doc-gallery-check-on' : ''}`}
        aria-label={selected ? '取消选择' : '选择'}
        onClick={(e) => {
          e.stopPropagation()
          onToggle()
        }}
      >
        {selected ? '✓' : ''}
      </button>
      <button type="button" className="doc-gallery-thumb" onClick={onOpen}>
        {visible ? (
          <FitPreviewFrame
            src={previewUrl(file.filename)}
            title={file.display_name}
            className="doc-gallery-frame"
          />
        ) : (
          <div className="doc-gallery-placeholder">
            <span className="doc-gallery-placeholder-icon">📄</span>
          </div>
        )}
      </button>
      <div className="doc-gallery-caption" title={file.filename}>
        {file.display_name}
      </div>
    </div>
  )
}

export default function DocumentGallery({ files, selected, onToggle, onOpenPreview }: Props) {
  const categories = useMemo(() => {
    const cats = [...new Set(files.map((f) => f.category))].sort()
    return ['全部', ...cats]
  }, [files])

  const [category, setCategory] = useState('全部')

  const filtered = useMemo(
    () => (category === '全部' ? files : files.filter((f) => f.category === category)),
    [files, category],
  )

  const indexByFilename = useMemo(() => {
    const map = new Map<string, number>()
    files.forEach((f, i) => map.set(f.filename, i))
    return map
  }, [files])

  const handleOpen = useCallback(
    (file: PreviewFile) => {
      const idx = indexByFilename.get(file.filename)
      if (idx !== undefined) onOpenPreview(idx)
    },
    [indexByFilename, onOpenPreview],
  )

  if (files.length === 0) {
    return <p className="hint">暂无可预览的文件</p>
  }

  return (
    <div className="doc-gallery">
      <div className="doc-gallery-filters">
        {categories.map((cat) => (
          <button
            key={cat}
            type="button"
            className={`doc-gallery-filter${category === cat ? ' doc-gallery-filter-active' : ''}`}
            onClick={() => setCategory(cat)}
          >
            {cat}
            {cat !== '全部' && (
              <span className="count-badge">{files.filter((f) => f.category === cat).length}</span>
            )}
          </button>
        ))}
      </div>
      <div className="doc-gallery-grid">
        {filtered.map((file) => (
          <LazyThumbnail
            key={file.filename}
            file={file}
            selected={selected.has(file.filename)}
            onToggle={() => onToggle(file.filename)}
            onOpen={() => handleOpen(file)}
          />
        ))}
      </div>
    </div>
  )
}

export function DocumentLightbox({
  files,
  index,
  onClose,
  onPrev,
  onNext,
}: {
  files: PreviewFile[]
  index: number
  onClose: () => void
  onPrev: () => void
  onNext: () => void
}) {
  const file = files[index]

  useEffect(() => {
    if (!file) return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
      if (e.key === 'ArrowLeft') onPrev()
      if (e.key === 'ArrowRight') onNext()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [file, onClose, onPrev, onNext])

  if (!file) return null

  return (
    <div className="doc-lightbox" role="dialog" aria-modal="true" aria-label="文档预览">
      <header className="doc-lightbox-toolbar">
        <span className="doc-lightbox-title">
          {file.display_name}
          <span className="doc-lightbox-counter">
            {index + 1} / {files.length}
          </span>
        </span>
        <div className="doc-lightbox-actions">
          <button type="button" className="btn-secondary" onClick={onPrev} disabled={index <= 0}>
            ← 上一份
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={onNext}
            disabled={index >= files.length - 1}
          >
            下一份 →
          </button>
          <button type="button" className="btn-secondary" onClick={onClose}>
            关闭
          </button>
        </div>
      </header>
      <div className="doc-lightbox-body">
        <FitPreviewFrame src={previewUrl(file.filename)} title={file.display_name} />
      </div>
    </div>
  )
}
