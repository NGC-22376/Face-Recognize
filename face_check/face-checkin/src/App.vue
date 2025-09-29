<template>
  <div class="wrap">
    <h3>人脸签到/录入</h3>

    <!-- 实时摄像头 -->
    <video ref="video" width="640" height="480" autoplay muted></video>

    <!-- 两个按钮 -->
    <div style="margin-top:12px">
      <el-button type="primary" @click="handleCheckIn" :loading="loading">
        签到
      </el-button>
      <el-button type="warning" @click="handleRegister" :loading="loadingReg">
        人脸录入
      </el-button>
    </div>

    <!-- 结果提示 -->
    <el-alert v-if="result" :title="result" :type="alertType" style="margin-top:16px"/>
  </div>

  <!-- 录入对话框 -->
  <el-dialog v-model="showDlg" title="录入人脸" width="400px">
    <el-input v-model="username" placeholder="请输入姓名" />
    <template #footer>
      <el-button @click="showDlg=false">取消</el-button>
      <el-button type="primary" @click="doRegister" :loading="loadingReg">
        确定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

/* ---------- axios ---------- */
const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://localhost:8000',
  timeout: 10000
})
http.interceptors.response.use(
  res => res.data,
  err => { ElMessage.error(err.response?.data?.msg || '网络错误'); return Promise.reject(err) }
)

/* ---------- API 函数 ---------- */
function checkIn(imageBlob) {
  const fd = new FormData()
  fd.append('file', imageBlob, 'face.jpg')
  return http.post('/api/face/checkin', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
}
function registerFace(imageBlob, name) {
  const fd = new FormData()
  fd.append('file', imageBlob, 'face.jpg')
  fd.append('username', name)          // 额外字段
  return http.post('/api/face/register', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
}

/* ---------- 响应式变量 ---------- */
const video = ref(null)
const loading   = ref(false)   // 签到加载
const loadingReg= ref(false)   // 录入加载
const result    = ref('')      // 提示文本
const alertType = ref<'success'|'error'>('success')
const showDlg   = ref(false)   // 录入对话框
const username  = ref('')      // 对话框输入框

let stream = null              // 媒体流

/* ---------- 通用截图 ---------- */
async function capture() {
  if (!video.value) return null
  const canvas = document.createElement('canvas')
  canvas.width  = video.value.videoWidth
  canvas.height = video.value.videoHeight
  canvas.getContext('2d').drawImage(video.value, 0, 0)
  return new Promise(resolve => {
    canvas.toBlob(blob => resolve(blob), 'image/jpeg', 0.9)
  })
}

/* ---------- 签到 ---------- */
async function handleCheckIn() {
  loading.value = true
  const blob = await capture()
  if (!blob) {
    ElMessage.error('截图失败')
    loading.value = false
    return
  }
  try {
    const res = await checkIn(blob)
    if (res.ok) {
      result.value = `签到成功！欢迎 ${res.username}，时间 ${res.time}`
      alertType.value = 'success'
    } else {
      // 其他后端自定义错误
      result.value = res.msg
      alertType.value = 'error'
    }
  } finally {
    loading.value = false
  }
}

/* ---------- 录入 ---------- */
async function handleRegister() {
  const blob = await capture()
  if (!blob) { ElMessage.error('截图失败'); return }
  // 先弹框拿用户名
  username.value = ''
  showDlg.value  = true
}

async function doRegister() {
  if (!username.value.trim()) {
    ElMessage.warning('请输入姓名')
    return
  }
  loadingReg.value = true
  const blob = await capture()
  if (!blob) {
    loadingReg.value = false
    return
  }
  try {
    await registerFace(blob, username.value.trim())
    result.value = `人脸录入成功！姓名：${username.value}`
    alertType.value = 'success'
  } catch {
    return
  } finally {
    loadingReg.value = false
    showDlg.value = false
  }
}

/* ---------- 生命周期 ---------- */
async function openCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true })
    video.value.srcObject = stream
  } catch (e) { ElMessage.error('无法调用摄像头：' + e.message) }
}
onMounted(() => openCamera())
onBeforeUnmount(() => stream && stream.getTracks().forEach(t => t.stop()))
</script>

<style scoped>
.wrap { display:flex; flex-direction:column; align-items:center; margin-top:40px; }
video { border:1px solid #ccc; margin-bottom:12px; }
</style>