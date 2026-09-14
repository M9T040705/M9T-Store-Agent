import axios from 'axios'

const api = axios.create({
  baseURL: '/api/kb',
  timeout: 60000
})

// 文档列表
export function getDocuments(params) {
  return api.get('/documents', { params })
}

// 文档详情
export function getDocument(docId) {
  return api.get(`/documents/${docId}`)
}

// 上传文档
export function uploadDocument(formData) {
  return api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 更新文档
export function updateDocument(docId, data) {
  return api.put(`/documents/${docId}`, data)
}

// 删除文档
export function deleteDocument(docId) {
  return api.delete(`/documents/${docId}`)
}

// 重建索引
export function rebuildIndex() {
  return api.post('/rebuild')
}

// 统计信息
export function getStats() {
  return api.get('/stats')
}

// 分类列表
export function getCategories() {
  return api.get('/categories')
}

export default api
