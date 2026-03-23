<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { IconMoonStars, IconSun } from '@tabler/icons-vue'
import { Bell, Menu as MenuIcon, Search } from '@element-plus/icons-vue'

import {
  buildMenuByRole,
  getStoredRole,
  resolveRoleDefaultRoute,
  ROLE_LABELS,
  ROLES,
  setStoredRole,
} from '../config/permissions'

const route = useRoute()
const router = useRouter()

const collapsed = ref(false)
const drawerVisible = ref(false)
const windowWidth = ref(window.innerWidth)
const theme = ref(document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light')

const currentRole = computed(() => route.meta?.role || getStoredRole())
const activeMenu = computed(() => route.path)
const pageTitle = computed(() => route.meta?.title || '运营中台')
const pageSection = computed(() => route.meta?.section || ROLE_LABELS[currentRole.value])
const roleLabel = computed(() => ROLE_LABELS[currentRole.value] || '运营商')
const visibleMenuGroups = computed(() => buildMenuByRole(currentRole.value))
const isMobile = computed(() => windowWidth.value < 960)

const handleResize = () => {
  windowWidth.value = window.innerWidth
  if (isMobile.value) collapsed.value = false
}

const handleMenuSelect = (path) => {
  router.push(path)
  if (isMobile.value) drawerVisible.value = false
}

const toggleTheme = () => {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  document.documentElement.dataset.theme = theme.value
  localStorage.setItem('theme', theme.value)
  window.dispatchEvent(new Event('themechange'))
}

const switchRole = (role) => {
  setStoredRole(role)
  router.push(resolveRoleDefaultRoute(role))
  if (isMobile.value) drawerVisible.value = false
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  handleResize()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <el-container class="layout-root">
    <el-aside v-if="!isMobile" :width="collapsed ? '88px' : '288px'" class="layout-aside">
      <div class="brand">
        <div class="brand__mark">EC</div>
        <div v-show="!collapsed" class="brand__text">
          <strong>E-Charge Console</strong>
          <span>{{ roleLabel }}</span>
        </div>
      </div>

      <div class="menu-scroll">
        <section v-for="group in visibleMenuGroups" :key="group.label" class="menu-group">
          <p v-show="!collapsed" class="menu-group__label">{{ group.label }}</p>
          <el-menu
            :default-active="activeMenu"
            class="menu"
            :collapse="collapsed"
            :collapse-transition="false"
            background-color="transparent"
            text-color="var(--color-sidebar-text)"
            active-text-color="#ffffff"
            @select="handleMenuSelect"
          >
            <el-menu-item v-for="item in group.items" :key="item.index" :index="item.index">
              <el-icon><component :is="item.icon" /></el-icon>
              <template #title>{{ item.title }}</template>
            </el-menu-item>
          </el-menu>
        </section>
      </div>
    </el-aside>

    <el-drawer v-model="drawerVisible" direction="ltr" :size="288" :with-header="false">
      <div class="brand brand--mobile">
        <div class="brand__mark">EC</div>
        <div class="brand__text">
          <strong>E-Charge Console</strong>
          <span>{{ roleLabel }}</span>
        </div>
      </div>
      <div class="menu-scroll">
        <section v-for="group in visibleMenuGroups" :key="group.label" class="menu-group">
          <p class="menu-group__label">{{ group.label }}</p>
          <el-menu
            :default-active="activeMenu"
            class="menu"
            background-color="transparent"
            text-color="var(--color-sidebar-text)"
            active-text-color="#ffffff"
            @select="handleMenuSelect"
          >
            <el-menu-item v-for="item in group.items" :key="item.index" :index="item.index">
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </el-menu-item>
          </el-menu>
        </section>
      </div>
    </el-drawer>

    <el-container class="main-shell">
      <el-header class="layout-header">
        <div class="header-left">
          <el-icon class="header-action" @click="isMobile ? (drawerVisible = true) : (collapsed = !collapsed)">
            <MenuIcon />
          </el-icon>
          <div class="page-meta">
            <span class="page-meta__section">{{ pageSection }}</span>
            <h2 class="page-meta__title">{{ pageTitle }}</h2>
          </div>
        </div>

        <div class="header-right">
          <el-input v-if="!isMobile" placeholder="搜索订单、站点、活动..." :prefix-icon="Search" class="search-input" />
          <el-button v-else circle :icon="Search" />

          <el-button circle class="toolbar-btn" @click="toggleTheme">
            <IconSun v-if="theme === 'dark'" :size="18" />
            <IconMoonStars v-else :size="18" />
          </el-button>

          <el-popover placement="bottom-end" :width="320" trigger="click">
            <template #reference>
              <el-button circle class="toolbar-btn">
                <el-badge :value="2">
                  <el-icon><Bell /></el-icon>
                </el-badge>
              </el-button>
            </template>
            <div class="notify-panel">
              <div class="notify-panel__item">
                <strong>重构导航已完成</strong>
                <p>管理员与运营商视角已经拆分为独立业务路径，后续开发不再需要反复改菜单结构。</p>
              </div>
              <div class="notify-panel__item">
                <strong>第二轮页面补齐中</strong>
                <p>占位页已逐步替换为正式页面，并统一接入后端接口与视觉系统。</p>
              </div>
            </div>
          </el-popover>

          <el-dropdown @command="switchRole">
            <div class="role-switcher">
              <span class="role-switcher__label">当前视角</span>
              <el-tag :type="currentRole === ROLES.ADMIN ? 'danger' : 'success'">{{ roleLabel }}</el-tag>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item :command="ROLES.ADMIN">切换到平台管理员</el-dropdown-item>
                <el-dropdown-item :command="ROLES.OPERATOR">切换到运营商</el-dropdown-item>
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
.layout-root {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.layout-aside {
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  background:
    radial-gradient(circle at top left, rgba(64, 158, 255, 0.18), transparent 34%),
    linear-gradient(180deg, rgba(7, 19, 42, 0.98), rgba(10, 26, 55, 0.98));
  transition: width 0.24s ease;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.brand__mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: linear-gradient(135deg, #36cfc9, #409eff);
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #fff;
}

.brand__text {
  display: flex;
  flex-direction: column;
}

.brand__text strong {
  font-size: 15px;
  color: #fff;
}

.brand__text span {
  margin-top: 4px;
  color: var(--color-sidebar-text-soft);
  font-size: 12px;
}

.brand--mobile {
  margin: -18px -16px 0;
  background:
    radial-gradient(circle at top left, rgba(64, 158, 255, 0.18), transparent 34%),
    linear-gradient(180deg, rgba(7, 19, 42, 0.98), rgba(10, 26, 55, 0.98));
}

.menu-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 18px 12px 20px;
}

.menu-group + .menu-group {
  margin-top: 14px;
}

.menu-group__label {
  margin: 0 0 8px;
  padding: 0 12px;
  color: var(--color-sidebar-text-soft);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.menu {
  border-right: none;
}

.menu :deep(.el-menu-item) {
  margin-bottom: 6px;
  border-radius: 12px;
  color: var(--color-sidebar-text) !important;
}

.menu :deep(.el-menu-item:hover) {
  background: var(--color-sidebar-hover) !important;
}

.menu :deep(.el-menu-item.is-active) {
  background: var(--color-sidebar-active) !important;
  box-shadow: 0 10px 24px rgba(64, 158, 255, 0.24);
}

.main-shell {
  min-width: 0;
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  height: 76px;
  padding: 0 20px;
  border-bottom: 1px solid var(--color-border);
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(14px);
}

:root[data-theme='dark'] .layout-header {
  background: rgba(15, 23, 42, 0.78);
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-action {
  font-size: 20px;
  cursor: pointer;
  color: var(--color-text-2);
}

.page-meta__section {
  display: inline-block;
  margin-bottom: 4px;
  color: var(--color-text-3);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.page-meta__title {
  margin: 0;
  font-size: 20px;
  color: var(--color-text);
}

.search-input {
  width: 260px;
}

.toolbar-btn {
  color: var(--color-text-2);
}

.notify-panel {
  display: grid;
  gap: 12px;
}

.notify-panel__item {
  padding: 12px;
  border-radius: 12px;
  background: var(--color-surface-2);
}

.notify-panel__item p {
  margin: 6px 0 0;
  color: var(--color-text-3);
  line-height: 1.5;
}

.role-switcher {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.role-switcher__label {
  color: var(--color-text-3);
  font-size: 12px;
}

.layout-main {
  padding: 20px;
  overflow-y: auto;
}

@media (max-width: 960px) {
  .layout-header {
    height: 68px;
    padding: 0 14px;
  }

  .layout-main {
    padding: 14px;
  }

  .page-meta__title {
    font-size: 18px;
  }
}
</style>
