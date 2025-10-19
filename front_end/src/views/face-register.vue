<template>
  <div class="face-clock-container">
    <div class="header">
      <h3>{{ '用户注册-人脸录入' }}</h3>
      <el-button type="info" size="small" @click="$router.back()">返回</el-button>
    </div>

    <!-- 摄像头 -->
    <div class="camera-box">
      <video ref="video" width="600" height="450" autoplay muted></video>
    </div>

    <!-- 操作区 -->
    <div class="action-cards">

      <el-button
        type="warning"
        size="large"
        :loading="loadingEnroll"
        @click="doEnroll"
      >
        人脸录入
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
  name: 'FaceRegister',
  data() {
    return {
      type: this.$route.params.type,
      apiBaseUrl: 'http://localhost:5000',
      loading: false,
      loadingEnroll: false,
      result: '',
      alertType: 'success',
      stream: null
    }
  },
  mounted() {
    // 打印完整的路由参数，方便调试
    console.log('从注册页面传递的参数:', this.$route.query);
    
    // 检查是否从注册页面跳转而来
    if (this.$route.query.register === 'true') {
      console.log('检测到从注册页面跳转而来');
      
      // 显示注册成功后的提示信息
      this.result = '欢迎！请点击下方按钮进行人脸录入';
      this.alertType = 'success';
      
      // 可以从路由参数中获取用户信息（如果需要）
      if (this.$route.query.userInfo) {
        console.log('发现userInfo参数，尝试解析...');
        try {
          const userInfo = JSON.parse(this.$route.query.userInfo);
          console.log('从注册页面传递的用户信息:', userInfo);
        } catch (e) {
          console.error('解析用户信息失败:', e);
        }
      } else {
        console.log('未发现userInfo参数');
      }
    } else {
      console.log('不是从注册页面跳转而来');
    }
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

    /* 获取用户信息 - 从路由参数中获取 */
    getUserInfo() {
      // 从路由参数中获取用户信息
      if (this.$route.query.userInfo) {
        try {
          return JSON.parse(this.$route.query.userInfo);
        } catch (e) {
          console.error('解析路由参数中的用户信息失败:', e);
        }
      }
    },
    
    /* 当前用户ID */
    currentUserId() {
      const userInfo = this.getUserInfo();
      return userInfo ? userInfo.user_id : null;
    },

    /* 人脸录入 */
    async doEnroll() {
      const uid = this.currentUserId()
      if (!uid) {
        this.$message.error('未登录或用户信息缺失')
        return
      }
      this.loadingEnroll = true
      this.result = ''
      const blob = await this.capture()
      if (!blob) {
        this.loadingEnroll = false
        return
      }
      const fd = new FormData()
      fd.append('file', blob, 'face.jpg')
      fd.append('user_id', uid)

      try {
        const res = await fetch(`${this.apiBaseUrl}/face/enroll`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
          body: fd
        }).then(r => r.json())

        if (res.alreadyExists && res.ok) {
          this.result = '该人脸已录入过！'
          this.alertType = 'warning'
        } else if(!res.alreadyExists && res.ok){
          this.result = '人脸录入成功！即将跳转登录页面...'
          this.alertType = 'success'
          // 暂停1s
          await new Promise(resolve => setTimeout(resolve, 1000));
          // 跳转登录页面
          this.$router.push({
            path: '/',
          });
        }else{
          this.result = res.msg || '录入失败，请重试！'
          this.alertType = 'error'
        }
      } finally {
        this.loadingEnroll = false
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