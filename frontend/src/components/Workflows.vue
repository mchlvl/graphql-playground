<template>
  <div class="container">
    <h2>Workflows Debug View</h2>
    <div class="section">
      <h3>Response:</h3>
      <div v-if="loading">Loading...</div>
      <div v-else-if="error">❌ Error: {{ error.message }}</div>
      <pre v-else class="json">{{ formattedJson }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useQuery } from '@vue/apollo-composable'
import gql from 'graphql-tag'
import { computed } from 'vue'

const queryText = gql`
query listAll {
  listWorkflows {
    id
    name
    createdAt
    modelCount
  }
}

`

const GET_WORKFLOWS = queryText

const { result, loading, error } = useQuery(GET_WORKFLOWS)

const formattedJson = computed(() => {
  return JSON.stringify(result.value, null, 2)
})
</script>

<style scoped>
.container {
  font-family: sans-serif;
  padding: 1rem 2rem;
  max-width: 1000px;
  margin: auto;
}

.section {
  margin-bottom: 2rem;
}

pre.code {
  background: #1e1e1e;
  color: #dcdcdc;
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
  font-family: 'Fira Code', monospace;
}

pre.json {
  background: #f6f8fa;
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow-x: auto;
  font-family: monospace;
}
</style>
