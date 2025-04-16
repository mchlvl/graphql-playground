// src/main.ts
import { createApp, h } from 'vue'
import App from './App.vue'
import { ApolloClients } from '@vue/apollo-composable'
import { apolloClient } from './apollo'

const app = createApp({
  setup() {
    return () => h(App)
  },
})

app.provide(ApolloClients, {
  default: apolloClient,
})

app.mount('#app')
