<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Connection,
  Grid,
  OfficeBuilding,
  Plus,
  RefreshRight,
  SetUp,
  Tickets,
  View,
} from '@element-plus/icons-vue'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import {
  applyOperatorStation,
  bindStationTemplate,
  fetchOperatorPricingTemplates,
  fetchOperatorStations,
  fetchStationChargers,
  updateStationVisibility,
} from '../../api/operator'

const router = useRouter()
const loading = ref(false)
const errorMessage = ref('')
const stations = ref([])
const total = ref(0)
const chargerLoading = ref(false)
const chargers = ref([])
const templateLoading = ref(false)
const templates = ref([])
const chargerDrawerVisible = ref(false)
const templateDialogVisible = ref(false)
const applyDialogVisible = ref(false)
const currentStation = ref(null)
const bindSubmitting = ref(false)
const applySubmitting = ref(false)

const pagination = reactive({
  page: 1,
  pageSize: 10,
})

const filters = reactive({
  keyword: '',
  status: '',
  visibility: '',
})

const summary = reactive({
  total_count: 0,
  online_count: 0,
  pending_count: 0,
  private_count: 0,
})

const bindForm = reactive({
  templateId: null,
})

const applyForm = reactive({
  station_name: '',
  province: '',
  city: '',
  district: '',
  address: '',
  longitude: 114.0579,
  latitude: 22.5431,
  contact_name: '',
  contact_phone: '',
  operation_hours: '00:00-24:00',
  parking_fee_desc: '',
  station_remark: '',
  planned_charger_count: 4,
  total_power_kw: 240,
  cover_image: '',
  site_photos_text: '',
  qualification_remark: '',
})

let searchTimer = null

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '已审核通过', value: 0 },
  { label: '待审核', value: 3 },
  { label: '已驳回', value: 4 },
]

const visibilityOptions = [
  { label: '全部可见性', value: '' },
  { label: '公开站点', value: 'public' },
  { label: '私有站点', value: 'private' },
]

const stats = computed(() => [
  {
    label: '电站总数',
    value: summary.total_count,
    suffix: ' 座',
    trend: '当前运营商名下全部电站',
    trendLabel: '含待审核与已驳回站点',
    tone: 'primary',
    icon: OfficeBuilding,
  },
  {
    label: '已审核通过',
    value: summary.online_count,
    suffix: ' 座',
    trend: '可继续配桩和绑定模板',
    trendLabel: '审核通过后才能公开运营',
    tone: 'success',
    icon: Grid,
  },
  {
    label: '待审核',
    value: summary.pending_count,
    suffix: ' 座',
    trend: '等待管理员处理申请',
    trendLabel: '审核结果会同步到站点资料',
    tone: 'warning',
    icon: View,
  },
  {
    label: '私有站点',
    value: summary.private_count,
    suffix: ' 座',
    trend: '未对外公开展示',
    trendLabel: '可按审核结果控制可见性',
    tone: 'info',
    icon: Connection,
  },
])

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
  if (status === 3) return 'info'
  return 'success'
}

const resetApplyForm = () => {
  Object.assign(applyForm, {
    station_name: '',
    province: '',
    city: '',
    district: '',
    address: '',
    longitude: 114.0579,
    latitude: 22.5431,
    contact_name: '',
    contact_phone: '',
    operation_hours: '00:00-24:00',
    parking_fee_desc: '',
    station_remark: '',
    planned_charger_count: 4,
    total_power_kw: 240,
    cover_image: '',
    site_photos_text: '',
    qualification_remark: '',
  })
}

const loadStations = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const { data } = await fetchOperatorStations({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword.trim() || undefined,
      status: filters.status === '' ? undefined : Number(filters.status),
      visibility: filters.visibility || undefined,
    })

    const payload = data.data || {}
    stations.value = payload.items || []
    total.value = Number(payload.total || 0)
    pagination.page = Number(payload.page || pagination.page)
    pagination.pageSize = Number(payload.page_size || pagination.pageSize)
    Object.assign(summary, payload.summary || {})
  } catch (error) {
    console.error(error)
    stations.value = []
    total.value = 0
    Object.assign(summary, {
      total_count: 0,
      online_count: 0,
      pending_count: 0,
      private_count: 0,
    })
    errorMessage.value = error?.response?.data?.message || error?.response?.data?.detail || '电站列表加载失败'
    ElMessage.error(errorMessage.value)
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
    ElMessage.error(error?.response?.data?.message || error?.response?.data?.detail || '电价模板加载失败')
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
    chargers.value = []
    ElMessage.error(error?.response?.data?.message || error?.response?.data?.detail || '电桩列表加载失败')
  } finally {
    chargerLoading.value = false
  }
}

const handleVisibilityChange = async (station, visibility) => {
  const actionText = visibility === 'public' ? '公开站点' : '设为私有'
  try {
    await ElMessageBox.confirm(`确认将“${station.station_name}”设置为${actionText}吗？`, '修改可见性', {
      type: 'warning',
      confirmButtonText: '确认',
      cancelButtonText: '取消',
    })
    const { data } = await updateStationVisibility(station.id, visibility)
    ElMessage.success(data.message || '可见性已更新')
    await loadStations()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error(error?.response?.data?.message || error?.response?.data?.detail || '可见性更新失败')
    }
  }
}

const openBindDialog = async (station) => {
  if (station.status !== 0) {
    ElMessage.warning('电站审核通过后才允许绑定电价模板')
    return
  }
  currentStation.value = station
  bindForm.templateId = station.price_template_id || null
  templateDialogVisible.value = true
  if (!templates.value.length) {
    await loadTemplates()
  }
}

const submitBindTemplate = async () => {
  if (!currentStation.value || !bindForm.templateId) {
    ElMessage.warning('请选择电价模板')
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
    ElMessage.error(error?.response?.data?.message || error?.response?.data?.detail || '模板绑定失败')
  } finally {
    bindSubmitting.value = false
  }
}

const openApplyDialog = () => {
  resetApplyForm()
  applyDialogVisible.value = true
}

const submitApplyStation = async () => {
  const requiredFields = [
    ['station_name', '请输入电站名称'],
    ['province', '请输入省份'],
    ['city', '请输入城市'],
    ['district', '请输入区县'],
    ['address', '请输入详细地址'],
    ['contact_name', '请输入联系人'],
    ['contact_phone', '请输入联系电话'],
  ]

  for (const [field, message] of requiredFields) {
    if (!String(applyForm[field] || '').trim()) {
      ElMessage.warning(message)
      return
    }
  }
  if (!Number(applyForm.planned_charger_count) || Number(applyForm.planned_charger_count) < 1) {
    ElMessage.warning('规划电桩数需大于 0')
    return
  }
  if (!Number(applyForm.total_power_kw) || Number(applyForm.total_power_kw) <= 0) {
    ElMessage.warning('规划总功率需大于 0')
    return
  }

  applySubmitting.value = true
  try {
    const { data } = await applyOperatorStation({
      station_name: applyForm.station_name.trim(),
      province: applyForm.province.trim(),
      city: applyForm.city.trim(),
      district: applyForm.district.trim(),
      address: applyForm.address.trim(),
      longitude: Number(applyForm.longitude),
      latitude: Number(applyForm.latitude),
      contact_name: applyForm.contact_name.trim(),
      contact_phone: applyForm.contact_phone.trim(),
      operation_hours: applyForm.operation_hours.trim(),
      parking_fee_desc: applyForm.parking_fee_desc.trim(),
      station_remark: applyForm.station_remark.trim(),
      planned_charger_count: Number(applyForm.planned_charger_count),
      total_power_kw: Number(applyForm.total_power_kw),
      cover_image: applyForm.cover_image.trim(),
      site_photos: applyForm.site_photos_text
        .split('\n')
        .map((item) => item.trim())
        .filter(Boolean),
      qualification_remark: applyForm.qualification_remark.trim(),
    })
    ElMessage.success(data.message || '电站申请已提交')
    applyDialogVisible.value = false
    pagination.page = 1
    await loadStations()
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.message || error?.response?.data?.detail || '电站申请提交失败')
  } finally {
    applySubmitting.value = false
  }
}

const resetFilters = () => {
  filters.keyword = ''
  filters.status = ''
  filters.visibility = ''
}

const openPileManagement = (station) => {
  router.push(`/operator/stations/chargers?stationId=${station.id}`)
}

const handlePageChange = (page) => {
  pagination.page = page
  loadStations()
}

const handleSizeChange = (size) => {
  pagination.page = 1
  pagination.pageSize = size
  loadStations()
}

watch(
  () => [filters.keyword, filters.status, filters.visibility],
  () => {
    if (searchTimer) clearTimeout(searchTimer)
    searchTimer = setTimeout(() => {
      pagination.page = 1
      loadStations()
    }, 300)
  },
)

onMounted(loadStations)

onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer)
})
</script>

<template>
  <div class="page-shell station-page">
    <PageSectionHeader
      eyebrow="资产管理"
      title="电站管理"
      description="维护电站申请资料、审核状态、公开配置和电价模板绑定信息。"
      chip="电站中心"
    >
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="openApplyDialog">申请新建电站</el-button>
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
          <p class="panel-heading__desc">支持按电站名称、地址、模板和审核状态快速检索。</p>
        </div>
        <div class="toolbar-actions">
          <el-button @click="resetFilters">重置</el-button>
          <el-button :loading="loading" @click="loadStations">重新加载</el-button>
        </div>
      </div>

      <div class="filter-row">
        <el-input
          v-model="filters.keyword"
          clearable
          placeholder="搜索电站名称、地址或模板"
          style="width: 340px"
        />
        <el-select v-model="filters.status" placeholder="选择状态" clearable style="width: 160px">
          <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.visibility" placeholder="选择可见性" clearable style="width: 160px">
          <el-option v-for="item in visibilityOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </div>
    </section>

    <section class="page-panel surface-card table-shell">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">电站列表</h3>
          <p class="panel-heading__desc">共 {{ total }} 条记录。</p>
        </div>
      </div>

      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        show-icon
        :closable="false"
        class="panel-alert"
      >
        <template #default>
          <el-button link type="primary" @click="loadStations">重新获取</el-button>
        </template>
      </el-alert>

      <el-table v-if="stations.length" :data="stations" v-loading="loading" stripe>
        <el-table-column label="电站信息" min-width="240">
          <template #default="{ row }">
            <div class="cell-stack">
              <strong>{{ row.station_name }}</strong>
              <span>{{ row.full_address }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="联系人" min-width="170">
          <template #default="{ row }">
            <div class="cell-stack">
              <strong>{{ row.contact_name || '-' }}</strong>
              <span>{{ row.contact_phone || '-' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="规划规模" width="140" align="center">
          <template #default="{ row }">{{ row.planned_charger_count }} 桩 / {{ row.total_power_kw }} kW</template>
        </el-table-column>
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
        <el-table-column prop="charger_count" label="当前电桩数" width="110" align="center" />
        <el-table-column prop="audit_remark" label="审核备注" min-width="180" show-overflow-tooltip />
        <el-table-column prop="created_at" label="提交时间" width="170" />
        <el-table-column label="操作" width="340" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openChargerDrawer(row)">查看资料</el-button>
            <el-button link type="primary" :icon="SetUp" @click="openPileManagement(row)">电桩管理</el-button>
            <el-button link type="info" :disabled="row.status !== 0" @click="openBindDialog(row)">绑定模板</el-button>
            <el-button
              link
              :type="row.visibility === 'public' ? 'warning' : 'success'"
              :disabled="row.status !== 0"
              @click="handleVisibilityChange(row, row.visibility === 'public' ? 'private' : 'public')"
            >
              {{ row.visibility === 'public' ? '设为私有' : '设为公开' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <EmptyStateBlock
        v-else-if="!loading"
        title="暂无电站数据"
        description="当前筛选条件下没有找到电站记录。"
      />

      <div class="pager">
        <el-pagination
          :current-page="pagination.page"
          :page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </section>

    <el-drawer v-model="chargerDrawerVisible" size="860px" :title="currentStation?.station_name || '电站资料'">
      <template v-if="currentStation">
        <div class="drawer-header-card">
          <div>
            <strong>{{ currentStation.station_name }}</strong>
            <p>{{ currentStation.full_address }}</p>
          </div>
          <div class="drawer-tags">
            <el-tag :type="statusTagType(currentStation.status)">{{ currentStation.status_text }}</el-tag>
            <el-tag :type="visibilityTagType(currentStation.visibility)">{{ currentStation.visibility_text }}</el-tag>
          </div>
        </div>

        <el-descriptions :column="2" border class="drawer-descriptions">
          <el-descriptions-item label="联系人">{{ currentStation.contact_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ currentStation.contact_phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="营业时间">{{ currentStation.operation_hours || '-' }}</el-descriptions-item>
          <el-descriptions-item label="停车费说明">{{ currentStation.parking_fee_desc || '-' }}</el-descriptions-item>
          <el-descriptions-item label="经纬度">{{ currentStation.longitude }}, {{ currentStation.latitude }}</el-descriptions-item>
          <el-descriptions-item label="规划规模">
            {{ currentStation.planned_charger_count }} 桩 / {{ currentStation.total_power_kw }} kW
          </el-descriptions-item>
          <el-descriptions-item label="资质说明" :span="2">{{ currentStation.qualification_remark || '-' }}</el-descriptions-item>
          <el-descriptions-item label="站点说明" :span="2">{{ currentStation.station_remark || '-' }}</el-descriptions-item>
          <el-descriptions-item label="审核备注" :span="2">{{ currentStation.audit_remark || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="currentStation.cover_image || currentStation.site_photos?.length" class="photo-panel">
          <div v-if="currentStation.cover_image" class="photo-block">
            <h4>站点封面</h4>
            <el-image :src="currentStation.cover_image" fit="cover" :preview-src-list="[currentStation.cover_image]" />
          </div>
          <div v-if="currentStation.site_photos?.length" class="photo-block">
            <h4>现场图片</h4>
            <div class="photo-grid">
              <el-image
                v-for="item in currentStation.site_photos"
                :key="item"
                :src="item"
                fit="cover"
                :preview-src-list="currentStation.site_photos"
              />
            </div>
          </div>
        </div>

        <el-descriptions :column="4" border class="drawer-descriptions">
          <el-descriptions-item label="电桩总数">{{ chargerSummary.total }}</el-descriptions-item>
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
      </el-table>

      <EmptyStateBlock
        v-if="!chargerLoading && !chargers.length"
        title="暂无电桩数据"
        description="当前电站下还没有电桩，请前往电桩管理页新增或批量生成。"
      />
    </el-drawer>

    <el-dialog v-model="templateDialogVisible" width="760px" title="绑定电价模板">
      <template v-if="currentStation">
        <div class="dialog-station-card">
          <div>
            <strong>{{ currentStation.station_name }}</strong>
            <p>{{ currentStation.full_address }}</p>
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
          <el-descriptions-item label="更新时间">{{ selectedTemplate.updated_at }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <EmptyStateBlock
        v-else
        title="请选择模板"
        description="选中后会在这里展示模板费率信息。"
      />

      <template #footer>
        <el-button @click="templateDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="bindSubmitting" @click="submitBindTemplate">确认绑定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="applyDialogVisible" width="920px" title="申请新建电站">
      <el-form label-width="104px" class="apply-form">
        <div class="form-grid">
          <el-form-item label="电站名称">
            <el-input v-model="applyForm.station_name" placeholder="请输入电站名称" />
          </el-form-item>
          <el-form-item label="联系人">
            <el-input v-model="applyForm.contact_name" placeholder="请输入联系人" />
          </el-form-item>
          <el-form-item label="省">
            <el-input v-model="applyForm.province" placeholder="请输入省份" />
          </el-form-item>
          <el-form-item label="联系电话">
            <el-input v-model="applyForm.contact_phone" placeholder="请输入联系电话" />
          </el-form-item>
          <el-form-item label="市">
            <el-input v-model="applyForm.city" placeholder="请输入城市" />
          </el-form-item>
          <el-form-item label="营业时间">
            <el-input v-model="applyForm.operation_hours" placeholder="例如 00:00-24:00" />
          </el-form-item>
          <el-form-item label="区县">
            <el-input v-model="applyForm.district" placeholder="请输入区县" />
          </el-form-item>
          <el-form-item label="停车费说明">
            <el-input v-model="applyForm.parking_fee_desc" placeholder="例如 首小时免费，后续按停车场规则收费" />
          </el-form-item>
          <el-form-item label="详细地址" class="form-grid__wide">
            <el-input v-model="applyForm.address" placeholder="请输入详细地址" />
          </el-form-item>
          <el-form-item label="经度">
            <el-input-number v-model="applyForm.longitude" :precision="6" :step="0.0001" style="width: 100%" />
          </el-form-item>
          <el-form-item label="纬度">
            <el-input-number v-model="applyForm.latitude" :precision="6" :step="0.0001" style="width: 100%" />
          </el-form-item>
          <el-form-item label="规划电桩数">
            <el-input-number v-model="applyForm.planned_charger_count" :min="1" :max="999" style="width: 100%" />
          </el-form-item>
          <el-form-item label="规划总功率">
            <el-input-number v-model="applyForm.total_power_kw" :min="1" :max="99999" style="width: 100%" />
          </el-form-item>
          <el-form-item label="站点封面" class="form-grid__wide">
            <el-input v-model="applyForm.cover_image" placeholder="可填写图片 URL 作为站点封面" />
          </el-form-item>
          <el-form-item label="站点说明" class="form-grid__wide">
            <el-input v-model="applyForm.station_remark" type="textarea" :rows="3" placeholder="补充站点位置、进出场、配套设施等说明" />
          </el-form-item>
          <el-form-item label="现场图片" class="form-grid__wide">
            <el-input
              v-model="applyForm.site_photos_text"
              type="textarea"
              :rows="3"
              placeholder="每行填写一个图片 URL，可先使用占位地址"
            />
          </el-form-item>
          <el-form-item label="资质补充" class="form-grid__wide">
            <el-input
              v-model="applyForm.qualification_remark"
              type="textarea"
              :rows="3"
              placeholder="补充产权、施工、报建、消防或并网等说明"
            />
          </el-form-item>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="applyDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="applySubmitting" @click="submitApplyStation">提交申请</el-button>
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

.toolbar-actions,
.drawer-tags {
  display: flex;
  gap: 10px;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.panel-alert {
  margin-bottom: 16px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.cell-stack {
  display: grid;
  gap: 6px;
}

.cell-stack span {
  color: var(--color-text-2);
  line-height: 1.5;
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

.drawer-descriptions {
  margin-bottom: 16px;
}

.photo-panel {
  display: grid;
  gap: 16px;
  margin-bottom: 16px;
}

.photo-block h4 {
  margin: 0 0 10px;
}

.photo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.photo-block :deep(.el-image),
.photo-grid :deep(.el-image) {
  width: 100%;
  height: 120px;
  border-radius: 14px;
  overflow: hidden;
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

.apply-form {
  margin-top: 8px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 2px 16px;
}

.form-grid__wide {
  grid-column: 1 / -1;
}

@media (max-width: 1280px) {
  .stats-grid--stations {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .stats-grid--stations,
  .form-grid {
    grid-template-columns: 1fr;
  }

  .drawer-header-card,
  .dialog-station-card,
  .template-detail-card__header {
    flex-direction: column;
  }
}
</style>
