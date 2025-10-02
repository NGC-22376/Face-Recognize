<template>
  <div class="login-container">
    <div class="form-box">
      <h2>{{ isLogin ? '用户登录' : '用户注册' }}</h2>
      <form @submit.prevent="isLogin ? handleLogin() : handleRegister()">
        <div v-if="!isLogin">
          <input v-model="registerForm.name" placeholder="姓名" required />
        </div>
        <div v-if="isLogin">
          <input v-model="form.account" placeholder="账号" required />
          <input v-model="form.password" type="password" placeholder="密码" required />
        </div>
        <div v-else>
          <input v-model="registerForm.account" placeholder="账号" required />
          <input v-model="registerForm.password" type="password" placeholder="密码" required />
        </div>
        <button type="submit" class="submit-button">{{ isLogin ? '登录' : '注册' }}</button>
      </form>
      <p @click="toggleForm" class="toggle-link">
        {{ isLogin ? '没有账号？去注册' : '已有账号？去登录' }}
      </p>
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
      registerForm: {
        name: '',
        account: '',
        password: '',
        role: '员工'
      },
      message: ''
    }
  },
  methods: {
    toggleForm() {
          if (this.isLogin) {
              this.$router.push('/register');
        } else {
            this.$router.push('/');
        }
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
          
          // 保存token和用户信息
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('user_info', JSON.stringify(data.user));
          
          // 根据用户角色跳转页面
          if (data.user.role === '管理员') {
            this.$router.push('/admin');
          } else {
            // 普通用户页面（暂时跳转到管理员页面，您可以后续创建普通用户页面）
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
          //暂停1s
          await new Promise(resolve => setTimeout(resolve, 500));
          // 通过路由参数传递用户信息到人脸录入页面
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
}
/* 通用按钮样式 */
.form-box button {
  padding: 10px;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

/* 提交按钮样式 */
.form-box .submit-button {
  width: 100%;
  background: #3498db;
  color: #fff;
}

.form-box .submit-button:hover {
  background: #2980b9;
}


.toggle-link {
  color: #3498db;
  text-align: center;
  cursor: pointer;
  margin-top: 12px;
}
.message {
  text-align: center;
  color: #e74c3c;
  margin-top: 10px;
}
</style>