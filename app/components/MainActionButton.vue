<script setup lang="ts">
const props = defineProps<{
  buttons: {
    label: string
    to: string
  }[]
}>()
</script>

<template>
  <div class="flex flex-col md:flex-row gap-20 w-full max-w-4xl justify-center ">
    <NuxtLink
      v-for="(button, index) in buttons"
      :key="index"
      :to="button.to"
      class="px-20 py-8 bg-black text-white text-3xl font-sm rounded-2xl shadow-xl 
             hover:scale-110 transition-all duration-600 whitespace-nowrap text-center
             hover:bg-blue-600"
    >
      {{ button.label }}
    </NuxtLink>
  </div>
</template>
