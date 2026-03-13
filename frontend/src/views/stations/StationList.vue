<script setup>
import { ref } from 'vue'
import { Search, Plus, OfficeBuilding, CircleCheck, Connection, Money } from '@element-plus/icons-vue'

// 顶部高级统计数据 (加入副标题指标)
const statCards = [
  { title: '电站总数', value: '12', unit: '座', desc: '较上周新增 1 座', icon: OfficeBuilding, color: '#409EFF', bgColor: '#ecf5ff' },
  { title: '运营中电站', value: '10', unit: '座', desc: '当前在线率 83.3%', icon: CircleCheck, color: '#67C23A', bgColor: '#f0f9eb' },
  { title: '总充电桩', value: '156', unit: '个', desc: '综合使用率 45.2%', icon: Connection, color: '#E6A23C', bgColor: '#fdf6ec' },
  { title: '今日总收益', value: '12,580.00', unit: '元', desc: '较昨日同时段 +12%', icon: Money, color: '#F56C6C', bgColor: '#fef0f0' }
]

// 丰富的搜索表单
const searchQuery = ref({ name: '', status: '', region: '', type: '' })

// 模拟表格数据 (增加评分和站点类型)
const tableData = ref([
  { id: 1, name: '南山区高新园超级超充站', region: '南山区', type: '公共超充', piles: '20/5', power: '2400', revenue: '3450.50', status: '营业中', rating: 4.8 },
  { id: 2, name: '福田区科创大厦充电站', region: '福田区', type: '公共快充', piles: '10/2', power: '1200', revenue: '1890.00', status: '营业中', rating: 4.5 },
  { id: 3, name: '宝安中心区地下场站', region: '宝安区', type: '商超配套', piles: '15/0', power: '1800', revenue: '2100.80', status: '营业中', rating: 4.6 },
  { id: 4, name: '龙华区壹方城示范站', region: '龙华区', type: '综合场站', piles: '30/10', power: '4200', revenue: '5600.20', status: '建设中', rating: 0 },
  { id: 5, name: '罗湖区国贸大厦超充站', region: '罗湖区', type: '写字楼配套', piles: '8/2', power: '960', revenue: '1200.00', status: '营业中', rating: 4.2 },
  { id: 6, name: '光明区高铁站枢纽站', region: '光明区', type: '交通枢纽', piles: '40/10', power: '6000', revenue: '0.00', status: '停业整顿', rating: 3.5 }
])
</script>

<template>
  <div class="page-container">
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6" v-for="(card, index) in statCards" :key="index">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-info">
              <div class="stat-title">{{ card.title }}</div>
              <div class="stat-value" :style="{ color: card.color }">
                <span v-if="card.unit === '元'" class="currency">￥</span>{{ card.value }} 
                <span class="unit" v-if="card.unit !== '元'">{{ card.unit }}</span>
              </div>
              <div class="stat-desc">{{ card.desc }}</div>
            </div>
            <div class="stat-icon-wrapper" :style="{ backgroundColor: card.bgColor, color: card.color }">
              <el-icon :size="24"><component :is="card.icon" /></el-icon>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="list-card">
      <template #header>
        <div class="card-header">
          <span class="header-title">充电站管理</span>
        </div>
      </template>

      <div class="action-bar">
        <div class="filter-group">
          <el-input v-model="searchQuery.name" placeholder="搜索电站名称..." :prefix-icon="Search" class="filter-item input-name" />
          <el-select v-model="searchQuery.region" placeholder="所在大区" class="filter-item">
            <el-option label="全部分区" value="" />
            <el-option label="南山区" value="南山区" />
            <el-option label="福田区" value="福田区" />
            <el-option label="宝安区" value="宝安区" />
          </el-select>
          <el-select v-model="searchQuery.type" placeholder="站点类型" class="filter-item">
            <el-option label="全部类型" value="" />
            <el-option label="公共超充" value="公共超充" />
            <el-option label="商超配套" value="商超配套" />
            <el-option label="交通枢纽" value="交通枢纽" />
          </el-select>
          <el-select v-model="searchQuery.status" placeholder="运营状态" class="filter-item">
            <el-option label="全部状态" value="" />
            <el-option label="营业中" value="营业中" />
            <el-option label="建设中" value="建设中" />
            <el-option label="停业" value="停业" />
          </el-select>
          <el-button type="primary" plain>查询</el-button>
          <el-button plain>重置</el-button>
        </div>
        <el-button type="primary" :icon="Plus">新增电站</el-button>
      </div>

      <el-table :data="tableData" stripe style="width: 100%" :header-cell-style="{ background: '#f5f7fa', color: '#606266' }">
        <el-table-column prop="name" label="电站名称" min-width="200">
          <template #default="scope">
            <div style="font-weight: 600; color: #303133;">{{ scope.row.name }}</div>
            <el-tag size="small" type="info" style="margin-top: 4px;">{{ scope.row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="region" label="所在地区" width="120" />
        <el-table-column prop="piles" label="快/慢充桩" width="100" />
        <el-table-column prop="rating" label="用户评分" width="160">
          <template #default="scope">
            <el-rate v-if="scope.row.rating > 0" v-model="scope.row.rating" disabled show-score text-color="#ff9900" score-template="{value}" />
            <span v-else style="color: #909399; font-size: 13px;">暂无评分</span>
          </template>
        </el-table-column>
        <el-table-column prop="power" label="总功率(kW)" width="100" align="right" />
        <el-table-column prop="revenue" label="今日收益(元)" width="140" align="right">
          <template #default="scope">
            <span style="font-weight: bold;" :style="{ color: scope.row.revenue !== '0.00' ? '#F56C6C' : '#606266' }">{{ scope.row.revenue }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.status === '营业中' ? 'success' : (scope.row.status === '建设中' ? 'warning' : 'danger')">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default>
            <el-button link type="primary" size="small">编辑</el-button>
            <el-button link type="success" size="small">配置电价</el-button>
            <el-button link type="info" size="small">查看电桩</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination background layout="total, sizes, prev, pager, next, jumper" :total="45" :page-size="10" />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.page-container { padding: 0; }
.stat-row { margin-bottom: 24px; }
.stat-card { border: none; border-radius: 8px; }
.stat-content { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; }
.stat-title { font-size: 14px; color: #909399; margin-bottom: 8px; }
.stat-value { font-size: 28px; font-weight: bold; font-family: 'DIN Alternate', sans-serif; margin-bottom: 4px; }
.currency { font-size: 18px; font-weight: normal; margin-right: 2px; }
.unit { font-size: 14px; color: #909399; font-weight: normal; margin-left: 4px; }
.stat-desc { font-size: 12px; color: #A8ABB2; }
.stat-icon-wrapper { width: 56px; height: 56px; border-radius: 50%; display: flex; justify-content: center; align-items: center; }

.list-card { border: none; border-radius: 8px; }
.card-header { display: flex; align-items: center; }
.header-title { font-size: 18px; font-weight: bold; color: #303133; }

.action-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.filter-group { display: flex; gap: 12px; flex-wrap: wrap; }
.filter-item { width: 140px; }
.input-name { width: 220px; }

.pagination-wrapper { margin-top: 20px; display: flex; justify-content: flex-end; }
</style>