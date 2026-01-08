<template>
  <div class="stat-card" :class="[variant, { 'clickable': clickable }]" @click="handleClick">
    <div class="stat-icon-wrapper">
      <span class="stat-icon">{{ icon }}</span>
    </div>
    <div class="stat-content">
      <div class="stat-value">{{ formatValue(value) }}</div>
      <div class="stat-label">{{ label }}</div>
      <div v-if="trend !== undefined" class="stat-trend" :class="{ 'up': trend > 0, 'down': trend < 0 }">
        <span class="trend-arrow">{{ trend > 0 ? '↑' : trend < 0 ? '↓' : '→' }}</span>
        <span class="trend-value">{{ Math.abs(trend) }}%</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  icon: {
    type: String,
    default: '📊'
  },
  label: {
    type: String,
    required: true
  },
  value: {
    type: [Number, String],
    default: 0
  },
  trend: {
    type: Number,
    default: undefined
  },
  variant: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'primary', 'success', 'warning', 'info'].includes(v)
  },
  clickable: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click'])

const formatValue = (val) => {
  if (typeof val === 'number') {
    if (val >= 1000000) return (val / 1000000).toFixed(1) + 'M'
    if (val >= 1000) return (val / 1000).toFixed(1) + 'K'
    return val.toString()
  }
  return val
}

const handleClick = () => {
  if (props.clickable) {
    emit('click')
  }
}
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
  border: 1px solid var(--border-color);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, var(--accent-color), transparent);
  opacity: 0;
  transition: opacity 0.3s;
}

.stat-card:hover::before {
  opacity: 1;
}

.stat-card.clickable {
  cursor: pointer;
}

.stat-card.clickable:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--accent-color);
}

.stat-card.primary {
  background: linear-gradient(135deg, #4f46e520 0%, #7c3aed20 100%);
  border-color: #7c3aed40;
}

.stat-card.success {
  background: linear-gradient(135deg, #10b98120 0%, #059669 20 100%);
  border-color: #10b98140;
}

.stat-card.warning {
  background: linear-gradient(135deg, #f59e0b20 0%, #d97706 20 100%);
  border-color: #f59e0b40;
}

.stat-card.info {
  background: linear-gradient(135deg, #3b82f620 0%, #2563eb20 100%);
  border-color: #3b82f640;
}

.stat-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  box-shadow: var(--shadow-sm);
  flex-shrink: 0;
}

.stat-icon {
  font-size: 28px;
  line-height: 1;
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  font-family: var(--font-mono);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
  font-weight: 500;
  letter-spacing: 0.02em;
}

.stat-trend {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  background: var(--bg-primary);
}

.stat-trend.up {
  color: #10b981;
  background: #10b98115;
}

.stat-trend.down {
  color: #ef4444;
  background: #ef444415;
}

.trend-arrow {
  font-size: 14px;
}

/* 响应式 */
@media (max-width: 768px) {
  .stat-card {
    padding: 16px;
  }
  
  .stat-icon-wrapper {
    width: 48px;
    height: 48px;
  }
  
  .stat-icon {
    font-size: 24px;
  }
  
  .stat-value {
    font-size: 24px;
  }
}
</style>

