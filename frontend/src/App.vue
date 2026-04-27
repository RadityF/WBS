<template>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="brand">Whistleblowing System</div>
      <nav class="nav">
        <template v-if="auth.isAuthenticated">
          <RouterLink class="nav-link" to="/admin/cases">Admin Case</RouterLink>
          <RouterLink class="nav-link" to="/admin/kb">Admin KB</RouterLink>
        </template>
        <template v-else-if="!isAdminRoute">
          <RouterLink class="nav-link" to="/report/new">Buat Laporan</RouterLink>
          <RouterLink class="nav-link" to="/report/status">Cek Status</RouterLink>
        </template>
        <button v-if="auth.isAuthenticated" class="btn ghost small" type="button" @click="logout">
          Logout
        </button>
      </nav>
    </div>
  </header>

  <main class="shell">
    <RouterView />
  </main>
</template>

<script setup>
import { useRouter } from "vue-router";
import { computed } from "vue";
import { useAdminAuthStore } from "./stores/adminAuth";

const auth = useAdminAuthStore();
const router = useRouter();
const isAdminRoute = computed(() => router.currentRoute.value.path.startsWith("/admin"));

function logout() {
  auth.logout();
  router.push("/admin/login");
}
</script>
