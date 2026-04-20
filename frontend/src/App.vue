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
        unique: false,
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
const LUMINANCE_RED_WEIGHT = 299
const LUMINANCE_GREEN_WEIGHT = 587
const LUMINANCE_BLUE_WEIGHT = 114
const LUMINANCE_DIVISOR = 1000
const LUMINANCE_THRESHOLD = 150
const COLUMN_TYPES = [
  'INT',
  'BIGINT',
  'VARCHAR(255)',
  'TEXT',
  'BOOLEAN',
  'DATE',
  'DATETIME',
  'TIMESTAMP',
  'DECIMAL(10,2)',
]

function resolveRelationshipColumn(table, columnId, columnName) {
  if (!table) {
    return null
  }
  return (
    table.columns.find((column) => column.id === columnId) ||
    table.columns.find((column) => column.name === columnName) ||
    null
  )
}

function relationColor(table, column) {
  return column?.color || table.color || '#2d7dd2'
}

function relationAnchor(table, column, targetTable) {
  const columnIndex = table.columns.findIndex((tableColumn) => tableColumn.id === column.id)
  if (columnIndex < 0) {
    return null
  }

  const columnRowElement =
    typeof document === 'undefined'
      ? null
      : Array.from(document.querySelectorAll('[data-column-id]')).find(
          (element) => element.getAttribute('data-column-id') === column.id,
        )

  const isTargetOnRight = targetTable.x > table.x + TABLE_WIDTH / 2
  const anchorX = isTargetOnRight ? table.x + TABLE_WIDTH : table.x
  const domAnchorY =
    columnRowElement instanceof HTMLElement
      ? table.y + columnRowElement.offsetTop + columnRowElement.offsetHeight / 2
      : null
  const anchorY = domAnchorY ?? table.y + HEADER_HEIGHT

  return {
    x: anchorX,
    y: anchorY,
  }
}

function contrastColor(hexColor) {
  const hex = hexColor.replace('#', '')
  const normalizedHex = hex.length === 3 ? hex.split('').map((char) => `${char}${char}`).join('') : hex
  if (normalizedHex.length !== 6) {
    return '#ffffff'
  }

  const red = Number.parseInt(normalizedHex.slice(0, 2), 16)
  const green = Number.parseInt(normalizedHex.slice(2, 4), 16)
  const blue = Number.parseInt(normalizedHex.slice(4, 6), 16)
  const luminance =
    (red * LUMINANCE_RED_WEIGHT + green * LUMINANCE_GREEN_WEIGHT + blue * LUMINANCE_BLUE_WEIGHT) /
    LUMINANCE_DIVISOR
  return luminance > LUMINANCE_THRESHOLD ? '#132033' : '#ffffff'
}

const relationLines = computed(() => {
  return relationships.value
    .map((relation) => {
      const fromTable = tableMap.value[relation.fromTableId]
      const toTable = tableMap.value[relation.toTableId]
      if (!fromTable || !toTable) {
        return null
      }

      const fromColumn = resolveRelationshipColumn(fromTable, relation.fromColumnId, relation.fromColumn)
      const toColumn = resolveRelationshipColumn(toTable, relation.toColumnId, relation.toColumn)
      if (!fromColumn || !toColumn) {
        return null
      }

      const start = relationAnchor(fromTable, fromColumn, toTable)
      const end = relationAnchor(toTable, toColumn, fromTable)
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
        fromColor: relationColor(fromTable, fromColumn),
        toColor: relationColor(toTable, toColumn),
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
        unique: false,
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

  const column = table.columns.find((tableColumn) => tableColumn.id === columnId)
  if (!column) {
    return
  }

  table.columns = table.columns.filter((tableColumn) => tableColumn.id !== columnId)
  relationships.value = relationships.value.filter((relation) => {
    if (
      relation.fromTableId === tableId &&
      (relation.fromColumnId === column.id || relation.fromColumn === column.name)
    ) {
      return false
    }
    if (relation.toTableId === tableId && (relation.toColumnId === column.id || relation.toColumn === column.name)) {
      return false
    }
    return true
  })

  if (relationshipDraft.value.fromTableId === tableId && relationshipDraft.value.fromColumn === column.id) {
    relationshipDraft.value.fromColumn = ''
  }
  if (relationshipDraft.value.toTableId === tableId && relationshipDraft.value.toColumn === column.id) {
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

  const fromTable = tableMap.value[draft.fromTableId]
  const toTable = tableMap.value[draft.toTableId]
  const fromColumn = resolveRelationshipColumn(fromTable, draft.fromColumn, draft.fromColumn)
  const toColumn = resolveRelationshipColumn(toTable, draft.toColumn, draft.toColumn)
  if (!fromColumn || !toColumn) {
    return
  }

  relationships.value.push({
    id: `rel-${relationships.value.length + 1}`,
    fromTableId: draft.fromTableId,
    toTableId: draft.toTableId,
    fromColumn: fromColumn.name,
    toColumn: toColumn.name,
    fromColumnId: fromColumn.id,
    toColumnId: toColumn.id,
    onDelete: 'RESTRICT',
    onUpdate: 'CASCADE',
  })

  relationshipDraft.value = { fromTableId: '', fromColumn: '', toTableId: '', toColumn: '' }
}

async function generateSql() {
  errorMessage.value = ''
  isGenerating.value = true

  try {
    const sqlRelationships = relationships.value
      .map((relation) => {
        const fromTable = tableMap.value[relation.fromTableId]
        const toTable = tableMap.value[relation.toTableId]
        const fromColumn = resolveRelationshipColumn(fromTable, relation.fromColumnId, relation.fromColumn)
        const toColumn = resolveRelationshipColumn(toTable, relation.toColumnId, relation.toColumn)
        if (!fromTable || !toTable || !fromColumn || !toColumn) {
          return null
        }

        return {
          ...relation,
          fromColumn: fromColumn.name,
          toColumn: toColumn.name,
        }
      })
      .filter(Boolean)

    const response = await fetch(`${apiBaseUrl}/api/generate-sql`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tables: tables.value, relationships: sqlRelationships }),
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
          <option v-for="column in fromColumns" :key="`from-column-${column.id}`" :value="column.id">{{ column.name }}</option>
        </select>
        <select v-model="relationshipDraft.toTableId">
          <option disabled value="">To table</option>
          <option v-for="table in tables" :key="`to-${table.id}`" :value="table.id">{{ table.name }}</option>
        </select>
        <select v-model="relationshipDraft.toColumn">
          <option disabled value="">To column</option>
          <option v-for="column in toColumns" :key="`to-column-${column.id}`" :value="column.id">{{ column.name }}</option>
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
          <div
            v-for="column in table.columns"
            :key="column.id"
            class="column-row"
            :data-column-id="column.id"
            :style="{ backgroundColor: column.color }"
          >
            <input v-model="column.name" aria-label="Column name" />
            <select v-model="column.type" aria-label="Column type">
              <option v-for="columnType in COLUMN_TYPES" :key="`${column.id}-${columnType}`" :value="columnType">
                {{ columnType }}
              </option>
            </select>
            <label>
              PK
              <input v-model="column.primaryKey" type="checkbox" />
            </label>
            <label>
              Unique
              <input v-model="column.unique" type="checkbox" />
            </label>
            <div class="column-actions">
              <input v-model="column.color" type="color" aria-label="Column color" />
              <button
                type="button"
                class="danger-button"
                :aria-label="`Delete column ${column.name}`"
                @click="deleteColumn(table.id, column.id)"
              >
                Delete column
              </button>
            </div>
          </div>
        </div>

        <button type="button" @click="addColumn(table.id)">Add column</button>
        <button
          type="button"
          class="danger-button"
          :aria-label="`Delete table ${table.name}`"
          @click="deleteTable(table.id)"
        >
          Delete table
        </button>
      </article>
    </main>
  </div>
</template>
