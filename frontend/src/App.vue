<script setup>
import { computed, ref } from 'vue'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

const tables = ref([
  {
    id: 'table-users',
    name: 'users',
    x: 80,
    y: 80,
    color: '#2d7dd2',
    columns: [
      {
        id: 'users-id',
        name: 'id',
        type: 'INT',
        primaryKey: true,
        nullable: false,
        autoIncrement: true,
        color: '#eef4ff',
      },
      {
        id: 'users-email',
        name: 'email',
        type: 'VARCHAR(255)',
        primaryKey: false,
        nullable: false,
        unique: true,
        color: '#eef4ff',
      },
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
const TABLE_WIDTH = 300
const HEADER_HEIGHT = 48
const COLUMN_ROW_HEIGHT = 103
const COLUMN_LIST_PADDING_TOP = 12

function relationColor(table, columnName) {
  const column = table.columns.find((item) => item.name === columnName)
  return column?.color || table.color || '#2d7dd2'
}

function relationAnchor(table, columnName, targetTable) {
  const columnIndex = table.columns.findIndex((column) => column.name === columnName)
  if (columnIndex < 0) {
    return null
  }

  const targetRight = targetTable.x > table.x + TABLE_WIDTH / 2
  return {
    x: targetRight ? table.x + TABLE_WIDTH : table.x,
    y: table.y + HEADER_HEIGHT + COLUMN_LIST_PADDING_TOP + columnIndex * COLUMN_ROW_HEIGHT + COLUMN_ROW_HEIGHT / 2,
  }
}

function contrastColor(hexColor) {
  const hex = hexColor.replace('#', '')
  if (hex.length !== 6) {
    return '#ffffff'
  }

  const red = Number.parseInt(hex.slice(0, 2), 16)
  const green = Number.parseInt(hex.slice(2, 4), 16)
  const blue = Number.parseInt(hex.slice(4, 6), 16)
  const luminance = (red * 299 + green * 587 + blue * 114) / 1000
  return luminance > 150 ? '#132033' : '#ffffff'
}

const relationLines = computed(() => {
  return relationships.value
    .map((relation) => {
      const fromTable = tableMap.value[relation.fromTableId]
      const toTable = tableMap.value[relation.toTableId]
      if (!fromTable || !toTable) {
        return null
      }

      const start = relationAnchor(fromTable, relation.fromColumn, toTable)
      const end = relationAnchor(toTable, relation.toColumn, fromTable)
      if (!start || !end) {
        return null
      }

      const angle = Math.atan2(end.y - start.y, end.x - start.x)
      const arrowLength = 10
      const arrowWidth = 6
      const arrowLeftX = end.x - Math.cos(angle) * arrowLength + Math.sin(angle) * arrowWidth
      const arrowLeftY = end.y - Math.sin(angle) * arrowLength - Math.cos(angle) * arrowWidth
      const arrowRightX = end.x - Math.cos(angle) * arrowLength - Math.sin(angle) * arrowWidth
      const arrowRightY = end.y - Math.sin(angle) * arrowLength + Math.cos(angle) * arrowWidth

      return {
        id: relation.id,
        gradientId: `gradient-${relation.id}`,
        x1: start.x,
        y1: start.y,
        x2: end.x,
        y2: end.y,
        fromColor: relationColor(fromTable, relation.fromColumn),
        toColor: relationColor(toTable, relation.toColumn),
        arrowPoints: `${end.x},${end.y} ${arrowLeftX},${arrowLeftY} ${arrowRightX},${arrowRightY}`,
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
    color: '#2d7dd2',
    columns: [
      {
        id: `${tableId}-id`,
        name: 'id',
        type: 'INT',
        primaryKey: true,
        nullable: false,
        autoIncrement: true,
        color: '#eef4ff',
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
    color: '#eef4ff',
  })
}

function cleanupRelationshipDraft(tableId) {
  if (relationshipDraft.value.fromTableId === tableId) {
    relationshipDraft.value.fromTableId = ''
    relationshipDraft.value.fromColumn = ''
  }
  if (relationshipDraft.value.toTableId === tableId) {
    relationshipDraft.value.toTableId = ''
    relationshipDraft.value.toColumn = ''
  }
}

function deleteTable(tableId) {
  tables.value = tables.value.filter((table) => table.id !== tableId)
  relationships.value = relationships.value.filter(
    (relation) => relation.fromTableId !== tableId && relation.toTableId !== tableId,
  )
  cleanupRelationshipDraft(tableId)
}

function deleteColumn(tableId, columnId) {
  const table = tableMap.value[tableId]
  if (!table) {
    return
  }

  const column = table.columns.find((item) => item.id === columnId)
  if (!column) {
    return
  }

  table.columns = table.columns.filter((item) => item.id !== columnId)
  relationships.value = relationships.value.filter((relation) => {
    if (relation.fromTableId === tableId && relation.fromColumn === column.name) {
      return false
    }
    if (relation.toTableId === tableId && relation.toColumn === column.name) {
      return false
    }
    return true
  })

  if (relationshipDraft.value.fromTableId === tableId && relationshipDraft.value.fromColumn === column.name) {
    relationshipDraft.value.fromColumn = ''
  }
  if (relationshipDraft.value.toTableId === tableId && relationshipDraft.value.toColumn === column.name) {
    relationshipDraft.value.toColumn = ''
  }
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
        <defs>
          <linearGradient
            v-for="line in relationLines"
            :id="line.gradientId"
            :key="`gradient-${line.id}`"
            gradientUnits="userSpaceOnUse"
            :x1="line.x1"
            :y1="line.y1"
            :x2="line.x2"
            :y2="line.y2"
          >
            <stop offset="0%" :stop-color="line.fromColor" />
            <stop offset="100%" :stop-color="line.toColor" />
          </linearGradient>
        </defs>
        <line
          v-for="line in relationLines"
          :key="line.id"
          :x1="line.x1"
          :y1="line.y1"
          :x2="line.x2"
          :y2="line.y2"
          :stroke="`url(#${line.gradientId})`"
        />
        <polygon v-for="line in relationLines" :key="`${line.id}-arrow`" :points="line.arrowPoints" :fill="line.toColor" />
      </svg>

      <article
        v-for="table in tables"
        :key="table.id"
        class="table-card"
        :style="{ left: `${table.x}px`, top: `${table.y}px`, borderColor: table.color }"
      >
        <header
          class="drag-handle"
          :style="{ backgroundColor: table.color, color: contrastColor(table.color) }"
          @mousedown="startDrag(table.id, $event)"
        >
          <input v-model="table.name" :style="{ color: contrastColor(table.color) }" aria-label="Table name" />
          <input v-model="table.color" type="color" aria-label="Table color" @mousedown.stop />
        </header>

        <div class="column-list">
          <div v-for="column in table.columns" :key="column.id" class="column-row" :style="{ backgroundColor: column.color }">
            <input v-model="column.name" aria-label="Column name" />
            <input v-model="column.type" aria-label="Column type" />
            <label>
              PK
              <input v-model="column.primaryKey" type="checkbox" />
            </label>
            <div class="column-actions">
              <input v-model="column.color" type="color" aria-label="Column color" />
              <button type="button" class="danger-button" @click="deleteColumn(table.id, column.id)">Delete column</button>
            </div>
          </div>
        </div>

        <button type="button" @click="addColumn(table.id)">Add column</button>
        <button type="button" class="danger-button" @click="deleteTable(table.id)">Delete table</button>
      </article>
    </main>
  </div>
</template>
