<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createTag, fetchTags } from '../../api/operator'

const loading = ref(false)
const rows = ref([])
const dialogVisible = ref(false)
const form = reactive({ name: '', color: '#409EFF', description: '' })

const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchTags()
    rows.value = res.data.data || []
  } finally {
    loading.value = false
  }
}

const save = async () => {
  await createTag({ ...form })
  ElMessage.success('标签已创建')
  dialogVisible.value = false
  form.name = ''
  form.color = '#409EFF'
  form.description = ''
  loadData()
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell">
    <section class="page-hero surface-card">
      <div>
        <p class="page-hero__eyebrow">Tags</p>
        <h1 class="page-hero__title">标签管理</h1>
        <p class="page-hero__desc">将原占位页升级为可操作的用户标签池，用于活动圈人、召回策略和客户细分运营。</p>
      </div>
      <el-button type="primary" @click="dialogVisible = true">创建标签</el-button>
    </section>

    <section class="panel-grid">
      <article class="page-panel surface-card table-shell">
        <el-table :data="rows" v-loading="loading">
          <el-table-column prop="name" label="标签" min-width="160">
            <template #default="{ row }">
              <span class="micro-chip" :style="{ background: `${row.color}18`, color: row.color }">{{ row.name }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="说明" min-width="220" />
          <el-table-column prop="user_count" label="覆盖人数" width="100" />
        </el-table>
      </article>

      <article class="page-panel surface-card">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">使用建议</h3>
            <p class="panel-heading__desc">标签体系建议从高频行为、活跃时段、车队属性三条线持续维护。</p>
          </div>
        </div>
        <div class="info-list">
          <div class="info-item">
            <p class="info-item__title">行为类标签</p>
            <p class="info-item__desc">例如高频通勤、夜间充电、周末活跃。</p>
          </div>
          <div class="info-item">
            <p class="info-item__title">价值类标签</p>
            <p class="info-item__desc">例如高消费用户、可升级会员、企业贡献用户。</p>
          </div>
          <div class="info-item">
            <p class="info-item__title">召回类标签</p>
            <p class="info-item__desc">用于承接复购召回、优惠券回流和沉睡用户唤醒。</p>
          </div>
        </div>
      </article>
    </section>

    <el-dialog v-model="dialogVisible" title="创建标签" width="480px">
      <el-form label-position="top">
        <el-form-item label="标签名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="标签颜色">
          <el-input v-model="form.color" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
