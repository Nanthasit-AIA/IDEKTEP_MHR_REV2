<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { io, Socket } from 'socket.io-client';

const router = useRouter()
const headerMessages = [
    "Mobility Healthcare Robot",
    "Temperature Measurement"
]

interface IrtData {
    temp_context: string;
    temp_max: number | null;
    temp_min?: number | null;
    temp_result: number | string | null;
}

interface IrtState {
    state: string;
}

interface IrtIndicator {
    state: string;
}

const irtData = ref<IrtData>({
    temp_context: "",
    temp_max: null,
    temp_min: null,
    temp_result: null
});

const irtState = ref<IrtState>({
    state: "Idle"
});

const irtIndicator = ref<IrtIndicator>({
    state: ""
});

const measuring = ref(false);

// API-Live Stream
const videoActive = ref(false);
const videoUrl = ref("http://localhost:5000/video_feed");

// Result Image
const resultImageUrl = ref<string | null>(null);

const screenWidth = 640;
const screenHeight = 480;

const calulateROI = (
    width: number,
    height: number,
    widthPercent: number = 0.7,
    heightPercent: number = 0.7
) => {
    const roiWidth = Math.floor((width) * widthPercent);
    const roiHeight = Math.floor(height * heightPercent);
    const roiX = Math.floor((width - roiWidth) / 2);
    const roiY = Math.floor((height - roiHeight) / 2);
    return { x: roiX, y: roiY, width: roiWidth, height: roiHeight };
};

const roi = computed(() => calulateROI(screenWidth, screenHeight));
const isMeasuringFace = computed(() => irtState.value.state === "Meas.");
const faceRingStroke = computed(() => (isMeasuringFace.value ? "#22c55e" : "#ef4444"));
const faceRingWidth = computed(() => (isMeasuringFace.value ? 6 : 3));
const faceRingPulseClass = computed(() => (isMeasuringFace.value ? "roi-pulse" : ""));

let socket: Socket | null = null;
let autoNavigateTimeout: ReturnType<typeof setTimeout> | null = null;

onMounted(() => {
    socket = io("http://localhost:5000");

    socket.on("connect", () => {
        console.log("Connected to IRT Socket.IO");
    });

    socket.on("disconnect", () => {
        console.log("Disconnected from IRT Socket.IO");
    });

    socket.on("irt_data", (payload: IrtData) => {
        irtData.value = payload;
    });

    //payload shape: { irt_state: { state: string }, irt_indicator: { state: 'm' | 'c' | 'e' } }
    socket.on("irt_update", (payload: { irt_state: IrtState; irt_indicator: IrtIndicator }) => {
        irtState.value = payload.irt_state;
        irtIndicator.value = payload.irt_indicator;

        const state = payload.irt_state.state;

        if (state === "Measuring") {
            measuring.value = true;
            resultImageUrl.value = null;
            videoActive.value = true;
        } else if (
            state === "Complete" ||
            state === "Error" ||
            state === "Ready"
        ) {
            measuring.value = false;
        }
        if (state === "Complete") {
            videoActive.value = false;

            //Store Final Temperature
            const rawTemp = irtData.value.temp_result;
            let storedTemp = "";

            if (typeof rawTemp === "number") {
                if (Number.isFinite(rawTemp) && rawTemp > 0) {
                    storedTemp = rawTemp.toString();
                }
            } else if (typeof rawTemp === "string") {
                const num = Number(rawTemp);
                if (Number.isFinite(num) && num > 0) {
                    storedTemp = rawTemp;
                }
            }
            sessionStorage.setItem("wellness_temp", storedTemp);

            if (!autoNavigateTimeout) {
                autoNavigateTimeout = setTimeout(() => {
                    router.push('/bp_measurement');
                }, 5000);
            }
        }
    });

    socket.on("irt_result", (payload: { image_url: string }) => {
        resultImageUrl.value = `http://localhost:5000${payload.image_url}`;
        console.log("IRT result image:", resultImageUrl.value);
    });
});

onUnmounted(() => {
    if (socket) {
        socket.disconnect();
        socket = null;
    }
    if (autoNavigateTimeout) {
        clearTimeout(autoNavigateTimeout);
        autoNavigateTimeout = null;
    }
});

const doMeasurement = () => {
    resultImageUrl.value = null;
    videoActive.value = true;
    irtState.value.state = "Measuring";
};

const handleMeasurementClick = () => {
    if (irtState.value.state === "Complete") {
        router.push('/bp_measurement');
        return;
    }
    doMeasurement();
};

const indicatorClass = computed(() => {
    switch (irtIndicator.value.state) {
        case "c":
            return "bg-green-400";
        case "m":
            return "bg-yellow-400 animate-pulse";
        case "e":
            return "bg-red-500";
        default:
            return "bg-gray-300";
    }
});

const buttonLabel = computed(() => {
    const state = irtState.value.state;
    if (state === "Measuring") return "Measuring...";
    if (state === "Complete") return "Measured";
    return "Measurement";
});

const displayTempResult = computed(() => {
    if (irtData.value.temp_result === null || irtData.value.temp_result === undefined) {
        return "";
    }
    return irtData.value.temp_result;
});
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
                    <button @click="router.push('/bp_measurement')"
                        class="absolute flex items-center right-0 top-0 justify-center w-32 h-16 bg-gray-0 rounded-full hover:bg-gray-400 transition">

                    </button>

                    <!-- Camera Frame  -->
                    <div class="flex flex-col items-center justify-center">
                        <div class="w-[640px] h-[640px] bg-gray-300 rounded-2xl overflow-hidden flex flex-col items-center justify-center relative"
                            style="aspect-ratio: 1;">
                            <template v-if="resultImageUrl">
                                <img :src="resultImageUrl" alt="IRT Heatmap Result"
                                    class="w-full h-full object-cover" />
                            </template>

                            <!-- Live Stream -->
                            <template v-else-if="videoActive">
                                <div class="relative w-full h-full">
                                    <img :src="videoUrl" alt="IR Camera Stream" class="w-full h-full object-cover" />

                                    <svg class="absolute top-0 left-0 w-full h-full pointer-events-none"
                                        :viewBox="`0 0 ${screenWidth} ${screenHeight}`" preserveAspectRatio="none">

                                        <defs>
                                            <mask id="circleMask">
                                                <rect width="100%" height="100%" fill="white" />
                                                <circle :cx="screenWidth / 2" :cy="screenHeight / 2"
                                                    :r="Math.min(roi.width, roi.height) / 2" fill="black" />
                                            </mask>
                                        </defs>

                                        <rect width="100%" height="100%" fill="rgb(209, 213, 219)" fill-opacity="1"
                                            mask="url(#circleMask)" />

                                        <circle :cx="screenWidth / 2" :cy="screenHeight / 2"
                                            :r="Math.min(roi.width, roi.height) / 2 + 3" fill="none"
                                            stroke="bg-gray-300" stroke-width="6" />

                                        <circle :cx="screenWidth / 2" :cy="screenHeight / 2"
                                            :r="Math.min(roi.width, roi.height) / 2" fill="none"
                                            :stroke="faceRingStroke" :stroke-width="faceRingWidth"
                                            :class="faceRingPulseClass" />
                                    </svg>
                                </div>
                            </template>

                            <!-- Idel Stage -->
                            <template v-else>
                                <div class="relative w-full h-full flex items-center justify-center">
                                    <p class="text-black text-xl font-medium z-10">Camera not Active</p>
                                    <svg class="absolute top-0 left-0 w-full h-full pointer-events-none"
                                        :viewBox="`0 0 ${screenWidth} ${screenHeight}`" preserveAspectRatio="none">
                                        <defs>
                                            <mask id="circleMaskInactive">
                                                <rect width="100%" height="100%" fill="white" />
                                                <circle :cx="screenWidth / 2" :cy="screenHeight / 2"
                                                    :r="Math.min(roi.width, roi.height) / 2" fill="black" />
                                            </mask>
                                        </defs>

                                        <rect width="100%" height="100%" fill="rgb(209, 213, 219)" fill-opacity="0.7"
                                            mask="url(#circleMaskInactive)" />

                                        <circle :cx="screenWidth / 2" :cy="screenHeight / 2"
                                            :r="Math.min(roi.width, roi.height) / 2 + 3" fill="none"
                                            stroke="bg-gray-300" stroke-width="6" />

                                        <circle :cx="screenWidth / 2" :cy="screenHeight / 2"
                                            :r="Math.min(roi.width, roi.height) / 2" fill="none" stroke="#ef4444"
                                            fill-opacity="0.7" stroke-width="3" />

                                    </svg>
                                </div>
                            </template>

                            <!-- Temperature Box -->
                            <div class="absolute bottom-0 left-1/2 transform -translate-x-1/2 bg-black rounded-2xl px- py-6 flex items-center justify-between w-full"
                                style="min-width: 60%;">
                                <i class="fi fi-rs-temperature-high text-white text-md flex items-center justify-center ml-7 text-2xl" ></i>
                                <span class="text-white text-2xl font-bold ml-5 ">
                                    Temperature : {{ displayTempResult }} °C
                                </span>
                                <span v-if="irtState.state !== 'Complete'"
                                    class="text-white text-l font-sm w-32 ml-auto text-right">
                                    {{ irtState.state }}
                                    <span v-if="irtState.state === 'Meas.' && irtData.temp_max !== null">
                                        {{ irtData.temp_max }}°C
                                    </span>
                                </span>
                                <div :class="['w-8 h-8 rounded-full mr-10 ml-5', indicatorClass]"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Measurement Button -->
            <button @click="handleMeasurementClick" class="px-20 py-8 bg-black text-white text-3xl font-extrabold rounded-2xl shadow-xl 
                hover:scale-110 transition-all duration-600 whitespace-nowrap text-center
                hover:bg-blue-600">
                {{ buttonLabel }}
            </button>
        </div>
    </div>
</template>

