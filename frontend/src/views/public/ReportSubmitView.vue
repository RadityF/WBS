<template>
  <section class="grid two">
    <div class="card">
      <div class="header-row">
        <h1 class="title">Kirim Laporan Anonim</h1>
        <span class="badge">MVP</span>
      </div>

      <p class="muted">
        Ceritakan kronologi dengan detail. Backend akan memproses klasifikasi skenario 1/2/3 sesuai plan.
      </p>

      <form class="section-spacer" @submit.prevent="onSubmit">
        <div>
          <label for="narrative">Narasi laporan</label>
          <textarea
            id="narrative"
            v-model.trim="form.narrative"
            placeholder="Contoh: Pada tanggal..., di lokasi..., terlapor..., bukti..."
            required
            minlength="10"
            maxlength="6000"
          />
          <div class="small muted">{{ form.narrative.length }}/6000 karakter</div>
        </div>

        <div class="section-spacer">
          <label for="attachments">Bukti pendukung (opsional)</label>
          <input id="attachments" type="file" multiple @change="onPickFiles" />
          <ul v-if="files.length" class="file-list small muted section-spacer">
            <li v-for="file in files" :key="file.name + file.size">
              {{ file.name }} ({{ Math.ceil(file.size / 1024) }} KB)
            </li>
          </ul>
        </div>

        <div v-if="validationError" class="alert error section-spacer">{{ validationError }}</div>
        <div v-if="store.submitError" class="alert error section-spacer">{{ store.submitError }}</div>

        <div class="actions section-spacer">
          <button class="btn primary" type="submit" :disabled="store.submitLoading">
            {{ store.submitLoading ? "Mengirim..." : "Submit laporan" }}
          </button>
          <RouterLink class="btn ghost" to="/report/status">Saya sudah punya ticket</RouterLink>
        </div>
      </form>
    </div>

    <aside class="card">
      <h2 class="title" style="font-size: 1.3rem">Panduan singkat</h2>
      <div class="list section-spacer small">
        <div class="list-item">Sertakan siapa, kapan, di mana, dan bukti agar cepat tervalidasi.</div>
        <div class="list-item">Setelah submit, Anda akan menerima <span class="mono">ticket_id</span> + PIN.</div>
        <div class="list-item">PIN hanya ditampilkan sekali, simpan di tempat aman.</div>
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

const form = reactive({
  narrative: "",
});

const files = ref([]);
const validationError = ref("");

function onPickFiles(event) {
  const targetFiles = Array.from(event.target.files || []);
  files.value = targetFiles;
}

async function onSubmit() {
  validationError.value = "";
  if (form.narrative.length < 10) {
    validationError.value = "Narasi minimal 10 karakter.";
    return;
  }

  const totalSizeMb = files.value.reduce((sum, file) => sum + file.size, 0) / (1024 * 1024);
  if (totalSizeMb > 25) {
    validationError.value = "Total ukuran lampiran maksimal 25 MB.";
    return;
  }

  const result = await store.submit({ narrative: form.narrative, attachments: files.value });
  if (!result) return;

  router.push({
    name: "report-success",
    state: {
      ticket_id: result.ticket_id,
      pin: result.pin,
      message: result.message,
      status: result.status,
    },
  });
}
</script>
