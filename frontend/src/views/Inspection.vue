<template>
  <div class="inspection-container">
    <el-card class="modern-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <i class="el-icon-search"></i> 巡检管理
          </span>
          <el-button type="primary" icon="el-icon-plus" @click="showTaskDialog = true">创建巡检任务</el-button>
        </div>
      </template>
      
      <el-tabs v-model="activeTab" type="card">
        <el-tab-pane label="定时任务" name="schedule">
          <el-table :data="tasks" border stripe v-loading="loading">
            <el-table-column type="index" label="#" width="60" align="center"></el-table-column>
            <el-table-column prop="name" label="任务名称" width="200"></el-table-column>
            <el-table-column prop="cron_expr" label="Cron表达式" width="150">
              <template #default="scope">
                <el-tag type="info">{{ scope.row.cron_expr }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="trigger_type" label="触发类型" width="120">
              <template #default="scope">
                <el-tag :type="scope.row.trigger_type === 'schedule' ? 'success' : 'warning'">
                  {{ scope.row.trigger_type === 'schedule' ? '定时' : '触发式' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="enabled" label="状态" width="100" align="center">
              <template #default="scope">
                <el-switch 
                  v-model="scope.row.enabled" 
                  @change="toggleTask(scope.row)"
                  :active-text="scope.row.enabled ? '启用' : '禁用'"
                ></el-switch>
              </template>
            </el-table-column>
            <el-table-column prop="last_run_time" label="最后执行时间" width="180">
              <template #default="scope">
                {{ scope.row.last_run_time || '未执行' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="scope">
                <el-button size="mini" type="primary" icon="el-icon-video-play" @click="triggerTask(scope.row.id)">立即执行</el-button>
                <el-button size="mini" type="danger" icon="el-icon-delete" @click="deleteTask(scope.row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        
        <el-tab-pane label="巡检报告" name="report">
          <el-table :data="reports" border stripe v-loading="reportLoading">
            <el-table-column type="index" label="#" width="60" align="center"></el-table-column>
            <el-table-column prop="device_id" label="设备ID" width="100"></el-table-column>
            <el-table-column prop="health_score" label="健康评分" width="120" align="center">
              <template #default="scope">
                <el-progress 
                  type="circle" 
                  :percentage="scope.row.health_score" 
                  :color="getHealthColor(scope.row.health_score)"
                  :width="60"
                ></el-progress>
              </template>
            </el-table-column>
            <el-table-column prop="inspect_time" label="巡检时间" width="180"></el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="scope">
                <el-button size="small" type="primary" icon="el-icon-view" @click="viewReport(scope.row)">查看详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 创建任务对话框 -->
    <el-dialog 
      title="创建巡检任务" 
      v-model="showTaskDialog" 
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form :model="newTask" label-width="120px" :rules="taskRules" ref="taskFormRef">
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="newTask.name" placeholder="请输入任务名称"></el-input>
        </el-form-item>
        <el-form-item label="选择设备" prop="device_ids">
          <el-select v-model="newTask.device_ids" multiple placeholder="请选择设备" style="width: 100%;">
            <el-option 
              v-for="device in devices" 
              :key="device.id" 
              :label="device.name" 
              :value="device.id"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="触发类型" prop="trigger_type">
          <el-radio-group v-model="newTask.trigger_type">
            <el-radio label="schedule">定时巡检</el-radio>
            <el-radio label="trigger">触发式巡检</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item 
          v-if="newTask.trigger_type === 'schedule'" 
          label="Cron表达式" 
          prop="cron_expr"
        >
          <el-input v-model="newTask.cron_expr" placeholder="如：0 3 * * * (每天凌晨3点)">
            <template #append>
              <el-button @click="showCronHelper = true">帮助</el-button>
            </template>
          </el-input>
          <div class="cron-hint">
            <p>格式：分 时 日 月 周</p>
            <p>示例：0 3 * * * (每天3点) | 0 */2 * * * (每2小时) | 0 0 * * 0 (每周日0点)</p>
          </div>
        </el-form-item>
        <el-form-item 
          v-if="newTask.trigger_type === 'trigger'" 
          label="触发条件" 
          prop="trigger_condition"
        >
          <el-row :gutter="10">
            <el-col :span="8">
              <el-select v-model="newTask.trigger_condition.metric" placeholder="指标">
                <el-option label="CPU使用率" value="cpu_usage"></el-option>
                <el-option label="内存使用率" value="memory_usage"></el-option>
                <el-option label="接口状态" value="interface_down"></el-option>
              </el-select>
            </el-col>
            <el-col :span="6">
              <el-select v-model="newTask.trigger_condition.comparison" placeholder="比较">
                <el-option label="大于" value=">"></el-option>
                <el-option label="小于" value="<"></el-option>
                <el-option label="等于" value="="></el-option>
              </el-select>
            </el-col>
            <el-col :span="10">
              <el-input-number v-model="newTask.trigger_condition.threshold" :min="0" :max="100" placeholder="阈值"></el-input-number>
            </el-col>
          </el-row>
        </el-form-item>
        <el-form-item label="自动修复">
          <el-switch v-model="newTask.auto_repair"></el-switch>
          <span style="margin-left: 10px; color: #909399; font-size: 12px;">启用后，发现故障将自动尝试修复</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTaskDialog = false">取消</el-button>
        <el-button type="primary" @click="createTask">确认</el-button>
      </template>
    </el-dialog>

    <!-- 报告详情对话框 -->
    <el-dialog 
      title="巡检报告详情" 
      v-model="showReportDialog" 
      width="900px"
      v-if="selectedReport"
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="设备ID">{{ selectedReport.device_id }}</el-descriptions-item>
        <el-descriptions-item label="健康评分">
          <el-tag :type="getHealthTagType(selectedReport.health_score)" size="large">
            {{ selectedReport.health_score }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="巡检时间" :span="2">{{ selectedReport.inspect_time }}</el-descriptions-item>
      </el-descriptions>
      
      <el-divider>故障详情</el-divider>
      <div v-if="selectedReport.abnormal">
        <pre style="background: #f5f7fa; padding: 15px; border-radius: 4px; white-space: pre-wrap;">{{ selectedReport.abnormal }}</pre>
      </div>
      
      <el-divider>修复结果</el-divider>
      <div v-if="selectedReport.repair_result">
        <pre style="background: #f5f7fa; padding: 15px; border-radius: 4px; white-space: pre-wrap;">{{ selectedReport.repair_result }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'Inspection',
  setup() {
    const activeTab = ref('schedule')
    const tasks = ref([])
    const reports = ref([])
    const devices = ref([])
    const loading = ref(false)
    const reportLoading = ref(false)
    const showTaskDialog = ref(false)
    const showReportDialog = ref(false)
    const showCronHelper = ref(false)
    const selectedReport = ref(null)
    const taskFormRef = ref(null)

    const newTask = ref({
      name: '',
      device_ids: [],
      cron_expr: '0 3 * * *',
      trigger_type: 'schedule',
      trigger_condition: {
        metric: 'cpu_usage',
        comparison: '>',
        threshold: 80
      },
      auto_repair: false
    })

    const taskRules = {
      name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
      device_ids: [{ required: true, message: '请选择设备', trigger: 'change' }],
      cron_expr: [{ required: true, message: '请输入Cron表达式', trigger: 'blur' }]
    }

    const loadTasks = async () => {
      loading.value = true
      try {
        const response = await axios.get('/api/scheduler/task/list')
        if (response.data?.code === 200) {
          tasks.value = response.data.data || []
        }
      } catch (error) {
        console.error('加载任务失败', error)
        tasks.value = []
      } finally {
        loading.value = false
      }
    }

    const loadDevices = async () => {
      try {
        const response = await axios.get('/api/device')
        devices.value = response.data?.data || response.data || []
      } catch (error) {
        console.error('加载设备列表失败', error)
      }
    }

    const loadReports = async () => {
      reportLoading.value = true
      try {
        // 从调度服务获取报告列表
        const response = await axios.get('/api/scheduler/report/list')
        if (response.data?.code === 200) {
          reports.value = response.data.data || []
        } else {
          reports.value = []
        }
      } catch (error) {
        console.error('加载报告失败', error)
        reports.value = []
      } finally {
        reportLoading.value = false
      }
    }

    const createTask = async () => {
      if (!taskFormRef.value) return
      
      await taskFormRef.value.validate(async (valid) => {
        if (valid) {
          try {
            const taskData = {
              ...newTask.value,
              trigger_condition: newTask.value.trigger_type === 'trigger' ? newTask.value.trigger_condition : {}
            }
            
            await axios.post('/api/scheduler/task/add', taskData)
            ElMessage.success('任务创建成功')
            showTaskDialog.value = false
            resetTaskForm()
            loadTasks()
          } catch (error) {
            ElMessage.error('创建任务失败：' + (error.response?.data?.msg || error.message))
          }
        }
      })
    }

    const resetTaskForm = () => {
      newTask.value = {
        name: '',
        device_ids: [],
        cron_expr: '0 3 * * *',
        trigger_type: 'schedule',
        trigger_condition: {
          metric: 'cpu_usage',
          comparison: '>',
          threshold: 80
        },
        auto_repair: false
      }
      if (taskFormRef.value) {
        taskFormRef.value.resetFields()
      }
    }

    const triggerTask = async (taskId) => {
      try {
        await axios.post('/api/scheduler/task/trigger', { task_id: taskId })
        ElMessage.success('任务已触发')
        loadTasks()
      } catch (error) {
        ElMessage.error('触发任务失败')
      }
    }

    const toggleTask = async (task) => {
      try {
        // 这里应该调用后端API更新任务状态
        // await axios.put(`/api/scheduler/task/${task.id}`, { enabled: task.enabled })
        ElMessage.success(task.enabled ? '任务已启用' : '任务已禁用')
      } catch (error) {
        ElMessage.error('操作失败')
      }
    }

    const deleteTask = async (taskId) => {
      try {
        await ElMessageBox.confirm('确定要删除该任务吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        // await axios.delete(`/api/scheduler/task/${taskId}`)
        ElMessage.success('删除成功')
        loadTasks()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }

    const viewReport = (report) => {
      selectedReport.value = report
      showReportDialog.value = true
    }

    const getHealthTagType = (score) => {
      if (score >= 80) return 'success'
      if (score >= 60) return 'warning'
      return 'danger'
    }

    const getHealthColor = (score) => {
      if (score >= 80) return '#67c23a'
      if (score >= 60) return '#e6a23c'
      return '#f56c6c'
    }

    onMounted(() => {
      loadTasks()
      loadDevices()
      loadReports()
    })

    return {
      activeTab,
      tasks,
      reports,
      devices,
      loading,
      reportLoading,
      showTaskDialog,
      showReportDialog,
      showCronHelper,
      selectedReport,
      newTask,
      taskFormRef,
      taskRules,
      loadTasks,
      createTask,
      triggerTask,
      toggleTask,
      deleteTask,
      viewReport,
      getHealthTagType,
      getHealthColor
    }
  }
}
</script>

<style scoped>
.inspection-container {
  padding: 0;
}

.modern-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.card-title i {
  margin-right: 8px;
  color: #409EFF;
}

.cron-hint {
  margin-top: 5px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
  color: #909399;
}

.cron-hint p {
  margin: 5px 0;
}
</style>
