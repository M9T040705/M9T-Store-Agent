<template>
  <div class="document-list">
    <el-card>
      <div class="toolbar">
        <el-input
          v-model="keyword"
          placeholder="搜索文档标题/文件名"
          clearable
          style="width: 240px;"
          @keyup.enter="loadDocuments"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="category" placeholder="全部分类" clearable style="width: 160px;" @change="loadDocuments">
          <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
        </el-select>
        <el-button type="primary" @click="showUpload = true">
          <el-icon><Upload /></el-icon> 上传文档
        </el-button>
        <el-button @click="loadDocuments">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>

      <el-table :data="documents" v-loading="loading" style="width: 100%;" stripe>
        <el-table-column prop="title" label="文档标题" min-width="200">
          <template #default="{ row }">
            <div style="font-weight: 500;">{{ row.title }}</div>
            <div style="font-size: 12px; color: #909399;">{{ row.filename }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.category }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chunk_count" label="Chunk 数" width="100" align="center" />
        <el-table-column prop="size" label="大小" width="100" align="center">
          <template #default="{ row }">{{ formatSize(row.size) }}</template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="170" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="editDocument(row)">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-button type="danger" link size="small" @click="removeDocument(row)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadDocuments"
          @current-change="loadDocuments"
        />
      </div>
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUpload" title="上传文档" width="500px">
      <el-form label-width="80px">
        <el-form-item label="选择文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".md,.txt,.pdf"
            :on-change="handleFileChange"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽文件到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 .md / .txt / .pdf 格式</div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="uploadForm.category" placeholder="自动识别" clearable style="width: 100%;">
            <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="uploadForm.title" placeholder="留空则自动提取" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUpload = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="confirmUpload">确认上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getDocuments, getCategories, uploadDocument, deleteDocument } from '../api'

const router = useRouter()
const documents = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const category = ref('')
const categories = ref([])
const loading = ref(false)
const showUpload = ref(false)
const uploading = ref(false)
const uploadRef = ref(null)
const uploadForm = ref({ category: '', title: '' })
const selectedFile = ref(null)

const loadDocuments = async () => {
  loading.value = true
  try {
    const { data } = await getDocuments({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value,
      category: category.value
    })
    documents.value = data.items
    total.value = data.total
  } catch (e) {
    ElMessage.error('加载文档列表失败')
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

const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

const confirmUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    if (uploadForm.value.category) formData.append('category', uploadForm.value.category)
    if (uploadForm.value.title) formData.append('title', uploadForm.value.title)
    await uploadDocument(formData)
    ElMessage.success('上传成功，建议重建索引')
    showUpload.value = false
    uploadRef.value?.clearFiles()
    selectedFile.value = null
    uploadForm.value = { category: '', title: '' }
    loadDocuments()
  } catch (e) {
    ElMessage.error('上传失败：' + (e.response?.data?.detail || e.message))
  } finally {
    uploading.value = false
  }
}

const editDocument = (row) => {
  router.push(`/documents/${row.doc_id}/edit`)
}

const removeDocument = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除文档「${row.title}」吗？删除后建议重建索引。`, '确认删除', {
      type: 'warning'
    })
    await deleteDocument(row.doc_id)
    ElMessage.success('删除成功')
    loadDocuments()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

onMounted(() => {
  loadDocuments()
  loadCategories()
})
</script>

<style scoped>
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; align-items: center; }
.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
