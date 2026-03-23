<template>
  <h1>Settings</h1>

  <div class="card">
    <h3>Tournament Name</h3>
    <div class="form-row">
      <input v-model="store.tournamentName" style="width:300px" placeholder="Tournament name" />
    </div>
  </div>

  <div class="card">
    <h3>Export / Import JSON</h3>
    <p class="text-sm text-dim mb-16">Save or restore all tournament data as a JSON file. Share this file with others to sync data.</p>
    <div class="flex gap-8">
      <button class="btn btn-primary" @click="doExport">Export JSON</button>
      <input type="file" ref="jsonInput" accept=".json" @change="handleJsonImport" style="display:none" />
      <button class="btn" @click="$refs.jsonInput.click()">Import JSON</button>
    </div>
    <div v-if="importStatus" class="mt-16 text-sm" :style="{ color: importError ? 'var(--red)' : 'var(--accent)' }">
      {{ importStatus }}
    </div>
  </div>

  <div class="card">
    <h3>Reset All Data</h3>
    <p class="text-sm text-dim mb-16">This will reset everything to defaults with fresh dummy data.</p>
    <button class="btn btn-danger" @click="doReset">Reset Everything</button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { store, exportData, importData, resetData } from '../stores/tournament.js'

const jsonInput = ref(null)
const importStatus = ref('')
const importError = ref(false)

function doExport() {
  exportData()
}

function handleJsonImport(e) {
  const file = e.target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => {
    const ok = importData(ev.target.result)
    if (ok) {
      importStatus.value = 'Data restored successfully.'
      importError.value = false
    } else {
      importStatus.value = 'Failed to parse JSON file.'
      importError.value = true
    }
  }
  reader.readAsText(file)
  if (jsonInput.value) jsonInput.value.value = ''
}

function doReset() {
  if (confirm('Are you sure? This will delete ALL data and regenerate defaults.')) {
    resetData()
    importStatus.value = 'Data has been reset.'
    importError.value = false
  }
}
</script>
