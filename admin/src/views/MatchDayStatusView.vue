<script setup>
import { ref, computed, onMounted } from 'vue'
import { mdiCalendarCheck } from '@mdi/js'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import CardBox from '@/components/CardBox.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import api from '@/api.js'

const seasons = ref([])
const mapKeys = ref([])
const rows = ref([])
const loading = ref(false)
const error = ref(null)
const selectedSeason = ref(null)
const selectedMapKey = ref(null)
const activeTab = ref('waivers')

const tabs = [
  { key: 'waivers',            label: 'Waivers',             s: 'startWaivers',            f: 'finishWaivers' },
  { key: 'waivers-settle',     label: 'Waivers Settle',      s: 'startWaiversSettle',      f: 'finishWaiversSettle' },
  { key: 'open-waivers',       label: 'Open Waivers',        s: 'startOpenWaivers',        f: 'finishOpenWaivers' },
  { key: 'open-waivers-settle',label: 'Open Waivers Settle', s: 'startOpenWaiversSettle',  f: 'finishOpenWaiversSettle' },
  { key: 'pre-match',          label: 'Pre Match',           s: 'startPreMatch',           f: 'finishPreMatch' },
  { key: 'match',              label: 'Match',               s: 'startMatch',              f: 'finishMatch' },
  { key: 'post-match',         label: 'Post Match',          s: 'startPostMatch',          f: 'finishPostMatch' },
  { key: 'other-dates',        label: 'Other Dates',         s: 'finishMatchDay',          f: 'finishBaseMatchDay',       sLabel: 'Close MD', fLabel: 'Change MD' },
  { key: 'allowed-dates',      label: 'Allowed Dates',       s: 'minAllowedRealMatchDate', f: 'maxAllowedRealMatchDate',  sLabel: 'Min', fLabel: 'Max' },
]

const currentTab = computed(() => tabs.find(t => t.key === activeTab.value) ?? tabs[0])

const fmtDate = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const diffStr = (s, f) => {
  if (!s || !f) return '—'
  const ms = new Date(f) - new Date(s)
  if (ms < 0) return '(*)'
  if (ms === 0) return '—'
  const d = Math.floor(ms / 86400000)
  const h = Math.floor((ms % 86400000) / 3600000)
  const m = Math.floor((ms % 3600000) / 60000)
  return (d ? `${d}d` : '') + (h ? `${h}h` : '') + (m ? `${m}m` : '') || '—'
}

const fmtMD = (symid, md) => (symid && md != null) ? `${symid}: ${md}` : '—'

async function fetchSeasons() {
  const res = await api.get('/api/v1/admin/match-day-statuses/seasons')
  seasons.value = res.data
  if (res.data.length > 0) selectedSeason.value = res.data[0]
}

async function fetchMapKeys() {
  if (!selectedSeason.value) return
  const res = await api.get('/api/v1/admin/match-day-statuses/map-keys', {
    params: { season_id: selectedSeason.value },
  })
  mapKeys.value = res.data
  selectedMapKey.value = res.data.length > 0 ? res.data[0] : null
}

async function fetchRows() {
  loading.value = true
  error.value = null
  try {
    const params = {}
    if (selectedSeason.value) params.season_id = selectedSeason.value
    if (selectedMapKey.value) params.match_day_map_key = selectedMapKey.value
    const res = await api.get('/api/v1/admin/match-day-statuses', { params })
    rows.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load match day statuses.'
  } finally {
    loading.value = false
  }
}

async function onSeasonChange() {
  await fetchMapKeys()
  await fetchRows()
}

async function onMapKeyChange() {
  await fetchRows()
}

onMounted(async () => {
  try {
    await fetchSeasons()
    await fetchMapKeys()
    await fetchRows()
  } catch (e) {
    error.value = 'Failed to initialize.'
    loading.value = false
  }
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton :icon="mdiCalendarCheck" title="Match Day Status" main />

      <!-- Selectors -->
      <div class="flex flex-wrap items-center gap-4 mb-4">
        <div class="flex items-center gap-2">
          <label class="text-sm font-medium text-gray-600 dark:text-slate-300">Season</label>
          <select
            v-model="selectedSeason"
            class="rounded border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-sm px-2 py-1 text-gray-700 dark:text-slate-200 min-w-[5rem]"
            @change="onSeasonChange"
          >
            <option v-for="s in seasons" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <div class="flex items-center gap-2">
          <label class="text-sm font-medium text-gray-600 dark:text-slate-300">Key</label>
          <select
            v-model="selectedMapKey"
            class="rounded border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-sm px-2 py-1 text-gray-700 dark:text-slate-200"
            @change="onMapKeyChange"
          >
            <option :value="null">— all —</option>
            <option v-for="k in mapKeys" :key="k" :value="k">{{ k }}</option>
          </select>
        </div>
      </div>

      <!-- Tab buttons -->
      <div class="flex flex-wrap gap-1 mb-3">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="px-2 py-1 rounded text-xs font-medium border transition-colors"
          :class="activeTab === tab.key
            ? 'bg-blue-600 text-white border-blue-600'
            : 'bg-white dark:bg-slate-800 text-gray-600 dark:text-slate-300 border-gray-300 dark:border-slate-600 hover:bg-gray-100 dark:hover:bg-slate-700'"
          @click="activeTab = tab.key"
        >{{ tab.label }}</button>
      </div>

      <p v-if="error" class="mb-4 text-red-500 text-sm">{{ error }}</p>

      <CardBox has-table class="overflow-x-auto">
        <table class="w-full text-xs whitespace-nowrap">
          <thead>
            <tr class="border-b border-gray-200 dark:border-slate-700">
              <th class="py-2 px-2 text-left font-semibold text-gray-600 dark:text-slate-300">ID</th>
              <th class="py-2 px-2 text-left font-semibold text-gray-600 dark:text-slate-300">Match Day</th>
              <th class="py-2 px-2 text-left font-semibold text-gray-600 dark:text-slate-300">Prev</th>
              <th class="py-2 px-2 text-left font-semibold text-gray-600 dark:text-slate-300">Next</th>
              <th class="py-2 px-2 text-center font-semibold text-gray-600 dark:text-slate-300">Act</th>
              <th class="py-2 px-2 text-center font-semibold text-gray-600 dark:text-slate-300">Ovr</th>
              <th class="py-2 px-2 text-left font-semibold text-gray-600 dark:text-slate-300">First</th>
              <th class="py-2 px-2 text-left font-semibold text-gray-600 dark:text-slate-300">Last</th>
              <th class="py-2 px-2 text-right font-semibold text-gray-600 dark:text-slate-300">Diff</th>
              <th class="py-2 px-2 text-left font-semibold text-blue-600 dark:text-blue-400">{{ currentTab.sLabel ?? 'Start' }}</th>
              <th class="py-2 px-2 text-left font-semibold text-blue-600 dark:text-blue-400">{{ currentTab.fLabel ?? 'Finish' }}</th>
              <th class="py-2 px-2 text-right font-semibold text-blue-600 dark:text-blue-400">Diff</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="12" class="py-4 px-2 text-gray-400">Loading…</td>
            </tr>
            <tr
              v-for="row in rows"
              :key="row.matchDayStatusID"
              class="border-b border-gray-50 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-700/30"
              :class="{ 'bg-blue-50 dark:bg-blue-900/10': row.active }"
            >
              <td class="py-1 px-2 text-gray-500 dark:text-slate-400">{{ row.matchDayStatusID }}</td>
              <td class="py-1 px-2 font-medium">{{ fmtMD(row.realCompetitionSYMID, row.realCompetitionMatchDay) }}</td>
              <td class="py-1 px-2 text-gray-500 dark:text-slate-400">{{ fmtMD(row.prevActiveRealCompetitionSYMID, row.prevActiveRealCompetitionMatchDay) }}</td>
              <td class="py-1 px-2 text-gray-500 dark:text-slate-400">{{ fmtMD(row.nextActiveRealCompetitionSYMID, row.nextActiveRealCompetitionMatchDay) }}</td>
              <td class="py-1 px-2 text-center">
                <span
                  class="rounded px-1.5 py-0.5 font-medium"
                  :class="row.active
                    ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'
                    : 'bg-gray-100 text-gray-400 dark:bg-slate-700 dark:text-slate-500'"
                >{{ row.active ? 'Yes' : 'No' }}</span>
              </td>
              <td class="py-1 px-2 text-center">
                <span v-if="row.overlapped" class="rounded px-1.5 py-0.5 bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300 font-medium">Yes</span>
                <span v-else class="text-gray-400">No</span>
              </td>
              <td class="py-1 px-2 text-gray-500 dark:text-slate-400">{{ fmtDate(row.minRealMatchDate) }}</td>
              <td class="py-1 px-2 text-gray-500 dark:text-slate-400">{{ fmtDate(row.maxRealMatchDate) }}</td>
              <td class="py-1 px-2 text-right text-gray-400">{{ diffStr(row.minRealMatchDate, row.maxRealMatchDate) }}</td>
              <td class="py-1 px-2 text-blue-700 dark:text-blue-300">{{ fmtDate(row[currentTab.s]) }}</td>
              <td class="py-1 px-2 text-blue-700 dark:text-blue-300">{{ fmtDate(row[currentTab.f]) }}</td>
              <td class="py-1 px-2 text-right text-blue-500 dark:text-blue-400">{{ diffStr(row[currentTab.s], row[currentTab.f]) }}</td>
            </tr>
          </tbody>
        </table>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
