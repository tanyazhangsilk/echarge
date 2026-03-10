<script setup>
import { ref, reactive } from 'vue'
import { Search, Refresh, Warning } from '@element-plus/icons-vue'

const searchForm = reactive({ stationId: '', type: '', status: '' })
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(100)

const tableData = ref([
  {
    pileSn: 'SN202310270001',
    stationName: '南山科技园充电站',
    type: 'dc',
    power: 120,
    status: 'charging',
    currentOrder: 'ORD202310270001'
  },
  {
    pileSn: 'SN202310270002',
    stationName: '南山科技园充电站',
    type: 'dc',
    power: 120,
    status: 'idle',
    currentOrder: ''
  },
  {
    pileSn: 'SN202310270003',
    stationName: '福田市民中心充电站',
    type: 'ac',
    power: 7,
    status: 'offline',
    currentOrder: ''
  },
  {
    pileSn: 'SN202310270004',
    stationName: '宝安国际机场充电站',
    type: 'dc',
    power: 180,
    status: 'fault',
    currentOrder: ''
  }
])

const getStatusType = (status) => {
  const map = {
    charging: 'success',
    idle: 'info',
    offline: 'info',
    fault: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    charging: '充电中',
    idle: '空闲',
    offline: '离线',
    fault: '故障'
  }
  return map[status] || '未知'
}

const getPileType = (type) => {
    return type === 'dc' ? '直流快充' : '交流慢充'
}

const handleRestart = (row) => {
    console.log('重启', row)
}

const handleDetail = (row) => {
    console.log('详情', row)
}
</script>

<template>
  <div class="page-container flex flex-col gap-4">
    <el-card shadow="never" class="base-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="所属电站">
          <el-select v-model="searchForm.stationId" placeholder="请选择电站" style="width: 180px" clearable>
             <el-option label="南山科技园充电站" value="1" />
             <el-option label="福田市民中心充电站" value="2" />
          </el-select>
        </el-form-item>
        <el-form-item label="电桩类型">
          <el-select v-model="searchForm.type" placeholder="全部" style="width: 120px" clearable>
            <el-option label="直流快充" value="dc" />
            <el-option label="交流慢充" value="ac" />
          </el-select>
        </el-form-item>
         <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" style="width: 120px" clearable>
            <el-option label="空闲" value="idle" />
            <el-option label="充电中" value="charging" />
            <el-option label="故障" value="fault" />
            <el-option label="离线" value="offline" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search">查询</el-button>
          <el-button :icon="Refresh">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="base-card flex-1">
      <el-table :data="tableData" style="width: 100%">
        <el-table-column prop="pileSn" label="设备编码(SN)" min-width="180" />
        <el-table-column prop="stationName" label="所属电站" min-width="180" />
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.type === 'dc' ? 'primary' : 'warning'" effect="plain">{{ getPileType(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="power" label="额定功率" width="120">
          <template #default="{ row }"> {{ row.power }} kW </template>
        </el-table-column>
        <el-table-column prop="status" label="实时状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" effect="dark">
                <div class="flex items-center gap-1">
                    <span v-if="row.status === 'charging'" class="animate-pulse w-1.5 h-1.5 rounded-full bg-white"></span>
                    {{ getStatusText(row.status) }}
                </div>
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleDetail(row)">详情</el-button>
            <el-popconfirm title="确定要强制重启该设备吗？" @confirm="handleRestart(row)">
                 <template #reference>
                    <el-button link type="danger" size="small">强制重启</el-button>
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
/* Tailwind classes handled in template */
</style>
