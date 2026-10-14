import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { useAuthStore } from '@/stores/auth.js'

import './css/main.css'

const pinia = createPinia()
const app = createApp(App)
app.use(pinia).use(router).mount('#app')

// Restore JWT header from localStorage on page load
useAuthStore(pinia).restoreAuth()

const defaultDocumentTitle = 'EFF Admin'

router.afterEach((to) => {
  document.title = to.meta?.title
    ? `${to.meta.title} — ${defaultDocumentTitle}`
    : defaultDocumentTitle
})
