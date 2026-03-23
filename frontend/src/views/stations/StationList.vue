<script setup>
import { ref, reactive } from 'vue'
import { Search, Plus, OfficeBuilding, CircleCheck, Location, Warning, DocumentAdd } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import http from '../../api/http'

// 顶部统计数据
const statCards = [
  { title: '我的电站总数', value: '6', unit: '座', desc: '含 1 座待审核', icon: OfficeBuilding, color: '#409EFF', bgColor: '#ecf5ff' },
  { title: '正式运营中', value: '4', unit: '座', desc: '当前在线率 92%', icon: CircleCheck, color: '#67C23A', bgColor: '#f0f9eb' },
  { title: '平台驳回整改', value: '1', unit: '座', desc: '请及时更新资料', icon: Warning, color: '#F56C6C', bgColor: '#fef0f0' }
]

const searchQuery = ref({ name: '', status: '' })

// 模拟表格数据 (包含各种审核状态)
const tableData = ref([
  { id: 1, name: '南山区高新园超级超充站', region: '南山区', piles: '20', power: '2400', revenue: '3450.50', status: '营业中' },
  { id: 2, name: '福田区科创大厦充电站', region: '福田区', piles: '10', power: '1200', revenue: '1890.00', status: '营业中' },
  { id: 3, name: '南山科技园地下二期扩建', region: '南山区', piles: '15', power: '1800', revenue: '0.00', status: '待审核', isNew: true },
  { id: 4, name: '罗湖区国贸大厦超充站', region: '罗湖区', piles: '8', power: '960', revenue: '1200.00', status: '营业中' },
  { id: 5, name: '福田高铁站临时配套站', region: '福田区', piles: '5', power: '600', revenue: '0.00', status: '已驳回', rejectReason: '现场实勘照片不清晰，无法确认消防设施位置，请重新拍摄上传。' }
])

// ================= 新增电站 (提交审核) 逻辑 =================
const applyDialogVisible = ref(false)
const isSubmitting = ref(false)
const formRef = ref(null)

const form = reactive({
  name: '',
  region: '南山区',
  address: '',
  piles: 10,
  power: 1200,
  lng: 113.943121,
  lat: 22.541243
})

const rules = {
  name: [{ required: true, message: '请输入电站名称', trigger: 'blur' }],
  address: [{ required: true, message: '请输入详细地址', trigger: 'blur' }]
}

const openApplyDialog = () => {
  applyDialogVisible.value = true
}

const submitApply = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      isSubmitting.value = true
      try {
        const res = await http.post('/operator/stations/apply', {
          name: form.name,
          lng: form.lng,
          lat: form.lat
        })
        
        if (res.data.code === 200) {
          ElMessage.success(res.data.message)
          applyDialogVisible.value = false
          
          // 前端直接伪造一条数据插入列表顶部，展现秒级响应体验
          tableData.value.unshift({
            id: res.data.station_id || 999,
            name: form.name,
            region: form.region,
            piles: form.piles,
            power: form.power,
            revenue: '0.00',
            status: '待审核',
            isNew: true
          })
          
          // 重置表单
          formRef.value.resetFields()
        }
      } catch (err) {
        ElMessage.error('提交失败，请检查网络')
      } finally {
        isSubmitting.value = false
      }
    }
  })
}
</script>

<template>
  <div class="page-container">
    <el-row :gutter="20" class="stat-row">
      <el-col :span="8" v-for="(card, index) in statCards" :key="index">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-info">
              <div class="stat-title">{{ card.title }}</div>
              <div class="stat-value" :style="{ color: card.color }">
                {{ card.value }} <span class="unit">{{ card.unit }}</span>
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
        <div class="flex justify-between items-center">
          <span class="header-title">我的电站资产</span>
          <el-button type="primary" :icon="Plus" @click="openApplyDialog">申请新建电站</el-button>
        </div>
      </template>

      <el-table :data="tableData" stripe style="width: 100%" :header-cell-style="{ background: '#f8fafc', color: '#475569' }">
        <el-table-column prop="name" label="电站名称" min-width="220">
          <template #default="scope">
            <div style="font-weight: 600; color: #1e293b; display: flex; align-items: center;">
              {{ scope.row.name }}
              <el-tag v-if="scope.row.isNew" type="danger" size="small" effect="dark" round style="margin-left: 8px;">新提报</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="region" label="所在地区" width="100" />
        <el-table-column prop="piles" label="终端数量" width="100" align="center" />
        <el-table-column prop="power" label="总功率" width="100" align="right">
          <template #default="scope">{{ scope.row.power }} kW</template>
        </el-table-column>
        <el-table-column prop="revenue" label="今日流水" width="120" align="right">
          <template #default="scope">
            <span style="font-weight: bold;" :style="{ color: scope.row.revenue !== '0.00' ? '#F56C6C' : '#94a3b8' }">￥{{ scope.row.revenue }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="运营状态" width="140" align="center">
          <template #default="scope">
            <el-tag v-if="scope.row.status === '营业中'" type="success" effect="plain"><el-icon><CircleCheck/></el-icon> 营业中</el-tag>
            <el-tag v-else-if="scope.row.status === '待审核'" type="warning" effect="dark">平台审核中</el-tag>
            <el-tooltip v-else-if="scope.row.status === '已驳回'" effect="dark" :content="scope.row.rejectReason" placement="top">
              <el-tag type="danger" effect="plain" style="cursor: help;"><el-icon><Warning/></el-icon> 已驳回 (查看原因)</el-tag>
            </el-tooltip>
          </template>
        </el-table-column>
        
        <el-table-column label="动作" width="180" fixed="right">
          <template #default="scope">
            <el-button v-if="scope.row.status === '营业中'" link type="primary" size="small">配置电价</el-button>
            <el-button v-if="scope.row.status === '已驳回'" link type="danger" size="small" @click="openApplyDialog">修改资料重提</el-button>
            <el-button link type="info" size="small">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="applyDialogVisible" title="提报新建电站申请" width="600px" destroy-on-close>
      <el-alert title="平台规范：电站信息提交后需经管理员进行合规审核，预计 1-2 个工作日。审核通过后方可正式上线并配置电价。" type="info" show-icon class="mb-6" :closable="false" />
      
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="电站名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：南山区XX地下停车场超充站" />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="所在行政区">
              <el-select v-model="form.region" placeholder="请选择">
                <el-option label="南山区" value="南山区" />
                <el-option label="福田区" value="福田区" />
                <el-option label="宝安区" value="宝安区" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="详细地址" prop="address">
              <el-input v-model="form.address" placeholder="输入街道与门牌号" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="地理坐标">
          <div class="map-picker-mock">
            <el-icon class="text-blue-500 mr-2" :size="20"><Location /></el-icon>
            <span>已选坐标：E {{ form.lng }}, N {{ form.lat }}</span>
            <el-button link type="primary" class="ml-auto">在地图上微调</el-button>
          </div>
        </el-form-item>

        <el-divider content-position="left">硬件规划</el-divider>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="规划枪数">
              <el-input-number v-model="form.piles" :min="1" :max="100" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="总功率(kW)">
              <el-input-number v-model="form.power" :min="30" :step="120" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="实勘照片">
           <div class="upload-mock-area">
             <el-icon :size="28" color="#94a3b8"><DocumentAdd /></el-icon>
             <span class="mt-2 text-xs text-gray-500">点击上传现场照片 (道闸、变压器铭牌等)</span>
           </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="applyDialogVisible = false">暂存草稿</el-button>
          <el-button type="primary" :loading="isSubmitting" @click="submitApply">
            确认并提交平台审核
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-container { padding: 0; }
.stat-row { margin-bottom: 24px; }
.stat-card { border: none; border-radius: 8px; }
.stat-content { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; }
.stat-title { font-size: 14px; color: #64748b; margin-bottom: 8px; }
.stat-value { font-size: 28px; font-weight: bold; font-family: 'DIN Alternate', sans-serif; margin-bottom: 4px; }
.unit { font-size: 14px; color: #94a3b8; font-weight: normal; margin-left: 4px; }
.stat-desc { font-size: 12px; color: #94a3b8; }
.stat-icon-wrapper { width: 56px; height: 56px; border-radius: 50%; display: flex; justify-content: center; align-items: center; }

.list-card { border: none; border-radius: 8px; }
.header-title { font-size: 18px; font-weight: bold; color: #1e293b; }

.flex { display: flex; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.mb-6 { margin-bottom: 24px; }
.mr-2 { margin-right: 8px; }
.ml-auto { margin-left: auto; }
.mt-2 { margin-top: 8px; }

.text-blue-500 { color: #3b82f6; }
.text-xs { font-size: 12px; }
.text-gray-500 { color: #64748b; }

.map-picker-mock {
  display: flex; align-items: center; background: #f1f5f9; padding: 10px 16px; border-radius: 6px; width: 100%; border: 1px solid #e2e8f0;
}
.upload-mock-area {
  width: 100%; height: 100px; border: 1px dashed #cbd5e1; border-radius: 6px; background: #f8fafc;
  display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: pointer; transition: all 0.3s;
}
.upload-mock-area:hover { border-color: #3b82f6; background: #eff6ff; }
</style>
