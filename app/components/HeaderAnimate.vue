<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

const props = defineProps<{
    message: string[]
}>()

const displayedText = ref("")
let currentIndex = 0
let isTyping = true
let charIndex = 0
let intervalId: number | null = null

const animate = () => {
    const currentMessage = props.message[currentIndex] || ""
    if (isTyping) {
        if (charIndex <= currentMessage.length) {
            displayedText.value = currentMessage.substring(0, charIndex)
            charIndex++
        } else {
            if (intervalId != null) clearInterval(intervalId)
            setTimeout(() => {
                isTyping = false
                intervalId = window.setInterval(animate, 50)
            }, 3000)
        }
    } else {
        if (charIndex >= 0) {
            displayedText.value = currentMessage.substring(0, charIndex)
            charIndex--
        } else {
            currentIndex = (currentIndex + 1) % props.message.length
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
    <div
        class="w-full max-w-6xl h-20 bg-black text-white text-3xl font-bold px-10 py-7 mt-5 rounded-2xl flex items-center gap-7">
        <i class="fi fi-sr-user-robot text-md flex items-center justify-center ml-7 text-3xl text-blue-500"></i>
        <div class="mix-w-[400px]">
            {{ displayedText }}<span class="animate-pluse"> |</span>
        </div>
    </div>
</template>
