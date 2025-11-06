<template>
  <div class="face-register-container">
    <!-- 头部 -->
    <div class="header">
      <div class="header-content">
        <div class="title-section">
          <el-icon class="user-icon"><User /></el-icon>
          <h2>人脸录入</h2>
          <div class="time-display">{{ currentTime }}</div>
        </div>
        <el-button type="primary" size="medium" @click="$router.back()" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>返回首页
        </el-button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 摄像头区域 -->
      <div class="camera-section">
        <div class="camera-wrapper">
          <div class="camera-frame">
            <div class="circle-mask">
              <video ref="video" width="400" height="400" autoplay muted></video>
              <div class="face-overlay">
                <div class="scan-line"></div>
                <div class="corner top-left"></div>
                <div class="corner top-right"></div>
                <div class="corner bottom-left"></div>
                <div class="corner bottom-right"></div>
              </div>
            </div>
          </div>
          <div class="camera-tips">
            <el-icon><InfoFilled /></el-icon>
            请确保面部在圆形区域内，光线充足
          </div>
        </div>
      </div>

      <!-- 操作区域 -->
      <div class="action-section">
        <el-card class="action-card" shadow="hover">
          <div class="card-content">
            <div class="action-icon">
              <el-icon><UserFilled /></el-icon>
            </div>
            <el-button
              type="warning"
              size="large"
              :loading="loadingEnroll"
              @click="captureForEnroll"
              class="action-btn"
            >
              <el-icon><Camera /></el-icon>
              人脸录入
            </el-button>
            <div class="action-desc">
              请确保面部清晰可见，光线均匀
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 结果提示 -->
    <el-alert
      v-if="result"
      :title="result"
      :type="alertType"
      class="result-alert"
      :closable="false"
      show-icon
    />

    <!-- 人脸确认弹窗 -->
    <el-dialog
      title="确认人脸录入"
      v-model="confirmDialogVisible"
      width="500px"
      center
      :close-on-click-modal="false"
    >
      <div class="confirm-dialog-content">
        <div class="captured-image-container">
          <div class="circle-image-frame">
            <img :src="capturedImageUrl" alt="人脸照片" class="captured-image" />
          </div>
          <div class="image-tips">请确认照片是否清晰可用</div>
        </div>
        <div class="dialog-actions">
          <el-button size="medium" @click="cancelCapture" class="cancel-btn">
            <el-icon><Close /></el-icon>取消
          </el-button>
          <el-button
            type="warning"
            size="medium"
            @click="confirmEnroll"
            :loading="loadingEnroll"
            class="confirm-btn"
          >
            <el-icon><Check /></el-icon>确认录入
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  User,
  ArrowLeft,
  InfoFilled,
  UserFilled,
  Camera,
  Close,
  Check
} from '@element-plus/icons-vue'

// 响应式数据
const apiBaseUrl = 'http://localhost:5000'
const loadingEnroll = ref(false)
const result = ref('')
const alertType = ref('success')
const stream = ref(null)
const confirmDialogVisible = ref(false)
const capturedImageUrl = ref('')
const capturedBlob = ref(null)
const currentTime = ref('')
const video = ref(null)

let timeInterval = null

// 生命周期
onMounted(() => {
  openCamera()
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  stopCamera()
  if (timeInterval) {
    clearInterval(timeInterval)
  }
  // 清理 blob URL
  if (capturedImageUrl.value) {
    URL.revokeObjectURL(capturedImageUrl.value)
  }
})

// 方法
const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

/* 摄像头 */
const openCamera = async () => {
  try {
    stream.value = await navigator.mediaDevices.getUserMedia({
      video: {
        width: 400,
        height: 400,
        facingMode: 'user'
      }
    })
    if (video.value) {
      video.value.srcObject = stream.value
    }
  } catch (e) {
    ElMessage.error('无法调用摄像头：' + e.message)
  }
}

const stopCamera = () => {
  if (stream.value) {
    stream.value.getTracks().forEach(t => t.stop())
    stream.value = null
  }
}

const capture = async () => {
  if (!video.value) return null
  const canvas = document.createElement('canvas')
  canvas.width = 400
  canvas.height = 400
  const ctx = canvas.getContext('2d')

  // 创建圆形裁剪路径
  ctx.beginPath()
  ctx.arc(200, 200, 200, 0, Math.PI * 2)
  ctx.closePath()
  ctx.clip()

  ctx.drawImage(video.value, 0, 0, 400, 400)
  return new Promise(resolve => {
    canvas.toBlob(blob => {
      const url = URL.createObjectURL(blob)
      resolve({ blob, url })
    }, 'image/jpeg', 0.9)
  })
}

/* 当前用户ID */
const currentUserId = () => {
  // 直接从 localStorage 获取用户信息
  const ui = localStorage.getItem('user_info')
  if (ui) {
    try {
      const userInfo = JSON.parse(ui)
      return userInfo.user_id
    } catch (e) {
      console.error('解析用户信息失败:', e)
      return null
    }
  }
  return null
}

/* 人脸录入 - 拍照 */
const captureForEnroll = async () => {
  const uid = currentUserId()
  if (!uid) {
    ElMessage.error('未登录或用户信息缺失')
    return
  }

  loadingEnroll.value = true
  const captureResult = await capture()
  if (!captureResult) {
    loadingEnroll.value = false
    return
  }

  // 清理之前的 blob URL
  if (capturedImageUrl.value) {
    URL.revokeObjectURL(capturedImageUrl.value)
  }

  capturedBlob.value = captureResult.blob
  capturedImageUrl.value = captureResult.url
  confirmDialogVisible.value = true
  loadingEnroll.value = false
}

/* 确认录入 */
const confirmEnroll = async () => {
  const uid = currentUserId()
  if (!uid) {
    ElMessage.error('未登录或用户信息缺失')
    return
  }

  loadingEnroll.value = true

  const fd = new FormData()
  fd.append('file', capturedBlob.value, 'face.jpg')
  fd.append('user_id', uid)

  try {
    const res = await fetch(`${apiBaseUrl}/face/enroll`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      body: fd
    }).then(r => r.json())

    if (res.alreadyExists && res.ok) {
      result.value = '该人脸已录入过！'
      alertType.value = 'warning'
      confirmDialogVisible.value = false
    } else if(!res.alreadyExists && res.ok){
      result.value = '人脸录入成功！'
      alertType.value = 'success'
      confirmDialogVisible.value = false
    } else {
      result.value = res.msg || '录入失败，请重试！'
      alertType.value = 'error'
    }
  } catch (e) {
    result.value = '网络错误，请检查连接'
    alertType.value = 'error'
  } finally {
    loadingEnroll.value = false
  }
}

/* 取消录入 */
const cancelCapture = () => {
  confirmDialogVisible.value = false
  // 清理资源
  if (capturedImageUrl.value) {
    URL.revokeObjectURL(capturedImageUrl.value)
    capturedImageUrl.value = ''
  }
  capturedBlob.value = null
  result.value = ''
}
</script>

<style scoped>
.face-register-container {
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 头部样式 */
.header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
  padding: 16px 0;
  flex-shrink: 0;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-icon {
  font-size: 28px;
  color: #E6A23C;
}

.title-section h2 {
  margin: 0;
  color: #303133;
  font-weight: 600;
}

.time-display {
  color: #606266;
  font-size: 14px;
  background: #f5f7fa;
  padding: 4px 12px;
  border-radius: 16px;
  font-family: 'Courier New', monospace;
}

.back-btn {
  border-radius: 20px;
  padding: 10px 20px;
}

/* 主要内容区域 */
.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
  align-items: center;
  flex: 1;
  overflow: auto;
}

/* 摄像头区域 */
.camera-section {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.camera-wrapper {
  text-align: center;
}

.camera-frame {
  padding: 20px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.circle-mask {
  width: 400px;
  height: 400px;
  border-radius: 50%;
  overflow: hidden;
  position: relative;
  background: #000;
  box-shadow: 0 0 0 8px rgba(255, 255, 255, 0.1),
              inset 0 0 20px rgba(0, 0, 0, 0.5);
}

.circle-mask video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.face-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.scan-line {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg,
    transparent 0%,
    #E6A23C 50%,
    transparent 100%);
  animation: scan 2s linear infinite;
  box-shadow: 0 0 10px #E6A23C;
}

@keyframes scan {
  0% { top: 0; }
  100% { top: 100%; }
}

.corner {
  position: absolute;
  width: 30px;
  height: 30px;
  border: 3px solid #E6A23C;
}

.corner.top-left {
  top: 20px;
  left: 20px;
  border-right: none;
  border-bottom: none;
}

.corner.top-right {
  top: 20px;
  right: 20px;
  border-left: none;
  border-bottom: none;
}

.corner.bottom-left {
  bottom: 20px;
  left: 20px;
  border-right: none;
  border-top: none;
}

.corner.bottom-right {
  bottom: 20px;
  right: 20px;
  border-left: none;
  border-top: none;
}

.camera-tips {
  margin-top: 20px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

/* 操作区域 */
.action-section {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.action-card {
  border: none;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  min-width: 300px;
}

:deep(.action-card .el-card__body) {
  padding: 40px 30px;
}

.card-content {
  text-align: center;
}

.action-icon {
  font-size: 64px;
  color: #E6A23C;
  margin-bottom: 24px;
}

.action-btn {
  width: 200px;
  height: 50px;
  border-radius: 25px;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  box-shadow: 0 4px 15px rgba(230, 162, 60, 0.3);
}

.action-desc {
  color: #909399;
  font-size: 14px;
}

/* 结果提示 */
.result-alert {
  max-width: 600px;
  margin: 20px auto;
  border-radius: 12px;
  border: none;
}

/* 确认弹窗 */
.confirm-dialog-content {
  text-align: center;
  padding: 20px 0;
}

.captured-image-container {
  margin-bottom: 24px;
}

.circle-image-frame {
  width: 200px;
  height: 200px;
  border-radius: 50%;
  overflow: hidden;
  margin: 0 auto 16px;
  border: 4px solid #E6A23C;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.captured-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-tips {
  color: #606266;
  font-size: 14px;
}

.dialog-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.cancel-btn,
.confirm-btn {
  border-radius: 20px;
  padding: 10px 24px;
  min-width: 100px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main-content {
    grid-template-columns: 1fr;
    gap: 30px;
    padding: 20px 16px;
  }

  .circle-mask {
    width: 300px;
    height: 300px;
  }

  .header-content {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }

  .action-card {
    min-width: 250px;
  }
}
</style>