<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { mdiTrophy, mdiArrowLeft } from '@mdi/js'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import CardBox from '@/components/CardBox.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import api from '@/api.js'

const route = useRoute()
const router = useRouter()

const comp = ref(null)
const loading = ref(true)
const error = ref(null)

onMounted(async () => {
  try {
    const res = await api.get(`/api/v1/admin/real-competitions/${route.params.id}`)
    comp.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load competition.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton :icon="mdiTrophy" :title="comp ? comp.realCompetitionName : 'Competition Detail'" main>
        <button
          class="flex items-center gap-1 rounded px-3 py-1 text-sm font-medium bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
          @click="router.push({ name: 'real-competitions' })"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
            <path :d="mdiArrowLeft" />
          </svg>
          Competitions
        </button>
      </SectionTitleLineWithButton>

      <p v-if="error" class="mb-4 text-red-500">{{ error }}</p>
      <p v-else-if="loading" class="text-gray-400">Loading…</p>

      <template v-else-if="comp">
        <CardBox class="mb-4">
          <table class="w-full text-sm">
            <tbody>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 w-48 font-semibold text-gray-500 dark:text-slate-400">ID</td>
                <td class="py-2 px-3 font-mono text-xs text-gray-400">{{ comp.realCompetitionID }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">UID</td>
                <td class="py-2 px-3 font-mono text-xs text-gray-400">{{ comp.realCompetitionUID || '—' }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">SYMID</td>
                <td class="py-2 px-3 font-mono text-xs font-medium">{{ comp.realCompetitionSYMID || '—' }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Name</td>
                <td class="py-2 px-3">{{ comp.realCompetitionName }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Country</td>
                <td class="py-2 px-3">{{ comp.realCompetitionCountry || '—' }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Season ID</td>
                <td class="py-2 px-3">{{ comp.realCompetitionSeasonId }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Season Name</td>
                <td class="py-2 px-3">{{ comp.realCompetitionSeasonName || '—' }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Last Match Day</td>
                <td class="py-2 px-3">{{ comp.realCompetitionLastMatchDay ?? '—' }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Base Competition ID</td>
                <td class="py-2 px-3 font-mono text-xs text-gray-400">{{ comp.baseRealCompetitionID ?? '—' }}</td>
              </tr>
              <tr>
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Extra Competition ID</td>
                <td class="py-2 px-3 font-mono text-xs text-gray-400">{{ comp.extraRealCompetitionID ?? '—' }}</td>
              </tr>
            </tbody>
          </table>
        </CardBox>

        <div class="flex gap-2 flex-wrap">
          <button
            class="rounded px-3 py-1.5 text-sm font-medium bg-blue-50 text-blue-600 hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400 dark:hover:bg-blue-900/50"
            @click="router.push({ name: 'real-matches', query: { key: comp.realCompetitionSYMID + '|' + comp.realCompetitionSeasonId } })"
          >Matches</button>
          <button
            class="rounded px-3 py-1.5 text-sm font-medium bg-green-50 text-green-600 hover:bg-green-100 dark:bg-green-900/30 dark:text-green-400 dark:hover:bg-green-900/50"
            @click="router.push({ name: 'real-team-members', query: { season_id: comp.realCompetitionSeasonId } })"
          >Members</button>
          <button
            class="rounded px-3 py-1.5 text-sm font-medium bg-purple-50 text-purple-600 hover:bg-purple-100 dark:bg-purple-900/30 dark:text-purple-400 dark:hover:bg-purple-900/50"
            @click="router.push({ name: 'real-standings', query: { season_id: comp.realCompetitionSeasonId } })"
          >Standings</button>
        </div>
      </template>
    </SectionMain>
  </LayoutAuthenticated>
</template>
