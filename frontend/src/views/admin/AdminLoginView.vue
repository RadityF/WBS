<template>
  <section class="shell" style="max-width:560px;padding-top:1rem;">
    <div class="card">
      <div class="header-row">
        <h1 class="title">Admin Login</h1>
        <span class="badge">JWT</span>
      </div>

      <p class="muted">Gunakan akun admin seed backend (`ADMIN_DEFAULT_USERNAME`).</p>

      <form class="section-spacer" @submit.prevent="onSubmit">
        <div>
          <label for="username">Username</label>
          <input id="username" v-model.trim="form.username" required />
        </div>

        <div class="section-spacer">
          <label for="password">Password</label>
          <input id="password" v-model="form.password" type="password" required />
        </div>

        <div v-if="auth.error" class="alert error section-spacer">{{ auth.error }}</div>

        <div class="actions section-spacer">
          <button class="btn primary" type="submit" :disabled="auth.loading">
            {{ auth.loading ? "Memproses..." : "Masuk" }}
          </button>
          <RouterLink class="btn ghost" to="/report/new">Ke halaman pelapor</RouterLink>
        </div>
      </form>
    </div>
  </section>
</template>

<script setup>
import { reactive } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAdminAuthStore } from "../../stores/adminAuth";

const auth = useAdminAuthStore();
const route = useRoute();
const router = useRouter();

const form = reactive({
  username: "",
  password: "",
});

async function onSubmit() {
  const success = await auth.login({
    username: form.username,
    password: form.password,
  });
  if (!success) return;

  const redirect = route.query.redirect?.toString() || "/admin/cases";
  router.push(redirect);
}
</script>
