<script setup>
import { ref, onMounted } from 'vue'
import { mdiCog, mdiChevronDown, mdiChevronRight } from '@mdi/js'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import CardBox from '@/components/CardBox.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import api from '@/api.js'

const types = ref([])
const selectedType = ref('')
const competitions = ref([])
const selectedCompetitionId = ref(null)
const rows = ref([])
const loading = ref(false)
const error = ref(null)
const expanded = ref(new Set())

async function fetchProcesses() {
  loading.value = true
  error.value = null
  rows.value = []
  expanded.value = new Set()
  try {
    const params = {}
    if (selectedType.value) params.process_type = selectedType.value
    if (selectedCompetitionId.value != null) params.real_competition_id = selectedCompetitionId.value
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
  fetchProcesses()
}

function onCompetitionChange(e) {
  const v = e.target.value
  selectedCompetitionId.value = v === '' ? null : Number(v)
  fetchProcesses()
}

function competitionLabel(c) {
  return `${c.realCompetitionSeasonId} · ${c.realCompetitionName}`
}

function toggleExpand(id) {
  if (expanded.value.has(id)) expanded.value.delete(id)
  else expanded.value.add(id)
  expanded.value = new Set(expanded.value)
}

function parseTasks(raw) {
  if (!raw) return null
  if (typeof raw === 'string') {
    try { return JSON.parse(raw) } catch { return null }
  }
  return raw
}

// Flatten the nested task tree into a list with indent level
function flattenTasks(tasks, level = 0) {
  if (!tasks) return []
  const result = []
  const list = Array.isArray(tasks) ? tasks : Object.values(tasks)
  for (const t of list) {
    result.push({ ...t, _level: level })
    if (t.tasks?.length) result.push(...flattenTasks(t.tasks, level + 1))
  }
  return result
}

function fmtDate(iso) {
  if (!iso) return '—'
  return iso.replace('T', ' ').replace(/\.\d+.*$/, '')
}

function fmtDuration(d) {
  if (d == null) return '—'
  if (d < 1) return `${(d * 1000).toFixed(0)}ms`
  if (d < 60) return `${d.toFixed(3)}s`
  const m = Math.floor(d / 60)
  const s = (d % 60).toFixed(0).padStart(2, '0')
  return `${m}m ${s}s`
}

function infoStr(info) {
  if (!info) return ''
  return Object.entries(info)
    .filter(([, v]) => v != null)
    .map(([k, v]) => `${k}: ${v}`)
    .join(' · ')
}

onMounted(async () => {
  try {
    const [typesRes, compsRes, baseRes] = await Promise.all([
      api.get('/api/v1/admin/processes/types'),
      api.get('/api/v1/admin/real-competitions'),
      api.get('/api/v1/admin/real-competitions/current-base'),
    ])
    types.value = typesRes.data
    competitions.value = compsRes.data
    selectedCompetitionId.value = baseRes.data?.realCompetitionID ?? null
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load filters.'
  }
  fetchProcesses()
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton :icon="mdiCog" title="Processes" main />

      <div class="mb-4 flex items-center gap-3 flex-wrap">
        <label class="text-sm font-medium text-gray-600 dark:text-slate-300">Competition</label>
        <select
          :value="selectedCompetitionId ?? ''"
          class="text-sm border border-gray-300 dark:border-slate-600 rounded px-2 py-1 bg-white dark:bg-slate-800 min-w-[14rem]"
          @change="onCompetitionChange"
        >
          <option value="">All</option>
          <option v-for="c in competitions" :key="c.realCompetitionID" :value="c.realCompetitionID">
            {{ competitionLabel(c) }}
          </option>
        </select>

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
              <th class="py-2 px-2 w-6"></th>
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
              <td colspan="7" class="py-4 px-3 text-gray-400">Loading…</td>
            </tr>
            <tr v-else-if="!loading && !rows.length">
              <td colspan="7" class="py-4 px-3 text-gray-400">No processes found.</td>
            </tr>

            <template v-for="row in rows" :key="row.processID">
              <!-- Main row -->
              <tr
                class="border-b border-gray-50 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-700/30 cursor-pointer"
                @click="toggleExpand(row.processID)"
              >
                <td class="py-2 px-2 text-gray-400">
                  <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current transition-transform" :class="{ 'rotate-0': !expanded.has(row.processID), 'rotate-90': expanded.has(row.processID) }">
                    <path :d="mdiChevronRight" />
                  </svg>
                </td>
                <td class="py-2 px-3 font-mono text-xs text-gray-500 dark:text-slate-400">{{ row.processID }}</td>
                <td class="py-2 px-3 text-gray-600 dark:text-slate-300">{{ row.processType }}</td>
                <td class="py-2 px-3 text-gray-800 dark:text-slate-200 max-w-xs truncate" :title="row.processName">{{ row.processName }}</td>
                <td class="py-2 px-3 font-mono text-xs text-gray-500 dark:text-slate-400 whitespace-nowrap">{{ fmtDate(row.startDate) }}</td>
                <td class="py-2 px-3 text-gray-500 dark:text-slate-400">{{ fmtDuration(row.duration) }}</td>
                <td class="py-2 px-3 text-gray-500 dark:text-slate-400 hidden md:table-cell">{{ row.versions }}</td>
              </tr>

              <!-- Expanded tasks -->
              <tr v-if="expanded.has(row.processID)" class="bg-gray-50/60 dark:bg-slate-800/40">
                <td colspan="7" class="px-6 pb-3 pt-1">
                  <template v-if="parseTasks(row.tasks)">
                    <table class="w-full text-xs">
                      <thead>
                        <tr class="border-b border-gray-200 dark:border-slate-700">
                          <th class="py-1 px-2 text-left font-semibold text-gray-500 dark:text-slate-400">Task</th>
                          <th class="py-1 px-2 text-left font-semibold text-gray-500 dark:text-slate-400">Status</th>
                          <th class="py-1 px-2 text-left font-semibold text-gray-500 dark:text-slate-400">Duration</th>
                          <th class="py-1 px-2 text-left font-semibold text-gray-500 dark:text-slate-400">Info</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr
                          v-for="(task, i) in flattenTasks(parseTasks(row.tasks))"
                          :key="i"
                          class="border-b border-gray-100 dark:border-slate-700/50"
                        >
                          <td class="py-1 px-2 text-gray-700 dark:text-slate-300" :style="{ paddingLeft: `${task._level * 16 + 8}px` }">
                            {{ task.name }}
                          </td>
                          <td class="py-1 px-2">
                            <span
                              v-if="task.status"
                              class="rounded px-1 py-0.5 font-medium"
                              :class="task.status === 'completed'
                                ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
                                : task.errors?.length
                                  ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                                  : 'bg-gray-100 text-gray-600 dark:bg-slate-700 dark:text-slate-300'"
                            >{{ task.status }}</span>
                            <span v-else class="text-gray-400">—</span>
                          </td>
                          <td class="py-1 px-2 text-gray-500 dark:text-slate-400 whitespace-nowrap">{{ fmtDuration(task.duration) }}</td>
                          <td class="py-1 px-2 text-gray-500 dark:text-slate-400">
                            <span v-if="task.errors?.length" class="text-red-500 mr-2">{{ task.errors.join('; ') }}</span>
                            {{ infoStr(task.info) }}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </template>
                  <span v-else class="text-xs text-gray-400">No task data.</span>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
