<template>
  <div class="login-container">
    <div class="form-box">
      <!-- 动态标题 -->
      <h2>{{ title }}</h2>

      <!-- 步骤容器滑动部分 -->
      <div class="steps-wrapper" :style="wrapperStyle">
        <!-- 步骤一：输入账号 -->
        <div class="step">
          <form @submit.prevent="handleStep1">
            <input v-model="account" placeholder="请输入您的账号" required />
            <button type="submit" class="submit-button">下一步</button>
          </form>
        </div>

        <!-- 步骤二：回答密保问题 -->
        <div class="step">
          <form @submit.prevent="handleStep2">
            <div class="question-display">{{ securityQuestion.text }}</div>
            <input v-model="securityAnswer" placeholder="请输入答案" required />
            <div class="button-group">
              <button type="button" class="back-button" @click="goBack">返回</button>
              <button type="submit" class="submit-button">验证</button>
            </div>
          </form>
        </div>

        <!-- 步骤三：重置密码 -->
        <div class="step">
          <form @submit.prevent="handleStep3">
            <input v-model="newPassword" type="password" placeholder="请输入新密码" required />
            <input v-model="confirmPassword" type="password" placeholder="请再次输入新密码" required />
            <div class="button-group">
                <button type="button" class="back-button" @click="goBack">返回</button>
                <button type="submit" class="submit-button">重置密码</button>
            </div>
          </form>
        </div>
      </div>

      <!-- 统一的错误信息提示 -->
      <p v-if="errorMessage" class="message">{{ errorMessage }}</p>
      <!-- 添加一个占位符，防止在没有错误消息时布局跳动 -->
      <p v-else class="message">&nbsp;</p>
    </div>
  </div>
</template>


<script>
import axios from 'axios';

export default {
  name: 'PasswordRecovery',
  data() {
    return {
      currentStep: 1, // 1: 输入账号, 2: 回答密保, 3: 重置密码
      account: '',
      
      // 用于步骤2
      securityQuestion: {
        id: null,
        text: ''
      },
      securityAnswer: '',

      // 用于步骤3
      newPassword: '',
      confirmPassword: '',
      resetToken: '', // 保存从步骤2获取的临时token

      errorMessage: '',
      isLoading: false // 用于防止重复提交
    };
  },
  computed: {
    title() {
      switch (this.currentStep) {
        case 1: return '找回密码';
        case 2: return '安全验证';
        case 3: return '重置密码';
        default: return '找回密码';
      }
    },
    wrapperStyle() {
      const totalSteps = 3;
      const percentage = (this.currentStep - 1) * (100 / totalSteps);
      return {
        transform: `translateX(-${percentage}%)`
      };
    }
  },
  methods: {
    // 步骤一：提交账号，获取密保问题
    async handleStep1() {
      this.errorMessage = '';
      if (!this.account) {
        this.errorMessage = '账号不能为空！';
        return;
      }
      if (this.isLoading) return;
      this.isLoading = true;

      try {
        const response = await axios.post('/api/password-recovery/get-questions', {
          account: this.account
        });
        
        // 保存获取到的问题
        this.securityQuestion = response.data.question;
        this.currentStep = 2; // 切换到下一步

      } catch (error) {
        this.errorMessage = error.response?.data?.message || '获取密保问题失败，请检查账号或网络。';
      } finally {
        this.isLoading = false;
      }
    },

    // 步骤二：提交密保答案，获取重置密码的临时token
    async handleStep2() {
      this.errorMessage = '';
      if (!this.securityAnswer) {
        this.errorMessage = '密保答案不能为空！';
        return;
      }
      if (this.isLoading) return;
      this.isLoading = true;

      try {
        const response = await axios.post('/api/password-recovery/verify-answer', {
          account: this.account,
          question_id: this.securityQuestion.id,
          answer: this.securityAnswer
        });

        // 保存用于重置密码的临时token
        this.resetToken = response.data.reset_token;
        this.currentStep = 3; // 切换到重置密码步骤

      } catch (error) {
        this.errorMessage = error.response?.data?.message || '验证失败，请重试。';
      } finally {
        this.isLoading = false;
      }
    },

    // 步骤三：提交新密码和临时token
    async handleStep3() {
      this.errorMessage = '';
      if (!this.newPassword || !this.confirmPassword) {
        this.errorMessage = '密码不能为空！'; return;
      }
      if (this.newPassword.length < 6) {
        this.errorMessage = '新密码长度不能少于6位'; return;
      }
      if (this.newPassword !== this.confirmPassword) {
        this.errorMessage = '两次输入的密码不一致！'; return;
      }
      if (this.isLoading) return;
      this.isLoading = true;

      try {
        await axios.post('/api/password-recovery/reset-password', {
          new_password: this.newPassword
        }, {
          headers: {
            // 将临时token放在请求头中
            'Authorization': `Bearer ${this.resetToken}`
          }
        });

        alert('密码重置成功！即将跳转到登录页面。');
        this.$router.push('/');

      } catch (error) {
        this.errorMessage = error.response?.data?.message || '密码重置失败，可能验证已过期，请重试。';
      } finally {
        this.isLoading = false;
      }
    },

    // 返回上一步
    goBack() {
      if (this.isLoading) return;
      if (this.currentStep > 1) {
        this.currentStep--;
        this.errorMessage = '';
        // 清理当前步骤的数据
        if (this.currentStep === 1) {
          this.securityAnswer = '';
        }
        if (this.currentStep === 2) {
          this.newPassword = '';
          this.confirmPassword = '';
          this.resetToken = '';
        }
      } else {
        // 在第一步点击返回，则回到登录页
        this.$router.push('/login');
      }
    }
  }
}
</script>


<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f6fa;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.form-box {
  width: 400px; 
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.08);
  overflow: hidden; 
  padding: 32px 0;
}

.form-box h2 {
  text-align: center;
  margin-top: 0;
  margin-bottom: 24px;
  padding: 0 40px; 
  color: #333;
  font-weight: 600;
}


.steps-wrapper {
  display: flex;
  width: 300%;
  transition: transform 0.4s cubic-bezier(0.68, -0.55, 0.27, 1.55);
}

.step {
  width: 33.3333%; 
  box-sizing: border-box; 
  padding: 0 40px;
  flex-shrink: 0; 
}

.step input {
  width: 100%;
  padding: 12px;
  margin-bottom: 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
  font-size: 16px;
  transition: all 0.2s ease;
}

.step input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.2);
}

/* 用于展示密保问题的样式 */
.question-display {
  padding: 12px 15px;
  margin-bottom: 16px;
  background-color: #f0f2f5;
  border-radius: 4px;
  color: #555;
  text-align: center;
  font-size: 15px;
  word-wrap: break-word;
}

/* 按钮基础样式 */
.step button {
  padding: 12px;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
  width: 100%;
}

/* 主操作按钮 */
.submit-button {
  background: #3498db;
  color: #fff;
}
.submit-button:hover {
  background: #2980b9;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(52, 152, 219, 0.2);
}

/* 返回按钮 */
.back-button {
  background: #f0f2f5;
  color: #555;
}
.back-button:hover {
  background: #e4e7ed;
}

/* 按钮组 */
.button-group {
  display: flex;
  gap: 10px;
}
.button-group .submit-button { flex: 2; }
.button-group .back-button { flex: 1; }

/* 错误信息样式 */
.message {
  text-align: center;
  color: #e74c3c;
  margin-top: 16px;
  padding: 0 40px;
  font-size: 14px;
  min-height: 20px;
  line-height: 20px;
}
</style>
