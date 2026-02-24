<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Menu as MenuIcon,
  Histogram,
  Tickets,
  Wallet,
  OfficeBuilding,
  UserFilled,
  Promotion,
  Setting,
} from '@element-plus/icons-vue'

const collapsed = ref(false)

const router = useRouter()
const route = useRoute()

const activeMenu = computed(() => route.path)
const pageTitle = computed(() => route.meta?.title || '管理平台')

const handleMenuSelect = (index) => {
  router.push(index)
}
</script>

<template>
  <el-container class="layout-root">
    <el-aside :width="collapsed ? '64px' : '220px'" class="layout-aside">
      <div class="logo-area">
        <span class="logo-mark">E</span>
        <span v-if="!collapsed" class="logo-text">E-Charge 管理平台</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="menu"
        :collapse="collapsed"
        :collapse-transition="false"
        @select="handleMenuSelect"
      >
        <el-menu-item index="/overview">
          <el-icon><Histogram /></el-icon>
          <span>概览</span>
        </el-menu-item>

        <el-sub-menu index="/orders">
          <template #title>
            <el-icon><Tickets /></el-icon>
            <span>订单管理</span>
          </template>
          <el-menu-item index="/orders/history">历史订单</el-menu-item>
          <el-menu-item index="/orders/realtime">实时订单</el-menu-item>
          <el-menu-item index="/orders/abnormal">异常订单</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="/finance">
          <template #title>
            <el-icon><Wallet /></el-icon>
            <span>财务管理</span>
          </template>
          <el-menu-item index="/finance/cards">绑卡管理</el-menu-item>
          <el-menu-item index="/finance/settlement">收益对账</el-menu-item>
          <el-menu-item index="/finance/invoice">開票管理</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="/stations">
          <template #title>
            <el-icon><OfficeBuilding /></el-icon>
            <span>电站电桩管理</span>
          </template>
          <el-menu-item index="/stations/list">电站列表</el-menu-item>
          <el-menu-item index="/stations/piles">电桩管理</el-menu-item>
          <el-menu-item index="/stations/pricing">电价设置</el-menu-item>
          <el-menu-item index="/stations/review">审核管理</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="/organizations">
          <template #title>
            <el-icon><OfficeBuilding /></el-icon>
            <span>机构管理</span>
          </template>
          <el-menu-item index="/organizations/operators">运营商资料</el-menu-item>
          <el-menu-item index="/organizations/exclusive">专属机构</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="/users">
          <template #title>
            <el-icon><UserFilled /></el-icon>
            <span>用户管理</span>
          </template>
          <el-menu-item index="/users/exclusive">专属用户</el-menu-item>
          <el-menu-item index="/users/fleet">车队管理</el-menu-item>
          <el-menu-item index="/users/whitelist">白名单管理</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="/marketing">
          <template #title>
            <el-icon><Promotion /></el-icon>
            <span>营销管理</span>
          </template>
          <el-menu-item index="/marketing/tags">标签管理</el-menu-item>
          <el-menu-item index="/marketing/discounts">折扣管理</el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="layout-header">
        <div class="header-left">
          <el-button text :icon="MenuIcon" @click="collapsed = !collapsed" />
          <span class="header-title">{{ pageTitle }}</span>
        </div>
        <div class="header-right">
          <span class="header-role">运营商管理员</span>
          <el-divider direction="vertical" />
          <span class="header-email">admin@echarge.com</span>
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
}

.layout-aside {
  border-right: 1px solid #ebeef5;
  background-color: #001529;
  color: #fff;
  display: flex;
  flex-direction: column;
}

.logo-area {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  font-weight: 600;
  font-size: 16px;
  color: #fff;
  box-sizing: border-box;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

.logo-mark {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: linear-gradient(135deg, #409eff, #36d1dc);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-right: 8px;
  font-size: 18px;
}

.logo-text {
  white-space: nowrap;
}

.menu {
  border-right: none;
  flex: 1;
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-sizing: border-box;
  background-color: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #606266;
}

.header-role {
  margin-right: 4px;
}

.header-email {
  font-weight: 500;
}

.layout-main {
  padding: 20px 24px 24px;
  background-color: #f5f7fa;
}
</style>

