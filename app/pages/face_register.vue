<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const headerMessages = [
  "Mobility Healthcare Robot",
  "Information Register"
];

// Form fields
const title = ref('');
const firstName = ref('');
const lastName = ref('');
const additionalInfo = ref('');

const handleRegister = async () => {
  if (!firstName.value || !lastName.value) {
    alert("Please enter at least first name and last name.");
    return;
  }

  try {
    // POST to backend
    const res: { id: string } = await $fetch("http://localhost:5000/api/register_information", {
      method: "POST",
      body: {
        title: title.value,
        first_name: firstName.value,
        last_name: lastName.value,
        additional_info: additionalInfo.value,
      },
    });

    const fullName = `${title.value} ${firstName.value} ${lastName.value}`.trim();

    // Navigate to face_capture with generated ID + Name
    router.push({
      path: "/face_capture",
      query: {
        id: res.id,
        name: fullName,
      },
    });

  } catch (err) {
    console.error("Register error:", err);
    alert("Error saving data.");
  }
};
</script>


<template>
  <div
    class="min-h-screen flex flex-col items-center justify-start py-10 px-6 bg-linear-to-r from-violet-200 to-pink-200">

    <!-- Header -->
    <HeaderAnimate :message="headerMessages" />

    <div class="w-full max-w-6xl bg-white rounded-2xl shadow-2xl p-10 mt-5">

      <!-- Top Buttons + Frame -->
      <div class="flex items-center justify-center mb-10 relative">

        <!-- Back Button -->
        <button
          @click="router.back()"
          class="absolute left-0 top-0 flex items-center justify-center w-32 h-16 bg-gray-300 rounded-full hover:bg-gray-400 transition">
          ← Back
        </button>

        <!-- Next Button -->
        <button
          @click="router.push('/face_capture')"
          class="absolute right-0 top-0 flex items-center justify-center w-32 h-16 bg-gray-300 rounded-full hover:bg-gray-400 transition">
          Next →
        </button>
      </div>

      <!-- Form Section -->
      <div class="w-full px-6">

        <!-- Title -->
        <label class="block text-2xl font-bold mb-2 mt-20">Title</label>
        <select v-model="title"
          class="w-full text-2xl p-5 border rounded-xl mb-6 bg-gray-50 focus:ring-4 focus:ring-violet-300">
          <option value="">Select</option>
          <option>Mr.</option>
          <option>Ms.</option>
          <option>Mrs.</option>
        </select>

        <!-- First Name -->
        <label class="block text-2xl font-bold mb-2">First Name</label>
        <input
          v-model="firstName"
          type="text"
          placeholder="Enter first name"
          class="w-full text-2xl p-5 border rounded-xl mb-6 bg-gray-50 focus:ring-4 focus:ring-violet-300"
        />

        <!-- Last Name -->
        <label class="block text-2xl font-bold mb-2">Last Name</label>
        <input
          v-model="lastName"
          type="text"
          placeholder="Enter last name"
          class="w-full text-2xl p-5 border rounded-xl mb-6 bg-gray-50 focus:ring-4 focus:ring-violet-300"
        />

        <!-- Additional Information -->
        <label class="block text-2xl font-bold mb-2">Additional Information</label>
        <textarea
          v-model="additionalInfo"
          rows="3"
          placeholder="Enter additional details"
          class="w-full text-2xl p-5 border rounded-xl bg-gray-50 focus:ring-4 focus:ring-violet-300"
        ></textarea>

      </div>

      <!-- Register Button -->
      <div class="flex justify-center mt-6">
        <button
        @click="handleRegister"
        class="px-20 py-8 bg-black text-white text-3xl font-extrabold rounded-2xl shadow-xl 
        hover:scale-110 transition-all duration-600 hover:bg-blue-600">
        Register
        </button>
      </div>

    </div>
  </div>
</template>
