<template>
  <div class="report-container">
    <el-card>
      <div slot="header">巡检报告</div>
      <el-table :data="reports" border>
        <el-table-column prop="device_id" label="设备ID" width="100"></el-table-column>
        <el-table-column prop="health_score" label="健康评分" width="120">
          <template #default="scope">
            <el-progress :percentage="scope.row.health_score" :color="getHealthColor(scope.row.health_score)"></el-progress>
          </template>
        </el-table-column>
        <el-table-column prop="inspect_time" label="巡检时间"></el-table-column>
        <el-table-column label="操作">
          <template #default="scope">
            <el-button size="small" @click="viewDetail(scope.row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

export default {
  name: 'Report',
  setup() {
    const reports = ref([])

    const loadReports = async () => {
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
      }
    }

    const getHealthColor = (score) => {
      if (score >= 80) return '#67c23a'
      if (score >= 60) return '#e6a23c'
      return '#f56c6c'
    }

    const viewDetail = (report) => {
      ElMessage.info('查看详情功能开发中')
    }

    onMounted(() => {
      loadReports()
    })

    return {
      reports,
      getHealthColor,
      viewDetail
    }
  }
}
</script>

<style scoped>
.report-container {
  padding: 20px;
}
</style>

