<script setup>
import { ref, computed } from 'vue'
import { Lightning, Refresh, Select, CircleClose, SwitchButton, Tools } from '@element-plus/icons-vue'

// 统计数据
const overview = { total: 15, charging: 8, free: 5, fault: 2 }

// 生成假数据 (加入电桩类型)
const allPiles = Array.from({ length: 15 }, (_, i) => {
  const rand = Math.random()
  let status = 'free'
  if (rand < 0.6) status = 'charging'
  else if (rand > 0.85) status = 'fault'

  return {
    id: `DC-120KW-${String(i + 1).padStart(3, '0')}`,
    type: i % 3 === 0 ? '交流慢充' : '直流快充',
    status: status,
    power: status === 'charging' ? (Math.random() * 80 + 30).toFixed(1) : 0,
    progress: status === 'charging' ? Math.floor(Math.random() * 90 + 10) : 0,
    voltage: status === 'charging' ? (Math.random() * 50 + 350).toFixed(0) : 0,
    current: status === 'charging' ? (Math.random() * 100 + 50).toFixed(1) : 0,
    duration: status === 'charging' ? `0${Math.floor(Math.random()*3)}:${Math.floor(Math.random()*50+10)}:00` : '--'
  }
})

// 筛选表单
const searchForm = ref({ station: '南山区高新园站', group: '', status: 'all', pileType: '' })

// 分页逻辑
const currentPage = ref(1)
const pageSize = ref(6)
const displayPiles = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return allPiles.slice(start, start + pageSize.value)
})

const getStatusType = (status) => {
  if (status === 'charging') return 'primary'
  if (status === 'free') return 'success'
  return 'danger'
}
const getStatusText = (status) => {
  if (status === 'charging') return '充电中'
  if (status === 'free') return '空闲可用'
  return '设备故障'
}
</script>

<template>
  <div class="page-container">
    <el-row :gutter="20" class="status-row">
      <el-col :span="6">
        <el-card shadow="hover" class="overview-card" style="border-left: 4px solid #909399;">
          <div class="overview-title">总电桩数 (台)</div>
          <div class="overview-num" style="color: #606266;">{{ overview.total }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="overview-card" style="border-left: 4px solid #409EFF;">
          <div class="overview-title">正在充电</div>
          <div class="overview-num" style="color: #409EFF;">{{ overview.charging }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="overview-card" style="border-left: 4px solid #67C23A;">
          <div class="overview-title">空闲可用</div>
          <div class="overview-num" style="color: #67C23A;">{{ overview.free }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="overview-card" style="border-left: 4px solid #F56C6C;">
          <div class="overview-title">离线/故障</div>
          <div class="overview-num" style="color: #F56C6C;">{{ overview.fault }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="main-card">
      <template #header>
        <div class="card-header">
          <span class="header-title">电桩列表</span>
        </div>
      </template>

      <div class="filter-bar">
        <div class="filter-left">
          <el-select v-model="searchForm.station" placeholder="所属电站" style="width: 200px">
            <el-option label="南山区高新园站" value="南山区高新园站" />
          </el-select>
          <el-select v-model="searchForm.group" placeholder="分区" style="width: 120px">
            <el-option label="全部" value="" />
            <el-option label="A区快充" value="A" />
          </el-select>
          <el-select v-model="searchForm.pileType" placeholder="设备类型" style="width: 140px">
            <el-option label="全部类型" value="" />
            <el-option label="直流快充" value="DC" />
            <el-option label="交流慢充" value="AC" />
          </el-select>
          <el-radio-group v-model="searchForm.status">
            <el-radio-button label="all">全部状态</el-radio-button>
            <el-radio-button label="charging">充电中</el-radio-button>
            <el-radio-button label="free">空闲</el-radio-button>
            <el-radio-button label="fault">故障</el-radio-button>
          </el-radio-group>
        </div>
        <div class="filter-right">
          <el-button type="primary" :icon="Refresh" plain>刷新状态</el-button>
        </div>
      </div>

      <el-row :gutter="20">
        <el-col :span="8" v-for="pile in displayPiles" :key="pile.id" style="margin-bottom: 20px;">
          <el-card shadow="hover" class="pile-card" :style="{ borderTop: `4px solid ${pile.status==='charging'?'#409EFF':(pile.status==='free'?'#67C23A':'#F56C6C')}` }">
            <div class="pile-header">
              <span class="pile-id"><el-icon style="margin-right: 4px; color: #909399;"><Lightning /></el-icon>{{ pile.id }}</span>
              <el-tag :type="getStatusType(pile.status)" effect="light" round>{{ getStatusText(pile.status) }}</el-tag>
            </div>

            <div class="pile-body">
              <template v-if="pile.status === 'charging'">
                <div class="charging-info">
                  <span class="info-text">实时功率: <strong style="color: #409EFF; font-size: 18px;">{{ pile.power }} kW</strong></span>
                  <span class="info-text">已充时长: {{ pile.duration }}</span>
                </div>
                <el-progress :percentage="pile.progress" :stroke-width="12" striped striped-flow color="#409EFF" style="margin: 16px 0;" />
                <div class="charging-info">
                  <span class="info-text">电压: {{ pile.voltage }} V</span>
                  <span class="info-text">电流: {{ pile.current }} A</span>
                </div>
              </template>
              
              <template v-else-if="pile.status === 'free'">
                <div class="center-state" style="color: #67C23A;">
                  <el-icon :size="48" style="margin-bottom: 8px;"><Select /></el-icon>
                  <span>设备待机中，可扫码充电</span>
                </div>
              </template>
              
              <template v-else>
                <div class="center-state" style="color: #F56C6C;">
                  <el-icon :size="48" style="margin-bottom: 8px;"><CircleClose /></el-icon>
                  <span>通讯超时 / 设备离线</span>
                </div>
              </template>
            </div>

            <div class="pile-footer">
              <el-button size="small" type="danger" plain style="flex: 1;" :disabled="pile.status !== 'charging'" :icon="SwitchButton">远程停机</el-button>
              <el-button size="small" type="info" plain style="flex: 1;" :icon="Tools">重启设备</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <div class="pagination-wrapper">
        <el-pagination background layout="prev, pager, next" :total="allPiles.length" :page-size="pageSize" v-model:current-page="currentPage" />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.status-row { margin-bottom: 24px; }
.overview-card { border-radius: 8px; text-align: center; }
.overview-title { color: #909399; font-size: 14px; margin-bottom: 8px; }
.overview-num { font-size: 32px; font-weight: bold; font-family: 'DIN Alternate', sans-serif; }

.main-card { border: none; border-radius: 8px; }
.card-header { font-size: 18px; font-weight: bold; color: #303133; }

.filter-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; background: #f8f9fa; padding: 16px; border-radius: 8px; }
.filter-left { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }

.pile-card { border-radius: 8px; padding: 0; }
.pile-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.pile-id { font-weight: bold; font-size: 16px; color: #303133; display: flex; align-items: center; }

/* 重点：锁死高度，保持网格绝对整齐 */
.pile-body { 
  background-color: #f8f9fa; 
  border-radius: 8px; 
  padding: 16px; 
  height: 140px; /* 锁死高度 */
  display: flex; 
  flex-direction: column; 
  justify-content: center; 
  margin-bottom: 16px;
}
.charging-info { display: flex; justify-content: space-between; align-items: center; }
.info-text { font-size: 13px; color: #606266; }
.center-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; font-weight: 500; }

.pile-footer { display: flex; gap: 12px; border-top: 1px solid #ebeef5; padding-top: 16px; }
.pagination-wrapper { margin-top: 24px; display: flex; justify-content: center; }
</style>