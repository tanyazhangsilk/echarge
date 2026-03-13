<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  CircleCheckFilled,
  CloseBold,
  Cpu,
  Lightning,
  Refresh,
  Search,
  SwitchButton,
  WarningFilled,
} from '@element-plus/icons-vue'

const filterForm = reactive({
  stationId: '',
  status: '',
})

const stationOptions = [
  { label: '南山科技园充电站', value: 'st-001' },
  { label: '福田市民中心充电站', value: 'st-002' },
  { label: '宝安国际机场充电站', value: 'st-003' },
  { label: '中心广场充电站', value: 'st-004' },
]

const pileData = ref([
  {
    id: 1,
    code: 'DC-120KW-001',
    stationId: 'st-004',
    stationName: '中心广场充电站',
    status: 'idle',
    ratedPowerKw: 120,
    realPowerKw: 0,
    progress: 0,
    durationMin: 0,
    temperatureC: 26,
    voltageV: 380,
    currentA: 0,
    lastSeen: '刚刚',
  },
  {
    id: 2,
    code: 'DC-120KW-002',
    stationId: 'st-004',
    stationName: '中心广场充电站',
    status: 'charging',
    ratedPowerKw: 120,
    realPowerKw: 95,
    progress: 68,
    durationMin: 42,
    temperatureC: 42,
    voltageV: 380,
    currentA: 250,
    lastSeen: '2 秒前',
  },
  {
    id: 3,
    code: 'AC-7KW-003',
    stationId: 'st-004',
    stationName: '中心广场充电站',
    status: 'offline',
    ratedPowerKw: 7,
    realPowerKw: 0,
    progress: 0,
    durationMin: 0,
    temperatureC: 0,
    voltageV: 0,
    currentA: 0,
    lastSeen: '8 分钟前',
  },
  {
    id: 4,
    code: 'DC-180KW-004',
    stationId: 'st-003',
    stationName: '宝安国际机场充电站',
    status: 'fault',
    ratedPowerKw: 180,
    realPowerKw: 0,
    progress: 0,
    durationMin: 0,
    temperatureC: 75,
    voltageV: 380,
    currentA: 0,
    lastSeen: '1 分钟前',
  },
  {
    id: 5,
    code: 'DC-160KW-005',
    stationId: 'st-001',
    stationName: '南山科技园充电站',
    status: 'charging',
    ratedPowerKw: 160,
    realPowerKw: 118,
    progress: 32,
    durationMin: 18,
    temperatureC: 39,
    voltageV: 750,
    currentA: 180,
    lastSeen: '1 秒前',
  },
  {
    id: 6,
    code: 'AC-7KW-006',
    stationId: 'st-001',
    stationName: '南山科技园充电站',
    status: 'idle',
    ratedPowerKw: 7,
    realPowerKw: 0,
    progress: 0,
    durationMin: 0,
    temperatureC: 28,
    voltageV: 220,
    currentA: 0,
    lastSeen: '刚刚',
  },
  {
    id: 7,
    code: 'DC-120KW-007',
    stationId: 'st-002',
    stationName: '福田市民中心充电站',
    status: 'idle',
    ratedPowerKw: 120,
    realPowerKw: 0,
    progress: 0,
    durationMin: 0,
    temperatureC: 25,
    voltageV: 380,
    currentA: 0,
    lastSeen: '5 秒前',
  },
  {
    id: 8,
    code: 'DC-120KW-008',
    stationId: 'st-002',
    stationName: '福田市民中心充电站',
    status: 'charging',
    ratedPowerKw: 120,
    realPowerKw: 72,
    progress: 81,
    durationMin: 67,
    temperatureC: 46,
    voltageV: 380,
    currentA: 210,
    lastSeen: '3 秒前',
  },
])

const filteredPiles = computed(() => {
  return pileData.value.filter((p) => {
    const stationOk = !filterForm.stationId || p.stationId === filterForm.stationId
    const statusOk = !filterForm.status || p.status === filterForm.status
    return stationOk && statusOk
  })
})

const stats = computed(() => {
  const total = filteredPiles.value.length
  const charging = filteredPiles.value.filter((p) => p.status === 'charging').length
  const idle = filteredPiles.value.filter((p) => p.status === 'idle').length
  const offlineFault = filteredPiles.value.filter((p) => p.status === 'offline' || p.status === 'fault').length
  const availability = total > 0 ? ((total - offlineFault) / total) * 100 : 0
  return {
    total,
    charging,
    idle,
    offlineFault,
    availability,
  }
})

const getStatusTagType = (status) => {
  const map = {
    charging: 'primary',
    idle: 'success',
    offline: 'info',
    fault: 'danger',
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    charging: '充电中',
    idle: '空闲',
    offline: '离线',
    fault: '故障',
  }
  return map[status] || '未知'
}

const formatDuration = (minutes) => {
  const min = Number(minutes || 0)
  const h = Math.floor(min / 60)
  const m = min % 60
  if (h <= 0) return `${m} 分钟`
  return `${h} 小时 ${m} 分钟`
}

const getProgressColor = (status) => {
  if (status === 'charging') return '#409eff'
  if (status === 'idle') return '#67c23a'
  return '#f56c6c'
}

const handleSearch = () => {
  ElMessage.info('功能开发中')
}

const handleReset = () => {
  filterForm.stationId = ''
  filterForm.status = ''
  ElMessage.info('功能开发中')
}

const handleToggle = () => {
  ElMessage.info('功能开发中')
}

const handleRestart = () => {
  ElMessage.info('功能开发中')
}
</script>

<template>
  <div class="pile-page">
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-bar stat-bar--neutral"></div>
          <div class="stat-main">
            <div class="stat-title">电桩总数</div>
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-sub">在线率 {{ stats.availability.toFixed(1) }}%</div>
          </div>
          <el-icon class="stat-icon"><Cpu /></el-icon>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-bar stat-bar--primary"></div>
          <div class="stat-main">
            <div class="stat-title">充电中</div>
            <div class="stat-value">{{ stats.charging }}</div>
            <div class="stat-sub">实时功率/状态刷新中</div>
          </div>
          <el-icon class="stat-icon"><Lightning /></el-icon>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-bar stat-bar--success"></div>
          <div class="stat-main">
            <div class="stat-title">空闲</div>
            <div class="stat-value">{{ stats.idle }}</div>
            <div class="stat-sub">可用资源充足</div>
          </div>
          <el-icon class="stat-icon"><CircleCheckFilled /></el-icon>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-bar stat-bar--danger"></div>
          <div class="stat-main">
            <div class="stat-title">离线 / 故障</div>
            <div class="stat-value">{{ stats.offlineFault }}</div>
            <div class="stat-sub">建议及时处理告警</div>
          </div>
          <el-icon class="stat-icon"><WarningFilled /></el-icon>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="filter-card">
      <el-row :gutter="12" align="middle">
        <el-col :xs="24" :sm="18" :md="20">
          <div class="filter-left">
            <el-select
              v-model="filterForm.stationId"
              clearable
              filterable
              placeholder="所属电站"
              style="width: 240px"
            >
              <el-option v-for="opt in stationOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
            </el-select>
            <el-select v-model="filterForm.status" clearable placeholder="设备状态" style="width: 180px">
              <el-option label="充电中" value="charging" />
              <el-option label="空闲" value="idle" />
              <el-option label="离线" value="offline" />
              <el-option label="故障" value="fault" />
            </el-select>
            <el-button type="primary" :icon="Search" @click="handleSearch">筛选</el-button>
            <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          </div>
        </el-col>
        <el-col :xs="24" :sm="6" :md="4">
          <div class="filter-right">
            <div class="pulse-dot"></div>
            <span class="realtime-text">实时监控</span>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-row :gutter="20" class="grid">
      <el-col v-for="pile in filteredPiles" :key="pile.id" :xs="24" :sm="12" :lg="8" :xl="6">
        <el-card shadow="hover" class="pile-card">
          <div class="pile-header">
            <div class="pile-title">
              <div class="pile-code">{{ pile.code }}</div>
              <div class="pile-station">{{ pile.stationName }}</div>
            </div>
            <el-tag :type="getStatusTagType(pile.status)" effect="dark" class="pile-tag">
              <span v-if="pile.status === 'charging'" class="tag-dot"></span>
              {{ getStatusText(pile.status) }}
            </el-tag>
          </div>

          <div class="pile-body">
            <div v-if="pile.status === 'charging'" class="charging-box">
              <el-progress
                :percentage="pile.progress"
                :stroke-width="10"
                :color="getProgressColor(pile.status)"
                :show-text="false"
              />
              <div class="charging-meta">
                <div class="meta-item">
                  <div class="meta-label">当前功率</div>
                  <div class="meta-value">{{ pile.realPowerKw }} kW</div>
                </div>
                <div class="meta-item">
                  <div class="meta-label">已充时长</div>
                  <div class="meta-value">{{ formatDuration(pile.durationMin) }}</div>
                </div>
                <div class="meta-item">
                  <div class="meta-label">进度</div>
                  <div class="meta-value">{{ pile.progress }}%</div>
                </div>
              </div>
            </div>
            <div v-else-if="pile.status === 'idle'" class="idle-box">
              <div class="idle-badge">
                <el-icon class="idle-icon"><CircleCheckFilled /></el-icon>
                <span>设备待机中</span>
              </div>
              <div class="idle-sub">可远程启停，随时可用</div>
            </div>
            <div v-else class="fault-box">
              <div class="fault-badge">
                <el-icon v-if="pile.status === 'offline'" class="fault-icon"><CloseBold /></el-icon>
                <el-icon v-else class="fault-icon"><WarningFilled /></el-icon>
                <span>{{ pile.status === 'offline' ? '设备离线' : '设备故障' }}</span>
              </div>
              <div class="fault-sub">最后心跳：{{ pile.lastSeen }}</div>
            </div>

            <div class="telemetry">
              <div class="telemetry-item">
                <span class="telemetry-k">额定</span>
                <span class="telemetry-v">{{ pile.ratedPowerKw }} kW</span>
              </div>
              <div class="telemetry-item">
                <span class="telemetry-k">电压</span>
                <span class="telemetry-v">{{ pile.voltageV > 0 ? pile.voltageV + 'V' : '--' }}</span>
              </div>
              <div class="telemetry-item">
                <span class="telemetry-k">电流</span>
                <span class="telemetry-v">{{ pile.currentA > 0 ? pile.currentA + 'A' : '--' }}</span>
              </div>
              <div class="telemetry-item">
                <span class="telemetry-k">温度</span>
                <span class="telemetry-v">{{ pile.temperatureC > 0 ? pile.temperatureC + '°C' : '--' }}</span>
              </div>
            </div>
          </div>

          <div class="pile-footer">
            <el-button size="small" type="primary" plain :icon="SwitchButton" @click="handleToggle(pile)">
              远程启停
            </el-button>
            <el-button size="small" type="danger" plain :icon="Refresh" @click="handleRestart(pile)">
              重启设备
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.pile-page {
  background: #0b1220;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: calc(100vh - 120px);
}

.stat-row :deep(.el-card) {
  border: none;
}

.stat-card {
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.02));
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #e5e7eb;
}

.stat-bar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

.stat-bar--neutral {
  background: #94a3b8;
}

.stat-bar--primary {
  background: #409eff;
}

.stat-bar--success {
  background: #67c23a;
}

.stat-bar--danger {
  background: #f56c6c;
}

.stat-main {
  padding: 8px 8px 8px 10px;
}

.stat-title {
  font-size: 13px;
  color: rgba(229, 231, 235, 0.75);
}

.stat-value {
  margin-top: 8px;
  font-size: 28px;
  font-weight: 800;
  letter-spacing: 0.5px;
}

.stat-sub {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(229, 231, 235, 0.6);
}

.stat-icon {
  position: absolute;
  right: 10px;
  top: 10px;
  font-size: 42px;
  opacity: 0.14;
}

.filter-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #e5e7eb;
}

.filter-left {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.filter-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.pulse-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #22c55e;
  box-shadow: 0 0 0 rgba(34, 197, 94, 0.4);
  animation: pulse 1.6s infinite;
}

.realtime-text {
  font-size: 12px;
  color: rgba(229, 231, 235, 0.75);
}

.grid {
  margin-top: 4px;
}

.pile-card {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.02));
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #e5e7eb;
}

.pile-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.pile-code {
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 0.3px;
}

.pile-station {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(229, 231, 235, 0.65);
}

.pile-tag {
  border: none;
}

.tag-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  margin-right: 6px;
  animation: blink 1.2s infinite;
}

.charging-box {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.charging-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.meta-item {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 10px;
}

.meta-label {
  font-size: 12px;
  color: rgba(229, 231, 235, 0.65);
}

.meta-value {
  margin-top: 6px;
  font-size: 14px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.idle-box,
.fault-box {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 12px;
}

.idle-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #86efac;
  font-weight: 700;
}

.idle-icon {
  font-size: 18px;
}

.idle-sub,
.fault-sub {
  margin-top: 8px;
  font-size: 12px;
  color: rgba(229, 231, 235, 0.65);
}

.fault-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #fca5a5;
  font-weight: 700;
}

.fault-icon {
  font-size: 18px;
}

.telemetry {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.telemetry-item {
  background: rgba(15, 23, 42, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.telemetry-k {
  font-size: 12px;
  color: rgba(229, 231, 235, 0.55);
}

.telemetry-v {
  font-size: 12px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.pile-footer {
  margin-top: 14px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

@keyframes blink {
  0%,
  100% {
    opacity: 0.2;
  }
  50% {
    opacity: 1;
  }
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(34, 197, 94, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(34, 197, 94, 0);
  }
}
</style>
