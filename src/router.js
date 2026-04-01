import { createRouter, createWebHashHistory } from 'vue-router'
import DashboardView from './views/DashboardView.vue'
import EventDetailView from './views/EventDetailView.vue'
import ScheduleView from './views/ScheduleView.vue'

export default createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: DashboardView, name: 'events' },
    { path: '/events/:id', component: EventDetailView, name: 'event-detail', props: true },
    { path: '/schedule', component: ScheduleView, name: 'schedule' },
  ],
})
