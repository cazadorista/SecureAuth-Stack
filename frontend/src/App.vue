<template>
  <RouterView />
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<style>
/* Tutaj możesz dodać globalne style CSS (np. reset marginesów, fonty) */
body {
  margin: 0;
  font-family: system-ui, -apple-system, sans-serif;
}
</style>