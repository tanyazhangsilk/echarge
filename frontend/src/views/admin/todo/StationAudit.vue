<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Bell, CircleCheck, WarningFilled, OfficeBuilding } from '@element-plus/icons-vue'

import PageSectionHeader from '../../../components/console/PageSectionHeader.vue'
import MetricCard from '../../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../../components/console/EmptyStateBlock.vue'
import { fetchStationAudits, processStationAudit } from '../../../api/admin'

const loading = ref(false)
const stations = ref([])
const drawerVisible = ref(false)
const currentStation = ref(null)

const filters = reactive({
  keyword: '',
  status: '',
})

const filteredStations = computed(() => {
  const keyword = filters.keyword.trim().toLowerCase()
  return stations.value.filter((item) => {
    const matchKeyword =
      !keyword ||
      [item.station_name, item.operator_name, item.address]
        .filter(Boolean)
        .some((field) => String(field).toLowerCase().includes(keyword))
    const matchStatus = !filters.status || Number(filters.status) === item.status
    return matchKeyword && matchStatus
  })
})

const stats = computed(() => [
  {
    label: '站点总数',
    value: stations.value.length,
    suffix: ' 座',
    trend: '平台站点存量',
    trendLabel: '适合截图展示审核规模',
    tone: 'primary',
    icon: OfficeBuilding,
  },
  {
    label: '待审核',
    value: stations.value.filter((item) => item.status === 3).length,
    suffix: ' 座',
    trend: '等待管理员审核',
    trendLabel: '通过后方可公开上线',
    tone: 'warning',
    icon: Bell,
  },
  {
    label: '已上线',
    value: stations.value.filter((item) => item.status === 0).length,
    suffix: ' 座',
    trend: '已审核通过',
    trendLabel: '公开站点可被运营商展示',
    tone: 'success',
    icon: CircleCheck,
  },
  {
    label: '已驳回',
    value: stations.value.filter((item) => item.status === 4).length,
    suffix: ' 座',
    trend: '待运营商整改',
    trendLabel: '驳回后自动转私有',
    tone: 'danger',
    icon: WarningFilled,
  },
])

const loadStations = async () => {
  loading.value = true
  try {
    const { data } = await fetchStationAudits()
    stations.value = data.data || []
  } catch (error) {
    console.error(error)
    ElMessage.error('电站审核列表加载失败')
  } finally {
    loading.value = false
  }
}

const handleAudit = async (row, action) => {
  const title = action === 'approve' ? '审核通过' : '驳回申请'
  try {
    await ElMessageBox.confirm(`确认对“${row.station_name}”执行${title}吗？`, title, {
      type: action === 'approve' ? 'success' : 'warning',
      confirmButtonText: '确认',
      cancelButtonText: '取消',
    })
    const { data } = await processStationAudit(row.id, { action })
    ElMessage.success(data.message || '处理成功')
    await loadStations()
    if (currentStation.value?.id === row.id) {
      currentStation.value = stations.value.find((item) => item.id === row.id) || null
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error(error?.response?.data?.message || '处理失败')
    }
  }
}

const openDrawer = (row) => {
  currentStation.value = row
  drawerVisible.value = true
}

onMounted(loadStations)
</script>

<template>
  <div class="page-shell station-audit-page">
    <PageSectionHeader
      eyebrow="Station Audit"
      title="电站审核"
      description="管理员审核电站上线申请，审核通过后电站才允许公开展示。"
      chip="管理员审核模块"
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
          <p class="panel-heading__desc">支持按电站名称、运营商和审核状态筛选。</p>
        </div>
      </div>

      <div class="filter-row">
        <el-input v-model="filters.keyword" clearable placeholder="搜索电站 / 运营商 / 地址" style="width: 320px" />
        <el-select v-model="filters.status" clearable placeholder="审核状态" style="width: 160px">
          <el-option label="已上线" :value="0" />
          <el-option label="待审核" :value="3" />
          <el-option label="已驳回" :value="4" />
        </el-select>
      </div>
    </section>

    <section class="page-panel surface-card table-shell">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">审核列表</h3>
          <p class="panel-heading__desc">共 {{ filteredStations.length }} 座电站，支持查看详情、通过和驳回。</p>
        </div>
      </div>

      <el-table v-if="filteredStations.length" :data="filteredStations" v-loading="loading" stripe>
        <el-table-column prop="station_name" label="电站名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="operator_name" label="运营商" min-width="180" show-overflow-tooltip />
        <el-table-column prop="address" label="地址" min-width="250" show-overflow-tooltip />
        <el-table-column prop="price_template_name" label="模板" min-width="150" show-overflow-tooltip />
        <el-table-column label="规模" width="130" align="center">
          <template #default="{ row }">{{ row.planned_piles }} 桩 / {{ row.total_power }} kW</template>
        </el-table-column>
        <el-table-column label="可见性" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.visibility === 'public' ? 'success' : 'info'">{{ row.visibility_text }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="审核状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 0 ? 'success' : row.status === 3 ? 'warning' : 'danger'">
              {{ row.status_text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交时间" width="170" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDrawer(row)">查看详情</el-button>
            <el-button v-if="row.status === 3" link type="success" @click="handleAudit(row, 'approve')">通过</el-button>
            <el-button v-if="row.status === 3" link type="danger" @click="handleAudit(row, 'reject')">驳回</el-button>
          </template>
        </el-table-column>
      </el-table>

      <EmptyStateBlock
        v-else-if="!loading"
        title="暂无电站审核记录"
        description="当前没有符合条件的电站记录。"
      />
    </section>

    <el-drawer v-model="drawerVisible" size="680px" :title="currentStation?.station_name || '电站详情'">
      <template v-if="currentStation">
        <div class="station-card">
          <div>
            <strong>{{ currentStation.station_name }}</strong>
            <p>{{ currentStation.operator_name }}</p>
          </div>
          <el-tag :type="currentStation.status === 0 ? 'success' : currentStation.status === 3 ? 'warning' : 'danger'">
            {{ currentStation.status_text }}
          </el-tag>
        </div>

        <el-descriptions :column="1" border>
          <el-descriptions-item label="站点地址">{{ currentStation.address }}</el-descriptions-item>
          <el-descriptions-item label="经纬度">
            {{ currentStation.lng }}, {{ currentStation.lat }}
          </el-descriptions-item>
          <el-descriptions-item label="站点规模">
            {{ currentStation.planned_piles }} 桩 / {{ currentStation.total_power }} kW
          </el-descriptions-item>
          <el-descriptions-item label="模板">{{ currentStation.price_template_name }}</el-descriptions-item>
          <el-descriptions-item label="可见性">{{ currentStation.visibility_text }}</el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ currentStation.created_at }}</el-descriptions-item>
        </el-descriptions>

        <div class="drawer-actions" v-if="currentStation.status === 3">
          <el-button type="danger" plain @click="handleAudit(currentStation, 'reject')">驳回申请</el-button>
          <el-button type="primary" @click="handleAudit(currentStation, 'approve')">审核通过并上线</el-button>
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

.drawer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 18px;
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
