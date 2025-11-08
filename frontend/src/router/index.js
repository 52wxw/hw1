import { createRouter, createWebHistory } from 'vue-router';
import DeviceManage from '../views/DeviceManage.vue';
import Inspection from '../views/Inspection.vue';
import Topology3D from '../views/Topology3D.vue';
import Report from '../views/Report.vue';
import MonitorPanel from '../views/MonitorPanel.vue';
import AlertConfig from '../views/AlertConfig.vue';
import ReportExport from '../views/ReportExport.vue';
import Login from '../views/Login.vue';

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { path: '/device', component: DeviceManage, meta: { requiresAuth: true } },
  { path: '/inspect', component: Inspection, meta: { requiresAuth: true } },
  { path: '/topology', component: Topology3D, meta: { requiresAuth: true } },
  { path: '/report', component: Report, meta: { requiresAuth: true } },
  { path: '/monitor', component: MonitorPanel, meta: { requiresAuth: true } },
  { path: '/alert', component: AlertConfig, meta: { requiresAuth: true } },
  { path: '/report-export', component: ReportExport, meta: { requiresAuth: true } },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

// 路由守卫（简单权限控制）
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth && !localStorage.getItem('token')) {
    next('/login');
  } else {
    next();
  }
});

export default router;
