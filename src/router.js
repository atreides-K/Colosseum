import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import DashboardView from './views/DashboardView.vue'
import EventsView from './views/EventsView.vue'
import EventDetailView from './views/EventDetailView.vue'
import ScheduleView from './views/ScheduleView.vue'

export default createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: HomeView, name: 'home' },
    { path: '/dashboard', component: DashboardView, name: 'dashboard' },
    { path: '/events', component: EventsView, name: 'events' },
    { path: '/events/:id', component: EventDetailView, name: 'event-detail', props: true },
    { path: '/schedule', component: ScheduleView, name: 'schedule' },
  ],
})
