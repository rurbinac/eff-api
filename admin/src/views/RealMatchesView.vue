<script setup>
import { ref, onMounted } from 'vue'
import { mdiSoccer } from '@mdi/js'
import { useRoute, useRouter } from 'vue-router'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import CardBox from '@/components/CardBox.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import api from '@/api.js'

const route = useRoute()
const router = useRouter()

const competitions = ref([])
const selectedKey = ref('')   // "SYMID|seasonId"
const rows = ref([])
const loading = ref(false)
const error = ref(null)

const compLabel = (c) =>
  `${c.realCompetitionSYMID} ${c.realCompetitionSeasonId}: ${c.realCompetitionName}`

const compKey = (c) => `${c.realCompetitionSYMID}|${c.realCompetitionSeasonId}`

const fmtDate = (iso) => {
  if (!iso) return '—'
  return iso.replace('T', ' ').replace(/(\.\d+)?Z$/, '')
}

const fmtAttendance = (n) => {
  if (n == null) return '—'
  return Number(n).toLocaleString('en-US')
}

const teamLabel = (name, short) => {
  if (!name) return '—'
  return short ? `${name} (${short})` : name
}

async function fetchMatches(key) {
  if (!key) return
  const [symid, season_id] = key.split('|')
  loading.value = true
  error.value = null
  rows.value = []
  try {
    const res = await api.get('/api/v1/admin/real-matches', { params: { symid, season_id } })
    rows.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load real matches.'
  } finally {
    loading.value = false
  }
}

function onCompChange(e) {
  selectedKey.value = e.target.value
  fetchMatches(selectedKey.value)
}

onMounted(async () => {
  try {
    const res = await api.get('/api/v1/admin/real-competitions')
    competitions.value = res.data
    const queryKey = route.query.key
    if (queryKey && res.data.some(c => compKey(c) === queryKey)) {
      selectedKey.value = queryKey
    } else if (res.data.length) {
      selectedKey.value = compKey(res.data[0])
    }
    if (selectedKey.value) fetchMatches(selectedKey.value)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load competitions.'
  }
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton :icon="mdiSoccer" title="Real Matches" main />

      <div class="mb-4 flex items-center gap-3 flex-wrap">
        <label class="text-sm font-medium text-gray-600 dark:text-slate-300">Competition</label>
        <select
          :value="selectedKey"
          class="text-sm border border-gray-300 dark:border-slate-600 rounded px-2 py-1 bg-white dark:bg-slate-800 min-w-[22rem]"
          @change="onCompChange"
        >
          <option
            v-for="c in competitions"
            :key="compKey(c)"
            :value="compKey(c)"
          >{{ compLabel(c) }}</option>
        </select>
        <span v-if="loading" class="text-sm text-gray-400">Loading…</span>
      </div>

      <p v-if="error" class="mb-4 text-sm text-red-500">{{ error }}</p>

      <CardBox has-table>
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-100 dark:border-slate-700">
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300" rowspan="2">Match Day</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300" rowspan="2">Date</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 hidden md:table-cell" rowspan="2">Period</th>
              <th class="py-2 px-3 text-right font-semibold text-gray-600 dark:text-slate-300 hidden lg:table-cell" rowspan="2">Attendance</th>
              <th class="py-2 px-3 text-center font-semibold text-blue-600 dark:text-blue-400 border-l border-gray-200 dark:border-slate-700" colspan="3">First Team</th>
              <th class="py-2 px-3 text-center font-semibold text-blue-600 dark:text-blue-400 border-l border-gray-200 dark:border-slate-700" colspan="3">Second Team</th>
              <th class="py-2 px-2" rowspan="2"></th>
            </tr>
            <tr class="border-b border-gray-100 dark:border-slate-700">
              <th class="py-1 px-2 text-center font-medium text-gray-500 dark:text-slate-400 text-xs border-l border-gray-200 dark:border-slate-700">H/A</th>
              <th class="py-1 px-3 text-left font-medium text-gray-500 dark:text-slate-400 text-xs">Team</th>
              <th class="py-1 px-2 text-center font-medium text-gray-500 dark:text-slate-400 text-xs">Score</th>
              <th class="py-1 px-2 text-center font-medium text-gray-500 dark:text-slate-400 text-xs border-l border-gray-200 dark:border-slate-700">H/A</th>
              <th class="py-1 px-3 text-left font-medium text-gray-500 dark:text-slate-400 text-xs">Team</th>
              <th class="py-1 px-2 text-center font-medium text-gray-500 dark:text-slate-400 text-xs">Score</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading && !rows.length">
              <td colspan="11" class="py-4 px-3 text-gray-400">Loading…</td>
            </tr>
            <tr v-else-if="!loading && !rows.length">
              <td colspan="11" class="py-4 px-3 text-gray-400">No matches found.</td>
            </tr>
            <tr
              v-for="row in rows"
              :key="row.realMatchID"
              class="border-b border-gray-50 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-700/30"
            >
              <td class="py-2 px-3 font-mono text-xs font-medium text-gray-700 dark:text-slate-300 whitespace-nowrap">
                {{ row.realCompetitionSYMID }}-{{ row.realCompetitionMatchDay }}
              </td>
              <td class="py-2 px-3 text-gray-600 dark:text-slate-300 whitespace-nowrap text-xs">{{ fmtDate(row.realMatchDate) }}</td>
              <td class="py-2 px-3 text-gray-500 dark:text-slate-400 hidden md:table-cell">{{ row.realMatchPeriod ?? '—' }}</td>
              <td class="py-2 px-3 text-right text-gray-500 dark:text-slate-400 hidden lg:table-cell">{{ fmtAttendance(row.realMatchAttendance) }}</td>
              <td class="py-2 px-2 text-center font-mono text-xs text-gray-500 dark:text-slate-400 border-l border-gray-100 dark:border-slate-800">{{ row.firstSide ?? '?' }}</td>
              <td class="py-2 px-3 text-gray-800 dark:text-slate-200">{{ teamLabel(row.firstName, row.firstShortName) }}</td>
              <td class="py-2 px-2 text-center font-bold text-gray-900 dark:text-slate-100">{{ row.firstScore ?? '—' }}</td>
              <td class="py-2 px-2 text-center font-mono text-xs text-gray-500 dark:text-slate-400 border-l border-gray-100 dark:border-slate-800">{{ row.secondSide ?? '?' }}</td>
              <td class="py-2 px-3 text-gray-800 dark:text-slate-200">{{ teamLabel(row.secondName, row.secondShortName) }}</td>
              <td class="py-2 px-2 text-center font-bold text-gray-900 dark:text-slate-100">{{ row.secondScore ?? '—' }}</td>
              <td class="py-2 px-2 whitespace-nowrap">
                <button
                  class="text-xs px-2 py-0.5 rounded border border-blue-400 text-blue-600 dark:text-blue-400 dark:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20"
                  @click="router.push({ name: 'real-match-detail', params: { id: row.realMatchID } })"
                >Detail</button>
              </td>
            </tr>
          </tbody>
        </table>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
