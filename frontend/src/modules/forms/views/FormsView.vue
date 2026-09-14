<template>
  <div style="padding: 20px; background: #e8f5e9;">
    <h1>Formularze (Forms)</h1>
    <p>Jesteś na subdomenie: {{ hostname }}</p>
  </div>
</template>

<script setup lang="ts">
const hostname = window.location.hostname
</script>