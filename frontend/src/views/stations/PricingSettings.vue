<script setup>
import Sortable from 'sortablejs'
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, Edit, Plus, Star, StarFilled, View } from '@element-plus/icons-vue'

import {
  calcCoverageMinutes,
  createDefaultPeriodForGap,
  disabledMinutes30Step,
  findFirstGap,
  hasOverlap,
  minutesToTime,
  parseTimeToMinutes,
} from '../../utils/pricing'
import { saveTemplateToList } from '../../utils/pricingStore'

/**
 * 业务类型枚举 / Period type enum
 */
const PERIOD_TYPES = {
  PEAK: 'Peak',
  FLAT: 'Flat',
  VALLEY: 'Valley',
}

/**
 * 时段颜色映射 / Color map for period types
 */
const PERIOD_COLORS = {
  [PERIOD_TYPES.PEAK]: '#F56C6C',
  [PERIOD_TYPES.FLAT]: '#409EFF',
  [PERIOD_TYPES.VALLEY]: '#67C23A',
}

/**
 * 模板列表 / Template list
 */
const templates = reactive([
  {
    id: 'tpl-001',
    name: '深圳运营商默认模板（峰平谷）',
    isDefault: true,
    stationIds: ['st-001', 'st-002', 'st-003'],
    periods: [
      { id: 'p-001', type: PERIOD_TYPES.VALLEY, timeRange: ['00:00', '07:00'], elecFee: 0.6821, serviceFee: 0.3500 },
      { id: 'p-002', type: PERIOD_TYPES.FLAT, timeRange: ['07:00', '10:00'], elecFee: 0.9321, serviceFee: 0.4500 },
      { id: 'p-003', type: PERIOD_TYPES.PEAK, timeRange: ['10:00', '12:00'], elecFee: 1.2321, serviceFee: 0.6000 },
      { id: 'p-004', type: PERIOD_TYPES.FLAT, timeRange: ['12:00', '18:00'], elecFee: 0.9321, serviceFee: 0.4500 },
      { id: 'p-005', type: PERIOD_TYPES.PEAK, timeRange: ['18:00', '22:00'], elecFee: 1.3321, serviceFee: 0.6500 },
      { id: 'p-006', type: PERIOD_TYPES.VALLEY, timeRange: ['22:00', '24:00'], elecFee: 0.6821, serviceFee: 0.3500 },
    ],
  },
  {
    id: 'tpl-002',
    name: '园区夜间优惠模板',
    isDefault: false,
    stationIds: ['st-004'],
    periods: [
      { id: 'p-101', type: PERIOD_TYPES.FLAT, timeRange: ['00:00', '08:00'], elecFee: 0.8000, serviceFee: 0.3000 },
      { id: 'p-102', type: PERIOD_TYPES.PEAK, timeRange: ['08:00', '12:00'], elecFee: 1.2000, serviceFee: 0.5000 },
      { id: 'p-103', type: PERIOD_TYPES.FLAT, timeRange: ['12:00', '18:00'], elecFee: 0.9000, serviceFee: 0.3500 },
      { id: 'p-104', type: PERIOD_TYPES.VALLEY, timeRange: ['18:00', '24:00'], elecFee: 0.6500, serviceFee: 0.2500 },
    ],
  },
  {
    id: 'tpl-003',
    name: '统一计费模板（测试）',
    isDefault: false,
    stationIds: [],
    periods: [
      { id: 'p-201', type: PERIOD_TYPES.FLAT, timeRange: ['00:00', '24:00'], elecFee: 0.9800, serviceFee: 0.3800 },
    ],
  },
])

/**
 * 当前编辑模板 / Current template
 */
const currentTemplate = reactive({
  id: '',
  name: '',
  isDefault: false,
  stationIds: [],
})

/**
 * 时段数组 / Period array (editable)
 */
const timePeriods = reactive([])

/**
 * 加载态 / Loading state
 */
const loading = ref(false)

/**
 * 左侧选中行 / Selected template row
 */
const selectedTemplateId = ref(templates[0]?.id || '')

/**
 * 电站树数据 / Station tree data
 */
const stationTreeData = ref([
  {
    id: 'op-001',
    name: '特来电（运营商）',
    children: [
      { id: 'st-001', name: '南山科技园充电站' },
      { id: 'st-002', name: '福田市民中心充电站' },
    ],
  },
  {
    id: 'op-002',
    name: '星星充电（运营商）',
    children: [
      { id: 'st-003', name: '宝安国际机场充电站' },
      { id: 'st-004', name: '中心广场充电站' },
    ],
  },
])

/**
 * 应用到电站弹窗 / Apply-to-stations dialog state
 */
const applyDialogVisible = ref(false)
const applyLoading = ref(false)
const selectedStationRows = ref([])

const formRef = ref()
const periodTableRef = ref()
let sortableInstance

/**
 * 计算：已分配分钟数 / totalMinutes computed
 */
const totalHours = computed(() => {
  const minutes = calcCoverageMinutes(timePeriods)
  return minutes / 60
})

/**
 * 计算：是否覆盖完整 24 小时 / isFullDay computed
 */
const isFullDay = computed(() => totalHours.value === 24)

/**
 * 计算：彩色横条 24 等分颜色 / 24-hour color bar blocks
 */
const hourBlocks = computed(() => {
  const blocks = []
  for (let h = 0; h < 24; h += 1) {
    const mid = h * 60 + 30
    const matched = timePeriods.find((p) => {
      const start = parseTimeToMinutes(p.timeRange?.[0])
      const end = parseTimeToMinutes(p.timeRange?.[1])
      return start !== null && end !== null && start <= mid && mid < end
    })
    const type = matched?.type || PERIOD_TYPES.FLAT
    blocks.push({
      hour: h,
      color: PERIOD_COLORS[type] || PERIOD_COLORS[PERIOD_TYPES.FLAT],
      tooltip: `${minutesToTime(h * 60)} - ${minutesToTime((h + 1) * 60)}`,
    })
  }
  return blocks
})

/**
 * 表单规则 / Form rules
 */
const rules = {
  name: [
    {
      required: true,
      message: '请输入模板名称',
      trigger: 'blur',
    },
    {
      max: 50,
      message: '模板名称最多 50 个字符',
      trigger: 'blur',
    },
    {
      validator: (_, value, callback) => {
        const val = String(value || '').trim()
        const duplicated = templates.some((tpl) => tpl.name === val && tpl.id !== currentTemplate.id)
        if (duplicated) callback(new Error('模板名称已存在，请更换'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
}

/**
 * 设为默认模板 / Set default template
 */
const setDefaultTemplate = async (tpl) => {
  loading.value = true
  try {
    await new Promise((r) => setTimeout(r, 200))
    templates.forEach((t) => {
      t.isDefault = t.id === tpl.id
    })
    if (currentTemplate.id === tpl.id) currentTemplate.isDefault = true
    ElMessage.success('已设为默认模板')
  } finally {
    loading.value = false
  }
}

/**
 * 删除模板 / Delete template
 */
const deleteTemplate = async (tpl) => {
  loading.value = true
  try {
    await new Promise((r) => setTimeout(r, 200))
    const idx = templates.findIndex((t) => t.id === tpl.id)
    if (idx >= 0) templates.splice(idx, 1)
    if (selectedTemplateId.value === tpl.id) {
      selectedTemplateId.value = templates[0]?.id || ''
      if (selectedTemplateId.value) selectTemplateById(selectedTemplateId.value)
    }
    ElMessage.success('模板已删除')
  } finally {
    loading.value = false
  }
}

/**
 * 选择模板 / Select template
 * @param {string} id template id
 */
const selectTemplateById = (id) => {
  const tpl = templates.find((t) => t.id === id)
  if (!tpl) return

  selectedTemplateId.value = id
  currentTemplate.id = tpl.id
  currentTemplate.name = tpl.name
  currentTemplate.isDefault = tpl.isDefault
  currentTemplate.stationIds = [...(tpl.stationIds || [])]

  timePeriods.splice(0, timePeriods.length)
  tpl.periods.forEach((p) => {
    timePeriods.push({ ...p, timeRange: [...p.timeRange] })
  })
}

/**
 * 添加时段 / Add new period
 */
const addPeriod = () => {
  if (hasOverlap(timePeriods)) {
    ElMessage.error('存在重叠时段，无法自动添加，请先调整')
    return
  }
  const gap = findFirstGap(timePeriods)
  if (!gap) {
    ElMessage.info('已覆盖完整 24 小时，无可用时段')
    return
  }
  const newPeriod = createDefaultPeriodForGap(gap, PERIOD_TYPES.FLAT)
  timePeriods.push(newPeriod)
}

/**
 * 删除时段 / Remove period (at least 3 rows)
 */
const removePeriod = (row) => {
  if (timePeriods.length <= 3) {
    ElMessage.warning('至少保留 3 个时段')
    return
  }
  const idx = timePeriods.findIndex((p) => p.id === row.id)
  if (idx >= 0) timePeriods.splice(idx, 1)
}

/**
 * 保存模板 / Save template
 */
const saveTemplate = async () => {
  const validateFn = formRef.value?.validate
  const valid = validateFn ? await validateFn().catch(() => false) : true
  if (!valid) return false

  if (hasOverlap(timePeriods)) {
    ElMessage.error('时段存在重叠，请调整后再保存')
    return false
  }
  if (!isFullDay.value) {
    ElMessage.error('时段未覆盖完整 24 小时，请补全后再保存')
    return false
  }

  loading.value = true
  try {
    await new Promise((r) => setTimeout(r, 300))
    const idx = templates.findIndex((t) => t.id === currentTemplate.id)
    if (idx < 0) {
      ElMessage.error('模板不存在')
      return false
    }
    const next = saveTemplateToList(
      templates,
      currentTemplate.id,
      {
        name: currentTemplate.name,
        isDefault: currentTemplate.isDefault,
        stationIds: currentTemplate.stationIds,
      },
      timePeriods
    )
    templates.splice(0, templates.length, ...next)
    ElMessage.success('模板保存成功')
    return true
  } finally {
    loading.value = false
  }
}

/**
 * 打开“应用到电站”弹窗 / Open apply dialog
 */
const openApplyDialog = () => {
  applyDialogVisible.value = true
}

/**
 * 提交应用到电站 / Confirm apply
 */
const confirmApplyStations = async () => {
  const leafStations = selectedStationRows.value.filter((r) => !r.children)
  const stationIds = leafStations.map((r) => r.id)

  applyLoading.value = true
  try {
    await new Promise((r) => setTimeout(r, 300))
    currentTemplate.stationIds = stationIds
    const tpl = templates.find((t) => t.id === currentTemplate.id)
    if (tpl) tpl.stationIds = [...stationIds]
    ElMessage.success('已应用到电站')
    applyDialogVisible.value = false
  } finally {
    applyLoading.value = false
  }
}

/**
 * 表格树选择变化 / Station selection change
 */
const handleStationSelectionChange = (rows) => {
  selectedStationRows.value = rows
}

/**
 * 绑定拖拽排序 / Bind SortableJS for periods
 */
const bindSortable = () => {
  const tbody = periodTableRef.value?.$el?.querySelector('.el-table__body-wrapper tbody')
  if (!tbody) return

  sortableInstance?.destroy?.()
  sortableInstance = Sortable.create(tbody, {
    animation: 150,
    handle: '.drag-handle',
    onEnd: (evt) => {
      const { oldIndex, newIndex } = evt
      if (oldIndex == null || newIndex == null || oldIndex === newIndex) return
      const moved = timePeriods.splice(oldIndex, 1)[0]
      timePeriods.splice(newIndex, 0, moved)
    },
  })
}

onMounted(() => {
  if (selectedTemplateId.value) selectTemplateById(selectedTemplateId.value)
  bindSortable()
})

onUnmounted(() => {
  sortableInstance?.destroy?.()
  sortableInstance = null
})

defineExpose({
  hasOverlap,
  saveTemplate,
  openApplyDialog,
  confirmApplyStations,
  handleStationSelectionChange,
  templates,
  currentTemplate,
  timePeriods,
})
</script>

<template>
  <div class="pricing-page">
    <el-row :gutter="16">
      <el-col :xs="24" :md="7">
        <el-card shadow="never" class="panel-card">
          <div class="panel-title">模板列表</div>
          <el-table
            :data="templates"
            row-key="id"
            highlight-current-row
            :current-row-key="selectedTemplateId"
            @row-click="(row) => selectTemplateById(row.id)"
          >
            <el-table-column prop="name" label="模板名称" min-width="160" show-overflow-tooltip />
            <el-table-column label="默认" width="72" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.isDefault" type="success" effect="plain">是</el-tag>
                <el-tag v-else type="info" effect="plain">否</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button link :icon="Edit" @click.stop="selectTemplateById(row.id)">编辑</el-button>
                <el-button link :icon="Delete" type="danger" @click.stop="deleteTemplate(row)">删除</el-button>
                <el-button
                  v-if="!row.isDefault"
                  link
                  :icon="Star"
                  type="primary"
                  @click.stop="setDefaultTemplate(row)"
                >
                  设为默认
                </el-button>
                <el-button v-else link :icon="StarFilled" type="success" disabled>默认</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="17">
        <el-card shadow="never" class="panel-card" v-loading="loading">
          <template #header>
            <div class="header-row">
              <div class="header-title">模板详情与编辑：{{ currentTemplate.name || '未命名模板' }}</div>
              <div class="header-meta">
                <el-tag v-if="isFullDay" type="success" effect="plain">已覆盖 24 小时</el-tag>
                <el-tag v-else type="warning" effect="plain">已分配 {{ totalHours.toFixed(1) }} 小时</el-tag>
              </div>
            </div>
          </template>

          <el-form ref="formRef" :model="currentTemplate" :rules="rules" label-width="120px" class="detail-form">
            <div class="section-title">基础信息</div>
            <el-form-item label="模板名称" prop="name" required>
              <el-input v-model="currentTemplate.name" maxlength="50" show-word-limit placeholder="请输入模板名称" />
            </el-form-item>
            <el-form-item label="适用电站数量">
              <el-input-number :model-value="currentTemplate.stationIds.length" :min="0" :controls="false" disabled />
              <el-button link type="primary" :icon="View" @click="openApplyDialog">查看电站</el-button>
            </el-form-item>

            <div class="section-title">24 小时时段费率</div>

            <div class="hour-bar" aria-label="24小时费率色带">
              <div
                v-for="b in hourBlocks"
                :key="b.hour"
                class="hour-block"
                :style="{ background: b.color }"
                :title="b.tooltip"
              ></div>
            </div>

            <el-table ref="periodTableRef" :data="timePeriods" row-key="id" class="period-table">
              <el-table-column label="" width="44" align="center">
                <template #default>
                  <span class="drag-handle">⋮⋮</span>
                </template>
              </el-table-column>
              <el-table-column label="时段类型" width="120">
                <template #default="{ row }">
                  <el-tag
                    :style="{ background: PERIOD_COLORS[row.type], borderColor: PERIOD_COLORS[row.type], color: '#fff' }"
                    effect="dark"
                  >
                    {{ row.type }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="时段范围" min-width="260">
                <template #default="{ row }">
                  <el-time-picker
                    v-model="row.timeRange"
                    is-range
                    format="HH:mm"
                    value-format="HH:mm"
                    range-separator="~"
                    start-placeholder="开始"
                    end-placeholder="结束"
                    :disabled-minutes="disabledMinutes30Step"
                  />
                </template>
              </el-table-column>
              <el-table-column label="基础电费(元/度)" width="180" align="right">
                <template #default="{ row }">
                  <el-input-number v-model="row.elecFee" :precision="4" :min="0" :max="9.9999" controls-position="right" />
                </template>
              </el-table-column>
              <el-table-column label="服务费(元/度)" width="180" align="right">
                <template #default="{ row }">
                  <el-input-number v-model="row.serviceFee" :precision="4" :min="0" :max="9.9999" controls-position="right" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100" align="center">
                <template #default="{ row }">
                  <el-button link type="danger" @click="removePeriod(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>

            <div class="period-actions">
              <el-button :icon="Plus" @click="addPeriod">添加时段</el-button>
              <div class="period-tip">
                <span v-if="hasOverlap(timePeriods)" class="tip-danger">存在重叠时段</span>
                <span v-else-if="!isFullDay" class="tip-warn">未覆盖 24 小时</span>
                <span v-else class="tip-ok">时段完整且无重叠</span>
              </div>
            </div>

            <div class="footer-bar">
              <el-button type="primary" @click="saveTemplate">保存模板</el-button>
              <el-button @click="openApplyDialog">应用到电站</el-button>
            </div>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="applyDialogVisible" title="应用到电站" width="720px">
      <el-table
        :data="stationTreeData"
        row-key="id"
        default-expand-all
        :tree-props="{ children: 'children' }"
        @selection-change="handleStationSelectionChange"
        v-loading="applyLoading"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column prop="name" label="电站/运营商" min-width="320" />
      </el-table>
      <template #footer>
        <el-button @click="applyDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="applyLoading" @click="confirmApplyStations">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.pricing-page {
  width: 100%;
}

.panel-card {
  border-radius: 8px;
}

.panel-title {
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 10px;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.header-title {
  font-weight: 700;
}

.detail-form {
  width: 100%;
}

.section-title {
  margin: 8px 0 12px;
  font-weight: 700;
  color: var(--text-primary);
}

.hour-bar {
  display: flex;
  width: 100%;
  height: 16px;
  border-radius: 4px;
  overflow: hidden;
  margin: 4px 0 14px;
}

.hour-block {
  width: 4.17%;
  height: 16px;
}

.period-table :deep(.el-table__row) {
  height: 48px;
}

.drag-handle {
  cursor: grab;
  user-select: none;
  font-size: 14px;
  color: #909399;
}

.period-actions {
  margin-top: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.period-tip {
  font-size: 12px;
}

.tip-danger {
  color: #f56c6c;
}

.tip-warn {
  color: #e6a23c;
}

.tip-ok {
  color: #67c23a;
}

.footer-bar {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 768px) {
  .header-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
