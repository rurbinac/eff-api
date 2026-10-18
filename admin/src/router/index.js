import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

const routes = [
  {
    meta: { title: 'Login', public: true },
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
  },
  {
    meta: { title: 'Dashboard' },
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/HomeView.vue'),
  },
  {
    meta: { title: 'Users' },
    path: '/users',
    name: 'users',
    component: () => import('@/views/UsersView.vue'),
  },
  {
    meta: { title: 'User Detail' },
    path: '/users/:id',
    name: 'user-detail',
    component: () => import('@/views/UserDetailView.vue'),
  },
  {
    meta: { title: 'Leagues & Divisions' },
    path: '/leagues',
    name: 'leagues',
    component: () => import('@/views/LeaguesView.vue'),
  },
  {
    meta: { title: 'League Divisions' },
    path: '/leagues/:id/divisions',
    name: 'league-divisions',
    component: () => import('@/views/LeagueDivisionsView.vue'),
  },
  {
    meta: { title: 'League Matches' },
    path: '/leagues/:id/matches',
    name: 'league-matches',
    component: () => import('@/views/LeagueMatchesView.vue'),
  },
  {
    meta: { title: 'Match Day Status' },
    path: '/match-day-statuses',
    name: 'match-day-statuses',
    component: () => import('@/views/MatchDayStatusView.vue'),
  },
  {
    meta: { title: 'Real Competitions' },
    path: '/real-competitions',
    name: 'real-competitions',
    component: () => import('@/views/RealCompetitionsView.vue'),
  },
  {
    meta: { title: 'Competition Detail' },
    path: '/real-competitions/:id',
    name: 'real-competition-detail',
    component: () => import('@/views/RealCompetitionDetailView.vue'),
  },
  {
    meta: { title: 'Match Days Map' },
    path: '/match-days-map',
    name: 'match-days-map',
    component: () => import('@/views/MatchDaysMapView.vue'),
  },
  {
    meta: { title: 'Real Matches' },
    path: '/real-matches',
    name: 'real-matches',
    component: () => import('@/views/RealMatchesView.vue'),
  },
  {
    meta: { title: 'Match Detail' },
    path: '/real-matches/:id',
    name: 'real-match-detail',
    component: () => import('@/views/RealMatchDetailView.vue'),
  },
  {
    meta: { title: 'Real Team Members' },
    path: '/real-team-members',
    name: 'real-team-members',
    component: () => import('@/views/RealTeamMembersView.vue'),
  },
  {
    meta: { title: 'Player Detail' },
    path: '/real-team-members/:key',
    name: 'real-team-member-detail',
    component: () => import('@/views/RealTeamMemberDetailView.vue'),
  },
  {
    meta: { title: 'Real Standings' },
    path: '/real-standings',
    name: 'real-standings',
    component: () => import('@/views/RealStandingsView.vue'),
  },
  {
    meta: { title: 'Standing Detail' },
    path: '/real-standings/:id',
    name: 'real-standing-detail',
    component: () => import('@/views/RealStandingDetailView.vue'),
  },
  {
    meta: { title: 'Processes' },
    path: '/processes',
    name: 'processes',
    component: () => import('@/views/ProcessesView.vue'),
  },
  {
    meta: { title: 'Backup' },
    path: '/backup',
    name: 'backup',
    component: () => import('@/views/BackupView.vue'),
  },
  {
    meta: { title: 'Error', public: true },
    path: '/error',
    name: 'error',
    component: () => import('@/views/ErrorView.vue'),
  },
  {
    path: '/',
    redirect: '/dashboard',
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    return savedPosition || { top: 0 }
  },
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'login' }
  }
  if (to.name === 'login' && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }
})

export default router
