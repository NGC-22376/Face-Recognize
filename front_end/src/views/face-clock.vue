<template>
  <div class="face-clock-container">
    <div class="header">
      <h3>{{ title }}</h3>
      <el-button type="info" size="small" @click="$router.back()">返回</el-button>
    </div>

    <!-- 摄像头 -->
    <div class="camera-box">
      <video ref="video" width="600" height="450" autoplay muted></video>
    </div>

    <!-- 操作区 -->
    <div class="action-cards">
      <el-button
        type="primary"
        size="large"
        :loading="loading"
        @click="captureAndRecognize"
      >
        {{ type === 'clock_in' ? '上班打卡' : '下班打卡' }}
      </el-button>

    </div>

    <!-- 结果提示 -->
    <el-alert
      v-if="result"
      :title="result"
      :type="alertType"
      class="result-alert"
    />
  </div>
</template>

<script>
export default {
  name: 'FaceClock',
  data() {
    return {
      type: this.$route.params.type, // clock_in | clock_out
      apiBaseUrl: 'http://localhost:5000',
      loading: false,
      loadingEnroll: false,
      result: '',
      alertType: 'success',
      stream: null
    }
  },
  computed: {
    title() {
      return this.type === 'clock_in' ? '上班人脸识别' : '下班人脸识别'
    }
  },
  mounted() {
    this.openCamera()
  },
  beforeUnmount() {
    this.stopCamera()
  },
  methods: {
    /* 摄像头 */
    async openCamera() {
      try {
        this.stream = await navigator.mediaDevices.getUserMedia({ video: true })
        this.$refs.video.srcObject = this.stream
      } catch (e) {
        this.$message.error('无法调用摄像头：' + e.message)
      }
    },
    stopCamera() {
      if (this.stream) {
        this.stream.getTracks().forEach(t => t.stop())
        this.stream = null
      }
    },
    async capture() {
      const video = this.$refs.video
      if (!video) return null
      const canvas = document.createElement('canvas')
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      canvas.getContext('2d').drawImage(video, 0, 0)
      return new Promise(resolve =>
        canvas.toBlob(blob => resolve(blob), 'image/jpeg', 0.9)
      )
    },

    /* 当前用户 */
    currentUserId() {
      const ui = localStorage.getItem('user_info')
      return ui ? JSON.parse(ui).user_id : null
    },


    /* 人脸识别打卡 */
    async captureAndRecognize() {
      const uid = this.currentUserId()
      console.log(uid)
      if (!uid) {
        this.$message.error('未登录或用户信息缺失')
        return
      }
      this.loading = true
      this.result = ''
      const blob = await this.capture()
      if (!blob) {
        this.loading = false
        return
      }
      const fd = new FormData()
      fd.append('file', blob, 'face.jpg')
      fd.append('user_id', uid)

      try {
        const res = await fetch(`${this.apiBaseUrl}/face/${this.type === 'clock_in' ? 'checkin' : 'checkout'}`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
          body: fd
        }).then(r => r.json())

        if (res.ok) {
          this.result = `识别成功！欢迎 ${res.username}`
          this.alertType = 'success'
          // this.stopCamera()
          // this.$router.replace({ name: 'AdminPage', query: { recognized: '1', type: this.type } })
        } else {
          this.result = res.msg || '识别失败，请重试'
          this.alertType = 'error'
        }
      } catch (e) {
        this.result = '网络错误'
        this.alertType = 'error'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.face-clock-container {
  padding: 12px;
  background: #f5f6fa;
  min-height: 100vh;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.camera-box {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

video {
  border: 1px solid #e1e8ed;
  border-radius: 8px;
  background: #000;
}

.action-cards {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-bottom: 24px;
}

.result-alert {
  max-width: 600px;
  margin: 0 auto;
}
</style>