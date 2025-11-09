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
          <div v-if="userProfile.role === '员工'" class="nav-item" :class="{ active: activeTab === 'personal_info' }"
            @click="setActiveTab('personal_info')">
            <span>👤</span> 个人信息
          </div>
          <div v-if="userProfile.role === '员工'" class="nav-item" :class="{ active: activeTab === 'personal' }"
            @click="setActiveTab('personal')">
            <span>👤</span> 个人考勤
          </div>
          <div v-if="userProfile.role === '员工'" class="nav-item" :class="{ active: activeTab === 'clock' }"
            @click="setActiveTab('clock')">
            <span>⏰</span> 打卡
          </div>
          <div v-if="userProfile.role === '员工'" class="nav-item" :class="{ active: activeTab === 'face_register' }"
            @click="setActiveTab('face_register')">
            <span>📷</span> 人脸录入
          </div>
          <div v-if="userProfile.role === '管理员'" class="nav-item" :class="{ active: activeTab === 'face_review' }"
            @click="setActiveTab('face_review')">
            <span>👁️</span> 人脸录入审核
          </div>
          <div class="nav-item" :class="{ active: activeTab === 'leave' }" @click="setActiveTab('leave')">
            <span>📝</span> 请假
          </div>
          <div v-if="userProfile.role === '管理员'" class="nav-item"
            :class="{ active: activeTab === 'employee_management' }" @click="setActiveTab('employee_management')">
            <span>👔</span> 员工管理
          </div>
        </nav>
      </div>

      <!-- 右侧内容区域 -->
      <div v-if="activeTab !== 'leave'" class="content-area">
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
            <h3>今日考勤统计</h3>
            <div class="charts-row">
              <div id="attendance-chart-1" style="width: 100%; height: 400px;"></div>
              <div id="attendance-chart-2" style="width: 100%; height: 400px; margin-left: 20px;"></div>
            </div>
          </div>

          <!-- 阶段考勤统计 -->
          <div class="period-stats-container">
            <h3>阶段考勤统计</h3>
            <div class="date-picker-container">
              <div class="date-picker">
                <label>开始日期：</label>
                <input type="date" v-model="periodStats.startDate" @change="loadPeriodStats">
              </div>
              <div class="date-picker">
                <label>结束日期：</label>
                <input type="date" v-model="periodStats.endDate" @change="loadPeriodStats">
              </div>
            </div>
            <div class="charts-row">
              <div id="leave-trend-chart" style="width: 100%; height: 400px;"></div>
              <div id="attendance-trend-chart" style="width: 100%; height: 400px; margin-left: 20px;"></div>
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
                  <option value="account">工号</option>
                  <option value="name">姓名</option>
                  <option value="late_count">迟到次数</option>
                  <option value="early_leave_count">早退次数</option>
                  <option value="normal_count">正常次数</option>
                  <option value="leave_count">请假天数</option>
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
                  <th>请假天数</th>
                  <th>应出勤天数</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="employee in employees" :key="employee.user_id">
                  <td><span class="employee-name-link" @click="showEmployeeDetail(employee)">{{ employee.name }}</span>
                  </td>
                  <td>{{ employee.account }}</td>
                  <td>
                    <span
                      :class="(employee.on_leave_today ? 'status-leave' : (employee.is_absent_today ? 'status-absent' : (employee.today_attendance > 0 ? 'status-present' : 'status-absent')))">
                      {{ employee.on_leave_today ? '请假' : (employee.is_absent_today ? '未出勤' : (employee.today_attendance
                        > 0 ? '已出勤' : '未出勤')) }}
                    </span>
                  </td>
                  <td>{{ employee.monthly_stats?.total_days ?? 0 }}</td>
                  <td class="late-count">{{ employee.monthly_stats?.late_count ?? 0 }}</td>
                  <td class="early-count">{{ employee.monthly_stats?.early_leave_count ?? 0 }}</td>
                  <td class="normal-count">{{ employee.monthly_stats?.normal_count ?? 0 }}</td>
                  <td class="leave-count">{{ employee.monthly_stats?.leave_count ?? 0 }}</td>
                  <td>{{ employee.monthly_stats?.should_attend ?? 0 }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 员工详细考勤信息弹窗 -->
          <div v-if="showEmployeeDetailModal" class="employee-detail-modal" @click="closeEmployeeDetailModal">
            <div class="employee-detail-content" @click.stop>
              <div class="employee-detail-header">
                <div class="employee-detail-title">{{ selectedEmployee.name }} 的考勤详情</div>
                <button class="close-button" @click="closeEmployeeDetailModal">×</button>
              </div>

              <!-- 文字信息栏 -->
              <div class="employee-info-grid">
                <div class="info-item">
                  <div class="info-label">本月最早到岗时间</div>
                  <div class="info-value">{{ employeeDetail.earliestClockIn || '-' }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">本月最晚到岗时间</div>
                  <div class="info-value">{{ employeeDetail.latestClockIn || '-' }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">本月最早离岗时间</div>
                  <div class="info-value">{{ employeeDetail.earliestClockOut || '-' }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">本月最晚离岗时间</div>
                  <div class="info-value">{{ employeeDetail.latestClockOut || '-' }}</div>
                </div>
              </div>

              <!-- 异常考勤趋势图 -->
              <div class="chart-container">
                <div class="chart-title">异常考勤趋势</div>
                <div ref="abnormalAttendanceChart" style="width: 100%; height: 300px;" @mouseleave="hideTooltip"></div>
                <!-- 悬停提示框 -->
                <div v-if="tooltip.visible && tooltip.chartType === 'abnormal'" class="chart-tooltip"
                  :style="{ top: tooltip.top + 'px', left: tooltip.left + 'px' }">
                  {{ tooltip.content }}
                </div>
              </div>

              <!-- 请假趋势图 -->
              <div class="chart-container">
                <div class="chart-title">请假趋势</div>
                <div ref="leaveTrendChart" style="width: 100%; height: 300px;" @mouseleave="hideTooltip"></div>
                <!-- 悬停提示框 -->
                <div v-if="tooltip.visible && tooltip.chartType === 'leave'" class="chart-tooltip"
                  :style="{ top: tooltip.top + 'px', left: tooltip.left + 'px' }">
                  {{ tooltip.content }}
                </div>
              </div>
            </div>
          </div>

          <!-- 分页控件 -->
          <div class="pagination-wrapper" v-if="totalEmployees > 0">
            <div class="pagination-controls">
              <button :disabled="currentPage === 1" @click="handlePageChange(currentPage - 1)">上一页</button>
              <span>第 {{ currentPage }} 页 / 共 {{ Math.ceil(totalEmployees / pageSize) }} 页</span>
              <button :disabled="currentPage === Math.ceil(totalEmployees / pageSize)"
                @click="handlePageChange(currentPage + 1)">下一页</button>
            </div>
            <div class="pagination-controls">
              <span>跳转到第</span>
              <input type="number" v-model.number="jumpToPage" placeholder="跳转页码" min="1"
                :max="Math.ceil(totalEmployees / pageSize)" style="width: 60px; text-align: center; margin: 0 8px;" />
              <span>页</span>
              <button @click="handlePageJump">跳转</button>
            </div>
          </div>
        </div>

        <!-- 个人信息 -->
        <div v-if="activeTab === 'personal_info'" class="tab-content">
          <h2>个人信息</h2>
          <div class="personal-info-container">
            <!-- 头像上传区域 -->
            <div class="avatar-section">
              <div class="avatar-upload">
                <div class="avatar-preview">
                  <img :src="avatarBlobUrl" alt="头像" class="avatar-image" />
                  <div class="avatar-overlay" @click="triggerFileInput">
                    <span>更换头像</span>
                  </div>
                </div>
                <input type="file" ref="fileInput" @change="handleAvatarUpload" accept="image/jpeg,image/png,image/gif"
                  style="display: none" />
                <div class="upload-tips">
                  <p>支持 JPG、PNG格式，文件大小不超过 2MB</p>
                </div>
              </div>
            </div>
          </div>
          <!-- 个人信息表单 -->
          <div class="info-form-section">
            <div class="info-card">
              <h3>基本信息</h3>
              <form @submit.prevent="updateProfile" class="profile-form">
                <div class="form-row">
                  <div class="form-group">
                    <label>工号</label>
                    <input type="text" v-model="userInfo.account" disabled class="disabled-input" />
                  </div>
                  <div class="form-group">
                    <label>姓名</label>
                    <input type="text" v-model="userInfo.name" disabled class="disabled-input" />
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>职位</label>
                    <input type="text" v-model="userInfo.role" disabled class="disabled-input" />
                  </div>
                  <div class="form-group">
                    <label>密码</label>
                    <div class="password-field">
                      <input type="password" value="********" disabled class="disabled-input" />
                      <button type="button" class="modify-btn" @click="showPasswordModal = true">修改</button>
                    </div>
                  </div>
                </div>

                <div class="form-row">
                  <div class="form-group">
                    <label>人脸状态</label>
                    <div class="password-field">
                      <input type="text" v-model="faceStatus" disabled class="face-status-text" :class="{
                        'face-status-recorded': faceStatus === '已录入',
                        'face-status-pending': faceStatus === '待审核',
                        'face-status-not-recorded': faceStatus === '未录入'
                      }" />
                      <button v-if="faceStatus === '已录入'" type="button" class="modify-btn" @click="reEnrollFace"
                        :disabled="isReEnrolling">
                        {{ isReEnrolling ? '申请中...' : '申请重录' }}
                      </button>
                    </div>
                  </div>
                  <div class="form-group">
                    <label></label>
                    <span></span>
                  </div>
                </div>

                <h4 style="margin-top: 24px; margin-bottom: 16px; color: #333;">安全设置</h4>
                <div class="form-row">
                  <div class="form-group">
                    <label>密保问题 1</label>
                    <input type="text" v-model="userInfo.security_question_1" placeholder="请输入密保问题" />
                  </div>
                  <div class="form-group">
                    <label>答案 1</label>
                    <div class="password-field">
                      <input type="password" value="********" disabled class="disabled-input" />
                      <button type="button" class="modify-btn" @click="showAnswerModal(1)">修改</button>
                    </div>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>密保问题 2</label>
                    <input type="text" v-model="userInfo.security_question_2" placeholder="请输入密保问题" />
                  </div>
                  <div class="form-group">
                    <label>答案 2</label>
                    <div class="password-field">
                      <input type="password" value="********" disabled class="disabled-input" />
                      <button type="button" class="modify-btn" @click="showAnswerModal(2)">修改</button>
                    </div>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>密保问题 3</label>
                    <input type="text" v-model="userInfo.security_question_3" placeholder="请输入密保问题" />
                  </div>
                  <div class="form-group">
                    <label>答案 3</label>
                    <div class="password-field">
                      <input type="password" value="********" disabled class="disabled-input" />
                      <button type="button" class="modify-btn" @click="showAnswerModal(3)">修改</button>
                    </div>
                  </div>
                </div>

                <div class="form-actions">
                  <button type="submit" class="save-btn" :disabled="isSaving">
                    {{ isSaving ? '保存中...' : '保存信息' }}
                  </button>
                  <button type="button" @click="loadDetailedProfile" class="refresh-btn">
                    刷新信息
                  </button>
                </div>

                <div v-if="profileMessage" class="profile-message" :class="profileMessageType">
                  {{ profileMessage }}
                </div>
              </form>
            </div>
          </div>
        </div>
        <!-- 修改密码模态框 -->
        <div v-if="showPasswordModal" class="modal-overlay" @click="showPasswordModal = false">
          <div class="modal-content" @click.stop>
            <div class="modal-header">
              <h3>修改密码</h3>
              <button class="close-btn" @click="showPasswordModal = false">×</button>
            </div>
            <div class="modal-body">
              <div class="form-group">
                <label>原密码</label>
                <input type="password" v-model="passwordForm.oldPassword" placeholder="请输入原密码" />
              </div>
              <div class="form-group">
                <label>新密码</label>
                <input type="password" v-model="passwordForm.newPassword" placeholder="请输入新密码" />
              </div>
              <div class="form-group">
                <label>确认新密码</label>
                <input type="password" v-model="passwordForm.confirmPassword" placeholder="请再次输入新密码" />
              </div>
            </div>
            <div class="modal-actions">
              <button class="cancel-btn" @click="showPasswordModal = false">取消</button>
              <button class="confirm-btn" @click="updatePassword" :disabled="isUpdatingPassword">
                {{ isUpdatingPassword ? '修改中...' : '确认修改' }}
              </button>
            </div>
          </div>
        </div>
        <!-- 修改密保答案模态框 -->
        <div v-if="showAnswerSecurityModal" class="modal-overlay" @click="showAnswerSecurityModal = false">
          <div class="modal-content" @click.stop>
            <div class="modal-header">
              <h3>修改密保答案 {{ editingAnswerIndex }}</h3>
              <button class="close-btn" @click="showAnswerSecurityModal = false">×</button>
            </div>
            <div class="modal-body">
              <div class="form-group">
                <label>问题</label>
                <input type="text" :value="getQuestionText(editingAnswerIndex)" disabled class="disabled-input" />
              </div>
              <div class="form-group">
                <label>新答案</label>
                <input type="text" v-model="answerForm.newAnswer" placeholder="请输入新答案" />
              </div>
              <div class="form-group">
                <label>确认新答案</label>
                <input type="text" v-model="answerForm.confirmAnswer" placeholder="请再次输入新答案" />
              </div>
            </div>
            <div class="modal-actions">
              <button class="cancel-btn" @click="showAnswerSecurityModal = false">取消</button>
              <button class="confirm-btn" @click="updateSecurityAnswer" :disabled="isUpdatingAnswer">
                {{ isUpdatingAnswer ? '修改中...' : '确认修改' }}
              </button>
            </div>
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

        <!-- 人脸录入审核 -->
        <div v-if="activeTab === 'face_review' && userProfile.role === '管理员'" class="tab-content">
          <h2>人脸录入审核</h2>

          <!-- 标签切换 -->
          <div class="tab-switch">
            <button :class="{ active: faceReviewTab === 'pending' }"
              @click="faceReviewTab = 'pending'; loadPendingFaceEnrollments(1)">
              待审核
            </button>
            <button :class="{ active: faceReviewTab === 'processed' }"
              @click="faceReviewTab = 'processed'; loadReviewedFaceEnrollments(1)">
              已处理
            </button>
          </div>

          <!-- 筛选控件 -->
          <div class="filter-controls"
            style="margin: 15px 0; display: flex; justify-content: space-between; align-items: center;">
            <div>
              <input type="text" v-model="faceNameFilter" placeholder="搜索姓名"
                @input="faceReviewTab === 'pending' ? (isFaceBatchMode ? loadPendingFaceEnrollments(1, true) : loadPendingFaceEnrollments(1)) : loadReviewedFaceEnrollments(1)"
                style="margin-right: 10px; padding: 5px; width: 200px;" />
              <select v-model.number="faceStatusFilter" style="padding: 5px; margin-right: 10px;"
                v-if="faceReviewTab === 'processed'" @change="loadReviewedFaceEnrollments(1)">
                <option value="-1">全部状态</option>
                <option value="1">已通过</option>
                <option value="2">已拒绝</option>
              </select>
            </div>
            <div v-if="faceReviewTab === 'pending'">
              <div v-if="!isFaceBatchMode">
                <button class="clock-btn" style="background-color: #5dade2; padding: 8px 16px;"
                  @click="toggleFaceBatchMode">批量处理</button>
              </div>
              <div class="batch-actions" v-else style="display: flex; align-items: center; gap: 10px;">
                <span>已选择 {{ selectedFaceEnrollments.length }} 项</span>
                <button class="clock-btn clock-in" style="background-color: #27ae60; padding: 8px 16px;"
                  @click="batchReviewFaceEnrollments(true)">批量通过</button>
                <button class="clock-btn clock-out" style="background-color: #e74c3c; padding: 8px 16px;"
                  @click="batchReviewFaceEnrollments(false)">批量拒绝</button>
                <button class="clock-btn" style="background-color: #95a5a6; padding: 8px 16px;"
                  @click="toggleFaceBatchMode">退出</button>
              </div>
            </div>
          </div>

          <!-- 待审核列表 -->
          <div v-if="faceReviewTab === 'pending'" class="records-table">
            <div v-if="loadingPending" class="loading-state">加载中...</div>
            <template v-else>
              <table>
                <thead>
                  <tr>
                    <th v-if="isFaceBatchMode">选择</th>
                    <th>姓名</th>
                    <th>工号</th>
                    <th>提交时间</th>
                    <th>人脸照片</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="enrollment in pendingFaceEnrollments" :key="enrollment.id"
                    :class="{ 'selected-row': isFaceBatchMode && isFaceEnrollmentSelected(enrollment.id) }"
                    @click="isFaceBatchMode && toggleFaceEnrollmentSelection(enrollment.id)">
                    <td v-if="isFaceBatchMode" style="text-align: center;">
                      <input type="checkbox" :checked="isFaceEnrollmentSelected(enrollment.id)"
                        @click.stop="toggleFaceEnrollmentSelection(enrollment.id)" />
                    </td>
                    <td>{{ enrollment.user_name }}</td>
                    <td>{{ enrollment.user_account }}</td>
                    <td>{{ formatDateTime(enrollment.created_time) }}</td>
                    <td>
                      <div class="face-image-preview">
                        <img :src="getEnrollmentImageUrl(enrollment.image_path)" alt="人脸照片"
                          @click="showImagePreview(enrollment.image_path)" class="preview-image" />
                      </div>
                    </td>
                    <td v-if="!isFaceBatchMode">
                      <button class="clock-btn clock-in" @click="reviewFaceEnrollment(enrollment.id, true)">通过</button>
                      <button class="clock-btn clock-out"
                        @click="reviewFaceEnrollment(enrollment.id, false)">拒绝</button>
                    </td>
                    <td v-else>
                      <button class="clock-btn clock-in"
                        @click.stop="reviewFaceEnrollment(enrollment.id, true)">通过</button>
                      <button class="clock-btn clock-out"
                        @click.stop="reviewFaceEnrollment(enrollment.id, false)">拒绝</button>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-if="pendingFaceEnrollments.length === 0" class="empty-state">
                暂无待审核的申请
              </div>
            </template>

            <!-- 待审核列表分页控件 -->
            <div class="pagination" v-if="facePagination.pending.total > 0 && !isFaceBatchMode">
              <button @click="changePendingFacePage(facePagination.pending.currentPage - 1)"
                :disabled="facePagination.pending.currentPage === 1" class="pagination-btn">
                上一页
              </button>

              <span
                v-for="page in generatePageNumbers(facePagination.pending.pages, facePagination.pending.currentPage)"
                :key="page" @click="changePendingFacePage(page)"
                :class="['pagination-item', { active: page === facePagination.pending.currentPage }]">
                {{ page }}
              </span>

              <button @click="changePendingFacePage(facePagination.pending.currentPage + 1)"
                :disabled="facePagination.pending.currentPage === facePagination.pending.pages" class="pagination-btn">
                下一页
              </button>

              <span class="pagination-info">
                第 {{ facePagination.pending.currentPage }} 页，共 {{ facePagination.pending.pages }} 页，共 {{
                  facePagination.pending.total }} 条记录
              </span>
            </div>
          </div>

          <!-- 已处理列表 -->
          <div v-else class="records-table">
            <div v-if="loadingReviewed" class="loading-state">加载中...</div>
            <template v-else>
              <table>
                <thead>
                  <tr>
                    <th>姓名</th>
                    <th>工号</th>
                    <th>提交时间</th>
                    <th>审核时间</th>
                    <th>状态</th>
                    <th>审核意见</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="enrollment in filteredReviewedEnrollments" :key="enrollment.id">
                    <td>{{ enrollment.user_name }}</td>
                    <td>{{ enrollment.user_account }}</td>
                    <td>{{ formatDateTime(enrollment.created_time) }}</td>
                    <td>{{ formatDateTime(enrollment.reviewed_time) }}</td>
                    <td>
                      <span :class="getFaceEnrollmentStatusClass(enrollment.status)">
                        {{ getFaceEnrollmentStatusText(enrollment.status) }}
                      </span>
                    </td>
                    <td>{{ enrollment.review_comment || '-' }}</td>
                  </tr>
                </tbody>
              </table>
              <div v-if="filteredReviewedEnrollments.length === 0" class="empty-state">
                暂无已处理的申请
              </div>
            </template>

            <!-- 已处理列表分页控件 -->
            <div class="pagination" v-if="facePagination.reviewed.total > 0">
              <button @click="changeReviewedFacePage(facePagination.reviewed.currentPage - 1)"
                :disabled="facePagination.reviewed.currentPage === 1" class="pagination-btn">
                上一页
              </button>

              <span
                v-for="page in generatePageNumbers(facePagination.reviewed.pages, facePagination.reviewed.currentPage)"
                :key="page" @click="changeReviewedFacePage(page)"
                :class="['pagination-item', { active: page === facePagination.reviewed.currentPage }]">
                {{ page }}
              </span>

              <button @click="changeReviewedFacePage(facePagination.reviewed.currentPage + 1)"
                :disabled="facePagination.reviewed.currentPage === facePagination.reviewed.pages"
                class="pagination-btn">
                下一页
              </button>

              <span class="pagination-info">
                第 {{ facePagination.reviewed.currentPage }} 页，共 {{ facePagination.reviewed.pages }} 页，共 {{
                  facePagination.reviewed.total }} 条记录
              </span>
            </div>
          </div>

          <!-- 图片预览模态框 -->
          <div v-if="showPreview" class="image-preview-modal" @click="closeImagePreview">
            <div class="modal-content" @click.stop>
              <button class="close-btn" @click="closeImagePreview">×</button>
              <img :src="previewImageUrl" alt="预览图片" />
            </div>
          </div>
        </div>


        <div v-if="activeTab === 'employee_management' && userProfile.role === '管理员'" class="tab-content">
          <div class="section-header">
            <h2>员工管理</h2>
            <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 12px;">
              <input type="text" v-model="employeeSearch" placeholder="搜索姓名或工号" style="padding: 5px; width: 220px;" />
              <button v-if="!isBatchMode" @click="toggleBatchMode" class="batch-toggle-btn">批量操作</button>
              <div v-else style="display: flex; gap: 10px; align-items: center;">
                <button @click="batchDeleteEmployees" class="batch-delete-btn"
                  :disabled="selectedEmployees.length === 0">批量删除
                  ({{ selectedEmployees.length }})</button>
                <button @click="toggleBatchMode" class="batch-cancel-btn">取消</button>
              </div>
            </div>
          </div>
          <div class="employees-table" style="position: relative; width: 100%;">
            <table>
              <thead>
                <tr>
                  <th style="width: 5%;" v-if="isBatchMode"></th>
                  <th style="width: 5%;" v-else></th>
                  <th style="width: 20%;">姓名</th>
                  <th style="width: 20%;">工号</th>
                  <th style="width: 30%;">人脸照片</th>
                  <th style="width: 25%;">操作</th>
                </tr>
              </thead>
              <tbody>
                <!-- 批量模式下显示所有员工 -->
                <tr v-for="employee in (isBatchMode ? allEmployees : filteredEmployees)" :key="employee.user_id">
                  <template v-if="isBatchMode">
                    <td><input type="checkbox" :value="employee.user_id" v-model="selectedEmployees"></td>
                  </template>
                  <template v-else>
                    <td></td>
                  </template>
                  <td>{{ employee.name }}</td>
                  <td>{{ employee.account }}</td>
                  <td>
                    <img :src="getEmployeePhotoUrl(employee.photo_url)" alt="人脸照片"
                      style="width: 100px; height: 100px; object-fit: cover;" />
                  </td>
                  <td>
                    <button class="delete-btn" @click="deleteEmployee(employee.user_id, employee.name)">删除</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 常态下的分页控件 -->
          <div class="pagination" v-if="!isBatchMode && filteredEmployeesTotal > 0">
            <button @click="handlePageChange(currentPage - 1)" :disabled="currentPage === 1" class="pagination-btn">
              上一页
            </button>

            <span v-for="page in generatePageNumbers(Math.ceil(filteredEmployeesTotal / pageSize), currentPage)"
              :key="page" @click="handlePageChange(page)"
              :class="['pagination-item', { active: page === currentPage }]">
              {{ page }}
            </span>

            <button @click="handlePageChange(currentPage + 1)"
              :disabled="currentPage === Math.ceil(filteredEmployeesTotal / pageSize)" class="pagination-btn">
              下一页
            </button>

            <span class="pagination-info">
              共 {{ filteredEmployeesTotal }} 条记录，第 {{ currentPage }} / {{ Math.ceil(filteredEmployeesTotal / pageSize)
              }} 页
            </span>
          </div>
        </div>

        <!-- 出勤情况弹窗（含员工信息） -->
        <el-dialog title="出勤情况" v-model="attendanceDialogVisible" width="700px" :append-to-body="true"
          :modal-append-to-body="true" :close-on-click-modal="false">
          <div style="display: flex; gap: 32px; align-items: flex-start;">
            <!-- 左侧员工信息 -->
            <div style="min-width: 180px; text-align: center;">
              <img v-if="currentAttendanceEmployee && currentAttendanceEmployee.photo_url"
                :src="getEmployeePhotoUrl(currentAttendanceEmployee.photo_url)" alt="人脸照片"
                style="width: 100px; height: 100px; object-fit: cover; border-radius: 8px; margin-bottom: 12px;" />
              <div v-if="currentAttendanceEmployee">
                <div style="font-weight: bold; font-size: 18px; margin-bottom: 4px;">{{ currentAttendanceEmployee.name
                }}</div>
                <div style="color: #888; font-size: 15px;">工号：{{ currentAttendanceEmployee.account }}</div>
              </div>
            </div>
            <!-- 右侧出勤表格 -->
            <div style="flex: 1;">
              <el-table :data="attendance" style="width: 100%">
                <el-table-column prop="clock_in_time" label="签到时间" width="180"></el-table-column>
                <el-table-column prop="clock_out_time" label="签退时间" width="180"></el-table-column>
                <el-table-column prop="status" label="状态" width="100"></el-table-column>
              </el-table>
            </div>
          </div>
          <template #footer>
            <el-button @click="attendanceDialogVisible = false">关闭</el-button>
          </template>
        </el-dialog>
      </div>

      <!-- 请假（员工提交 / 管理员审核） -->
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
            <!-- 用户端历史请假记录页签和排序控件 -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
              <!-- 10px * 0.8 -->
              <div class="tab-switch">
                <button :class="{ active: myLeavesTab === 'pending' }"
                  @click="myLeavesTab = 'pending'; loadMyLeaves(1)">申请中</button>
                <button :class="{ active: myLeavesTab === 'approved' }"
                  @click="myLeavesTab = 'approved'; loadMyLeaves(1)">已通过</button>
                <button :class="{ active: myLeavesTab === 'rejected' }"
                  @click="myLeavesTab = 'rejected'; loadMyLeaves(1)">已拒绝</button>
              </div>

              <!-- 用户端历史请假记录排序控件 -->
              <div class="sort-controls" style="display: flex; align-items: center; gap: 8px;">
                <!-- 10px * 0.8 -->
                <label>排序方式:</label>
                <select v-model="myLeavesSortBy" @change="loadMyLeaves(1)" style="padding: 5px;">
                  <option value="start_time">起始时间</option>
                  <option value="end_time">结束时间</option>
                </select>
                <select v-model="myLeavesSortOrder" @change="loadMyLeaves(1)" style="padding: 5px;">
                  <option value="asc">正序</option>
                  <option value="desc">倒序</option>
                </select>
              </div>
            </div>

            <table>
              <thead>
                <tr>
                  <th>起始时间</th>
                  <th>结束时间</th>
                  <th>事由</th>
                  <th>请假类型</th>
                  <th>状态</th>
                  <th v-if="myLeavesTab === 'pending'">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in myLeaves" :key="item.id">
                  <td>{{ formatDateTime(item.start_time) }}</td>
                  <td>{{ formatDateTime(item.end_time) }}</td>
                  <td>{{ item.reason }}</td>
                  <td>{{ getLeaveTypeLabel(item.absence_type) }}</td>
                  <td>{{ statusMap[item.status] || item.status }}</td>
                  <td v-if="myLeavesTab === 'pending'">
                    <button class="clock-btn clock-out" @click="cancelLeave(item.id)">撤销</button>
                  </td>
                </tr>
              </tbody>
            </table>

            <!-- 分页控件 -->
            <div class="pagination" v-if="pagination.myLeaves.total > 0">
              <button @click="changeMyLeavesPage(pagination.myLeaves.currentPage - 1)"
                :disabled="pagination.myLeaves.currentPage === 1" class="pagination-btn">
                上一页
              </button>

              <span v-for="page in generatePageNumbers(pagination.myLeaves.pages, pagination.myLeaves.currentPage)"
                :key="page" @click="changeMyLeavesPage(page)"
                :class="['pagination-item', { active: page === pagination.myLeaves.currentPage }]">
                {{ page }}
              </span>

              <button @click="changeMyLeavesPage(pagination.myLeaves.currentPage + 1)"
                :disabled="pagination.myLeaves.currentPage === pagination.myLeaves.pages" class="pagination-btn">
                下一页
              </button>

              <span class="pagination-info">
                共 {{ pagination.myLeaves.total }} 条记录，第 {{ pagination.myLeaves.currentPage }} / {{
                  pagination.myLeaves.pages }} 页
              </span>
            </div>
          </div>
        </template>
        <template v-else>
          <h2>请假审核</h2>
          <div class="tab-switch">
            <button :class="{ active: leaveAdminTab === 'unprocessed' }"
              @click="leaveAdminTab = 'unprocessed'; loadAdminLeaves(false)">
              未处理
            </button>
            <button :class="{ active: leaveAdminTab === 'processed' }"
              @click="leaveAdminTab = 'processed'; loadAdminLeaves(true)">
              已处理
            </button>
          </div>

          <!-- 筛选控件 -->
          <div class="filter-controls"
            style="margin: 12px 0; display: flex; justify-content: space-between; align-items: center;">
            <!-- 15px * 0.8 -->
            <div style="display: flex; gap: 15px; align-items: center;">
              <div style="display: flex; flex-direction: column;">
                <input type="text" v-model="nameFilter" placeholder="请输入姓名"
                  style="padding: 8px; width: 180px; border: 1px solid #ddd; border-radius: 4px;" />
              </div>
              <div style="display: flex; flex-direction: column;">
                <select v-model="typeFilter"
                  style="padding: 8px; width: 150px; border: 1px solid #ddd; border-radius: 4px;">
                  <option value="-1">全部类型</option>
                  <option v-for="type in leaveTypes" :key="type.value" :value="type.value">{{ type.label }}</option>
                </select>
              </div>
            </div>
            <div v-if="leaveAdminTab === 'unprocessed'">
              <button class="batch-process-btn" @click="toggleBatchMode" v-if="!isBatchMode">
                批量处理
              </button>
              <div v-else style="display: flex; gap: 8px;">
                <!-- 10px * 0.8 -->
                <button class="batch-btn batch-approve" @click="batchReview('approve')"
                  :disabled="isBatchProcessing || selectedLeaves.length === 0">
                  {{ isBatchProcessing ? '处理中' : '批量通过' }}
                </button>
                <button class="batch-btn batch-reject" @click="batchReview('reject')"
                  :disabled="isBatchProcessing || selectedLeaves.length === 0">
                  {{ isBatchProcessing ? '处理中' : '批量拒绝' }}
                </button>
                <button class="batch-btn batch-exit" @click="toggleBatchMode">
                  退出
                </button>
              </div>
            </div>
          </div>

          <!-- 未处理标签页内容 -->
          <div class="records-table" v-if="leaveAdminTab === 'unprocessed'">
            <table>
              <thead>
                <tr>
                  <th v-if="isBatchMode">选择</th>
                  <th>姓名</th>
                  <th>工号</th>
                  <th>起始时间</th>
                  <th>结束时间</th>
                  <th>事由</th>
                  <th>请假类型</th>
                  <th v-if="!isBatchMode">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in filteredUnprocessedLeaves" :key="item.id">
                  <td v-if="isBatchMode">
                    <input type="checkbox" v-model="selectedLeaves" :value="item.id" class="batch-checkbox">
                  </td>
                  <td>{{ item.name }}</td>
                  <td>{{ item.account }}</td>
                  <td>{{ formatDateTime(item.start_time) }}</td>
                  <td>{{ formatDateTime(item.end_time) }}</td>
                  <td @click="selectedLeave = item" class="reason-cell">{{ item.reason }}</td>
                  <td>{{ getLeaveTypeLabel(item.absence_type) }}</td>
                  <td v-if="!isBatchMode">
                    <button class="clock-btn clock-in" @click.stop="reviewLeave(item.id, 'approve')">通过</button>
                    <button class="clock-btn clock-out" @click.stop="reviewLeave(item.id, 'reject')">拒绝</button>
                  </td>
                </tr>
              </tbody>
            </table>

            <!-- 未处理分页控件 -->
            <div class="pagination" v-if="pagination.adminLeaves.unprocessed.total > 0 && !isBatchMode">
              <button
                @click="changeAdminLeavesPage(false, Math.max(1, pagination.adminLeaves.unprocessed.currentPage - 1))"
                :disabled="pagination.adminLeaves.unprocessed.currentPage === 1" class="pagination-btn">
                上一页
              </button>

              <span
                v-for="page in generatePageNumbers(pagination.adminLeaves.unprocessed.pages, pagination.adminLeaves.unprocessed.currentPage)"
                :key="page" @click="changeAdminLeavesPage(false, page)"
                :class="['pagination-item', { active: page === pagination.adminLeaves.unprocessed.currentPage }]">
                {{ page }}
              </span>

              <button
                @click="changeAdminLeavesPage(false, Math.min(pagination.adminLeaves.unprocessed.pages, pagination.adminLeaves.unprocessed.currentPage + 1))"
                :disabled="pagination.adminLeaves.unprocessed.currentPage === pagination.adminLeaves.unprocessed.pages"
                class="pagination-btn">
                下一页
              </button>

              <span class="pagination-info">
                共筛选到 {{ pagination.adminLeaves.unprocessed.total }} 条记录，第 {{
                  pagination.adminLeaves.unprocessed.currentPage }} / {{ pagination.adminLeaves.unprocessed.pages }} 页
              </span>
            </div>
          </div>

          <!-- 已通过标签页内容 -->
          <div class="records-table" v-else-if="leaveAdminTab === 'approved'">
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
                <tr v-for="item in filteredApprovedLeaves" :key="item.id">
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

            <!-- 已通过分页控件 -->
            <div class="pagination" v-if="pagination.adminLeaves.approved.total > 0 && !isBatchMode">
              <button
                @click="changeAdminLeavesPage('approved', Math.max(1, pagination.adminLeaves.approved.currentPage - 1))"
                :disabled="pagination.adminLeaves.approved.currentPage === 1" class="pagination-btn">
                上一页
              </button>

              <span
                v-for="page in generatePageNumbers(pagination.adminLeaves.approved.pages, pagination.adminLeaves.approved.currentPage)"
                :key="page" @click="changeAdminLeavesPage('approved', page)"
                :class="['pagination-item', { active: page === pagination.adminLeaves.approved.currentPage }]">
                {{ page }}
              </span>

              <button
                @click="changeAdminLeavesPage('approved', Math.min(pagination.adminLeaves.approved.pages, pagination.adminLeaves.approved.currentPage + 1))"
                :disabled="pagination.adminLeaves.approved.currentPage === pagination.adminLeaves.approved.pages"
                class="pagination-btn">
                下一页
              </button>

              <span class="pagination-info">
                共筛选到 {{ pagination.adminLeaves.approved.total }} 条记录，第 {{
                  pagination.adminLeaves.approved.currentPage }} / {{ pagination.adminLeaves.approved.pages }} 页
              </span>
            </div>
          </div>

          <!-- 已处理标签页内容 -->
          <div class="records-table" v-else-if="leaveAdminTab === 'processed'">
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

            <!-- 已处理分页控件 -->
            <div class="pagination" v-if="pagination.adminLeaves.processed.total > 0 && !isBatchMode">
              <button
                @click="changeAdminLeavesPage(true, Math.max(1, pagination.adminLeaves.processed.currentPage - 1))"
                :disabled="pagination.adminLeaves.processed.currentPage === 1" class="pagination-btn">
                上一页
              </button>

              <span
                v-for="page in generatePageNumbers(pagination.adminLeaves.processed.pages, pagination.adminLeaves.processed.currentPage)"
                :key="page" @click="changeAdminLeavesPage(true, page)"
                :class="['pagination-item', { active: page === pagination.adminLeaves.processed.currentPage }]">
                {{ page }}
              </span>

              <button
                @click="changeAdminLeavesPage(true, Math.min(pagination.adminLeaves.processed.pages, pagination.adminLeaves.processed.currentPage + 1))"
                :disabled="pagination.adminLeaves.processed.currentPage === pagination.adminLeaves.processed.pages"
                class="pagination-btn">
                下一页
              </button>

              <span class="pagination-info">
                共筛选到 {{ pagination.adminLeaves.processed.total }} 条记录，第 {{
                  pagination.adminLeaves.processed.currentPage }} / {{ pagination.adminLeaves.processed.pages }} 页
              </span>
            </div>
          </div>

          <!-- 已拒绝标签页内容 -->
          <div class="records-table" v-else-if="leaveAdminTab === 'rejected'">
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
                <tr v-for="item in filteredRejectedLeaves" :key="item.id">
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

            <!-- 已拒绝分页控件 -->
            <div class="pagination" v-if="pagination.adminLeaves.rejected.total > 0 && !isBatchMode">
              <button
                @click="changeAdminLeavesPage('rejected', Math.max(1, pagination.adminLeaves.rejected.currentPage - 1))"
                :disabled="pagination.adminLeaves.rejected.currentPage === 1" class="pagination-btn">
                上一页
              </button>

              <span
                v-for="page in generatePageNumbers(pagination.adminLeaves.rejected.pages, pagination.adminLeaves.rejected.currentPage)"
                :key="page" @click="changeAdminLeavesPage('rejected', page)"
                :class="['pagination-item', { active: page === pagination.adminLeaves.rejected.currentPage }]">
                {{ page }}
              </span>

              <button
                @click="changeAdminLeavesPage('rejected', Math.min(pagination.adminLeaves.rejected.pages, pagination.adminLeaves.rejected.currentPage + 1))"
                :disabled="pagination.adminLeaves.rejected.currentPage === pagination.adminLeaves.rejected.pages"
                class="pagination-btn">
                下一页
              </button>

              <span class="pagination-info">
                共筛选到 {{ pagination.adminLeaves.rejected.total }} 条记录，第 {{
                  pagination.adminLeaves.rejected.currentPage }} / {{ pagination.adminLeaves.rejected.pages }} 页
              </span>
            </div>
          </div>

          <div v-if="selectedLeave" class="leave-detail leave-detail-center">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <h3>申请详情</h3>
              <button @click="selectedLeave = null"
                style="background: none; border: none; font-size: 24px; cursor: pointer; color: #999;">×</button>
            </div>
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
</template>

<script>
import * as echarts from 'echarts';
import { ElMessage, ElMessageBox } from 'element-plus';

export default {
  name: 'AdminPage',
  data() {
    return {
      activeTab: 'personal_info',
      userProfile: {},
      apiBaseUrl: '/api',
      dailyStats: {
        date: '',
        should_attend: 0,
        actual_attendance: 0,
        late_count: 0,
        early_leave_count: 0,
        normal_count: 0,
        leave_count: 0
      },
      employees: [],
      allEmployees: [], // 员工管理界面使用的所有员工数据
      employeeSearch: '', // 员工搜索关键词
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

      // 请假数据
      leaveForm: { start_time: '', end_time: '', reason: '', absence_type: 0 },
      leaveTypes: [
        { value: 0, label: '病假' },
        { value: 1, label: '私事请假' },
        { value: 2, label: '公事请假' }
      ],
      myLeaves: [],
      // 用户端历史请假记录页签
      myLeavesTab: 'pending', // pending: 申请中(未读), approved: 已通过, rejected: 已拒绝
      // 用户端历史请假记录排序
      myLeavesSortBy: 'start_time', // 默认按起始时间排序
      myLeavesSortOrder: 'desc', // 默认倒序
      leaveMessage: '',
      leaveMessageType: '',
      statusMap: { 0: '未读', 1: '拒绝', 2: '通过' },
      leaveAdminTab: 'unprocessed',
      adminLeavesUnprocessed: [],
      adminLeavesProcessed: [],
      adminLeavesApproved: [],  // 已通过的请假申请
      adminLeavesRejected: [],  // 已拒绝的请假申请
      selectedLeave: null,
      nameFilter: '',
      typeFilter: -1, // -1表示全部类型
      currentPage: 1,
      pageSize: 10,
      totalEmployees: 0,
      jumpToPage: 1,
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
          },
          approved: {
            currentPage: 1,
            total: 0,
            pages: 0,
            perPage: 10
          },
          rejected: {
            currentPage: 1,
            total: 0,
            pages: 0,
            perPage: 10
          }
        }
      },
      // 批量处理相关状态
      isBatchProcessing: false,
      isBatchMode: false,
      selectedLeaves: [], // 选中的请假申请ID数组
      selectedEmployees: [], // 选中的员工ID数组
      // 人脸审核相关
      faceReviewTab: 'pending',
      faceNameFilter: '',
      faceStatusFilter: -1,
      pendingFaceEnrollments: [],
      reviewedFaceEnrollments: [],
      showPreview: false,
      previewImageUrl: '',
      loadingPending: false,
      loadingReviewed: false,
      // 人脸审核分页相关
      facePagination: {
        pending: {
          currentPage: 1,
          total: 0,
          pages: 0,
          perPage: 10
        },
        reviewed: {
          currentPage: 1,
          total: 0,
          pages: 0,
          perPage: 10
        }
      },
      // 人脸审核批量处理相关
      isFaceBatchMode: false,
      selectedFaceEnrollments: [], // 选中的待审核人脸录入ID数组

      // 阶段考勤统计相关
      periodStats: {
        startDate: '',
        endDate: '',
        leaveTrendChart: null,
        attendanceTrendChart: null,
        phaseRanges: null
      },



      // 员工详细考勤信息弹窗相关
      showEmployeeDetailModal: false,
      selectedEmployee: null,
      employeeDetail: {
        earliestClockIn: '',
        latestClockIn: '',
        earliestClockOut: '',
        latestClockOut: '',
        attendanceTrendData: {
          weeks: [],
          late: [],
          earlyLeave: []
        }, // 异常考勤趋势数据
        leaveTrendData: {
          weeks: [],
          sickLeave: [],
          personalLeave: [],
          officialLeave: []
        } // 请假趋势数据
      },
      // 图表悬停提示框
      tooltip: {
        visible: false,
        content: '',
        top: 0,
        left: 0,
        chartType: '' // 'abnormal' 或 'leave'
      },
      // 图表实例
      attendanceTrendChartInstance: null,
      leaveTrendChartInstance: null,
      // 员工管理界面相关
      attendanceDialogVisible: false,
      currentAttendanceEmployee: null,

      //个人信息
      isUploading: false,
      avatarBlobUrl: '',
      isSaving: false,
      profileMessage: '',
      profileMessageType: '',
      userInfo: {},
      // 模态框状态
      showPasswordModal: false,
      showAnswerSecurityModal: false,
      editingAnswerIndex: 1,
      isUpdatingPassword: false,
      isUpdatingAnswer: false,
      // 表单数据
      passwordForm: {
        oldPassword: '',
        newPassword: '',
        confirmPassword: ''
      },
      answerForm: {
        newAnswer: '',
        confirmAnswer: ''
      },
      //人脸状态
      faceStatus: '未录入',
      isReEnrolling: false,
    }
  },
  watch: {
    activeTab(newTab) {
      if (newTab === 'dashboard' && this.userProfile.role === '管理员') {
        // 重新加载今日考勤统计数据并渲染饼图
        this.loadDashboardData().then(() => {
          this.$nextTick(() => {
            this.renderAttendanceCharts();
          });
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
    // 监听employeeSearch变化，搜索时重置分页状态
    employeeSearch(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.currentPage = 1; // 重置到第一页
      }
    },
  },
  async mounted() {
    this.updateTime()
    setInterval(this.updateTime, 1000)

    await this.loadUserProfile();
    if (this.userProfile.role === '管理员') {
      this.activeTab = 'dashboard';
      await this.loadDashboardData();
      this.$nextTick(() => {
        this.renderAttendanceCharts();
        // 加载阶段考勤统计数据
        this.loadPeriodStats();
      });
    } else {
      this.activeTab = 'personal_info';
      await this.loadPersonalInfo();
      await this.loadPersonalDataPure();
    }

    // 如果人脸识别完跳回来，自动打卡
    if (this.$route.query.recognized === '1') {
      const type = this.$route.query.type // clock_in / clock_out
      await this.performClock(type)
      await this.$router.replace({ query: {} })
    }
  },

  methods: {
    // 获取人脸状态
    async loadFaceStatus() {
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${this.apiBaseUrl}/user/face_status`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (response.ok) {
          const data = await response.json();
          if (data.ok) {
            this.faceStatus = data.status;
          }
        }
      } catch (error) {
        console.error('获取人脸状态失败:', error);
      }
    },

    // 申请重新录入人脸
    async reEnrollFace() {
      this.isReEnrolling = true;
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${this.apiBaseUrl}/user/face_re_enroll`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });
        const data = await response.json();
        if (response.ok && data.ok) {
          ElMessage.success('申请成功，请前往人脸录入页面');
          this.$router.push({ name: 'FaceRegister' });
        } else {
          ElMessage.error('申请失败，请重试');
        }
      } catch (error) {
        console.error('申请失败重新录入人脸失败:', error);
        ElMessage.error('网络错误，请重试');
      } finally {
        this.isReEnrolling = false;
      }
    },
    // 显示修改密保答案模态框
    showAnswerModal(index) {
      this.editingAnswerIndex = index;
      this.answerForm.newAnswer = '';
      this.answerForm.confirmAnswer = '';
      this.showAnswerSecurityModal = true;
    },
    // 获取问题文本
    getQuestionText(index) {
      const questions = {
        1: this.userInfo.security_question_1 || '未设置问题',
        2: this.userInfo.security_question_2 || '未设置问题',
        3: this.userInfo.security_question_3 || '未设置问题'
      };
      return questions[index];
    },
    // 修改密码
    async updatePassword() {
      if (!this.passwordForm.oldPassword) {
        ElMessage.error('请输入原密码');
        return;
      }
      if (!this.passwordForm.newPassword) {
        ElMessage.error('请输入新密码');
        return;
      }
      if (this.passwordForm.newPassword !== this.passwordForm.confirmPassword) {
        ElMessage.error('两次输入的新密码不一致');
        return;
      }
      this.isUpdatingPassword = true;
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${this.apiBaseUrl}/user/update_password`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            old_password: this.passwordForm.oldPassword,
            new_password: this.passwordForm.newPassword
          })
        });
        const data = await response.json();
        if (response.ok && data.ok) {
          ElMessage.success('密码修改成功');
          this.showPasswordModal = false;
          this.passwordForm = { oldPassword: '', newPassword: '', confirmPassword: '' };
        } else {
          ElMessage.error(data.msg || '密码修改失败');
        }
      } catch (error) {
        console.error('修改密码失败:', error);
        ElMessage.error('网络错误，请重试');
      } finally {
        this.isUpdatingPassword = false;
      }
    },
    // 修改密保答案
    async updateSecurityAnswer() {
      if (!this.answerForm.newAnswer) {
        ElMessage.error('请输入新答案');
        return;
      }
      if (this.answerForm.newAnswer !== this.answerForm.confirmAnswer) {
        ElMessage.error('两次输入的答案不一致');
        return;
      }
      this.isUpdatingAnswer = true;
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${this.apiBaseUrl}/user/update_security_answer`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            question_index: this.editingAnswerIndex,
            answer: this.answerForm.newAnswer
          })
        });
        const data = await response.json();
        if (response.ok && data.ok) {
          ElMessage.success('密保答案修改成功');
          this.showAnswerSecurityModal = false;
          this.answerForm = { newAnswer: '', confirmAnswer: '' };
          // 重新加载用户信息
          await this.loadDetailedProfile();
        } else {
          ElMessage.error(data.msg || '密保答案修改失败');
        }
      } catch (error) {
        console.error('修改密保答案失败:', error);
        ElMessage.error('网络错误，请重试');
      } finally {
        this.isUpdatingAnswer = false;
      }
    },
    // 加载个人信息
    async loadPersonalInfo() {
      await this.loadAvatarBlob();
      await this.loadDetailedProfile();
      await this.loadFaceStatus();
    },
    //加载头像
    async loadAvatarBlob() {
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${this.apiBaseUrl}/profile/avatar_pre`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (response.ok) {
          const blob = await response.blob();
          this.avatarBlobUrl = URL.createObjectURL(blob);
        } else {
          // 使用默认头像
          this.avatarBlobUrl = `${this.apiBaseUrl}/profile/temp.jpg`;
        }
      } catch (error) {
        console.error('加载头像失败:', error);
        this.avatarBlobUrl = `${this.apiBaseUrl}/profile/temp.jpg`;
      }
    },
    // 触发文件选择
    triggerFileInput() {
      this.$refs.fileInput.click();
    },
    // 处理头像上传
    async handleAvatarUpload(event) {
      const file = event.target.files[0];
      if (!file) {
        ElMessage.error('请上传文件');
        return;
      }
      // 文件类型检查
      const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
      if (!allowedTypes.includes(file.type)) {
        ElMessage.error('请上传 JPG、PNG 或 GIF 格式的图片');
        return;
      }
      // 文件大小检查 (2MB)
      if (file.size > 2 * 1024 * 1024) {
        ElMessage.error('图片大小不能超过 2MB');
        return;
      }
      this.isUploading = true;
      try {
        const formData = new FormData();
        formData.append('avatar', file);
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${this.apiBaseUrl}/user/avatar`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        });
        if (response.ok) {
          ElMessage.success('头像上传成功');
          //更新同步
          this.loadAvatarBlob();
        } else {
          ElMessage.error(response.msg);
        }
      } catch (error) {
        console.error('头像上传失败:', error);
        ElMessage.error('网络错误，请重试');
      } finally {
        this.isUploading = false;
        // 清空文件输入，允许重复选择同一文件
        event.target.value = '';
      }
    },

    // 加载详细信息
    async loadDetailedProfile() {
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${this.apiBaseUrl}/user/profile/detailed`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (response.ok) {
          const data = await response.json();
          if (data.ok) {
            // 合并基本信息和新获取的详细信息
            this.userInfo = data.profile;
            ElMessage.success('刷新成功')
          } else {
            ElMessage.error('加载个人信息失败');
          }
        } else {
          ElMessage.error('加载个人信息失败');
        }
      } catch (error) {
        console.error('加载详细信息失败:', error);
        ElMessage.error('网络错误，请重试');
      }
    },

    // 更新个人信息
    async updateProfile() {
      this.isSaving = true;
      this.profileMessage = '';
      try {
        const token = localStorage.getItem('access_token');
        const updateData = {
          name: this.userInfo.name,
          security_question_1: this.userInfo.security_question_1,
          security_question_2: this.userInfo.security_question_2,
          security_question_3: this.userInfo.security_question_3
        };
        const response = await fetch(`${this.apiBaseUrl}/user/profile/update`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(updateData)
        });
        const data = await response.json();
        if (response.ok && data.ok) {
          ElMessage.success('个人信息更新成功');
          // 重新加载确保数据同步
          await this.loadDetailedProfile();
        } else {
          ElMessage.error(data.msg);
        }
      } catch (error) {
        console.error('更新个人信息失败:', error);
        ElMessage.error('网络错误，请重试');
      } finally {
        this.isSaving = false;
      }
    },

    // 重置分页到第一页
    resetPagination() {
      if (this.leaveAdminTab === 'unprocessed') {
        this.pagination.adminLeaves.unprocessed.currentPage = 1;
      } else if (this.leaveAdminTab === 'approved') {
        this.pagination.adminLeaves.approved.currentPage = 1;
      } else if (this.leaveAdminTab === 'rejected') {
        this.pagination.adminLeaves.rejected.currentPage = 1;
      } else {
        this.pagination.adminLeaves.processed.currentPage = 1;
      }
    },
    goFace(type) {
      this.$router.push({ name: 'FaceClock', params: { type } })
    },

    goToFaceRegister() {
      this.$router.push({ name: 'FaceRegister' })
    },

    goToEmployeeManagement() {
      this.$router.push({ name: 'EmployeeManagement' })
    },

    setActiveTab(tab) {
      // 检查权限
      if ((tab === 'dashboard' || tab === 'employees') && this.userProfile.role !== '管理员') {
        return
      }

      this.activeTab = tab
      if (tab === 'dashboard') {
        // 重新加载今日考勤统计数据并渲染饼图
        this.loadDashboardData().then(() => {
          this.$nextTick(() => {
            this.renderAttendanceCharts();
          });
        });
        // 重新加载阶段考勤统计数据，确保在页签切换后数据能正确显示
        this.$nextTick(() => {
          this.loadPeriodStats();
        });
      } else if (tab === 'employees') {
        this.loadEmployeesData()
      } else if (tab === 'personal_info') {
        this.loadPersonalInfo()
      } else if (tab === 'employee_management') {
        this.loadEmployeesData_c(1)
      } else if (tab === 'personal') {
        this.loadPersonalDataPure()
      } else if (tab === 'face_review') {
        this.switchFaceReviewTab('pending')
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

    // 切换人脸审核标签页
    switchFaceReviewTab(tab) {
      this.faceReviewTab = tab
      this.faceNameFilter = ''
      this.faceStatusFilter = -1
      if (tab === 'pending') {
        this.loadPendingFaceEnrollments()
      } else {
        this.loadReviewedFaceEnrollments()
      }
    },

    // 处理筛选条件变化
    handleFaceFilterChange() {
      // 筛选逻辑已经在计算属性中处理，这里只需要确保数据已加载
      if (this.faceReviewTab === 'pending' && this.pendingFaceEnrollments.length === 0) {
        this.loadPendingFaceEnrollments()
      } else if (this.faceReviewTab === 'processed' && this.reviewedFaceEnrollments.length === 0) {
        this.loadReviewedFaceEnrollments()
      }
    },

    // 加载待审核的人脸录入申请（支持分页）
    async loadPendingFaceEnrollments(page = 1, loadAll = false) {
      this.loadingPending = true
      try {
        const token = localStorage.getItem('access_token')
        // 构建查询参数
        const params = new URLSearchParams()

        // 如果不是加载所有数据，则使用分页参数
        if (!loadAll) {
          params.append('page', page)
          params.append('page_size', this.facePagination.pending.perPage)
        } else {
          // 加载所有数据时，设置一个足够大的page_size
          params.append('page', 1)
          params.append('page_size', 10000) // 假设不会有超过10000条记录
        }

        // 添加姓名过滤参数
        if (this.faceNameFilter) {
          params.append('name', this.faceNameFilter)
        }

        const response = await fetch(`${this.apiBaseUrl}/admin/face-enrollments/pending?${params}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        if (response.ok) {
          const data = await response.json()
          this.pendingFaceEnrollments = data.enrollments || []
          // 更新分页信息（仅在非加载所有数据时）
          if (!loadAll) {
            this.facePagination.pending.currentPage = data.current_page || 1
            this.facePagination.pending.total = data.total || 0
            this.facePagination.pending.pages = data.pages || 0
          }
        } else {
          console.error('加载待审核列表失败，状态码:', response.status)
          ElMessage.error('加载待审核列表失败')
        }
      } catch (error) {
        console.error('Failed to load pending face enrollments:', error)
        ElMessage.error('加载待审核列表失败')
      } finally {
        this.loadingPending = false
      }
    },

    // 加载已审核的人脸录入申请（支持分页）
    async loadReviewedFaceEnrollments(page = 1) {
      this.loadingReviewed = true
      try {
        const token = localStorage.getItem('access_token')
        // 构建查询参数
        const params = new URLSearchParams({
          page: page,
          page_size: this.facePagination.reviewed.perPage
        })
        // 添加姓名过滤参数
        if (this.faceNameFilter) {
          params.append('name', this.faceNameFilter)
        }
        // 添加状态过滤参数（已处理页面只显示已审核的记录）
        if (this.faceStatusFilter !== -1) {
          params.append('status', this.faceStatusFilter)
        }

        const response = await fetch(`${this.apiBaseUrl}/admin/face-enrollments/all?${params}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        if (response.ok) {
          const data = await response.json()
          this.reviewedFaceEnrollments = data.enrollments || []
          // 更新分页信息
          this.facePagination.reviewed.currentPage = data.current_page || 1
          this.facePagination.reviewed.total = data.total || 0
          this.facePagination.reviewed.pages = data.pages || 0
        } else {
          console.error('加载已处理列表失败，状态码:', response.status)
          ElMessage.error('加载已处理列表失败')
        }
      } catch (error) {
        console.error('Failed to load reviewed face enrollments:', error)
        ElMessage.error('加载已处理列表失败')
      } finally {
        this.loadingReviewed = false
      }
    },

    // 获取人脸录入图片URL
    getEnrollmentImageUrl(imagePath) {
      if (imagePath && !imagePath.startsWith('http')) {
        return `${this.apiBaseUrl}/${imagePath}`
      }
      return imagePath
    },

    // 获取员工照片URL
    getEmployeePhotoUrl(imagePath) {
      if (!imagePath) {
        // 如果没有照片，返回默认图片或空字符串
        return '';
      }

      if (imagePath.startsWith('http')) {
        // 如果已经是完整URL，直接返回
        return imagePath;
      }

      // 否则，构造完整URL
      return `${this.apiBaseUrl}/${imagePath}`;
    },

    // 审核人脸录入申请
    async reviewFaceEnrollment(enrollmentId, approve) {
      try {
        const comment = approve ? '审核通过' : '图片不清晰或不符合要求'

        const token = localStorage.getItem('access_token')
        const response = await fetch(`${this.apiBaseUrl}/admin/face-enrollments/${enrollmentId}/review`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            approve: approve,
            comment: comment
          })
        })

        const data = await response.json()
        if (response.ok) {
          ElMessage.success(data.msg)
          // 重新加载列表
          if (this.faceReviewTab === 'pending') {
            this.loadPendingFaceEnrollments()
          } else {
            this.loadReviewedFaceEnrollments()
          }
        } else {
          ElMessage.error(data.msg || '审核失败')
        }
      } catch (error) {
        console.error('Review face enrollment failed:', error)
        ElMessage.error('网络错误，请重试')
      }
    },

    // 显示图片预览
    showImagePreview(imagePath) {
      this.previewImageUrl = this.getEnrollmentImageUrl(imagePath)
      this.showPreview = true
    },

    // 关闭图片预览
    closeImagePreview() {
      this.showPreview = false
      this.previewImageUrl = ''
    },

    // 获取人脸审核状态文本
    getFaceEnrollmentStatusText(status) {
      const statusMap = {
        0: '待审核',
        1: '已通过',
        2: '已拒绝'
      }
      return statusMap[status] || '未知状态'
    },

    // 获取人脸审核状态样式类
    getFaceEnrollmentStatusClass(status) {
      const classMap = {
        0: 'status-pending',
        1: 'status-approved',
        2: 'status-rejected'
      }
      return classMap[status] || 'status-pending'
    },

    // 人脸审核分页相关方法
    changePendingFacePage(page) {
      if (page >= 1 && page <= this.facePagination.pending.pages) {
        this.loadPendingFaceEnrollments(page)
      }
    },

    changeReviewedFacePage(page) {
      if (page >= 1 && page <= this.facePagination.reviewed.pages) {
        this.loadReviewedFaceEnrollments(page)
      }
    },

    // 生成分页数字数组
    generatePageNumbers(totalPages, currentPage) {
      const delta = 2
      const range = []
      for (let i = Math.max(1, currentPage - delta); i <= Math.min(totalPages, currentPage + delta); i++) {
        range.push(i)
      }

      // 添加省略号和边界页码
      if (range[0] > 1) {
        range.unshift('...')
        range.unshift(1)
      }
      if (range[range.length - 1] < totalPages) {
        range.push('...')
        range.push(totalPages)
      }

      return range
    },

    // 人脸审核批量处理相关方法
    async toggleFaceBatchMode() {
      this.isFaceBatchMode = !this.isFaceBatchMode;
      if (this.isFaceBatchMode) {
        // 进入批量模式时加载所有数据
        await this.loadPendingFaceEnrollments(1, true);
      } else {
        // 退出批量模式时清空选中项并恢复分页数据
        this.selectedFaceEnrollments = [];
        await this.loadPendingFaceEnrollments(this.facePagination.pending.currentPage);
      }
    },

    toggleFaceEnrollmentSelection(enrollmentId) {
      const index = this.selectedFaceEnrollments.indexOf(enrollmentId);
      if (index === -1) {
        // 未选中则添加
        this.selectedFaceEnrollments.push(enrollmentId);
      } else {
        // 已选中则移除
        this.selectedFaceEnrollments.splice(index, 1);
      }
    },

    isFaceEnrollmentSelected(enrollmentId) {
      return this.selectedFaceEnrollments.includes(enrollmentId);
    },

    async batchReviewFaceEnrollments(approved) {
      if (this.selectedFaceEnrollments.length === 0) {
        alert('请至少选择一条记录');
        return;
      }

      if (!confirm(`确定要${approved ? '通过' : '拒绝'}选中的 ${this.selectedFaceEnrollments.length} 条记录吗？`)) {
        return;
      }

      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${this.apiBaseUrl}/admin/face-enrollments/batch-review`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            enrollment_ids: this.selectedFaceEnrollments,
            approved: approved
          })
        });

        const data = await response.json();

        if (response.ok) {
          // 批量处理成功，重新加载数据
          this.selectedFaceEnrollments = []; // 清空选中项
          this.isFaceBatchMode = false; // 退出批量模式
          // 退出批量模式后恢复分页数据
          await this.loadPendingFaceEnrollments(this.facePagination.pending.currentPage);
          alert(`成功${approved ? '通过' : '拒绝'} ${data.success_count} 条记录`);
        } else {
          alert(data.message || '批量处理失败');
        }
      } catch (error) {
        console.error('Batch review error:', error);
        alert('网络错误，批量处理失败');
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
      this.isLoading = true
      try {
        const token = localStorage.getItem('access_token')
        const response = await fetch(`${this.apiBaseUrl}/admin/attendance/employees?sort_by=${this.sortBy}&sort_order=${this.sortOrder}&page=${this.currentPage}&page_size=${this.pageSize}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          const data = await response.json()
          this.employees = data.employees
          this.totalEmployees = data.total  // 设置总员工数用于分页控件显示
        } else {
          console.error('Failed to load data, status:', response.status)
          alert('加载员工数据失败！')
        }
      } catch (error) {
        console.error('Failed to load employees data:', error)
      } finally {
        this.isLoading = false
      }
    },
    async loadEmployeesData_c() {
      this.isLoading = true;
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${this.apiBaseUrl}/admin/attendance/employees?sort_by=${this.sortBy}&sort_order=${this.sortOrder}&page=1&page_size=10000`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          this.allEmployees = data.employees || [];
        } else {
          alert('加载员工数据失败！');
        }
      } catch (error) {
        console.error('Failed to load employees data:', error);
      } finally {
        this.isLoading = false;
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

    // 获取个人纯考勤数据（不包含请假相关内容）
    async loadPersonalDataPure() {
      try {
        const token = localStorage.getItem('access_token')
        const response = await fetch(`${this.apiBaseUrl}/attendance/personal/pure`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        if (response.ok) {
          const data = await response.json()
          // 更新最近记录
          this.recentRecords = data.recent_records
          // 更新考勤统计数据
          if (data.monthly_stats) {
            this.personalStats = data.monthly_stats
          }
        }
      } catch (error) {
        console.error('获取个人纯考勤数据失败:', error)
        this.$message.error('获取个人纯考勤数据失败')
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
          this.loadPersonalDataPure()
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
        // 根据当前页签确定状态参数
        let statusParam = '';
        if (this.myLeavesTab === 'pending') {
          statusParam = '&status=0'; // 未读
        } else if (this.myLeavesTab === 'approved') {
          statusParam = '&status=2'; // 已通过
        } else if (this.myLeavesTab === 'rejected') {
          statusParam = '&status=1'; // 已拒绝
        }

        // 添加排序参数
        const sortParam = `&sort_by=${this.myLeavesSortBy}&order=${this.myLeavesSortOrder}`;

        const res = await fetch(`${this.apiBaseUrl}/absence/personal?page=${page}${statusParam}${sortParam}`, {
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
      } catch (e) {
        console.error(e)
      }
    },

    async loadAdminLeaves(processed, page = 1, status = null) {
      try {
        const token = localStorage.getItem('access_token')
        // 构建查询参数
        let queryParams = `page=${page}`

        // 根据status参数决定查询条件
        if (status !== null) {
          // 按具体状态查询（已通过/已拒绝）
          queryParams += `&status=${status}`
        } else {
          // 兼容旧的processed参数
          queryParams += `&processed=${processed ? 'true' : 'false'}`
        }

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
          if (status === 2) {
            // 已通过的请假申请
            this.adminLeavesApproved = data.absences || []
            // 使用后端返回的分页信息
            this.pagination.adminLeaves.approved.currentPage = data.current_page || 1
            this.pagination.adminLeaves.approved.total = data.total || 0
            this.pagination.adminLeaves.approved.pages = data.pages || 0
            this.pagination.adminLeaves.approved.perPage = data.per_page || 5
          } else if (status === 1) {
            // 已拒绝的请假申请
            this.adminLeavesRejected = data.absences || []
            // 使用后端返回的分页信息
            this.pagination.adminLeaves.rejected.currentPage = data.current_page || 1
            this.pagination.adminLeaves.rejected.total = data.total || 0
            this.pagination.adminLeaves.rejected.pages = data.pages || 0
            this.pagination.adminLeaves.rejected.perPage = data.per_page || 5
          } else if (processed) {
            // 旧的已处理逻辑（兼容）
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
          this.loadPersonalDataPure();
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

    // 切换批量模式
    toggleBatchMode() {
      this.isBatchMode = !this.isBatchMode;
      this.selectedLeaves = []; // 清空选中列表
      this.selectedEmployees = []; // 清空选中的员工列表

      if (this.isBatchMode) {
        // 进入批量模式时加载所有员工数据
        this.loadEmployeesData_c();
        // 如果当前是请假审批标签页，加载所有未处理的请假申请
        if (this.activeTab === 'leave') {
          this.loadAllUnprocessedLeaves();
        }
      } else {
        // 退出批量模式时恢复分页加载
        this.loadEmployeesData();
        // 如果当前是请假审批标签页，恢复正常的分页加载
        if (this.activeTab === 'leave') {
          this.loadAdminLeaves(false, 1);
        }
      }
    },

    // 批量删除员工
    async batchDeleteEmployees() {
      if (this.selectedEmployees.length === 0) {
        ElMessage.warning('请至少选择一个员工进行删除');
        return;
      }

      try {
        await ElMessageBox.confirm(
          `确定要删除选中的 ${this.selectedEmployees.length} 名员工吗？此操作将永久删除这些员工及其所有相关信息，且无法恢复。`,
          '批量删除确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
            center: true
          }
        );

        // 用户点击了确定，执行批量删除操作
        const token = localStorage.getItem('access_token');

        // 使用批量删除API
        const response = await fetch(`${this.apiBaseUrl}/employees/batch`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            employee_ids: this.selectedEmployees
          })
        });

        const data = await response.json();

        if (response.ok && data.message) {
          ElMessage.success(data.message);
          // 清空选中列表
          this.selectedEmployees = [];
          // 重新加载员工数据
          await this.loadEmployeesData_c();
        } else {
          ElMessage.error(data.message || '批量删除失败');
        }
      } catch (error) {
        // 用户点击了取消按钮或出现其他错误
        if (error === 'cancel' || error === 'close') {
          // 用户取消操作，不显示错误消息
          return;
        }
        console.error('批量删除员工时发生错误:', error);
        ElMessage.error('批量删除失败: ' + (error.message || '未知错误'));
      }
    },

    // 加载所有未处理的请假申请（不分页）
    async loadAllUnprocessedLeaves() {
      try {
        const token = localStorage.getItem('access_token');
        if (!token) {
          alert('登录已过期，请重新登录');
          this.$router.push('/');
          return;
        }

        // 获取所有未处理的请假申请（不分页，显示全部）
        const res = await fetch(`${this.apiBaseUrl}/admin/absence?processed=false&page=1&page_size=10000`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (res.ok) {
          const data = await res.json();
          const absences = data.absences || [];

          if (absences.length === 0) {
            alert('没有未处理的请假申请');
            this.isBatchMode = false;
            return;
          }

          // 在批量模式下显示所有记录到一页中
          this.adminLeavesUnprocessed = absences;
          this.pagination.adminLeaves.unprocessed.currentPage = 1;
          this.pagination.adminLeaves.unprocessed.total = absences.length;
          this.pagination.adminLeaves.unprocessed.pages = 1;
          this.pagination.adminLeaves.unprocessed.perPage = absences.length;

        } else {
          const errorData = await res.json();
          alert(errorData.message || '获取未处理申请失败');
          this.isBatchMode = false;
        }
      } catch (error) {
        console.error('获取未处理申请失败:', error);
        alert('网络错误，请稍后重试');
        this.isBatchMode = false;
      }
    },

    // 批量审核请假申请
    async batchReview(decision) {
      if (this.isBatchProcessing || this.selectedLeaves.length === 0) return;

      this.isBatchProcessing = true;

      try {
        const token = localStorage.getItem('access_token');
        if (!token) {
          alert('登录已过期，请重新登录');
          this.$router.push('/');
          return;
        }

        // 确认批量处理
        const confirmMessage = `确定要批量${decision === 'approve' ? '通过' : '拒绝'} ${this.selectedLeaves.length} 条请假申请吗？`;
        if (!confirm(confirmMessage)) {
          this.isBatchProcessing = false;
          return;
        }

        // 使用批量API处理选中的请假申请
        const batchRes = await fetch(`${this.apiBaseUrl}/admin/absence/batch`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            decision: decision,
            absence_ids: this.selectedLeaves
          })
        });

        if (batchRes.ok) {
          const result = await batchRes.json();
          alert(result.message);

          // 处理成功后重新加载数据
          this.selectedLeaves = [];
          this.loadAllUnprocessedLeaves();

        } else {
          const errorData = await batchRes.json();
          alert(errorData.message || '批量处理失败');
        }
      } catch (error) {
        console.error('批量处理请假申请失败:', error);
        alert('网络错误，请稍后重试');
      } finally {
        this.isBatchProcessing = false;
      }
    },

    // 分页相关方法
    changeMyLeavesPage(page) {
      if (page >= 1 && page <= this.pagination.myLeaves.pages) {
        this.loadMyLeaves(page)
      }
    },

    changeAdminLeavesPage(processed, page) {
      let paginationKey, status;

      // 根据标签页确定分页键和状态参数
      if (this.leaveAdminTab === 'approved') {
        paginationKey = 'approved';
        status = 2; // 已通过
      } else if (this.leaveAdminTab === 'rejected') {
        paginationKey = 'rejected';
        status = 1; // 已拒绝
      } else {
        paginationKey = processed ? 'processed' : 'unprocessed';
        status = null; // 使用processed参数
      }

      if (page >= 1 && page <= this.pagination.adminLeaves[paginationKey].pages) {
        // 对于approved和rejected标签页，使用status参数
        if (status !== null) {
          this.loadAdminLeaves(null, page, status);
        } else {
          // 对于其他标签页，保持原有逻辑
          this.loadAdminLeaves(processed, page);
        }
      }
    },

    // 生成页码数组


    // 重置分页到第一页
    resetAndRecalculatePagination() {
      if (this.leaveAdminTab === 'unprocessed') {
        this.pagination.adminLeaves.unprocessed.currentPage = 1;
        this.loadAdminLeaves(false, 1);
      } else if (this.leaveAdminTab === 'approved') {
        this.pagination.adminLeaves.approved.currentPage = 1;
        this.loadAdminLeaves(null, 1, 2); // 已通过
      } else if (this.leaveAdminTab === 'rejected') {
        this.pagination.adminLeaves.rejected.currentPage = 1;
        this.loadAdminLeaves(null, 1, 1); // 已拒绝
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

    formatTime(dateString) {
      if (!dateString) return ''
      return new Date(dateString).toLocaleTimeString('zh-CN')
    },

    // 导出考勤数据为CSV
    exportAttendanceData() {
      let csvContent = '\uFEFF姓名,工号,迟到次数,早退次数,正常次数\n'

      this.employees.forEach(employee => {
        const row = [
          employee.name,
          employee.account,
          employee.monthly_stats.late_count,
          employee.monthly_stats.early_leave_count,
          employee.monthly_stats.normal_count
        ]
        csvContent += row.join(',') + '\n'
      })

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)

      const now = new Date()
      const year = now.getFullYear()
      const month = String(now.getMonth() + 1).padStart(2, '0')
      const fileName = `${year}年${month}月考勤统计.csv`

      link.setAttribute('href', url)
      link.setAttribute('download', fileName)
      link.style.visibility = 'hidden'

      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      URL.revokeObjectURL(url)
    },

    getStatusClass(status) {
      if (status === '正常') return 'status-normal'
      if (status === '请假') return 'status-leave'
      return 'status-bad'
    },

    logout() {
      localStorage.removeItem('access_token')
      this.$router.push('/')
    },

    getLeaveTypeLabel(type) {
      const leaveType = this.leaveTypes.find(t => t.value === type);
      return leaveType ? leaveType.label : '未知类型';
    },
    handlePageChange(newPage) {
      // 确保页码在有效范围内
      const totalPages = Math.ceil(this.filteredEmployeesTotal / this.pageSize);
      if (newPage >= 1 && newPage <= totalPages) {
        this.currentPage = newPage; // 更新当前页码
      }
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
    },

    // 加载阶段考勤统计数据
    async loadPeriodStats() {
      try {
        const token = localStorage.getItem('access_token');
        if (!token) {
          alert('登录已过期，请重新登录');
          this.$router.push('/');
          return;
        }

        // 如果没有选择日期，设置默认日期（近一个月）
        let startDate = this.periodStats.startDate;
        let endDate = this.periodStats.endDate;

        if (!startDate || !endDate) {
          const today = new Date();
          endDate = today.toISOString().split('T')[0];
          startDate = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

          // 更新数据模型中的日期
          this.periodStats.startDate = startDate;
          this.periodStats.endDate = endDate;
        }

        const response = await fetch(`${this.apiBaseUrl}/admin/attendance/period?start_date=${startDate}&end_date=${endDate}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          // 保存阶段时间范围数据
          this.periodStats.phaseRanges = data.phase_ranges;
          this.renderLeaveTrendChart(data.absence_stats);
          this.renderAttendanceTrendChart(data.attendance_stats);
        } else {
          const errorData = await response.json();
          alert(errorData.message || '获取阶段考勤统计数据失败');
        }
      } catch (error) {
        console.error('获取阶段考勤统计数据失败:', error);
        alert('网络错误，请稍后重试');
      }
    },

    // 渲染请假趋势统计折线图
    renderLeaveTrendChart(absenceStats) {
      const chartDom = document.getElementById('leave-trend-chart');
      if (!chartDom) {
        console.error('leave-trend-chart 容器未找到');
        return;
      }

      // 销毁之前的图表实例（如果存在）
      if (this.periodStats.leaveTrendChart) {
        this.periodStats.leaveTrendChart.dispose();
      }

      const chart = echarts.init(chartDom);
      this.periodStats.leaveTrendChart = chart;

      // 准备数据
      const stages = ['第一阶段', '第二阶段', '第三阶段'];
      const sickData = absenceStats.map(stage => stage.sick_leave);
      const personalData = absenceStats.map(stage => stage.personal_leave);
      const officialData = absenceStats.map(stage => stage.official_leave);

      // 定义阶段时间范围显示文本
      const getPhaseRangeText = (index) => {
        if (!this.periodStats.phaseRanges) return '';
        const phaseNames = ['第一阶段', '第二阶段', '第三阶段'];
        const phaseKey = phaseNames[index];
        const range = this.periodStats.phaseRanges[phaseKey];
        return range ? `\n${range.start} 至 ${range.end}` : '';
      };

      const option = {
        title: {
          text: '请假趋势统计',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            const stageIndex = params[0].dataIndex;
            const stageName = stages[stageIndex];
            const rangeText = getPhaseRangeText(stageIndex);

            let tooltipText = `${stageName}${rangeText}<br/>`;
            params.forEach(param => {
              tooltipText += `${param.marker} ${param.seriesName}: ${param.data}<br/>`;
            });
            return tooltipText;
          }
        },
        legend: {
          data: ['病假', '私事请假', '公事请假'],
          top: '10%'
        },
        xAxis: {
          type: 'category',
          data: stages
        },
        yAxis: {
          type: 'value',
          name: '人数',
          axisLabel: {
            formatter: '{value}'
          },
          splitNumber: 5,
          minInterval: 1
        },
        series: [
          {
            name: '病假',
            type: 'line',
            data: sickData,
            smooth: true,
            itemStyle: { color: '#5eb95e' } // 绿色
          },
          {
            name: '私事请假',
            type: 'line',
            data: personalData,
            smooth: true,
            itemStyle: { color: '#3b82f6' } // 深蓝色
          },
          {
            name: '公事请假',
            type: 'line',
            data: officialData,
            smooth: true,
            itemStyle: { color: '#f59e0b' } // 橙色
          }
        ]
      };

      chart.setOption(option);
    },

    // 渲染出勤趋势统计折线图
    renderAttendanceTrendChart(attendanceStats) {
      const chartDom = document.getElementById('attendance-trend-chart');
      if (!chartDom) {
        console.error('attendance-trend-chart 容器未找到');
        return;
      }

      // 销毁之前的图表实例（如果存在）
      if (this.periodStats.attendanceTrendChart) {
        this.periodStats.attendanceTrendChart.dispose();
      }

      const chart = echarts.init(chartDom);
      this.periodStats.attendanceTrendChart = chart;

      // 准备数据
      const stages = ['第一阶段', '第二阶段', '第三阶段'];
      const normalData = attendanceStats.map(stage => stage.normal);
      const lateData = attendanceStats.map(stage => stage.late);
      const earlyData = attendanceStats.map(stage => stage.early);
      const overtimeData = attendanceStats.map(stage => stage.overtime);

      // 定义阶段时间范围显示文本
      const getPhaseRangeText = (index) => {
        if (!this.periodStats.phaseRanges) return '';
        const phaseNames = ['第一阶段', '第二阶段', '第三阶段'];
        const phaseKey = phaseNames[index];
        const range = this.periodStats.phaseRanges[phaseKey];
        return range ? `\n${range.start} 至 ${range.end}` : '';
      };

      const option = {
        title: {
          text: '出勤趋势统计',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            const stageIndex = params[0].dataIndex;
            const stageName = stages[stageIndex];
            const rangeText = getPhaseRangeText(stageIndex);

            let tooltipText = `${stageName}${rangeText}<br/>`;
            params.forEach(param => {
              tooltipText += `${param.marker} ${param.seriesName}: ${param.data}<br/>`;
            });
            return tooltipText;
          }
        },
        legend: {
          data: ['正常', '迟到', '早退', '加班'],
          top: '10%'
        },
        xAxis: {
          type: 'category',
          data: stages
        },
        yAxis: {
          type: 'value',
          name: '人数',
          axisLabel: {
            formatter: '{value}'
          },
          splitNumber: 5,
          minInterval: 1
        },
        series: [
          {
            name: '正常',
            type: 'line',
            data: normalData,
            smooth: true,
            itemStyle: { color: '#3b82f6' } // 蓝色
          },
          {
            name: '迟到',
            type: 'line',
            data: lateData,
            smooth: true,
            itemStyle: { color: '#5eb95e' } // 绿色
          },
          {
            name: '早退',
            type: 'line',
            data: earlyData,
            smooth: true,
            itemStyle: { color: '#3b82f6' } // 深蓝色
          },
          {
            name: '加班',
            type: 'line',
            data: overtimeData,
            smooth: true,
            itemStyle: { color: '#f59e0b' } // 橙色
          }
        ]
      };

      chart.setOption(option);
    },

    // 显示员工详细考勤信息弹窗
    async showEmployeeDetail(employee) {
      this.selectedEmployee = employee;

      try {
        const token = localStorage.getItem('access_token');
        if (!token) {
          alert('登录已过期，请重新登录');
          this.$router.push('/');
          return;
        }

        console.log('请求URL:', `${this.apiBaseUrl}/admin/attendance/employee/${employee.user_id}`);

        const response = await fetch(`${this.apiBaseUrl}/admin/attendance/employee/${employee.user_id}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        console.log('响应状态:', response.status);
        console.log('响应状态文本:', response.statusText);

        if (response.ok) {
          const data = await response.json();
          console.log('响应数据:', data);

          // 设置员工详细信息
          this.employeeDetail = {
            earliestClockIn: data.earliestClockIn,
            latestClockIn: data.latestClockIn,
            earliestClockOut: data.earliestClockOut,
            latestClockOut: data.latestClockOut,
            attendanceTrendData: data.attendanceTrendData,
            leaveTrendData: data.leaveTrendData
          };
        } else {
          console.error('获取员工详细信息失败:', response.status, response.statusText);
          const errorText = await response.text();
          console.error('错误详情:', errorText);
          // 如果获取失败，显示错误信息，不使用模拟数据
          alert(`获取员工详细信息失败: ${response.status} ${response.statusText}\n${errorText}`);
          return;
        }
      } catch (error) {
        console.error('获取员工详细信息时发生错误:', error);
        // 如果发生错误，显示错误信息，不使用模拟数据
        alert(`获取员工详细信息时发生网络错误，请检查网络连接后重试\n错误信息: ${error.message}\n错误堆栈: ${error.stack}`);
        return;
      }

      this.showEmployeeDetailModal = true;

      // 渲染图表
      this.$nextTick(() => {
        this.renderAbnormalAttendanceChart();
        this.renderEmployeeLeaveTrendChart();
      });
    },

    // 关闭员工详细考勤信息弹窗
    closeEmployeeDetailModal() {
      this.showEmployeeDetailModal = false;
      this.selectedEmployee = null;
      // 重置employeeDetail为初始结构
      this.employeeDetail = {
        earliestClockIn: '',
        latestClockIn: '',
        earliestClockOut: '',
        latestClockOut: '',
        attendanceTrendData: {
          weeks: [],
          late: [],
          earlyLeave: [],
          overtime: []
        },
        leaveTrendData: {
          weeks: [],
          sickLeave: [],
          personalLeave: [],
          officialLeave: []
        }
      };

      // 销毁图表实例
      if (this.attendanceTrendChartInstance) {
        this.attendanceTrendChartInstance.dispose();
        this.attendanceTrendChartInstance = null;
      }
      if (this.leaveTrendChartInstance) {
        this.leaveTrendChartInstance.dispose();
        this.leaveTrendChartInstance = null;
      }
    },

    // 撤销请假申请
    async cancelLeave(id) {
      try {
        // 确认撤销操作
        const confirmed = confirm('确定要撤销这条请假申请吗？');
        if (!confirmed) return;

        const token = localStorage.getItem('access_token');
        if (!token) {
          alert('登录已过期，请重新登录');
          this.$router.push('/');
          return;
        }

        const res = await fetch(`${this.apiBaseUrl}/absence/${id}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        const data = await res.json();

        if (res.ok) {
          // 撤销成功后刷新列表
          this.loadMyLeaves(this.pagination.myLeaves.currentPage);
          alert(data.message || '撤销成功');
        } else {
          // 服务器返回错误
          alert(data.message || '撤销失败：服务器返回错误');
          console.error('撤销失败:', data);
        }
      } catch (e) {
        // 网络或其他错误
        alert('撤销失败：网络错误或服务器异常');
        console.error('撤销请假时发生错误:', e);
      }
    },

    // 渲染异常考勤趋势图
    renderAbnormalAttendanceChart() {
      // 检查数据是否存在
      if (!this.employeeDetail || !this.employeeDetail.attendanceTrendData) {
        console.warn('员工详细考勤信息未加载或数据结构不正确');
        return;
      }

      const chartDom = this.$refs.abnormalAttendanceChart;
      if (!chartDom) {
        console.error('abnormalAttendanceChart 容器未找到');
        return;
      }

      // 销毁之前的图表实例（如果存在）
      if (this.attendanceTrendChartInstance) {
        this.attendanceTrendChartInstance.dispose();
      }

      const chart = echarts.init(chartDom);
      this.attendanceTrendChartInstance = chart;

      // 准备数据
      const weeks = this.employeeDetail.attendanceTrendData.weeks;
      const lateData = this.employeeDetail.attendanceTrendData.late;
      const earlyLeaveData = this.employeeDetail.attendanceTrendData.earlyLeave;
      const overtimeData = this.employeeDetail.attendanceTrendData.overtime;

      const option = {
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            // params是一个数组，包含所有系列在该点的数据
            if (params.length > 0) {
              const dataIndex = params[0].dataIndex;
              // 确保索引有效
              if (dataIndex >= 0 && dataIndex < weeks.length) {
                const weekRange = weeks[dataIndex];
                let tooltipText = `${weekRange}<br/>`;
                params.forEach(param => {
                  tooltipText += `${param.marker} ${param.seriesName}: ${param.data}<br/>`;
                });
                return tooltipText;
              }
            }
            return '';
          }
        },
        legend: {
          data: ['迟到次数', '早退次数', '加班次数'],
          top: '10%'
        },
        xAxis: {
          type: 'category',
          data: weeks
        },
        yAxis: {
          type: 'value',
          name: '次数',
          axisLabel: {
            formatter: '{value}'
          },
          splitNumber: 5,
          minInterval: 1
        },
        series: [
          {
            name: '迟到次数',
            type: 'line',
            data: lateData,
            smooth: true,
            itemStyle: { color: '#f59e0b' } // 橙色
          },
          {
            name: '早退次数',
            type: 'line',
            data: earlyLeaveData,
            smooth: true,
            itemStyle: { color: '#3b82f6' } // 蓝色
          },
          {
            name: '加班次数',
            type: 'line',
            data: overtimeData,
            smooth: true,
            itemStyle: { color: '#8b5cf6' } // 紫色
          }
        ]
      };

      chart.setOption(option);
    },

    // 渲染请假趋势图
    renderEmployeeLeaveTrendChart() {
      // 检查数据是否存在
      if (!this.employeeDetail || !this.employeeDetail.leaveTrendData) {
        console.warn('员工详细考勤信息未加载或数据结构不正确');
        return;
      }

      const chartDom = this.$refs.leaveTrendChart;
      if (!chartDom) {
        console.error('leaveTrendChart 容器未找到');
        return;
      }

      // 销毁之前的图表实例（如果存在）
      if (this.leaveTrendChartInstance) {
        this.leaveTrendChartInstance.dispose();
      }

      const chart = echarts.init(chartDom);
      this.leaveTrendChartInstance = chart;

      // 准备数据
      const weeks = this.employeeDetail.leaveTrendData.weeks;
      const sickLeaveData = this.employeeDetail.leaveTrendData.sickLeave;
      const personalLeaveData = this.employeeDetail.leaveTrendData.personalLeave;
      const officialLeaveData = this.employeeDetail.leaveTrendData.officialLeave;

      const option = {
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            // params是一个数组，包含所有系列在该点的数据
            if (params.length > 0) {
              const dataIndex = params[0].dataIndex;
              // 确保索引有效
              if (dataIndex >= 0 && dataIndex < weeks.length) {
                const weekRange = weeks[dataIndex];
                let tooltipText = `${weekRange}<br/>`;
                params.forEach(param => {
                  tooltipText += `${param.marker} ${param.seriesName}: ${param.data}<br/>`;
                });
                return tooltipText;
              }
            }
            return '';
          }
        },
        legend: {
          data: ['病假', '私事请假', '公事请假'],
          top: '10%'
        },
        xAxis: {
          type: 'category',
          data: weeks
        },
        yAxis: {
          type: 'value',
          name: '次数',
          axisLabel: {
            formatter: '{value}'
          },
          splitNumber: 5,
          minInterval: 1
        },
        series: [
          {
            name: '病假',
            type: 'line',
            data: sickLeaveData,
            smooth: true,
            itemStyle: { color: '#5eb95e' } // 绿色
          },
          {
            name: '私事请假',
            type: 'line',
            data: personalLeaveData,
            smooth: true,
            itemStyle: { color: '#3b82f6' } // 蓝色
          },
          {
            name: '公事请假',
            type: 'line',
            data: officialLeaveData,
            smooth: true,
            itemStyle: { color: '#f59e0b' } // 橙色
          }
        ]
      };

      chart.setOption(option);
    },

    // 显示图表悬停提示
    showTooltip(event, chartType, dataIndex) {
      // 获取对应图表的数据
      let weeksData = [];
      if (chartType === 'abnormal' && this.employeeDetail.attendanceTrendData) {
        weeksData = this.employeeDetail.attendanceTrendData.weeks;
      } else if (chartType === 'leave' && this.employeeDetail.leaveTrendData) {
        weeksData = this.employeeDetail.leaveTrendData.weeks;
      }

      // 确保有数据且索引有效
      if (weeksData.length > 0 && dataIndex >= 0 && dataIndex < weeksData.length) {
        const weekRange = weeksData[dataIndex];
        // 显示"第x周"在上一行，日期范围在下一行
        const weekNumber = dataIndex + 1;
        this.tooltip.content = `第${weekNumber}周\n${weekRange}`;
        this.tooltip.chartType = chartType;
        this.tooltip.visible = true;

        // 计算提示框位置
        const rect = event.currentTarget.getBoundingClientRect();
        this.tooltip.top = rect.top - 40;
        this.tooltip.left = rect.left + (rect.width / 2) - 50;
      }
    },

    // 隐藏提示框
    hideTooltip() {
      this.tooltip.visible = false;
    },

    // 删除员工方法
    async deleteEmployee(employeeId, employeeName) {
      // 显示确认对话框
      try {
        await ElMessageBox.confirm(
          `确定要删除员工 "${employeeName}" 吗？此操作将永久删除该员工及其所有相关信息，且无法恢复。`,
          '删除确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
            center: true
          }
        );

        // 用户点击了确定，执行删除操作
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${this.apiBaseUrl}/employees/${employeeId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        const data = await response.json();

        if (response.ok && data.message) {
          ElMessage.success(data.message);
          // 重新加载员工数据
          await this.loadEmployeesData_c(1);
        } else {
          ElMessage.error(data.message || '删除失败');
        }
      } catch (error) {
        // 用户点击了取消按钮或出现其他错误
        if (error === 'cancel' || error === 'close') {
          // 用户取消操作，不显示错误消息
          return;
        }
        console.error('删除员工时发生错误:', error);
        ElMessage.error('删除失败: ' + (error.message || '未知错误'));
      }
    }
  },
  computed: {
    filteredEmployees() {
      let list = this.allEmployees || [];
      if (this.employeeSearch && this.employeeSearch.trim()) {
        const keyword = this.employeeSearch.trim().toLowerCase();
        list = list.filter(emp =>
          (emp.name && emp.name.toLowerCase().includes(keyword)) ||
          (emp.account && emp.account.toLowerCase().includes(keyword))
        );
      }
      // 分页
      const start = (this.currentPage - 1) * this.pageSize;
      const end = start + this.pageSize;
      return list.slice(start, end);
    },
    filteredEmployeesTotal() {
      let list = this.allEmployees || [];
      if (this.employeeSearch && this.employeeSearch.trim()) {
        const keyword = this.employeeSearch.trim().toLowerCase();
        list = list.filter(emp =>
          (emp.name && emp.name.toLowerCase().includes(keyword)) ||
          (emp.account && emp.account.toLowerCase().includes(keyword))
        );
      }
      return list.length;
    },
    // 过滤后的待审核申请
    filteredPendingEnrollments() {
      return this.pendingFaceEnrollments.filter(enrollment => {
        return enrollment.user_name.toLowerCase().includes(this.faceNameFilter.toLowerCase()) ||
          enrollment.user_account.toLowerCase().includes(this.faceNameFilter.toLowerCase())
      })
    },
    // 过滤后的已审核申请
    filteredReviewedEnrollments() {
      return this.reviewedFaceEnrollments.filter(enrollment => {
        const nameMatch = enrollment.user_name.toLowerCase().includes(this.faceNameFilter.toLowerCase()) ||
          enrollment.user_account.toLowerCase().includes(this.faceNameFilter.toLowerCase())
        const statusMatch = this.faceStatusFilter === -1 || enrollment.status === this.faceStatusFilter
        return nameMatch && statusMatch
      })
    },
    // 未处理的请假申请（直接返回后端返回的数据）
    filteredUnprocessedLeaves() {
      return this.adminLeavesUnprocessed;
    },
    // 已处理的请假申请（直接返回后端返回的数据）
    filteredProcessedLeaves() {
      return this.adminLeavesProcessed;
    },
    // 已通过的请假申请
    filteredApprovedLeaves() {
      return this.adminLeavesApproved;
    },
    // 已拒绝的请假申请
    filteredRejectedLeaves() {
      return this.adminLeavesRejected;
    }
  }
}
</script>

<style scoped>
.admin-container {
  min-height: 100vh;
  background-color: #f5f6fa;
}

/* 批量操作按钮样式 */
.batch-toggle-btn {
  padding: 6px 12px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.batch-toggle-btn:hover {
  background-color: #337ecc;
}

.batch-select-all-btn,
.batch-clear-selection-btn {
  padding: 6px 12px;
  background-color: #67c23a;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.batch-select-all-btn:hover,
.batch-clear-selection-btn:hover {
  background-color: #55a030;
}

.batch-delete-btn {
  padding: 6px 12px;
  background-color: #f56c6c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.batch-delete-btn:hover:not(:disabled) {
  background-color: #d9534f;
}

.batch-delete-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.batch-cancel-btn {
  padding: 6px 12px;
  background-color: #909399;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.batch-cancel-btn:hover {
  background-color: #73767a;
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
  margin-top: 12px;
  /* 15px * 0.8 */
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  /* 10px * 0.8 */
}

/* 图表提示框样式 */
.chart-tooltip {
  position: fixed;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 14px;
  z-index: 1000;
  pointer-events: none;
  white-space: pre-line;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.pagination-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  /* 20px * 0.8 */
  margin: 24px 0;
  /* 30px * 0.8 */
}

.pagination-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  /* 15px * 0.8 */
}

.pagination-btn {
  padding: 4.8px 9.6px;
  /* 6px * 0.8, 12px * 0.8 */
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
  padding: 4.8px 9.6px;
  /* 6px * 0.8, 12px * 0.8 */
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
  margin-left: 8px;
  /* 10px * 0.8 */
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
  display: block;
  position: relative;
}

/* 让请假审核详情在content-area下全宽居中显示，避免与tab-content并排 */
.leave-detail-center {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  padding: 24px 32px;
  z-index: 10;
}

.tab-content {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  flex: 1 1 0%;
  min-width: 0;
  width: 100%;
  box-sizing: border-box;
  align-self: stretch;
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
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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

.charts-row {
  display: flex;
  justify-content: space-between;
  gap: 20px;
}

.charts-row>div {
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 20px;
}

.period-stats-container {
  margin-top: 30px;
  padding: 20px;
}

.date-picker-container {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.date-picker {
  display: flex;
  align-items: center;
  gap: 10px;
}

.date-picker label {
  font-weight: 500;
}

.date-picker input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
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
  /* 移除滚动条 */
  overflow: visible;
}

.employees-table table,
.records-table table {
  width: 100%;
  border-collapse: collapse;
  /* 固定表格布局，防止内容变化导致列宽变化 */
  table-layout: fixed;
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
  padding: 8px 16px;
  /* 10px * 0.8, 20px * 0.8 */
  font-size: 14px;
  background: #3498DB;
  color: #fff;
  margin-top: 8px;
  /* 10px * 0.8 */
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

/* 批量处理按钮样式 */
.batch-process-btn {
  background: #5dade2;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.3s;
}

.batch-process-btn:hover:not(:disabled) {
  background: #3498db;
}

.batch-process-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
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
  gap: 9.6px;
  /* 12px * 0.8 */
  margin-bottom: 9.6px;
  /* 12px * 0.8 */
}

.tab-switch button {
  padding: 6.4px 9.6px;
  /* 8px * 0.8, 12px * 0.8 */
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
}

.tab-switch button.active {
  background: #3498db;
  color: #fff;
}

.batch-confirm-area {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 16px 0;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.batch-confirm-btn {
  padding: 8px 16px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.batch-confirm-btn:hover:not(:disabled) {
  background: #2980b9;
}

.batch-confirm-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.batch-selected-info {
  color: #666;
  font-size: 14px;
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

/* 员工管理删除按钮样式 */
.delete-btn {
  padding: 8px 16px;
  font-size: 14px;
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.delete-btn:hover:not(:disabled) {
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

/* 批量处理按钮样式 */
.batch-btn {
  padding: 6.4px 12.8px;
  /* 8px * 0.8, 16px * 0.8 */
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  margin-left: 8px;
  /* 10px * 0.8 */
}

.batch-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.batch-approve {
  background: #28a745;
  color: white;
}

.batch-approve:hover:not(:disabled) {
  background: #218838;
}

.batch-reject {
  background: #dc3545;
  color: white;
}

.batch-reject:hover:not(:disabled) {
  background: #c82333;
}

.batch-processing {
  background: #6c757d;
  color: white;
}

.batch-exit {
  background: #6c757d;
  color: white;
}

.batch-exit:hover:not(:disabled) {
  background: #5a6268;
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

/* 请假事由列样式 */
.reason-cell {
  cursor: pointer;
  color: #007bff;
}


.reason-cell:hover {
  text-decoration: underline;
}

/* 员工姓名链接样式 */
.employee-name-link {
  cursor: pointer;
  color: #007bff;
  text-decoration: none;
}

.employee-name-link:hover {
  color: #0056b3;
}

/* 请假表单控件样式 */
.leave-form input[type="datetime-local"],
.leave-form textarea,
.leave-form select {
  width: 100%;
  padding: 4px;
  margin: 4px 0 8px 0;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
  background-color: #fff;
}

.leave-form input[type="datetime-local"]:focus,
.leave-form textarea:focus,
.leave-form select:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 1.92px rgba(52, 152, 219, 0.2);
  /* 2.4px * 0.8 */
}

.leave-form label {
  display: block;
  margin-top: 7.68px;
  /* 9.6px * 0.8 */
  font-weight: 500;
  color: #333;
}

/* 管理员页面筛选控件样式 */
.filter-controls select {
  width: 150%;
  /* 增加为原本的1.5倍 */
  padding: 6.4px;
  /* 8px * 0.8 */
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.filter-controls input[type="text"] {
  padding: 6.4px;
  /* 8px * 0.8 */
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

/* 人脸审核特定样式 */
.face-image-preview {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid #e1e8ed;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.2s;
}

.preview-image:hover {
  transform: scale(1.1);
}

.image-preview-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  position: relative;
  max-width: 90%;
  max-height: 90%;
}

.modal-content img {
  max-width: 100%;
  max-height: 90vh;
  border-radius: 8px;
}

.close-btn {
  position: absolute;
  top: -40px;
  right: 0;
  background: none;
  border: none;
  color: white;
  font-size: 30px;
  cursor: pointer;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 人脸审核状态样式 */
.status-pending {
  color: #f39c12;
  font-weight: 500;
  color: #333;
}

.status-rejected {
  color: #e74c3c;
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #7f8c8d;
  font-style: italic;
}

.loading-state {
  text-align: center;
  padding: 40px;
  color: #3498db;
  font-style: italic;
}

/* 个人信息样式 */
.personal-info-container {
  display: flex;
  gap: 32px;
  margin-top: 24px;
}

.avatar-section {
  flex: 0 0 200px;
}

.avatar-upload {
  text-align: center;
}

.avatar-preview {
  position: relative;
  width: 150px;
  height: 150px;
  margin: 0 auto 16px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid #e1e8ed;
  cursor: pointer;
  transition: all 0.3s ease;
}

.avatar-preview:hover {
  border-color: #3498db;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
  color: white;
  font-size: 14px;
}

.avatar-preview:hover .avatar-overlay {
  opacity: 1;
}

.upload-tips {
  font-size: 12px;
  color: #7f8c8d;
  line-height: 1.4;
}

/* 个人信息表单样式 */
.info-form-section {
  flex: 1;
}

.info-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 24px;
  border-left: 4px solid #3498db;
}

.profile-form {
  margin-top: 16px;
}

.form-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.form-group {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.form-group label {
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-group input {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

.disabled-input {
  background-color: #f5f5f5;
  color: #666;
  cursor: not-allowed;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e1e8ed;
}

.save-btn,
.refresh-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.save-btn {
  background: #27ae60;
  color: white;
}

.save-btn:hover:not(:disabled) {
  background: #229954;
}

.save-btn:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.refresh-btn {
  background: #3498db;
  color: white;
}

.refresh-btn:hover {
  background: #2980b9;
}

.profile-message {
  margin-top: 16px;
  padding: 12px;
  border-radius: 6px;
  font-weight: 500;
}

.profile-message.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.profile-message.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .personal-info-container {
    flex-direction: column;
  }

  .avatar-section {
    flex: none;
    margin-bottom: 24px;
  }

  .form-row {
    flex-direction: column;
    gap: 12px;
  }
}

/* 密码字段样式 */
.password-field {
  position: relative;
  display: flex;
  align-items: center;
}

.password-field input {
  flex: 1;
  margin-right: 8px;
}

.modify-btn {
  padding: 8px 12px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  white-space: nowrap;
}

.modify-btn:hover {
  background: #2980b9;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 400px;
  max-width: 90%;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e1e8ed;
}

.modal-header h3 {
  margin: 0;
  color: #2c3e50;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #7f8c8d;
}

.close-btn:hover {
  color: #e74c3c;
}

.modal-body {
  padding: 20px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e1e8ed;
}

.cancel-btn,
.confirm-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.cancel-btn {
  background: #95a5a6;
  color: white;
}

.cancel-btn:hover {
  background: #7f8c8d;
}

.confirm-btn {
  background: #27ae60;
  color: white;
}

.confirm-btn:hover:not(:disabled) {
  background: #229954;
}

.confirm-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .password-field {
    flex-direction: column;
    align-items: stretch;
  }

  .password-field input {
    margin-right: 0;
    margin-bottom: 8px;
  }

  .modal-content {
    width: 95%;
  }
}

/* 人脸状态输入框样式 */
.face-status-field {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.face-status-text {
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 500;
  font-size: 14px;
  border: 1px solid #ddd;
  background-color: #f5f5f5;
  color: #333;
  text-align: center;
  width: 100px;
  /* 固定宽度使其看起来更整齐 */
}

/* 已录入 - 绿色 */
.face-status-text.face-status-recorded {
  background: #d4edda;
  color: #155724;
  border-color: #c3e6cb;
}

/* 待审核 - 黄色 */
.face-status-text.face-status-pending {
  background: #fff3cd;
  color: #856404;
  border-color: #ffeaa7;
}

/* 未录入 - 红色 */
.face-status-text.face-status-not-recorded {
  background: #f8d7da;
  color: #721c24;
  border-color: #f5c6cb;
}

/* 员工详细考勤信息弹窗样式 */
.employee-detail-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.employee-detail-content {
  background: white;
  border-radius: 8px;
  padding: 24px;
  width: 80%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
}

.employee-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.employee-detail-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.close-button {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.close-button:hover {
  color: #333;
}

.employee-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.info-item {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 6px;
  text-align: center;
}

.info-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.info-value {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.chart-container {
  margin: 20px 0;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}
</style>
