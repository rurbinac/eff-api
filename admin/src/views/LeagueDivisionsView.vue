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
const title = computed(() => `${leagueName.value} — Divisions`)

const rows = ref([])
const loading = ref(true)
const error = ref(null)

const draftStatusLabel = (s) => {
  const map = { 0: 'Not drafted', 1: 'Drafting', 2: 'Drafted', 3: 'Paused' }
  return map[s] ?? String(s)
}

const fmtDate = (iso) => {
  if (!iso) return '—'
  return iso.replace('T', ' ').replace(/\.\d+.*$/, '')
}

onMounted(async () => {
  try {
    const res = await api.get(`/api/v1/admin/leagues/${leagueId.value}/divisions`)
    rows.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load divisions.'
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

      <CardBox has-table>
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-100 dark:border-slate-700">
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">ID</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 hidden md:table-cell">Type</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">Draft Status</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 hidden lg:table-cell">Draft Date</th>
              <th class="py-2 px-3 text-right font-semibold text-gray-600 dark:text-slate-300">Teams</th>
              <th class="py-2 px-3 text-right font-semibold text-gray-600 dark:text-slate-300 hidden md:table-cell">Match Day</th>
              <th class="py-2 px-3 text-right font-semibold text-gray-600 dark:text-slate-300 hidden lg:table-cell">MD Range</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 hidden xl:table-cell">Commissioner</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="8" class="py-4 px-3 text-gray-400">Loading…</td>
            </tr>
            <tr
              v-for="div in rows"
              :key="div.divisionID"
              class="border-b border-gray-50 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-700/30"
            >
              <td class="py-2 px-3 font-mono text-xs text-gray-400">{{ div.divisionID }}</td>
              <td class="py-2 px-3 text-gray-500 dark:text-slate-400 hidden md:table-cell">{{ div.divisionType }}</td>
              <td class="py-2 px-3">
                <span
                  class="text-xs font-medium px-1.5 py-0.5 rounded"
                  :class="{
                    'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400': div.draftStatus === 2,
                    'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400': div.draftStatus === 1,
                    'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400': div.draftStatus === 3,
                    'bg-gray-100 text-gray-600 dark:bg-slate-700 dark:text-slate-300': div.draftStatus === 0,
                  }"
                >{{ draftStatusLabel(div.draftStatus) }}</span>
              </td>
              <td class="py-2 px-3 font-mono text-xs text-gray-500 dark:text-slate-400 hidden lg:table-cell">{{ fmtDate(div.draftDate) }}</td>
              <td class="py-2 px-3 text-right text-gray-600 dark:text-slate-300">{{ div.numTeams }} / {{ div.totalTeams }}</td>
              <td class="py-2 px-3 text-right text-gray-600 dark:text-slate-300 hidden md:table-cell">{{ div.matchDay ?? '—' }}</td>
              <td class="py-2 px-3 text-right text-xs text-gray-400 hidden lg:table-cell">{{ div.firstRealCompetitionMatchDay ?? '—' }}–{{ div.lastRealCompetitionMatchDay ?? '—' }}</td>
              <td class="py-2 px-3 font-mono text-xs text-gray-400 hidden xl:table-cell">{{ div.commissionerID }}</td>
            </tr>
          </tbody>
        </table>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
