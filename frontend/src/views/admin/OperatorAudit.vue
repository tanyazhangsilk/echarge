<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import { fetchOperatorAuditPage } from '../../api/console'

const loading = ref(false)
const drawerVisible = ref(false)
const currentRecord = ref(null)
const stats = ref([])
const sourceChannels = ref([])
const records = ref([])
const filters = reactive({
  keyword: '',
  status: '',
  riskLevel: '',
})

const statusTagMap = {
  pending: 'warning',
  approved: 'success',
  rejected: 'danger',
}

const filteredRecords = computed(() =>
  records.value.filter((item) => {
    const keyword = filters.keyword.trim().toLowerCase()
    const matchKeyword =
      !keyword ||
      [item.operatorName, item.creditCode, item.contactName, item.cityGroup].some((field) =>
        String(field).toLowerCase().includes(keyword),
      )
    const matchStatus = !filters.status || item.status === filters.status
    const matchRisk = !filters.riskLevel || item.riskLevel === filters.riskLevel
    return matchKeyword && matchStatus && matchRisk
  }),
)

const loadData = async () => {
  loading.value = true
  try {
    const { data } = await fetchOperatorAuditPage()
    stats.value = data.stats
    sourceChannels.value = data.channels
    records.value = data.records
  } catch (error) {
    console.error(error)
    ElMessage.error('运营商审核页面加载失败。')
  } finally {
    loading.value = false
  }
}

const openDrawer = (row) => {
  currentRecord.value = row
  drawerVisible.value = true
}

const handleAudit = async (row, action) => {
  const actionText = action === 'approved' ? '通过' : '驳回'
  const result = await ElMessageBox.prompt(`请输入${actionText}说明，后续可直接映射到审核备注字段。`, `${actionText}运营商申请`, {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    inputPlaceholder: action === 'approved' ? '例如：资料完整，允许进入结算配置' : '例如：授权委托书已过期，请补件后重提',
  }).catch(() => null)

  if (!result) return

  const target = records.value.find((item) => item.id === row.id)
  if (target) {
    target.status = action
    target.reviewer = '平台审核组-当前用户'
    target.remark = result.value || (action === 'approved' ? '已通过人工终审。' : '已驳回，等待补件。')
  }

  if (currentRecord.value?.id === row.id) {
    currentRecord.value = { ...target }
  }

  ElMessage.success(`已${actionText} ${row.operatorName} 的入驻申请。`)
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      eyebrow="Operator Admission"
      title="运营商审核"
      description="用于平台管理员审核充电运营商准入资料，覆盖主体信息、结算信息、附件进度、风险等级和审核动作，为后续真实入驻流程保留扩展空间。"
      chip="管理员审核流"
    >
      <template #actions>
        <el-button @click="filters.keyword = ''; filters.status = ''; filters.riskLevel = ''">清空筛选</el-button>
        <el-button type="primary" @click="loadData">刷新列表</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid">
      <MetricCard
        v-for="item in stats"
        :key="item.label"
        :label="item.label"
        :value="item.value"
        :hint="item.hint"
        :tone="item.tone"
      />
    </section>

    <section class="split-layout">
      <article class="page-panel surface-card table-shell">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">审核列表</h3>
            <p class="panel-heading__desc">支持按运营商、状态和风险等级筛选，详情通过抽屉展开，便于后续直接替换成真实接口。</p>
          </div>
        </div>

        <div class="toolbar-row toolbar-row--wrap">
          <div class="toolbar-group">
            <el-input v-model="filters.keyword" placeholder="搜索运营商、统一社会信用代码、联系人" clearable style="width: 320px;" />
            <el-select v-model="filters.status" clearable placeholder="审核状态" style="width: 140px;">
              <el-option label="待审核" value="pending" />
              <el-option label="已通过" value="approved" />
              <el-option label="已驳回" value="rejected" />
            </el-select>
            <el-select v-model="filters.riskLevel" clearable placeholder="风险等级" style="width: 140px;">
              <el-option label="高风险" value="high" />
              <el-option label="中风险" value="medium" />
              <el-option label="低风险" value="low" />
            </el-select>
          </div>
        </div>

        <el-table v-loading="loading" :data="filteredRecords">
          <el-table-column prop="operatorName" label="运营商名称" min-width="240" />
          <el-table-column prop="cityGroup" label="覆盖区域" min-width="160" />
          <el-table-column prop="stationCount" label="电站数" width="90" />
          <el-table-column prop="connectorCount" label="枪口数" width="90" />
          <el-table-column label="附件进度" width="120">
            <template #default="{ row }">{{ row.attachmentProgress }}/{{ row.attachmentTotal }}</template>
          </el-table-column>
          <el-table-column label="风险等级" width="110">
            <template #default="{ row }">
              <el-tag :type="row.riskLevel === 'high' ? 'danger' : row.riskLevel === 'medium' ? 'warning' : 'success'">
                {{ row.riskLevel === 'high' ? '高风险' : row.riskLevel === 'medium' ? '中风险' : '低风险' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="审核状态" width="110">
            <template #default="{ row }">
              <el-tag :type="statusTagMap[row.status]">
                {{ row.status === 'pending' ? '待审核' : row.status === 'approved' ? '已通过' : '已驳回' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="submittedAt" label="提交时间" width="160" />
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openDrawer(row)">查看详情</el-button>
              <el-button v-if="row.status === 'pending'" link type="success" @click="handleAudit(row, 'approved')">通过</el-button>
              <el-button v-if="row.status === 'pending'" link type="danger" @click="handleAudit(row, 'rejected')">驳回</el-button>
            </template>
          </el-table-column>
        </el-table>

        <EmptyStateBlock
          v-if="!loading && filteredRecords.length === 0"
          title="暂无匹配的运营商申请"
          description="可尝试重置筛选条件，或补充更多入驻申请数据。"
        />
      </article>

      <article class="page-panel surface-card">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">来源渠道分布</h3>
            <p class="panel-heading__desc">保留渠道字段，后续便于做平台招商与区域合作分析。</p>
          </div>
        </div>
        <div class="channel-list">
          <div v-for="item in sourceChannels" :key="item.channel" class="list-card">
            <div class="channel-item">
              <strong class="list-card__title">{{ item.channel }}</strong>
              <span class="channel-item__count">{{ item.count }} 家</span>
            </div>
          </div>
        </div>
      </article>
    </section>

    <el-drawer v-model="drawerVisible" title="运营商审核详情" size="560px">
      <template v-if="currentRecord">
        <div class="drawer-head">
          <h3>{{ currentRecord.operatorName }}</h3>
          <el-tag :type="statusTagMap[currentRecord.status]">
            {{ currentRecord.status === 'pending' ? '待审核' : currentRecord.status === 'approved' ? '已通过' : '已驳回' }}
          </el-tag>
        </div>

        <div class="info-kv">
          <div class="info-kv__item">
            <p class="info-kv__label">统一社会信用代码</p>
            <p class="info-kv__value">{{ currentRecord.creditCode }}</p>
          </div>
          <div class="info-kv__item">
            <p class="info-kv__label">企业类型</p>
            <p class="info-kv__value">{{ currentRecord.companyType }}</p>
          </div>
          <div class="info-kv__item">
            <p class="info-kv__label">结算账户</p>
            <p class="info-kv__value">{{ currentRecord.settlementAccount }}</p>
          </div>
          <div class="info-kv__item">
            <p class="info-kv__label">联系人</p>
            <p class="info-kv__value">{{ currentRecord.contactName }} / {{ currentRecord.contactPhone }}</p>
          </div>
          <div class="info-kv__item">
            <p class="info-kv__label">覆盖区域</p>
            <p class="info-kv__value">{{ currentRecord.cityGroup }}</p>
          </div>
          <div class="info-kv__item">
            <p class="info-kv__label">当前规模</p>
            <p class="info-kv__value">{{ currentRecord.stationCount }} 座电站 / {{ currentRecord.connectorCount }} 个枪口</p>
          </div>
        </div>

        <article class="detail-panel soft-card">
          <div class="detail-panel__header">
            <strong>资料检查</strong>
            <span>{{ currentRecord.attachmentProgress }}/{{ currentRecord.attachmentTotal }}</span>
          </div>
          <el-progress :percentage="Math.round((currentRecord.attachmentProgress / currentRecord.attachmentTotal) * 100)" />
          <p class="detail-panel__remark">{{ currentRecord.remark }}</p>
        </article>

        <article class="detail-panel soft-card">
          <div class="detail-panel__header">
            <strong>审核记录</strong>
            <span>{{ currentRecord.reviewer || '待人工审核' }}</span>
          </div>
          <p class="detail-panel__remark">
            {{ currentRecord.status === 'pending' ? '当前处于待审核状态，可执行通过或驳回。' : currentRecord.remark }}
          </p>
        </article>

        <div class="drawer-actions">
          <el-button @click="drawerVisible = false">关闭</el-button>
          <el-button v-if="currentRecord.status === 'pending'" type="danger" plain @click="handleAudit(currentRecord, 'rejected')">驳回申请</el-button>
          <el-button v-if="currentRecord.status === 'pending'" type="primary" @click="handleAudit(currentRecord, 'approved')">审核通过</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<style scoped>
.channel-list {
  display: grid;
  gap: 12px;
}

.channel-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.channel-item__count {
  color: var(--color-primary-strong);
  font-weight: 700;
}

.drawer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.drawer-head h3 {
  margin: 0;
  font-size: 20px;
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

.detail-panel__remark {
  margin: 12px 0 0;
  color: var(--color-text-2);
  line-height: 1.6;
}

.drawer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}
</style>
