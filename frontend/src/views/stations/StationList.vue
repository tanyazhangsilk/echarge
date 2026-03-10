<script setup>
import { ref, reactive } from 'vue'
import { Search, Plus, Edit, View, Delete } from '@element-plus/icons-vue'

const searchForm = reactive({ keyword: '', status: '' })
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(100)

const tableData = ref([
  {
    stationName: '南山科技园充电站',
    address: '深圳市南山区科兴科学园B栋地下停车场',
    operator: '特来电',
    totalPiles: 20,
    idlePiles: 5,
    status: 'operating',
    type: 'public'
  },
  {
    stationName: '福田市民中心充电站',
    address: '深圳市福田区福中三路市民中心停车场',
    operator: '星星充电',
    totalPiles: 50,
    idlePiles: 12,
    status: 'operating',
    type: 'public'
  },
  {
    stationName: '宝安国际机场充电站',
    address: '深圳市宝安区机场南路',
    operator: '南方电网',
    totalPiles: 100,
    idlePiles: 45,
    status: 'maintenance',
    type: 'exclusive'
  },
  {
    stationName: '龙岗大运中心充电站',
    address: '深圳市龙岗区龙翔大道',
    operator: '依威能源',
    totalPiles: 30,
    idlePiles: 0,
    status: 'closed',
    type: 'public'
  }
])

const handleAdd = () => { console.log('新增电站') }
const handleEdit = (row) => { console.log('编辑电站', row) }
const handleViewPiles = (row) => { console.log('查看电桩', row) }

const getStatusType = (status) => {
  const map = {
    operating: 'success',
    building: 'primary',
    maintenance: 'warning',
    closed: 'info'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    operating: '营业中',
    building: '建设中',
    maintenance: '维护中',
    closed: '歇业'
  }
  return map[status] || '未知'
}
</script>

<template>
  <div class="page-container flex flex-col gap-4">
    <el-card shadow="never" class="base-card">
      <div class="flex justify-between items-center mb-4">
        <div class="flex gap-2">
          <el-select v-model="searchForm.status" placeholder="电站状态" style="width: 120px" clearable>
            <el-option label="营业中" value="operating" />
            <el-option label="建设中" value="building" />
            <el-option label="维护中" value="maintenance" />
            <el-option label="歇业" value="closed" />
          </el-select>
          <el-input v-model="searchForm.keyword" placeholder="电站名称/地址" style="width: 200px" clearable :prefix-icon="Search" />
          <el-button type="primary" :icon="Search">查询</el-button>
        </div>
        <el-button type="primary" :icon="Plus" @click="handleAdd">新增电站</el-button>
      </div>

      <el-table :data="tableData" style="width: 100%">
        <el-table-column prop="stationName" label="电站名称" min-width="180" show-overflow-tooltip>
           <template #default="{ row }">
            <div class="font-medium">{{ row.stationName }}</div>
            <div class="text-xs text-gray-400" v-if="row.type === 'exclusive'">专属电站</div>
          </template>
        </el-table-column>
        <el-table-column prop="address" label="详细地址" min-width="250" show-overflow-tooltip />
        <el-table-column prop="operator" label="所属运营商" min-width="120" />
        <el-table-column label="电桩状态 (空闲/总数)" width="180" align="center">
          <template #default="{ row }">
            <div class="flex items-center justify-center gap-1">
              <span class="text-green-600 font-bold">{{ row.idlePiles }}</span>
              <span class="text-gray-400">/</span>
              <span>{{ row.totalPiles }}</span>
            </div>
             <el-progress 
              :percentage="row.totalPiles > 0 ? (row.idlePiles / row.totalPiles) * 100 : 0" 
              :show-text="false" 
              :stroke-width="4"
              :color="row.idlePiles > 0 ? '#67c23a' : '#f56c6c'"
              class="mt-1"
            />
          </template>
        </el-table-column>
        <el-table-column prop="status" label="运营状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" effect="light">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" :icon="Edit" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="primary" size="small" :icon="View" @click="handleViewPiles(row)">电桩</el-button>
            <el-button link type="danger" size="small" :icon="Delete">删除</el-button>
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
