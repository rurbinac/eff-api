<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { mdiTrophy } from '@mdi/js'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import CardBox from '@/components/CardBox.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import api from '@/api.js'

const router = useRouter()

const rows = ref([])
const loading = ref(true)
const error = ref(null)

onMounted(async () => {
  try {
    const res = await api.get('/api/v1/admin/real-competitions')
    rows.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load real competitions.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton :icon="mdiTrophy" title="Real Competitions" main />

      <p v-if="error" class="mb-4 text-sm text-red-500">{{ error }}</p>

      <CardBox has-table>
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-100 dark:border-slate-700">
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">ID</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">Name</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 hidden md:table-cell">Country</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">Season</th>
              <th class="py-2 px-3 text-right font-semibold text-gray-600 dark:text-slate-300">Last MD</th>
              <th class="py-2 px-3 text-right font-semibold text-gray-600 dark:text-slate-300 hidden xl:table-cell">Base ID</th>
              <th class="py-2 px-3 text-right font-semibold text-gray-600 dark:text-slate-300 hidden xl:table-cell">Extra ID</th>
              <th class="py-2 px-3"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="8" class="py-4 px-3 text-gray-400">Loading…</td>
            </tr>
            <tr
              v-for="row in rows"
              :key="row.realCompetitionID"
              class="border-b border-gray-50 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-700/30"
            >
              <td class="py-2 px-3 text-gray-500 dark:text-slate-400">{{ row.realCompetitionID }}</td>
              <td class="py-2 px-3">{{ row.realCompetitionName }}</td>
              <td class="py-2 px-3 text-gray-500 dark:text-slate-400 hidden md:table-cell">{{ row.realCompetitionCountry }}</td>
              <td class="py-2 px-3 text-gray-600 dark:text-slate-300">{{ row.realCompetitionSeasonId }}</td>
              <td class="py-2 px-3 text-right">{{ row.realCompetitionLastMatchDay }}</td>
              <td class="py-2 px-3 text-right text-gray-400 hidden xl:table-cell">{{ row.baseRealCompetitionID ?? '—' }}</td>
              <td class="py-2 px-3 text-right text-gray-400 hidden xl:table-cell">{{ row.extraRealCompetitionID ?? '—' }}</td>
              <td class="py-2 px-3">
                <div class="flex items-center gap-1 flex-wrap justify-end">
                  <button
                    class="rounded px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600 whitespace-nowrap"
                    @click="router.push({ name: 'real-competition-detail', params: { id: row.realCompetitionID } })"
                  >Detail</button>
                  <button
                    class="rounded px-2 py-0.5 text-xs font-medium bg-blue-50 text-blue-600 hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400 dark:hover:bg-blue-900/50 whitespace-nowrap"
                    @click="router.push({ name: 'real-matches', query: { key: row.realCompetitionSYMID + '|' + row.realCompetitionSeasonId } })"
                  >Matches</button>
                  <button
                    class="rounded px-2 py-0.5 text-xs font-medium bg-green-50 text-green-600 hover:bg-green-100 dark:bg-green-900/30 dark:text-green-400 dark:hover:bg-green-900/50 whitespace-nowrap"
                    @click="router.push({ name: 'real-team-members', query: { season_id: row.realCompetitionSeasonId } })"
                  >Members</button>
                  <button
                    class="rounded px-2 py-0.5 text-xs font-medium bg-purple-50 text-purple-600 hover:bg-purple-100 dark:bg-purple-900/30 dark:text-purple-400 dark:hover:bg-purple-900/50 whitespace-nowrap"
                    @click="router.push({ name: 'real-standings', query: { season_id: row.realCompetitionSeasonId } })"
                  >Standings</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
