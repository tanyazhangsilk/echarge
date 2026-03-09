<script setup>
import { ref, reactive } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'

// 1. 筛选表单数据
const searchForm = reactive({
  dateRange: [],
  status: '',
  keyword: ''
})

// 2. 表格 Mock 数据
const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

const handleSearch = () => {
  console.log('执行搜索', searchForm)
}
</script>

<template>
  <div class="page-container">
    <el-card class="base-card filter-card" shadow="never">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="订单日期">
          <el-date-picker v-model="searchForm.dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" />
        </el-form-item>
        <el-form-item label="订单状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" style="width: 150px">
            <el-option label="待支付" value="pending" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键字">
          <el-input v-model="searchForm.keyword" placeholder="订单号/手机号/车架号" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="base-card table-card" shadow="never">
      <el-table :data="tableData" style="width: 100%" v-loading="false">
        <el-table-column prop="orderNo" label="订单号" min-width="180" />
        <el-table-column prop="user" label="用户" min-width="120" />
        <el-table-column prop="station" label="充电站/桩" min-width="180" />
        <el-table-column prop="kwh" label="充电量(度)" width="100" />
        <el-table-column prop="fee" label="总费用(元)" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag type="success">已完成</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default>
            <el-button link type="primary" size="small">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
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
.page-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.filter-card {
  margin-bottom: 0;
}
.search-form .el-form-item {
  margin-bottom: 0; /* 让表单在一行内更紧凑 */
}
.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>