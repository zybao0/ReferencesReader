import { createRouter, createWebHistory } from 'vue-router'
import ReferencesListView from '../views/ReferencesListView.vue'
import UploadPaperView from '../views/UploadPaperView.vue'
import BibTexView from '../views/BibTexView.vue'

const routes = [
  {
    path: '/',
    name: 'UploadPaper',
    component: UploadPaperView
  },
  {
    path: '/Raw_References',
    name: 'RawReferences',
    component: ReferencesListView
  },
  {
    path: '/BibTex',
    name: 'BibTex',
    component: BibTexView
  },
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router

// import { createRouter, createWebHistory } from 'vue-router'
// import HomeView from '../views/HomeView.vue'

// const routes = [
//   {
//     path: '/',
//     name: 'home',
//     component: HomeView
//   },
//   {
//     path: '/about',
//     name: 'about',
//     // route level code-splitting
//     // this generates a separate chunk (about.[hash].js) for this route
//     // which is lazy-loaded when the route is visited.
//     component: function () {
//       return import(/* webpackChunkName: "about" */ '../views/AboutView.vue')
//     }
//   }
// ]

// const router = createRouter({
//   history: createWebHistory(process.env.BASE_URL),
//   routes
// })

// export default router
