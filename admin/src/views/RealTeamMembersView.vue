<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { mdiAccountMultiple } from '@mdi/js'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import CardBox from '@/components/CardBox.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import api from '@/api.js'

const route = useRoute()
const seasons = ref([])
const selectedSeason = ref('')
const rows = ref([])
const loading = ref(false)
const error = ref(null)

async function fetchMembers(season) {
  if (!season) return
  loading.value = true
  error.value = null
  rows.value = []
  try {
    const res = await api.get('/api/v1/admin/real-team-members', { params: { season_id: season } })
    rows.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load team members.'
  } finally {
    loading.value = false
  }
}

function onSeasonChange(e) {
  selectedSeason.value = e.target.value
  fetchMembers(selectedSeason.value)
}

onMounted(async () => {
  try {
    const res = await api.get('/api/v1/admin/real-team-members/seasons')
    seasons.value = res.data
    if (res.data.length) {
      const querySeason = route.query.season_id
      selectedSeason.value = (querySeason && res.data.includes(querySeason))
        ? querySeason
        : res.data[0]
      fetchMembers(selectedSeason.value)
    }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load seasons.'
  }
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton :icon="mdiAccountMultiple" title="Real Team Members" main />

      <div class="mb-4 flex items-center gap-3 flex-wrap">
        <label class="text-sm font-medium text-gray-600 dark:text-slate-300">Season</label>
        <select
          :value="selectedSeason"
          class="text-sm border border-gray-300 dark:border-slate-600 rounded px-2 py-1 bg-white dark:bg-slate-800 min-w-[6rem]"
          @change="onSeasonChange"
        >
          <option v-for="s in seasons" :key="s" :value="s">{{ s }}</option>
        </select>
        <span v-if="loading" class="text-sm text-gray-400">Loading…</span>
        <span v-if="!loading && rows.length" class="text-sm text-gray-400">{{ rows.length }} members</span>
      </div>

      <p v-if="error" class="mb-4 text-sm text-red-500">{{ error }}</p>

      <CardBox has-table>
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-100 dark:border-slate-700">
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">Key</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">Name</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">Position</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">Team</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading && !rows.length">
              <td colspan="4" class="py-4 px-3 text-gray-400">Loading…</td>
            </tr>
            <tr v-else-if="!loading && !rows.length">
              <td colspan="4" class="py-4 px-3 text-gray-400">No members found.</td>
            </tr>
            <tr
              v-for="row in rows"
              :key="row.key"
              class="border-b border-gray-50 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-700/30"
            >
              <td class="py-2 px-3 font-mono text-xs font-medium text-gray-700 dark:text-slate-300">{{ row.key }}</td>
              <td class="py-2 px-3 text-gray-800 dark:text-slate-200">{{ row.name }}</td>
              <td class="py-2 px-3 text-gray-500 dark:text-slate-400">{{ row.position ?? '—' }}</td>
              <td class="py-2 px-3 text-gray-600 dark:text-slate-300">
                {{ row.teamName }}
                <span v-if="row.teamShortName" class="text-gray-400 dark:text-slate-500 font-mono text-xs">({{ row.teamShortName }})</span>
              </td>
            </tr>
          </tbody>
        </table>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
