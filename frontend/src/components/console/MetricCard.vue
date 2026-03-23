<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: {
    type: String,
    required: true,
  },
  value: {
    type: [String, Number],
    required: true,
  },
  prefix: {
    type: String,
    default: '',
  },
  suffix: {
    type: String,
    default: '',
  },
  hint: {
    type: String,
    default: '',
  },
  trend: {
    type: String,
    default: '',
  },
  tone: {
    type: String,
    default: 'primary',
  },
})

const displayValue = computed(() => `${props.prefix}${props.value}${props.suffix}`)
</script>

<template>
  <article class="stat-surface surface-card" :class="`stat-surface--${tone}`">
    <p class="stat-surface__label">{{ label }}</p>
    <h3 class="stat-surface__value">{{ displayValue }}</h3>
    <p class="stat-surface__meta">{{ trend || hint }}</p>
  </article>
</template>

<style scoped>
.stat-surface {
  position: relative;
  overflow: hidden;
}

.stat-surface::after {
  content: '';
  position: absolute;
  inset: 0 auto auto 0;
  width: 100%;
  height: 3px;
  opacity: 0.9;
}

.stat-surface--primary::after {
  background: linear-gradient(90deg, #2f74ff, #62a2ff);
}

.stat-surface--success::after {
  background: linear-gradient(90deg, #22a06b, #62c98d);
}

.stat-surface--warning::after {
  background: linear-gradient(90deg, #d9911f, #f3bf57);
}

.stat-surface--danger::after {
  background: linear-gradient(90deg, #d84f57, #f78a8f);
}

.stat-surface--info::after {
  background: linear-gradient(90deg, #4b5f7a, #7d90ab);
}
</style>
