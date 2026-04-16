<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  CircleCheck,
  Lightning,
  Plus,
  RefreshRight,
  Tickets,
  WarningFilled,
} from '@element-plus/icons-vue'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import {
  batchCreateStationChargers,
  createStationCharger,
  fetchOperatorStations,
  fetchStationChargers,
  updateStationCharger,
} from '../../api/operator'

const route = useRoute()
const loading = ref(false)
const stationLoading = ref(false)
const submitLoading = ref(false)
const batchSubmitting = ref(false)
const stations = ref([])
const selectedStationId = ref(null)
const chargers = ref([])
const addDialogVisible = ref(false)
const batchDialogVisible = ref(false)

const addForm = reactive({
  sn_code: '',
  charger_name: '',
  type: 'DC',
  power_kw: 120,
  status: 0,
})

const batchForm = reactive({
  count: 5,
  type: 'DC',
  power_kw: 120,
})

const selectedStation = computed(() => stations.value.find((item) => item.id === selectedStationId.value) || null)
const canManage = computed(() => selectedStation.value?.status === 0)

const chargerStats = computed(() => [
  {
    label: '电桩总数',
    value: chargers.value.length,
    suffix: ' 台',
    trend: '当前电站设备规模',
    trendLabel: '支持单个新增和批量生成',
    tone: 'primary',
    icon: Lightning,
  },
  {
    label: '空闲可用',
    value: chargers.value.filter((item) => item.status === 0).length,
    suffix: ' 台',
    trend: '可立即接单的电桩',
    trendLabel: '适合作为扫码和手动模拟入口',
    tone: 'success',
    icon: CircleCheck,
  },
  {
    label: '充电中',
    value: chargers.value.filter((item) => item.status === 1).length,
    suffix: ' 台',
    trend: '当前占用中的电桩',
    trendLabel: '与实时订单联动展示',
    tone: 'warning',
    icon: Tickets,
  },
  {
    label: '故障/停用',
    value: chargers.value.filter((item) => [2, 3].includes(item.status)).length,
    suffix: ' 台',
    trend: '需排查或暂停服务的设备',
    trendLabel: '支持直接调整设备状态',
    tone: 'danger',
    icon: WarningFilled,
  },
])

const statusOptions = [
  { label: '空闲', value: 0 },
  { label: '充电中', value: 1 },
  { label: '故障', value: 2 },
  { label: '停用', value: 3 },
]

const statusTagType = (status) => {
  if (status === 1) return 'warning'
  if (status === 2) return 'danger'
  if (status === 3) return 'info'
  return 'success'
}

const resetAddForm = () => {
  Object.assign(addForm, {
    sn_code: '',
    charger_name: '',
    type: 'DC',
    power_kw: 120,
    status: 0,
  })
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
    ElMessage.error(error?.response?.data?.message || '电站列表加载失败')
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
    chargers.value = []
    ElMessage.error(error?.response?.data?.message || '电桩数据加载失败')
  } finally {
    loading.value = false
  }
}

const openAddDialog = () => {
  if (!canManage.value) {
    ElMessage.warning('电站审核通过后才允许新增和配置电桩')
    return
  }
  resetAddForm()
  addDialogVisible.value = true
}

const submitAddCharger = async () => {
  if (!selectedStationId.value) {
    ElMessage.warning('请先选择电站')
    return
  }
  if (!addForm.sn_code.trim()) {
    ElMessage.warning('请输入电桩编号')
    return
  }
  if (!addForm.charger_name.trim()) {
    ElMessage.warning('请输入电桩名称')
    return
  }

  submitLoading.value = true
  try {
    const { data } = await createStationCharger(selectedStationId.value, {
      sn_code: addForm.sn_code.trim(),
      charger_name: addForm.charger_name.trim(),
      type: addForm.type,
      power_kw: Number(addForm.power_kw),
      status: Number(addForm.status),
    })
    ElMessage.success(data.message || '电桩新增成功')
    addDialogVisible.value = false
    await Promise.all([loadStations(), loadChargers()])
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.message || '电桩新增失败')
  } finally {
    submitLoading.value = false
  }
}

const openBatchDialog = () => {
  if (!canManage.value) {
    ElMessage.warning('电站审核通过后才允许批量生成电桩')
    return
  }
  Object.assign(batchForm, {
    count: 5,
    type: 'DC',
    power_kw: 120,
  })
  batchDialogVisible.value = true
}

const submitBatchCreate = async () => {
  if (!selectedStationId.value) {
    ElMessage.warning('请先选择电站')
    return
  }
  batchSubmitting.value = true
  try {
    const { data } = await batchCreateStationChargers(selectedStationId.value, {
      count: Number(batchForm.count),
      type: batchForm.type,
      power_kw: Number(batchForm.power_kw),
    })
    ElMessage.success(data.message || '批量生成成功')
    batchDialogVisible.value = false
    await Promise.all([loadStations(), loadChargers()])
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.message || '批量生成失败')
  } finally {
    batchSubmitting.value = false
  }
}

const updateChargerStatus = async (row, status) => {
  try {
    const { data } = await updateStationCharger(selectedStationId.value, row.id, { status })
    ElMessage.success(data.message || '电桩状态已更新')
    await loadChargers()
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.message || '电桩状态更新失败')
    await loadChargers()
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
      eyebrow="资产管理"
      title="电桩管理"
      description="为已审核通过的电站新增电桩、批量生成演示设备并维护设备状态。"
      chip="设备配置"
    >
      <template #actions>
        <el-select
          v-model="selectedStationId"
          placeholder="请选择电站"
          filterable
          :loading="stationLoading"
          style="width: 300px"
        >
          <el-option
            v-for="item in stations"
            :key="item.id"
            :label="`${item.station_name} · ${item.status_text}`"
            :value="item.id"
          />
        </el-select>
        <el-button type="primary" :icon="Plus" @click="openAddDialog">新增电桩</el-button>
        <el-button type="primary" plain :icon="Tickets" @click="openBatchDialog">批量生成演示电桩</el-button>
        <el-button :icon="RefreshRight" :loading="loading" @click="loadChargers">刷新</el-button>
      </template>
    </PageSectionHeader>

    <div class="station-banner surface-card" v-if="selectedStation">
      <div>
        <strong>{{ selectedStation.station_name }}</strong>
        <p>{{ selectedStation.full_address }}</p>
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

    <el-alert
      v-if="selectedStation && !canManage"
      title="当前电站尚未审核通过，暂不支持新增电桩、批量生成或绑定模板后的运营动作。"
      type="warning"
      :closable="false"
      show-icon
      class="station-alert"
    />

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
          <p class="panel-heading__desc">按电站查看电桩编号、类型、功率和当前运行状态。</p>
        </div>
      </div>

      <el-table v-if="chargers.length" :data="chargers" v-loading="loading" stripe>
        <el-table-column prop="sn_code" label="电桩编号" min-width="160" />
        <el-table-column prop="charger_name" label="电桩名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="type" label="类型" width="110" align="center" />
        <el-table-column prop="power_kw" label="功率" width="110" align="center">
          <template #default="{ row }">{{ row.power_kw }} kW</template>
        </el-table-column>
        <el-table-column label="状态" width="180" align="center">
          <template #default="{ row }">
            <div class="status-editor">
              <el-tag :type="statusTagType(row.status)">{{ row.status_text }}</el-tag>
              <el-select
                v-if="canManage"
                :model-value="row.status"
                size="small"
                style="width: 110px"
                @change="(value) => updateChargerStatus(row, value)"
              >
                <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180" />
      </el-table>

      <EmptyStateBlock
        v-else-if="!loading"
        title="暂无电桩数据"
        description="当前电站下还没有设备，请新增或批量生成演示电桩。"
      />
    </section>

    <el-dialog v-model="addDialogVisible" width="560px" title="新增电桩">
      <el-form label-width="96px">
        <el-form-item label="电桩编号">
          <el-input v-model="addForm.sn_code" placeholder="例如 ST001DC001" />
        </el-form-item>
        <el-form-item label="电桩名称">
          <el-input v-model="addForm.charger_name" placeholder="例如 A 区快充 01 号桩" />
        </el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="addForm.type">
            <el-radio-button label="AC">AC</el-radio-button>
            <el-radio-button label="DC">DC</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="功率">
          <el-input-number v-model="addForm.power_kw" :min="1" :max="999" style="width: 100%" />
        </el-form-item>
        <el-form-item label="初始状态">
          <el-select v-model="addForm.status" style="width: 100%">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitAddCharger">确认新增</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="batchDialogVisible" width="520px" title="批量生成演示电桩">
      <el-form label-width="96px">
        <el-form-item label="生成数量">
          <el-input-number v-model="batchForm.count" :min="1" :max="50" style="width: 100%" />
        </el-form-item>
        <el-form-item label="电桩类型">
          <el-radio-group v-model="batchForm.type">
            <el-radio-button label="AC">AC</el-radio-button>
            <el-radio-button label="DC">DC</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="默认功率">
          <el-input-number v-model="batchForm.power_kw" :min="1" :max="999" style="width: 100%" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="batchSubmitting" @click="submitBatchCreate">确认生成</el-button>
      </template>
    </el-dialog>
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

.station-alert {
  margin-bottom: 16px;
}

.status-editor {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
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
