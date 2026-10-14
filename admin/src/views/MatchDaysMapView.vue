<script setup>
import { ref, onMounted } from 'vue'
import { mdiCalendarMultiple } from '@mdi/js'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import CardBox from '@/components/CardBox.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import api from '@/api.js'

const groups = ref([])
const rows = ref([])
const loading = ref(false)
const error = ref(null)
const selectedGroup = ref(null)

const groupLabel = (g) =>
  `${g.realCompetitionSYMID} ${g.realCompetitionSeasonId}: ${g.firstRealCompetitionMatchDay}`

async function fetchGroups() {
  const res = await api.get('/api/v1/admin/match-days-map/groups')
  groups.value = res.data
  if (res.data.length > 0) selectedGroup.value = res.data[0]
}

async function fetchRows() {
  if (!selectedGroup.value) return
  loading.value = true
  error.value = null
  try {
    const g = selectedGroup.value
    const res = await api.get('/api/v1/admin/match-days-map', {
      params: {
        symid: g.realCompetitionSYMID,
        season_id: g.realCompetitionSeasonId,
        first_md: g.firstRealCompetitionMatchDay,
      },
    })
    rows.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load.'
  } finally {
    loading.value = false
  }
}

async function onGroupChange() {
  await fetchRows()
}

onMounted(async () => {
  try {
    await fetchGroups()
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
      <SectionTitleLineWithButton :icon="mdiCalendarMultiple" title="Match Days Map" main />

      <!-- Group selector -->
      <div class="flex items-center gap-2 mb-4">
        <label class="text-sm font-medium text-gray-600 dark:text-slate-300">Groups</label>
        <select
          v-model="selectedGroup"
          class="rounded border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-sm px-2 py-1 text-gray-700 dark:text-slate-200 min-w-[12rem]"
          @change="onGroupChange"
        >
          <option v-for="g in groups" :key="groupLabel(g)" :value="g">{{ groupLabel(g) }}</option>
        </select>
      </div>

      <p v-if="error" class="mb-4 text-red-500 text-sm">{{ error }}</p>

      <CardBox has-table>
        <table class="w-full text-xs">
          <thead>
            <tr class="border-b border-gray-200 dark:border-slate-700">
              <th rowspan="2" class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 align-bottom">ID</th>
              <th colspan="6" class="py-1 px-3 text-center font-semibold text-gray-600 dark:text-slate-300 border-b border-gray-100 dark:border-slate-700">Fantasy</th>
              <th colspan="2" class="py-1 px-3 text-center font-semibold text-gray-600 dark:text-slate-300 border-b border-gray-100 dark:border-slate-700">Real</th>
            </tr>
            <tr class="border-b border-gray-200 dark:border-slate-700">
              <th class="py-1 px-3 text-left font-semibold text-gray-500 dark:text-slate-400">Competition</th>
              <th class="py-1 px-3 text-right font-semibold text-gray-500 dark:text-slate-400">Min Teams</th>
              <th class="py-1 px-3 text-right font-semibold text-gray-500 dark:text-slate-400">Max Teams</th>
              <th class="py-1 px-3 text-right font-semibold text-gray-500 dark:text-slate-400">Rounds</th>
              <th class="py-1 px-3 text-right font-semibold text-gray-500 dark:text-slate-400">Match days</th>
              <th class="py-1 px-3 text-right font-semibold text-gray-500 dark:text-slate-400">Match day</th>
              <th class="py-1 px-3 text-left font-semibold text-gray-500 dark:text-slate-400">Competition</th>
              <th class="py-1 px-3 text-right font-semibold text-gray-500 dark:text-slate-400">MD</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="9" class="py-4 px-3 text-gray-400">Loading…</td>
            </tr>
            <tr
              v-for="row in rows"
              :key="row.matchDayMapID"
              class="border-b border-gray-50 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-700/30"
            >
              <td class="py-1 px-3 text-gray-400 dark:text-slate-500">{{ row.matchDayMapID }}</td>
              <td class="py-1 px-3 text-gray-400 dark:text-slate-500">{{ row.competitionType ?? '?' }}</td>
              <td class="py-1 px-3 text-right">{{ row.minNumTeams }}</td>
              <td class="py-1 px-3 text-right">{{ row.maxNumTeams }}</td>
              <td class="py-1 px-3 text-right">{{ row.rounds }}</td>
              <td class="py-1 px-3 text-right">{{ row.totalMatchDays }}</td>
              <td class="py-1 px-3 text-right font-medium">{{ row.matchDay }}</td>
              <td class="py-1 px-3 text-gray-600 dark:text-slate-300">{{ row.realCompetitionSYMID }} - {{ row.realCompetitionSeasonId }}</td>
              <td class="py-1 px-3 text-right font-medium">{{ row.realCompetitionMatchDay }}</td>
            </tr>
          </tbody>
        </table>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
