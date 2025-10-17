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
          <div v-if="userProfile.role === '管理员'" class="nav-item" :class="{ active: activeTab === 'dashboard' }" @click="setActiveTab('dashboard')">
            <span>📊</span> 考勤概览
          </div>
          <div v-if="userProfile.role === '管理员'" class="nav-item" :class="{ active: activeTab === 'employees' }" @click="setActiveTab('employees')">
            <span>👥</span> 员工考勤
          </div>
          <div class="nav-item" :class="{ active: activeTab === 'personal' }" @click="setActiveTab('personal')">
            <span>👤</span> 个人考勤
          </div>
          <div class="nav-item" :class="{ active: activeTab === 'clock' }" @click="setActiveTab('clock')">
            <span>⏰</span> 打卡
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
                  <option value="name">姓名</option>
                  <option value="late_count">迟到次数</option>
                  <option value="early_leave_count">早退次数</option>
                  <option value="normal_count">正常次数</option>
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
                  <th>应出勤天数</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="employee in employees" :key="employee.user_id">
                  <td>{{ employee.name }}</td>
                  <td>{{ employee.account }}</td>
                  <td>
                    <span :class="employee.today_attendance > 0 ? 'status-present' : 'status-absent'">
                      {{ employee.today_attendance > 0 ? '已出勤' : '未出勤' }}
                    </span>
                  </td>
                  <td>{{ employee.monthly_stats.total_days }}</td>
                  <td class="late-count">{{ employee.monthly_stats.late_count }}</td>
                  <td class="early-count">{{ employee.monthly_stats.early_leave_count }}</td>
                  <td class="normal-count">{{ employee.monthly_stats.normal_count }}</td>
                  <td>{{ employee.monthly_stats.should_attend }}</td>
                </tr>
              </tbody>
            </table>
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
                    <td>{{ formatTime(record.clock_in_time) }}</td>
                    <td>{{ record.clock_out_time ? formatTime(record.clock_out_time) : '未打卡' }}</td>
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
               <button @click="goFace('clock_in')"  class="clock-btn clock-in">上班打卡</button>
               <button @click="goFace('clock_out')" class="clock-btn clock-out">下班打卡</button>
            </div>

            <div v-if="clockMessage" class="clock-message" :class="clockMessageType">
              {{ clockMessage }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
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
      sortBy: 'name',
      sortOrder: 'asc',
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
      clockMessageType: ''
    }
  },
  async mounted() {
    this.updateTime()
    setInterval(this.updateTime, 1000)
    
    await this.loadUserProfile()
    
    // 根据用户角色设置默认tab
    if (this.userProfile.role === '管理员') {
      this.activeTab = 'dashboard'
      await this.loadDashboardData()
    } else {
      this.activeTab = 'personal'
      await this.loadPersonalData()
    }
    // 如果人脸识别完跳回来，自动打卡
    if (this.$route.query.recognized === '1') {
      const type = this.$route.query.type // clock_in / clock_out
      await this.performClock(type)       // 复用老接口
      // 清参数，防止刷新重复
      await this.$router.replace({ query: {} })
    }
  },
  methods: {
    goFace(type) {
      this.$router.push({ name: 'FaceClock', params: { type } })
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
      try {
        const token = localStorage.getItem('access_token')
        const response = await fetch(`${this.apiBaseUrl}/admin/attendance/employees?sort_by=${this.sortBy}&sort_order=${this.sortOrder}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        if (response.ok) {
          const data = await response.json()
          this.employees = data.employees
        }
      } catch (error) {
        console.error('Failed to load employees data:', error)
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
      return {
        'status-normal': status === '正常',
        'status-late': status === '迟到',
        'status-early': status === '早退'
      }
    },
    
    logout() {
      localStorage.removeItem('access_token')
      this.$router.push('/')
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
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
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
  box-shadow: 2px 0 8px rgba(0,0,0,0.1);
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
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
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

.employees-table, .records-table {
  overflow-x: auto;
}

.employees-table table, .records-table table {
  width: 100%;
  border-collapse: collapse;
}

.employees-table th, .employees-table td,
.records-table th, .records-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e1e8ed;
}

.employees-table th, .records-table th {
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

/* 导出功能样式 */
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

.date-info {
  margin-top: 16px;
  color: #7f8c8d;
  font-style: italic;
}
</style>
