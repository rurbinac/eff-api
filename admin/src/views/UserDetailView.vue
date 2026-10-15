<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { mdiAccount, mdiArrowLeft } from '@mdi/js'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import CardBox from '@/components/CardBox.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import api from '@/api.js'

const route = useRoute()
const router = useRouter()

const user = ref(null)
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
    const res = await api.get(`/api/v1/admin/users/${route.params.id}`)
    user.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load user.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton :icon="mdiAccount" :title="user ? `${user.firstName} ${user.lastName}` : 'User Detail'" main>
        <button
          class="flex items-center gap-1 rounded px-3 py-1 text-sm font-medium bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
          @click="router.push({ name: 'users' })"
        >
          <svg :viewBox="mdiArrowLeft.startsWith('M') ? '0 0 24 24' : '0 0 24 24'" class="w-4 h-4 fill-current" xmlns="http://www.w3.org/2000/svg">
            <path :d="mdiArrowLeft" />
          </svg>
          Users
        </button>
      </SectionTitleLineWithButton>

      <p v-if="error" class="mb-4 text-red-500">{{ error }}</p>
      <p v-else-if="loading" class="text-gray-400">Loading…</p>

      <template v-else-if="user">
        <CardBox class="mb-4">
          <table class="w-full text-sm">
            <tbody>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 w-40 font-semibold text-gray-500 dark:text-slate-400">ID</td>
                <td class="py-2 px-3 font-mono text-xs text-gray-400">{{ user.userID }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Name</td>
                <td class="py-2 px-3">{{ user.firstName }} {{ user.lastName }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Username</td>
                <td class="py-2 px-3">{{ user.userName || '—' }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Email</td>
                <td class="py-2 px-3">{{ user.userEmail }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Level</td>
                <td class="py-2 px-3">
                  <span
                    class="rounded px-1.5 py-0.5 text-xs font-medium"
                    :class="user.userLevel === 3
                      ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                      : 'bg-gray-100 text-gray-600 dark:bg-slate-700 dark:text-slate-300'"
                  >{{ levelLabel(user.userLevel) }}</span>
                </td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Birthday</td>
                <td class="py-2 px-3">{{ fmtDate(user.birthday) }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Location</td>
                <td class="py-2 px-3">{{ [user.city, user.state, user.country].filter(Boolean).join(', ') || '—' }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Phone</td>
                <td class="py-2 px-3">{{ user.phoneNumber || '—' }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Timezone</td>
                <td class="py-2 px-3">{{ user.timeZone || '—' }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Favourite team</td>
                <td class="py-2 px-3">{{ user.favoriteTeam || '—' }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Last sign-in</td>
                <td class="py-2 px-3">{{ fmtDate(user.lastSignInDate) }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Last IP</td>
                <td class="py-2 px-3 font-mono text-xs text-gray-400">{{ user.lastSignInIP || '—' }}</td>
              </tr>
              <tr class="border-b border-gray-50 dark:border-slate-800">
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Created</td>
                <td class="py-2 px-3">{{ fmtDate(user.createdIn) }}</td>
              </tr>
              <tr>
                <td class="py-2 px-3 font-semibold text-gray-500 dark:text-slate-400">Updated</td>
                <td class="py-2 px-3">{{ fmtDate(user.updatedIn) }}</td>
              </tr>
            </tbody>
          </table>
        </CardBox>

        <div>
          <button
            class="rounded px-3 py-1.5 text-sm font-medium bg-emerald-50 text-emerald-600 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-300 dark:hover:bg-emerald-900/50"
            @click="router.push({ name: 'leagues', query: { userId: user.userID } })"
          >View leagues</button>
        </div>
      </template>
    </SectionMain>
  </LayoutAuthenticated>
</template>
