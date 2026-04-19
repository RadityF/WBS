<template>
  <section class="grid two">
    <div class="card">
      <div class="header-row">
        <h1 class="title">Cek Status Laporan</h1>
        <span class="badge">Anonim</span>
      </div>

      <p class="muted">Masukkan ticket ID dan PIN untuk melihat status serta pertanyaan follow-up.</p>

      <form class="section-spacer" @submit.prevent="onCheck">
        <div>
          <label for="ticket">Ticket ID</label>
          <input id="ticket" v-model.trim="form.ticketId" placeholder="WBS-YYYYMMDD-1234" required />
        </div>

        <div class="section-spacer">
          <label for="pin">PIN</label>
          <input
            id="pin"
            v-model.trim="form.pin"
            placeholder="6 digit PIN"
            required
            minlength="6"
            maxlength="6"
          />
        </div>

        <div v-if="store.statusError" class="alert error section-spacer">{{ store.statusError }}</div>

        <div class="actions section-spacer">
          <button class="btn primary" type="submit" :disabled="store.statusLoading">
            {{ store.statusLoading ? "Memeriksa..." : "Cek status" }}
          </button>
          <RouterLink class="btn ghost" to="/report/new">Kirim laporan baru</RouterLink>
        </div>
      </form>
    </div>

    <aside class="card">
      <h2 class="title" style="font-size: 1.3rem">Catatan keamanan</h2>
      <div class="list section-spacer small">
        <div class="list-item">PIN tidak disimpan permanen di browser.</div>
        <div class="list-item">Jika PIN salah berulang, akses bisa dikunci sementara.</div>
        <div class="list-item">Gunakan format ticket: <span class="mono">WBS-YYYYMMDD-XXXX</span>.</div>
      </div>
    </aside>
  </section>
</template>

<script setup>
import { reactive } from "vue";
import { useRouter } from "vue-router";
import { usePublicReportStore } from "../../stores/publicReport";

const router = useRouter();
const store = usePublicReportStore();

const form = reactive({
  ticketId: store.sessionTicketId || "",
  pin: store.sessionPin || "",
});

async function onCheck() {
  const data = await store.fetchStatus(form.ticketId, form.pin);
  if (!data) return;

  router.push({
    name: "report-detail",
    params: { ticketId: form.ticketId },
    query: { pin: form.pin },
  });
}
</script>
