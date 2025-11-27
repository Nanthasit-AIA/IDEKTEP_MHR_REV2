<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { io, Socket } from 'socket.io-client';

const router = useRouter();

const headerMessages = [
  'Mobility Healthcare Robot',
  'Blood Pressure Measurement',
];

// ---- Types ----
interface BpData {
  systolic: number | null;
  diastolic: number | null;
  pulse?: number | null;
  msg?: string;
  success?: boolean;
}

interface bpIndicator {
  state: string;
}
// ---- State ----

const drawerStatus = ref<'idle' | 'opening' | 'open' | 'closing' | 'closed'>('idle');
const measuring = ref(false);
const bpData = ref<BpData | null>(null);
const bpStateText = ref<string>('Idle');

const bpState = ref<string>('Idle');
const bpIndicator = ref<string>('i');
const measurementDone = ref(false);   // 🔹 NEW

let socket: Socket | null = null;
let drawerOpenTimer: ReturnType<typeof setTimeout> | null = null;
const skipAutoNavigate = ref(false);
let autoNavigateTimeout: ReturnType<typeof setTimeout> | null = null;

// can measure only when drawer open and not measuring
const canMeasure = computed(() => drawerStatus.value === 'open' && !measuring.value);

// ---- Lifecycle ----
onMounted(() => {
  socket = io('http://localhost:5000');

  socket.on('connect', () => {
    console.log('Connected to BP Socket.IO');

    // 1) After navigating to /bp_measurement, wait 2s then open drawer
    drawerOpenTimer = setTimeout(() => {
      socket?.emit('drawer_control', { data: 'med_1DrawerOpen' });
      drawerStatus.value = 'opening';
      bpStateText.value = 'Opening Drawer...';
      bpIndicator.value = 'm';            // 🔹 indicator = moving while drawer opens
    }, 10000);
  });

  // Drawer status from backend (trigger_drawer in app.py)
  socket.on('mhr_status', (payload: { status: string }) => {
    if (payload.status === '1DrawerOpen') {
      drawerStatus.value = 'open';
      bpStateText.value = 'Ready to measure';
      bpIndicator.value = 'c';          // 🔹 drawer open & ready → green
    }

    else if (payload.status === '1DrawerClose') {
      drawerStatus.value = 'closed';
      bpStateText.value = 'Drawer Closed';
      bpIndicator.value = 'i';          // 🔹 drawer closed/idle → gray

      // ❌ If user clicked the Close button → DO NOT auto navigate
      if (skipAutoNavigate.value) {
        console.log("Drawer closed manually → no navigation.");
        skipAutoNavigate.value = false;  // reset
        return;
      }

      // ✅ Auto navigation ONLY when closed by system
      if (!autoNavigateTimeout) {
        autoNavigateTimeout = setTimeout(() => {
          router.push('/anal_measurement');
          autoNavigateTimeout = null;
        }, 5000);
      }
    }
  });


  // Optional: progress messages from bp_module.bp_controller
  socket.on('bp_update', (payload) => {
    if (payload.bp_state?.state) {
      bpState.value = payload.bp_state.state;
      bpStateText.value = payload.bp_state.state;   // 🔹 sync text with bpState when available
    }
    if (payload.bp_indicator?.state) {
      bpIndicator.value = payload.bp_indicator.state;
    }
  });

});

onUnmounted(() => {
  if (drawerOpenTimer) {
    clearTimeout(drawerOpenTimer);
    drawerOpenTimer = null;
  }
  if (autoNavigateTimeout) {
    clearTimeout(autoNavigateTimeout);
    autoNavigateTimeout = null;
  }
  if (socket) {
    socket.disconnect();
    socket = null;
  }
});

// ---- Actions ----
const handleCloseDrawer = () => {
  skipAutoNavigate.value = true;   // ← prevent navigation
  socket?.emit('drawer_control', { data: 'med_1DrawerClose' });
  drawerStatus.value = 'closing';
  bpStateText.value = 'Closing drawer...';
  bpIndicator.value = 'm';         // 🔹 closing drawer → moving
};

const indicatorClass = computed(() => {
  switch (bpIndicator.value) {
    case 'c': return 'bg-green-400';
    case 'm': return 'bg-yellow-400 animate-pulse';
    case 'e': return 'bg-red-500';
    default: return 'bg-gray-300';
  }
});

const canClickMainButton = computed(() => {
  if (measuring.value) return false;

  // Can click when:
  // - ready to measure (drawer open), OR
  // - measurement done and drawer already closed → go to next page
  return canMeasure.value || (measurementDone.value && drawerStatus.value === 'closed');
});

const mainButtonLabel = computed(() => {
  if (measuring.value) return 'Measuring…';
  if (measurementDone.value && drawerStatus.value === 'closed') return 'wellness summary';
  return 'Measurement';
});

const handleMeasurementClick = async () => {
  // 🔹 If measurement already done & drawer is closed → go to /anal_measurement
  if (measurementDone.value && drawerStatus.value === 'closed') {
    if (autoNavigateTimeout) {
      clearTimeout(autoNavigateTimeout);
      autoNavigateTimeout = null;
    }
    router.push('/anal_measurement');
    return;
  }

  if (!canMeasure.value) return;

  measuring.value = true;
  measurementDone.value = false;
  bpData.value = null;
  bpStateText.value = 'Measuring...';

  try {
    // 2) Call backend BP API (bp_controller)
    const res = await $fetch<BpData>('http://localhost:5000/api/bp_measurement', {
      method: 'POST',
      body: {}, // add extra params later if needed
    });

    bpData.value = res;
    bpStateText.value = res.msg ?? (res.success ? 'Measurement Completed' : 'Measurement Failed');

    if (res.success) {
      measurementDone.value = true;   // 🔹 mark as complete
    }
    // 🔹 store BP values for wellness summary (0 / invalid / null → "--")
    const normalize = (val: number | null | undefined): string => {
      if (val == null) return "";
      if (!Number.isFinite(val) || val <= 0) return "";
      return String(val);
    };

    sessionStorage.setItem("wellness_sys", normalize(res.systolic));
    sessionStorage.setItem("wellness_dia", normalize(res.diastolic));
    sessionStorage.setItem("wellness_pulse", normalize(res.pulse));

    // 3) After measurement complete, close drawer
    socket?.emit('drawer_control', { data: 'med_1DrawerClose' });
    drawerStatus.value = 'closing';
  } catch (err) {
    console.error(err);
    bpStateText.value = 'Measurement Error';
    measurementDone.value = false;
  } finally {
    measuring.value = false;
  }
};



// Optional: navigate to other page (you already had this button)
const goToAnalMeasurement = () => {
  router.push('/anal_measurement');
};
</script>

<template>
  <div
    class="min-h-screen flex flex-col items-center justify-start py-10 px-6 bg-linear-to-r from-violet-200 to-pink-200">
    <!-- Header -->
    <HeaderAnimate :message="headerMessages" />

    <div class="w-full max-w-6xl bg-white rounded-2xl shadow-2xl p-10 flex flex-col items-center justify-center mt-5">
      <div class="bg-white rounded-2xl px-1 py-1 w-full">
        <div class="flex items-center justify-center mb-8 relative">

          <!-- Side Button -->
          <button @click="router.back()"
            class="absolute flex items-center left-0 top-0 justify-center w-32 h-16 bg-gray-300 rounded-full hover:bg-gray-400 transition">
            ← Back
          </button>
          <button @click="router.push('/anal_measurement')"
            class="absolute flex items-center right-0 top-0 justify-center w-32 h-16 bg-gray-0 rounded-full hover:bg-gray-400 transition">

          </button>
          <button @click="handleCloseDrawer"
            class="absolute flex items-center right-0 top-40 justify-center w-32 h-16 bg-gray-0 rounded-full hover:bg-gray-400 transition">
          </button>

          <!--  Frame  -->
          <div class="flex flex-col items-center justify-center">
            <div
              class="w-[640px] h-[640px] bg-gray-300 rounded-2xl overflow-hidden flex flex-col items-center justify-center relative"
              style="aspect-ratio: 1;">

              <!-- Blood pressure Box -->
              <div
                class="absolute top-6 left-1/2 transform -translate-x-1/2 bg-black rounded-2xl  py-6 flex items-center justify-between w-[90%]"
                style="min-width: 60%;">
                <span class="text-white text-2xl font-bold ml-5">
                  Blood Pressure
                </span>
                <span class="text-white text-l font-sm w-56 ml-auto text-right">{{ bpStateText }}</span>
                <div :class="['w-8 h-8 rounded-full bg-white mr-10 ml-5', indicatorClass]"></div>
              </div>
              <div
                class="absolute w-[90%] top-40 left-1/2 transform -translate-x-1/2 bg-black rounded-2xl py-8 mt-6 flex justify-between items-center">
                <div class="flex flex-col leading-tight">
                  <span class="text-white text-7xl ml-10 font-black">SYS</span>
                  <span class="text-white text-sm ml-10 mt-3">mmHg</span>
                </div>
                <span class="text-white text-8xl font-black mr-20">{{ bpData?.systolic ?? '--' }}</span>
              </div>
              <div
                class="absolute w-[90%] top-90 left-1/2 transform -translate-x-1/2 bg-black rounded-2xl py-8 mt-6 flex justify-between items-center">
                <div class="flex flex-col leading-tight">
                  <span class="text-white text-7xl ml-10 font-black">DIA</span>
                  <span class="text-white text-sm ml-10 mt-3">mmHg</span>
                </div>
                <span class="text-white text-8xl font-black mr-20">{{ bpData?.diastolic ?? '--' }}</span>
              </div>
              <!-- <div class="absolute w-[90%] top-110 left-1/2 transform -translate-x-1/2 bg-black rounded-2xl py-6 mt-6 flex justify-between items-center">
                                <div class="flex flex-col leading-tight">
                                <span class="text-white text-7xl ml-10 font-black">PULSE</span>
                                <span class="text-white text-sm ml-10 mt-3">BPM</span>
                                </div>
                                <span class="text-white text-8xl font-black mr-20">{{ bpData?.pulse ?? '--' }}</span>
                            </div> -->
            </div>
          </div>

        </div>
      </div>

      <!-- Measurement Button -->
      <button @click="handleMeasurementClick" :disabled="!canClickMainButton" class="px-20 py-8 text-3xl font-extrabold rounded-2xl shadow-xl 
                    hover:scale-110 transition-all duration-600 whitespace-nowrap text-center" :class="canClickMainButton
                      ? 'bg-black text-white hover:bg-blue-600'
                      : 'bg-gray-400 text-gray-700 cursor-not-allowed'">
        {{ mainButtonLabel }}
      </button>

    </div>
  </div>
</template>
