<template>
  <div class="face-clock-container">
    <!-- 头部 -->
    <div class="header">
      <div class="header-content">
        <div class="title-section">
          <el-icon class="clock-icon"><Clock /></el-icon>
          <h2>{{ title }}</h2>
          <div class="time-display">{{ currentTime }}</div>
        </div>
        <el-button type="primary" size="medium" @click="router.back()" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>返回首页
        </el-button>
      </div>
    </div>

    <!-- 提示容器 -->
    <div class="alert-container" v-if="result">
      <el-alert
        :title="result"
        :type="alertType"
        :closable="true"
        @close="result = ''"
        show-icon
        class="custom-alert"
      />
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
              <el-icon v-if="type === 'clock_in'"><Upload /></el-icon>
              <el-icon v-else><Download /></el-icon>
            </div>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              @click="captureAndRecognize"
              class="action-btn"
            >
              <el-icon><Camera /></el-icon>
              {{ type === 'clock_in' ? '上班打卡' : '下班打卡' }}
            </el-button>
            <div class="action-desc">
              {{ type === 'clock_in' ? '开始一天的工作' : '结束一天的工作' }}
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 人脸确认弹窗 -->
    <el-dialog
      :title="`确认${type === 'clock_in' ? '上班' : '下班'}打卡`"
      v-model="confirmDialogVisible"
      width="500px"
      center
      :close-on-click-modal="false"
      @close="cancelCapture"
    >
      <div class="confirm-dialog-content">
        <div class="captured-image-container">
          <div class="circle-image-frame">
            <img :src="capturedImageUrl" alt="人脸照片" class="captured-image" />
          </div>
          <div class="image-tips">请确认是否是您本人</div>
        </div>
        <div class="dialog-actions">
          <el-button size="medium" @click="cancelCapture" class="cancel-btn">
            <el-icon><Close /></el-icon>取消
          </el-button>
          <el-button
            type="primary"
            size="medium"
            @click="confirmCapture"
            :loading="loading"
            class="confirm-btn"
          >
            <el-icon><Check /></el-icon>确认打卡
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Clock,
  ArrowLeft,
  InfoFilled,
  Upload,
  Download,
  Camera,
  Close,
  Check
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

// 响应式数据
const type = ref(route.params.type) // clock_in | clock_out
const apiBaseUrl = 'http://localhost:5000'
const loading = ref(false)
const result = ref('')
const alertType = ref('success')
const stream = ref(null)
const confirmDialogVisible = ref(false)
const capturedImageUrl = ref('')
const capturedBlob = ref(null)
const currentTime = ref('')
const video = ref(null)

let timeInterval = null

// 计算属性
const title = computed(() => {
  return type.value === 'clock_in' ? '上班人脸识别打卡' : '下班人脸识别打卡'
})

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

/* 当前用户 */
const currentUserId = () => {
  const ui = localStorage.getItem('user_info')
  return ui ? JSON.parse(ui).user_id : null
}

/* 人脸识别打卡 */
const captureAndRecognize = async () => {
  const uid = currentUserId()
  if (!uid) {
    ElMessage.error('未登录或用户信息缺失')
    return
  }

  loading.value = true
  const captureResult = await capture()
  if (!captureResult) {
    loading.value = false
    return
  }

  // 清理之前的 blob URL
  if (capturedImageUrl.value) {
    URL.revokeObjectURL(capturedImageUrl.value)
  }

  capturedBlob.value = captureResult.blob
  capturedImageUrl.value = captureResult.url
  confirmDialogVisible.value = true
  loading.value = false
}

/* 确认打卡 */
const confirmCapture = async () => {
  const uid = currentUserId()
  loading.value = true
  const fd = new FormData()
  fd.append('file', capturedBlob.value, 'face.jpg')
  fd.append('user_id', uid)
  try {
    const res = await fetch(`${apiBaseUrl}/face/${type.value === 'clock_in' ? 'checkin' : 'checkout'}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      body: fd
    }).then(r => r.json())
    if (res.ok) {
      // 先关闭弹窗
      confirmDialogVisible.value = false
      // 等待弹窗关闭后显示成功提示
      await nextTick()
      result.value = `识别成功！欢迎 ${res.username}，${type.value === 'clock_in' ? '上班' : '下班'}打卡成功！`
      alertType.value = 'success'
      confirmDialogVisible.value = false
      // 清理资源
      if (capturedImageUrl.value) {
        URL.revokeObjectURL(capturedImageUrl.value)
        capturedImageUrl.value = ''
        capturedBlob.value = null
      }
      // 3秒后自动清除结果
      setTimeout(() => {
        result.value = ''
      }, 3000)
    } else {
      result.value = res.msg || '识别失败，请重试'
      alertType.value = 'error'
      // 错误时不关闭弹窗，让用户重试或取消
    }
  } catch (e) {
    result.value = '网络错误，请检查连接'
    alertType.value = 'error'
  } finally {
    loading.value = false
  }
}

/* 取消打卡 */
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
.face-clock-container {
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

.clock-icon {
  font-size: 28px;
  color: #409EFF;
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

/* 提示容器 */
.alert-container {
  flex-shrink: 0;
  padding: 10px 24px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
  animation: fadeIn 0.3s ease-in-out;
}

.custom-alert {
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 主要内容区域 */
.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px 24px;
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
    #409EFF 50%,
    transparent 100%);
  animation: scan 2s linear infinite;
  box-shadow: 0 0 10px #409EFF;
}

@keyframes scan {
  0% { top: 0; }
  100% { top: 100%; }
}

.corner {
  position: absolute;
  width: 30px;
  height: 30px;
  border: 3px solid #409EFF;
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
  color: #409EFF;
  margin-bottom: 24px;
}

.action-btn {
  width: 200px;
  height: 50px;
  border-radius: 25px;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  box-shadow: 0 4px 15px rgba(64, 158, 255, 0.3);
}

.action-desc {
  color: #909399;
  font-size: 14px;
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
  border: 4px solid #409EFF;
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