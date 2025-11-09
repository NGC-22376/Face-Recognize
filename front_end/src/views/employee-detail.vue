<template>
  <div class="employee-detail-container">
    <!-- 头部 -->
    <div class="header">
      <div class="header-content">
        <div class="title-section">
          <el-icon class="back-icon" @click="goBack">
            <ArrowLeft />
          </el-icon>
          <h2>个人考勤详情</h2>
        </div>
        <div class="user-info">
          <el-avatar :src="employeeInfo.avatar" v-if="employeeInfo.avatar"></el-avatar>
          <el-avatar v-else>{{ employeeInfo.name?.charAt(0) }}</el-avatar>
          <span class="username">{{ employeeInfo.name }} ({{ employeeInfo.employee_id }})</span>
        </div>
      </div>
    </div>

    <!-- 加载提示 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton animated>
        <template #template>
          <el-skeleton-item variant="h3" style="width: 30%" />
          <div style="margin-top: 20px">
            <el-skeleton-item variant="p" style="width: 100%" />
            <el-skeleton-item variant="p" style="width: 100%; margin-top: 10px" />
            <el-skeleton-item variant="p" style="width: 100%; margin-top: 10px" />
          </div>
        </template>
      </el-skeleton>
    </div>

    <!-- 主要内容 -->
    <div v-else class="main-content">
      <!-- 统计卡片 -->
      <div class="stats-cards">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card class="stat-card" shadow="hover">
              <div class="stat-content">
                <div class="stat-title">应出勤天数</div>
                <div class="stat-value">{{ attendanceStats.scheduled_days }}</div>
                <div class="stat-desc">本月应出勤天数</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card" shadow="hover">
              <div class="stat-content">
                <div class="stat-title">实际出勤</div>
                <div class="stat-value">{{ attendanceStats.actual_days }}</div>
                <div class="stat-desc">本月实际出勤天数</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card" shadow="hover">
              <div class="stat-content">
                <div class="stat-title">迟到次数</div>
                <div class="stat-value">{{ attendanceStats.late_count }}</div>
                <div class="stat-desc">本月迟到次数</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card" shadow="hover">
              <div class="stat-content">
                <div class="stat-title">早退次数</div>
                <div class="stat-value">{{ attendanceStats.early_leave_count }}</div>
                <div class="stat-desc">本月早退次数</div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 图表区域 -->
      <div class="charts-section">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card class="chart-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <span>考勤趋势</span>
                </div>
              </template>
              <div class="chart-container">
                <div ref="attendanceChartRef" class="chart"></div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="chart-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <span>请假趋势</span>
                </div>
              </template>
              <div class="chart-container">
                <div ref="leaveChartRef" class="chart"></div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 考勤记录表格 -->
      <div class="records-section">
        <el-card class="records-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>近期考勤记录</span>
            </div>
          </template>
          <el-table :data="attendanceRecords" stripe style="width: 100%">
            <el-table-column prop="date" label="日期" width="120"></el-table-column>
            <el-table-column prop="clock_in_time" label="上班时间" width="120"></el-table-column>
            <el-table-column prop="clock_out_time" label="下班时间" width="120"></el-table-column>
            <el-table-column prop="status" label="状态" width="150">
              <template #default="scope">
                <el-tag :type="getStatusTagType(scope.row.status)">
                  {{ getStatusText(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="late_minutes" label="迟到(分钟)" width="100"></el-table-column>
            <el-table-column prop="early_leave_minutes" label="早退(分钟)" width="100"></el-table-column>
          </el-table>
          <div class="pagination-container">
            <el-pagination @current-change="handlePageChange" :current-page="currentPage" :page-size="pageSize"
              :total="totalRecords" layout="prev, pager, next" background />
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

// 路由和路由参数
const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(true)
const employeeInfo = reactive({
  employee_id: '',
  name: '',
  avatar: ''
})

// 考勤统计数据
const attendanceStats = reactive({
  scheduled_days: 0,
  actual_days: 0,
  late_count: 0,
  early_leave_count: 0
})

// 考勤记录
const attendanceRecords = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const totalRecords = ref(0)

// 图表引用
const attendanceChartRef = ref(null)
const leaveChartRef = ref(null)
let attendanceChart = null
let leaveChart = null

// API基础URL
const apiBaseUrl = 'http://localhost:5000'

// 获取当前用户ID
const currentUserId = () => {
  const ui = localStorage.getItem('user_info')
  return ui ? JSON.parse(ui).user_id : null
}

// 返回上一页
const goBack = () => {
  router.back()
}

// 获取员工详细信息
const fetchEmployeeDetail = async () => {
  const userId = route.query.user_id || currentUserId()
  if (!userId) {
    ElMessage.error('用户信息缺失')
    return
  }

  try {
    const res = await fetch(`${apiBaseUrl}/employees/${userId}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    }).then(r => r.json())

    if (res.ok) {
      employeeInfo.employee_id = res.data.employee_id
      employeeInfo.name = res.data.name
      employeeInfo.avatar = res.data.avatar
    } else {
      ElMessage.error(res.msg || '获取员工信息失败')
    }
  } catch (e) {
    ElMessage.error('网络错误：' + e.message)
  }
}

// 获取考勤统计数据
const fetchAttendanceStats = async () => {
  const userId = route.query.user_id || currentUserId()
  if (!userId) return

  try {
    const res = await fetch(`${apiBaseUrl}/attendance/stats/${userId}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    }).then(r => r.json())

    if (res.ok) {
      Object.assign(attendanceStats, res.data)
    } else {
      ElMessage.error(res.msg || '获取考勤统计数据失败')
    }
  } catch (e) {
    ElMessage.error('网络错误：' + e.message)
  }
}

// 获取考勤记录
const fetchAttendanceRecords = async (page = 1) => {
  const userId = route.query.user_id || currentUserId()
  if (!userId) return

  try {
    const res = await fetch(
      `${apiBaseUrl}/attendance/records/${userId}?page=${page}&per_page=${pageSize.value}`,
      {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
      }
    ).then(r => r.json())

    if (res.ok) {
      attendanceRecords.value = res.data.records
      totalRecords.value = res.data.total
      currentPage.value = page
    } else {
      ElMessage.error(res.msg || '获取考勤记录失败')
    }
  } catch (e) {
    ElMessage.error('网络错误：' + e.message)
  }
}

// 获取考勤趋势数据
const fetchAttendanceTrend = async () => {
  const userId = route.query.user_id || currentUserId()
  if (!userId) return

  try {
    const res = await fetch(`${apiBaseUrl}/attendance/trend/${userId}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    }).then(r => r.json())

    if (res.ok) {
      renderAttendanceChart(res.data)
    } else {
      ElMessage.error(res.msg || '获取考勤趋势数据失败')
    }
  } catch (e) {
    ElMessage.error('网络错误：' + e.message)
  }
}

// 获取请假趋势数据
const fetchLeaveTrend = async () => {
  const userId = route.query.user_id || currentUserId()
  if (!userId) return

  try {
    const res = await fetch(`${apiBaseUrl}/leave/trend/${userId}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    }).then(r => r.json())

    if (res.ok) {
      renderLeaveChart(res.data)
    } else {
      ElMessage.error(res.msg || '获取请假趋势数据失败')
    }
  } catch (e) {
    ElMessage.error('网络错误：' + e.message)
  }
}

// 渲染考勤趋势图表
const renderAttendanceChart = (data) => {
  if (!attendanceChartRef.value) return

  // 初始化图表
  if (!attendanceChart) {
    attendanceChart = echarts.init(attendanceChartRef.value)
  }

  // 处理数据
  const dates = data.map(item => item.date)
  const normalCount = data.map(item => item.normal)
  const lateCount = data.map(item => item.late)
  const earlyLeaveCount = data.map(item => item.early_leave)
  const absenceCount = data.map(item => item.absence)
  const overtimeCount = data.map(item => item.overtime)

  // 图表配置
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['正常', '迟到', '早退', '缺勤', '加班']
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value',
      name: '次数'
    },
    series: [
      {
        name: '正常',
        type: 'line',
        data: normalCount,
        smooth: true
      },
      {
        name: '迟到',
        type: 'line',
        data: lateCount,
        smooth: true
      },
      {
        name: '早退',
        type: 'line',
        data: earlyLeaveCount,
        smooth: true
      },
      {
        name: '缺勤',
        type: 'line',
        data: absenceCount,
        smooth: true
      },
      {
        name: '加班',
        type: 'line',
        data: overtimeCount,
        smooth: true
      }
    ]
  }

  // 设置图表配置
  attendanceChart.setOption(option, true)
}

// 渲染请假趋势图表
const renderLeaveChart = (data) => {
  if (!leaveChartRef.value) return

  // 初始化图表
  if (!leaveChart) {
    leaveChart = echarts.init(leaveChartRef.value)
  }

  // 处理数据
  const dates = data.map(item => item.date)
  const sickLeave = data.map(item => item.sick_leave)
  const personalLeave = data.map(item => item.personal_leave)
  const officialLeave = data.map(item => item.official_leave)

  // 图表配置
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['病假', '私事假', '公事假']
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value',
      name: '次数'
    },
    series: [
      {
        name: '病假',
        type: 'line',
        data: sickLeave,
        smooth: true
      },
      {
        name: '私事假',
        type: 'line',
        data: personalLeave,
        smooth: true
      },
      {
        name: '公事假',
        type: 'line',
        data: officialLeave,
        smooth: true
      }
    ]
  }

  // 设置图表配置
  leaveChart.setOption(option, true)
}

// 处理分页变化
const handlePageChange = (page) => {
  fetchAttendanceRecords(page)
}

// 获取状态标签类型
const getStatusTagType = (status) => {
  switch (status) {
    case 'normal':
      return 'success'
    case 'late':
      return 'warning'
    case 'early_leave':
      return 'warning'
    case 'absence':
      return 'danger'
    case 'overtime':
      return 'primary'
    default:
      return 'info'
  }
}

// 获取状态文本
const getStatusText = (status) => {
  switch (status) {
    case 'normal':
      return '正常'
    case 'late':
      return '迟到'
    case 'early_leave':
      return '早退'
    case 'absence':
      return '缺勤'
    case 'overtime':
      return '加班'
    case 'not_signed_out':
      return '未签退'
    default:
      return status
  }
}

// 初始化所有数据
const initAllData = async () => {
  loading.value = true
  await Promise.all([
    fetchEmployeeDetail(),
    fetchAttendanceStats(),
    fetchAttendanceRecords(),
    fetchAttendanceTrend(),
    fetchLeaveTrend()
  ])
  loading.value = false
}

// 生命周期钩子
onMounted(async () => {
  await initAllData()

  // 等待DOM渲染完成后初始化图表
  await nextTick()
  window.addEventListener('resize', () => {
    if (attendanceChart) attendanceChart.resize()
    if (leaveChart) leaveChart.resize()
  })
})
</script>

<style scoped>
.employee-detail-container {
  height: 100vh;
  background-color: #f5f7fa;
  padding: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 头部样式 */
.header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
  padding: 16px 0;
  flex-shrink: 0;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-icon {
  font-size: 24px;
  cursor: pointer;
  color: #409eff;
}

.title-section h2 {
  margin: 0;
  color: #303133;
  font-weight: 600;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.username {
  color: #606266;
  font-size: 16px;
}

/* 加载容器 */
.loading-container {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 24px;
  flex: 1;
}

/* 主要内容区域 */
.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px 24px;
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 统计卡片 */
.stats-cards {
  flex-shrink: 0;
}

.stat-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.stat-content {
  text-align: center;
  padding: 20px 0;
}

.stat-title {
  color: #909399;
  font-size: 14px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.stat-desc {
  color: #c0c4cc;
  font-size: 12px;
}

/* 图表区域 */
.charts-section {
  flex-shrink: 0;
}

.chart-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 300px;
  padding: 10px;
}

.chart {
  width: 100%;
  height: 100%;
}

/* 记录区域 */
.records-section {
  flex: 1;
  min-height: 0;
}

.records-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.records-card :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }

  .main-content {
    padding: 16px 12px;
  }

  .stats-cards :deep(.el-col) {
    margin-bottom: 12px;
  }

  .charts-section :deep(.el-col) {
    margin-bottom: 12px;
  }

  .chart-container {
    height: 250px;
  }
}
</style>