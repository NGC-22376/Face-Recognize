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
          <input v-model="registerForm.password" type="password" placeholder="密码" required />
          
          <hr class="divider">
          
          <!-- 密保问题输入框 -->
          <p class="security-tip">请设置三个密保问题用于找回密码</p>
          <input v-model="registerForm.security_question_1" placeholder="密保问题1" required />
          <input v-model="registerForm.security_answer_1" placeholder="密保答案1" required />
          <input v-model="registerForm.security_question_2" placeholder="密保问题2" required />
          <input v-model="registerForm.security_answer_2" placeholder="密保答案2" required />
          <input v-model="registerForm.security_question_3" placeholder="密保问题3" required />
          <input v-model="registerForm.security_answer_3" placeholder="密保答案3" required />
        </div>

        <button type="submit" class="submit-button">{{ isLogin ? '登录' : '注册' }}</button>
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
      message: ''
    }
  },
  methods: {
    toggleForm() {
      // 切换登录/注册视图
      this.isLogin = !this.isLogin;
      // 清空可能存在的错误信息和表单数据
      this.message = '';
      Object.keys(this.form).forEach(key => this.form[key] = '');
      Object.keys(this.registerForm).forEach(key => this.registerForm[key] = '');
      this.registerForm.role = '员工'; // 重置role

      // 根据状态更新路由
      if (this.isLogin) {
          this.$router.push({ name: 'LoginPage' }).catch(()=>{});
      } else {
          this.$router.push({ name: 'RegisterPage' }).catch(()=>{});
      }
    },
    to_PwRec() {
      this.$router.push('/password-recovery');
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
      try {
        const res = await fetch('http://localhost:5000/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.registerForm)
        });
        const data = await res.json();
        if (res.ok) {
          this.message = '注册成功，下一步将跳转录入人脸信息...';
          await new Promise(resolve => setTimeout(resolve, 500));
          console.log("注册返回的用户信息:", JSON.stringify(data.user));
          this.$router.push({
            path: '/face-register',
            query: {
              userInfo: JSON.stringify(data.user),
              register: 'true'
            }
          });
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
  box-shadow: 0 2px 16px rgba(0,0,0,0.08);
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
  background-color: #f0f2f5;
  color: #555;
  border: 1px solid #dcdfe6; 
  border-radius: 5px; 
  text-align: center; 
  cursor: pointer; 
  transition: all 0.3s ease;
}
.toggle-link:hover {
  background-color: #e4e7ed;
  border-color: #c0c4cc;
}
.form-box .submit-button {
  width: 100%;
  padding: 10px 15px; 
  box-sizing: border-box; 
  background: #3498db;
  color: #fff;
}
.form-box .submit-button:hover {
  background: #2980b9;
}
.message {
  text-align: center;
  color: #e74c3c;
  margin-top: 10px;
}
/* 新增样式 */
.divider {
  border: none;
  border-top: 1px solid #eee;
  margin: 20px 0;
}
.security-tip {
  font-size: 14px;
  color: #888;
  margin-bottom: 12px;
  text-align: center;
}
</style>
