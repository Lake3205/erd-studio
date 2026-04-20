<script setup>
import { computed, ref } from 'vue'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

const tables = ref([
  {
    id: 'table-users',
    name: 'users',
    x: 80,
    y: 80,
    columns: [
      { id: 'users-id', name: 'id', type: 'INT', primaryKey: true, nullable: false, autoIncrement: true },
      { id: 'users-email', name: 'email', type: 'VARCHAR(255)', primaryKey: false, nullable: false, unique: true },
    ],
  },
])

const relationships = ref([])
const relationshipDraft = ref({ fromTableId: '', fromColumn: '', toTableId: '', toColumn: '' })
const sqlScript = ref('')
const isGenerating = ref(false)
const errorMessage = ref('')

let tableCounter = 1
let columnCounter = 2
let activeDrag = null

const tableMap = computed(() => Object.fromEntries(tables.value.map((table) => [table.id, table])))

const relationLines = computed(() => {
  return relationships.value
    .map((relation) => {
      const fromTable = tableMap.value[relation.fromTableId]
      const toTable = tableMap.value[relation.toTableId]
      if (!fromTable || !toTable) {
        return null
      }

      return {
        id: relation.id,
        x1: fromTable.x + 150,
        y1: fromTable.y + 45,
        x2: toTable.x + 150,
        y2: toTable.y + 45,
      }
    })
    .filter(Boolean)
})

const fromColumns = computed(() => {
  const table = tableMap.value[relationshipDraft.value.fromTableId]
  return table ? table.columns : []
})

const toColumns = computed(() => {
  const table = tableMap.value[relationshipDraft.value.toTableId]
  return table ? table.columns : []
})

function addTable() {
  tableCounter += 1
  const tableId = `table-${tableCounter}`
  tables.value.push({
    id: tableId,
    name: `table_${tableCounter}`,
    x: 80 + tableCounter * 20,
    y: 80 + tableCounter * 20,
    columns: [
      {
        id: `${tableId}-id`,
        name: 'id',
        type: 'INT',
        primaryKey: true,
        nullable: false,
        autoIncrement: true,
      },
    ],
  })
}

function addColumn(tableId) {
  columnCounter += 1
  const table = tableMap.value[tableId]
  if (!table) {
    return
  }

  table.columns.push({
    id: `${tableId}-column-${columnCounter}`,
    name: `column_${columnCounter}`,
    type: 'VARCHAR(255)',
    primaryKey: false,
    nullable: true,
    autoIncrement: false,
    unique: false,
  })
}

function startDrag(tableId, event) {
  const table = tableMap.value[tableId]
  if (!table) {
    return
  }

  activeDrag = {
    tableId,
    offsetX: event.clientX - table.x,
    offsetY: event.clientY - table.y,
  }
}

function onCanvasMove(event) {
  if (!activeDrag) {
    return
  }

  const table = tableMap.value[activeDrag.tableId]
  if (!table) {
    return
  }

  table.x = Math.max(16, event.clientX - activeDrag.offsetX)
  table.y = Math.max(16, event.clientY - activeDrag.offsetY)
}

function stopDrag() {
  activeDrag = null
}

function addRelationship() {
  const draft = relationshipDraft.value
  if (!draft.fromTableId || !draft.toTableId || !draft.fromColumn || !draft.toColumn) {
    return
  }

  relationships.value.push({
    id: `rel-${relationships.value.length + 1}`,
    ...draft,
    onDelete: 'RESTRICT',
    onUpdate: 'CASCADE',
  })

  relationshipDraft.value = { fromTableId: '', fromColumn: '', toTableId: '', toColumn: '' }
}

async function generateSql() {
  errorMessage.value = ''
  isGenerating.value = true

  try {
    const response = await fetch(`${apiBaseUrl}/api/generate-sql`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tables: tables.value, relationships: relationships.value }),
    })

    const payload = await response.json()

    if (!response.ok) {
      throw new Error(payload.error || 'Failed to generate SQL')
    }

    sqlScript.value = payload.sql || ''
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to generate SQL'
  } finally {
    isGenerating.value = false
  }
}
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <h1>ERD Studio</h1>
      <p>Drag tables on the canvas, define relationships, and generate SQL scripts.</p>

      <button type="button" @click="addTable">Add Table</button>

      <div class="relationship-builder">
        <h2>Relationship</h2>
        <select v-model="relationshipDraft.fromTableId">
          <option disabled value="">From table</option>
          <option v-for="table in tables" :key="`from-${table.id}`" :value="table.id">{{ table.name }}</option>
        </select>
        <select v-model="relationshipDraft.fromColumn">
          <option disabled value="">From column</option>
          <option v-for="column in fromColumns" :key="`from-column-${column.id}`" :value="column.name">{{ column.name }}</option>
        </select>
        <select v-model="relationshipDraft.toTableId">
          <option disabled value="">To table</option>
          <option v-for="table in tables" :key="`to-${table.id}`" :value="table.id">{{ table.name }}</option>
        </select>
        <select v-model="relationshipDraft.toColumn">
          <option disabled value="">To column</option>
          <option v-for="column in toColumns" :key="`to-column-${column.id}`" :value="column.name">{{ column.name }}</option>
        </select>
        <button type="button" @click="addRelationship">Add Relationship</button>
      </div>

      <button type="button" @click="generateSql" :disabled="isGenerating">
        {{ isGenerating ? 'Generating...' : 'Generate SQL' }}
      </button>

      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

      <textarea
        v-model="sqlScript"
        rows="16"
        readonly
        placeholder="Generated SQL script appears here"
      />
    </aside>

    <main class="canvas" @mousemove="onCanvasMove" @mouseup="stopDrag" @mouseleave="stopDrag">
      <svg class="relationship-lines" width="100%" height="100%" aria-hidden="true">
        <line
          v-for="line in relationLines"
          :key="line.id"
          :x1="line.x1"
          :y1="line.y1"
          :x2="line.x2"
          :y2="line.y2"
        />
      </svg>

      <article v-for="table in tables" :key="table.id" class="table-card" :style="{ left: `${table.x}px`, top: `${table.y}px` }">
        <header class="drag-handle" @mousedown="startDrag(table.id, $event)">
          <input v-model="table.name" aria-label="Table name" />
        </header>

        <div class="column-list">
          <div v-for="column in table.columns" :key="column.id" class="column-row">
            <input v-model="column.name" aria-label="Column name" />
            <input v-model="column.type" aria-label="Column type" />
            <label>
              PK
              <input v-model="column.primaryKey" type="checkbox" />
            </label>
          </div>
        </div>

        <button type="button" @click="addColumn(table.id)">Add column</button>
      </article>
    </main>
  </div>
</template>
