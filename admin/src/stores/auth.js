import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api.js'

const TOKEN_KEY = 'eff_admin_token'
const USER_KEY = 'eff_admin_user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || null)
  const user = ref(JSON.parse(localStorage.getItem(USER_KEY) || 'null'))

  const isAuthenticated = computed(() => !!token.value)
  const userName = computed(() => user.value?.userName || '')
  const userEmail = computed(() => user.value?.userEmail || '')

  async function login(email, password) {
    const res = await api.post('/api/v1/auth/sign_in', {
      userEmail: email,
      userPassword: password,
    })
    const data = res.data
    if (data.userLevel !== 3) {
      throw new Error('Access restricted to site administrators.')
    }
    token.value = data.token
    user.value = {
      userName: data.userName,
      userEmail: data.userEmail,
      userLevel: data.userLevel,
      signinTime: data.firstRequest,
      currentIP: data.lastSignInIP,
      lastSigninIP: data.lastSignInIP,
      lastSigninTime: data.lastSignInDate,
      matchDayStatus: data.matchDayStatus,
      matchDayStatusStart: data.matchDayStatusStart,
      matchDayStatusFinish: data.matchDayStatusFinish,
      realCompetitionID: data.realCompetitionID,
      realCompetitionMatchDay: data.realCompetitionMatchDay,
      prevActiveRealCompetitionID: data.prevActiveRealCompetitionID,
      prevActiveRealCompetitionMatchDay: data.prevActiveRealCompetitionMatchDay,
      nextActiveRealCompetitionID: data.nextActiveRealCompetitionID,
      nextActiveRealCompetitionMatchDay: data.nextActiveRealCompetitionMatchDay,
    }
    localStorage.setItem(TOKEN_KEY, data.token)
    localStorage.setItem(USER_KEY, JSON.stringify(user.value))
    api.defaults.headers.common['Authorization'] = `Bearer ${data.token}`
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    delete api.defaults.headers.common['Authorization']
  }

  function restoreAuth() {
    if (token.value) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    }
  }

  return { token, user, isAuthenticated, userName, userEmail, login, logout, restoreAuth }
})
