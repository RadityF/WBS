<template>
  <section class="grid two">
    <div class="card">
      <div class="header-row">
        <h1 class="title">Detail Kasus</h1>
        <StatusBadge :status="detail?.status" />
      </div>

      <div class="actions" style="margin-bottom:.75rem;">
        <RouterLink class="btn ghost" to="/admin/cases">Kembali ke list</RouterLink>
        <button class="btn ghost" type="button" @click="load" :disabled="store.loadingDetail">Refresh detail</button>
      </div>

      <div v-if="store.detailError" class="alert error">{{ store.detailError }}</div>
      <div v-else-if="store.loadingDetail" class="alert info">Memuat detail kasus...</div>

      <template v-else-if="detail">
        <div class="kv section-spacer">
          <div class="key">Ticket ID</div>
          <div class="mono">{{ detail.ticket_id }}</div>
          <div class="key">Status</div>
          <div>{{ detail.status }}</div>
          <div class="key">Scenario</div>
          <div>{{ detail.scenario ?? "-" }}</div>
          <div class="key">Kategori</div>
          <div>{{ detail.category || "-" }}</div>
          <div class="key">Urgensi</div>
          <div>{{ detail.urgency || "-" }}</div>
          <div class="key">Summary</div>
          <div>{{ detail.summary || "-" }}</div>
          <div class="key">Reason</div>
          <div>{{ detail.reason || "-" }}</div>
          <div class="key">Respon terakhir</div>
          <div>{{ detail.latest_response_to_reporter || "-" }}</div>
          <div class="key">Follow-up round</div>
          <div>{{ detail.followup_round }}</div>
          <div class="key">Created</div>
          <div>{{ formatDate(detail.created_at) }}</div>
          <div class="key">Updated</div>
          <div>{{ formatDate(detail.updated_at) }}</div>
        </div>

        <div class="section-spacer">
          <h3 style="margin:.2rem 0 .55rem">Lampiran</h3>
          <div v-if="!detail.attachments?.length" class="empty">Tidak ada lampiran.</div>
          <div v-else class="list">
            <div v-for="item in detail.attachments" :key="`${item.saved_path}_${item.filename}`" class="list-item small">
              <div><strong>{{ item.filename }}</strong></div>
              <div class="muted">{{ item.content_type || "unknown" }}</div>
              <div class="mono">{{ item.saved_path }}</div>
              <div class="muted">{{ formatDate(item.created_at) }}</div>
            </div>
          </div>
        </div>

        <div class="section-spacer">
          <h3 style="margin:.2rem 0 .55rem">Riwayat Pesan</h3>
          <div v-if="!detail.messages?.length" class="empty">Belum ada pesan.</div>
          <div v-else class="list">
            <div v-for="(msg, index) in detail.messages" :key="`${msg.created_at}_${index}`" class="list-item">
              <div class="small muted">{{ msg.sender_type }} • {{ msg.message_type }} • {{ formatDate(msg.created_at) }}</div>
              <div style="margin-top:.4rem;white-space:pre-wrap;">{{ msg.content }}</div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <aside class="card">
      <h2 class="title" style="font-size:1.25rem">Update Status</h2>

      <form class="section-spacer" @submit.prevent="onUpdateStatus">
        <div>
          <label for="new-status">Status baru</label>
          <select id="new-status" v-model="statusPayload.new_status" required>
            <option disabled value="">Pilih status</option>
            <option v-for="status in ADMIN_STATUS_OPTIONS" :key="status" :value="status">
              {{ status }}
            </option>
          </select>
        </div>

        <div class="section-spacer">
          <label for="notes">Catatan (opsional)</label>
          <textarea id="notes" v-model.trim="statusPayload.notes" maxlength="1000" placeholder="Alasan perubahan status" />
        </div>

        <div v-if="store.updateError" class="alert error section-spacer">{{ store.updateError }}</div>
        <div v-if="store.updateMessage" class="alert success section-spacer">{{ store.updateMessage }}</div>

        <div class="actions section-spacer">
          <button class="btn primary" type="submit" :disabled="store.updateLoading || !detail">
            {{ store.updateLoading ? "Menyimpan..." : "Simpan status" }}
          </button>
        </div>
      </form>

      <div class="section-spacer" style="border-top:1px solid var(--border);padding-top:1rem;">
        <h2 class="title" style="font-size:1.15rem">Pesan ke Pelapor</h2>
        <p class="muted small">Gunakan untuk meminta klarifikasi atau membuka komunikasi lanjutan. Pesan ini terlihat oleh pelapor.</p>

        <form class="section-spacer" @submit.prevent="onSendMessage">
          <label for="admin-message">Isi pesan</label>
          <textarea id="admin-message" v-model.trim="adminMessagePayload.message" maxlength="3000" placeholder="Contoh: Mohon unggah bukti tambahan atau jelaskan kronologi..." required />
          <div class="small muted">{{ adminMessagePayload.message.length }}/3000 karakter</div>

          <label class="checkbox-row section-spacer">
            <input v-model="adminMessagePayload.mark_needs_info" type="checkbox" />
            <span>Ubah status menjadi perlu klarifikasi</span>
          </label>

          <div v-if="store.adminReplyError" class="alert error section-spacer">{{ store.adminReplyError }}</div>
          <div v-if="store.adminReplyMessage" class="alert success section-spacer">{{ store.adminReplyMessage }}</div>

          <div class="actions section-spacer">
            <button class="btn primary" type="submit" :disabled="store.adminReplyLoading || !detail">
              {{ store.adminReplyLoading ? "Mengirim..." : "Kirim pesan" }}
            </button>
          </div>
        </form>
      </div>
    </aside>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import StatusBadge from "../../components/StatusBadge.vue";
import { useAdminAuthStore } from "../../stores/adminAuth";
import { useAdminCasesStore } from "../../stores/adminCases";
import { ADMIN_STATUS_OPTIONS } from "../../utils/constants";
import { formatDate } from "../../utils/format";

const route = useRoute();
const router = useRouter();
const auth = useAdminAuthStore();
const store = useAdminCasesStore();

const statusPayload = reactive({
  new_status: "",
  notes: "",
});

const adminMessagePayload = reactive({
  message: "",
  mark_needs_info: true,
});

const ticketId = computed(() => route.params.ticketId?.toString() || "");
const detail = computed(() => store.detail);

watch(
  () => auth.isAuthenticated,
  (value) => {
    if (!value) {
      router.push("/admin/login");
    }
  },
);

onMounted(load);

async function load() {
  if (!ticketId.value) return;
  await store.fetchCaseDetail(ticketId.value);
  if (store.detail?.status) {
    statusPayload.new_status = store.detail.status;
  }
}

async function onUpdateStatus() {
  if (!ticketId.value || !statusPayload.new_status) return;
  const ok = await store.updateStatus(ticketId.value, {
    new_status: statusPayload.new_status,
    notes: statusPayload.notes || null,
  });
  if (!ok) return;
  await load();
}

async function onSendMessage() {
  if (!ticketId.value || !adminMessagePayload.message) return;
  const ok = await store.sendMessage(ticketId.value, {
    message: adminMessagePayload.message,
    mark_needs_info: adminMessagePayload.mark_needs_info,
  });
  if (!ok) return;
  adminMessagePayload.message = "";
  await load();
}
</script>
