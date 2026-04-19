<template>
  <section class="card">
    <div class="header-row">
      <h1 class="title">Laporan Berhasil Dikirim</h1>
      <StatusBadge :status="result.status || 'SUBMITTED'" />
    </div>

    <p class="muted">Simpan data berikut. PIN tidak ditampilkan lagi setelah halaman ini ditutup.</p>

    <div class="kv section-spacer">
      <div class="key">Ticket ID</div>
      <div class="mono">{{ result.ticket_id }}</div>
      <div class="key">PIN</div>
      <div class="mono">{{ result.pin }}</div>
      <div class="key">Pesan sistem</div>
      <div>{{ result.message || "Laporan diterima" }}</div>
    </div>

    <div class="alert warn section-spacer" style="background:#fff4e9;border:1px solid #ffd8b5;color:#8a3a00;">
      Catat <span class="mono">ticket_id</span> dan PIN Anda sekarang. Keduanya dibutuhkan untuk cek status/follow-up.
    </div>

    <div class="actions section-spacer">
      <RouterLink class="btn primary" :to="`/report/${encodeURIComponent(result.ticket_id)}`">Lihat detail status</RouterLink>
      <RouterLink class="btn ghost" to="/report/status">Cek status manual</RouterLink>
      <button class="btn" type="button" @click="clearAndBack">Buat laporan baru</button>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import StatusBadge from "../../components/StatusBadge.vue";
import { usePublicReportStore } from "../../stores/publicReport";

const router = useRouter();
const store = usePublicReportStore();

const result = computed(() => {
  const state = history.state || {};
  return {
    ticket_id: state.ticket_id || store.submitResult?.ticket_id || store.sessionTicketId,
    pin: state.pin || store.submitResult?.pin || store.sessionPin,
    message: state.message || store.submitResult?.message,
    status: state.status || store.submitResult?.status,
  };
});

onMounted(() => {
  if (!result.value.ticket_id || !result.value.pin) {
    router.replace("/report/new");
  }
});

function clearAndBack() {
  store.clearSession();
  store.submitResult = null;
  router.push("/report/new");
}
</script>
