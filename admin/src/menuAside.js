import {
  mdiMonitor,
  mdiAccountGroup,
  mdiSoccerField,
  mdiCalendarCheck,
  mdiCalendarMultiple,
  mdiTrophy,
  mdiSoccer,
  mdiAccountMultiple,
  mdiChartBar,
  mdiCog,
  mdiDatabaseArrowUp,
  mdiLogout,
} from '@mdi/js'

export const menuAsideMain = [
  {
    to: '/dashboard',
    icon: mdiMonitor,
    label: 'Dashboard',
  },
  {
    to: '/users',
    icon: mdiAccountGroup,
    label: 'Users',
  },
  {
    to: '/leagues',
    icon: mdiSoccerField,
    label: 'Leagues',
  },
  {
    to: '/match-day-statuses',
    icon: mdiCalendarCheck,
    label: 'Match Day Status',
  },
  {
    to: '/match-days-map',
    icon: mdiCalendarMultiple,
    label: 'Match Days Map',
  },
  {
    to: '/real-competitions',
    icon: mdiTrophy,
    label: 'Real Competitions',
  },
  {
    to: '/real-matches',
    icon: mdiSoccer,
    label: 'Real Matches',
  },
  {
    to: '/real-team-members',
    icon: mdiAccountMultiple,
    label: 'Real Team Members',
  },
  {
    to: '/real-standings',
    icon: mdiChartBar,
    label: 'Real Standings',
  },
  {
    to: '/processes',
    icon: mdiCog,
    label: 'Processes',
  },
  {
    to: '/backup',
    icon: mdiDatabaseArrowUp,
    label: 'Backup',
  },
]

export const menuAsideBottom = [
  {
    label: 'Logout',
    icon: mdiLogout,
    color: 'info',
    isLogout: true,
  },
]
