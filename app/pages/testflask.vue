<script setup>
const { data, pending, error } = await useFetch('http://localhost:5000/api/hello')
</script>

<template>
  <div>
    <p v-if="pending">Loading...</p>
    <p v-else-if="error">Error loading API</p>
    <p v-else>{{ data.message }}</p>
  </div>
</template>