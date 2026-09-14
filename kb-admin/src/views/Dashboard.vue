<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #409eff;">
            <el-icon :size="28"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_docs }}</div>
            <div class="stat-label">文档总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #67c23a;">
            <el-icon :size="28"><Collection /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_chunks }}</div>
            <div class="stat-label">向量 Chunk 数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #e6a23c;">
            <el-icon :size="28"><Menu /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ Object.keys(stats.categories).length }}</div>
            <div class="stat-label">文档分类数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #f56c6c;">
            <el-icon :size="28"><Cpu /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.vector_store }}</div>
            <div class="stat-label">向量引擎</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span style="font-weight: 600;">文档分类分布</span>
          </template>
          <div v-if="categoryData.length" class="category-list">
            <div v-for="item in categoryData" :key="item.name" class="category-item">
              <span class="category-name">{{ item.name }}</span>
              <el-progress :percentage="item.percent" :stroke-width="16" :show-text="false" />
              <span class="category-count">{{ item.count }}</span>
            </div>
          </div>
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span style="font-weight: 600;">系统信息</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="向量引擎">{{ stats.vector_store }}</el-descriptions-item>
            <el-descriptions-item label="索引路径">{{ stats.index_path }}</el-descriptions-item>
            <el-descriptions-item label="最后重建">{{ stats.last_rebuild || '未重建' }}</el-descriptions-item>
          </el-descriptions>
          <div style="margin-top: 16px;">
            <el-button type="primary" @click="$router.push('/index')">
              <el-icon><Refresh /></el-icon> 去重建索引
            </el-button>
            <el-button @click="$router.push('/documents')">
              <el-icon><Folder /></el-icon> 管理文档
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getStats } from '../api'

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

onMounted(async () => {
  try {
    const { data } = await getStats()
    stats.value = data
  } catch (e) {
    console.error('获取统计失败', e)
  }
})
</script>

<style scoped>
.stat-card { display: flex; align-items: center; gap: 16px; }
.stat-icon {
  width: 56px; height: 56px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
}
.stat-value { font-size: 28px; font-weight: 700; color: #303133; }
.stat-label { font-size: 13px; color: #909399; margin-top: 2px; }
.category-list { display: flex; flex-direction: column; gap: 12px; }
.category-item { display: flex; align-items: center; gap: 12px; }
.category-name { width: 100px; font-size: 13px; color: #606266; }
.category-count { width: 40px; text-align: right; font-size: 13px; color: #909399; }
</style>
