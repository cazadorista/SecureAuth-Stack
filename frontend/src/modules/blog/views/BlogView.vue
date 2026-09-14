<template>
  <div style="padding: 20px; background: #f3e5f5;">
    <h1>Blog (Blog)</h1>
    <p>Jesteś na subdomenie: {{ hostname }}</p>
  </div>
</template>

<script setup lang="ts">
const hostname = window.location.hostname
</script>