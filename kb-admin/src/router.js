import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import DocumentList from './views/DocumentList.vue'
import DocumentEdit from './views/DocumentEdit.vue'
import IndexManage from './views/IndexManage.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'Dashboard', component: Dashboard, meta: { title: '仪表盘' } },
  { path: '/documents', name: 'DocumentList', component: DocumentList, meta: { title: '文档管理' } },
  { path: '/documents/:docId/edit', name: 'DocumentEdit', component: DocumentEdit, meta: { title: '编辑文档' } },
  { path: '/index', name: 'IndexManage', component: IndexManage, meta: { title: '索引管理' } }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
