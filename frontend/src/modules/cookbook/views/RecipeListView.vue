<template>
  <div style="padding: 20px; background: #fff3e0;">
    <h1>Książka Kucharska (Cookbook)</h1>
    <p>Jesteś na subdomenie: {{ hostname }}</p>
  </div>
</template>

<script setup lang="ts">
const hostname = window.location.hostname
</script>