<template>
  <div class="index-manage">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span style="font-weight: 600;">索引状态</span>
          </template>
          <el-descriptions :column="1" border v-loading="loading">
            <el-descriptions-item label="向量引擎">
              <el-tag :type="stats.vector_store === 'milvus' ? 'success' : 'warning'" size="small">
                {{ stats.vector_store === 'milvus' ? 'Milvus（生产）' : '内存模式（演示）' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="文档总数">{{ stats.total_docs }}</el-descriptions-item>
            <el-descriptions-item label="向量 Chunk 数">{{ stats.total_chunks }}</el-descriptions-item>
            <el-descriptions-item label="索引路径">{{ stats.index_path }}</el-descriptions-item>
            <el-descriptions-item label="最后重建时间">{{ stats.last_rebuild || '从未重建' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <span style="font-weight: 600;">索引操作</span>
          </template>
          <div class="action-area">
            <el-alert
              title="重建索引会遍历所有文档，进行分块和向量化，耗时取决于文档数量。"
              type="info"
              :closable="false"
              style="margin-bottom: 16px;"
            />
            <el-button
              type="primary"
              size="large"
              :loading="rebuilding"
              @click="rebuild"
              style="width: 100%;"
            >
              <el-icon v-if="!rebuilding"><RefreshRight /></el-icon>
              {{ rebuilding ? '正在重建索引...' : '重建向量索引' }}
            </el-button>
            <div v-if="rebuildResult" class="rebuild-result">
              <el-result icon="success" title="索引重建完成">
                <template #extra>
                  <div class="result-stats">
                    <div><span>处理文档</span><strong>{{ rebuildResult.total_docs }}</strong></div>
                    <div><span>生成 Chunk</span><strong>{{ rebuildResult.total_chunks }}</strong></div>
                    <div><span>耗时</span><strong>{{ rebuildResult.elapsed_ms }} ms</strong></div>
                  </div>
                </template>
              </el-result>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span style="font-weight: 600;">分类分布</span>
      </template>
      <div v-if="categoryData.length" class="category-grid">
        <div v-for="item in categoryData" :key="item.name" class="category-card">
          <div class="category-name">{{ item.name }}</div>
          <div class="category-count">{{ item.count }}</div>
          <el-progress :percentage="item.percent" :stroke-width="8" :show-text="false" />
        </div>
      </div>
      <el-empty v-else description="暂无数据" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getStats, rebuildIndex } from '../api'

const loading = ref(false)
const rebuilding = ref(false)
const rebuildResult = ref(null)
const stats = ref({
  total_docs: 0,
  total_chunks: 0,
  categories: {},
  vector_store: '-',
  index_path: '-',
  last_rebuild: null
})

const categoryData = computed(() => {
  const entries = Object.entries(stats.value.categories || {})
  const max = Math.max(...entries.map(([, c]) => c), 1)
  return entries
    .map(([name, count]) => ({ name, count, percent: Math.round((count / max) * 100) }))
    .sort((a, b) => b.count - a.count)
})

const loadStats = async () => {
  loading.value = true
  try {
    const { data } = await getStats()
    stats.value = data
  } catch (e) {
    ElMessage.error('加载统计失败')
  } finally {
    loading.value = false
  }
}

const rebuild = async () => {
  rebuilding.value = true
  rebuildResult.value = null
  try {
    const { data } = await rebuildIndex()
    rebuildResult.value = data
    ElMessage.success('索引重建完成')
    loadStats()
  } catch (e) {
    ElMessage.error('索引重建失败：' + (e.response?.data?.detail || e.message))
  } finally {
    rebuilding.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.action-area { padding: 10px 0; }
.rebuild-result { margin-top: 20px; }
.result-stats {
  display: flex;
  gap: 40px;
  justify-content: center;
}
.result-stats div {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.result-stats span { font-size: 13px; color: #909399; }
.result-stats strong { font-size: 24px; color: #303133; }
.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}
.category-card {
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fafafa;
}
.category-name { font-size: 14px; color: #606266; margin-bottom: 8px; }
.category-count { font-size: 28px; font-weight: 700; color: #303133; margin-bottom: 8px; }
</style>
