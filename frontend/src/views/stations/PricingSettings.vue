<script setup>
import { ref } from 'vue'
import { Edit, DocumentChecked, Location } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// 模拟模板列表
const templates = ref([
  { id: 1, name: '默认基础模板', stations: 5, updateTime: '2026-03-10' },
  { id: 2, name: '工业区峰谷特惠', stations: 2, updateTime: '2026-03-12' },
  { id: 3, name: '夜间物流车专享', stations: 0, updateTime: '2026-03-13' }
])
const activeTab = ref(1)

// 24小时可视化条数据生成
const timeBlocks = Array.from({ length: 24 }, (_, i) => {
  if (i < 8) return 'valley'
  if (i < 12) return 'peak'
  if (i < 18) return 'flat'
  if (i < 22) return 'peak'
  return 'valley'
})

const getBlockColor = (type) => {
  if (type === 'peak') return '#F56C6C' // 红色 (峰)
  if (type === 'flat') return '#409EFF' // 蓝色 (平)
  return '#67C23A' // 绿色 (谷)
}

// 选中模板的具体配置
const currentConfig = ref([
  { id: 1, timeRange: '08:00 - 12:00, 18:00 - 22:00', type: '峰时 (Peak)', eleFee: '1.25', serviceFee: '0.60' },
  { id: 2, timeRange: '12:00 - 18:00', type: '平时 (Flat)', eleFee: '0.85', serviceFee: '0.50' },
  { id: 3, timeRange: '00:00 - 08:00, 22:00 - 24:00', type: '谷时 (Valley)', eleFee: '0.35', serviceFee: '0.40' }
])

// --- 应用到电站功能逻辑 ---
const dialogVisible = ref(false)
const stationData = ref([
  { id: 101, name: '南山区高新园超级超充站', region: '南山区' },
  { id: 102, name: '福田区科创大厦充电站', region: '福田区' },
  { id: 103, name: '宝安中心区地下场站', region: '宝安区' },
  { id: 104, name: '龙华区壹方城示范站', region: '龙华区' },
  { id: 105, name: '罗湖区国贸大厦超充站', region: '罗湖区' }
])
const selectedStations = ref([])

const openStationDialog = (tpl) => {
  activeTab.value = tpl.id
  dialogVisible.value = true
}

const submitStationApply = () => {
  dialogVisible.value = false
  ElMessage.success(`成功将模板应用到 ${selectedStations.value.length} 个电站`)
}
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="top-card">
      <template #header>
        <div class="card-header-flex">
          <span class="header-title">计费模板库</span>
          <el-button type="primary" plain :icon="Edit">新建模板</el-button>
        </div>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="8" v-for="tpl in templates" :key="tpl.id">
          <div class="tpl-card" :class="{ 'active-tpl': activeTab === tpl.id }" @click="activeTab = tpl.id">
            <div class="tpl-top">
              <strong class="tpl-name">{{ tpl.name }}</strong>
              <el-tag size="small" type="info" class="station-tag" @click.stop="openStationDialog(tpl)">
                <el-icon><Location /></el-icon> 适用 {{ tpl.stations }} 站
              </el-tag>
            </div>
            <div class="tpl-time">最后更新: {{ tpl.updateTime }}</div>
            <div class="tpl-action">
              <el-button size="small" :type="activeTab === tpl.id ? 'primary' : 'default'">
                {{ activeTab === tpl.id ? '正在编辑' : '点击查看' }}
              </el-button>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never" class="bottom-card">
      <template #header>
        <div class="card-header-flex" style="justify-content: flex-start;">
          <el-icon class="title-icon"><DocumentChecked /></el-icon>
          <span class="header-title">规则编辑 ({{ templates.find(t => t.id === activeTab)?.name }})</span>
        </div>
      </template>

      <div class="visual-wrapper">
        <div class="time-labels">
          <span>00:00</span>
          <span>12:00</span>
          <span>24:00</span>
        </div>
        <div class="rainbow-bar">
          <el-tooltip v-for="(type, index) in timeBlocks" :key="index" :content="`${String(index).padStart(2,'0')}:00 - ${String(index+1).padStart(2,'0')}:00`" placement="top">
            <div class="color-block" :style="{ backgroundColor: getBlockColor(type) }"></div>
          </el-tooltip>
        </div>
        <div class="legend-group">
          <div class="legend-item"><div class="color-dot" style="background: #F56C6C;"></div>峰时 (电价最高)</div>
          <div class="legend-item"><div class="color-dot" style="background: #409EFF;"></div>平时 (标准电价)</div>
          <div class="legend-item"><div class="color-dot" style="background: #67C23A;"></div>谷时 (电价最低)</div>
        </div>
      </div>

      <el-table :data="currentConfig" border style="width: 100%" class="pricing-table">
        <el-table-column prop="type" label="时段类型" width="150" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.type.includes('Peak') ? 'danger' : (scope.row.type.includes('Flat') ? 'primary' : 'success')" effect="dark">
              {{ scope.row.type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="timeRange" label="生效时间范围" min-width="250" />
        <el-table-column label="基础电费 (元/度)" width="200">
          <template #default="scope">
            <el-input v-model="scope.row.eleFee"><template #prefix>￥</template></el-input>
          </template>
        </el-table-column>
        <el-table-column label="平台服务费 (元/度)" width="200">
          <template #default="scope">
            <el-input v-model="scope.row.serviceFee"><template #prefix>￥</template></el-input>
          </template>
        </el-table-column>
        <el-table-column label="用户总费用" width="150" align="center">
          <template #default="scope">
            <span class="total-fee">￥{{ (parseFloat(scope.row.eleFee) + parseFloat(scope.row.serviceFee)).toFixed(2) }}</span>
          </template>
        </el-table-column>
      </el-table>

      <el-alert title="修改模板后，已应用该模板的电站电价将立即同步更新，请谨慎操作。" type="warning" show-icon :closable="false" style="margin-bottom: 24px;" />

      <div class="submit-area">
        <el-button type="primary" size="large" style="width: 200px;">保存模板规则</el-button>
        <el-button size="large" @click="openStationDialog(templates.find(t => t.id === activeTab))">应用到指定电站</el-button>
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" title="将模板应用到指定电站" width="600px">
      <div style="margin-bottom: 16px; color: #606266;">
        当前选中模板：<strong style="color: #409EFF;">{{ templates.find(t => t.id === activeTab)?.name }}</strong>
      </div>
      <el-table :data="stationData" @selection-change="(val) => (selectedStations.value = val)" border height="300">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="电站名称" />
        <el-table-column prop="region" label="所在大区" width="120" />
      </el-table>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitStationApply" :disabled="selectedStations.length === 0">
            确认应用 (已选 {{ selectedStations.length }} 个)
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.top-card { margin-bottom: 24px; border: none; border-radius: 8px; }
.bottom-card { border: none; border-radius: 8px; }
.card-header-flex { display: flex; justify-content: space-between; align-items: center; }
.header-title { font-size: 18px; font-weight: bold; color: #303133; }
.title-icon { color: #409EFF; font-size: 20px; margin-right: 8px; }

.tpl-card { padding: 16px; border: 1px solid #dcdfe6; border-radius: 8px; cursor: pointer; transition: all 0.3s; background: #fafafa; }
.tpl-card:hover { border-color: #c0c4cc; }
.active-tpl { border-color: #409EFF; background: #ecf5ff; box-shadow: 0 2px 12px 0 rgba(64, 158, 255, 0.2); }
.tpl-top { display: flex; justify-content: space-between; margin-bottom: 12px; align-items: center; }
.tpl-name { font-size: 16px; color: #303133; }
.station-tag { cursor: pointer; transition: opacity 0.2s; }
.station-tag:hover { opacity: 0.8; }
.tpl-time { font-size: 12px; color: #A8ABB2; margin-bottom: 16px; }
.tpl-action { display: flex; justify-content: flex-end; }

/* 核心彩虹条 CSS */
.visual-wrapper { margin-bottom: 32px; background: #fafafa; padding: 20px; border-radius: 8px; border: 1px solid #ebeef5; }
.time-labels { display: flex; justify-content: space-between; font-size: 13px; color: #909399; margin-bottom: 8px; padding: 0 4px; }
.rainbow-bar { display: flex; height: 36px; border-radius: 6px; overflow: hidden; background: #ebeef5; box-shadow: inset 0 1px 3px rgba(0,0,0,0.1); }
.color-block { flex: 1; border-right: 1px solid rgba(255,255,255,0.4); cursor: pointer; transition: opacity 0.2s; }
.color-block:hover { opacity: 0.7; }
.legend-group { display: flex; justify-content: center; gap: 32px; margin-top: 16px; }
.legend-item { display: flex; align-items: center; font-size: 13px; color: #606266; }
.color-dot { width: 12px; height: 12px; border-radius: 3px; margin-right: 8px; }

.pricing-table { margin-bottom: 24px; }
.total-fee { font-size: 18px; font-weight: bold; color: #E6A23C; }
.submit-area { display: flex; justify-content: center; gap: 16px; margin-top: 24px; }
</style>
