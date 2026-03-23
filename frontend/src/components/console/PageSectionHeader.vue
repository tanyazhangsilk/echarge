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
  <section class="page-hero surface-card">
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
.page-hero__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}
</style>
