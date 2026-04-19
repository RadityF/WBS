<template>
  <section class="card">
    <div class="header-row">
      <h1 class="title">Daftar Kasus</h1>
      <div class="actions">
        <input
          v-model.trim="search"
          type="search"
          placeholder="Cari ticket_id"
          style="min-width:220px;"
        />
        <select v-model="selected" @change="onFilterChange" style="min-width:220px;">
          <option value="">Semua status</option>
          <option v-for="status in ADMIN_STATUS_OPTIONS" :key="status" :value="status">{{ status }}</option>
        </select>
        <button class="btn ghost" type="button" @click="load">Refresh</button>
      </div>
    </div>

    <div v-if="store.listError" class="alert error">{{ store.listError }}</div>
    <div v-else-if="store.loadingList" class="alert info">Memuat daftar kasus...</div>

    <div v-else-if="!filteredCases.length" class="empty">Tidak ada kasus yang cocok dengan filter saat ini.</div>

    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Ticket ID</th>
            <th>Status</th>
            <th>Scenario</th>
            <th>Kategori</th>
            <th>Urgensi</th>
            <th>Updated</th>
            <th>Aksi</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filteredCases" :key="item.ticket_id">
            <td class="mono">{{ item.ticket_id }}</td>
            <td><StatusBadge :status="item.status" /></td>
            <td>{{ item.scenario ?? "-" }}</td>
            <td>{{ item.category || "-" }}</td>
            <td>{{ item.urgency || "-" }}</td>
            <td>{{ formatDate(item.updated_at) }}</td>
            <td>
              <RouterLink class="btn ghost small" :to="`/admin/cases/${encodeURIComponent(item.ticket_id)}`">
                Detail
              </RouterLink>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import StatusBadge from "../../components/StatusBadge.vue";
import { useAdminAuthStore } from "../../stores/adminAuth";
import { useAdminCasesStore } from "../../stores/adminCases";
import { ADMIN_STATUS_OPTIONS } from "../../utils/constants";
import { formatDate } from "../../utils/format";

const store = useAdminCasesStore();
const auth = useAdminAuthStore();
const router = useRouter();
const selected = ref("");
const search = ref("");

const filteredCases = computed(() => {
  const needle = search.value.toLowerCase();
  if (!needle) return store.cases;
  return store.cases.filter((item) => item.ticket_id?.toLowerCase().includes(needle));
});

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
  await store.fetchCases(selected.value);
}

async function onFilterChange() {
  await store.fetchCases(selected.value);
}
</script>
