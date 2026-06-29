import { useState } from 'react'
import { apiFetch, API } from '../api'
import type { ManifestEntry } from '../api'

export default function DownloadPage() {
  const [generating, setGenerating] = useState(false)
  const [manifest, setManifest] = useState<ManifestEntry[] | null>(null)
  const [warnings, setWarnings] = useState<ManifestEntry[]>([])
  const [summary, setSummary] = useState<{ total: number; generated: number } | null>(null)
  const [msg, setMsg] = useState('')
  const [downloading, setDownloading] = useState(false)

  async function generate() {
    setGenerating(true)
    setMsg('')
    setManifest(null)
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
      setMsg('✓ ZIP 资料包已下载')
    } catch (e: any) {
      setMsg('✗ 下载失败: ' + e.message)
    }
    setDownloading(false)
  }

  const byCategory = manifest
    ? manifest.reduce<Record<string, ManifestEntry[]>>((acc, e) => {
        ;(acc[e.category] = acc[e.category] || []).push(e)
        return acc
      }, {})
    : null

  return (
    <div data-testid="page-download" className="page-content">
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

      {byCategory && (
        <section className="card">
          <h2>文件清单</h2>
          {Object.entries(byCategory).map(([cat, entries]) => (
            <details key={cat} open={entries.length <= 10}>
              <summary className="manifest-category">
                {cat} <span className="count-badge">{entries.length}</span>
              </summary>
              <ul className="file-list">
                {entries.map((e, i) => (
                  <li key={i} className={e.skipped ? 'file-skipped' : e.missing_keys?.length ? 'file-warn' : 'file-ok'}>
                    <span className="file-icon">{e.skipped ? '✗' : e.missing_keys?.length ? '⚠' : '✓'}</span>
                    <span className="file-name">{e.filename.split('/').pop()}</span>
                    <span className="file-path">{e.filename}</span>
                  </li>
                ))}
              </ul>
            </details>
          ))}
        </section>
      )}
    </div>
  )
}
