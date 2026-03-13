<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { IconMoonStars, IconSun } from '@tabler/icons-vue'
import {
  Menu as MenuIcon,
  Search,
  Bell
} from '@element-plus/icons-vue'
import { buildMenuByRole, ROLE_DEFAULT_ROUTE } from '../config/permissions'

const router = useRouter()
const route = useRoute()

// 响应式状态控制
const collapsed = ref(false)
const drawerVisible = ref(false)
const windowWidth = ref(window.innerWidth)
const theme = ref(document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light')
const currentRole = ref(localStorage.getItem('userRole') || 'operator')

const activeMenu = computed(() => route.path)
const pageTitle = computed(() => route.meta?.title || '管理平台')

const visibleMenus = computed(() => buildMenuByRole(currentRole.value))

// 计算当前屏幕断点
const isMobile = computed(() => windowWidth.value < 768)
const isTablet = computed(() => windowWidth.value >= 768 && windowWidth.value < 1024)

// 监听屏幕尺寸变化的核心逻辑
const handleResize = () => {
  windowWidth.value = window.innerWidth
  if (isMobile.value) {
    collapsed.value = false 
  } else if (isTablet.value) {
    collapsed.value = true 
    drawerVisible.value = false
  } else {
    collapsed.value = false 
    drawerVisible.value = false
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  handleResize()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

const handleMenuSelect = (index) => {
  router.push(index)
  if (isMobile.value) {
    drawerVisible.value = false 
  }
}

const toggleTheme = () => {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  document.documentElement.dataset.theme = theme.value
  localStorage.setItem('theme', theme.value)
  window.dispatchEvent(new Event('themechange'))
}

const handleRoleSwitch = (val) => {
  currentRole.value = val
  localStorage.setItem('userRole', val)
  router.push(ROLE_DEFAULT_ROUTE[val] || '/')
  if (isMobile.value) drawerVisible.value = false
}
</script>

<template>
  <el-container class="layout-root">
    
    <el-aside v-if="!isMobile" :width="collapsed ? 'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)'" class="layout-aside hidden-on-mobile">
      <div class="logo-area">
        <span class="logo-mark">E</span>
        <span v-show="!collapsed" class="logo-text">E-Charge 平台</span>
      </div>
      <el-menu :default-active="activeMenu" class="custom-menu" :collapse="collapsed" :collapse-transition="false" background-color="var(--sidebar-bg)" text-color="#a6adb4" active-text-color="#ffffff" @select="handleMenuSelect">
        <template v-for="item in visibleMenus" :key="item.index">
          <el-sub-menu v-if="item.children" :index="item.index">
            <template #title>
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </template>
            <el-menu-item v-for="child in item.children" :key="child.index" :index="child.index">
              {{ child.title }}
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item v-else :index="item.index">
            <el-icon><component :is="item.icon" /></el-icon>
            <template #title><span>{{ item.title }}</span></template>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-drawer v-model="drawerVisible" direction="ltr" :size="240" :with-header="false" custom-class="mobile-drawer">
      <div class="logo-area mobile-logo">
        <span class="logo-mark">E</span>
        <span class="logo-text">E-Charge 平台</span>
      </div>
      <el-menu :default-active="activeMenu" class="custom-menu" background-color="var(--sidebar-bg)" text-color="#a6adb4" active-text-color="#ffffff" @select="handleMenuSelect">
        <template v-for="item in visibleMenus" :key="item.index">
          <el-sub-menu v-if="item.children" :index="item.index">
            <template #title>
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </template>
            <el-menu-item v-for="child in item.children" :key="child.index" :index="child.index">
              {{ child.title }}
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item v-else :index="item.index">
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-drawer>

    <el-container class="main-container">
      <el-header class="layout-header">
        <div class="header-left">
          <el-icon class="toggle-btn" @click="isMobile ? (drawerVisible = true) : (collapsed = !collapsed)">
            <MenuIcon />
          </el-icon>
          <span v-if="!isMobile" class="header-title">{{ pageTitle }}</span>
        </div>

        <div class="header-right">
          <div class="search-box">
            <el-input v-if="!isMobile" aria-label="全局搜索" placeholder="搜索订单号、电站名称..." :prefix-icon="Search" class="search-input" />
            <el-button v-else circle :icon="Search" aria-label="打开搜索" />
          </div>

          <el-divider direction="vertical" class="hidden-on-mobile" />

          <el-button
            circle
            class="theme-toggle"
            :aria-label="theme === 'dark' ? '切换到浅色模式' : '切换到深色模式'"
            @click="toggleTheme"
          >
            <IconSun v-if="theme === 'dark'" :size="20" />
            <IconMoonStars v-else :size="20" />
          </el-button>
          
          <el-popover placement="bottom-end" :width="300" trigger="click" popper-class="notify-popover">
            <template #reference>
              <el-badge :is-dot="true" class="notify-badge">
                <el-icon class="notify-icon"><Bell /></el-icon>
              </el-badge>
            </template>
            <div class="notify-panel">
              <div class="notify-header">
                <span style="font-weight: 600;">系统通知 (2)</span>
                <el-button link type="primary" size="small">全部已读</el-button>
              </div>
              <el-divider style="margin: 8px 0" />
              <div class="notify-list">
                <div class="notify-item">
                  <div class="notify-title"><el-tag size="small" type="danger" style="margin-right: 8px;">报警</el-tag>A区01号直流桩发生离线故障</div>
                  <div class="notify-time">10 分钟前</div>
                </div>
                <div class="notify-item">
                  <div class="notify-title"><el-tag size="small" type="success" style="margin-right: 8px;">财务</el-tag>昨日收益 T+1 清分已完成</div>
                  <div class="notify-time">2 小时前</div>
                </div>
              </div>
              <el-divider style="margin: 8px 0" />
              <div class="notify-footer">
                <el-button link style="width: 100%;">查看全部通知</el-button>
              </div>
            </div>
          </el-popover>

          <el-dropdown trigger="click" @command="handleRoleSwitch" style="margin-right: 16px;">
            <span class="el-dropdown-link" style="cursor: pointer; display: flex; align-items: center; color: var(--text-primary);">
              <el-tag :type="currentRole === 'admin' ? 'danger' : 'success'" size="small" style="margin-right: 8px;">
                {{ currentRole === 'admin' ? '管理员模式' : '运营商模式' }}
              </el-tag>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="admin">切换至: 管理员</el-dropdown-item>
                <el-dropdown-item command="operator">切换至: 运营商</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <el-dropdown trigger="click" style="margin-left: 12px;">
            <span class="user-info">
              <el-avatar :size="32" class="avatar">Admin</el-avatar>
              <span class="hidden-on-mobile user-email">admin@echarge.com</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人中心</el-dropdown-item>
                <el-dropdown-item divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>

  </el-container>
</template>

<style scoped>
/* 保持上一版的样式不变 */
.layout-root { height: 100vh; width: 100vw; overflow: hidden; }
.main-container { display: flex; flex-direction: column; flex: 1; min-width: 0; }
.layout-aside { background-color: var(--sidebar-bg); transition: width 0.3s cubic-bezier(0.2, 0, 0, 1) 0s; display: flex; flex-direction: column; z-index: 10; }
.logo-area { height: 60px; display: flex; align-items: center; padding: 0 16px; overflow: hidden; color: #fff; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
.logo-mark { min-width: 32px; height: 32px; border-radius: 8px; background: linear-gradient(135deg, #1890ff, #36d1dc); display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px; margin-right: 12px; }
.logo-text { font-size: 16px; font-weight: 600; white-space: nowrap; }
.custom-menu { border-right: none; flex: 1; overflow-y: auto; }
.layout-header { height: 60px; background-color: var(--bg-card); border-bottom: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between; padding: 0 16px; }
.header-left { display: flex; align-items: center; gap: 16px; }
.toggle-btn { font-size: 20px; cursor: pointer; color: var(--text-regular); transition: color 0.2s; }
.toggle-btn:hover { color: #1890ff; }
.header-title { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.header-right { display: flex; align-items: center; gap: 16px; }
.search-box { display: flex; align-items: center; }
.search-input { width: 240px; }
.theme-toggle { border: 1px solid var(--border-color); background: var(--bg-card); }
.notify-icon { font-size: 20px; cursor: pointer; color: var(--text-regular); margin-top: 4px; outline: none; }
.notify-icon:hover { color: #1890ff; }
.notify-badge { cursor: pointer; }
.user-info { display: flex; align-items: center; gap: 8px; cursor: pointer; outline: none; }
.avatar { background-color: #1890ff; font-size: 12px; }
.user-email { font-size: 14px; color: var(--text-regular); }
.layout-main { background-color: var(--bg-main); padding: 20px; flex: 1; overflow-y: auto; }
.mobile-logo { background-color: var(--sidebar-bg); }

/* 通知面板内的样式 */
.notify-panel { padding: 4px; }
.notify-header { display: flex; justify-content: space-between; align-items: center; padding: 0 8px; }
.notify-list { max-height: 240px; overflow-y: auto; }
.notify-item { padding: 12px 8px; border-radius: 6px; cursor: pointer; transition: background 0.2s; }
.notify-item:hover { background-color: #f5f7fa; }
.notify-title { font-size: 14px; color: var(--text-primary); margin-bottom: 4px; line-height: 1.4; display: flex; align-items: flex-start; }
.notify-time { font-size: 12px; color: #909399; margin-left: 42px; }
.notify-footer { text-align: center; padding-top: 4px; }

@media (max-width: 768px) {
  .hidden-on-mobile { display: none !important; }
  .layout-header { padding: 0 12px; }
  .layout-main { padding: 12px; }
}
</style>
