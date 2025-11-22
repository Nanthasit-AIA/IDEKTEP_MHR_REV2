<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter()
const headerMessages = [
    "Mobility Healthcare Robot",
    "Analysis Measurement"
]

const actionButtons = [
    { label: "wellness analysis", to: "/" }
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
                    <!-- <button @click="router.back()"
                        class="absolute left-0 top-0 w-14 h-14 rounded-full bg-gray-300 flex items-center justify-center 
                        hover:scale-110 transition-all duration-600 whitespace-nowrap text-center
                        hover:bg-blue-600">
                        <span class="text-2xl font-bold text-gray-700"></span>
                    </button> -->
                    <button @click="router.back()"
                        class="absolute flex items-center left-0 top-0 justify-center w-32 h-16 bg-gray-300 rounded-full hover:bg-gray-400 transition">
                        ← Back
                    </button>
                    <button @click="router.push('/')"
                        class="absolute flex items-center right-0 top-0 justify-center w-32 h-16 bg-gray-0 rounded-full hover:bg-gray-400 transition">

                    </button>


                    <!--  Frame  -->
                    <div class="flex flex-col items-center justify-center">
                        <div class="w-[750px] h-[640px] bg-white rounded-2xl overflow-hidden flex flex-col items-center justify-center relative"
                            style="aspect-ratio: 1;">

                            <!-- Analysis Box -->
                            <div class="absolute w-[90%] top-0 left-1/2 -translate-x-1/2 bg-black rounded-2xl  py-4 text-white flex flex-col ">
                                <!-- Header: title + green status dot -->
                                <div class="w-full flex items-center justify-between border-b-4 border-white pb-4">
                                    <h2 class="text-2xl font-sm px-10">wellness analysis</h2>
                                    <span class="w-6 h-6 rounded-full bg-lime-400 mr-10"></span>
                                </div>

                                <!-- Content -->
                                <div class="flex flex-col md:flex-row items-center gap-8 pt-4">
                                    <!-- Smiley circle -->
                                    <div class="flex items-center justify-center w-32 h-32 rounded-full">
                                        <span class="text-6xl">🙂</span>
                                    </div>

                                    <!-- Text block -->
                                    <div class="flex-1 text-center md:text-left">
                                        <p class="text-xl font-semibold">
                                            Great job! Your vital signs look good today.
                                        </p>

                                        <div class="mt-4 space-y-1 text-lg ml-10">
                                            <p>🌡️temperature - normal</p>
                                            <p>💓blood pressure - balance</p>
                                            <p>🫀pulse - healthy</p>
                                        </div>

                                        <p class="mt-4 text-lg">
                                            Keep maintaining a healthy lifestyle!
                                        </p>
                                    </div>
                                </div>
                            </div>
                            <div class="absolute w-[90%] top-75 left-1/2 -translate-x-1/2 bg-black rounded-2xl  py-4 text-white flex flex-col ">
                                <!-- Header: title + green status dot -->
                                <div class="w-full flex items-center justify-between border-b-4 border-white pb-4">
                                    <h2 class="text-2xl font-sm px-10">wellness summary</h2>
                                </div>

                                <!-- Content -->
                                <div class="flex flex-col md:flex-row items-center justify-center gap-8 pt-4 py-60">
                                    <div
                                        class="absolute w-[70%] top-20 bg-black bg-opacity-100 rounded-2xl py-2 mt-2 flex items-center px-5 hover:scale-110">
                                        <span class="text-white text-2xl mr-4">🌡️</span>
                                        <span class="text-white text-2xl font-sm w-32">Temperature</span>
                                        <span class="text-white text-4xl font-sm ml-30 mr-2">36.0</span>
                                        <span class="text-white text-xl w-16 ml-auto">°C</span>
                                    </div>
                                    <div
                                        class="absolute w-[70%] top-35 bg-black bg-opacity-100 rounded-2xl py-2 mt-2 flex items-center px-5 hover:scale-110">
                                        <span class="text-white text-2xl mr-4">💓</span>
                                        <span class="text-white text-2xl font-sm w-32">SYS</span>
                                        <span class="text-white text-4xl font-sm ml-30 mr-2">120</span>
                                        <span class="text-white text-xl w-16 ml-auto">mmHg</span>
                                    </div>
                                    <div
                                        class="absolute w-[70%] top-50 bg-black bg-opacity-100 rounded-2xl py-2 mt-2 flex items-center px-5 hover:scale-110">
                                        <span class="text-white text-2xl mr-4">💓</span>
                                        <span class="text-white text-2xl font-sm w-32">DIA</span>
                                        <span class="text-white text-4xl font-sm ml-30 mr-2">80</span>
                                        <span class="text-white text-xl w-16 ml-auto">mmHg</span>
                                    </div>
                                    <div
                                        class="absolute w-[70%] top-65 bg-black bg-opacity-100 rounded-2xl py-2 mt-2 flex items-center px-5 hover:scale-110">
                                        <span class="text-white text-2xl mr-4">🫀</span>
                                        <span class="text-white text-2xl font-sm w-32">PULSE</span>
                                        <span class="text-white text-4xl font-sm ml-30 mr-2">100</span>
                                        <span class="text-white text-xl w-16 ml-auto">BPM</span>
                                    </div>
                                </div>
                            </div>
                            <!-- Result Box -->
                            <!-- 
                            <div class="absolute w-[70%] top-90 left-1/2 transform -translate-x-1/2 bg-purple-300 bg-opacity-100 rounded-2xl py-4 mt-6 flex items-center px-5 hover:scale-110">
                                <span class="text-white text-2xl mr-4">💓</span>
                                <span class="text-white text-2xl font-black w-32">SYS</span>
                                <span class="text-white text-4xl font-sm ml-30 mr-2">120</span>
                                <span class="text-white text-xl w-16 ml-auto">mmHg</span>
                            </div>

                            <div class="absolute w-[70%] top-110 left-1/2 transform -translate-x-1/2 bg-blue-300 bg-opacity-100 rounded-2xl py-4 mt-6 flex items-center px-5 hover:scale-110">
                                <span class="text-white text-2xl mr-4">💓</span>
                                <span class="text-white text-2xl font-black w-32">DIA</span>
                                <span class="text-white text-4xl font-sm ml-30 mr-2">80</span>
                                <span class="text-white text-xl w-16 ml-auto">mmHg</span>
                            </div>

                            <div class="absolute w-[70%] top-130 left-1/2 transform -translate-x-1/2 bg-green-300 bg-opacity-100 rounded-2xl py-4 mt-6 flex items-center px-5 hover:scale-110">
                                <span class="text-white text-2xl mr-4">🫀</span>
                                <span class="text-white text-2xl font-black w-32">PULSE</span>
                                <span class="text-white text-4xl font-sm ml-30 mr-2">100</span>
                                <span class="text-white text-xl w-16 ml-auto">BPM</span>
                            </div> -->
                        </div>
                    </div>
                </div>
            </div>


            <!-- Measurement Button -->
            <MainActionButton :buttons="actionButtons" />
        </div>
    </div>
</template>
