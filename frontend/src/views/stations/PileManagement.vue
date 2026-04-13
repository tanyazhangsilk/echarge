<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { CircleCheck, Lightning, RefreshRight, WarningFilled } from '@element-plus/icons-vue'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import { fetchOperatorStations, fetchStationChargers } from '../../api/operator'

const route = useRoute()
const loading = ref(false)
const stationLoading = ref(false)
const stations = ref([])
const selectedStationId = ref(null)
const chargers = ref([])

const selectedStation = computed(() => stations.value.find((item) => item.id === selectedStationId.value) || null)

const chargerStats = computed(() => [
  {
    label: '充电桩总数',
    value: chargers.value.length,
    suffix: ' 台',
    trend: '当前电站设备规模',
    trendLabel: '适合设备管理截图',
    tone: 'primary',
    icon: Lightning,
  },
  {
    label: '充电中',
    value: chargers.value.filter((item) => item.status === 1).length,
    suffix: ' 台',
    trend: '实时占用数量',
    trendLabel: '用于展示设备状态',
    tone: 'warning',
    icon: RefreshRight,
  },
  {
    label: '空闲可用',
    value: chargers.value.filter((item) => item.status === 0).length,
    suffix: ' 台',
    trend: '可继续服务',
    trendLabel: '体现设备供给能力',
    tone: 'success',
    icon: CircleCheck,
  },
  {
    label: '故障告警',
    value: chargers.value.filter((item) => item.status === 2).length,
    suffix: ' 台',
    trend: '待维护设备',
    trendLabel: '适合运维管理展示',
    tone: 'danger',
    icon: WarningFilled,
  },
])

const statusTagType = (status) => {
  if (status === 1) return 'warning'
  if (status === 2) return 'danger'
  return 'success'
}

const loadStations = async () => {
  stationLoading.value = true
  try {
    const { data } = await fetchOperatorStations({ page: 1, page_size: 100 })
    stations.value = data.data?.items || []

    const queryId = Number(route.query.stationId || 0) || null
    if (queryId && stations.value.some((item) => item.id === queryId)) {
      selectedStationId.value = queryId
    } else if (!selectedStationId.value && stations.value.length) {
      selectedStationId.value = stations.value[0].id
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('电站列表加载失败')
  } finally {
    stationLoading.value = false
  }
}

const loadChargers = async () => {
  if (!selectedStationId.value) {
    chargers.value = []
    return
  }

  loading.value = true
  try {
    const { data } = await fetchStationChargers(selectedStationId.value)
    chargers.value = data.data || []
  } catch (error) {
    console.error(error)
    ElMessage.error('电桩数据加载失败')
  } finally {
    loading.value = false
  }
}

watch(selectedStationId, () => {
  loadChargers()
})

onMounted(async () => {
  await loadStations()
  await loadChargers()
})
</script>

<template>
  <div class="page-shell charger-page">
    <PageSectionHeader
      eyebrow="Chargers"
      title="电桩状态总览"
      description="按电站查看充电桩编号、类型、功率与状态，用于支撑毕业设计中的设备管理展示。"
      chip="运营商设备管理"
    >
      <template #actions>
        <el-select
          v-model="selectedStationId"
          placeholder="请选择电站"
          filterable
          :loading="stationLoading"
          style="width: 280px"
        >
          <el-option v-for="item in stations" :key="item.id" :label="item.station_name" :value="item.id" />
        </el-select>
        <el-button :icon="RefreshRight" :loading="loading" @click="loadChargers">刷新</el-button>
      </template>
    </PageSectionHeader>

    <div class="station-banner surface-card" v-if="selectedStation">
      <div>
        <strong>{{ selectedStation.station_name }}</strong>
        <p>{{ selectedStation.address }}</p>
      </div>
      <div class="station-banner__meta">
        <el-tag :type="selectedStation.status === 0 ? 'success' : selectedStation.status === 3 ? 'warning' : 'danger'">
          {{ selectedStation.status_text }}
        </el-tag>
        <el-tag :type="selectedStation.visibility === 'public' ? 'success' : 'info'">
          {{ selectedStation.visibility_text }}
        </el-tag>
      </div>
    </div>

    <section class="stats-grid stats-grid--chargers">
      <MetricCard
        v-for="item in chargerStats"
        :key="item.label"
        :label="item.label"
        :value="item.value"
        :suffix="item.suffix"
        :trend="item.trend"
        :trend-label="item.trendLabel"
        :tone="item.tone"
        :icon="item.icon"
      />
    </section>

    <section class="page-panel surface-card table-shell">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">电桩列表</h3>
          <p class="panel-heading__desc">统一展示电桩编号、名称、类型、功率、状态与所属电站。</p>
        </div>
      </div>

      <el-table v-if="chargers.length" :data="chargers" v-loading="loading" stripe>
        <el-table-column prop="sn_code" label="电桩编号" min-width="160" />
        <el-table-column prop="charger_name" label="电桩名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="type" label="类型" width="110" align="center" />
        <el-table-column prop="power_kw" label="功率" width="110" align="center">
          <template #default="{ row }">{{ row.power_kw }} kW</template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ row.status_text }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="station_name" label="所属电站" min-width="180" show-overflow-tooltip />
        <el-table-column prop="updated_at" label="更新时间" width="180" />
      </el-table>

      <EmptyStateBlock
        v-else-if="!loading"
        title="暂无电桩数据"
        description="请选择电站，或检查当前电站下是否已经有充电桩数据。"
      />
    </section>
  </div>
</template>

<style scoped>
.charger-page {
  padding-bottom: 8px;
}

.stats-grid--chargers {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.station-banner {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
  background: linear-gradient(135deg, rgba(47, 116, 255, 0.08), rgba(73, 187, 174, 0.1));
}

.station-banner strong {
  display: block;
  margin-bottom: 8px;
  font-size: 20px;
}

.station-banner p {
  margin: 0;
  color: var(--color-text-2);
}

.station-banner__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 1280px) {
  .stats-grid--chargers {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .stats-grid--chargers {
    grid-template-columns: 1fr;
  }

  .station-banner {
    flex-direction: column;
  }
}
</style>
