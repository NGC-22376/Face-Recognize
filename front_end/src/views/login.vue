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
          <input v-model="registerForm.role" placeholder="角色（如员工/管理员）" required />
        </div>
        <button type="submit">{{ isLogin ? '登录' : '注册' }}</button>
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
        role: ''
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
        const res = await fetch('/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.form)
        });
        const data = await res.json();
        if (res.ok) {
          this.message = '登录成功';
          // 登录成功后可跳转页面，如：this.$router.push('/home')
        } else {
          this.message = data.message || '登录失败';
        }
      } catch (err) {
        this.message = '网络错误';
      }
    },
    async handleRegister() {
      try {
        const res = await fetch('/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.registerForm)
        });
        console.log(this.registerForm);
        const data = await res.json();
        if (res.ok) {
          this.message = '注册成功，请登录';
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
.form-box button {
  width: 100%;
  padding: 10px;
  background: #3498db;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
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