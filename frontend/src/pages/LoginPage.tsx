import { useState, type FormEvent } from 'react'

const USERNAME = 'admin'
const PASSWORD = 'wiseflow2024'
const SESSION_KEY = 'audit_logged_in'

export function isLoggedIn(): boolean {
  return sessionStorage.getItem(SESSION_KEY) === 'true'
}

interface Props {
  onLogin: () => void
}

export default function LoginPage({ onLogin }: Props) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    setTimeout(() => {
      if (username === USERNAME && password === PASSWORD) {
        sessionStorage.setItem(SESSION_KEY, 'true')
        onLogin()
      } else {
        setError('用户名或密码错误，请重试')
      }
      setLoading(false)
    }, 400)
  }

  return (
    <div className="login-overlay">
      <div className="login-card">
        <div className="login-logo">📋</div>
        <h1 className="login-title">HR 审计资料管理系统</h1>
        <p className="login-subtitle">请登录以继续</p>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="login-field">
            <label htmlFor="username">用户名</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="请输入用户名"
              autoComplete="username"
              required
            />
          </div>
          <div className="login-field">
            <label htmlFor="password">密码</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="请输入密码"
              autoComplete="current-password"
              required
            />
          </div>
          {error && <p className="login-err">{error}</p>}
          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? '登录中…' : '登 录'}
          </button>
        </form>
      </div>
    </div>
  )
}
