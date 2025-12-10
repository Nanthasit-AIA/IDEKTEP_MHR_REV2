<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const headerMessages = [
  'Mobility Healthcare Robot',
  'Analysis Measurement',
];

const analysisDone = ref(false)
// ---------- Wellness summary state ----------
const tempSummary = ref<string>('−−');
const sysSummary = ref<string>('−−');
const diaSummary = ref<string>('−−');
const pulseSummary = ref<string>('−−');

// ---------- Wellness analysis state ----------
const analysisMain = ref<string>('');      // main sentence
const analysisFooter = ref<string>('');    // footer sentence
const analysisTempLine = ref<string>('');  // "temperature - xxx"
const analysisBpLine = ref<string>('');    // "blood pressure - xxx"

const isAnalyzing = ref<boolean>(false);        // spinner control
const canClickMainButton = ref<boolean>(false); // enable button after data ready


// ---------- Indicator (status dot) ----------
type Indicator = 'c' | 'm' | 'e' | '';
const analIndicator = ref<Indicator>(''); // c = good, m = medium, e = error

const indicatorClass = computed(() => {
  switch (analIndicator.value) {
    case 'c':
      return 'bg-green-400';
    case 'm':
      return 'bg-yellow-400 animate-pulse';
    case 'e':
      return 'bg-red-500';
    default:
      return 'bg-gray-300';
  }
});

// ---------- Status text (idle / analysis... / result) ----------
const analStatusText = computed(() => {
  // Stage 2 – while analyzing
  if (isAnalyzing.value) {
    return 'analysis...';
  }

  // Stage 3 – result shown
  switch (analIndicator.value) {
    case 'c':
      return 'normal';
    case 'm':
      return 'caution';
    case 'e':
      return 'alert';
    default:
      // Stage 1 – idle (no analysis yet)
      return 'idle';
  }
});

const mainButtonLabel = computed(() =>
  !analysisDone.value ? 'wellness analysis' : 'save & back to home'
);

// ---------- Helpers ----------
const formattedTempSummary = computed(() => {
  const n = Number(tempSummary.value);
  return Number.isFinite(n) ? n.toFixed(1) : tempSummary.value;
});

const normalizeMeasurement = (raw: string | null): string => {
  if (!raw) return '−−';
  const num = Number(raw);
  if (!Number.isFinite(num) || num <= 0) return '−−';
  return raw;
};

const toNumber = (val: string): number | null => {
  const n = Number(val);
  return Number.isFinite(n) && n > 0 ? n : null;
};

// ---------- Core analysis logic ----------
const runWellnessAnalysis = () => {
  const t = toNumber(tempSummary.value);
  const s = toNumber(sysSummary.value);
  const d = toNumber(diaSummary.value);

  type Level = 'missing' | 'low' | 'normal' | 'high';

  let tempLevel: Level = 'missing';
  if (t !== null) {
    if (t >= 37.6) tempLevel = 'high';
    else if (t <= 35.5) tempLevel = 'low';
    else tempLevel = 'normal';
  }

  let bpLevel: Level = 'missing';
  if (s !== null && d !== null) {
    if (s >= 140 || d >= 90) bpLevel = 'high';
    else if (s < 90 || d < 60) bpLevel = 'low';
    else bpLevel = 'normal';
  }

  // lines under the main text
  analysisTempLine.value =
    tempLevel === 'missing'
      ? 'temperature – not available'
      : tempLevel === 'high'
        ? 'temperature – high'
        : tempLevel === 'low'
          ? 'temperature – low'
          : 'temperature – normal';

  analysisBpLine.value =
    bpLevel === 'missing'
      ? 'blood pressure – not available'
      : bpLevel === 'high'
        ? 'blood pressure – high'
        : bpLevel === 'low'
          ? 'blood pressure – low'
          : 'blood pressure – balance';

  // --------- choose main + footer + indicator ----------
  // no data
  if (tempLevel === 'missing' && bpLevel === 'missing') {
    analIndicator.value = '';
    analysisMain.value = "We couldn't get a clear reading this time.";
    analysisFooter.value = 'Please try the measurement again for accurate results.';
    return;
  }

  // 1) both normal
  if (tempLevel === 'normal' && bpLevel === 'normal') {
    analIndicator.value = 'c'; // green
    analysisMain.value = 'Great job! Your vital signs look good today.';
    analysisFooter.value = 'Keep maintaining a healthy lifestyle!';
    return;
  }

  // 2) temp high, BP normal
  if (tempLevel === 'high' && bpLevel === 'normal') {
    analIndicator.value = 'm'; // yellow
    analysisMain.value = 'Your temperature is slightly elevated.';
    analysisFooter.value = 'Rest, drink plenty of fluids, and monitor how you feel.';
    return;
  }

  // 3) temp low, BP normal
  if (tempLevel === 'low' && bpLevel === 'normal') {
    analIndicator.value = 'm'; // yellow
    analysisMain.value = 'Your temperature is lower than usual.';
    analysisFooter.value = 'Keep yourself warm and recheck if you still feel unwell.';
    return;
  }

  // 4) temp normal, BP high
  if (tempLevel === 'normal' && bpLevel === 'high') {
    analIndicator.value = 'e'; // red
    analysisMain.value = 'Your blood pressure is higher than the normal range.';
    analysisFooter.value =
      'Try to relax, limit salty foods today, and consider checking your BP again soon.';
    return;
  }

  // 5) temp normal, BP low
  if (tempLevel === 'normal' && bpLevel === 'low') {
    analIndicator.value = 'm'; // yellow
    analysisMain.value = 'Your blood pressure is lower than normal.';
    analysisFooter.value =
      'Drink enough water and stand up slowly to avoid dizziness.';
    return;
  }

  // 6) temp high & BP high
  if (tempLevel === 'high' && bpLevel === 'high') {
    analIndicator.value = 'e'; // red
    analysisMain.value =
      'Your temperature and blood pressure are both above normal levels.';
    analysisFooter.value =
      'Please rest and monitor closely. Seek medical advice if symptoms persist.';
    return;
  }

  // 7) temp high & BP low
  if (tempLevel === 'high' && bpLevel === 'low') {
    analIndicator.value = 'e'; // red
    analysisMain.value =
      'Your temperature is elevated and your blood pressure is lower than normal.';
    analysisFooter.value =
      'Stay hydrated and rest. Seek medical advice if you feel weak or dizzy.';
    return;
  }

  // 8) only BP known
  if (tempLevel === 'missing' && bpLevel !== 'missing') {
    if (bpLevel === 'normal') {
      analIndicator.value = 'c';
      analysisMain.value = 'Your blood pressure is within the normal range.';
      analysisFooter.value = 'Keep up the good lifestyle habits.';
    } else if (bpLevel === 'low') {
      analIndicator.value = 'm';
      analysisMain.value = 'Your blood pressure is lower than normal.';
      analysisFooter.value =
        'Drink enough water and stand up slowly to avoid dizziness.';
    } else {
      analIndicator.value = 'e';
      analysisMain.value = 'Your blood pressure is higher than the normal range.';
      analysisFooter.value =
        'Try to relax today and consider rechecking or consulting a healthcare professional.';
    }
    return;
  }

  // 9) only temperature known
  if (bpLevel === 'missing' && tempLevel !== 'missing') {
    if (tempLevel === 'normal') {
      analIndicator.value = 'c';
      analysisMain.value = 'Your temperature is within the normal range.';
      analysisFooter.value = 'Keep maintaining a healthy lifestyle!';
    } else if (tempLevel === 'low') {
      analIndicator.value = 'm';
      analysisMain.value = 'Your temperature is lower than usual.';
      analysisFooter.value =
        'Keep yourself warm and recheck if you still feel unwell.';
    } else {
      analIndicator.value = 'm';
      analysisMain.value = 'Your temperature is slightly elevated.';
      analysisFooter.value =
        'Rest, drink plenty of fluids, and monitor how you feel.';
    }
    return;
  }

  // fallback
  analIndicator.value = 'm';
  analysisMain.value = 'Your measurements show some values outside the normal range.';
  analysisFooter.value =
    'Monitor your condition and consider consulting a healthcare professional.';
};
const saveMeasurementAndGoHome = async () => {
  // convert display text into numbers or null
  const payload = {
    temp: toNumber(tempSummary.value),
    systolic: toNumber(sysSummary.value),
    diastolic: toNumber(diaSummary.value),
    pulse: toNumber(pulseSummary.value),
    indicator: analIndicator.value,
  };

  try {
    await $fetch('http://localhost:5000/api/save_measurement', {
      method: 'POST',
      body: payload,
    });

    // ✅ clear all stage / state
    tempSummary.value = '−−';
    sysSummary.value = '−−';
    diaSummary.value = '−−';
    pulseSummary.value = '−−';

    analysisMain.value = '';
    analysisFooter.value = '';
    analysisTempLine.value = '';
    analysisBpLine.value = '';

    analIndicator.value = '';
    isAnalyzing.value = false;
    canClickMainButton.value = false;
    analysisDone.value = false;

    // optional: clear session values so next time is fresh
    sessionStorage.removeItem('wellness_temp');
    sessionStorage.removeItem('wellness_sys');
    sessionStorage.removeItem('wellness_dia');
    sessionStorage.removeItem('wellness_pulse');

    // ✅ go back home
    router.push('/');
  } catch (err) {
    console.error('Failed to save measurement', err);
    // you can show a toast / error text here if you like
  }
};
// ---------- Button handler ----------

const handleMeasurementClick = () => {
  // block when data not ready or still analyzing
  if (isAnalyzing.value || !canClickMainButton.value) return;

  // 🟡 1st click: run analysis
  if (!analysisDone.value) {
    isAnalyzing.value = true;
    analIndicator.value = 'm'; // yellow while thinking

    // clear previous analysis while "thinking"
    analysisMain.value = '';
    analysisFooter.value = '';
    analysisTempLine.value = '';
    analysisBpLine.value = '';

    setTimeout(() => {
      runWellnessAnalysis();   // sets analIndicator to c/m/e
      isAnalyzing.value = false;
      analysisDone.value = true; // ✅ mark analysis finished
    }, 2000);

    return;
  }

  // ✅ 2nd click: save & go home
  saveMeasurementAndGoHome();
};


// ---------- Lifecycle ----------
onMounted(() => {
  const temp = sessionStorage.getItem('wellness_temp');
  const sys = sessionStorage.getItem('wellness_sys');
  const dia = sessionStorage.getItem('wellness_dia');
  const pulse = sessionStorage.getItem('wellness_pulse');

  // first show "−−", then update after 2s
  setTimeout(() => {
    tempSummary.value = normalizeMeasurement(temp);
    sysSummary.value = normalizeMeasurement(sys);
    diaSummary.value = normalizeMeasurement(dia);
    pulseSummary.value = normalizeMeasurement(pulse);

    // allow analysis after numbers are visible
    canClickMainButton.value = true;
  }, 2000);
});
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
            <div
              class="w-[750px] h-[640px] bg-white rounded-2xl overflow-hidden flex flex-col items-center justify-center relative"
              style="aspect-ratio: 1;">

              <!-- Analysis Box -->
              <div
                class="absolute w-[90%] top-0 left-1/2 -translate-x-1/2 bg-black rounded-2xl py-6 text-white flex flex-col">

                <!-- Header row -->
                <div class="w-full flex items-center justify-between border-b-4 border-white pb-4">
                  <h2 class="text-2xl font-sm px-10">wellness analysis</h2>
                  <span class="text-white text-l font-sm w-24 ml-auto text-right">{{ analStatusText }}</span>

                  <!-- ★ Indicator Dot -->
                  <div :class="['w-8 h-8 rounded-full mr-10 ml-5', indicatorClass]"></div>
                </div>

                <!-- Analysis Content -->
                <div class="flex flex-col md:flex-row items-center justify-center gap-8 pt-8 py-8">

                  <!-- Emoji / Spinner -->
                  <div class="flex items-center justify-center w-32 h-32 rounded-full">

                    <!-- Loading spinner -->
                    <div v-if="isAnalyzing"
                      class="w-16 h-16 border-4 border-white border-t-transparent rounded-full animate-spin ml-10">
                    </div>

                    <!-- Result emoji -->
                    <span v-else-if="analIndicator === 'c'" class="text-6xl ml-10">
                      😊
                    </span>

                    <span v-else-if="analIndicator === 'm'" class="text-6xl ml-10">
                      😕
                    </span>

                    <span v-else-if="analIndicator === 'e'" class="text-6xl ml-10">
                      ☹️
                    </span>

                    <!-- Idle (blank) -->
                    <span v-else class="text-6xl ml-10"></span>
                  </div>

                  <!-- Main Text -->
                  <div class="flex-1 text-center md:text-left">

                    <!-- Main message -->
                    <p v-if="analysisMain" class="text-xl font-semibold">
                      {{ analysisMain }}
                    </p>

                    <!-- Lines -->
                    <div class="mt-4 space-y-1 text-lg ml-10">
                      <p v-if="analysisTempLine">🌡️ {{ analysisTempLine }}</p>
                      <p v-if="analysisBpLine">🩸 {{ analysisBpLine }}</p>
                    </div>

                    <!-- Footer message -->
                    <p v-if="analysisFooter" class="mt-8 text-lg">
                      {{ analysisFooter }}
                    </p>
                  </div>
                </div>
              </div>
              <div
                class="absolute w-[90%] top-85 left-1/2 -translate-x-1/2 bg-black rounded-2xl  py-4 text-white flex flex-col ">
                <!-- Header: title + green status dot -->
                <div class="w-full flex items-center justify-between border-b-4 border-white pb-4">
                  <h2 class="text-2xl font-sm px-10">wellness summary</h2>
                </div>

                <!-- Content -->
                <div class="flex flex-col md:flex-row items-center justify-center gap-8 pt-4 py-48">
                  <div
                    class="absolute w-[70%] top-20 bg-black bg-opacity-100 rounded-2xl py-2 mt-2 flex items-center px-5 hover:scale-110">
                    <i class="fi fi-rs-temperature-high text-md flex items-center justify-center mr-4 text-2xl" />
                    <span class="text-white text-2xl font-sm w-32 mr-20">Temperature</span>
                    <span class="text-white text-4xl font-sm mr-2 ml-auto text-right">{{ formattedTempSummary }}</span>
                    <span class="text-white text-xl w-16 ml-auto">°C</span>
                  </div>
                  <div
                    class="absolute w-[70%] top-35 bg-black bg-opacity-100 rounded-2xl py-2 mt-2 flex items-center px-5 hover:scale-110">
                    <i class="fi fi-rs-blood text-md flex items-center justify-center mr-4 text-2xl" />
                    <span class="text-white text-2xl font-sm w-32 mr-20">SYS</span>
                    <span class="text-white text-4xl font-sm  mr-2 ml-auto text-right">{{ sysSummary }}</span>
                    <span class="text-white text-xl w-16 ml-auto">mmHg</span>
                  </div>
                  <div
                    class="absolute w-[70%] top-50 bg-black bg-opacity-100 rounded-2xl py-2 mt-2 flex items-center px-5 hover:scale-110">
                    <i class="fi fi-rs-blood text-md flex items-center justify-center mr-4 text-2xl" />
                    <span class="text-white text-2xl font-sm w-32 mr-20">DIA</span>
                    <span class="text-white text-4xl font-sm mr-2 ml-auto text-right">{{ diaSummary }}</span>
                    <span class="text-white text-xl w-16 ml-auto">mmHg</span>
                  </div>
                  <!-- <div
                                        class="absolute w-[70%] top-65 bg-black bg-opacity-100 rounded-2xl py-2 mt-2 flex items-center px-5 hover:scale-110">
                                        <span class="text-white text-2xl mr-4">🫀</span>
                                        <span class="text-white text-2xl font-sm w-32">PULSE</span>
                                        <span class="text-white text-4xl font-sm ml-30 mr-2">100</span>
                                        <span class="text-white text-xl w-16 ml-auto">BPM</span>
                                    </div> -->
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <button @click="handleMeasurementClick"
              :disabled="!canClickMainButton || isAnalyzing"
              class="px-20 py-8 text-3xl font-extrabold rounded-2xl shadow-xl 
                    hover:scale-110 transition-all duration-600 whitespace-nowrap text-center"
              :class="!canClickMainButton || isAnalyzing
                      ? 'bg-gray-400 text-gray-700 cursor-not-allowed'
                      : 'bg-black text-white hover:bg-blue-600'">
        {{ mainButtonLabel }}
      </button>
    </div>
  </div>
</template>
