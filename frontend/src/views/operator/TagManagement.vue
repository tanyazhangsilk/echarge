<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import { createTag, fetchTags } from '../../api/operator'
import { mockTags } from '../../mock/backoffice'

const loading = ref(false)
const rows = ref([])
const dialogVisible = ref(false)
const form = reactive({ name: '', color: '#409EFF', description: '' })

const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchTags()
    rows.value = res.data.data || mockTags
  } catch (error) {
    rows.value = mockTags
  } finally {
    loading.value = false
  }
}

const save = async () => {
  try {
    await createTag({ ...form })
  } catch (error) {
    rows.value.unshift({ ...form, id: Date.now(), user_count: 0 })
  }
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
    <PageSectionHeader eyebrow="客户管理" title="标签管理" description="维护用户标签体系，用于分层、召回与活动投放。" chip="标签中心">
      <template #actions>
        <el-button type="primary" @click="dialogVisible = true">创建标签</el-button>
      </template>
    </PageSectionHeader>

    <section class="panel-grid">
      <article class="page-panel surface-card table-shell">
        <el-table :data="rows" v-loading="loading">
          <el-table-column prop="name" label="标签" min-width="160">
            <template #default="{ row }"><span class="micro-chip" :style="{ background: `${row.color}18`, color: row.color }">{{ row.name }}</span></template>
          </el-table-column>
          <el-table-column prop="description" label="说明" min-width="220" />
          <el-table-column prop="user_count" label="覆盖人数" width="100" />
        </el-table>
      </article>

      <article class="page-panel surface-card">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">使用建议</h3>
            <p class="panel-heading__desc">建议从行为、价值与召回三类标签开始维护。</p>
          </div>
        </div>
        <div class="info-list">
          <div class="info-item"><p class="info-item__title">行为类</p><p class="info-item__desc">例如高频充电、夜间活跃、工作日通勤。</p></div>
          <div class="info-item"><p class="info-item__title">价值类</p><p class="info-item__desc">例如高消费用户、潜力会员、重点车队成员。</p></div>
          <div class="info-item"><p class="info-item__title">召回类</p><p class="info-item__desc">用于优惠券投放、沉默用户唤醒和活动回流。</p></div>
        </div>
      </article>
    </section>

    <el-dialog v-model="dialogVisible" title="创建标签" width="480px">
      <el-form label-position="top">
        <el-form-item label="标签名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="标签颜色"><el-input v-model="form.color" /></el-form-item>
        <el-form-item label="说明"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
