<template>
  <span class="status-badge" :class="`status-${status}`">{{ displayText }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true
  }
})

const statusLabels = {
  suggested: 'Suggested',
  researching: 'Researching',
  want_to_visit: 'Want to Visit',
  planned: 'Planned',
  visited: 'Visited',
  archived: 'Archived'
}

const displayText = computed(() => {
  return statusLabels[props.status] || props.status
})
</script>

<style scoped>
.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.status-suggested {
  background: rgba(147, 197, 253, 0.15);
  color: #93c5fd;
}

.status-researching {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.status-want_to_visit {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.status-planned {
  background: rgba(248, 113, 113, 0.15);
  color: #f87171;
}

.status-visited {
  background: rgba(192, 132, 252, 0.15);
  color: #c084fc;
}

.status-archived {
  background: rgba(156, 163, 175, 0.15);
  color: #9ca3af;
}
</style>
