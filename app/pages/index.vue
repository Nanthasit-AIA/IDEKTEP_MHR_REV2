<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const displayedText = ref("")

const headerMessages = [
  "Mobility Healthcare Robot",
  "Welcome to Robo Assistant Application :-)"
]

let currentIndex = 0
let isTyping = true
let charIndex = 0
let intervalId: number | null = null

const animate = () => {
  const currentMessage = headerMessages[currentIndex] || ""
  if (isTyping) {
    if (charIndex <= currentMessage.length) {
      displayedText.value = currentMessage.substring(0, charIndex)
      charIndex++
    } else {
      if (intervalId !== null) clearInterval(intervalId)
      setTimeout(() => {
        isTyping = false
        charIndex = currentMessage.length
        intervalId = window.setInterval(animate, 50)
      }, 5000)
    }
  } else {
    if (charIndex >= 0) {
      displayedText.value = currentMessage.substring(0, charIndex)
      charIndex--
    } else {
      currentIndex = (currentIndex + 1) % headerMessages.length
      isTyping = true
      charIndex = 0
    }
  }
}

onMounted(() => {
  intervalId = window.setInterval(animate, 100) 
})

onUnmounted(() => {
  if (intervalId !== null) {
    clearInterval(intervalId)
  }
})
</script>

<template>
    <div class="min-h-screen flex flex-col items-center justify-start py-10 px-6 bg-linear-to-r from-violet-200 to-pink-200">

      <!-- Header -->
      <div class="w-full max-w-6xl h-20 bg-black text-white text-3xl font-bold px-10 py-7 rounded-2xl flex items-center gap-7 mb-20">
        <span class="text-2xl">❇</span>
        <div class="min-w-[400px]">
          {{ displayedText }}<span class="text-m animate-pulse"> |</span>
        </div>
      </div>

        <!-- Title -->
        <h1 class="text-[5rem] lg:text-[5rem] font-black text-center mb-16 leading-tight">
            Robo Assistant Application
        </h1>

        <!-- Buttons -->
        <div class="flex flex-col md:flex-row gap-20 w-full max-w-4xl justify-center mt-60">
            <NuxtLink to="/face-verify"
                class="px-20 py-8 bg-black text-white text-3xl font-extrabold rounded-2xl shadow-xl hover:scale-110 transition duration-200 whitespace-nowrap">
                Face Verify
            </NuxtLink>

            <NuxtLink to="/face-register"
                class="px-20 py-8 bg-black text-white text-3xl font-extrabold rounded-2xl shadow-xl hover:scale-110 transition duration-200 whitespace-nowrap">
                Face Register
            </NuxtLink>

            <NuxtLink to="/temp_measurement"
                class="px-20 py-8 bg-black text-white text-3xl font-extrabold rounded-2xl shadow-xl hover:scale-110 transition duration-200 whitespace-nowrap">
                Measurement
            </NuxtLink>
        </div>


        <!-- Footer -->
        <div class="mt-auto flex flex-col items-center justify-center pb-15">

            <footer class="text-m text-black/70 mb-4">
                © 2025 Robo Assist Application. All rights reserved.
            </footer>

            <div class="flex gap-10 items-center justify-center">
                <img src="~/assets/logo/idektep.png" alt="IDEKTEP Logo" class="w-20 h-20 rounded-full" />
                <img src="~/assets/logo/idektep.png" alt="IDEKTEP Logo" class="w-20 h-20 rounded-full" />
                <img src="~/assets/logo/idektep.png" alt="IDEKTEP Logo" class="w-20 h-20 rounded-full" />
            </div>

        </div>

    </div>
</template>

