<template>
  <div class="login-container">
    <div class="form-box">
      <h2>{{ isLogin ? '用户登录' : '用户注册' }}</h2>
      <form @submit.prevent="isLogin ? handleLogin() : handleRegister()">
        <!-- 登录表单 -->
        <div v-if="isLogin">
          <input v-model="form.account" placeholder="账号" required />
          <input v-model="form.password" type="password" placeholder="密码" required />
        </div>

        <!-- 注册表单 -->
        <div v-else>
          <input v-model="registerForm.name" placeholder="姓名" required />
          <input v-model="registerForm.account" placeholder="工号（五位小写英文+三位数字）" required />
          <input v-model="registerForm.password" type="password" placeholder="密码（字母和数字组合，5-15个字符）" required
            @blur="validatePassword" />
          <div v-if="passwordError" class="error-message">{{ passwordError }}</div>

          <hr class="divider">

          <!-- 密保问题输入框 -->
          <p class="security-tip">请设置三个密保问题用于找回密码</p>
          <input v-model="registerForm.security_question_1" placeholder="密保问题1（3-20个字符）" required
            @blur="validateSecurityQuestions" />
          <input v-model="registerForm.security_answer_1" placeholder="密保答案1" required />
          <input v-model="registerForm.security_question_2" placeholder="密保问题2（3-20个字符）" required
            @blur="validateSecurityQuestions" />
          <input v-model="registerForm.security_answer_2" placeholder="密保答案2" required />
          <input v-model="registerForm.security_question_3" placeholder="密保问题3（3-20个字符）" required
            @blur="validateSecurityQuestions" />
          <input v-model="registerForm.security_answer_3" placeholder="密保答案3" required />
          <div v-if="securityQuestionError" class="error-message">{{ securityQuestionError }}</div>
        </div>

        <button type="submit" class="submit-button"
          :class="{ 'register-active': !isLogin && !passwordError && !securityQuestionError }"
          :disabled="!isLogin && (!!passwordError || !!securityQuestionError)">{{ isLogin ? '登录' : '注册' }}</button>
      </form>

      <div class="toggle-container">
        <span @click="toggleForm" class="toggle-link">
          {{ isLogin ? '没有账号？去注册' : '已有账号？去登录' }}
        </span>
        <span v-if="isLogin" @click="to_PwRec" class="toggle-link">
          找回密码
        </span>
      </div>
      <p v-if="message" class="message">{{ message }}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LoginPage',
  data() {
    return {
      isLogin: true,
      form: {
        account: '',
        password: ''
      },
      // 添加密保字段
      registerForm: {
        name: '',
        account: '',
        password: '',
        role: '员工',
        security_question_1: '',
        security_answer_1: '',
        security_question_2: '',
        security_answer_2: '',
        security_question_3: '',
        security_answer_3: ''
      },
      message: '',
      passwordError: '',
      securityQuestionError: '' // 密保问题错误信息
    }
  },
  methods: {
    toggleForm() {
      // 切换登录/注册视图
      this.isLogin = !this.isLogin;
      // 清空可能存在的错误信息和表单数据
      this.message = '';
      this.passwordError = '';
      Object.keys(this.form).forEach(key => this.form[key] = '');
      Object.keys(this.registerForm).forEach(key => this.registerForm[key] = '');
      this.registerForm.role = '员工'; // 重置role

      // 根据状态更新路由
      if (this.isLogin) {
        this.$router.push({ name: 'LoginPage' }).catch(() => { });
      } else {
        this.$router.push({ name: 'RegisterPage' }).catch(() => { });
      }
    },
    to_PwRec() {
      this.$router.push('/password-recovery');
    },
    validatePassword() {
      const password = this.registerForm.password;
      if (!password) {
        this.passwordError = '';
        return;
      }

      // 检查长度是否在5-15个字符之间
      if (password.length < 5 || password.length > 15) {
        this.passwordError = '密码长度必须在5-15个字符之间';
        return;
      }

      // 检查是否同时包含字母和数字
      const hasLetter = /[a-zA-Z]/.test(password);
      const hasNumber = /\d/.test(password);

      if (!hasLetter || !hasNumber) {
        this.passwordError = '密码必须同时包含字母和数字';
        return;
      }

      this.passwordError = '';
    },
    // 密保问题验证方法
    validateSecurityQuestions() {
      const questions = [
        this.registerForm.security_question_1,
        this.registerForm.security_question_2,
        this.registerForm.security_question_3
      ];

      // 检查每个问题的长度是否在3-20个字符之间
      for (let i = 0; i < questions.length; i++) {
        const question = questions[i];
        if (question && (question.length < 3 || question.length > 20)) {
          this.securityQuestionError = `密保问题${i + 1}的长度必须在3-20个字符之间`;
          return;
        }
      }

      // 检查问题是否重复
      const uniqueQuestions = new Set(questions.filter(q => q.trim() !== ''));
      if (uniqueQuestions.size !== questions.filter(q => q.trim() !== '').length) {
        this.securityQuestionError = '密保问题不允许重复';
        return;
      }

      this.securityQuestionError = '';
    },
    async handleLogin() {
      try {
        const res = await fetch('http://localhost:5000/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.form)
        });
        const data = await res.json();
        if (res.ok) {
          this.message = '登录成功';
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('user_info', JSON.stringify(data.user));
          if (data.user.role === '管理员') {
            this.$router.push('/admin');
          } else {
            this.$router.push('/admin');
          }
        } else {
          this.message = data.message || '登录失败';
        }
      } catch (err) {
        this.message = '网络错误';
      }
    },
    async handleRegister() {
      // 在提交前再次验证密码和密保问题
      this.validatePassword();
      this.validateSecurityQuestions();

      if (this.passwordError || this.securityQuestionError) {
        this.message = '请修正错误后再提交';
        return;
      }

      try {
        const res = await fetch('http://localhost:5000/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.registerForm)
        });
        const data = await res.json();
        if (res.ok) {
          this.message = '注册成功，请登录';
          // 清空注册表单
          this.registerForm = {
            name: '',
            account: '',
            password: '',
            role: '员工'
          };
          this.isLogin = true;
        } else {
          this.message = data.message || '注册失败';
        }
      } catch (err) {
        this.message = '网络错误';
      }
    }
  },
  mounted() {
    this.isLogin = this.$route.name !== 'RegisterPage';
  },
  watch: {
    '$route'(to) {
      this.isLogin = to.name !== 'RegisterPage';
      this.message = '';
    },
    'registerForm.password'() {
      // 当密码变化时清除错误信息
      if (this.passwordError) {
        this.passwordError = '';
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
  height: 100vh;
  background: #f5f6fa;
}

.form-box {
  background: #fff;
  padding: 32px 40px;
  border-radius: 8px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.08);
  min-width: 320px;
  max-height: 90vh;
  overflow-y: auto;
}

.form-box h2 {
  text-align: center;
  margin-bottom: 24px;
}

.form-box input {
  width: 100%;
  padding: 10px;
  margin-bottom: 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}

.form-box button {
  padding: 10px;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  width: 100%;
  background-color: #1890ff;
  color: white;
}

.form-box button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.toggle-container {
  display: flex;
  width: 100%;
  margin-top: 10px;
  gap: 10px;
}

.toggle-link {
  flex: 1;
  padding: 10px 15px;
  box-sizing: border-box;
  text-align: center;
  background: #f0f0f0;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.toggle-link:hover {
  background: #e0e0e0;
}

.message {
  margin-top: 16px;
  text-align: center;
  color: #f56565;
  font-size: 14px;
}

.error-message {
  color: #ff4d4f;
  font-size: 14px;
  margin-top: 5px;
  margin-bottom: 10px;
}

.security-tip {
  font-size: 14px;
  color: #666;
  margin-bottom: 10px;
}

.divider {
  margin: 20px 0;
  border: 0;
  border-top: 1px solid #eee;
}

.security-tip {
  text-align: center;
  color: #666;
  margin: 16px 0;
  font-size: 14px;
}
</style>