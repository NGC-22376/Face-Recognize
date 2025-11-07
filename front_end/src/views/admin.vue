<template>
  <div class="admin-container">
    <!-- 顶部导航 -->
    <div class="header">
      <div class="user-info">
        <div class="avatar">{{ userProfile.name ? userProfile.name.charAt(0) : 'A' }}</div>
        <div class="user-details">
          <h3>{{ userProfile.name }}</h3>
          <p>工号：{{ userProfile.account }} | 权限：{{ userProfile.role }}</p>
        </div>
      </div>
      <div class="header-actions">
        <button @click="logout" class="logout-btn">退出登录</button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧导航 -->
      <div class="sidebar">
        <nav class="nav-menu">
          <div v-if="userProfile.role === '管理员'" class="nav-item" :class="{ active: activeTab === 'dashboard' }"
            @click="setActiveTab('dashboard')">
            <span>📊</span> 考勤概览
          </div>
          <div v-if="userProfile.role === '管理员'" class="nav-item" :class="{ active: activeTab === 'employees' }"
            @click="setActiveTab('employees')">
            <span>👥</span> 员工考勤
          </div>
          <div v-if="userProfile.role === '员工'" class="nav-item" :class="{ active: activeTab === 'personal' }" @click="setActiveTab('personal')">
            <span>👤</span> 个人考勤
          </div>
          <div v-if="userProfile.role === '员工'" class="nav-item" :class="{ active: activeTab === 'clock' }" @click="setActiveTab('clock')">
            <span>⏰</span> 打卡
          </div>
          <div v-if="userProfile.role === '员工'" class="nav-item" :class="{ active: activeTab === 'face_register' }" @click="setActiveTab('face_register')">
            <span>📷</span> 人脸录入
          </div>
          <div class="nav-item" :class="{ active: activeTab === 'leave' }" @click="setActiveTab('leave')">
            <span>📝</span> 请假
          </div>
        </nav>
      </div>

      <!-- 右侧内容区域 -->
      <div class="content-area">
        <!-- 考勤概览 -->
        <div v-if="activeTab === 'dashboard' && userProfile.role === '管理员'" class="tab-content">
          <h2>今日考勤概览</h2>
          <div class="stats-cards">
            <div class="stat-card">
              <div class="stat-number">{{ dailyStats.should_attend }}</div>
              <div class="stat-label">应到人数</div>
            </div>
            <div class="stat-card">
              <div class="stat-number">{{ dailyStats.actual_attendance }}</div>
              <div class="stat-label">实到人数</div>
            </div>
            <div class="stat-card late">
              <div class="stat-number">{{ dailyStats.late_count }}</div>
              <div class="stat-label">迟到人数</div>
            </div>
            <div class="stat-card early">
              <div class="stat-number">{{ dailyStats.early_leave_count }}</div>
              <div class="stat-label">早退人数</div>
            </div>
            <div class="stat-card normal">
              <div class="stat-number">{{ dailyStats.normal_count }}</div>
              <div class="stat-label">正常人数</div>
            </div>
          </div>
          <div class="charts-container">
            <h3>考勤统计图表</h3>
            <div id="attendance-chart-1" style="width: 100%; height: 400px;"></div>
            <div id="attendance-chart-2" style="width: 100%; height: 400px; margin-top: 20px;"></div>
          </div>
          <div class="date-info">
            <p>统计日期：{{ dailyStats.date }}</p>
          </div>
        </div>

        <!-- 员工考勤管理 -->
        <div v-if="activeTab === 'employees' && userProfile.role === '管理员'" class="tab-content">
          <div class="section-header">
            <h2>员工考勤管理</h2>
            <div class="section-actions">
              <div class="sort-controls">
                <label>排序方式：</label>
                <select v-model="sortBy" @change="loadEmployeesData">
                  <option value="account">工号</option>
                  <option value="name">姓名</option>
                  <option value="late_count">迟到次数</option>
                  <option value="early_leave_count">早退次数</option>
                  <option value="normal_count">正常次数</option>
                  <option value="leave_count">请假次数</option>
                </select>
                <select v-model="sortOrder" @change="loadEmployeesData">
                  <option value="asc">升序</option>
                  <option value="desc">降序</option>
                </select>
              </div>
              <button @click="exportAttendanceData" class="export-btn">导出考勤数据</button>
            </div>
          </div>

          <div class="employees-table">
            <table>
              <thead>
                <tr>
                  <th>姓名</th>
                  <th>工号</th>
                  <th>今日出勤</th>
                  <th>本月出勤</th>
                  <th>迟到次数</th>
                  <th>早退次数</th>
                  <th>正常次数</th>
                  <th>请假次数</th>
                  <th>应出勤天数</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="employee in employees" :key="employee.user_id">
                  <td>{{ employee.name }}</td>
                  <td>{{ employee.account }}</td>
                  <td>
                    <span
                      :class="(employee.on_leave_today ? 'status-leave' : (employee.is_absent_today ? 'status-absent' : (employee.today_attendance > 0 ? 'status-present' : 'status-absent')))">
                      {{ employee.on_leave_today ? '请假' : (employee.is_absent_today ? '未出勤' : (employee.today_attendance
                        > 0 ? '已出勤' : '未出勤')) }}
                    </span>
                  </td>
                  <td>{{ employee.monthly_stats.total_days }}</td>
                  <td class="late-count">{{ employee.monthly_stats.late_count }}</td>
                  <td class="early-count">{{ employee.monthly_stats.early_leave_count }}</td>
                  <td class="normal-count">{{ employee.monthly_stats.normal_count }}</td>
                  <td class="leave-count">{{ employee.monthly_stats.leave_count }}</td>
                  <td>{{ employee.monthly_stats.should_attend }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 分页控件 -->
          <div class="pagination-controls" v-if="totalEmployees > 0">
            <button :disabled="currentPage === 1" @click="handlePageChange(currentPage - 1)">上一页</button>
            <span>第 {{ currentPage }} 页 / 共 {{ Math.ceil(totalEmployees / pageSize) }} 页</span>
            <button :disabled="currentPage === Math.ceil(totalEmployees / pageSize)" @click="handlePageChange(currentPage + 1)">下一页</button>
            
          </div>
          <div class="pagination-controls" v-if="totalEmployees > 0">
            <span>跳转到第</span>
            <input
              type="number"
              v-model.number="jumpToPage"
              placeholder="跳转页码"
              min="1"
              :max="Math.ceil(totalEmployees / pageSize)"
              style="width: 60px; text-align: center; margin: 0 8px;"
            />
            <span>页</span>
            <button @click="handlePageJump">跳转</button>
          </div>
        </div>

        <!-- 个人考勤 -->
        <div v-if="activeTab === 'personal'" class="tab-content">
          <h2>我的考勤记录</h2>
          <div class="personal-stats">
            <div class="stat-card">
              <div class="stat-number">{{ personalStats.should_attend }}</div>
              <div class="stat-label">应出勤天数</div>
            </div>
            <div class="stat-card">
              <div class="stat-number">{{ personalStats.total_days }}</div>
              <div class="stat-label">实际出勤</div>
            </div>
            <div class="stat-card late">
              <div class="stat-number">{{ personalStats.late_count }}</div>
              <div class="stat-label">迟到次数</div>
            </div>
            <div class="stat-card early">
              <div class="stat-number">{{ personalStats.early_leave_count }}</div>
              <div class="stat-label">早退次数</div>
            </div>
            <div class="stat-card normal">
              <div class="stat-number">{{ personalStats.normal_count }}</div>
              <div class="stat-label">正常次数</div>
            </div>
          </div>

          <div class="recent-records">
            <h3>最近考勤记录</h3>
            <div class="records-table">
              <table>
                <thead>
                  <tr>
                    <th>日期</th>
                    <th>上班时间</th>
                    <th>下班时间</th>
                    <th>状态</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="record in recentRecords" :key="record.attendance_id">
                    <td>{{ formatDate(record.clock_in_time) }}</td>
                    <td>{{ record.status === '请假' ? '-' : (record.status === '未出勤' ? '未打卡' :
                      formatTime(record.clock_in_time)) }}</td>
                    <td>{{ record.status === '请假' ? '-' : (record.clock_out_time ? formatTime(record.clock_out_time) :
                      '未打卡') }}</td>
                    <td>
                      <span :class="getStatusClass(record.status)">{{ record.status }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- 打卡 -->
        <div v-if="activeTab === 'clock'" class="tab-content">
          <h2>打卡</h2>
          <div class="clock-section">
            <div class="current-time">
              <div class="time-display">{{ currentTime }}</div>
              <div class="date-display">{{ currentDate }}</div>
            </div>

            <div class="clock-buttons">
              <button @click="goFace('clock_in')" class="clock-btn clock-in">上班打卡</button>
              <button @click="goFace('clock_out')" class="clock-btn clock-out">下班打卡</button>
            </div>

            <div v-if="clockMessage" class="clock-message" :class="clockMessageType">
              {{ clockMessage }}
            </div>
          </div>
        </div>

        <!-- 人脸录入 -->
        <div v-if="activeTab === 'face_register'" class="tab-content">
          <h2>人脸录入</h2>
          <div class="face-register-section">
            <div class="info-card">
              <h3>人脸录入说明</h3>
              <ul>
                <li>请确保在光线充足的环境下进行录入</li>
                <li>保持面部清晰可见，不要佩戴帽子或墨镜</li>
                <li>请正对摄像头，保持自然表情</li>
                <li>录入成功后即可使用人脸识别打卡功能</li>
              </ul>
            </div>
            <div class="register-action">
              <button @click="goToFaceRegister" class="register-btn">
                <span class="btn-icon">📷</span>
                <span class="btn-text">开始人脸录入</span>
              </button>
              <p class="register-tips">点击上方按钮进入人脸录入页面</p>
            </div>
          </div>
        </div>

        <!-- 新增：请假（员工提交 / 管理员审核） -->
        <div v-if="activeTab === 'leave'" class="tab-content">
          <template v-if="userProfile.role === '员工'">
            <h2>请假申请</h2>
            <div class="leave-form">
              <label>开始时间</label>
              <input type="datetime-local" v-model="leaveForm.start_time" />
              <label>结束时间</label>
              <input type="datetime-local" v-model="leaveForm.end_time" />
              <label>请假原因</label>
              <textarea v-model="leaveForm.reason" rows="3"></textarea>
              <label>请假类型</label>
              <select v-model="leaveForm.absence_type">
                <option v-for="type in leaveTypes" :key="type.value" :value="type.value">{{ type.label }}</option>
              </select>
              <button @click="submitLeave" class="clock-btn leave-submit">提交申请</button>
              <div v-if="leaveMessage" class="clock-message" :class="leaveMessageType">{{ leaveMessage }}</div>
            </div>

            <div class="records-table">
              <h3>历史请假申请</h3>
              <table>
                <thead>
                  <tr>
                    <th>起始时间</th>
                    <th>结束时间</th>
                    <th>事由</th>
                    <th>请假类型</th>
                    <th>状态</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in myLeaves" :key="item.id">
                    <td>{{ formatDateTime(item.start_time) }}</td>
                    <td>{{ formatDateTime(item.end_time) }}</td>
                    <td>{{ item.reason }}</td>
                    <td>{{ getLeaveTypeLabel(item.absence_type) }}</td>
                    <td>{{ statusMap[item.status] || item.status }}</td>
                  </tr>
                </tbody>
              </table>
              
              <!-- 分页控件 -->
              <div class="pagination" v-if="pagination.myLeaves.total > 0">
                <button 
                  @click="changeMyLeavesPage(pagination.myLeaves.currentPage - 1)" 
                  :disabled="pagination.myLeaves.currentPage === 1"
                  class="pagination-btn"
                >
                  上一页
                </button>
                
                <span 
                  v-for="page in generatePageNumbers(pagination.myLeaves.pages, pagination.myLeaves.currentPage)" 
                  :key="page"
                  @click="changeMyLeavesPage(page)"
                  :class="['pagination-item', { active: page === pagination.myLeaves.currentPage }]"
                >
                  {{ page }}
                </span>
                
                <button 
                  @click="changeMyLeavesPage(pagination.myLeaves.currentPage + 1)" 
                  :disabled="pagination.myLeaves.currentPage === pagination.myLeaves.pages"
                  class="pagination-btn"
                >
                  下一页
                </button>
                
                <span class="pagination-info">
                  共 {{ pagination.myLeaves.total }} 条记录，第 {{ pagination.myLeaves.currentPage }} / {{ pagination.myLeaves.pages }} 页
                </span>
              </div>
            </div>
          </template>
          <template v-else>
            <h2>请假审核</h2>
            <div class="tab-switch">
              <button :class="{ active: leaveAdminTab === 'unprocessed' }"
                @click="leaveAdminTab = 'unprocessed'; loadAdminLeaves(false)">未处理</button>
              <button :class="{ active: leaveAdminTab === 'processed' }"
                @click="leaveAdminTab = 'processed'; loadAdminLeaves(true, 1)">已处理</button>
            </div>

            <!-- 筛选控件 -->
            <div class="filter-controls" style="margin: 15px 0;">
              <input type="text" v-model="nameFilter" placeholder="搜索姓名" style="margin-right: 10px; padding: 5px;" />
              <select v-model="typeFilter" style="padding: 5px;">
                <option value="-1">全部类型</option>
                <option v-for="type in leaveTypes" :key="type.value" :value="type.value">{{ type.label }}</option>
              </select>
            </div>

            <div class="records-table" v-if="leaveAdminTab === 'unprocessed'">
              <table>
                <thead>
                  <tr>
                    <th>姓名</th>
                    <th>工号</th>
                    <th>起始时间</th>
                    <th>结束时间</th>
                    <th>事由</th>
                    <th>请假类型</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in filteredUnprocessedLeaves" :key="item.id" @click="selectedLeave = item">
                    <td>{{ item.name }}</td>
                    <td>{{ item.account }}</td>
                    <td>{{ formatDateTime(item.start_time) }}</td>
                    <td>{{ formatDateTime(item.end_time) }}</td>
                    <td>{{ item.reason }}</td>
                    <td>{{ getLeaveTypeLabel(item.absence_type) }}</td>
                    <td>
                      <button class="clock-btn clock-in" @click.stop="reviewLeave(item.id, 'approve')">通过</button>
                      <button class="clock-btn clock-out" @click.stop="reviewLeave(item.id, 'reject')">拒绝</button>
                    </td>
                  </tr>
                </tbody>
              </table>
              
              <!-- 分页控件 -->
              <div class="pagination" v-if="pagination.adminLeaves.unprocessed.total > 0">
                <button 
                  @click="changeAdminLeavesPage(false, Math.max(1, pagination.adminLeaves.unprocessed.currentPage - 1))" 
                  :disabled="pagination.adminLeaves.unprocessed.currentPage === 1"
                  class="pagination-btn"
                >
                  上一页
                </button>
                
                <span 
                  v-for="page in generatePageNumbers(pagination.adminLeaves.unprocessed.pages, pagination.adminLeaves.unprocessed.currentPage)" 
                  :key="page"
                  @click="changeAdminLeavesPage(false, page)"
                  :class="['pagination-item', { active: page === pagination.adminLeaves.unprocessed.currentPage }]"
                >
                  {{ page }}
                </span>
                
                <button 
                  @click="changeAdminLeavesPage(false, Math.min(pagination.adminLeaves.unprocessed.pages, pagination.adminLeaves.unprocessed.currentPage + 1))" 
                  :disabled="pagination.adminLeaves.unprocessed.currentPage === pagination.adminLeaves.unprocessed.pages"
                  class="pagination-btn"
                >
                  下一页
                </button>
                
                <span class="pagination-info">
                  共筛选到 {{ pagination.adminLeaves.unprocessed.total }} 条记录，第 {{ pagination.adminLeaves.unprocessed.currentPage }} / {{ pagination.adminLeaves.unprocessed.pages }} 页
                </span>
              </div>
            </div>

            <div class="records-table" v-else>
              <table>
                <thead>
                  <tr>
                    <th>姓名</th>
                    <th>工号</th>
                    <th>起始时间</th>
                    <th>结束时间</th>
                    <th>事由</th>
                    <th>请假类型</th>
                    <th>状态</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in filteredProcessedLeaves" :key="item.id">
                    <td>{{ item.name }}</td>
                    <td>{{ item.account }}</td>
                    <td>{{ formatDateTime(item.start_time) }}</td>
                    <td>{{ formatDateTime(item.end_time) }}</td>
                    <td>{{ item.reason }}</td>
                    <td>{{ getLeaveTypeLabel(item.absence_type) }}</td>
                    <td>{{ statusMap[item.status] || item.status }}</td>
                  </tr>
                </tbody>
              </table>
              
              <!-- 分页控件 -->
              <div class="pagination" v-if="pagination.adminLeaves.processed.total > 0">
                <button 
                  @click="changeAdminLeavesPage(true, Math.max(1, pagination.adminLeaves.processed.currentPage - 1))" 
                  :disabled="pagination.adminLeaves.processed.currentPage === 1"
                  class="pagination-btn"
                >
                  上一页
                </button>
                
                <span 
                  v-for="page in generatePageNumbers(pagination.adminLeaves.processed.pages, pagination.adminLeaves.processed.currentPage)" 
                  :key="page"
                  @click="changeAdminLeavesPage(true, page)"
                  :class="['pagination-item', { active: page === pagination.adminLeaves.processed.currentPage }]"
                >
                  {{ page }}
                </span>
                
                <button 
                  @click="changeAdminLeavesPage(true, Math.min(pagination.adminLeaves.processed.pages, pagination.adminLeaves.processed.currentPage + 1))" 
                  :disabled="pagination.adminLeaves.processed.currentPage === pagination.adminLeaves.processed.pages"
                  class="pagination-btn"
                >
                  下一页
                </button>
                
                <span class="pagination-info">
                  共筛选到 {{ pagination.adminLeaves.processed.total }} 条记录，第 {{ pagination.adminLeaves.processed.currentPage }} / {{ pagination.adminLeaves.processed.pages }} 页
                </span>
              </div>
            </div>

            <div v-if="selectedLeave" class="leave-detail">
              <h3>申请详情</h3>
              <p>姓名：{{ selectedLeave.name }}（工号：{{ selectedLeave.account }}）</p>
              <p>起止：{{ formatDateTime(selectedLeave.start_time) }} - {{ formatDateTime(selectedLeave.end_time) }}</p>
              <p>事由：{{ selectedLeave.reason }}</p>
              <div class="detail-actions">
                <button class="clock-btn clock-in" @click="reviewLeave(selectedLeave.id, 'approve')">通过</button>
                <button class="clock-btn clock-out" @click="reviewLeave(selectedLeave.id, 'reject')">拒绝</button>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts';

export default {
  name: 'AdminPage',
  data() {
    return {
      activeTab: 'personal', // 默认显示个人考勤，管理员会在mounted中改为dashboard
      userProfile: {},
      apiBaseUrl: 'http://localhost:5000',
      dailyStats: {
        date: '',
        should_attend: 0,
        actual_attendance: 0,
        late_count: 0,
        early_leave_count: 0,
        normal_count: 0
      },
      employees: [],
      sortBy: 'account',
      sortOrder: 'asc',
      isLoading: false,
      personalStats: {
        should_attend: 0,
        total_days: 0,
        late_count: 0,
        early_leave_count: 0,
        normal_count: 0
      },
      recentRecords: [],
      currentTime: '',
      currentDate: '',
      clockLoading: false,
      clockMessage: '',
      clockMessageType: '',
      // 新增：请假数据
      leaveForm: { start_time: '', end_time: '', reason: '', absence_type: 0 },
      // 请假类型选项
      leaveTypes: [
        { value: 0, label: '病假' },
        { value: 1, label: '私事请假' },
        { value: 2, label: '公事请假' }
      ],
      myLeaves: [],
      leaveMessage: '',
      leaveMessageType: '',
      statusMap: { 0: '未读', 1: '拒绝', 2: '通过' },
      leaveAdminTab: 'unprocessed',
      adminLeavesUnprocessed: [],
      adminLeavesProcessed: [],
      selectedLeave: null,
      // 筛选相关字段
      nameFilter: '',
      typeFilter: -1, // -1表示全部类型
      // 分页相关数据
      pagination: {
        myLeaves: {
          currentPage: 1,
          total: 0,
          pages: 0,
          perPage: 10
        },
        adminLeaves: {
          unprocessed: {
            currentPage: 1,
            total: 0,
            pages: 0,
            perPage: 10
          },
          processed: {
            currentPage: 1,
            total: 0,
            pages: 0,
            perPage: 10
          }
        }
      }
    }
  },
  watch: {
    activeTab(newTab) {
      if (newTab === 'dashboard' && this.userProfile.role === '管理员') {
        this.$nextTick(() => {
          this.renderAttendanceCharts();
        });
      }
    },
    // 监听nameFilter变化
    nameFilter(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.resetAndRecalculatePagination();
      }
    },
    // 监听typeFilter变化
    typeFilter(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.resetAndRecalculatePagination();
      }
    },
  },
  async mounted() {
    this.updateTime();
    setInterval(this.updateTime, 1000);

    await this.loadUserProfile();
    if (this.userProfile.role === '管理员') {
      this.activeTab = 'dashboard';
      await this.loadDashboardData();
      this.$nextTick(() => {
        this.renderAttendanceCharts();
      });
    } else {
      this.activeTab = 'personal';
      await this.loadPersonalData();
    }

    // 如果人脸识别完跳回来，自动打卡
    if (this.$route.query.recognized === '1') {
      const type = this.$route.query.type; // clock_in / clock_out
      this.performClock(type); // 复用老接口
      this.$router.replace({ query: {} }); // 清参数，防止刷新重复
    }
  },
  methods: {
    // 重置分页到第一页
    resetPagination() {
      if (this.leaveAdminTab === 'unprocessed') {
        this.pagination.adminLeaves.unprocessed.currentPage = 1;
      } else {
        this.pagination.adminLeaves.processed.currentPage = 1;
      }
    },
    goFace(type) {
      this.$router.push({ name: 'FaceClock', params: { type } })
    },
    // 跳转到人脸录入页面
    goToFaceRegister() {
      this.$router.push({ name: 'FaceRegister' })
    },
    setActiveTab(tab) {
      // 检查权限
      if ((tab === 'dashboard' || tab === 'employees') && this.userProfile.role !== '管理员') {
        return
      }

      this.activeTab = tab
      if (tab === 'dashboard') {
        this.loadDashboardData()
      } else if (tab === 'employees') {
        this.loadEmployeesData()
      } else if (tab === 'personal') {
        this.loadPersonalData()
      } else if (tab === 'leave') {
        if (this.userProfile.role === '员工') {
          // 重置到第一页
          this.pagination.myLeaves.currentPage = 1
          this.loadMyLeaves(1)
        } else {
          // 重置到第一页
          this.pagination.adminLeaves.unprocessed.currentPage = 1
          this.loadAdminLeaves(false, 1)
        }
      }
    },

    async loadUserProfile() {
      try {
        const token = localStorage.getItem('access_token')
        const response = await fetch(`${this.apiBaseUrl}/user/profile`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        if (response.ok) {
          this.userProfile = await response.json()
        }
      } catch (error) {
        console.error('Failed to load user profile:', error)
      }
    },

    async loadDashboardData() {
      try {
        const token = localStorage.getItem('access_token')
        const response = await fetch(`${this.apiBaseUrl}/admin/attendance/daily`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        if (response.ok) {
          this.dailyStats = await response.json()
        }
      } catch (error) {
        console.error('Failed to load daily stats:', error)
      }
    },

    async loadEmployeesData() {
      // 增加加载状态
      this.isLoading = true; 
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${this.apiBaseUrl}/admin/attendance/employees?sort_by=${this.sortBy}&sort_order=${this.sortOrder}&page=${this.currentPage}&page_size=${this.pageSize}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (response.ok) {
          const data = await response.json();
          this.employees = data.employees || []; // 确保 employees 是数组
          this.totalEmployees = data.total || 0; // 确保 total 是数字
          console.log(data.employees);
        } else {
          console.error('Failed to load employees data:', await response.text());
        }
      } catch (error) {
        console.error('Failed to load employees data:', error);
      }
    },

    async loadPersonalData() {
      try {
        const token = localStorage.getItem('access_token')
        const response = await fetch(`${this.apiBaseUrl}/attendance/personal`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        if (response.ok) {
          const data = await response.json()
          this.personalStats = data.monthly_stats
          this.recentRecords = data.recent_records
        }
      } catch (error) {
        console.error('Failed to load personal data:', error)
      }
    },

    async clockIn() {
      await this.performClock('clock_in')
    },

    async clockOut() {
      await this.performClock('clock_out')
    },

    async performClock(type) {
      this.clockLoading = true
      this.clockMessage = ''

      try {
        const token = localStorage.getItem('access_token')
        const response = await fetch(`${this.apiBaseUrl}/attendance`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ type })
        })

        const data = await response.json()

        if (response.ok) {
          this.clockMessage = data.message
          this.clockMessageType = 'success'
          // 刷新数据
          this.loadDashboardData()
          this.loadPersonalData()
        } else {
          this.clockMessage = data.message || '打卡失败'
          this.clockMessageType = 'error'
        }
      } catch (error) {
        this.clockMessage = '网络错误'
        this.clockMessageType = 'error'
      } finally {
        this.clockLoading = false
        setTimeout(() => {
          this.clockMessage = ''
        }, 3000)
      }
    },

    // 请假相关
    async submitLeave() {
      this.leaveMessage = ''
      try {
        const token = localStorage.getItem('access_token')
        const res = await fetch(`${this.apiBaseUrl}/absence`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(this.leaveForm)
        })
        const data = await res.json()
        if (res.ok) {
          this.leaveMessage = data.message
          this.leaveMessageType = 'success'
          this.leaveForm = { start_time: '', end_time: '', reason: '' }
          this.loadMyLeaves()
        } else {
          this.leaveMessage = data.message || '提交失败'
          this.leaveMessageType = 'error'
        }
      } catch (e) {
        this.leaveMessage = '网络错误'
        this.leaveMessageType = 'error'
      }
    },

    async loadMyLeaves(page = 1) {
      try {
        const token = localStorage.getItem('access_token')
        const res = await fetch(`${this.apiBaseUrl}/absence/personal?page=${page}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        const data = await res.json()
        if (res.ok) {
          this.myLeaves = data.absences || []
          // 更新分页信息
          this.pagination.myLeaves.currentPage = data.current_page || 1
          this.pagination.myLeaves.total = data.total || 0
          this.pagination.myLeaves.pages = data.pages || 0
          this.pagination.myLeaves.perPage = data.per_page || 5
        }
      } catch (e) { console.error(e) }
    },

    async loadAdminLeaves(processed, page = 1) {
      try {
        const token = localStorage.getItem('access_token')
        // 构建查询参数
        let queryParams = `processed=${processed ? 'true' : 'false'}&page=${page}`
        
        // 添加过滤参数
        if (this.nameFilter) {
          queryParams += `&name=${encodeURIComponent(this.nameFilter)}`
        }
        if (this.typeFilter !== -1 && this.typeFilter !== '-1') {
          queryParams += `&absence_type=${this.typeFilter}`
        }
        
        // 使用后端分页和过滤，每页5条记录
        const res = await fetch(`${this.apiBaseUrl}/admin/absence?${queryParams}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        const data = await res.json()
        if (res.ok) {
          if (processed) {
            this.adminLeavesProcessed = data.absences || []
            // 使用后端返回的分页信息
            this.pagination.adminLeaves.processed.currentPage = data.current_page || 1
            this.pagination.adminLeaves.processed.total = data.total || 0
            this.pagination.adminLeaves.processed.pages = data.pages || 0
            this.pagination.adminLeaves.processed.perPage = data.per_page || 5
          } else {
            this.adminLeavesUnprocessed = data.absences || []
            // 使用后端返回的分页信息
            this.pagination.adminLeaves.unprocessed.currentPage = data.current_page || 1
            this.pagination.adminLeaves.unprocessed.total = data.total || 0
            this.pagination.adminLeaves.unprocessed.pages = data.pages || 0
            this.pagination.adminLeaves.unprocessed.perPage = data.per_page || 5
          }
        }
      } catch (e) { console.error(e) }
    },

    async reviewLeave(id, decision) {
      try {
        // 添加按钮点击反馈
        console.log('审核按钮被点击，ID:', id, '决定:', decision);
        
        const token = localStorage.getItem('access_token');
        if (!token) {
          alert('登录已过期，请重新登录');
          this.$router.push('/');
          return;
        }
        
        const res = await fetch(`${this.apiBaseUrl}/admin/absence/${id}`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ decision })
        });
        
        const data = await res.json();
        
        if (res.ok) {
          // 审核后刷新列表，保持当前页码
          const isProcessed = this.leaveAdminTab === 'processed';
          const currentPage = isProcessed ? 
            this.pagination.adminLeaves.processed.currentPage : 
            this.pagination.adminLeaves.unprocessed.currentPage;
          
          // 重新加载未处理列表（因为当前记录会被移到已处理列表）
          this.loadAdminLeaves(false, currentPage);
          
          // 如果当前在已处理标签页，也刷新已处理列表
          if (this.leaveAdminTab === 'processed') {
            this.loadAdminLeaves(true, this.pagination.adminLeaves.processed.currentPage);
          }
          
          this.selectedLeave = null;
          // 同步刷新个人考勤（如果涉及到本人）
          this.loadPersonalData();
        } else {
          // 服务器返回错误
          alert(data.message || '操作失败：服务器返回错误');
          console.error('审核失败:', data);
        }
      } catch (e) {
        // 网络或其他错误
        alert('操作失败：网络错误或服务器异常');
        console.error('审核请假时发生错误:', e);
      }
    },
    
    // 分页相关方法
    changeMyLeavesPage(page) {
      if (page >= 1 && page <= this.pagination.myLeaves.pages) {
        this.loadMyLeaves(page)
      }
    },
    
    changeAdminLeavesPage(processed, page) {
      const paginationKey = processed ? 'processed' : 'unprocessed'
      if (page >= 1 && page <= this.pagination.adminLeaves[paginationKey].pages) {
        this.loadAdminLeaves(processed, page)
      }
    },
    
    // 生成页码数组
    generatePageNumbers(totalPages, currentPage, maxVisible = 5) {
      const pages = []
      let start = Math.max(1, currentPage - Math.floor(maxVisible / 2))
      let end = Math.min(totalPages, start + maxVisible - 1)
      
      if (end - start + 1 < maxVisible) {
        start = Math.max(1, end - maxVisible + 1)
      }
      
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      return pages
    },
    
    // 重置分页到第一页
    resetAndRecalculatePagination() {
      if (this.leaveAdminTab === 'unprocessed') {
        this.pagination.adminLeaves.unprocessed.currentPage = 1;
        this.loadAdminLeaves(false, 1);
      } else {
        this.pagination.adminLeaves.processed.currentPage = 1;
        this.loadAdminLeaves(true, 1);
      }
    },

    updateTime() {
      const now = new Date()
      this.currentTime = now.toLocaleTimeString('zh-CN')
      this.currentDate = now.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'long'
      })
    },

    formatDate(dateString) {
      if (!dateString) return ''
      return new Date(dateString).toLocaleDateString('zh-CN')
    },

    formatDateTime(dateString) {
      if (!dateString) return ''
      const d = new Date(dateString)
      return d.toLocaleString('zh-CN', { hour12: false })
    },

    // 导出考勤数据为CSV
    exportAttendanceData() {
      // 准备CSV数据，添加BOM以支持Excel正确识别UTF-8编码的中文
      let csvContent = '\uFEFF姓名,工号,迟到次数,早退次数,正常次数\n';

      // 添加每个员工的数据
      this.employees.forEach(employee => {
        const row = [
          employee.name,
          employee.account,
          employee.monthly_stats.late_count,
          employee.monthly_stats.early_leave_count,
          employee.monthly_stats.normal_count
        ];
        csvContent += row.join(',') + '\n';
      });

      // 创建Blob对象
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });

      // 创建下载链接
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);

      // 设置文件名（使用当前年月）
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const fileName = `${year}年${month}月考勤统计.csv`;

      link.setAttribute('href', url);
      link.setAttribute('download', fileName);
      link.style.visibility = 'hidden';

      // 添加到DOM并触发下载
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // 释放URL对象
      URL.revokeObjectURL(url);
    },

    formatTime(dateString) {
      if (!dateString) return ''
      return new Date(dateString).toLocaleTimeString('zh-CN')
    },

    getStatusClass(status) {
      // 最近出勤记录的状态颜色：正常绿色、请假紫色、其它统一红色
      if (status === '正常') return 'status-normal'
      if (status === '请假') return 'status-leave'
      return 'status-bad'
    },

    logout() {
        localStorage.removeItem('access_token')
        this.$router.push('/')
      },
      // 获取请假类型标签
      getLeaveTypeLabel(type) {
        const leaveType = this.leaveTypes.find(t => t.value === type);
        return leaveType ? leaveType.label : '未知类型';
      },
      handlePageChange(newPage) {
        this.currentPage = newPage; // 更新当前页码
        this.loadEmployeesData(); // 重新加载数据
      },

      handlePageJump() {
        // 确保跳转的页码在有效范围内
        if (this.jumpToPage >= 1 && this.jumpToPage <= Math.ceil(this.totalEmployees / this.pageSize)) {
          this.currentPage = this.jumpToPage;
          this.loadEmployeesData();
        } else {
          alert("请输入有效的页码！");
        }
      },

      renderAttendanceChart() {
        const chartDom = document.getElementById('attendance-chart');
        const myChart = echarts.init(chartDom);
        const option = {
          title: {
            text: '本月考勤统计',
            left: 'center'
          },
          tooltip: {
            trigger: 'item'
          },
          legend: {
            bottom: '0%',
            left: 'center'
          },
          series: [
            {
              name: '考勤情况',
              type: 'pie',
              radius: '50%',
              data: [
                { value: this.dailyStats.actual_attendance, name: '实到人数' },
                { value: this.dailyStats.late_count, name: '迟到人数' },
                { value: this.dailyStats.early_leave_count, name: '早退人数' },
                { value: this.dailyStats.normal_count, name: '正常人数' },
                { value: this.dailyStats.should_attend - this.dailyStats.actual_attendance, name: '未到人数' }
              ],
              emphasis: {
                itemStyle: {
                  shadowBlur: 10,
                  shadowOffsetX: 0,
                  shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
              }
            }
          ]
        };
        option && myChart.setOption(option);
      },

      renderAttendanceCharts() {
        // 检查数据是否加载完成
        if (!this.dailyStats) {
          console.error('dailyStats 数据未加载完成');
          return;
        }

        // 图表 1: 实到人数和未到人数
        const chartDom1 = document.getElementById('attendance-chart-1');
        if (!chartDom1) {
          console.error('attendance-chart-1 容器未找到');
          return;
        }
        const chart1 = echarts.init(chartDom1);
        const option1 = {
          title: {
            text: '实到人数与未到人数',
            left: 'center'
          },
          tooltip: {
            trigger: 'item'
          },
          legend: {
            bottom: '0%',
            left: 'center'
          },
          series: [
            {
              name: '考勤情况',
              type: 'pie',
              radius: '50%',
              data: [
                { value: this.dailyStats.actual_attendance, name: '实到人数' },
                { value: this.dailyStats.should_attend - this.dailyStats.actual_attendance, name: '未到人数' }
              ],
              emphasis: {
                itemStyle: {
                  shadowBlur: 10,
                  shadowOffsetX: 0,
                  shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
              }
            }
          ]
        };
        chart1.setOption(option1);

        // 图表 2: 正常、迟到、早退、请假人数
        const chartDom2 = document.getElementById('attendance-chart-2');
        if (!chartDom2) {
          console.error('attendance-chart-2 容器未找到');
          return;
        }
        const chart2 = echarts.init(chartDom2);
        const option2 = {
          title: {
            text: '考勤详细统计',
            left: 'center'
          },
          tooltip: {
            trigger: 'item'
          },
          legend: {
            bottom: '0%',
            left: 'center'
          },
          series: [
            {
              name: '考勤情况',
              type: 'pie',
              radius: '50%',
              data: [
                { value: this.dailyStats.normal_count, name: '正常人数' },
                { value: this.dailyStats.late_count, name: '迟到人数' },
                { value: this.dailyStats.early_leave_count, name: '早退人数' },
                { value: this.dailyStats.leave_count, name: '请假人数' }
              ],
              emphasis: {
                itemStyle: {
                  shadowBlur: 10,
                  shadowOffsetX: 0,
                  shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
              }
            }
          ]
        };
        chart2.setOption(option2);
      }
  },
  computed: {
    // 未处理的请假申请（直接返回后端返回的数据）
    filteredUnprocessedLeaves() {
      return this.adminLeavesUnprocessed;
    },
    // 已处理的请假申请（直接返回后端返回的数据）
    filteredProcessedLeaves() {
      return this.adminLeavesProcessed;
    }
  }
}

</script>

<style scoped>
.admin-container {
  min-height: 100vh;
  background-color: #f5f6fa;
}

.header {
  background: white;
  padding: 16px 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #3498db;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: bold;
}

.user-details h3 {
  margin: 0;
  font-size: 18px;
}

.user-details p {
  margin: 4px 0 0 0;
  color: #666;
  font-size: 14px;
}

.logout-btn {
  padding: 8px 16px;
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

/* 分页样式 */
.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
}

.pagination-btn {
  padding: 6px 12px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.pagination-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.pagination-item {
  padding: 6px 12px;
  cursor: pointer;
  border-radius: 4px;
}

.pagination-item:hover {
  background: #f0f0f0;
}

.pagination-item.active {
  background: #3498db;
  color: white;
}

.pagination-info {
   margin-left: 10px;
   color: #666;
 }

.logout-btn:hover {
  background: #c0392b;
}

.main-content {
  display: flex;
  min-height: calc(100vh - 80px);
}

.sidebar {
  width: 240px;
  background: white;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

.nav-menu {
  padding: 24px 0;
}

.nav-item {
  padding: 16px 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all 0.2s;
}

.nav-item:hover {
  background: #f8f9fa;
}

.nav-item.active {
  background: #3498db;
  color: white;
}

.content-area {
  flex: 1;
  padding: 24px;
}

.tab-content {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin: 24px 0;
}

.stat-card {
  background: white;
  border: 1px solid #e1e8ed;
  border-radius: 8px;
  padding: 24px;
  text-align: center;
}

.stat-card.late {
  border-left: 4px solid #e74c3c;
}

.stat-card.early {
  border-left: 4px solid #f39c12;
}

.stat-card.normal {
  border-left: 4px solid #27ae60;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #2c3e50;
}

.stat-label {
  color: #7f8c8d;
  margin-top: 8px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.sort-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sort-controls select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.employees-table,
.records-table {
  overflow-x: auto;
}

.employees-table table,
.records-table table {
  width: 100%;
  border-collapse: collapse;
}

.employees-table th,
.employees-table td,
.records-table th,
.records-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e1e8ed;
}

.employees-table th,
.records-table th {
  background: #f8f9fa;
  font-weight: 600;
}

.status-present {
  color: #27ae60;
  font-weight: 500;
}

.status-absent {
  color: #e74c3c;
  font-weight: 500;
}

.late-count {
  color: #e74c3c;
  font-weight: 500;
}

.early-count {
  color: #f39c12;
  font-weight: 500;
}

.normal-count {
  color: #27ae60;
  font-weight: 500;
}

.personal-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.recent-records h3 {
  margin-bottom: 16px;
}

.status-normal {
  color: #27ae60;
  font-weight: 500;
}

.status-late {
  color: #e74c3c;
  font-weight: 500;
}

.status-early {
  color: #f39c12;
  font-weight: 500;
}

.status-leave {
  color: #8e44ad;
  font-weight: 500;
}

.status-bad {
  color: #e74c3c;
  font-weight: 500;
}

.clock-section {
  text-align: center;
  max-width: 400px;
  margin: 0 auto;
}

.current-time {
  margin-bottom: 32px;
}

.time-display {
  font-size: 48px;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 8px;
}

.date-display {
  font-size: 18px;
  color: #7f8c8d;
}

.clock-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-bottom: 24px;
}

.clock-btn {
  padding: 16px 32px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}


.leave-submit {
  padding: 10px 20px;
  font-size: 14px;
  background: #3498DB;
  color: #fff;
}


.section-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}

.export-btn {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.export-btn:hover {
  background-color: #45a049;
}

.export-btn:active {
  background-color: #3e8e41;
}

.clock-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.clock-in {
  background: #27ae60;
  color: white;
}

.clock-in:hover:not(:disabled) {
  background: #229954;
}

.clock-out {
  background: #3498db;
  color: white;
}

.clock-out:hover:not(:disabled) {
  background: #2980b9;
}


.records-table .clock-btn,
.detail-actions .clock-btn {
  padding: 10px 18px;
  font-size: 14px;
}

.clock-message {
  padding: 12px;
  border-radius: 4px;
  font-weight: 500;
}

.clock-message.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.clock-message.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.leave-form {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
  max-width: 480px;
}

.tab-switch {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.tab-switch button {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
}

.tab-switch button.active {
  background: #3498db;
  color: #fff;
}

.detail-actions {
  display: flex;
  gap: 16px;
  margin-top: 10px;
}

.date-info {
  margin-top: 16px;
  color: #7f8c8d;
  font-style: italic;
}

/* 管理员拒绝按钮设为红色，并扩大间距 */
.records-table td .clock-out {
  background: #e74c3c;
  color: #fff;
}

.records-table td .clock-out:hover:not(:disabled) {
  background: #c0392b;
}

.detail-actions .clock-out {
  background: #e74c3c;
  color: #fff;
}

.detail-actions .clock-out:hover:not(:disabled) {
  background: #c0392b;
}


.records-table td .clock-btn+.clock-btn {
  margin-left: 16px;
}

/* 人脸录入样式 */
.face-register-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  max-width: 600px;
  margin: 0 auto;
}

.register-info {
  width: 100%;
}

.info-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 24px;
  border-left: 4px solid #3498db;
}

.info-card h3 {
  margin: 0 0 16px 0;
  color: #2c3e50;
}

.info-card ul {
  margin: 0;
  padding-left: 20px;
}

.info-card li {
  margin-bottom: 8px;
  color: #555;
  line-height: 1.5;
}

.register-action {
  text-align: center;
}

.register-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 20px 40px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.register-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.btn-icon {
  font-size: 24px;
}

.btn-text {
  flex: 1;
}

.register-tips {
  margin-top: 16px;
  color: #7f8c8d;
  font-size: 14px;
}
</style>