<script setup>
import { ref, reactive } from 'vue'
import { Search, Refresh, Warning } from '@element-plus/icons-vue'

const searchForm = reactive({
  dateRange: [],
  station: '',
  keyword: ''
})

const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(25)

const tableData = ref([
  {
    orderNo: 'ERR202310260005',
    stationName: '中心广场充电站',
    pileNo: 'A05',
    user: '赵六 (13600136000)',
    time: '2023-10-26 14:30:00',
    errorCode: 'E001',
    errorDesc: '连接超时',
    status: 'pending'
  },
  {
    orderNo: 'ERR202310260008',
    stationName: '商业区充电站',
    pileNo: 'B01',
    user: '孙七 (13500135000)',
    time: '2023-10-26 15:45:00',
    errorCode: 'E003',
    errorDesc: '电压异常',
    status: 'processing'
  },
  {
    orderNo: 'ERR202310250012',
    stationName: '工业园充电站',
    pileNo: 'C02',
    user: '周八 (13400134000)',
    time: '2023-10-25 09:10:00',
    errorCode: 'E002',
    errorDesc: '用户中途拔枪',
    status: 'resolved'
  }
])

const handleSearch = () => {
  console.log('search')
}

const handleReset = () => {
  Object.assign(searchForm, { dateRange: [], station: '', keyword: '' })
}

const handleResolve = (row) => {
  console.log('resolve', row)
}

const getStatusType = (status) => {
  const map = {
    pending: 'danger',
    processing: 'warning',
    resolved: 'success'
  }
  return map[status]
}

const getStatusText = (status) => {
  const map = {
    pending: '待处理',
    processing: '处理中',
    resolved: '已解决'
  }
  return map[status]
}
</script>

<template>
  <div class="page-container flex flex-col gap-4">
    <!-- 筛选区域 -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="发生时间">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
          />
        </el-form-item>
        <el-form-item label="充电站">
           <el-input v-model="searchForm.station" placeholder="充电站名称" clearable />
        </el-form-item>
        <el-form-item label="关键字">
          <el-input v-model="searchForm.keyword" placeholder="订单号/用户/错误码" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 列表区域 -->
    <el-card shadow="never" class="table-card flex-1">
      <el-table :data="tableData" style="width: 100%" v-loading="false">
        <el-table-column prop="orderNo" label="异常单号" min-width="180" />
        <el-table-column prop="stationName" label="充电站" min-width="150" />
        <el-table-column prop="pileNo" label="桩号" width="100" />
        <el-table-column prop="user" label="用户" min-width="180" />
        <el-table-column prop="time" label="发生时间" width="180" />
        <el-table-column prop="errorCode" label="错误码" width="100">
           <template #default="{ row }">
            <el-tag type="danger" effect="plain">{{ row.errorCode }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="errorDesc" label="异常描述" min-width="150" />
        <el-table-column prop="status" label="处理状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" v-if="row.status !== 'resolved'" @click="handleResolve(row)">处理</el-button>
            <el-button link type="info" size="small" v-else>详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="mt-4 flex justify-end">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
/* 样式已使用 Tailwind 类名替代，保持与全局风格一致 */
</style>
