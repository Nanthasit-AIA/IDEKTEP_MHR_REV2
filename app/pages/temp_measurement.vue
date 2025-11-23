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

// 🔹 Live video & result image
const videoActive = ref(false);
const videoUrl = ref("http://localhost:5000/video_feed");

// 👉 when detection finished, backend sends this
const resultImageUrl = ref<string | null>(null);

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

    // ✅ listen to combined state + indicator from backend
    //    payload shape: { irt_state: { state: string }, irt_indicator: { state: 'm' | 'c' | 'e' } }
    socket.on("irt_update", (payload: { irt_state: IrtState; irt_indicator: IrtIndicator }) => {
        irtState.value = payload.irt_state;
        irtIndicator.value = payload.irt_indicator;

        const state = payload.irt_state.state;

        if (state === "Measuring") {
            measuring.value = true;
            resultImageUrl.value = null; // clear old result when new measurement starts
            videoActive.value = true;
        } else if (
            state === "Complete" ||
            state === "Error" ||
            state === "Ready"
        ) {
            measuring.value = false;
        }

        // ✅ auto-stop video and schedule navigation when complete
        if (state === "Complete") {
            videoActive.value = false;

            if (!autoNavigateTimeout) {
                autoNavigateTimeout = setTimeout(() => {
                    router.push('/bp_measurement');
                }, 5000);
            }
        }
    });

    // 🔹 listen for result image
    socket.on("irt_result", (payload: { image_url: string }) => {
        // combine backend host + relative URL
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
    // Start a new measurement: show video, clear old result
    resultImageUrl.value = null;
    videoActive.value = true;
    irtState.value.state = "Measuring";
};

const handleMeasurementClick = () => {
    // ✅ If measurement already complete, go to BP measurement
    if (irtState.value.state === "Complete") {
        router.push('/bp_measurement');
        return;
    }
    // Otherwise start / restart measurement
    doMeasurement();
};

const indicatorClass = computed(() => {
    // ✅ now controlled by irtIndicator, not irtState
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
    // ✅ no more “Stop” label
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

                            <!-- 2) Otherwise show live video if active -->
                            <template v-else-if="videoActive">
                                <img :src="videoUrl" alt="IR Camera Stream" class="w-full h-full object-cover" />
                            </template>

                            <!-- 3) Otherwise show placeholder text -->
                            <template v-else>
                                <p class="text-black text-xl font-medium">Camera not Active</p>
                            </template>

                            <!-- Temperature Box -->
                            <div class="absolute bottom-3 left-1/2 transform -translate-x-1/2 bg-black rounded-2xl px- py-6 flex items-center justify-between w-[90%]"
                                style="min-width: 60%;">
                                <span class="text-white text-2xl font-bold ml-10">
                                    Temperature : {{ displayTempResult }} °C
                                </span>
                                <span
                                    v-if="irtState.state !== 'Complete'"
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
