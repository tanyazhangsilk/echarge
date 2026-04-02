<script setup>
defineProps({
  eyebrow: {
    type: String,
    default: '',
  },
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    default: '',
  },
  chip: {
    type: String,
    default: '',
  },
})
</script>

<template>
  <section class="page-hero surface-card page-section-header">
    <div>
      <p v-if="eyebrow" class="page-hero__eyebrow">{{ eyebrow }}</p>
      <h1 class="page-hero__title">{{ title }}</h1>
      <p v-if="description" class="page-hero__desc">{{ description }}</p>
    </div>
    <div v-if="$slots.actions || chip" class="page-hero__actions">
      <slot name="actions" />
      <span v-if="chip" class="micro-chip">{{ chip }}</span>
    </div>
  </section>
</template>

<style scoped>
.page-section-header {
  animation: headerReveal 420ms ease both;
}

.page-hero__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

@keyframes headerReveal {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
