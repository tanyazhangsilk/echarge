<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Connection,
  Grid,
  OfficeBuilding,
  RefreshRight,
  View,
} from '@element-plus/icons-vue'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import {
  bindStationTemplate,
  fetchOperatorPricingTemplates,
  fetchOperatorStations,
  fetchStationChargers,
  updateStationVisibility,
} from '../../api/operator'

const loading = ref(false)
const stations = ref([])
const chargerLoading = ref(false)
const chargers = ref([])
const templateLoading = ref(false)
const templates = ref([])
const chargerDrawerVisible = ref(false)
const templateDialogVisible = ref(false)
const currentStation = ref(null)
const bindSubmitting = ref(false)

const filters = reactive({
  keyword: '',
  status: '',
  visibility: '',
})

const bindForm = reactive({
  templateId: null,
})

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '已上线', value: 0 },
  { label: '待审核', value: 3 },
  { label: '已驳回', value: 4 },
]

const visibilityOptions = [
  { label: '全部可见性', value: '' },
  { label: '公开站点', value: 'public' },
  { label: '私有站点', value: 'private' },
]

const filteredStations = computed(() => {
  const keyword = filters.keyword.trim().toLowerCase()
  return stations.value.filter((item) => {
    const matchKeyword =
      !keyword ||
      [item.station_name, item.operator_name, item.address, item.price_template_name]
        .filter(Boolean)
        .some((field) => String(field).toLowerCase().includes(keyword))
    const matchStatus = filters.status === '' || Number(filters.status) === item.status
    const matchVisibility = !filters.visibility || filters.visibility === item.visibility
    return matchKeyword && matchStatus && matchVisibility
  })
})

const stats = computed(() => {
  const total = stations.value.length
  const online = stations.value.filter((item) => item.status === 0).length
  const pending = stations.value.filter((item) => item.status === 3).length
  const privateCount = stations.value.filter((item) => item.visibility === 'private').length
  return [
    {
      label: '总电站',
      value: total,
      suffix: ' 座',
      trend: '运营商场站规模',
      trendLabel: '适合后台总览截图',
      tone: 'primary',
      icon: OfficeBuilding,
    },
    {
      label: '已上线',
      value: online,
      suffix: ' 座',
      trend: '可对外运营',
      trendLabel: '审核通过后可设为公开',
      tone: 'success',
      icon: Grid,
    },
    {
      label: '待审核',
      value: pending,
      suffix: ' 座',
      trend: '等待平台审核',
      trendLabel: '未通过前不能公开',
      tone: 'warning',
      icon: View,
    },
    {
      label: '私有站点',
      value: privateCount,
      suffix: ' 座',
      trend: '内部可见',
      trendLabel: '支持运营中切换回显',
      tone: 'info',
      icon: Connection,
    },
  ]
})

const selectedTemplate = computed(() =>
  templates.value.find((item) => item.id === bindForm.templateId) || null,
)

const chargerSummary = computed(() => ({
  total: chargers.value.length,
  charging: chargers.value.filter((item) => item.status === 1).length,
  idle: chargers.value.filter((item) => item.status === 0).length,
  fault: chargers.value.filter((item) => item.status === 2).length,
}))

const statusTagType = (status) => {
  if (status === 0) return 'success'
  if (status === 3) return 'warning'
  if (status === 4) return 'danger'
  return 'info'
}

const visibilityTagType = (visibility) => (visibility === 'public' ? 'success' : 'info')

const chargerStatusType = (status) => {
  if (status === 1) return 'warning'
  if (status === 2) return 'danger'
  return 'success'
}

const loadStations = async () => {
  loading.value = true
  try {
    const { data } = await fetchOperatorStations()
    stations.value = data.data || []
  } catch (error) {
    console.error(error)
    ElMessage.error('电站列表加载失败')
  } finally {
    loading.value = false
  }
}

const loadTemplates = async () => {
  templateLoading.value = true
  try {
    const { data } = await fetchOperatorPricingTemplates()
    templates.value = data.data || []
  } catch (error) {
    console.error(error)
    ElMessage.error('电价模板加载失败')
  } finally {
    templateLoading.value = false
  }
}

const openChargerDrawer = async (station) => {
  currentStation.value = station
  chargerDrawerVisible.value = true
  chargerLoading.value = true
  try {
    const { data } = await fetchStationChargers(station.id)
    chargers.value = data.data || []
  } catch (error) {
    console.error(error)
    ElMessage.error('电桩列表加载失败')
  } finally {
    chargerLoading.value = false
  }
}

const handleVisibilityChange = async (station, visibility) => {
  const actionText = visibility === 'public' ? '公开站点' : '私有站点'
  try {
    await ElMessageBox.confirm(`确认将“${station.station_name}”设置为${actionText}吗？`, '修改可见性', {
      type: 'warning',
      confirmButtonText: '确认修改',
      cancelButtonText: '取消',
    })
    const { data } = await updateStationVisibility(station.id, visibility)
    ElMessage.success(data.message || '可见性已更新')
    await loadStations()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error(error?.response?.data?.message || '修改失败')
    }
  }
}

const openBindDialog = async (station) => {
  currentStation.value = station
  bindForm.templateId = station.price_template_id || null
  templateDialogVisible.value = true
  if (!templates.value.length) {
    await loadTemplates()
  }
}

const submitBindTemplate = async () => {
  if (!currentStation.value || !bindForm.templateId) {
    ElMessage.warning('请先选择一个模板')
    return
  }
  bindSubmitting.value = true
  try {
    const { data } = await bindStationTemplate(currentStation.value.id, bindForm.templateId)
    ElMessage.success(data.message || '模板绑定成功')
    templateDialogVisible.value = false
    await loadStations()
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.message || '模板绑定失败')
  } finally {
    bindSubmitting.value = false
  }
}

const resetFilters = () => {
  filters.keyword = ''
  filters.status = ''
  filters.visibility = ''
}

onMounted(async () => {
  await Promise.all([loadStations(), loadTemplates()])
})
</script>

<template>
  <div class="page-shell station-page">
    <PageSectionHeader
      eyebrow="Operator Stations"
      title="电站管理"
      description="展示电站、充电桩与电价模板的绑定关系，适合作为毕业论文中的运营后台页面截图。"
      chip="运营商资产管理"
    >
      <template #actions>
        <el-button :icon="RefreshRight" :loading="loading" @click="loadStations">刷新列表</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid stats-grid--stations">
      <MetricCard
        v-for="item in stats"
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

    <section class="page-panel surface-card">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">筛选条件</h3>
          <p class="panel-heading__desc">支持按电站名称、状态和可见性快速筛选。</p>
        </div>
        <div class="toolbar-actions">
          <el-button @click="resetFilters">重置</el-button>
          <el-button type="primary" :loading="loading" @click="loadStations">重新加载</el-button>
        </div>
      </div>

      <div class="filter-row">
        <el-input v-model="filters.keyword" clearable placeholder="搜索电站名称 / 运营商 / 地址 / 模板" style="width: 340px" />
        <el-select v-model="filters.status" placeholder="选择状态" style="width: 160px">
          <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.visibility" placeholder="选择可见性" style="width: 160px">
          <el-option v-for="item in visibilityOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </div>
    </section>

    <section class="page-panel surface-card table-shell">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">电站列表</h3>
          <p class="panel-heading__desc">共 {{ filteredStations.length }} 座电站，支持查看电桩、切换可见性和绑定电价模板。</p>
        </div>
      </div>

      <el-table v-if="filteredStations.length" :data="filteredStations" v-loading="loading" stripe>
        <el-table-column prop="station_name" label="电站名称" min-width="220" show-overflow-tooltip />
        <el-table-column prop="operator_name" label="运营商" min-width="180" show-overflow-tooltip />
        <el-table-column prop="address" label="地址" min-width="280" show-overflow-tooltip />
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ row.status_text }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="可见性" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="visibilityTagType(row.visibility)">{{ row.visibility_text }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="price_template_name" label="绑定模板" min-width="180" show-overflow-tooltip />
        <el-table-column prop="charger_count" label="充电桩数量" width="110" align="center" />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openChargerDrawer(row)">查看电桩</el-button>
            <el-button
              link
              :type="row.visibility === 'public' ? 'warning' : 'success'"
              @click="handleVisibilityChange(row, row.visibility === 'public' ? 'private' : 'public')"
            >
              {{ row.visibility === 'public' ? '设为私有' : '设为公开' }}
            </el-button>
            <el-button link type="info" @click="openBindDialog(row)">绑定模板</el-button>
          </template>
        </el-table-column>
      </el-table>

      <EmptyStateBlock
        v-else-if="!loading"
        title="暂无电站数据"
        description="当前没有符合条件的电站记录。"
      />
    </section>

    <el-drawer v-model="chargerDrawerVisible" size="780px" :title="currentStation?.station_name || '电桩管理'">
      <template v-if="currentStation">
        <div class="drawer-header-card">
          <div>
            <strong>{{ currentStation.station_name }}</strong>
            <p>{{ currentStation.address }}</p>
          </div>
          <div class="drawer-tags">
            <el-tag :type="statusTagType(currentStation.status)">{{ currentStation.status_text }}</el-tag>
            <el-tag :type="visibilityTagType(currentStation.visibility)">{{ currentStation.visibility_text }}</el-tag>
          </div>
        </div>

        <el-descriptions :column="4" border class="drawer-descriptions">
          <el-descriptions-item label="充电桩总数">{{ chargerSummary.total }}</el-descriptions-item>
          <el-descriptions-item label="充电中">{{ chargerSummary.charging }}</el-descriptions-item>
          <el-descriptions-item label="空闲">{{ chargerSummary.idle }}</el-descriptions-item>
          <el-descriptions-item label="故障">{{ chargerSummary.fault }}</el-descriptions-item>
        </el-descriptions>
      </template>

      <el-table :data="chargers" v-loading="chargerLoading" stripe class="drawer-table">
        <el-table-column prop="sn_code" label="电桩编号" min-width="150" />
        <el-table-column prop="charger_name" label="电桩名称" min-width="170" show-overflow-tooltip />
        <el-table-column prop="type" label="类型" width="110" align="center" />
        <el-table-column prop="power_kw" label="功率" width="110" align="center">
          <template #default="{ row }">{{ row.power_kw }} kW</template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="chargerStatusType(row.status)">{{ row.status_text }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="station_name" label="所属电站" min-width="170" show-overflow-tooltip />
      </el-table>

      <EmptyStateBlock
        v-if="!chargerLoading && !chargers.length"
        title="暂无电桩数据"
        description="当前电站下还没有可展示的充电桩。"
      />
    </el-drawer>

    <el-dialog v-model="templateDialogVisible" width="760px" title="绑定电价模板">
      <template v-if="currentStation">
        <div class="dialog-station-card">
          <div>
            <strong>{{ currentStation.station_name }}</strong>
            <p>{{ currentStation.address }}</p>
          </div>
          <el-tag :type="statusTagType(currentStation.status)">{{ currentStation.status_text }}</el-tag>
        </div>

        <el-form label-width="96px" class="bind-form">
          <el-form-item label="选择模板">
            <el-select
              v-model="bindForm.templateId"
              placeholder="请选择电价模板"
              style="width: 100%"
              :loading="templateLoading"
            >
              <el-option v-for="item in templates" :key="item.id" :label="item.name" :value="item.id" />
            </el-select>
          </el-form-item>
        </el-form>
      </template>

      <div v-if="selectedTemplate" class="template-detail-card">
        <div class="template-detail-card__header">
          <div>
            <h4>{{ selectedTemplate.name }}</h4>
            <p>适用范围：{{ selectedTemplate.scope }}</p>
          </div>
          <el-tag :type="selectedTemplate.status === 'active' ? 'success' : 'info'">
            {{ selectedTemplate.status === 'active' ? '启用中' : '草稿' }}
          </el-tag>
        </div>

        <el-descriptions :column="2" border>
          <el-descriptions-item label="尖峰电价">¥{{ Number(selectedTemplate.peak_price).toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="平段电价">¥{{ Number(selectedTemplate.flat_price).toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="谷段电价">¥{{ Number(selectedTemplate.valley_price).toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="服务费">¥{{ Number(selectedTemplate.service_price).toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="模板状态">{{ selectedTemplate.status }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ selectedTemplate.updated_at }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <EmptyStateBlock
        v-else
        title="请选择一个模板"
        description="选择模板后会在这里展示模板价格详情。"
      />

      <template #footer>
        <el-button @click="templateDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="bindSubmitting" @click="submitBindTemplate">确认绑定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.station-page {
  padding-bottom: 8px;
}

.stats-grid--stations {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.toolbar-actions {
  display: flex;
  gap: 10px;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.drawer-header-card,
.dialog-station-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 18px;
  margin-bottom: 16px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(47, 116, 255, 0.08), rgba(73, 187, 174, 0.1));
}

.drawer-header-card strong,
.dialog-station-card strong {
  display: block;
  margin-bottom: 8px;
  font-size: 18px;
}

.drawer-header-card p,
.dialog-station-card p,
.template-detail-card__header p {
  margin: 0;
  color: var(--color-text-2);
}

.drawer-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.drawer-descriptions {
  margin-bottom: 16px;
}

.bind-form {
  margin-bottom: 12px;
}

.template-detail-card {
  padding: 18px;
  border-radius: 18px;
  background: #f8fbff;
  border: 1px solid rgba(47, 116, 255, 0.12);
}

.template-detail-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.template-detail-card__header h4 {
  margin: 0 0 8px;
}

@media (max-width: 1280px) {
  .stats-grid--stations {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .stats-grid--stations {
    grid-template-columns: 1fr;
  }

  .drawer-header-card,
  .dialog-station-card,
  .template-detail-card__header {
    flex-direction: column;
  }
}
</style>
