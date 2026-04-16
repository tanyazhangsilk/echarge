<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Bell, CircleCheck, OfficeBuilding, WarningFilled } from '@element-plus/icons-vue'

import PageSectionHeader from '../../../components/console/PageSectionHeader.vue'
import MetricCard from '../../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../../components/console/EmptyStateBlock.vue'
import { fetchStationAudits, processStationAudit } from '../../../api/admin'

const loading = ref(false)
const stations = ref([])
const drawerVisible = ref(false)
const currentStation = ref(null)
const auditSubmitting = ref(false)

const filters = reactive({
  keyword: '',
  status: '',
})

const auditForm = reactive({
  remark: '',
})

const filteredStations = computed(() => {
  const keyword = filters.keyword.trim().toLowerCase()
  return stations.value.filter((item) => {
    const matchKeyword =
      !keyword ||
      [
        item.station_name,
        item.operator_name,
        item.full_address,
        item.contact_name,
        item.contact_phone,
      ]
        .filter(Boolean)
        .some((field) => String(field).toLowerCase().includes(keyword))
    const matchStatus = filters.status === '' || Number(filters.status) === item.status
    return matchKeyword && matchStatus
  })
})

const stats = computed(() => [
  {
    label: '申请总数',
    value: stations.value.length,
    suffix: ' 座',
    trend: '平台电站提报总量',
    trendLabel: '按提交资料进入审核队列',
    tone: 'primary',
    icon: OfficeBuilding,
  },
  {
    label: '待审核',
    value: stations.value.filter((item) => item.status === 3).length,
    suffix: ' 座',
    trend: '等待管理员处理',
    trendLabel: '通过后运营商可继续配桩和绑定模板',
    tone: 'warning',
    icon: Bell,
  },
  {
    label: '已通过',
    value: stations.value.filter((item) => item.status === 0).length,
    suffix: ' 座',
    trend: '已允许继续经营配置',
    trendLabel: '可设置公开站点并发起订单',
    tone: 'success',
    icon: CircleCheck,
  },
  {
    label: '已驳回',
    value: stations.value.filter((item) => item.status === 4).length,
    suffix: ' 座',
    trend: '待运营商补充修正',
    trendLabel: '驳回原因会回写到申请资料',
    tone: 'danger',
    icon: WarningFilled,
  },
])

const statusTagType = (status) => {
  if (status === 0) return 'success'
  if (status === 3) return 'warning'
  if (status === 4) return 'danger'
  return 'info'
}

const loadStations = async () => {
  loading.value = true
  try {
    const { data } = await fetchStationAudits()
    stations.value = data.data || []
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.message || '电站审核列表加载失败')
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
    const { data } = await processStationAudit(currentStation.value.id, {
      action,
      remark: auditForm.remark.trim(),
    })
    ElMessage.success(data.message || '审核处理成功')
    await loadStations()
    currentStation.value = stations.value.find((item) => item.id === currentStation.value.id) || null
    if (currentStation.value) {
      auditForm.remark = currentStation.value.audit_remark || data.data?.remark || ''
    }
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.message || '审核处理失败')
  } finally {
    auditSubmitting.value = false
  }
}

onMounted(loadStations)
</script>

<template>
  <div class="page-shell station-audit-page">
    <PageSectionHeader
      eyebrow="待办审核"
      title="电站审核"
      description="查看运营商提交的完整电站资料，并处理通过或驳回。"
      chip="站点审核"
    >
      <template #actions>
        <el-button :loading="loading" @click="loadStations">刷新</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid stats-grid--audit">
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
          <p class="panel-heading__desc">支持按电站、运营商、联系人和审核状态筛选。</p>
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

      <el-table v-if="filteredStations.length" :data="filteredStations" v-loading="loading" stripe>
        <el-table-column prop="station_name" label="电站名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="operator_name" label="运营商" min-width="180" show-overflow-tooltip />
        <el-table-column label="联系人" min-width="160">
          <template #default="{ row }">
            <div class="cell-stack">
              <strong>{{ row.contact_name || '-' }}</strong>
              <span>{{ row.contact_phone || '-' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="full_address" label="地址" min-width="250" show-overflow-tooltip />
        <el-table-column label="规划规模" width="150" align="center">
          <template #default="{ row }">{{ row.planned_charger_count }} 桩 / {{ row.total_power_kw }} kW</template>
        </el-table-column>
        <el-table-column label="审核状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ row.status_text }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交时间" width="170" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDrawer(row)">查看详情</el-button>
            <el-button v-if="row.status === 3" link type="success" @click="openDrawer(row)">审核处理</el-button>
          </template>
        </el-table-column>
      </el-table>

      <EmptyStateBlock
        v-else-if="!loading"
        title="暂无电站审核记录"
        description="当前没有符合条件的电站申请。"
      />
    </section>

    <el-drawer v-model="drawerVisible" size="860px" :title="currentStation?.station_name || '电站详情'">
      <template v-if="currentStation">
        <div class="station-card">
          <div>
            <strong>{{ currentStation.station_name }}</strong>
            <p>{{ currentStation.operator_name }}</p>
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
          <el-descriptions-item label="规划规模">
            {{ currentStation.planned_charger_count }} 桩 / {{ currentStation.total_power_kw }} kW
          </el-descriptions-item>
          <el-descriptions-item label="当前模板">{{ currentStation.price_template_name || '未绑定模板' }}</el-descriptions-item>
          <el-descriptions-item label="资质补充" :span="2">{{ currentStation.qualification_remark || '-' }}</el-descriptions-item>
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

        <div class="audit-box" v-if="currentStation.status === 3">
          <h4>审核意见</h4>
          <el-input
            v-model="auditForm.remark"
            type="textarea"
            :rows="4"
            placeholder="通过时可填写补充说明，驳回时请明确写明原因"
          />
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
.station-audit-page {
  padding-bottom: 8px;
}

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

.cell-stack span {
  color: var(--color-text-2);
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

.station-card strong {
  display: block;
  margin-bottom: 8px;
  font-size: 18px;
}

.station-card p {
  margin: 0;
  color: var(--color-text-2);
}

.detail-card,
.photo-panel,
.audit-box {
  margin-bottom: 16px;
}

.photo-block h4,
.audit-box h4 {
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

  .station-card {
    flex-direction: column;
  }
}
</style>
