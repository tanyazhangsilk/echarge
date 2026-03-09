<script setup>
import { ref } from 'vue'
import { Search, Refresh, Warning } from '@element-plus/icons-vue'

const searchForm = ref({
  status: '',
  keyword: ''
})

const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(100)

const tableData = ref([
  {
    orderNo: 'ORD202310270001',
    stationName: '中心广场充电站',
    pileNo: 'A01',
    user: '张三 (13800138000)',
    startTime: '2023-10-27 10:00:00',
    duration: '00:45:00',
    kwh: 45.5,
    amount: 56.8,
    status: 'charging'
  },
  {
    orderNo: 'ORD202310270002',
    stationName: '商业区充电站',
    pileNo: 'B02',
    user: '李四 (13900139000)',
    startTime: '2023-10-27 10:15:00',
    duration: '00:30:00',
    kwh: 32.0,
    amount: 40.0,
    status: 'charging'
  },
   {
    orderNo: 'ORD202310270003',
    stationName: '工业园充电站',
    pileNo: 'C03',
    user: '王五 (13700137000)',
    startTime: '2023-10-27 10:20:00',
    duration: '00:25:00',
    kwh: 68.0,
    amount: 85.0,
    status: 'charging'
  }
])

const handleSearch = () => {
  console.log('search')
}

const handleReset = () => {
  searchForm.value = { status: '', keyword: '' }
}

const handleStopCharging = (row) => {
  console.log('stop charging', row)
}
</script>

<template>
  <div class="page-container flex flex-col gap-4">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="16">
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="mb-4 sm:mb-0">
          <div class="flex items-center">
            <div class="p-3 rounded-full bg-blue-100 text-blue-500 mr-4">
              <el-icon :size="24"><img src="https://api.iconify.design/heroicons:bolt.svg" class="w-6 h-6" /></el-icon>
            </div>
            <div>
              <div class="text-gray-500 text-sm">进行中订单</div>
              <div class="text-2xl font-bold">45</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="mb-4 sm:mb-0">
          <div class="flex items-center">
             <div class="p-3 rounded-full bg-green-100 text-green-500 mr-4">
              <el-icon :size="24"><img src="https://api.iconify.design/heroicons:battery-50.svg" class="w-6 h-6" /></el-icon>
            </div>
            <div>
              <div class="text-gray-500 text-sm">累计充电量(今日)</div>
              <div class="text-2xl font-bold">1,245 kWh</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover">
          <div class="flex items-center">
             <div class="p-3 rounded-full bg-orange-100 text-orange-500 mr-4">
              <el-icon :size="24"><img src="https://api.iconify.design/heroicons:currency-yen.svg" class="w-6 h-6" /></el-icon>
            </div>
            <div>
              <div class="text-gray-500 text-sm">预估收益(今日)</div>
              <div class="text-2xl font-bold">¥ 1,850.00</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选区域 -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="充电站">
          <el-input v-model="searchForm.keyword" placeholder="请输入充电站名称" clearable />
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
        <el-table-column prop="orderNo" label="订单号" min-width="180" />
        <el-table-column prop="stationName" label="充电站" min-width="150" />
        <el-table-column prop="pileNo" label="桩号" width="100" />
        <el-table-column prop="user" label="用户" min-width="180" />
        <el-table-column prop="startTime" label="开始时间" width="180" />
        <el-table-column prop="duration" label="已充时长" width="120" />
        <el-table-column prop="kwh" label="已充电量(kWh)" width="140">
           <template #default="{ row }">
            <span class="font-bold text-blue-600">{{ row.kwh }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default>
            <el-tag type="success" effect="light">
              <span class="flex items-center gap-1">
                <span class="animate-pulse w-2 h-2 rounded-full bg-green-500"></span>
                充电中
              </span>
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-popconfirm title="确定要强制结束该订单吗？" @confirm="handleStopCharging(row)">
              <template #reference>
                <el-button link type="danger" size="small">强制结束</el-button>
              </template>
            </el-popconfirm>
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
