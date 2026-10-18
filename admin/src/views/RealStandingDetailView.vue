<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { mdiChartBar, mdiArrowLeft } from '@mdi/js'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import CardBox from '@/components/CardBox.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import api from '@/api.js'

const route = useRoute()
const router = useRouter()

const s = ref(null)
const loading = ref(true)
const error = ref(null)

const title = computed(() => {
  if (!s.value) return 'Standing Detail'
  return s.value.isPlayer ? (s.value.name || 'Player') : (s.value.realTeamName || 'Team')
})

const fmtDate = (iso) => {
  if (!iso) return '—'
  return iso.replace('T', ' ').replace(/\.\d+.*$/, '')
}

const fmt = (v) => v ?? '—'

onMounted(async () => {
  try {
    const res = await api.get(`/api/v1/admin/real-standings/${route.params.id}`)
    s.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load standing.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton :icon="mdiChartBar" :title="title" main>
        <button
          class="flex items-center gap-1 rounded px-3 py-1 text-sm font-medium bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
          @click="router.back()"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current"><path :d="mdiArrowLeft" /></svg>
          Back
        </button>
      </SectionTitleLineWithButton>

      <p v-if="error" class="mb-4 text-red-500">{{ error }}</p>
      <p v-else-if="loading" class="text-gray-400">Loading…</p>

      <template v-else-if="s">

        <!-- Context: competition + match -->
        <CardBox class="mb-4">
          <div class="px-3 py-2 border-b border-gray-100 dark:border-slate-700 font-semibold text-sm text-gray-700 dark:text-slate-200">Context</div>
          <div class="grid grid-cols-2 md:grid-cols-4 text-sm divide-x divide-gray-100 dark:divide-slate-700">
            <div class="px-4 py-3">
              <div class="text-xs text-gray-500 dark:text-slate-400 mb-0.5">Competition</div>
              <div class="font-medium">{{ s.realCompetitionSYMID }}</div>
              <div class="text-xs text-gray-400">Season {{ s.realCompetitionSeasonId }}</div>
            </div>
            <div class="px-4 py-3">
              <div class="text-xs text-gray-500 dark:text-slate-400 mb-0.5">Match Day</div>
              <div class="font-bold text-lg">{{ s.realCompetitionMatchDay }}</div>
              <div class="text-xs text-gray-400">of {{ s.realCompetitionLastMatchDay }}</div>
            </div>
            <div class="px-4 py-3">
              <div class="text-xs text-gray-500 dark:text-slate-400 mb-0.5">Match</div>
              <div class="font-mono text-xs">ID {{ s.realMatchID ?? '—' }}</div>
              <div class="text-xs text-gray-400">{{ fmtDate(s.realMatchDate) }}</div>
            </div>
            <div class="px-4 py-3">
              <div class="text-xs text-gray-500 dark:text-slate-400 mb-0.5">Score</div>
              <div class="font-bold font-mono">
                {{ s.realTeamScore ?? '?' }} – {{ s.oppositeRealTeamScore ?? '?' }}
              </div>
              <div class="text-xs text-gray-400">{{ s.realTeamSide }} vs {{ s.oppositeRealTeamShortName || s.oppositeRealTeamName }}</div>
            </div>
          </div>
        </CardBox>

        <!-- ── PLAYER layout ── -->
        <template v-if="s.isPlayer">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <!-- Identity -->
            <CardBox>
              <div class="px-3 py-2 border-b border-gray-100 dark:border-slate-700 font-semibold text-sm text-gray-700 dark:text-slate-200">Player</div>
              <table class="w-full text-sm">
                <tbody>
                  <tr class="border-b border-gray-50 dark:border-slate-800">
                    <td class="py-1.5 px-3 w-36 text-gray-500 dark:text-slate-400">Key</td>
                    <td class="py-1.5 px-3 font-mono text-xs">{{ s.realTeamMemberKey }}</td>
                  </tr>
                  <tr class="border-b border-gray-50 dark:border-slate-800">
                    <td class="py-1.5 px-3 text-gray-500 dark:text-slate-400">Name</td>
                    <td class="py-1.5 px-3 font-medium">{{ s.knownName || s.name }}</td>
                  </tr>
                  <tr class="border-b border-gray-50 dark:border-slate-800">
                    <td class="py-1.5 px-3 text-gray-500 dark:text-slate-400">Position</td>
                    <td class="py-1.5 px-3">{{ s.position || '—' }} <span v-if="s.draftPosition" class="text-xs text-gray-400">({{ s.draftPosition }})</span></td>
                  </tr>
                  <tr>
                    <td class="py-1.5 px-3 text-gray-500 dark:text-slate-400">Team</td>
                    <td class="py-1.5 px-3">{{ s.realTeamName }} <span v-if="s.realTeamShortName" class="text-xs text-gray-400">({{ s.realTeamShortName }})</span></td>
                  </tr>
                </tbody>
              </table>
            </CardBox>

            <!-- Match stats -->
            <CardBox>
              <div class="px-3 py-2 border-b border-gray-100 dark:border-slate-700 font-semibold text-sm text-gray-700 dark:text-slate-200">This Match</div>
              <div class="grid grid-cols-3 divide-x divide-gray-100 dark:divide-slate-700">
                <div v-for="stat in [
                  { label: 'Played', value: fmt(s.matchGamePlayed) },
                  { label: 'Minutes', value: fmt(s.matchTimePlayed) },
                  { label: 'Points L1', value: fmt(s.matchPointsL1) },
                  { label: 'Goals', value: fmt(s.matchGoals) },
                  { label: 'Assists', value: fmt(s.matchAssists) },
                  { label: 'Clean Sheet', value: fmt(s.matchCleanSheet) },
                  { label: 'Yellow', value: fmt(s.matchYellowCards) },
                  { label: 'Red', value: fmt(s.matchRedCards) },
                  { label: 'Goals Conc.', value: fmt(s.matchGoalsConceded) },
                ]" :key="stat.label" class="px-3 py-2 text-center">
                  <div class="text-base font-bold text-gray-800 dark:text-slate-100">{{ stat.value }}</div>
                  <div class="text-xs text-gray-500 dark:text-slate-400">{{ stat.label }}</div>
                </div>
              </div>
              <div class="border-t border-gray-100 dark:border-slate-700 px-3 py-2 text-xs text-gray-500 dark:text-slate-400 grid grid-cols-4 gap-2 mt-1">
                <span>Played: {{ fmt(s.matchPointsL1Played) }}</span>
                <span>Goals: {{ fmt(s.matchPointsL1Goals) }}</span>
                <span>Assists: {{ fmt(s.matchPointsL1Assists) }}</span>
                <span>Cards: {{ fmt(s.matchPointsL1Cards) }}</span>
                <span>CS: {{ fmt(s.matchPointsL1CleanSheet) }}</span>
                <span>GA: {{ fmt(s.matchPointsL1GoalsAllowed) }}</span>
                <span>OG: {{ fmt(s.matchPointsL1OwnGoals) }}</span>
              </div>
            </CardBox>
          </div>

          <!-- Cumulative stats -->
          <CardBox>
            <div class="px-3 py-2 border-b border-gray-100 dark:border-slate-700 font-semibold text-sm text-gray-700 dark:text-slate-200">
              Cumulative (through MD {{ s.realCompetitionMatchDay }})
            </div>
            <div class="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-10 divide-x divide-gray-100 dark:divide-slate-700">
              <div v-for="stat in [
                { label: 'Ranking', value: fmt(s.ranking) },
                { label: 'Points L1', value: fmt(s.pointsL1) },
                { label: 'Played', value: fmt(s.gamePlayed) },
                { label: 'Goals', value: fmt(s.goals) },
                { label: 'Assists', value: fmt(s.assists) },
                { label: 'Yellow', value: fmt(s.yellowCards) },
                { label: 'Red', value: fmt(s.redCards) },
                { label: 'Clean Sheet', value: fmt(s.cleanSheet) },
                { label: 'Goals Conc.', value: fmt(s.goalsConceded) },
                { label: 'Time (min)', value: fmt(s.timePlayed) },
              ]" :key="stat.label" class="px-2 py-3 text-center">
                <div class="text-base font-bold text-gray-800 dark:text-slate-100">{{ stat.value }}</div>
                <div class="text-xs text-gray-500 dark:text-slate-400">{{ stat.label }}</div>
              </div>
            </div>
          </CardBox>
        </template>

        <!-- ── TEAM layout ── -->
        <template v-else>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <!-- Match stats -->
            <CardBox>
              <div class="px-3 py-2 border-b border-gray-100 dark:border-slate-700 font-semibold text-sm text-gray-700 dark:text-slate-200">This Match</div>
              <div class="grid grid-cols-3 divide-x divide-gray-100 dark:divide-slate-700">
                <div v-for="stat in [
                  { label: 'Points L1', value: fmt(s.matchPointsL1) },
                  { label: 'Won', value: fmt(s.matchWon) },
                  { label: 'Draw', value: fmt(s.matchDraw) },
                  { label: 'Lost', value: fmt(s.matchLost) },
                  { label: 'Goals', value: fmt(s.matchGoals) },
                  { label: 'Goals Conc.', value: fmt(s.matchGoalsConceded) },
                ]" :key="stat.label" class="px-3 py-2 text-center">
                  <div class="text-base font-bold text-gray-800 dark:text-slate-100">{{ stat.value }}</div>
                  <div class="text-xs text-gray-500 dark:text-slate-400">{{ stat.label }}</div>
                </div>
              </div>
            </CardBox>

            <!-- Cumulative -->
            <CardBox>
              <div class="px-3 py-2 border-b border-gray-100 dark:border-slate-700 font-semibold text-sm text-gray-700 dark:text-slate-200">
                Cumulative (through MD {{ s.realCompetitionMatchDay }})
              </div>
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-gray-100 dark:border-slate-700 text-xs text-gray-500 dark:text-slate-400">
                    <th class="py-1 px-3 text-left font-medium"></th>
                    <th class="py-1 px-3 text-right font-medium">P</th>
                    <th class="py-1 px-3 text-right font-medium">W</th>
                    <th class="py-1 px-3 text-right font-medium">D</th>
                    <th class="py-1 px-3 text-right font-medium">L</th>
                    <th class="py-1 px-3 text-right font-medium">GF</th>
                    <th class="py-1 px-3 text-right font-medium">GA</th>
                    <th class="py-1 px-3 text-right font-medium">Pos</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in [
                    { label: 'Overall', p: s.played, w: s.won, d: s.draw, l: s.lost, gf: s.goalsFor, ga: s.goalsAgainst, pos: s.place },
                    { label: 'Home', p: s.playedHome, w: s.wonHome, d: s.drawHome, l: s.lostHome, gf: s.goalsForHome, ga: s.goalsAgainstHome, pos: s.placeHome },
                    { label: 'Away', p: s.playedAway, w: s.wonAway, d: s.drawAway, l: s.lostAway, gf: s.goalsForAway, ga: s.goalsAgainstAway, pos: s.placeAway },
                  ]" :key="row.label" class="border-b border-gray-50 dark:border-slate-800 text-xs">
                    <td class="py-1.5 px-3 font-medium text-gray-500 dark:text-slate-400">{{ row.label }}</td>
                    <td class="py-1.5 px-3 text-right">{{ fmt(row.p) }}</td>
                    <td class="py-1.5 px-3 text-right">{{ fmt(row.w) }}</td>
                    <td class="py-1.5 px-3 text-right">{{ fmt(row.d) }}</td>
                    <td class="py-1.5 px-3 text-right">{{ fmt(row.l) }}</td>
                    <td class="py-1.5 px-3 text-right">{{ fmt(row.gf) }}</td>
                    <td class="py-1.5 px-3 text-right">{{ fmt(row.ga) }}</td>
                    <td class="py-1.5 px-3 text-right font-bold">{{ fmt(row.pos) }}</td>
                  </tr>
                </tbody>
              </table>
            </CardBox>
          </div>
        </template>

      </template>
    </SectionMain>
  </LayoutAuthenticated>
</template>
