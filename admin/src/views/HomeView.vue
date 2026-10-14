<script setup>
import { ref, onMounted } from 'vue'
import { mdiMonitor, mdiSoccerField, mdiDatabaseArrowUp, mdiShieldAccount, mdiTrophy, mdiCalendarCheck } from '@mdi/js'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import CardBoxWidget from '@/components/CardBoxWidget.vue'
import CardBox from '@/components/CardBox.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import { useAuthStore } from '@/stores/auth.js'
import { useRouter } from 'vue-router'
import api from '@/api.js'

const auth = useAuthStore()
const router = useRouter()
const competitions = ref(null)

function fmtDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' })
}

onMounted(async () => {
  try {
    const res = await api.get('/api/v1/admin/competitions')
    competitions.value = res.data
  } catch {
    // non-critical
  }
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton :icon="mdiMonitor" title="Dashboard" main />

      <p class="mb-6 text-gray-500 dark:text-slate-400">
        Welcome, {{ auth.userName }}. Select a section to get started.
      </p>

      <!-- Quick access cards -->
      <div class="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <CardBoxWidget
          color="text-blue-500"
          :icon="mdiSoccerField"
          label="Leagues & Divisions"
          :number="null"
          trend="Manage draft settings and team order"
          trend-type="info"
          class="cursor-pointer"
          @click="router.push('/leagues')"
        />
        <CardBoxWidget
          color="text-emerald-500"
          :icon="mdiDatabaseArrowUp"
          label="Backup"
          :number="null"
          trend="Trigger and restore Cloud SQL backups"
          trend-type="info"
          class="cursor-pointer"
          @click="router.push('/backup')"
        />
      </div>

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <!-- Session -->
        <div>
          <SectionTitleLineWithButton :icon="mdiShieldAccount" title="Session" />
          <CardBox>
            <table class="w-full text-sm">
              <tbody>
                <tr class="border-b border-gray-100 dark:border-slate-700">
                  <td class="py-2 pr-4 font-medium text-gray-500 dark:text-slate-400 w-40">Sign-in time</td>
                  <td class="py-2">{{ fmtDate(auth.user?.signinTime) }}</td>
                </tr>
                <tr class="border-b border-gray-100 dark:border-slate-700">
                  <td class="py-2 pr-4 font-medium text-gray-500 dark:text-slate-400">Current IP</td>
                  <td class="py-2">{{ auth.user?.currentIP || '—' }}</td>
                </tr>
                <tr>
                  <td class="py-2 pr-4 font-medium text-gray-500 dark:text-slate-400">Last sign-in</td>
                  <td class="py-2">{{ fmtDate(auth.user?.lastSigninTime) }}</td>
                </tr>
              </tbody>
            </table>
          </CardBox>
        </div>

        <!-- Competitions -->
        <div>
          <SectionTitleLineWithButton :icon="mdiTrophy" title="Competitions" />
          <CardBox>
            <table class="w-full text-sm">
              <tbody v-if="competitions">
                <tr class="border-b border-gray-100 dark:border-slate-700">
                  <td class="py-2 pr-4 font-medium text-gray-500 dark:text-slate-400 w-48">Base Competition</td>
                  <td class="py-2 font-mono text-xs">{{ competitions.base?.realCompetitionID }}</td>
                </tr>
                <tr class="border-b border-gray-100 dark:border-slate-700">
                  <td class="py-2 pr-4 pl-4 text-gray-400 dark:text-slate-500">— name</td>
                  <td class="py-2">{{ competitions.base?.realCompetitionName }}</td>
                </tr>
                <tr class="border-b border-gray-100 dark:border-slate-700">
                  <td class="py-2 pr-4 pl-4 text-gray-400 dark:text-slate-500">— season</td>
                  <td class="py-2">{{ competitions.base?.realCompetitionSeasonName }}</td>
                </tr>
                <tr class="border-b border-gray-100 dark:border-slate-700">
                  <td class="py-2 pr-4 pl-4 text-gray-400 dark:text-slate-500">— last match day</td>
                  <td class="py-2">{{ competitions.base?.realCompetitionLastMatchDay }}</td>
                </tr>
                <tr class="border-b border-gray-100 dark:border-slate-700">
                  <td class="py-2 pr-4 pl-4 text-gray-400 dark:text-slate-500">— match day before extra</td>
                  <td class="py-2">{{ competitions.base?.realCompetitionExtraMatchDay ?? '—' }}</td>
                </tr>
                <tr class="border-b border-gray-100 dark:border-slate-700">
                  <td class="py-2 pr-4 pl-4 text-gray-400 dark:text-slate-500">— use extra</td>
                  <td class="py-2">{{ competitions.base?.useExtraRealCompetition }}</td>
                </tr>
                <tr class="border-b border-gray-100 dark:border-slate-700">
                  <td class="py-2 pr-4 font-medium text-gray-500 dark:text-slate-400">Extra Competition</td>
                  <td class="py-2 font-mono text-xs">{{ competitions.extra?.realCompetitionID }}</td>
                </tr>
                <tr class="border-b border-gray-100 dark:border-slate-700">
                  <td class="py-2 pr-4 pl-4 text-gray-400 dark:text-slate-500">— name</td>
                  <td class="py-2">{{ competitions.extra?.realCompetitionName }}</td>
                </tr>
                <tr class="border-b border-gray-100 dark:border-slate-700">
                  <td class="py-2 pr-4 pl-4 text-gray-400 dark:text-slate-500">— season</td>
                  <td class="py-2">{{ competitions.extra?.realCompetitionSeasonName }}</td>
                </tr>
                <tr>
                  <td class="py-2 pr-4 pl-4 text-gray-400 dark:text-slate-500">— last match day</td>
                  <td class="py-2">{{ competitions.extra?.realCompetitionLastMatchDay }}</td>
                </tr>
              </tbody>
              <tbody v-else>
                <tr><td class="py-2 text-gray-400">Loading…</td></tr>
              </tbody>
            </table>
          </CardBox>
        </div>

        <!-- Status -->
        <div>
          <SectionTitleLineWithButton :icon="mdiCalendarCheck" title="Status" />
          <CardBox>
            <table class="w-full text-sm">
              <tbody>
                <tr class="border-b border-gray-100 dark:border-slate-700">
                  <td class="py-2 pr-4 font-medium text-gray-500 dark:text-slate-400 w-40">Match day status</td>
                  <td class="py-2">{{ auth.user?.matchDayStatus || '—' }}</td>
                </tr>
                <tr class="border-b border-gray-100 dark:border-slate-700">
                  <td class="py-2 pr-4 pl-4 text-gray-400 dark:text-slate-500">— start</td>
                  <td class="py-2">{{ fmtDate(auth.user?.matchDayStatusStart) }}</td>
                </tr>
                <tr class="border-b border-gray-100 dark:border-slate-700">
                  <td class="py-2 pr-4 pl-4 text-gray-400 dark:text-slate-500">— finish</td>
                  <td class="py-2">{{ fmtDate(auth.user?.matchDayStatusFinish) }}</td>
                </tr>
                <tr class="border-b border-gray-100 dark:border-slate-700">
                  <td class="py-2 pr-4 font-medium text-gray-500 dark:text-slate-400">Competition</td>
                  <td class="py-2">{{ auth.user?.realCompetitionID ?? '—' }}</td>
                </tr>
                <tr class="border-b border-gray-100 dark:border-slate-700">
                  <td class="py-2 pr-4 font-medium text-gray-500 dark:text-slate-400">Match day</td>
                  <td class="py-2">{{ auth.user?.realCompetitionMatchDay ?? '—' }}</td>
                </tr>
                <tr class="border-b border-gray-100 dark:border-slate-700">
                  <td class="py-2 pr-4 font-medium text-gray-500 dark:text-slate-400">Prev competition</td>
                  <td class="py-2">{{ auth.user?.prevActiveRealCompetitionID ?? '—' }}</td>
                </tr>
                <tr class="border-b border-gray-100 dark:border-slate-700">
                  <td class="py-2 pr-4 font-medium text-gray-500 dark:text-slate-400">Prev match day</td>
                  <td class="py-2">{{ auth.user?.prevActiveRealCompetitionMatchDay ?? '—' }}</td>
                </tr>
                <tr class="border-b border-gray-100 dark:border-slate-700">
                  <td class="py-2 pr-4 font-medium text-gray-500 dark:text-slate-400">Next competition</td>
                  <td class="py-2">{{ auth.user?.nextActiveRealCompetitionID ?? '—' }}</td>
                </tr>
                <tr>
                  <td class="py-2 pr-4 font-medium text-gray-500 dark:text-slate-400">Next match day</td>
                  <td class="py-2">{{ auth.user?.nextActiveRealCompetitionMatchDay ?? '—' }}</td>
                </tr>
              </tbody>
            </table>
          </CardBox>
        </div>
      </div>

    </SectionMain>
  </LayoutAuthenticated>
</template>
