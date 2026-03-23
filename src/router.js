import { createRouter, createWebHashHistory } from 'vue-router'
import DashboardView from './views/DashboardView.vue'
import EventsView from './views/EventsView.vue'
import EventDetailView from './views/EventDetailView.vue'
import ScheduleView from './views/ScheduleView.vue'
import BulletinView from './views/BulletinView.vue'
import SettingsView from './views/SettingsView.vue'

export default createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: DashboardView, name: 'dashboard' },
    { path: '/events', component: EventsView, name: 'events' },
    { path: '/events/:id', component: EventDetailView, name: 'event-detail', props: true },
    { path: '/schedule', component: ScheduleView, name: 'schedule' },
    { path: '/bulletin', component: BulletinView, name: 'bulletin' },
    { path: '/settings', component: SettingsView, name: 'settings' },
  ],
})
