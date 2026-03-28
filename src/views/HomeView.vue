<template>
  <div class="home">
    <!-- Hero Carousel -->
    <div class="carousel">
      <div class="carousel-track" :style="{ transform: `translateX(-${currentSlide * 100}%)` }">
        <div v-for="(slide, i) in allSlides" :key="i" class="carousel-slide" :style="{ background: slide.bg }">
          <img v-if="slide.img" :src="slide.img" :alt="slide.title || `Poster ${i + 1}`" class="carousel-img" />
          <div class="carousel-overlay" v-if="slide.title">
            <h2 class="carousel-title">{{ slide.title }}</h2>
            <p v-if="slide.subtitle" class="carousel-subtitle">{{ slide.subtitle }}</p>
          </div>
        </div>
      </div>
      <template v-if="allSlides.length > 1">
        <button class="carousel-btn carousel-prev" @click="prevSlide">&#8249;</button>
        <button class="carousel-btn carousel-next" @click="nextSlide">&#8250;</button>
        <div class="carousel-dots">
          <button
            v-for="(_, i) in allSlides"
            :key="i"
            class="carousel-dot"
            :class="{ active: currentSlide === i }"
            @click="currentSlide = i"
          ></button>
        </div>
      </template>
    </div>

    <!-- About Section -->
    <div class="home-section">
      <h2>About Spectrum</h2>
      <p>
        Spectrum is the annual inter-departmental sports tournament of the Indian Institute of Science, Bangalore.
        Bringing together students, staff, faculty, and alumni across <strong>20 sporting events</strong>,
        Spectrum is a celebration of athleticism, teamwork, and campus spirit.
      </p>
      <p>
        From the track to the chessboard, from the pool to the foosball table &mdash;
        there's something for everyone. Whether you're a seasoned athlete or a first-time participant,
        Spectrum welcomes you.
      </p>
    </div>

    <!-- Events Grid -->
    <div class="home-section">
      <h2>20 Events</h2>
      <div class="home-events-grid">
        <router-link
          v-for="evt in store.events"
          :key="evt.id"
          :to="`/events/${evt.id}`"
          class="home-event-chip"
        >
          <span class="home-event-icon">{{ evt.icon }}</span>
          <span>{{ evt.sport }}</span>
        </router-link>
      </div>
    </div>

    <!-- Quick Stats -->
    <div class="home-section">
      <div class="home-stats">
        <div class="home-stat">
          <div class="home-stat-number">20</div>
          <div class="home-stat-label">Sports Events</div>
        </div>
        <div class="home-stat">
          <div class="home-stat-number">20+</div>
          <div class="home-stat-label">Departments</div>
        </div>
        <div class="home-stat">
          <div class="home-stat-number">250+</div>
          <div class="home-stat-label">Athletes</div>
        </div>
        <div class="home-stat">
          <div class="home-stat-number">April '26</div>
          <div class="home-stat-label">Tournament</div>
        </div>
      </div>
    </div>

    <!-- CTA -->
    <div class="home-section home-cta">
      <h2>Ready to compete?</h2>
      <p>Browse events, check the rules, and register for your sport.</p>
      <div class="flex gap-12" style="justify-content:center;margin-top:16px">
        <router-link to="/events" class="btn btn-primary btn-lg">Browse Events</router-link>
        <router-link to="/schedule" class="btn btn-lg">View Schedule</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { store } from '../stores/tournament.js'
import posterFiles from '../data/posters.json'

const currentSlide = ref(0)
let autoplayTimer = null

// Fixed hero slides + auto-discovered poster images from public/posters/
const allSlides = computed(() => {
  const hero = [
    {
      title: 'SPECTRUM 2026',
      subtitle: 'The Annual Inter-Department Sports Tournament of IISc',
      bg: 'linear-gradient(135deg, #1a4a2e 0%, #0f1923 50%, #1a2733 100%)',
      img: null,
    },
    {
      title: 'Register Now',
      subtitle: '20 sports, one stage. Find your event and sign up.',
      bg: 'linear-gradient(135deg, #1a2733 0%, #2e1a33 100%)',
      img: null,
    },
    {
      title: 'Team Sports',
      subtitle: 'Football, Basketball, Volleyball, Kabaddi, and more',
      bg: 'linear-gradient(135deg, #0f2333 0%, #1a3322 100%)',
      img: null,
    },
    {
      title: 'Individual Events',
      subtitle: 'Athletics, Swimming, Chess, Powerlifting, Cycling',
      bg: 'linear-gradient(135deg, #2a1a0f 0%, #1a2733 100%)',
      img: null,
    },
  ]
  // Poster images as additional slides
  const posters = posterFiles.map(file => ({
    title: '',
    subtitle: '',
    bg: '#0f1923',
    img: `posters/${file}`,
  }))
  return [...posters, ...hero]
})

function nextSlide() {
  currentSlide.value = (currentSlide.value + 1) % allSlides.value.length
}

function prevSlide() {
  currentSlide.value = (currentSlide.value - 1 + allSlides.value.length) % allSlides.value.length
}

onMounted(() => {
  autoplayTimer = setInterval(nextSlide, 5000)
})

onUnmounted(() => {
  clearInterval(autoplayTimer)
})
</script>
