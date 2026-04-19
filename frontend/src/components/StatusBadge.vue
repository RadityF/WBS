<template>
  <span class="badge" :class="statusClass(status)">{{ statusLabel(status) }}</span>
</template>

<script setup>
import { statusClass, statusLabel } from "../utils/format";

defineProps({
  status: {
    type: String,
    default: "",
  },
});
</script>
