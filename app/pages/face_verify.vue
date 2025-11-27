<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { io, Socket } from 'socket.io-client';

const router = useRouter()
const headerMessages = [
    "Mobility Healthcare Robot",
    "Temperature Measurement"
]
</script>

<template>
    <div
        class="min-h-screen flex flex-col items-center justify-start py-10 px-6 bg-linear-to-r from-violet-200 to-pink-200">
        <!-- Header -->
        <HeaderAnimate :message="headerMessages" />

        <div
            class="w-full max-w-6xl bg-white rounded-2xl shadow-2xl p-10 flex flex-col items-center justify-center mt-5">
            <div class="bg-white rounded-2xl px-1 py-1 w-full">
                <div class="flex items-center justify-center mb-8 relative">

                    <!-- Side Button -->
                    <button @click="router.back()"
                        class="absolute flex items-center left-0 top-0 justify-center w-32 h-16 bg-gray-300 rounded-full hover:bg-gray-400 transition">
                        ← Back
                    </button>
                    <button @click="router.push('/face_id')"
                        class="absolute flex items-center right-0 top-0 justify-center w-32 h-16 bg-gray-0 rounded-full hover:bg-gray-400 transition">

                    </button>

                    <!-- Camera Frame  -->
                    <div class="flex flex-col items-center justify-center">
                        <div class="w-[640px] h-[640px] bg-gray-300 rounded-2xl overflow-hidden flex flex-col items-center justify-center relative"
                            style="aspect-ratio: 1;">
                            <!-- <template v-if="resultImageUrl">
                                <img :src="resultImageUrl" alt="IRT Heatmap Result"
                                    class="w-full h-full object-cover" />
                            </template>

2) Otherwise show live video if active -->
                            <!-- <template v-else-if="videoActive">
                                <img :src="videoUrl" alt="IR Camera Stream" class="w-full h-full object-cover" />
                            </template> -->

                            <!-- 3) Otherwise show placeholder text -->
                            <template>
                                <p class="text-black text-xl font-medium">Camera not Active</p>
                            </template>

                            <!-- Temperature Box -->
                            <div class="absolute bottom-3 left-1/2 transform -translate-x-1/2 bg-black rounded-2xl px- py-6 flex items-center justify-between w-[90%]"
                                style="min-width: 60%;">
                                <span class="text-white text-2xl font-bold ml-10">
                                    Face verify :
                                </span>
                                <span class="text-white text-l font-sm w-32 ml-auto text-right">
                                    analysis..
                                </span>
                                <div :class="['w-8 h-8 rounded-full bg-white mr-10 ml-5']"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Measurement Button -->
            <button class="px-20 py-8 bg-black text-white text-3xl font-extrabold rounded-2xl shadow-xl 
                hover:scale-110 transition-all duration-600 whitespace-nowrap text-center
                hover:bg-blue-600">
                Face verify
            </button>
        </div>
    </div>
</template>
