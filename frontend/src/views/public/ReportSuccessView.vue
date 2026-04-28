<template>
  <section class="card">
    <div class="header-row">
      <h1 class="title">Laporan Berhasil Dikirim</h1>
      <StatusBadge :status="result.status || 'SUBMITTED'" />
    </div>

    <p class="muted">Simpan kode akses berikut. Kode ini hanya ditampilkan sekali setelah laporan dibuat.</p>

    <div class="kv section-spacer">
      <div class="key">Kode akses</div>
      <div class="access-code-inline">
        <span class="access-code mono">{{ accessCode }}</span>
        <button class="btn ghost small" type="button" @click="copyAccessCode">Copy</button>
      </div>
      <div class="key">Pesan sistem</div>
      <div>{{ result.message || "Laporan diterima" }}</div>
    </div>

    <div class="alert warn section-spacer" style="background:#fff4e9;border:1px solid #ffd8b5;color:#8a3a00;">
      Catat atau salin kode akses sekarang. Formatnya <span class="mono">ticket_id;pin</span> dan dibutuhkan untuk cek status atau menjawab klarifikasi.
    </div>
    <div v-if="copyMessage" class="alert success section-spacer">{{ copyMessage }}</div>

    <div class="actions section-spacer">
      <RouterLink class="btn ghost" :to="`/report/${encodeURIComponent(result.ticket_id)}`">Lihat detail status</RouterLink>
      <RouterLink class="btn ghost" to="/report/status">Cek status manual</RouterLink>
      <button class="btn" type="button" @click="clearAndBack">Buat laporan baru</button>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import StatusBadge from "../../components/StatusBadge.vue";
import { usePublicReportStore } from "../../stores/publicReport";

const router = useRouter();
const store = usePublicReportStore();
const copyMessage = ref("");

const result = computed(() => {
  const state = history.state || {};
  return {
    ticket_id: state.ticket_id || store.submitResult?.ticket_id || store.sessionTicketId,
    pin: state.pin || store.submitResult?.pin || store.sessionPin,
    message: state.message || store.submitResult?.message,
    status: state.status || store.submitResult?.status,
  };
});

const accessCode = computed(() => `${result.value.ticket_id};${result.value.pin}`);

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

async function copyAccessCode() {
  await navigator.clipboard.writeText(accessCode.value);
  copyMessage.value = "Kode akses berhasil disalin.";
}
</script>

<style scoped>
.access-code-inline {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
</style>
