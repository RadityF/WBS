<template>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="brand">Whistleblowing System</div>
      <nav class="nav">
        <RouterLink class="nav-link" to="/report/new">Buat Laporan</RouterLink>
        <RouterLink class="nav-link" to="/report/status">Cek Status</RouterLink>
        <RouterLink class="nav-link" to="/admin/cases">Admin Cases</RouterLink>
        <RouterLink class="nav-link" to="/admin/kb">Admin KB</RouterLink>
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
import { useAdminAuthStore } from "./stores/adminAuth";

const auth = useAdminAuthStore();
const router = useRouter();

function logout() {
  auth.logout();
  router.push("/admin/login");
}
</script>
