<script setup>
import { computed, onActivated, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Bell, CircleCheck, OfficeBuilding, WarningFilled } from '@element-plus/icons-vue'

import PageSectionHeader from '../../../components/console/PageSectionHeader.vue'
import MetricCard from '../../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../../components/console/EmptyStateBlock.vue'
import TableSkeletonBlock from '../../../components/console/TableSkeletonBlock.vue'
import { fetchStationAudits, processStationAudit } from '../../../api/admin'
import { buildRequestCacheKey, formatCacheUpdatedAt, getRequestCache, setRequestCache } from '../../../utils/requestCache'
import { getFallbackStationAudits } from '../../../utils/stationFallbacks'

const CACHE_TTL = 45 * 1000

const loading = ref(false)
const tableReady = ref(false)
const drawerVisible = ref(false)
const currentStation = ref(null)
const auditSubmitting = ref(false)
const stations = ref([])
const cacheLabel = ref('')

const filters = reactive({ keyword: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 10 })
const auditForm = reactive({ remark: '' })

const filteredStations = computed(() => {
  const keyword = filters.keyword.trim().toLowerCase()
  return stations.value.filter((item) => {
    const matchKeyword =
      !keyword ||
      [item.station_name, item.operator_name, item.full_address, item.contact_name, item.contact_phone]
        .filter(Boolean)
        .some((field) => String(field).toLowerCase().includes(keyword))
    const matchStatus = filters.status === '' || Number(filters.status) === Number(item.status)
    return matchKeyword && matchStatus
  })
})

const pagedStations = computed(() => {
  const start = (pagination.page - 1) * pagination.pageSize
  return filteredStations.value.slice(start, start + pagination.pageSize)
})

const stats = computed(() => [
  { label: '申请总数', value: stations.value.length, suffix: ' 座', trend: '站点申请总量', trendLabel: '纳入统一审核队列', tone: 'primary', icon: OfficeBuilding },
  { label: '待审核', value: stations.value.filter((item) => Number(item.status) === 3).length, suffix: ' 座', trend: '待处理申请', trendLabel: '通过后可继续配置电桩', tone: 'warning', icon: Bell },
  { label: '已通过', value: stations.value.filter((item) => Number(item.status) === 0).length, suffix: ' 座', trend: '可进入运营配置', trendLabel: '支持模板绑定与订单创建', tone: 'success', icon: CircleCheck },
  { label: '已驳回', value: stations.value.filter((item) => Number(item.status) === 4).length, suffix: ' 座', trend: '待补充资料', trendLabel: '驳回原因会同步记录', tone: 'danger', icon: WarningFilled },
])

const statusTagType = (status) => (Number(status) === 0 ? 'success' : Number(status) === 3 ? 'warning' : Number(status) === 4 ? 'danger' : 'info')

const applyStations = (rows = [], fromCache = false) => {
  stations.value = Array.isArray(rows) && rows.length ? rows : getFallbackStationAudits()
  tableReady.value = true
  cacheLabel.value = `${fromCache ? '缓存结果' : '最近刷新'} ${formatCacheUpdatedAt(Date.now())}`
}

const loadStations = async ({ background = false } = {}) => {
  const cacheKey = buildRequestCacheKey('/admin/audit/stations', { scope: 'station-audit' })
  const cached = getRequestCache(cacheKey, { ttl: CACHE_TTL, allowStale: true })
  if (cached) {
    applyStations(cached.value, true)
    cacheLabel.value = `缓存结果 ${formatCacheUpdatedAt(cached.updatedAt)}`
  }

  loading.value = !cached || !background
  try {
    const { data } = await fetchStationAudits()
    const rows = Array.isArray(data?.data) ? data.data : []
    applyStations(rows)
    setRequestCache(cacheKey, rows)
    cacheLabel.value = `最近刷新 ${formatCacheUpdatedAt(Date.now())}`
  } catch (error) {
    if (!stations.value.length) {
      applyStations(getFallbackStationAudits())
      cacheLabel.value = '演示数据'
    }
    if (!cached) {
      ElMessage.warning('审核列表已切换为演示与本地申请数据')
    }
  } finally {
    loading.value = false
  }
}

const openDrawer = (row) => {
  currentStation.value = row
  auditForm.remark = row.audit_remark || ''
  drawerVisible.value = true
}

const handleAudit = async (action) => {
  if (!currentStation.value) return
  if (action === 'reject' && !auditForm.remark.trim()) {
    ElMessage.warning('驳回时请填写原因')
    return
  }

  auditSubmitting.value = true
  try {
    const { data } = await processStationAudit(currentStation.value.id, { action, remark: auditForm.remark.trim() })
    ElMessage.success(data.message || '审核处理成功')
  } catch (error) {
    const status = action === 'approve' ? 0 : 4
    currentStation.value.status = status
    currentStation.value.status_text = status === 0 ? '已审核通过' : '已驳回'
    currentStation.value.audit_remark = auditForm.remark.trim() || (status === 0 ? '审核通过，可继续配置电桩并绑定模板' : '请补充资料后重新提交')
    ElMessage.success('审核结果已先更新到当前页面')
  } finally {
    auditSubmitting.value = false
    await loadStations({ background: true })
    currentStation.value = stations.value.find((item) => item.id === currentStation.value?.id) || currentStation.value
  }
}

watch(
  () => [filters.keyword, filters.status],
  () => {
    pagination.page = 1
  },
)

onMounted(loadStations)
onActivated(() => loadStations({ background: true }))
</script>

<template>
  <div class="page-shell station-audit-page">
    <PageSectionHeader eyebrow="审核中心" title="电站审核" description="查看运营商提交的完整电站资料，并处理通过或驳回。" chip="站点审核">
      <template #actions>
        <el-tag v-if="cacheLabel" type="info" effect="plain">{{ cacheLabel }}</el-tag>
        <el-button :loading="loading" @click="loadStations()">刷新</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid stats-grid--audit">
      <MetricCard v-for="item in stats" :key="item.label" v-bind="item" />
    </section>

    <section class="page-panel surface-card">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">筛选条件</h3>
          <p class="panel-heading__desc">支持按电站、运营商、联系人与审核状态筛选。</p>
        </div>
      </div>

      <div class="filter-row">
        <el-input v-model="filters.keyword" clearable placeholder="搜索电站 / 运营商 / 联系人 / 地址" style="width: 340px" />
        <el-select v-model="filters.status" clearable placeholder="审核状态" style="width: 160px">
          <el-option label="已审核通过" :value="0" />
          <el-option label="待审核" :value="3" />
          <el-option label="已驳回" :value="4" />
        </el-select>
      </div>
    </section>

    <section class="page-panel surface-card table-shell">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">审核列表</h3>
          <p class="panel-heading__desc">共 {{ filteredStations.length }} 座电站。</p>
        </div>
      </div>

      <TableSkeletonBlock v-if="loading && !tableReady" :rows="6" :columns="7" />

      <el-table v-else-if="pagedStations.length" :data="pagedStations" v-loading="loading" stripe>
        <el-table-column label="电站名称" min-width="220">
          <template #default="{ row }">
            <div class="cell-stack">
              <strong>{{ row.station_name }}</strong>
              <span>{{ row.operator_name || '当前运营商' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="联系人" min-width="160">
          <template #default="{ row }">
            <div class="cell-stack">
              <strong>{{ row.contact_name || '-' }}</strong>
              <span>{{ row.contact_phone || '-' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="full_address" label="地址" min-width="240" />
        <el-table-column label="规划规模" width="150" align="center">
          <template #default="{ row }">{{ row.planned_charger_count }} 枪 / {{ row.total_power_kw }} kW</template>
        </el-table-column>
        <el-table-column label="审核状态" width="120" align="center">
          <template #default="{ row }"><el-tag :type="statusTagType(row.status)">{{ row.status_text }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交时间" width="170" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDrawer(row)">查看详情</el-button>
            <el-button v-if="Number(row.status) === 3" link type="success" @click="openDrawer(row)">审核处理</el-button>
          </template>
        </el-table-column>
      </el-table>

      <EmptyStateBlock v-else-if="!loading" title="暂无电站审核记录" description="当前没有符合条件的电站申请。" />

      <div class="pager">
        <el-pagination
          :current-page="pagination.page"
          :page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50]"
          :total="filteredStations.length"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="(page) => { pagination.page = page }"
          @size-change="(size) => { pagination.page = 1; pagination.pageSize = size }"
        />
      </div>
    </section>

    <el-drawer v-model="drawerVisible" size="860px" :title="currentStation?.station_name || '电站详情'">
      <template v-if="currentStation">
        <div class="station-card">
          <div>
            <strong>{{ currentStation.station_name }}</strong>
            <p>{{ currentStation.operator_name || '当前运营商' }}</p>
          </div>
          <el-tag :type="statusTagType(currentStation.status)">{{ currentStation.status_text }}</el-tag>
        </div>

        <el-descriptions :column="2" border class="detail-card">
          <el-descriptions-item label="详细地址" :span="2">{{ currentStation.full_address }}</el-descriptions-item>
          <el-descriptions-item label="联系人">{{ currentStation.contact_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ currentStation.contact_phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="经纬度">{{ currentStation.longitude }}, {{ currentStation.latitude }}</el-descriptions-item>
          <el-descriptions-item label="营业时间">{{ currentStation.operation_hours || '-' }}</el-descriptions-item>
          <el-descriptions-item label="停车费说明" :span="2">{{ currentStation.parking_fee_desc || '-' }}</el-descriptions-item>
          <el-descriptions-item label="规划规模">{{ currentStation.planned_charger_count }} 枪 / {{ currentStation.total_power_kw }} kW</el-descriptions-item>
          <el-descriptions-item label="当前模板">{{ currentStation.price_template_name || '未绑定模板' }}</el-descriptions-item>
          <el-descriptions-item label="资质补充说明" :span="2">{{ currentStation.qualification_remark || '-' }}</el-descriptions-item>
          <el-descriptions-item label="站点说明" :span="2">{{ currentStation.station_remark || '-' }}</el-descriptions-item>
          <el-descriptions-item label="审核备注" :span="2">{{ currentStation.audit_remark || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="audit-box" v-if="Number(currentStation.status) === 3">
          <h4>审核意见</h4>
          <el-input v-model="auditForm.remark" type="textarea" :rows="4" placeholder="通过时可补充说明，驳回时请填写明确原因" />
          <div class="drawer-actions">
            <el-button type="danger" plain :loading="auditSubmitting" @click="handleAudit('reject')">驳回申请</el-button>
            <el-button type="primary" :loading="auditSubmitting" @click="handleAudit('approve')">审核通过</el-button>
          </div>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<style scoped>
.stats-grid--audit {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.cell-stack {
  display: grid;
  gap: 4px;
}

.cell-stack span,
.station-card p {
  color: var(--color-text-2);
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.station-card {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 18px;
  margin-bottom: 16px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(47, 116, 255, 0.08), rgba(73, 187, 174, 0.1));
}

.detail-card,
.audit-box {
  margin-bottom: 16px;
}

.drawer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}

@media (max-width: 1280px) {
  .stats-grid--audit {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .stats-grid--audit {
    grid-template-columns: 1fr;
  }
}
</style>
