<script setup lang="ts">
import HeaderAnimate from '~/components/HeaderAnimate.vue';
import MainActionButton from '~/components/MainActionButton.vue';


const headerMessages = [
    "Mobility Healthcare Robot",
    "Welcome to Robo Assistant Application"
]

const actionButtons = [
    { label: "Face Verify", to: "/face_verify" },
    { label: "Face Register", to: "/face_register" },
    { label: "Measurement", to: "/temp_measurement" }
]
</script>

<template>
    <div
        class="min-h-screen flex flex-col items-center justify-start py-10 px-6 bg-linear-to-r from-violet-200 to-pink-200">

        <!-- Header -->
        <HeaderAnimate :message="headerMessages" />

        <!-- Title -->
        <h1 class="text-[5rem] lg:text-[5rem] font-black text-center mb-1 leading-tight mt-20">
            Robo Assistant Application
        </h1>
        <!-- Robot Image Center -->
        <div class="mt-8 flex justify-center">
        <img
            src="/mhr_image.png"
            alt="Robot"
            class="w-[350px] h-auto object-contain drop-shadow-xl mb-10"
        />
        </div>

        <!-- Buttons -->
        <MainActionButton :buttons="actionButtons" />

        <!-- Footer -->
        <div class="mt-auto flex flex-col items-center justify-center pb-15">

            <footer class="text-m text-black/70 mb-4 mt-10">
                © 2025 Robo Assist Application. All rights reserved.
            </footer>

            <div class="flex gap-10 items-center justify-center">
                <img src="~/assets/logo/idektep.png" alt="IDEKTEP Logo" class="w-20 h-20 rounded-full" />
                <img src="~/assets/logo/logo_ku.png" alt="IDEKTEP Logo" class="w-20 h-20 rounded-full" />
                <img src="~/assets/logo/logo_ku_eng.png" alt="IDEKTEP Logo" class="w-25 h-20 rounded-full" />
            </div>

        </div>

    </div>
</template>
