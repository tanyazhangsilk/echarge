<script setup>
import { ref } from 'vue'
import { Upload, Document } from '@element-plus/icons-vue'

const activeTab = ref('pending')
const tableData = ref([
  {
    applyDate: '2026-03-08 10:30',
    user: '张三 (13800138000)',
    amount: 235.50,
    email: 'zhangsan@example.com',
    status: 'pending'
  },
  {
    applyDate: '2026-03-08 11:15',
    user: '李四 (13900139000)',
    amount: 120.00,
    email: 'lisi@example.com',
    status: 'pending'
  }
])

const processedData = ref([
    {
    applyDate: '2026-03-07 09:20',
    user: '王五 (13700137000)',
    amount: 500.00,
    email: 'wangwu@example.com',
    status: 'processed',
    invoiceUrl: 'http://example.com/invoice.pdf'
  }
])

const handleUpload = (row) => {
  console.log('触发上传发票逻辑', row)
}

const handleDownload = (row) => {
    console.log('下载发票', row)
}
</script>

<template>
  <div class="page-container flex flex-col gap-4">
    <el-card shadow="never" class="base-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="待处理申请" name="pending">
            <div class="flex justify-end mb-4">
                 <el-button type="primary" plain>批量导出</el-button>
            </div>
          <el-table :data="tableData" style="width: 100%">
            <el-table-column prop="applyDate" label="申请时间" min-width="160" />
            <el-table-column prop="user" label="申请用户" min-width="180" />
            <el-table-column prop="amount" label="开票金额(元)" width="120">
                <template #default="{ row }">
                    <span class="font-bold">¥ {{ row.amount.toFixed(2) }}</span>
                </template>
            </el-table-column>
            <el-table-column prop="email" label="接收邮箱" min-width="200" />
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" size="small" :icon="Upload" @click="handleUpload(row)">上传发票</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        
        <el-tab-pane label="已开票记录" name="processed">
          <el-table :data="processedData" style="width: 100%">
            <el-table-column prop="applyDate" label="申请时间" min-width="160" />
            <el-table-column prop="user" label="申请用户" min-width="180" />
            <el-table-column prop="amount" label="开票金额(元)" width="120">
                 <template #default="{ row }">
                    <span class="font-bold text-gray-500">¥ {{ row.amount.toFixed(2) }}</span>
                </template>
            </el-table-column>
            <el-table-column prop="email" label="接收邮箱" min-width="200" />
            <el-table-column label="状态" width="100">
                <template #default>
                    <el-tag type="success">已发送</el-tag>
                </template>
            </el-table-column>
             <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" :icon="Document" @click="handleDownload(row)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
/* 样式已使用 Tailwind 类名替代 */
</style>
