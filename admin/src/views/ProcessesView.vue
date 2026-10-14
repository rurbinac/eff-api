<script setup>
import { ref, onMounted } from 'vue'
import { mdiCog } from '@mdi/js'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import CardBox from '@/components/CardBox.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import api from '@/api.js'

const types = ref([])
const selectedType = ref('')
const rows = ref([])
const loading = ref(false)
const error = ref(null)

async function fetchProcesses(type) {
  loading.value = true
  error.value = null
  rows.value = []
  try {
    const params = type ? { process_type: type } : {}
    const res = await api.get('/api/v1/admin/processes', { params })
    rows.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load processes.'
  } finally {
    loading.value = false
  }
}

function onTypeChange(e) {
  selectedType.value = e.target.value
  fetchProcesses(selectedType.value)
}

function fmtDate(iso) {
  if (!iso) return '—'
  return iso.replace('T', ' ').replace(/\.\d+.*$/, '')
}

function fmtDuration(d) {
  if (d == null) return '—'
  if (d < 60) return `${d.toFixed(1)}s`
  const m = Math.floor(d / 60)
  const s = (d % 60).toFixed(0).padStart(2, '0')
  return `${m}m ${s}s`
}

onMounted(async () => {
  try {
    const res = await api.get('/api/v1/admin/processes/types')
    types.value = res.data
    fetchProcesses('')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load process types.'
  }
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton :icon="mdiCog" title="Processes" main />

      <div class="mb-4 flex items-center gap-3 flex-wrap">
        <label class="text-sm font-medium text-gray-600 dark:text-slate-300">Type</label>
        <select
          :value="selectedType"
          class="text-sm border border-gray-300 dark:border-slate-600 rounded px-2 py-1 bg-white dark:bg-slate-800 min-w-[10rem]"
          @change="onTypeChange"
        >
          <option value="">All</option>
          <option v-for="t in types" :key="t" :value="t">{{ t }}</option>
        </select>

        <span v-if="loading" class="text-sm text-gray-400">Loading…</span>
        <span v-if="!loading && rows.length" class="text-sm text-gray-400">{{ rows.length }} rows</span>
      </div>

      <p v-if="error" class="mb-4 text-sm text-red-500">{{ error }}</p>

      <CardBox has-table>
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-100 dark:border-slate-700">
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">ID</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">Type</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">Name</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">Start</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300">Duration</th>
              <th class="py-2 px-3 text-left font-semibold text-gray-600 dark:text-slate-300 hidden md:table-cell">Ver</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading && !rows.length">
              <td colspan="6" class="py-4 px-3 text-gray-400">Loading…</td>
            </tr>
            <tr v-else-if="!loading && !rows.length">
              <td colspan="6" class="py-4 px-3 text-gray-400">No processes found.</td>
            </tr>
            <tr
              v-for="row in rows"
              :key="row.processID"
              class="border-b border-gray-50 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-700/30"
            >
              <td class="py-2 px-3 font-mono text-xs text-gray-500 dark:text-slate-400">{{ row.processID }}</td>
              <td class="py-2 px-3 text-gray-600 dark:text-slate-300">{{ row.processType }}</td>
              <td class="py-2 px-3 text-gray-800 dark:text-slate-200 max-w-xs truncate" :title="row.processName">{{ row.processName }}</td>
              <td class="py-2 px-3 font-mono text-xs text-gray-500 dark:text-slate-400 whitespace-nowrap">{{ fmtDate(row.startDate) }}</td>
              <td class="py-2 px-3 text-gray-500 dark:text-slate-400">{{ fmtDuration(row.duration) }}</td>
              <td class="py-2 px-3 text-gray-500 dark:text-slate-400 hidden md:table-cell">{{ row.versions }}</td>
            </tr>
          </tbody>
        </table>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
