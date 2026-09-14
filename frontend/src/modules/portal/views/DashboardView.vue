<template>
  <div style="padding: 20px;">
    <h1>Subdomena: {{ hostname }}</h1>

    <!-- Czekamy na zakończenie inicjalizacji sesji -->
    <div v-if="!authStore.isInitialized">
      Ładowanie stanu sesji...
    </div>

    <div v-else>
      <div v-if="authStore.authenticated">
        <p>✅ Zalogowano jako: <strong>{{ authStore.user?.preferred_username || authStore.user?.name || 'Użytkownik' }}</strong></p>
        <button @click="authStore.logout()">Wyloguj się</button>
      </div>
      <div v-else>
        <p>❌ Niezalogowany</p>
        <button @click="authStore.login()">Zaloguj się przez Keycloak</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'

const hostname = window.location.hostname
const authStore = useAuthStore()
</script>