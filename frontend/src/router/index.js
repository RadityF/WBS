import { createRouter, createWebHistory } from "vue-router";
import { useAdminAuthStore } from "../stores/adminAuth";
import { pinia } from "../stores/pinia";

import ReportSubmitView from "../views/public/ReportSubmitView.vue";
import ReportSuccessView from "../views/public/ReportSuccessView.vue";
import ReportStatusLookupView from "../views/public/ReportStatusLookupView.vue";
import ReportDetailView from "../views/public/ReportDetailView.vue";
import AdminLoginView from "../views/admin/AdminLoginView.vue";
import AdminCasesView from "../views/admin/AdminCasesView.vue";
import AdminCaseDetailView from "../views/admin/AdminCaseDetailView.vue";
import AdminKbView from "../views/admin/AdminKbView.vue";
import NotFoundView from "../views/NotFoundView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/report/new" },
    { path: "/report", redirect: "/report/new" },
    { path: "/report/new", name: "report-new", component: ReportSubmitView },
    { path: "/report/success", name: "report-success", component: ReportSuccessView },
    { path: "/report/status", name: "report-status", component: ReportStatusLookupView },
    { path: "/report/:ticketId", name: "report-detail", component: ReportDetailView },
    {
      path: "/admin",
      redirect: "/admin/cases",
    },
    {
      path: "/admin/login",
      name: "admin-login",
      component: AdminLoginView,
      meta: { guestOnly: true },
    },
    {
      path: "/admin/cases",
      name: "admin-cases",
      component: AdminCasesView,
      meta: { requiresAdmin: true },
    },
    {
      path: "/admin/cases/:ticketId",
      name: "admin-case-detail",
      component: AdminCaseDetailView,
      meta: { requiresAdmin: true },
    },
    {
      path: "/admin/kb",
      name: "admin-kb",
      component: AdminKbView,
      meta: { requiresAdmin: true },
    },
    { path: "/:pathMatch(.*)*", name: "not-found", component: NotFoundView },
  ],
});

router.beforeEach((to) => {
  const auth = useAdminAuthStore(pinia);
  auth.initialize();

  if (to.meta.requiresAdmin && !auth.isAuthenticated) {
    return {
      name: "admin-login",
      query: { redirect: to.fullPath },
    };
  }

  if (to.meta.guestOnly && auth.isAuthenticated) {
    return { name: "admin-cases" };
  }

  return true;
});

export default router;
