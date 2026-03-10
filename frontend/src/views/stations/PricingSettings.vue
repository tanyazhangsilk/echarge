<script setup>
import { ref } from 'vue'
import { Edit, View, Plus, CopyDocument } from '@element-plus/icons-vue'

const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(100)

const tableData = ref([
  {
    stationName: '南山科技园充电站',
    model: 'time_sharing',
    avgPrice: 1.25,
    serviceFee: 0.60,
    updateTime: '2023-10-25 10:00:00',
    status: 'active'
  },
  {
    stationName: '福田市民中心充电站',
    model: 'flat_rate',
    avgPrice: 1.50,
    serviceFee: 0.80,
    updateTime: '2023-10-24 15:30:00',
    status: 'active'
  },
  {
    stationName: '宝安国际机场充电站',
    model: 'time_sharing',
    avgPrice: 1.80,
    serviceFee: 1.00,
    updateTime: '2023-10-26 09:00:00',
    status: 'active'
  }
])

const getModelText = (model) => {
    return model === 'time_sharing' ? '分时计费(峰平谷)' : '统一计费'
}

const handleConfig = (row) => {
    console.log('配置电价', row)
}

const handleCopy = (row) => {
    console.log('复制模板', row)
}
</script>

<template>
  <div class="page-container flex flex-col gap-4">
    <el-alert 
        title="温馨提示：电价规则修改后，将在次日凌晨 00:00 生效，请谨慎操作。建议在用电低谷期进行调整。" 
        type="warning" 
        show-icon 
        :closable="false"
    />
    
    <el-card shadow="never" class="base-card flex-1">
      <div class="flex justify-between items-center mb-4">
        <div class="text-gray-500 text-sm">共 {{ tableData.length }} 条计费规则</div>
        <el-button type="primary" :icon="Plus">新增电价模板</el-button>
      </div>

      <el-table :data="tableData" style="width: 100%">
        <el-table-column prop="stationName" label="电站名称" min-width="180" />
        <el-table-column prop="model" label="计费模型" width="180">
          <template #default="{ row }">
            <el-tag effect="plain">{{ getModelText(row.model) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="avgPrice" label="当前均价 (元/度)" width="150">
            <template #default="{ row }">
                <span class="font-bold text-orange-500">¥ {{ row.avgPrice.toFixed(2) }}</span>
            </template>
        </el-table-column>
        <el-table-column prop="serviceFee" label="服务费 (元/度)" width="150">
             <template #default="{ row }">
                <span class="text-gray-600">¥ {{ row.serviceFee.toFixed(2) }}</span>
            </template>
        </el-table-column>
        <el-table-column prop="updateTime" label="最后更新时间" width="180" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" :icon="Edit" @click="handleConfig(row)">配置模板</el-button>
            <el-button link type="primary" size="small" :icon="CopyDocument" @click="handleCopy(row)">复制</el-button>
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
