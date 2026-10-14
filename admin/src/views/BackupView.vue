<script setup>
import { ref, onMounted } from 'vue'
import { mdiDatabaseArrowUp, mdiDatabaseRefresh, mdiPlus } from '@mdi/js'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import CardBox from '@/components/CardBox.vue'
import BaseButton from '@/components/BaseButton.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import api from '@/api.js'

const backups = ref([])
const loading = ref(false)
const creating = ref(false)
const restoring = ref(false)
const confirmId = ref(null)   // backup id awaiting restore confirmation
const error = ref(null)
const notice = ref(null)

const statusColor = (s) => {
  if (!s) return 'text-gray-400'
  if (s === 'SUCCESSFUL') return 'text-emerald-600 dark:text-emerald-400'
  if (s === 'RUNNING' || s === 'ENQUEUED') return 'text-blue-600 dark:text-blue-400'
  if (s === 'FAILED' || s === 'SKIPPED') return 'text-red-500'
  return 'text-gray-500'
}

const fmtDate = (iso) => {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' })
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const res = await api.get('/api/v1/admin/backup-runs')
    backups.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load backups.'
  } finally {
    loading.value = false
  }
}

async function createBackup() {
  creating.value = true
  error.value = null
  notice.value = null
  try {
    const res = await api.post('/api/v1/admin/backup-runs')
    notice.value = `Backup started (operation: ${res.data.operationId ?? res.data.status}).`
    await load()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to start backup.'
  } finally {
    creating.value = false
  }
}

async function confirmRestore(id) {
  confirmId.value = id
}

async function doRestore() {
  const id = confirmId.value
  confirmId.value = null
  restoring.value = true
  error.value = null
  notice.value = null
  try {
    const res = await api.post('/api/v1/admin/backup-runs/restore', { backup_id: id })
    notice.value = `Restore of backup #${id} started (operation: ${res.data.operationId ?? res.data.status}).`
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to start restore.'
  } finally {
    restoring.value = false
  }
}

onMounted(load)
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton :icon="mdiDatabaseArrowUp" title="Backup &amp; Restore" main>
        <BaseButton
          :icon="mdiPlus"
          label="Create Backup"
          color="info"
          :disabled="creating || loading"
          @click="createBackup"
        />
      </SectionTitleLineWithButton>

      <!-- Restore confirmation banner -->
      <div
        v-if="confirmId !== null"
        class="mb-4 rounded-lg border border-amber-300 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-700 px-4 py-3 flex items-center gap-4"
      >
        <span class="flex-1 text-sm font-medium text-amber-800 dark:text-amber-200">
          Restore backup <strong>#{{ confirmId }}</strong>? This will replace <strong>all current data</strong>.
        </span>
        <button
          class="rounded px-3 py-1 text-sm font-medium bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
          :disabled="restoring"
          @click="doRestore"
        >{{ restoring ? 'Restoring…' : 'Yes, Restore' }}</button>
        <button
          class="rounded px-3 py-1 text-sm font-medium border border-gray-300 dark:border-slate-600 hover:bg-gray-100 dark:hover:bg-slate-700"
          @click="confirmId = null"
        >Cancel</button>
      </div>

      <p v-if="error" class="mb-4 text-sm text-red-500">{{ error }}</p>
      <p v-if="notice" class="mb-4 text-sm text-emerald-600 dark:text-emerald-400">{{ notice }}</p>

      <CardBox has-table>
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-100 dark:border-slate-700">
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">ID</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">Status</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">Start Time</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 hidden lg:table-cell">End Time</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="5" class="py-4 px-3 text-gray-400">Loading…</td>
            </tr>
            <tr v-else-if="!backups.length">
              <td colspan="5" class="py-4 px-3 text-gray-400">No backups found.</td>
            </tr>
            <tr
              v-for="b in backups"
              :key="b.id"
              class="border-b border-gray-50 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-700/30"
              :class="{ 'bg-amber-50 dark:bg-amber-900/10': confirmId === b.id }"
            >
              <td class="py-2 px-3 font-mono text-xs text-gray-500 dark:text-slate-400">{{ b.id }}</td>
              <td class="py-2 px-3 font-medium" :class="statusColor(b.status)">{{ b.status ?? '—' }}</td>
              <td class="py-2 px-3 text-gray-600 dark:text-slate-300">{{ fmtDate(b.startTime) }}</td>
              <td class="py-2 px-3 text-gray-500 dark:text-slate-400 hidden lg:table-cell">{{ fmtDate(b.endTime) }}</td>
              <td class="py-2 px-3 text-right">
                <button
                  class="rounded px-2.5 py-1 text-xs font-medium border border-gray-300 dark:border-slate-600 hover:bg-gray-100 dark:hover:bg-slate-700 disabled:opacity-40"
                  :disabled="restoring || confirmId !== null"
                  @click="confirmRestore(b.id)"
                >Restore</button>
              </td>
            </tr>
          </tbody>
        </table>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
