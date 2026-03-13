<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'

// 搜索表单 / Search form state
const searchForm = reactive({
  name: '',
  status: '',
})

// 表格数据 / Table data
const tableData = ref([
  {
    id: 1,
    name: '南山科技园充电站',
    region: '深圳市南山区',
    fast: 10,
    slow: 5,
    totalPower: 750.5,
    todayIncome: 3280.0,
    status: 'open',
  },
  {
    id: 2,
    name: '福田市民中心充电站',
    region: '深圳市福田区',
    fast: 18,
    slow: 12,
    totalPower: 1280.0,
    todayIncome: 5126.4,
    status: 'open',
  },
  {
    id: 3,
    name: '宝安国际机场快充站',
    region: '深圳市宝安区',
    fast: 36,
    slow: 8,
    totalPower: 2400.8,
    todayIncome: 9635.2,
    status: 'open',
  },
  {
    id: 4,
    name: '龙岗大运中心充电站',
    region: '深圳市龙岗区',
    fast: 12,
    slow: 20,
    totalPower: 980.0,
    todayIncome: 1840.5,
    status: 'building',
  },
  {
    id: 5,
    name: '罗湖口岸公共充电站',
    region: '深圳市罗湖区',
    fast: 8,
    slow: 16,
    totalPower: 620.5,
    todayIncome: 970.0,
    status: 'open',
  },
  {
    id: 6,
    name: '前海自贸区示范站',
    region: '深圳市南山区',
    fast: 20,
    slow: 10,
    totalPower: 1600.2,
    todayIncome: 0,
    status: 'building',
  },
  {
    id: 7,
    name: '盐田港物流园充电站',
    region: '深圳市盐田区',
    fast: 14,
    slow: 6,
    totalPower: 900.0,
    todayIncome: 365.8,
    status: 'closed',
  },
  {
    id: 8,
    name: '光明科学城综合站',
    region: '深圳市光明区',
    fast: 16,
    slow: 24,
    totalPower: 1450.3,
    todayIncome: 2260.0,
    status: 'open',
  },
])

// 分页状态 / Pagination state
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(tableData.value.length)

// 搜索操作 / Search actions
const handleSearch = () => {
  ElMessage.info('功能开发中')
}

const handleReset = () => {
  ElMessage.info('功能开发中')
}

// 业务操作 / Business actions
const handleAdd = () => {
  ElMessage.info('功能开发中')
}

const handleEdit = () => {
  ElMessage.info('功能开发中')
}

const handlePrice = () => {
  ElMessage.info('功能开发中')
}

const handlePiles = () => {
  ElMessage.info('功能开发中')
}

// 分页事件 / Pagination events
const handleSizeChange = (val) => {
  pageSize.value = val
  ElMessage.info('功能开发中')
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  ElMessage.info('功能开发中')
}

const formatPower = (val) => {
  const num = Number(val)
  if (Number.isNaN(num)) return '-'
  return num.toFixed(1)
}

const formatMoney = (val) => {
  const num = Number(val)
  if (Number.isNaN(num)) return '￥ 0.00'
  return `￥ ${num.toFixed(2)}`
}

const getStatusTagType = (status) => {
  const map = {
    open: 'success',
    building: 'warning',
    closed: 'info',
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    open: '营业中',
    building: '建设中',
    closed: '停业',
  }
  return map[status] || '未知'
}
</script>

<template>
  <div class="station-page">
    <el-card shadow="never" class="action-card">
      <el-row :gutter="12" align="middle">
        <el-col :xs="24" :sm="16" :md="18">
          <div class="action-left">
            <el-input
              v-model="searchForm.name"
              size="default"
              clearable
              :prefix-icon="Search"
              placeholder="电站名称"
              style="width: 220px"
            />
            <el-select
              v-model="searchForm.status"
              size="default"
              clearable
              placeholder="运营状态"
              style="width: 160px"
            >
              <el-option label="营业中" value="open" />
              <el-option label="建设中" value="building" />
              <el-option label="停业" value="closed" />
            </el-select>
            <el-button type="primary" size="default" :icon="Search" @click="handleSearch">查询</el-button>
            <el-button size="default" @click="handleReset">重置</el-button>
          </div>
        </el-col>
        <el-col :xs="24" :sm="8" :md="6">
          <div class="action-right">
            <el-button type="primary" size="default" class="btn-add" @click="handleAdd">+ 新增电站</el-button>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never" class="table-card">
      <el-table :data="tableData" stripe :border="false" fit highlight-current-row class="station-table">
        <el-table-column prop="name" label="电站名称" width="180" align="left" show-overflow-tooltip />
        <el-table-column prop="region" label="所在地区" width="160" align="left" />
        <el-table-column label="快充/慢充桩数量" width="140" align="right" class-name="col-number">
          <template #default="{ row }">{{ row.fast }}/{{ row.slow }}</template>
        </el-table-column>
        <el-table-column prop="totalPower" label="总功率(kW)" width="120" align="right" class-name="col-number">
          <template #default="{ row }">{{ formatPower(row.totalPower) }}</template>
        </el-table-column>
        <el-table-column prop="todayIncome" label="今日收益(元)" width="130" align="right" class-name="col-number">
          <template #default="{ row }">{{ formatMoney(row.todayIncome) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button link class="action-link" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button link class="action-link" @click="handlePrice(scope.row)">配置电价</el-button>
            <el-button link class="action-link" @click="handlePiles(scope.row)">查看电桩</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.station-page {
  min-height: calc(100vh - 60px);
  background: #f5f7fa;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.action-card,
.table-card {
  background: #ffffff;
  border-radius: 4px;
}

.action-left {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.action-right {
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.btn-add {
  margin-right: 8px;
}

.pager {
  text-align: right;
  margin-top: 16px;
}

:deep(.station-table .el-table__header-wrapper th.el-table__cell) {
  background: #fafafa;
  color: #606266;
  font-size: 14px;
}

:deep(.col-number .cell) {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

:deep(.action-link.el-button) {
  color: #409eff;
}

:deep(.action-link.el-button:hover) {
  color: #66b1ff;
}
</style>
