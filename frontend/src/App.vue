<template>
  <div id="app">
    <el-container v-if="isLoggedIn" style="height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
      <el-aside width="240px" style="background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%); box-shadow: 2px 0 8px rgba(0,0,0,0.1);">
        <div class="sidebar-header">
          <h2 style="color: #fff; margin: 20px 0; text-align: center; font-size: 20px; font-weight: bold;">
            <i class="el-icon-cpu"></i> AI智能巡检
          </h2>
        </div>
        <el-menu
          :default-active="activeMenu"
          router
          background-color="transparent"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
          style="border: none;"
          class="sidebar-menu"
        >
          <el-menu-item index="/device" class="menu-item">
            <i class="el-icon-monitor"></i>
            <span>设备管理</span>
          </el-menu-item>
          <el-menu-item index="/monitor" class="menu-item">
            <i class="el-icon-data-line"></i>
            <span>监控面板</span>
          </el-menu-item>
          <el-menu-item index="/inspect" class="menu-item">
            <i class="el-icon-search"></i>
            <span>巡检管理</span>
          </el-menu-item>
          <el-menu-item index="/report" class="menu-item">
            <i class="el-icon-document"></i>
            <span>巡检报告</span>
          </el-menu-item>
          <el-menu-item index="/topology" class="menu-item">
            <i class="el-icon-connection"></i>
            <span>3D拓扑</span>
          </el-menu-item>
          <el-menu-item index="/alert" class="menu-item">
            <i class="el-icon-bell"></i>
            <span>告警配置</span>
          </el-menu-item>
          <el-menu-item index="/report-export" class="menu-item">
            <i class="el-icon-download"></i>
            <span>报告导出</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-container>
        <el-header style="background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); border-bottom: 1px solid #e4e7ed; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
          <h2 style="margin: 0; color: #303133; font-size: 18px; font-weight: 600;">
            <i class="el-icon-cpu" style="color: #409EFF;"></i> AI智能网络巡检系统
          </h2>
          <div>
            <el-dropdown @command="handleCommand">
              <span class="user-info">
                <i class="el-icon-user"></i> {{ username || '管理员' }}
                <i class="el-icon-arrow-down"></i>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                  <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>
        <el-main style="background: #f5f7fa; padding: 20px; overflow-y: auto;">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
    <router-view v-else />
  </div>
</template>

<script>
import { computed, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'

export default {
  name: 'App',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const username = ref(localStorage.getItem('username') || '管理员')
    
    const isLoggedIn = computed(() => {
      return !!localStorage.getItem('token')
    })
    
    const activeMenu = computed(() => {
      return route.path
    })
    
    const handleLogout = () => {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      router.push('/login')
    }
    
    const handleCommand = (command) => {
      if (command === 'logout') {
        handleLogout()
      } else if (command === 'profile') {
        // 个人中心
        console.log('个人中心')
      }
    }
    
    onMounted(() => {
      if (!isLoggedIn.value && route.path !== '/login') {
        router.push('/login')
      }
    })
    
    return {
      isLoggedIn,
      activeMenu,
      username,
      handleLogout,
      handleCommand
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji';
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  height: 100vh;
  overflow: hidden;
}

.el-header {
  height: 60px !important;
  line-height: 60px;
  padding: 0 20px;
}

.user-info {
  cursor: pointer;
  color: #303133;
  font-size: 14px;
  padding: 0 15px;
  display: inline-block;
  transition: color 0.3s;
}

.user-info:hover {
  color: #409EFF;
}

.sidebar-menu .menu-item {
  margin: 5px 10px;
  border-radius: 8px;
  transition: all 0.3s;
}

.sidebar-menu .menu-item:hover {
  background: rgba(255, 255, 255, 0.1) !important;
}

.sidebar-menu .el-menu-item.is-active {
  background: linear-gradient(90deg, #409EFF 0%, #66b1ff 100%) !important;
  color: #fff !important;
  border-radius: 8px;
}

.sidebar-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 10px;
}
</style>
