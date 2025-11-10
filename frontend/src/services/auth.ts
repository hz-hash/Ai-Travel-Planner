export interface MockUser {
  name: string
  email: string
  password: string
}

const USERS_KEY = 'ai_trip_mock_users'
const SESSION_KEY = 'ai_trip_session_user'

const seedUsers: MockUser[] = [
  {
    name: '体验用户',
    email: 'demo@aitrip.com',
    password: 'demo123'
  }
]

function readUsers(): MockUser[] {
  if (typeof window === 'undefined') return seedUsers
  const raw = window.localStorage.getItem(USERS_KEY)
  if (!raw) {
    window.localStorage.setItem(USERS_KEY, JSON.stringify(seedUsers))
    return [...seedUsers]
  }
  try {
    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed)) {
      return parsed as MockUser[]
    }
  } catch {
    // ignore parse error and reset
  }
  window.localStorage.setItem(USERS_KEY, JSON.stringify(seedUsers))
  return [...seedUsers]
}

function writeUsers(users: MockUser[]) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(USERS_KEY, JSON.stringify(users))
}

export function registerUser(user: MockUser): { success: boolean; message: string } {
  if (!user.email || !user.password || !user.name) {
    return { success: false, message: '请填写完整的用户信息' }
  }
  const users = readUsers()
  if (users.some((item) => item.email === user.email)) {
    return { success: false, message: '该邮箱已注册,请直接登录' }
  }
  users.push(user)
  writeUsers(users)
  saveSession(user)
  return { success: true, message: '注册成功' }
}

export function loginUser(email: string, password: string): { success: boolean; message: string } {
  const users = readUsers()
  const target = users.find((user) => user.email === email && user.password === password)
  if (!target) {
    return { success: false, message: '邮箱或密码错误' }
  }
  saveSession(target)
  return { success: true, message: '登录成功' }
}

export function saveSession(user: MockUser) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(SESSION_KEY, JSON.stringify({ name: user.name, email: user.email }))
}

export function getSessionUser(): { name: string; email: string } | null {
  if (typeof window === 'undefined') return null
  const raw = window.localStorage.getItem(SESSION_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export function clearSession() {
  if (typeof window === 'undefined') return
  window.localStorage.removeItem(SESSION_KEY)
}

export const publicAuthRoutes = ['/auth']
