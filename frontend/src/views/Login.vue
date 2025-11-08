<template>
  <div class="login-container">
    <el-card class="login-card">
      <div slot="header" class="login-header">
        <h2>华为设备AI智能巡检系统</h2>
        <p>请输入账号密码登录</p>
      </div>

      <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" class="login-form">
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            prefix-icon="User"
            autocomplete="off"
          ></el-input>
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            autocomplete="off"
            show-password
          ></el-input>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            class="login-btn"
            @click="handleLogin"
            :loading="loading"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const router = useRouter()
const loading = ref(false)
const loginFormRef = ref(null)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = reactive({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
})

const handleLogin = async () => {
  if (!loginFormRef.value) return

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const response = await axios.post('/api/auth/login', loginForm)

        if (response.data.code === 200) {
          const { token, user } = response.data.data
          localStorage.setItem('token', token)
          localStorage.setItem('username', user.username)
          localStorage.setItem('role', user.role)

          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`

          ElMessage.success('登录成功')
          // 修复：admin角色跳现有路由/monitor（避免404）
          router.push(user.role === 'admin' ? '/monitor' : '/device')
        } else {
          ElMessage.error(response.data.msg || '登录失败')
        }
      } catch (error) {
        console.error('登录失败:', error)
        if (error.response) {
          ElMessage.error(error.response.data.msg || '登录失败，请检查用户名和密码')
        } else {
          ElMessage.error('服务器连接失败，请检查服务是否正常运行')
        }
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.login-card {
  width: 400px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  padding: 20px 0;
}

.login-form {
  padding: 0 20px 20px;
}

.login-btn {
  width: 100%;
}
</style>
