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

const leagues = ref([])
const loading = ref(true)
const error = ref(null)

const userId = computed(() => route.query.userId ? Number(route.query.userId) : null)
const title = computed(() => userId.value ? `Leagues — user #${userId.value}` : 'Leagues')

onMounted(async () => {
  try {
    const params = userId.value ? { user_id: userId.value } : {}
    const res = await api.get('/api/v1/admin/leagues', { params })
    leagues.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load leagues.'
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
          v-if="userId"
          class="flex items-center gap-1 rounded px-3 py-1 text-sm font-medium bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
          @click="router.push({ name: 'user-detail', params: { id: userId } })"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current" xmlns="http://www.w3.org/2000/svg">
            <path :d="mdiArrowLeft" />
          </svg>
          User
        </button>
      </SectionTitleLineWithButton>

      <p v-if="error" class="mb-4 text-red-500">{{ error }}</p>

      <CardBox has-table>
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-100 dark:border-slate-700">
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">ID</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">League</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 hidden lg:table-cell">Season</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 hidden lg:table-cell">Season #</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 hidden lg:table-cell">Divisions</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 hidden lg:table-cell">Commissioner ID</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="6" class="py-4 px-3 text-gray-400">Loading…</td>
            </tr>
            <tr
              v-for="league in leagues"
              :key="league.leagueID"
              class="border-b border-gray-50 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-700/30 cursor-pointer"
            >
              <td class="py-2 px-3 font-mono text-xs text-gray-400">{{ league.leagueID }}</td>
              <td class="py-2 px-3 font-medium">{{ league.leagueName }}</td>
              <td class="py-2 px-3 text-gray-500 dark:text-slate-400 hidden lg:table-cell">{{ league.season }}</td>
              <td class="py-2 px-3 text-gray-500 dark:text-slate-400 hidden lg:table-cell">{{ league.seasonNum }}</td>
              <td class="py-2 px-3 text-gray-500 dark:text-slate-400 hidden lg:table-cell">{{ league.numDivisions }}</td>
              <td class="py-2 px-3 font-mono text-xs text-gray-400 hidden lg:table-cell">{{ league.commissionerID }}</td>
            </tr>
          </tbody>
        </table>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
