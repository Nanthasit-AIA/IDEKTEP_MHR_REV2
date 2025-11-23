<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter()
const headerMessages = [
    "Mobility Healthcare Robot",
    "Blood Pressure Measurement"
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
                    <button
                        @click="router.back()"
                        class="absolute flex items-center left-0 top-0 justify-center w-32 h-16 bg-gray-300 rounded-full hover:bg-gray-400 transition"
                        >
                        ← Back
                    </button>
                    <button
                        @click="router.push('/anal_measurement')"
                        class="absolute flex items-center right-0 top-0 justify-center w-32 h-16 bg-gray-0 rounded-full hover:bg-gray-400 transition"
                        >

                    </button>

                    <!--  Frame  -->
                    <div class="flex flex-col items-center justify-center">
                        <div class="w-[640px] h-[640px] bg-gray-300 rounded-2xl overflow-hidden flex flex-col items-center justify-center relative"
                            style="aspect-ratio: 1;">

                            <!-- Blood pressure Box -->
                            <div class="absolute top-6 left-1/2 transform -translate-x-1/2 bg-black rounded-2xl  py-6 flex items-center justify-between w-[90%]"
                                style="min-width: 60%;">
                                <span class="text-white text-2xl font-bold ml-5">
                                    Blood Pressure
                                </span>
                                <span class="text-white text-l font-sm w-32 ml-auto">blood pressure</span>
                                <div :class="['w-8 h-8 rounded-full bg-white mr-10']"></div>
                            </div>
                            <div class="absolute w-[90%] top-30 left-1/2 transform -translate-x-1/2 bg-black rounded-2xl py-6 mt-6 flex justify-between items-center">
                                <div class="flex flex-col leading-tight">
                                <span class="text-white text-7xl ml-10 font-black">SYS</span>
                                <span class="text-white text-sm ml-10 mt-3">mmHg</span>
                                </div>
                                <span class="text-white text-8xl font-black mr-20">120</span>
                            </div>
                            <div class="absolute w-[90%] top-70 left-1/2 transform -translate-x-1/2 bg-black rounded-2xl py-6 mt-6 flex justify-between items-center">
                                <div class="flex flex-col leading-tight">
                                <span class="text-white text-7xl ml-10 font-black">DIA</span>
                                <span class="text-white text-sm ml-10 mt-3">mmHg</span>
                                </div>
                                <span class="text-white text-8xl font-black mr-20">80</span>
                            </div>
                            <div class="absolute w-[90%] top-110 left-1/2 transform -translate-x-1/2 bg-black rounded-2xl py-6 mt-6 flex justify-between items-center">
                                <div class="flex flex-col leading-tight">
                                <span class="text-white text-7xl ml-10 font-black">PULSE</span>
                                <span class="text-white text-sm ml-10 mt-3">BPM</span>
                                </div>
                                <span class="text-white text-8xl font-black mr-20">80</span>
                            </div>
                        </div>
                    </div>

                </div>
            </div>

            <!-- Measurement Button -->
            <button
                class="px-20 py-8 bg-black text-white text-3xl font-extrabold rounded-2xl shadow-xl 
                hover:scale-110 transition-all duration-600 whitespace-nowrap text-center
                hover:bg-blue-600" >
                Measurement
            </button>
        </div>
    </div>
</template>
