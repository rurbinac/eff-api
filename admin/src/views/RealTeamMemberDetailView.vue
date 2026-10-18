<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { mdiAccountMultiple, mdiArrowLeft } from '@mdi/js'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import CardBox from '@/components/CardBox.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import api from '@/api.js'

const route = useRoute()
const router = useRouter()

const member = ref(null)
const loading = ref(true)
const error = ref(null)

const title = computed(() => member.value?.name || 'Player Detail')

const fmtDate = (iso) => {
  if (!iso) return '—'
  return iso.replace('T', ' ').replace(/\.\d+.*$/, '')
}

onMounted(async () => {
  try {
    const res = await api.get(`/api/v1/admin/real-team-members/${route.params.key}`)
    member.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load member.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton :icon="mdiAccountMultiple" :title="title" main>
        <button
          class="flex items-center gap-1 rounded px-3 py-1 text-sm font-medium bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
          @click="router.back()"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current"><path :d="mdiArrowLeft" /></svg>
          Back
        </button>
      </SectionTitleLineWithButton>

      <p v-if="error" class="mb-4 text-red-500">{{ error }}</p>
      <p v-else-if="loading" class="text-gray-400">Loading…</p>

      <template v-else-if="member">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">

          <!-- Identity -->
          <CardBox>
            <div class="px-3 py-2 border-b border-gray-100 dark:border-slate-700 font-semibold text-sm text-gray-700 dark:text-slate-200">Identity</div>
            <table class="w-full text-sm">
              <tbody>
                <tr class="border-b border-gray-50 dark:border-slate-800">
                  <td class="py-1.5 px-3 w-36 text-gray-500 dark:text-slate-400">Key</td>
                  <td class="py-1.5 px-3 font-mono text-xs">{{ member.realTeamMemberKey }}</td>
                </tr>
                <tr class="border-b border-gray-50 dark:border-slate-800">
                  <td class="py-1.5 px-3 text-gray-500 dark:text-slate-400">Name</td>
                  <td class="py-1.5 px-3 font-medium">{{ member.name }}</td>
                </tr>
                <tr v-if="member.knownName" class="border-b border-gray-50 dark:border-slate-800">
                  <td class="py-1.5 px-3 text-gray-500 dark:text-slate-400">Known as</td>
                  <td class="py-1.5 px-3">{{ member.knownName }}</td>
                </tr>
                <tr class="border-b border-gray-50 dark:border-slate-800">
                  <td class="py-1.5 px-3 text-gray-500 dark:text-slate-400">First / Last</td>
                  <td class="py-1.5 px-3">{{ member.firstName || '—' }} {{ member.lastName || '' }}</td>
                </tr>
                <tr class="border-b border-gray-50 dark:border-slate-800">
                  <td class="py-1.5 px-3 text-gray-500 dark:text-slate-400">Position</td>
                  <td class="py-1.5 px-3">{{ member.position || '—' }} <span v-if="member.draftPosition" class="text-gray-400 text-xs">({{ member.draftPosition }})</span></td>
                </tr>
                <tr class="border-b border-gray-50 dark:border-slate-800">
                  <td class="py-1.5 px-3 text-gray-500 dark:text-slate-400">Jersey #</td>
                  <td class="py-1.5 px-3">{{ member.jerseyNumber ?? '—' }}</td>
                </tr>
                <tr class="border-b border-gray-50 dark:border-slate-800">
                  <td class="py-1.5 px-3 text-gray-500 dark:text-slate-400">Birth date</td>
                  <td class="py-1.5 px-3">{{ member.birthDate || '—' }}</td>
                </tr>
                <tr class="border-b border-gray-50 dark:border-slate-800">
                  <td class="py-1.5 px-3 text-gray-500 dark:text-slate-400">Height / Weight</td>
                  <td class="py-1.5 px-3">{{ member.height ?? '—' }} cm / {{ member.weight ?? '—' }} kg</td>
                </tr>
                <tr>
                  <td class="py-1.5 px-3 text-gray-500 dark:text-slate-400">Enabled</td>
                  <td class="py-1.5 px-3">{{ member.enabled ? 'Yes' : 'No' }}</td>
                </tr>
              </tbody>
            </table>
          </CardBox>

          <!-- Team & Competition -->
          <CardBox>
            <div class="px-3 py-2 border-b border-gray-100 dark:border-slate-700 font-semibold text-sm text-gray-700 dark:text-slate-200">Team &amp; Competition</div>
            <table class="w-full text-sm">
              <tbody>
                <tr class="border-b border-gray-50 dark:border-slate-800">
                  <td class="py-1.5 px-3 w-36 text-gray-500 dark:text-slate-400">Team</td>
                  <td class="py-1.5 px-3 font-medium">{{ member.realTeamName }} <span v-if="member.realTeamShortName" class="text-xs text-gray-400">({{ member.realTeamShortName }})</span></td>
                </tr>
                <tr class="border-b border-gray-50 dark:border-slate-800">
                  <td class="py-1.5 px-3 text-gray-500 dark:text-slate-400">Competition</td>
                  <td class="py-1.5 px-3">{{ member.realCompetitionName }}</td>
                </tr>
                <tr class="border-b border-gray-50 dark:border-slate-800">
                  <td class="py-1.5 px-3 text-gray-500 dark:text-slate-400">SYMID</td>
                  <td class="py-1.5 px-3 font-mono text-xs">{{ member.realCompetitionSYMID }}</td>
                </tr>
                <tr class="border-b border-gray-50 dark:border-slate-800">
                  <td class="py-1.5 px-3 text-gray-500 dark:text-slate-400">Season</td>
                  <td class="py-1.5 px-3">{{ member.realCompetitionSeasonId }}</td>
                </tr>
                <tr class="border-b border-gray-50 dark:border-slate-800">
                  <td class="py-1.5 px-3 text-gray-500 dark:text-slate-400">Player ID</td>
                  <td class="py-1.5 px-3 font-mono text-xs text-gray-400">{{ member.realPlayerID ?? '—' }}</td>
                </tr>
                <tr class="border-b border-gray-50 dark:border-slate-800">
                  <td class="py-1.5 px-3 text-gray-500 dark:text-slate-400">Last F7</td>
                  <td class="py-1.5 px-3 font-mono text-xs text-gray-400">{{ fmtDate(member.lastF7Date) }}</td>
                </tr>
                <tr>
                  <td class="py-1.5 px-3 text-gray-500 dark:text-slate-400">Last F42</td>
                  <td class="py-1.5 px-3 font-mono text-xs text-gray-400">{{ fmtDate(member.lastF42Date) }}</td>
                </tr>
              </tbody>
            </table>
          </CardBox>
        </div>

        <!-- Season stats -->
        <CardBox>
          <div class="px-3 py-2 border-b border-gray-100 dark:border-slate-700 font-semibold text-sm text-gray-700 dark:text-slate-200">Season Stats</div>
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-0 divide-x divide-gray-100 dark:divide-slate-700">
            <div v-for="stat in [
              { label: 'Ranking', value: member.ranking ?? '—' },
              { label: 'Points L1', value: member.pointsL1 ?? '—' },
              { label: 'Played', value: member.gamePlayed ?? '—' },
              { label: 'Goals', value: member.goals ?? '—' },
              { label: 'Assists', value: member.assists ?? '—' },
              { label: 'Yellow', value: member.yellowCards ?? '—' },
              { label: 'Red', value: member.redCards ?? '—' },
              { label: 'Clean Sheet', value: member.cleanSheet ?? '—' },
              { label: 'Goals Conc.', value: member.goalsConceded ?? '—' },
              { label: 'Time (min)', value: member.timePlayed ?? '—' },
            ]" :key="stat.label" class="px-4 py-3 text-center">
              <div class="text-lg font-bold text-gray-800 dark:text-slate-100">{{ stat.value }}</div>
              <div class="text-xs text-gray-500 dark:text-slate-400 mt-0.5">{{ stat.label }}</div>
            </div>
          </div>
        </CardBox>
      </template>
    </SectionMain>
  </LayoutAuthenticated>
</template>
