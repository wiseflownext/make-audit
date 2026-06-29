import { useState, useEffect, useRef, useCallback } from 'react'
import SignaturePad from 'signature_pad'
import { apiFetch } from '../api'

interface EmployeeSignStatus {
  name: string
  signed: boolean
}

export default function SignaturePadPage() {
  const [employees, setEmployees] = useState<EmployeeSignStatus[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [msg, setMsg] = useState('')
  const [allDone, setAllDone] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)

  const canvasRef = useRef<HTMLCanvasElement>(null)
  const padRef = useRef<SignaturePad | null>(null)

  // 初始化：获取员工列表和已签名列表
  useEffect(() => {
    async function fetchData() {
      try {
        const [empRes, sigRes] = await Promise.all([
          apiFetch('/signatures/employees').then(r => r.json()),
          apiFetch('/signatures/').then(r => r.json()),
        ])
        const signedNames: string[] = sigRes.employees_with_signatures || []
        const empNames: string[] = empRes.employees || []
        if (empNames.length === 0) {
          setMsg('尚未上传花名册，请先在电脑端上传员工数据。')
          setLoading(false)
          return
        }
        const list: EmployeeSignStatus[] = empNames.map(name => ({
          name,
          signed: signedNames.includes(name),
        }))
        setEmployees(list)
        // 定位到第一个未签名的员工
        const firstUnsigned = list.findIndex(e => !e.signed)
        if (firstUnsigned === -1) {
          setAllDone(true)
        } else {
          setCurrentIndex(firstUnsigned)
        }
      } catch (e: any) {
        setMsg('加载失败：' + e.message)
      }
      setLoading(false)
    }
    void fetchData()
  }, [])

  // 初始化/切换 SignaturePad
  const initPad = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    if (padRef.current) {
      padRef.current.off()
    }
    const ratio = window.devicePixelRatio || 1
    canvas.width = canvas.offsetWidth * ratio
    canvas.height = canvas.offsetHeight * ratio
    const ctx = canvas.getContext('2d')
    if (ctx) ctx.scale(ratio, ratio)

    const pad = new SignaturePad(canvas, {
      backgroundColor: 'rgba(248, 249, 250, 0)',
      penColor: '#1a1a2e',
      minWidth: 1.5,
      maxWidth: 3,
    })
    padRef.current = pad
  }, [])

  useEffect(() => {
    if (!loading && employees.length > 0 && !allDone) {
      // 等 DOM 渲染后再初始化
      const timer = setTimeout(() => initPad(), 50)
      return () => clearTimeout(timer)
    }
  }, [loading, currentIndex, employees.length, allDone, initPad])

  // 阻止 canvas 区域的触摸滚动
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const prevent = (e: TouchEvent) => e.preventDefault()
    canvas.addEventListener('touchstart', prevent, { passive: false })
    canvas.addEventListener('touchmove', prevent, { passive: false })
    return () => {
      canvas.removeEventListener('touchstart', prevent)
      canvas.removeEventListener('touchmove', prevent)
    }
  }, [loading, allDone])

  function clearPad() {
    padRef.current?.clear()
    setMsg('')
  }

  async function submitSignature() {
    const pad = padRef.current
    if (!pad || pad.isEmpty()) {
      setMsg('请先在签名区域签名')
      return
    }
    const employee = employees[currentIndex]
    setSubmitting(true)
    setMsg('')

    try {
      // 将 canvas 转为 PNG blob
      const canvas = canvasRef.current!
      const blob = await new Promise<Blob>((resolve, reject) => {
        canvas.toBlob(b => (b ? resolve(b) : reject(new Error('转换失败'))), 'image/png')
      })
      const fd = new FormData()
      fd.append('file', blob, `${employee.name}.png`)
      await apiFetch(`/signatures/upload/${encodeURIComponent(employee.name)}`, {
        method: 'POST',
        body: fd,
      })

      // 标记为已签名
      const updated = employees.map((e, i) =>
        i === currentIndex ? { ...e, signed: true } : e
      )
      setEmployees(updated)

      // 找下一个未签名的
      const nextUnsigned = updated.findIndex((e, i) => i > currentIndex && !e.signed)
      if (nextUnsigned !== -1) {
        setCurrentIndex(nextUnsigned)
        setMsg('')
      } else {
        // 检查是否全部完成
        const anyUnsigned = updated.find(e => !e.signed)
        if (!anyUnsigned) {
          setAllDone(true)
        } else {
          // 还有前面跳过的未签名
          const firstUnsigned = updated.findIndex(e => !e.signed)
          setCurrentIndex(firstUnsigned)
          setMsg('')
        }
      }
    } catch (e: any) {
      setMsg('上传失败：' + e.message)
    }
    setSubmitting(false)
  }

  function goToEmployee(index: number) {
    if (index === currentIndex) return
    setCurrentIndex(index)
    setMsg('')
  }

  const signedCount = employees.filter(e => e.signed).length
  const total = employees.length

  if (loading) {
    return (
      <div style={styles.loadingWrap}>
        <div style={styles.spinner} />
        <p style={{ color: '#666', marginTop: 12 }}>加载员工名单…</p>
      </div>
    )
  }

  if (msg && employees.length === 0) {
    return (
      <div style={styles.errorWrap}>
        <div style={styles.errorIcon}>⚠️</div>
        <p style={styles.errorText}>{msg}</p>
        <p style={{ color: '#888', fontSize: 14 }}>
          请在电脑端访问主页面，完成花名册上传后再使用手机签名。
        </p>
      </div>
    )
  }

  if (allDone) {
    return (
      <div style={styles.doneWrap}>
        <div style={styles.doneIcon}>✅</div>
        <h2 style={styles.doneTitle}>全部签名完成！</h2>
        <p style={styles.doneText}>共 {total} 名员工，所有签名已保存。</p>
        <p style={{ color: '#888', fontSize: 13, marginTop: 8 }}>
          请返回电脑端继续生成审计资料包。
        </p>
      </div>
    )
  }

  const currentEmployee = employees[currentIndex]

  return (
    <div style={styles.page}>
      {/* 顶部标题和进度 */}
      <div style={styles.header}>
        <h1 style={styles.headerTitle}>员工签名收集</h1>
        <div style={styles.progressRow}>
          <span style={styles.progressText}>
            {signedCount} / {total} 已签名
          </span>
          <div style={styles.progressBarBg}>
            <div
              style={{
                ...styles.progressBarFill,
                width: `${total > 0 ? (signedCount / total) * 100 : 0}%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* 员工下拉选择 */}
      <div style={styles.dropdownContainer}>
        <button
          style={styles.dropdownTrigger}
          onClick={() => setShowDropdown(!showDropdown)}
        >
          <div style={styles.dropdownTriggerLeft}>
            <span style={styles.dropdownTriggerLabel}>选择员工：</span>
            <span style={styles.dropdownTriggerValue}>
              {currentEmployee?.name}
              {currentEmployee?.signed ? (
                <span style={{ color: '#16a34a', marginLeft: 6, fontSize: 13 }}>[已签名 ✓]</span>
              ) : (
                <span style={{ color: '#ef4444', marginLeft: 6, fontSize: 13 }}>[未签名]</span>
              )}
            </span>
          </div>
          <span style={{
            fontSize: 12,
            color: '#6b7280',
            transform: showDropdown ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.2s',
            display: 'inline-block',
          }}>
            ▼
          </span>
        </button>

        {showDropdown && (
          <>
            {/* 遮罩层，点击关闭下拉 */}
            <div
              style={styles.dropdownOverlay}
              onClick={() => setShowDropdown(false)}
            />
            <div style={styles.dropdownMenu}>
              <div style={styles.dropdownMenuHeader}>
                <span>员工名单 ({signedCount}/{total} 已签)</span>
                <button
                  style={styles.dropdownCloseBtn}
                  onClick={() => setShowDropdown(false)}
                >
                  关闭
                </button>
              </div>
              <div style={styles.dropdownList}>
                {employees.map((emp, i) => (
                  <div
                    key={emp.name}
                    style={{
                      ...styles.dropdownItem,
                      ...(i === currentIndex ? styles.dropdownItemActive : {}),
                    }}
                    onClick={() => {
                      goToEmployee(i)
                      setShowDropdown(false)
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <input
                        type="checkbox"
                        checked={emp.signed}
                        readOnly
                        style={styles.checkbox}
                      />
                      <span style={{
                        fontSize: 15,
                        fontWeight: i === currentIndex ? '600' : 'normal',
                        color: i === currentIndex ? '#2563eb' : '#374151',
                      }}>
                        {emp.name}
                      </span>
                    </div>
                    {emp.signed ? (
                      <span style={styles.statusSigned}>已签名</span>
                    ) : (
                      <span style={styles.statusUnsigned}>未签名</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>

      {/* 当前员工姓名 */}
      <div style={styles.employeeCard}>
        <p style={styles.employeeLabel}>当前签名人</p>
        <h2 style={styles.employeeName}>{currentEmployee?.name}</h2>
        <p style={styles.employeeIndex}>
          第 {currentIndex + 1} 位 / 共 {total} 位
        </p>
      </div>

      {/* 签名区域 */}
      <div style={styles.canvasWrap}>
        <p style={styles.canvasHint}>请在下方空白处用手指签名</p>
        <canvas
          ref={canvasRef}
          style={styles.canvas}
        />
      </div>

      {/* 操作按钮 */}
      {msg && (
        <p style={{ ...styles.msg, color: msg.startsWith('上传失败') ? '#dc3545' : '#e67e22' }}>
          {msg}
        </p>
      )}
      <div style={styles.btnRow}>
        <button
          style={styles.btnClear}
          onClick={clearPad}
          disabled={submitting}
        >
          清除
        </button>
        <button
          style={{ ...styles.btnSubmit, opacity: submitting ? 0.6 : 1 }}
          onClick={submitSignature}
          disabled={submitting}
        >
          {submitting ? '保存中…' : '完成签名'}
        </button>
      </div>

      {/* 跳转按钮 */}
      <div style={styles.navRow}>
        <button
          style={styles.btnNav}
          onClick={() => {
            const prev = [...employees]
              .slice(0, currentIndex)
              .map((e, i) => ({ e, i }))
              .filter(x => !x.e.signed)
              .pop()
            if (prev) goToEmployee(prev.i)
            else {
              const firstUnsigned = employees.findIndex(e => !e.signed)
              if (firstUnsigned !== -1 && firstUnsigned !== currentIndex) goToEmployee(firstUnsigned)
            }
          }}
          disabled={employees.filter((e, i) => i < currentIndex && !e.signed).length === 0}
        >
          ← 上一位
        </button>
        <button
          style={styles.btnNav}
          onClick={() => {
            const next = employees
              .slice(currentIndex + 1)
              .map((e, i) => ({ e, i: i + currentIndex + 1 }))
              .find(x => !x.e.signed)
            if (next) goToEmployee(next.i)
          }}
          disabled={employees.filter((e, i) => i > currentIndex && !e.signed).length === 0}
        >
          跳过 →
        </button>
      </div>
    </div>
  )
}

// ─── Styles ────────────────────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: '100vh',
    background: '#fff',
    display: 'flex',
    flexDirection: 'column',
    padding: '0 0 24px 0',
    touchAction: 'pan-x pan-y',
    WebkitUserSelect: 'none',
    userSelect: 'none',
  },
  loadingWrap: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
  },
  spinner: {
    width: 40,
    height: 40,
    border: '3px solid #e2e8f0',
    borderTop: '3px solid #3b82f6',
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite',
  },
  errorWrap: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    textAlign: 'center',
  },
  errorIcon: { fontSize: 48, marginBottom: 12 },
  errorText: { fontSize: 16, color: '#333', fontWeight: 500, marginBottom: 8 },
  doneWrap: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    textAlign: 'center',
    background: '#fff',
  },
  doneIcon: { fontSize: 72, marginBottom: 16 },
  doneTitle: { fontSize: 26, fontWeight: 700, color: '#16a34a', margin: '0 0 8px' },
  doneText: { fontSize: 16, color: '#555' },
  header: {
    background: 'linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)',
    padding: '20px 16px 16px',
    color: '#fff',
  },
  headerTitle: {
    margin: '0 0 10px',
    fontSize: 20,
    fontWeight: 700,
    letterSpacing: 0.5,
  },
  progressRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  progressText: {
    fontSize: 13,
    whiteSpace: 'nowrap',
    opacity: 0.9,
  },
  progressBarBg: {
    flex: 1,
    height: 6,
    background: 'rgba(255,255,255,0.3)',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    background: '#86efac',
    borderRadius: 3,
    transition: 'width 0.4s ease',
  },
  dropdownContainer: {
    position: 'relative',
    padding: '12px 12px 8px',
    borderBottom: '1px solid #f0f0f0',
    zIndex: 10,
  },
  dropdownTrigger: {
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 16px',
    borderRadius: '8px',
    border: '1px solid #d1d5db',
    background: '#f9fafb',
    cursor: 'pointer',
    fontSize: '14px',
    color: '#374151',
  },
  dropdownTriggerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  dropdownTriggerLabel: {
    color: '#6b7280',
    fontWeight: 500,
  },
  dropdownTriggerValue: {
    fontWeight: 600,
    color: '#111827',
  },
  dropdownOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0, 0, 0, 0.4)',
    zIndex: 99,
  },
  dropdownMenu: {
    position: 'fixed',
    bottom: 0,
    left: 0,
    right: 0,
    maxHeight: '70vh',
    background: '#fff',
    borderTopLeftRadius: '16px',
    borderTopRightRadius: '16px',
    boxShadow: '0 -4px 20px rgba(0, 0, 0, 0.15)',
    zIndex: 100,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  dropdownMenuHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px',
    borderBottom: '1px solid #f0f0f0',
    fontSize: '16px',
    fontWeight: 600,
    color: '#1f2937',
    background: '#f9fafb',
  },
  dropdownCloseBtn: {
    background: 'none',
    border: 'none',
    color: '#2563eb',
    fontSize: '14px',
    fontWeight: 600,
    cursor: 'pointer',
  },
  dropdownList: {
    flex: 1,
    overflowY: 'auto',
    padding: '8px 0',
    WebkitOverflowScrolling: 'touch',
  },
  dropdownItem: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '14px 16px',
    borderBottom: '1px solid #f9fafb',
    cursor: 'pointer',
    transition: 'background-color 0.15s',
  },
  dropdownItemActive: {
    background: '#eff6ff',
  },
  checkbox: {
    width: '18px',
    height: '18px',
    borderRadius: '4px',
    border: '1px solid #d1d5db',
    accentColor: '#16a34a',
    cursor: 'pointer',
  },
  statusSigned: {
    fontSize: '12px',
    color: '#16a34a',
    background: '#f0fdf4',
    padding: '2px 8px',
    borderRadius: '12px',
    fontWeight: 500,
  },
  statusUnsigned: {
    fontSize: '12px',
    color: '#9ca3af',
    background: '#f3f4f6',
    padding: '2px 8px',
    borderRadius: '12px',
  },
  tagList: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 6,
    padding: '12px 12px 8px',
    borderBottom: '1px solid #f0f0f0',
  },
  tag: {
    padding: '4px 10px',
    borderRadius: 20,
    border: '1px solid #d1d5db',
    background: '#f9fafb',
    color: '#6b7280',
    fontSize: 12,
    cursor: 'pointer',
    transition: 'all 0.15s',
  },
  tagActive: {
    background: '#eff6ff',
    borderColor: '#3b82f6',
    color: '#1d4ed8',
    fontWeight: 600,
  },
  tagSigned: {
    background: '#f0fdf4',
    borderColor: '#86efac',
    color: '#16a34a',
  },
  employeeCard: {
    padding: '16px 16px 8px',
    textAlign: 'center',
  },
  employeeLabel: {
    margin: '0 0 4px',
    fontSize: 12,
    color: '#9ca3af',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  employeeName: {
    margin: 0,
    fontSize: 28,
    fontWeight: 800,
    color: '#111827',
    letterSpacing: 2,
  },
  employeeIndex: {
    margin: '4px 0 0',
    fontSize: 13,
    color: '#9ca3af',
  },
  canvasWrap: {
    margin: '8px 12px 0',
    border: '2px solid #e2e8f0',
    borderRadius: 12,
    background: '#f8fafc',
    overflow: 'hidden',
    position: 'relative',
  },
  canvasHint: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    color: '#d1d5db',
    fontSize: 14,
    pointerEvents: 'none',
    margin: 0,
    whiteSpace: 'nowrap',
  } as React.CSSProperties,
  canvas: {
    display: 'block',
    width: '100%',
    height: 350,
    touchAction: 'none',
    cursor: 'crosshair',
  },
  msg: {
    margin: '8px 16px 0',
    fontSize: 13,
    textAlign: 'center',
  },
  btnRow: {
    display: 'flex',
    gap: 10,
    padding: '12px 12px 0',
  },
  btnClear: {
    flex: 1,
    padding: '14px 0',
    borderRadius: 10,
    border: '1px solid #d1d5db',
    background: '#f9fafb',
    color: '#374151',
    fontSize: 16,
    fontWeight: 500,
    cursor: 'pointer',
  },
  btnSubmit: {
    flex: 2,
    padding: '14px 0',
    borderRadius: 10,
    border: 'none',
    background: 'linear-gradient(135deg, #2563eb, #3b82f6)',
    color: '#fff',
    fontSize: 16,
    fontWeight: 700,
    cursor: 'pointer',
    boxShadow: '0 4px 12px rgba(59,130,246,0.35)',
  },
  navRow: {
    display: 'flex',
    gap: 10,
    padding: '10px 12px 0',
  },
  btnNav: {
    flex: 1,
    padding: '10px 0',
    borderRadius: 8,
    border: '1px solid #e5e7eb',
    background: 'transparent',
    color: '#6b7280',
    fontSize: 14,
    cursor: 'pointer',
  },
}
