<template>
  <section class="grid two">
    <div class="card">
      <div class="header-row">
        <h1 class="title">Kirim Laporan Anonim</h1>
        <span class="badge">Rahasia</span>
      </div>

      <p class="muted">
        Ceritakan kronologi dengan detail. Anda tidak perlu mencantumkan identitas pribadi jika ingin tetap anonim.
      </p>

      <div class="process-flow section-spacer" aria-label="Alur pelaporan">
        <div class="flow-step active"><strong>1</strong><span>Tulis laporan</span></div>
        <div class="flow-line"></div>
        <div class="flow-step"><strong>2</strong><span>Validasi awal AI</span></div>
        <div class="flow-line"></div>
        <div class="flow-step"><strong>3</strong><span>Klarifikasi bila perlu</span></div>
        <div class="flow-line"></div>
        <div class="flow-step"><strong>4</strong><span>Review admin</span></div>
      </div>

      <form class="section-spacer" @submit.prevent="onSubmit">
        <div class="hint-panel">
          <strong>Isi laporan sebaiknya mencakup:</strong>
          <div class="hint-grid section-spacer small">
            <span>Siapa pihak terlibat</span>
            <span>Apa dugaan pelanggaran</span>
            <span>Kapan kejadian terjadi</span>
            <span>Di mana lokasinya</span>
            <span>Bukti atau saksi</span>
            <span>Dampak yang diketahui</span>
          </div>
        </div>

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
          <div class="small muted section-spacer">
            Lampirkan screenshot, foto, PDF, atau dokumen yang relevan. Hindari data pribadi yang tidak berkaitan dengan laporan.
          </div>
          <ul v-if="files.length" class="file-list small muted section-spacer">
            <li v-for="file in files" :key="file.name + file.size">
              {{ file.name }} ({{ Math.ceil(file.size / 1024) }} KB)
            </li>
          </ul>
        </div>

        <div v-if="validationError" class="alert error section-spacer">{{ validationError }}</div>
        <div v-if="store.submitError" class="alert error section-spacer">{{ store.submitError }}</div>
        <div v-if="store.submitLoading" class="loading-panel section-spacer" role="status" aria-live="polite">
          <div class="spinner"></div>
          <div>
            <strong>Sedang mengirim dan menganalisis laporan...</strong>
            <p class="muted small">Mohon tunggu. Jangan refresh, menutup halaman, atau menekan tombol kembali sampai proses selesai.</p>
          </div>
        </div>

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
        <div class="list-item"><strong>Privasi:</strong> laporan diproses menggunakan Ticket ID dan PIN, bukan akun pribadi.</div>
        <div class="list-item">Sertakan siapa, kapan, di mana, bukti, dan kategori agar cepat tervalidasi.</div>
        <div class="list-item">
          <strong>Kategori pelanggaran:</strong>
          <ul class="dot-list">
            <li><strong>Gratifikasi</strong>: Pemberian hadiah/fasilitas yang berpotensi memengaruhi objektivitas kerja.</li>
            <li><strong>Suap (Bribery)</strong>: Pemberian atau penerimaan imbalan untuk memengaruhi keputusan secara tidak sah.</li>
            <li><strong>Korupsi / Fraud</strong>: Penyalahgunaan jabatan, manipulasi, atau kecurangan untuk keuntungan pribadi/kelompok.</li>
            <li><strong>Konflik Kepentingan</strong>: Situasi saat kepentingan pribadi memengaruhi keputusan profesional.</li>
            <li><strong>Pelecehan (Harassment)</strong>: Tindakan verbal, non-verbal, atau fisik yang merendahkan/menyakiti pihak lain.</li>
            <li><strong>Pencurian Data (Data Breach)</strong>: Akses, pengambilan, atau penyebaran data tanpa wewenang.</li>
            <li><strong>Penyalahgunaan Aset</strong>: Penggunaan aset perusahaan untuk kepentingan pribadi atau di luar aturan.</li>
          </ul>
        </div>
        <div class="list-item">Setelah submit, Anda akan menerima kode akses gabungan <span class="mono">ticket_id;pin</span>.</div>
        <div class="list-item">Kode akses hanya ditampilkan sekali. Jika hilang, akses tidak dapat dipulihkan demi menjaga anonimitas.</div>
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
