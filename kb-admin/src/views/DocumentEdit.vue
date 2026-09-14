<template>
  <div class="document-edit">
    <el-card v-loading="loading">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: 600; font-size: 16px;">编辑文档</span>
          <el-button @click="$router.back()">
            <el-icon><Back /></el-icon> 返回列表
          </el-button>
        </div>
      </template>

      <el-form label-width="100px" style="max-width: 900px;">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="文档标题">
              <el-input v-model="form.title" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="文档分类">
              <el-select v-model="form.category" style="width: 100%;">
                <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="文档ID">
          <el-input v-model="form.doc_id" disabled />
        </el-form-item>

        <el-form-item label="文档内容">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="20"
            placeholder="支持 Markdown 格式..."
            style="font-family: monospace; font-size: 13px;"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="saveDocument">
            <el-icon><Check /></el-icon> 保存修改
          </el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>

      <el-divider />

      <div style="max-width: 900px;">
        <div style="font-weight: 600; margin-bottom: 12px;">文档元信息</div>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="文件名">{{ form.filename }}</el-descriptions-item>
          <el-descriptions-item label="文件大小">{{ formatSize(form.size) }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ form.created_at }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ form.updated_at }}</el-descriptions-item>
          <el-descriptions-item label="Chunk 数">{{ form.chunk_count }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getDocument, updateDocument, getCategories } from '../api'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const categories = ref([])
const form = ref({
  doc_id: '',
  title: '',
  category: '',
  content: '',
  filename: '',
  size: 0,
  created_at: '',
  updated_at: '',
  chunk_count: 0
})

const loadDocument = async () => {
  loading.value = true
  try {
    const { data } = await getDocument(route.params.docId)
    form.value = { ...form.value, ...data }
  } catch (e) {
    ElMessage.error('加载文档失败')
    router.back()
  } finally {
    loading.value = false
  }
}

const loadCategories = async () => {
  try {
    const { data } = await getCategories()
    categories.value = data.categories
  } catch (e) {
    console.error('加载分类失败', e)
  }
}

const saveDocument = async () => {
  saving.value = true
  try {
    await updateDocument(route.params.docId, {
      title: form.value.title,
      category: form.value.category,
      content: form.value.content
    })
    ElMessage.success('保存成功，建议重建索引')
  } catch (e) {
    ElMessage.error('保存失败：' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

const formatSize = (bytes) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

onMounted(() => {
  loadDocument()
  loadCategories()
})
</script>

<style scoped>
.document-edit { max-width: 1000px; }
</style>
