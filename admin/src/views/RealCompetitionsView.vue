<script setup>
import { ref, onMounted } from 'vue'
import { mdiTrophy } from '@mdi/js'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import CardBox from '@/components/CardBox.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import api from '@/api.js'

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
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">UID</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">SYMID</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">Name</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 hidden md:table-cell">Country</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">Season</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 hidden lg:table-cell">Season name</th>
              <th class="py-2 px-3 text-right font-semibold text-gray-600 dark:text-slate-300">Last MD</th>
              <th class="py-2 px-3 text-right font-semibold text-gray-600 dark:text-slate-300 hidden xl:table-cell">Base ID</th>
              <th class="py-2 px-3 text-right font-semibold text-gray-600 dark:text-slate-300 hidden xl:table-cell">Extra ID</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="10" class="py-4 px-3 text-gray-400">Loading…</td>
            </tr>
            <tr
              v-for="row in rows"
              :key="row.realCompetitionID"
              class="border-b border-gray-50 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-700/30"
            >
              <td class="py-2 px-3 text-gray-500 dark:text-slate-400">{{ row.realCompetitionID }}</td>
              <td class="py-2 px-3 font-mono text-xs text-gray-500 dark:text-slate-400">{{ row.realCompetitionUID }}</td>
              <td class="py-2 px-3 font-mono text-xs font-medium">{{ row.realCompetitionSYMID }}</td>
              <td class="py-2 px-3">{{ row.realCompetitionName }}</td>
              <td class="py-2 px-3 text-gray-500 dark:text-slate-400 hidden md:table-cell">{{ row.realCompetitionCountry }}</td>
              <td class="py-2 px-3 text-gray-600 dark:text-slate-300">{{ row.realCompetitionSeasonId }}</td>
              <td class="py-2 px-3 text-gray-500 dark:text-slate-400 hidden lg:table-cell">{{ row.realCompetitionSeasonName }}</td>
              <td class="py-2 px-3 text-right">{{ row.realCompetitionLastMatchDay }}</td>
              <td class="py-2 px-3 text-right text-gray-400 hidden xl:table-cell">{{ row.baseRealCompetitionID ?? '—' }}</td>
              <td class="py-2 px-3 text-right text-gray-400 hidden xl:table-cell">{{ row.extraRealCompetitionID ?? '—' }}</td>
            </tr>
          </tbody>
        </table>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
