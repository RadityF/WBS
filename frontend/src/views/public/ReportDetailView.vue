<template>
  <section class="grid two">
    <div class="card">
      <div class="header-row">
        <h1 class="title">Status Laporan</h1>
        <StatusBadge :status="statusData?.status" />
      </div>

      <div v-if="store.statusLoading" class="alert info">Memuat status laporan...</div>
      <div v-else-if="store.statusError" class="alert error">{{ store.statusError }}</div>

      <template v-else-if="statusData">
        <div class="kv section-spacer">
          <div class="key">Ticket ID</div>
          <div class="mono">{{ statusData.ticket_id }}</div>
          <div class="key">Tahap laporan</div>
          <div>{{ scenarioLabel }}</div>
          <template v-if="!isScenarioThree">
            <div class="key">Kategori</div>
            <div>{{ statusData.category || "-" }}</div>
          </template>
          <div class="key">Urgensi</div>
          <div>{{ statusData.urgency || "-" }}</div>
          <div class="key">Terakhir diperbarui</div>
          <div>{{ formatDate(statusData.updated_at) }}</div>
          <template v-if="!isScenarioThree">
          <div class="key">Ringkasan</div>
            <div>{{ statusData.summary || "Belum tersedia" }}</div>
          </template>
          <div class="key">Respons</div>
          <div>{{ statusData.response_to_reporter || "-" }}</div>
          <div class="key">Jumlah klarifikasi</div>
          <div>{{ statusData.followup_round }}</div>
        </div>

        <div class="section-spacer" :class="showReply ? 'action-panel' : ''">
          <h3 style="margin:0 0 .5rem">{{ showReply ? "Tindakan diperlukan" : "Pertanyaan klarifikasi" }}</h3>
          <div v-if="!statusData.follow_up_questions?.length" class="empty">Tidak ada pertanyaan follow-up aktif.</div>
          <ol v-else class="file-list">
            <li v-for="question in statusData.follow_up_questions" :key="question">{{ question }}</li>
          </ol>
        </div>

        <form
          v-if="showReply"
          class="section-spacer"
          style="border-top:1px solid var(--border);padding-top:1rem;"
          @submit.prevent="onReply"
        >
          <label for="reply">Balasan klarifikasi</label>
          <textarea id="reply" v-model.trim="replyMessage" minlength="3" maxlength="3000" required placeholder="Jawab pertanyaan klarifikasi di atas dengan detail." />
          <div class="small muted">{{ replyMessage.length }}/3000 karakter</div>

          <div class="section-spacer">
            <label for="reply-attachments">Upload bukti tambahan (opsional)</label>
            <input id="reply-attachments" type="file" multiple @change="onPickReplyFiles" />
            <ul v-if="replyFiles.length" class="file-list small muted section-spacer">
              <li v-for="file in replyFiles" :key="file.name + file.size">{{ file.name }} ({{ Math.ceil(file.size / 1024) }} KB)</li>
            </ul>
          </div>

          <div v-if="store.replyError" class="alert error section-spacer">{{ store.replyError }}</div>
          <div v-if="store.replyMessage" class="alert success section-spacer">{{ store.replyMessage }}</div>

          <div class="actions section-spacer">
            <button class="btn primary" type="submit" :disabled="store.replyLoading || !activePin">
              {{ store.replyLoading ? "Mengirim..." : "Kirim balasan" }}
            </button>
          </div>
        </form>
      </template>
    </div>

    <aside class="card">
      <h2 class="title" style="font-size:1.25rem">Akses ticket</h2>
      <p class="muted small">Jika Anda membuka halaman ini dari bookmark, isi ulang PIN untuk verifikasi.</p>

      <form class="section-spacer" @submit.prevent="refreshWithPin">
        <label for="active-pin">PIN aktif</label>
        <input id="active-pin" v-model.trim="pinInput" placeholder="6 digit PIN" inputmode="numeric" minlength="6" maxlength="6" required />

        <div class="actions section-spacer">
          <button class="btn ghost" type="submit" :disabled="store.statusLoading">Refresh status</button>
        </div>
      </form>
    </aside>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import StatusBadge from "../../components/StatusBadge.vue";
import { usePublicReportStore } from "../../stores/publicReport";
import { formatDate } from "../../utils/format";

const route = useRoute();
const store = usePublicReportStore();

const replyMessage = ref("");
const replyFiles = ref([]);
const pinInput = ref("");

const ticketId = computed(() => route.params.ticketId?.toString() || "");
const activePin = computed(() => pinInput.value || store.sessionPin);
const statusData = computed(() => store.statusResult);
const isScenarioThree = computed(() => Number(statusData.value?.scenario) === 3);
const scenarioLabel = computed(() => {
  const scenario = Number(statusData.value?.scenario);
  if (scenario === 1) return "Terverifikasi awal";
  if (scenario === 2) return "Perlu konfirmasi tambahan";
  if (scenario === 3) return "Dialihkan / bukan kategori WBS";
  return "Menunggu analisis";
});
const showReply = computed(
  () => statusData.value?.status === "NEEDS_INFO" && (statusData.value?.follow_up_questions?.length || 0) > 0,
);

onMounted(async () => {
  pinInput.value = store.sessionPin || "";
  if (ticketId.value && activePin.value) {
    await store.fetchStatus(ticketId.value, activePin.value);
  } else {
    store.statusError = "PIN diperlukan untuk membuka detail status laporan.";
  }
});

async function refreshWithPin() {
  if (!ticketId.value || !activePin.value) {
    store.statusError = "Ticket ID atau PIN tidak valid.";
    return;
  }
  await store.fetchStatus(ticketId.value, activePin.value);
}

async function onReply() {
  if (!ticketId.value || !activePin.value) {
    store.replyError = "PIN diperlukan untuk mengirim balasan.";
    return;
  }

  const result = await store.sendReply(ticketId.value, activePin.value, replyMessage.value, replyFiles.value);
  if (!result) return;

  replyMessage.value = "";
  replyFiles.value = [];
  await store.fetchStatus(ticketId.value, activePin.value);
}

function onPickReplyFiles(event) {
  replyFiles.value = Array.from(event.target.files || []);
}
</script>
