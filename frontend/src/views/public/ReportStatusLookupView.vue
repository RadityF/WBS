<template>
  <section class="grid two">
    <div class="card">
      <div class="header-row">
        <h1 class="title">Cek Status Laporan</h1>
        <span class="badge">Anonim</span>
      </div>

      <p class="muted">Masukkan kode akses dengan format <span class="mono">ticket_id;pin</span> untuk melihat status serta pertanyaan follow-up.</p>

      <form class="section-spacer" @submit.prevent="onCheck">
        <div>
          <label for="access-code">Kode akses</label>
          <input id="access-code" v-model.trim="form.accessCode" placeholder="WBS-YYYYMMDD-1234;123456" required />
        </div>

        <div v-if="validationError" class="alert error section-spacer">{{ validationError }}</div>

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
        <div class="list-item">Gunakan format kode akses: <span class="mono">WBS-YYYYMMDD-XXXX;123456</span>.</div>
        <div class="list-item">Jangan bagikan kode akses kepada pihak lain.</div>
      </div>
    </aside>
  </section>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { usePublicReportStore } from "../../stores/publicReport";

const router = useRouter();
const store = usePublicReportStore();
const validationError = ref("");

const form = reactive({
  accessCode: store.sessionTicketId && store.sessionPin ? `${store.sessionTicketId};${store.sessionPin}` : "",
});

async function onCheck() {
  validationError.value = "";
  const [ticketId, pin] = form.accessCode.split(";").map((part) => part.trim());
  if (!ticketId || !pin) {
    validationError.value = "Kode akses harus berformat ticket_id;pin.";
    return;
  }

  const data = await store.fetchStatus(ticketId, pin);
  if (!data) return;

  router.push({
    name: "report-detail",
    params: { ticketId },
  });
}
</script>
