<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { io, Socket } from 'socket.io-client';

const router = useRouter();
const route = useRoute();

const headerMessages = [
  'Mobility Healthcare Robot',
  'Face collection',
];

// ---- Socket ----
const socket = ref<Socket | null>(null);

// ---- User info from previous page ----
// Expect /face_capture?id=XXXX&name=Mr.%20John%20Doe
const personId = ref<string>((route.query.id as string) || '');
const personName = ref<string>((route.query.name as string) || 'Idle');

// ---- Capture state ----
const capturedCount = ref(0);
const totalCount = ref(10);          // must match img_capture in backend
const videoActive = ref(false);
const previewImageUrl = ref<string | null>(null);

// ---- Video URL (MJPEG stream) ----
const videoUrl = computed(() => {
  const base = 'http://localhost:5000/face_collect_feed';
  if (personId.value) {
    return `${base}?id=${encodeURIComponent(personId.value)}`;
  }
  return base;
});

// ---- Indicator color: idle → capturing → done ----
const indicatorClass = computed(() => {
  if (previewImageUrl.value) {
    // capture finished and preview shown
    return 'bg-green-500';
  }
  if (capturedCount.value > 0) {
    // capturing in progress
    return 'bg-yellow-400 animate-pulse';
  }
  // idle
  return 'bg-gray-300';
});

// ---- Start capture when button clicked ----
const startCapture = () => {
  if (!socket.value) return;

  // reset state
  capturedCount.value = 0;
  previewImageUrl.value = null;
  videoActive.value = true;

  socket.value.emit('start_face_collect', {
    id: personId.value,
    name: personName.value,
  });
};

// ---- Lifecycle: connect socket & listen events ----
onMounted(() => {
  socket.value = io('http://localhost:5000');

  socket.value.on('connect', () => {
    console.log('Connected to Socket.IO (face_capture)');
  });

  // single image captured
  socket.value.on('res_collect_face_img', (payload: { count: number; person_id?: string }) => {
    capturedCount.value = payload.count;
    videoActive.value = true;

    // if person name not set, fallback to id from backend
    if (!personId.value && payload.person_id) {
      personId.value = payload.person_id;
    }
  });

  // overall capture status (e.g., "Completed")
  socket.value.on('res_collect_face', (payload: { data: string }) => {
    if (payload.data === 'Completed') {
      console.log('Face capture completed');
      // preview will arrive via res_collect_face_preview
    }
  });

  // final captured image preview
  socket.value.on('res_collect_face_preview', (payload: { image_url: string; person_id?: string }) => {
    const base = 'http://localhost:5000';
    previewImageUrl.value = payload.image_url.startsWith('http')
      ? payload.image_url
      : base + payload.image_url;

    videoActive.value = false;

    if (!personId.value && payload.person_id) {
      personId.value = payload.person_id;
    }
  });
});

onUnmounted(() => {
  if (socket.value) {
    socket.value.disconnect();
    socket.value = null;
  }
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

          <!-- Back Button -->
          <button @click="router.back()"
            class="absolute flex items-center left-0 top-0 justify-center w-32 h-16 bg-gray-300 rounded-full hover:bg-gray-400 transition">
            ← Back
          </button>

          <!-- Next Button -->
          <button @click="router.push('/face_id')"
            class="absolute flex items-center right-0 top-0 justify-center w-32 h-16 bg-gray-300 rounded-full hover:bg-gray-400 transition">
          </button>

          <!-- Camera Frame -->
          <div class="flex flex-col items-center justify-center">
            <div
              class="w-[640px] h-[640px] bg-gray-300 rounded-2xl overflow-hidden flex flex-col items-center justify-center relative"
              style="aspect-ratio: 1;">

              <!-- 1) Show final captured face -->
              <template v-if="previewImageUrl">
                <img :src="previewImageUrl" class="w-full h-full object-cover" />
              </template>

              <!-- 2) Show live camera -->
              <template v-else-if="videoActive">
                <img :src="videoUrl" class="w-full h-full object-cover" />
              </template>

              <!-- 3) Default placeholder -->
              <template v-else>
                <p class="text-black text-xl font-medium">Camera not Active</p>
              </template>

              <!-- Bottom Capture Status Box -->
              <div
                class="absolute bottom-3 left-1/2 transform -translate-x-1/2 bg-black rounded-2xl py-6 px-6 flex items-center justify-between w-[90%]"
                style="min-width: 60%;">

                <!-- Name from register -->
                <span class="text-white text-xl font-bold ml-5">
                  Face collect : {{ personName }}
                </span>

                <!-- Count -->
                <span class="text-white text-xl w-32 ml-auto text-right">
                  {{ capturedCount }}/{{ totalCount }}
                </span>

                <!-- Indicator -->
                <div :class="['w-8 h-8 rounded-full ml-5 mr-5', indicatorClass]"></div>

              </div>
            </div>
          </div>

        </div>
      </div>

      <!-- Capture Button -->
      <button @click="startCapture" class="px-20 py-8 bg-black text-white text-3xl font-extrabold rounded-2xl shadow-xl 
               hover:scale-110 transition-all duration-600 whitespace-nowrap text-center
               hover:bg-blue-600">
        Face Capture
      </button>
    </div>
  </div>
</template>
