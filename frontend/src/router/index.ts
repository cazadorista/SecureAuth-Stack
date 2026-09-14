import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const hostname = window.location.hostname

function getRoutes(): RouteRecordRaw[] {
  if (hostname.startsWith('cook')) {
    return [{ path: '/', name: 'cookbook-home', component: () => import('../modules/cookbook/views/RecipeListView.vue') }]
  }
  if (hostname.startsWith('forms')) {
    return [{ path: '/', name: 'forms-home', component: () => import('../modules/forms/views/FormsView.vue') }]
  }
  if (hostname.startsWith('blog')) {
    return [{ path: '/', name: 'blog-home', component: () => import('../modules/blog/views/BlogView.vue') }]
  }
  return [{ path: '/', name: 'portal-home', component: () => import('../modules/portal/views/DashboardView.vue') }]
}

const router = createRouter({
  history: createWebHistory(),
  routes: getRoutes()
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  if (!authStore.isInitialized) {
    await authStore.checkAuth()
  }
  next()
})

export default router