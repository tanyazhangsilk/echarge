<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import EmptyStateBlock from '../../../components/console/EmptyStateBlock.vue'
import MetricCard from '../../../components/console/MetricCard.vue'
import PageSectionHeader from '../../../components/console/PageSectionHeader.vue'
import { fetchStationAuditPage } from '../../../api/console'

const loading = ref(false)
const drawerVisible = ref(false)
const records = ref([])
const stats = ref([])
const currentRecord = ref(null)
const filters = reactive({
  keyword: '',
  status: '',
  priority: '',
})

const filteredRecords = computed(() =>
  records.value.filter((item) => {
    const keyword = filters.keyword.trim().toLowerCase()
    const matchKeyword =
      !keyword ||
      [item.stationName, item.operatorName, item.city, item.address].some((field) =>
        String(field).toLowerCase().includes(keyword),
      )
    const matchStatus = !filters.status || item.status === filters.status
    const matchPriority = !filters.priority || item.priority === filters.priority
    return matchKeyword && matchStatus && matchPriority
  }),
)

const loadData = async () => {
  loading.value = true
  try {
    const { data } = await fetchStationAuditPage()
    stats.value = data.stats
    records.value = data.records
  } catch (error) {
    console.error(error)
    ElMessage.error('电站审核页面加载失败。')
  } finally {
    loading.value = false
  }
}

const openDrawer = (row) => {
  currentRecord.value = row
  drawerVisible.value = true
}

const handleAudit = async (row, action) => {
  const text = action === 'approved' ? '通过' : '驳回'
  const result = await ElMessageBox.prompt(`请输入${text}说明，便于后续保留审核痕迹。`, `${text}电站上架申请`, {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    inputPlaceholder: action === 'approved' ? '例如：资料齐全，允许同步上线' : '例如：消防资料缺失，请补充后重新提交',
  }).catch(() => null)

  if (!result) return

  const target = records.value.find((item) => item.id === row.id)
  if (target) {
    target.status = action
    target.gridStatus = action === 'approved' ? '已通过' : '待补资料'
    target.auditHistory = [
      {
        time: new Date().toLocaleString('zh-CN', { hour12: false }),
        action: action === 'approved' ? '平台审核通过' : '平台审核驳回',
        operator: '平台审核组-当前用户',
        note: result.value,
      },
      ...target.auditHistory,
    ]
  }

  if (currentRecord.value?.id === row.id) {
    currentRecord.value = { ...target }
  }

  ElMessage.success(`已${text} ${row.stationName} 的上架申请。`)
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      eyebrow="Station Admission"
      title="电站审核"
      description="用于平台管理员审核电站上架申请，覆盖站点档案、配电规模、附件状态、审核记录和上架动作，适合作为后续接入站点审核接口的前端骨架。"
      chip="电站准入审核"
    >
      <template #actions>
        <el-button @click="filters.keyword = ''; filters.status = ''; filters.priority = ''">清空筛选</el-button>
        <el-button type="primary" @click="loadData">刷新列表</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid">
      <MetricCard
        v-for="item in stats"
        :key="item.label"
        :label="item.label"
        :value="item.value"
        :suffix="item.suffix"
        :hint="item.hint"
        :tone="item.tone"
      />
    </section>

    <article class="page-panel surface-card table-shell">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">电站申请列表</h3>
          <p class="panel-heading__desc">支持按电站、运营商、优先级和状态筛选，列表与详情抽屉已为后端联调预留字段。</p>
        </div>
      </div>

      <div class="toolbar-row toolbar-row--wrap">
        <div class="toolbar-group">
          <el-input v-model="filters.keyword" placeholder="搜索电站名称、运营商、地址" clearable style="width: 320px;" />
          <el-select v-model="filters.status" clearable placeholder="审核状态" style="width: 140px;">
            <el-option label="待审核" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已驳回" value="rejected" />
          </el-select>
          <el-select v-model="filters.priority" clearable placeholder="优先级" style="width: 140px;">
            <el-option label="高优先级" value="high" />
            <el-option label="中优先级" value="medium" />
          </el-select>
        </div>
      </div>

      <el-table v-loading="loading" :data="filteredRecords">
        <el-table-column prop="stationName" label="电站名称" min-width="220" />
        <el-table-column prop="operatorName" label="所属运营商" min-width="220" />
        <el-table-column prop="city" label="城市" min-width="140" />
        <el-table-column label="规模" width="160">
          <template #default="{ row }">{{ row.connectorCount }} 枪 / {{ row.totalPowerKw }} kW</template>
        </el-table-column>
        <el-table-column prop="gridStatus" label="资料状态" min-width="140" />
        <el-table-column label="优先级" width="110">
          <template #default="{ row }">
            <el-tag :type="row.priority === 'high' ? 'danger' : 'warning'">
              {{ row.priority === 'high' ? '高优先级' : '中优先级' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="审核状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.status === 'approved' ? 'success' : row.status === 'rejected' ? 'danger' : 'warning'">
              {{ row.status === 'approved' ? '已通过' : row.status === 'rejected' ? '已驳回' : '待审核' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="submittedAt" label="提交时间" width="160" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openDrawer(row)">查看详情</el-button>
            <el-button v-if="row.status === 'pending'" type="success" link @click="handleAudit(row, 'approved')">通过</el-button>
            <el-button v-if="row.status === 'pending'" type="danger" link @click="handleAudit(row, 'rejected')">驳回</el-button>
          </template>
        </el-table-column>
      </el-table>

      <EmptyStateBlock
        v-if="!loading && filteredRecords.length === 0"
        title="暂无符合条件的电站申请"
        description="可以尝试调整筛选条件，或继续补充站点上架 mock 数据。"
      />
    </article>

    <el-drawer v-model="drawerVisible" title="电站审核详情" size="620px">
      <template v-if="currentRecord">
        <div class="drawer-head">
          <div>
            <h3>{{ currentRecord.stationName }}</h3>
            <p>{{ currentRecord.operatorName }} · {{ currentRecord.city }}</p>
          </div>
          <el-tag :type="currentRecord.status === 'approved' ? 'success' : currentRecord.status === 'rejected' ? 'danger' : 'warning'">
            {{ currentRecord.status === 'approved' ? '已通过' : currentRecord.status === 'rejected' ? '已驳回' : '待审核' }}
          </el-tag>
        </div>

        <div class="info-kv">
          <div class="info-kv__item">
            <p class="info-kv__label">详细地址</p>
            <p class="info-kv__value">{{ currentRecord.address }}</p>
          </div>
          <div class="info-kv__item">
            <p class="info-kv__label">站点类型</p>
            <p class="info-kv__value">{{ currentRecord.stationType }}</p>
          </div>
          <div class="info-kv__item">
            <p class="info-kv__label">功率与枪口</p>
            <p class="info-kv__value">{{ currentRecord.totalPowerKw }} kW / {{ currentRecord.connectorCount }} 枪</p>
          </div>
          <div class="info-kv__item">
            <p class="info-kv__label">车位与服务半径</p>
            <p class="info-kv__value">{{ currentRecord.parkingSlots }} 车位 / {{ currentRecord.serviceRadiusKm }} km</p>
          </div>
          <div class="info-kv__item">
            <p class="info-kv__label">联系人</p>
            <p class="info-kv__value">{{ currentRecord.contactName }} / {{ currentRecord.contactPhone }}</p>
          </div>
          <div class="info-kv__item">
            <p class="info-kv__label">坐标与营业时间</p>
            <p class="info-kv__value">{{ currentRecord.longitude }}, {{ currentRecord.latitude }} / {{ currentRecord.businessHours }}</p>
          </div>
        </div>

        <article class="detail-panel soft-card">
          <div class="detail-panel__header">
            <strong>配套服务</strong>
            <span>{{ currentRecord.photoCount }} 张现场照片</span>
          </div>
          <div class="tag-list">
            <el-tag v-for="item in currentRecord.amenities" :key="item" effect="plain">{{ item }}</el-tag>
          </div>
        </article>

        <article class="detail-panel soft-card">
          <div class="detail-panel__header">
            <strong>附件状态</strong>
            <span>{{ currentRecord.gridStatus }}</span>
          </div>
          <div class="attachment-list">
            <div v-for="item in currentRecord.attachments" :key="item.name" class="attachment-item">
              <span>{{ item.name }}</span>
              <el-tag :type="item.status === 'ready' ? 'success' : 'danger'">
                {{ item.status === 'ready' ? '已上传' : '缺失' }}
              </el-tag>
            </div>
          </div>
        </article>

        <article class="detail-panel soft-card">
          <div class="detail-panel__header">
            <strong>审核记录</strong>
            <span>{{ currentRecord.auditHistory.length }} 条</span>
          </div>
          <div class="timeline-list">
            <div v-for="item in currentRecord.auditHistory" :key="`${item.time}-${item.action}`" class="timeline-item">
              <strong>{{ item.action }}</strong>
              <p>{{ item.time }} · {{ item.operator }}</p>
              <p>{{ item.note }}</p>
            </div>
          </div>
        </article>

        <div class="drawer-actions">
          <el-button @click="drawerVisible = false">关闭</el-button>
          <el-button v-if="currentRecord.status === 'pending'" type="danger" plain @click="handleAudit(currentRecord, 'rejected')">驳回并补件</el-button>
          <el-button v-if="currentRecord.status === 'pending'" type="primary" @click="handleAudit(currentRecord, 'approved')">审核通过并上架</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<style scoped>
.drawer-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.drawer-head h3 {
  margin: 0;
  font-size: 20px;
}

.drawer-head p {
  margin: 6px 0 0;
  color: var(--color-text-3);
}

.detail-panel {
  margin-top: 16px;
  padding: 16px;
}

.detail-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.tag-list,
.attachment-list,
.timeline-list {
  display: grid;
  gap: 10px;
}

.attachment-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.4);
}

.timeline-item {
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid var(--color-border);
  background: rgba(255, 255, 255, 0.4);
}

.timeline-item strong {
  color: var(--color-text);
}

.timeline-item p {
  margin: 6px 0 0;
  color: var(--color-text-2);
  line-height: 1.5;
}

.drawer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}
</style>
