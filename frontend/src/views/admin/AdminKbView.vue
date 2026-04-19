<template>
  <section class="grid two">
    <div class="card">
      <div class="header-row">
        <h1 class="title">Knowledge Base Reindex</h1>
        <span class="badge">Qdrant + Ollama</span>
      </div>

      <p class="muted">
        Endpoint ini menjalankan reindex data Knowledge Base ke Qdrant sesuai backend plan.
      </p>

      <div v-if="store.reindexError" class="alert error section-spacer">{{ store.reindexError }}</div>
      <div v-if="store.reindexResult" class="alert success section-spacer">
        Reindex selesai. Indexed: <strong>{{ store.reindexResult.indexed ?? 0 }}</strong>
        <span v-if="store.reindexResult.message"> - {{ store.reindexResult.message }}</span>
      </div>

      <div class="actions section-spacer">
        <button class="btn primary" type="button" :disabled="store.reindexLoading" @click="onReindex">
          {{ store.reindexLoading ? "Menjalankan reindex..." : "Trigger reindex KB" }}
        </button>
      </div>
    </div>

    <aside class="card">
      <h2 class="title" style="font-size:1.2rem">Checklist sebelum reindex</h2>
      <ul class="file-list section-spacer">
        <li>Service Qdrant running</li>
        <li>Service Ollama running + model sudah tersedia</li>
        <li>File <span class="mono">plan/Knowledge Base.xlsx</span> valid</li>
      </ul>
    </aside>
  </section>
</template>

<script setup>
import { watch } from "vue";
import { useRouter } from "vue-router";
import { useAdminAuthStore } from "../../stores/adminAuth";
import { useAdminCasesStore } from "../../stores/adminCases";

const store = useAdminCasesStore();
const auth = useAdminAuthStore();
const router = useRouter();

watch(
  () => auth.isAuthenticated,
  (value) => {
    if (!value) {
      router.push("/admin/login");
    }
  },
);

async function onReindex() {
  const result = await store.reindexKb();
  if (!result && !auth.isAuthenticated) {
    router.push("/admin/login");
  }
}
</script>
