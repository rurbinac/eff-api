<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { mdiSoccerField, mdiArrowLeft } from '@mdi/js'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import CardBox from '@/components/CardBox.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import api from '@/api.js'

const route = useRoute()
const router = useRouter()

const leagueId = computed(() => Number(route.params.id))
const leagueName = computed(() => route.query.name || `League #${leagueId.value}`)
const title = computed(() => `${leagueName.value} — Matches`)

const rows = ref([])
const loading = ref(true)
const error = ref(null)

const matchDays = computed(() => [...new Set(rows.value.map(r => r.competitionMatchDay))].sort((a, b) => a - b))
const selectedMatchDay = ref(null)

const filtered = computed(() =>
  selectedMatchDay.value == null ? rows.value : rows.value.filter(r => r.competitionMatchDay === selectedMatchDay.value)
)

const statusLabel = (s) => {
  const map = { 0: 'Pending', 1: 'Active', 2: 'Done', 3: 'Cancelled' }
  return map[s] ?? String(s)
}

onMounted(async () => {
  try {
    const res = await api.get(`/api/v1/admin/leagues/${leagueId.value}/matches`, {
      params: { competition_type: 3 },
    })
    rows.value = res.data
    if (res.data.length) selectedMatchDay.value = res.data[res.data.length - 1].competitionMatchDay
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load matches.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton :icon="mdiSoccerField" :title="title" main>
        <button
          class="flex items-center gap-1 rounded px-3 py-1 text-sm font-medium bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
          @click="router.push({ name: 'leagues' })"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current"><path :d="mdiArrowLeft" /></svg>
          Leagues
        </button>
      </SectionTitleLineWithButton>

      <p v-if="error" class="mb-4 text-sm text-red-500">{{ error }}</p>

      <div v-if="!loading && matchDays.length" class="mb-4 flex items-center gap-3 flex-wrap">
        <label class="text-sm font-medium text-gray-600 dark:text-slate-300">Match Day</label>
        <select
          :value="selectedMatchDay"
          class="text-sm border border-gray-300 dark:border-slate-600 rounded px-2 py-1 bg-white dark:bg-slate-800"
          @change="selectedMatchDay = Number($event.target.value)"
        >
          <option :value="null">All</option>
          <option v-for="md in matchDays" :key="md" :value="md">MD {{ md }}</option>
        </select>
        <span class="text-xs text-gray-400">{{ filtered.length }} match{{ filtered.length === 1 ? '' : 'es' }}</span>
      </div>

      <CardBox has-table>
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-100 dark:border-slate-700">
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">ID</th>
              <th class="py-2 px-3 text-right font-semibold text-gray-600 dark:text-slate-300 hidden md:table-cell">MD</th>
              <th class="py-2 px-3 text-right font-semibold text-gray-600 dark:text-slate-300 hidden lg:table-cell">Division</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">Home</th>
              <th class="py-2 px-3 text-center font-semibold text-gray-600 dark:text-slate-300">Score</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">Away</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 hidden lg:table-cell">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="7" class="py-4 px-3 text-gray-400">Loading…</td>
            </tr>
            <tr v-else-if="!filtered.length">
              <td colspan="7" class="py-4 px-3 text-gray-400">No matches.</td>
            </tr>
            <tr
              v-for="m in filtered"
              :key="m.matchID"
              class="border-b border-gray-50 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-700/30"
            >
              <td class="py-2 px-3 font-mono text-xs text-gray-400">{{ m.matchID }}</td>
              <td class="py-2 px-3 text-right text-gray-500 dark:text-slate-400 hidden md:table-cell">{{ m.competitionMatchDay ?? '—' }}</td>
              <td class="py-2 px-3 text-right font-mono text-xs text-gray-400 hidden lg:table-cell">{{ m.divisionID }}</td>
              <td class="py-2 px-3 font-medium text-gray-800 dark:text-slate-200">{{ m.homeName || '—' }}</td>
              <td class="py-2 px-3 text-center font-mono font-bold text-gray-900 dark:text-slate-100 whitespace-nowrap">
                {{ m.homeScore ?? '?' }} – {{ m.awayScore ?? '?' }}
              </td>
              <td class="py-2 px-3 font-medium text-gray-800 dark:text-slate-200">{{ m.awayName || '—' }}</td>
              <td class="py-2 px-3 hidden lg:table-cell">
                <span class="text-xs font-medium px-1.5 py-0.5 rounded"
                  :class="{
                    'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400': m.matchStatus === 2,
                    'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400': m.matchStatus === 1,
                    'bg-gray-100 text-gray-600 dark:bg-slate-700 dark:text-slate-300': m.matchStatus === 0,
                  }"
                >{{ statusLabel(m.matchStatus) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
