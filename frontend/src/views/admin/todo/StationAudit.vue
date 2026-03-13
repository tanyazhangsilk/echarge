<script setup>
import { ref, computed, onMounted } from 'vue'
import { Stamp, Location, Picture, Check, Close, InfoFilled } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const tableData = ref([])
const loading = ref(true)

// 抽屉与审核逻辑状态
const drawerVisible = ref(false)
const currentStation = ref(null)
const isProcessing = ref(false)
const auditRemark = ref('')

const fetchAudits = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/v1/admin/audit/stations')
    if (res.data.code === 200) {
      tableData.value = res.data.data
    }
  } catch (error) {
    ElMessage.error('获取审核列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => { fetchAudits() })

const openAuditDrawer = (row) => {
  currentStation.value = row
  auditRemark.value = ''
  drawerVisible.value = true
}

const submitAudit = async (action) => {
  if (action === 'reject' && !auditRemark.value) {
    ElMessage.warning('驳回操作必须填写审核意见')
    return
  }

  const confirmText = action === 'approve' 
    ? `确认通过【${currentStation.value.station_name}】的上线申请吗？通过后该电站将立即在C端地图上可见。` 
    : `确认驳回该申请？`

  try {
    await ElMessageBox.confirm(confirmText, '高危操作确认', { type: action === 'approve' ? 'success' : 'warning' })
    
    isProcessing.value = true
    const res = await axios.post(`/api/v1/admin/audit/stations/${currentStation.value.id}/process`, {
      action: action,
      remark: auditRemark.value
    })
    
    if (res.data.code === 200) {
      ElMessage.success(action === 'approve' ? '审核已通过，电站正式上线！' : '已驳回，工单已打回给运营商')
      drawerVisible.value = false
      fetchAudits() // 刷新列表，被通过的将从该待办列表中消失
    }
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('处理失败')
  } finally {
    isProcessing.value = false
  }
}
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="border-0 rounded-lg">
      <template #header>
        <div class="font-bold text-lg text-gray-800 flex items-center">
          <el-icon class="mr-2 text-blue-500"><Stamp /></el-icon> 平台电站上线审核中心
        </div>
      </template>

      <el-alert 
        title="合规提醒：请严格核实运营商提交的电站经纬度与现场照片是否一致。一旦点击【审核通过】，该电站及下属电桩将立即对所有 C 端车主公开可见。" 
        type="info" 
        show-icon 
        class="mb-6" 
        :closable="false"
      />

      <el-table :data="tableData" v-loading="loading" stripe border style="width: 100%" :header-cell-style="{ background: '#f8f9fa', color: '#475569' }">
        <el-table-column prop="operator_name" label="归属运营商" min-width="160">
          <template #default="scope"><strong class="text-gray-700">{{ scope.row.operator_name }}</strong></template>
        </el-table-column>
        <el-table-column prop="station_name" label="申报电站名称" min-width="180" />
        <el-table-column prop="planned_piles" label="申报终端数" width="100" align="center">
          <template #default="scope">
            <el-tag type="info" size="small">{{ scope.row.planned_piles }} 个</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_power" label="总装机功率" width="120" align="right">
          <template #default="scope">{{ scope.row.total_power }} kW</template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交申请时间" width="170" />
        <el-table-column label="当前状态" width="100" align="center">
          <template #default="scope">
            <div class="status-indicator" :class="scope.row.status === 3 ? 'status-pending' : 'status-rejected'">
              {{ scope.row.status === 3 ? '待审核' : '已驳回' }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="动作" width="120" fixed="right" align="center">
          <template #default="scope">
            <el-button v-if="scope.row.status === 3" type="primary" size="small" @click="openAuditDrawer(scope.row)">
              调阅审核
            </el-button>
            <el-button v-else link type="info" size="small" @click="openAuditDrawer(scope.row)">查看驳回记录</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-drawer v-model="drawerVisible" title="电站准入合规审查" size="550px" destroy-on-close class="audit-drawer">
      <div v-if="currentStation" class="drawer-content">
        
        <div class="audit-header mb-6">
          <h2 class="text-xl font-bold text-gray-800 mb-2">{{ currentStation.station_name }}</h2>
          <el-tag type="warning" effect="dark">等待平台管理员审核</el-tag>
        </div>

        <el-divider content-position="left">基础档案核对</el-divider>
        <el-descriptions :column="1" border class="mb-6">
          <el-descriptions-item label="提报主体">{{ currentStation.operator_name }}</el-descriptions-item>
          <el-descriptions-item label="详细地址">{{ currentStation.address }}</el-descriptions-item>
          <el-descriptions-item label="装机规模">
            <strong class="text-blue-600">{{ currentStation.planned_piles }}</strong> 根充电枪 / <strong class="text-blue-600">{{ currentStation.total_power }}</strong> kW
          </el-descriptions-item>
          <el-descriptions-item label="GPS 坐标">
            <el-link type="primary" :underline="false">
              <el-icon><Location /></el-icon> {{ currentStation.lng }}, {{ currentStation.lat }}
            </el-link>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">现场实勘底稿</el-divider>
        <div class="photo-grid mb-6">
          <div class="mock-photo">
            <el-icon :size="24" class="mb-1"><Picture /></el-icon>
            <span>入口道闸/全景.jpg</span>
          </div>
          <div class="mock-photo">
            <el-icon :size="24" class="mb-1"><Picture /></el-icon>
            <span>高压变压器铭牌.jpg</span>
          </div>
          <div class="mock-photo">
            <el-icon :size="24" class="mb-1"><Picture /></el-icon>
            <span>消防器材配置.jpg</span>
          </div>
        </div>

        <div class="audit-action-zone" v-if="currentStation.status === 3">
          <div class="mb-2 flex items-center text-gray-700 font-bold">
            <el-icon class="mr-1"><InfoFilled /></el-icon> 审核处理意见
          </div>
          <el-input 
            v-model="auditRemark" 
            type="textarea" 
            :rows="3" 
            placeholder="若驳回，请务必填写需整改的原因（如：实勘照片不清晰，坐标偏差过大等）" 
            class="mb-4"
          />
          <div class="flex gap-4">
            <el-button type="danger" plain class="flex-1" :loading="isProcessing" @click="submitAudit('reject')" :icon="Close">
              打回整改
            </el-button>
            <el-button type="success" class="flex-1" :loading="isProcessing" @click="submitAudit('approve')" :icon="Check">
              各项合规，允许上线
            </el-button>
          </div>
        </div>
        
        <el-alert v-if="currentStation.status === 4" title="该电站申请已被平台驳回，正在等待运营商重新提交资料。" type="error" :closable="false" />
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.mb-6 { margin-bottom: 24px; }
.mb-4 { margin-bottom: 16px; }
.mb-2 { margin-bottom: 8px; }
.mb-1 { margin-bottom: 4px; }
.mr-2 { margin-right: 8px; }
.mr-1 { margin-right: 4px; }
.flex { display: flex; }
.items-center { align-items: center; }
.flex-1 { flex: 1; }
.gap-4 { gap: 16px; }

.text-gray-800 { color: #1e293b; }
.text-gray-700 { color: #334155; }
.text-xl { font-size: 20px; }
.font-bold { font-weight: bold; }
.text-blue-500 { color: #3b82f6; }
.text-blue-600 { color: #2563eb; }

/* 状态指示器 */
.status-indicator {
  display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;
}
.status-pending { background-color: #fff7ed; color: #ea580c; border: 1px solid #fed7aa; }
.status-rejected { background-color: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }

/* 抽屉内部样式 */
.drawer-content { padding: 0 8px; }
.audit-header { border-left: 4px solid #f59e0b; padding-left: 12px; }

.photo-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.mock-photo {
  background: #f1f5f9; border: 1px dashed #cbd5e1; border-radius: 6px; height: 100px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  font-size: 12px; color: #64748b; cursor: pointer; transition: all 0.3s;
}
.mock-photo:hover { border-color: #3b82f6; color: #3b82f6; background: #eff6ff; }

.audit-action-zone { background: #f8fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; }
</style>
