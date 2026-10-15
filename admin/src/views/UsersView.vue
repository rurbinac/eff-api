<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { mdiAccountGroup } from '@mdi/js'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import CardBox from '@/components/CardBox.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import api from '@/api.js'

const router = useRouter()

const users = ref([])
const loading = ref(true)
const error = ref(null)

const levelLabel = (level) => {
  if (level === 3) return 'Admin'
  if (level === 2) return 'Manager'
  return 'User'
}

const fmtDate = (iso) => {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' })
}

onMounted(async () => {
  try {
    const res = await api.get('/api/v1/admin/users')
    users.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load users.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton :icon="mdiAccountGroup" title="Users" main />

      <p v-if="error" class="mb-4 text-red-500">{{ error }}</p>

      <CardBox has-table>
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-100 dark:border-slate-700">
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">ID</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">Name</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">Email</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">Level</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 hidden lg:table-cell">Last sign-in</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 hidden lg:table-cell">Last IP</th>
              <th class="py-2 px-3"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="7" class="py-4 px-3 text-gray-400">Loading…</td>
            </tr>
            <tr
              v-for="user in users"
              :key="user.userID"
              class="border-b border-gray-50 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-700/30"
            >
              <td class="py-2 px-3 font-mono text-xs text-gray-400">{{ user.userID }}</td>
              <td class="py-2 px-3">{{ user.firstName }} {{ user.lastName }}</td>
              <td class="py-2 px-3 text-gray-500 dark:text-slate-400">{{ user.userEmail }}</td>
              <td class="py-2 px-3">
                <span
                  class="rounded px-1.5 py-0.5 text-xs font-medium"
                  :class="user.userLevel === 3
                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                    : 'bg-gray-100 text-gray-600 dark:bg-slate-700 dark:text-slate-300'"
                >
                  {{ levelLabel(user.userLevel) }}
                </span>
              </td>
              <td class="py-2 px-3 text-gray-500 dark:text-slate-400 hidden lg:table-cell">{{ fmtDate(user.lastSignInDate) }}</td>
              <td class="py-2 px-3 font-mono text-xs text-gray-400 hidden lg:table-cell">{{ user.lastSignInIP || '—' }}</td>
              <td class="py-2 px-3 text-right whitespace-nowrap">
                <button
                  class="mr-1 rounded px-2 py-0.5 text-xs font-medium bg-blue-50 text-blue-600 hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-300 dark:hover:bg-blue-900/50"
                  @click="router.push({ name: 'user-detail', params: { id: user.userID } })"
                >Detail</button>
                <button
                  class="rounded px-2 py-0.5 text-xs font-medium bg-emerald-50 text-emerald-600 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-300 dark:hover:bg-emerald-900/50"
                  @click="router.push({ name: 'leagues', query: { userId: user.userID } })"
                >Leagues</button>
              </td>
            </tr>
          </tbody>
        </table>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
