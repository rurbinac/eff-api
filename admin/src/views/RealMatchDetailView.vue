<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { mdiSoccer, mdiArrowLeft } from '@mdi/js'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import CardBox from '@/components/CardBox.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import api from '@/api.js'

const route = useRoute()
const router = useRouter()

const match = ref(null)
const loading = ref(true)
const error = ref(null)
const activeTab = ref('players')

const title = computed(() => {
  if (!match.value) return 'Match Detail'
  const m = match.value
  return `${m.firstName ?? '?'} ${m.firstScore ?? '—'} – ${m.secondScore ?? '—'} ${m.secondName ?? '?'}`
})

const fmtDate = (iso) => {
  if (!iso) return '—'
  return iso.replace('T', ' ').replace(/\.\d+.*$/, '')
}

const fmtTime = (mins) => {
  if (mins == null) return '—'
  return `${mins}'`
}

const fmtAttendance = (n) => {
  if (n == null) return '—'
  return Number(n).toLocaleString('en-US')
}

const periodLabel = (p) => {
  if (p == null) return '—'
  const map = { 1: 'Q1', 2: 'Q2', 3: 'Q3', 4: 'Q4', 5: 'ET1', 6: 'ET2', 16: 'FT', 32: 'AET' }
  return map[p] ?? String(p)
}

const resultLabel = (r) => {
  if (r == null) return '—'
  const map = { 1: 'Win', 0: 'Draw', '-1': 'Loss', '-1': 'Loss' }
  return r === 1 ? 'Win' : r === 0 ? 'Draw' : r === -1 ? 'Loss' : String(r)
}

const eventIcon = (reason) => {
  const r = (reason || '').toLowerCase()
  if (r.includes('goal')) return '⚽'
  if (r.includes('red')) return '🟥'
  if (r.includes('yellow')) return '🟨'
  if (r.includes('sub') || r.includes('tactical')) return '🔄'
  return '•'
}

const playersByTeam = computed(() => {
  if (!match.value?.players) return []
  const groups = {}
  for (const p of match.value.players) {
    const key = p.realTeamID
    if (!groups[key]) groups[key] = { name: p.realTeamName, side: p.realTeamSide, players: [] }
    groups[key].players.push(p)
  }
  return Object.values(groups).sort((a, b) => a.side.localeCompare(b.side))
})

const statIcon = (p) => {
  const parts = []
  if (p.matchGoals) parts.push(`${'⚽'.repeat(p.matchGoals)}`)
  if (p.matchAssists) parts.push(`${'🅰️'.repeat(p.matchAssists)}`)
  if (p.matchYellowCards) parts.push('🟨'.repeat(p.matchYellowCards))
  if (p.matchRedCards) parts.push('🟥')
  if (p.matchCleanSheet) parts.push('🧤')
  return parts.join(' ')
}

onMounted(async () => {
  try {
    const res = await api.get(`/api/v1/admin/real-matches/${route.params.id}`)
    match.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load match.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton :icon="mdiSoccer" :title="title" main>
        <button
          class="flex items-center gap-1 rounded px-3 py-1 text-sm font-medium bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
          @click="router.push({ name: 'real-matches' })"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
            <path :d="mdiArrowLeft" />
          </svg>
          Matches
        </button>
      </SectionTitleLineWithButton>

      <p v-if="error" class="mb-4 text-red-500">{{ error }}</p>
      <p v-else-if="loading" class="text-gray-400">Loading…</p>

      <template v-else-if="match">

        <!-- Score header -->
        <CardBox class="mb-4">
          <div class="flex items-center justify-center gap-6 py-4">
            <div class="text-right flex-1">
              <div class="text-lg font-semibold text-gray-800 dark:text-slate-100">{{ match.firstName }}</div>
              <div class="text-xs text-gray-500 dark:text-slate-400">{{ match.firstSide }}</div>
            </div>
            <div class="text-3xl font-bold font-mono text-gray-900 dark:text-slate-100 min-w-[5rem] text-center">
              {{ match.firstScore ?? '—' }} – {{ match.secondScore ?? '—' }}
            </div>
            <div class="text-left flex-1">
              <div class="text-lg font-semibold text-gray-800 dark:text-slate-100">{{ match.secondName }}</div>
              <div class="text-xs text-gray-500 dark:text-slate-400">{{ match.secondSide }}</div>
            </div>
          </div>
          <div class="flex justify-center gap-6 text-xs text-gray-500 dark:text-slate-400 pb-3 border-t border-gray-50 dark:border-slate-800 pt-2 mt-1">
            <span>{{ match.realCompetitionSYMID }}-{{ match.realCompetitionMatchDay }}</span>
            <span>{{ fmtDate(match.realMatchDate) }}</span>
            <span v-if="match.realMatchPeriod">Period: {{ match.realMatchPeriod }}</span>
            <span v-if="match.realMatchAttendance">{{ fmtAttendance(match.realMatchAttendance) }} att.</span>
          </div>
        </CardBox>

        <!-- Match details -->
        <CardBox class="mb-4">
          <table class="w-full text-sm">
            <tbody>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 w-44 font-semibold text-gray-500 dark:text-slate-400">Match ID</td>
                <td class="py-2 px-3 font-mono text-xs text-gray-400">{{ match.realMatchID }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Type</td>
                <td class="py-2 px-3">{{ match.realMatchType || '—' }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Period</td>
                <td class="py-2 px-3">{{ match.realMatchPeriod || '—' }} / {{ match.realMatchRealPeriod || '—' }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Result type</td>
                <td class="py-2 px-3">{{ match.realMatchResultType || '—' }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Match time</td>
                <td class="py-2 px-3 font-mono text-xs">
                  {{ fmtTime(match.realMatchTime) }}
                  <span v-if="match.realMatchFirstHalfTime != null" class="text-gray-400 ml-2">1H: {{ fmtTime(match.realMatchFirstHalfTime) }}</span>
                  <span v-if="match.realMatchSecondHalfTime != null" class="text-gray-400 ml-2">2H: {{ fmtTime(match.realMatchSecondHalfTime) }}</span>
                </td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Attendance</td>
                <td class="py-2 px-3">{{ fmtAttendance(match.realMatchAttendance) }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Season</td>
                <td class="py-2 px-3">{{ match.realCompetitionSYMID }} / {{ match.realCompetitionSeasonId }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Last F7</td>
                <td class="py-2 px-3 font-mono text-xs text-gray-400">{{ fmtDate(match.lastF7Date) }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Last F42</td>
                <td class="py-2 px-3 font-mono text-xs text-gray-400">{{ fmtDate(match.lastF42Date) }}</td>
              </tr>
            </tbody>
          </table>
        </CardBox>

        <!-- Teams side by side -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <CardBox v-for="(side, idx) in [
            { label: match.firstName, short: match.firstShortName, side: match.firstSide, score: match.firstScore, realScore: match.firstRealScore, result: match.firstResult, points: match.firstPoints, cleanSheet: match.firstCleanSheet },
            { label: match.secondName, short: match.secondShortName, side: match.secondSide, score: match.secondScore, realScore: match.secondRealScore, result: match.secondResult, points: match.secondPoints, cleanSheet: match.secondCleanSheet },
          ]" :key="idx">
            <div class="px-3 py-2">
              <div class="font-semibold text-gray-800 dark:text-slate-100 mb-2">{{ side.label }} <span class="text-xs text-gray-400">({{ side.side }})</span></div>
              <table class="w-full text-xs">
                <tr><td class="py-0.5 w-28 text-gray-500 dark:text-slate-400">Score</td><td class="font-bold">{{ side.score ?? '—' }}</td></tr>
                <tr v-if="side.realScore != null"><td class="py-0.5 text-gray-500 dark:text-slate-400">Real score</td><td>{{ side.realScore }}</td></tr>
                <tr><td class="py-0.5 text-gray-500 dark:text-slate-400">Result</td><td>{{ resultLabel(side.result) }}</td></tr>
                <tr><td class="py-0.5 text-gray-500 dark:text-slate-400">Points</td><td>{{ side.points ?? '—' }}</td></tr>
                <tr><td class="py-0.5 text-gray-500 dark:text-slate-400">Clean sheet</td><td>{{ side.cleanSheet === 1 ? 'Yes' : side.cleanSheet === 0 ? 'No' : '—' }}</td></tr>
              </table>
            </div>
          </CardBox>
        </div>

        <!-- Tab bar -->
        <div class="flex gap-1 mb-3 border-b border-gray-200 dark:border-slate-700">
          <button
            v-for="tab in [{ key: 'players', label: `Players (${match.players.length})` }, { key: 'events', label: `Events (${match.events.length})` }]"
            :key="tab.key"
            class="px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors"
            :class="activeTab === tab.key
              ? 'border-blue-500 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200'"
            @click="activeTab = tab.key"
          >{{ tab.label }}</button>
        </div>

        <!-- Players tab -->
        <template v-if="activeTab === 'players'">
          <div v-if="!match.players.length" class="py-4 text-sm text-gray-400">No player data.</div>
          <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <CardBox v-for="group in playersByTeam" :key="group.name" has-table>
              <div class="px-3 py-2 border-b border-gray-100 dark:border-slate-700 font-semibold text-sm text-gray-700 dark:text-slate-200">
                {{ group.name }} <span class="text-xs font-normal text-gray-400">({{ group.side }})</span>
              </div>
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-gray-100 dark:border-slate-700 text-xs">
                    <th class="py-1.5 px-3 text-left font-semibold text-gray-500 dark:text-slate-400">Player</th>
                    <th class="py-1.5 px-3 text-left font-semibold text-gray-500 dark:text-slate-400 hidden sm:table-cell">Pos</th>
                    <th class="py-1.5 px-3 text-right font-semibold text-gray-500 dark:text-slate-400">Min</th>
                    <th class="py-1.5 px-3 text-right font-semibold text-gray-500 dark:text-slate-400 hidden md:table-cell">Pts</th>
                    <th class="py-1.5 px-3 text-left font-semibold text-gray-500 dark:text-slate-400"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="p in group.players"
                    :key="p.realStandingID"
                    class="border-b border-gray-50 dark:border-slate-800"
                    :class="{ 'opacity-50': !p.matchGamePlayed }"
                  >
                    <td class="py-1.5 px-3 text-gray-800 dark:text-slate-200">{{ p.playerName }}</td>
                    <td class="py-1.5 px-3 text-xs text-gray-400 hidden sm:table-cell">{{ p.draftPosition || p.position }}</td>
                    <td class="py-1.5 px-3 text-right font-mono text-xs text-gray-500 dark:text-slate-400">{{ p.matchTimePlayed ?? '—' }}</td>
                    <td class="py-1.5 px-3 text-right font-mono text-xs text-gray-500 dark:text-slate-400 hidden md:table-cell">{{ p.matchPointsL1 ?? '—' }}</td>
                    <td class="py-1.5 px-3 text-sm">{{ statIcon(p) }}</td>
                  </tr>
                </tbody>
              </table>
            </CardBox>
          </div>
        </template>

        <!-- Events tab -->
        <CardBox v-else has-table>
          <div v-if="!match.events.length" class="px-3 py-4 text-sm text-gray-400">No events.</div>
          <table v-else class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-100 dark:border-slate-700">
                <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 text-xs">#</th>
                <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 text-xs">Event</th>
                <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 text-xs">Player</th>
                <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 text-xs">Team</th>
                <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 text-xs hidden md:table-cell">Time</th>
                <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 text-xs hidden lg:table-cell">Type / Class</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="ev in match.events"
                :key="ev.realMatchEventID"
                class="border-b border-gray-50 dark:border-slate-800"
              >
                <td class="py-2 px-3 font-mono text-xs text-gray-400">{{ ev.eventPosition }}</td>
                <td class="py-2 px-3">
                  <span class="mr-1">{{ eventIcon(ev.eventReason) }}</span>
                  <span class="text-gray-700 dark:text-slate-300">{{ ev.eventReason }}</span>
                </td>
                <td class="py-2 px-3 text-gray-800 dark:text-slate-200">{{ ev.playerName || '—' }}</td>
                <td class="py-2 px-3 text-gray-500 dark:text-slate-400 text-xs">{{ ev.teamName }} <span class="text-gray-400">({{ ev.teamSide }})</span></td>
                <td class="py-2 px-3 font-mono text-xs text-gray-500 dark:text-slate-400 whitespace-nowrap hidden md:table-cell">
                  <span v-if="ev.eventPeriod != null">P{{ ev.eventPeriod }}</span>
                  <span v-if="ev.eventMin != null" class="ml-1">{{ ev.eventMin }}'</span><span v-if="ev.eventSec != null">{{ String(ev.eventSec).padStart(2,'0') }}"</span>
                </td>
                <td class="py-2 px-3 text-xs text-gray-400 hidden lg:table-cell">
                  {{ [ev.eventType, ev.eventClass].filter(Boolean).join(' / ') || '—' }}
                </td>
              </tr>
            </tbody>
          </table>
        </CardBox>

      </template>
    </SectionMain>
  </LayoutAuthenticated>
</template>
