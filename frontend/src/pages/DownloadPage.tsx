import { useCallback, useMemo, useState } from 'react'
import DocumentGallery, { DocumentLightbox } from '../components/DocumentGallery'
import { apiFetch, API, type ManifestEntry, type PreviewFile } from '../api'

type ViewMode = 'gallery' | 'list'

function toPreviewFiles(manifest: ManifestEntry[]): PreviewFile[] {
  const seen = new Set<string>()
  const files: PreviewFile[] = []
  for (const e of manifest) {
    if (e.skipped || !e.filename || seen.has(e.filename)) continue
    seen.add(e.filename)
    files.push({
      filename: e.filename,
      category: e.category,
      display_name: e.filename.split('/').pop() || e.filename,
    })
  }
  return files
}

export default function DownloadPage() {
  const [generating, setGenerating] = useState(false)
  const [manifest, setManifest] = useState<ManifestEntry[] | null>(null)
  const [warnings, setWarnings] = useState<ManifestEntry[]>([])
  const [summary, setSummary] = useState<{ total: number; generated: number } | null>(null)
  const [msg, setMsg] = useState('')
  const [downloading, setDownloading] = useState(false)
  const [printing, setPrinting] = useState(false)
  const [viewMode, setViewMode] = useState<ViewMode>('gallery')
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null)

  const previewFiles = useMemo(
    () => (manifest ? toPreviewFiles(manifest) : []),
    [manifest],
  )

  const allSelected =
    previewFiles.length > 0 && previewFiles.every((f) => selected.has(f.filename))
  const someSelected = selected.size > 0

  async function generate() {
    setGenerating(true)
    setMsg('')
    setManifest(null)
    setSelected(new Set())
    setLightboxIndex(null)
    try {
      const res = await apiFetch('/generate/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ years: [], manager_map: {} }),
      })
      const data = await res.json()
      setManifest(data.manifest)
      setSummary({ total: data.total, generated: data.generated })
      setWarnings(data.precheck_warnings || [])
      setMsg(`✓ 生成完成：共 ${data.total} 份，成功 ${data.generated} 份`)
    } catch (e: any) {
      setMsg('✗ ' + e.message)
    }
    setGenerating(false)
  }

  async function downloadZip() {
    setDownloading(true)
    setMsg('⏳ 正在转换 PDF 并打包，请稍候…')
    try {
      const res = await fetch(`${API}/generate/download`)
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || res.statusText)
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      Object.assign(document.createElement('a'), { href: url, download: 'HR审核资料包.zip' }).click()
      URL.revokeObjectURL(url)
      setMsg('✓ ZIP 资料包已下载')
    } catch (e: any) {
      setMsg('✗ 下载失败: ' + e.message)
    }
    setDownloading(false)
  }

  const toggleFile = useCallback((filename: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(filename)) next.delete(filename)
      else next.add(filename)
      return next
    })
  }, [])

  function selectAll() {
    setSelected(new Set(previewFiles.map((f) => f.filename)))
  }

  function clearSelection() {
    setSelected(new Set())
  }

  async function printSelected() {
    if (selected.size === 0) return
    setPrinting(true)
    setMsg('⏳ 正在准备打印，请稍候…')
    try {
      const res = await fetch(`${API}/generate/print`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filenames: [...selected] }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || res.statusText)
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const iframe = document.createElement('iframe')
      iframe.style.position = 'fixed'
      iframe.style.right = '0'
      iframe.style.bottom = '0'
      iframe.style.width = '0'
      iframe.style.height = '0'
      iframe.style.border = 'none'
      iframe.src = url
      document.body.appendChild(iframe)
      await new Promise<void>((resolve, reject) => {
        iframe.onload = () => {
          try {
            iframe.contentWindow?.focus()
            iframe.contentWindow?.print()
            resolve()
          } catch (e) {
            reject(e)
          }
        }
        iframe.onerror = () => reject(new Error('无法加载打印预览'))
      })
      setMsg(`✓ 已发送 ${selected.size} 份文档到打印机`)
      window.setTimeout(() => {
        document.body.removeChild(iframe)
        URL.revokeObjectURL(url)
      }, 60_000)
    } catch (e: any) {
      setMsg('✗ 打印失败: ' + e.message)
    }
    setPrinting(false)
  }

  const byCategory = manifest
    ? manifest.reduce<Record<string, ManifestEntry[]>>((acc, e) => {
        ;(acc[e.category] = acc[e.category] || []).push(e)
        return acc
      }, {})
    : null

  return (
    <div data-testid="page-download" className="page-content page-download">
      <h1 className="page-title">下载资料包</h1>

      <section className="card">
        <h2>生成与下载</h2>
        <div className="row-actions">
          <button onClick={generate} disabled={generating} className="btn-primary">
            {generating ? '⏳ 生成中…' : '▶ 一键生成资料包'}
          </button>
          {manifest && (
            <button onClick={downloadZip} disabled={downloading} className="btn-success">
              {downloading ? '⏳ 转换 PDF 并打包…' : '⬇ 下载 ZIP 资料包'}
            </button>
          )}
        </div>
        {msg && <p className={msg.startsWith('✓') ? 'msg-ok' : 'msg-err'}>{msg}</p>}

        {summary && (
          <div className="summary-chips">
            <span className="chip chip-blue">共 {summary.total} 份</span>
            <span className="chip chip-green">成功 {summary.generated} 份</span>
            {warnings.length > 0 && (
              <span className="chip chip-yellow">⚠ {warnings.length} 项预检警告</span>
            )}
          </div>
        )}
      </section>

      {warnings.length > 0 && (
        <section className="card card-warn">
          <h2>⚠ 预检警告（可继续生成）</h2>
          <ul className="warn-list">
            {warnings.slice(0, 20).map((w, i) => (
              <li key={i}>
                <strong>{w.filename}</strong>
                {w.missing_keys?.length > 0 && (
                  <span className="missing-keys"> 缺失字段: {w.missing_keys.join(', ')}</span>
                )}
                {w.skipped && <span className="skip-reason"> 跳过: {(w as any).skip_reason}</span>}
              </li>
            ))}
          </ul>
        </section>
      )}

      {previewFiles.length > 0 && (
        <section className="card doc-gallery-panel">
          <div className="doc-gallery-header">
            <h2>资料预览</h2>
            <div className="doc-gallery-view-tabs">
              <button
                type="button"
                className={`doc-gallery-view-tab${viewMode === 'gallery' ? ' doc-gallery-view-tab-active' : ''}`}
                onClick={() => setViewMode('gallery')}
              >
                相册
              </button>
              <button
                type="button"
                className={`doc-gallery-view-tab${viewMode === 'list' ? ' doc-gallery-view-tab-active' : ''}`}
                onClick={() => setViewMode('list')}
              >
                清单
              </button>
            </div>
          </div>

          <div className="doc-gallery-toolbar">
            <button type="button" className="btn-secondary" onClick={selectAll} disabled={allSelected}>
              全选
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={clearSelection}
              disabled={!someSelected}
            >
              取消选择
            </button>
            <span className="doc-gallery-selection-count">
              {someSelected ? `已选 ${selected.size} 份` : `共 ${previewFiles.length} 份`}
            </span>
            <button
              type="button"
              className="btn-primary doc-gallery-print-btn"
              onClick={printSelected}
              disabled={!someSelected || printing}
            >
              {printing ? '⏳ 准备打印…' : '🖨 打印选中'}
            </button>
          </div>

          {viewMode === 'gallery' ? (
            <DocumentGallery
              files={previewFiles}
              selected={selected}
              onToggle={toggleFile}
              onOpenPreview={setLightboxIndex}
            />
          ) : (
            byCategory && (
              <div className="doc-list-fallback">
                {Object.entries(byCategory).map(([cat, entries]) => (
                  <details key={cat} open={entries.length <= 10}>
                    <summary className="manifest-category">
                      {cat} <span className="count-badge">{entries.length}</span>
                    </summary>
                    <ul className="file-list">
                      {entries.map((e, i) => (
                        <li
                          key={i}
                          className={
                            e.skipped
                              ? 'file-skipped'
                              : e.missing_keys?.length
                                ? 'file-warn'
                                : 'file-ok'
                          }
                        >
                          {!e.skipped && e.filename && (
                            <input
                              type="checkbox"
                              checked={selected.has(e.filename)}
                              onChange={() => toggleFile(e.filename)}
                              aria-label={`选择 ${e.filename}`}
                            />
                          )}
                          <span className="file-icon">
                            {e.skipped ? '✗' : e.missing_keys?.length ? '⚠' : '✓'}
                          </span>
                          <span className="file-name">{e.filename.split('/').pop()}</span>
                          <span className="file-path">{e.filename}</span>
                        </li>
                      ))}
                    </ul>
                  </details>
                ))}
              </div>
            )
          )}
        </section>
      )}

      {lightboxIndex !== null && (
        <DocumentLightbox
          files={previewFiles}
          index={lightboxIndex}
          onClose={() => setLightboxIndex(null)}
          onPrev={() => setLightboxIndex((i) => Math.max(0, (i ?? 0) - 1))}
          onNext={() =>
            setLightboxIndex((i) => Math.min(previewFiles.length - 1, (i ?? 0) + 1))
          }
        />
      )}

      {someSelected && viewMode === 'gallery' && (
        <div className="doc-gallery-bar">
          <span>已选 {selected.size} 份</span>
          <button
            type="button"
            className="btn-primary"
            onClick={printSelected}
            disabled={printing}
          >
            {printing ? '准备中…' : '一键打印'}
          </button>
        </div>
      )}
    </div>
  )
}
