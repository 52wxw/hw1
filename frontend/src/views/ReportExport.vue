<template>
  <div class="report-export">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>巡检报告</span>
          <div>
            <el-button @click="exportPDF">导出PDF</el-button>
            <el-button @click="exportExcel">导出Excel</el-button>
            <el-button @click="exportMarkdown">导出Markdown</el-button>
          </div>
        </div>
      </template>

      <!-- 筛选条件 -->
      <el-form :inline="true" :model="filterForm" style="margin-bottom: 20px;">
        <el-form-item label="设备">
          <el-select v-model="filterForm.deviceId" placeholder="选择设备" clearable style="width: 200px;">
            <el-option 
              v-for="device in devices" 
              :key="device.id" 
              :label="device.name" 
              :value="device.id"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="filterForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          ></el-date-picker>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadReports">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 报告列表 -->
      <el-table :data="reports" border style="width: 100%">
        <el-table-column prop="id" label="ID" width="80"></el-table-column>
        <el-table-column prop="deviceName" label="设备名称" width="150"></el-table-column>
        <el-table-column prop="inspectTime" label="巡检时间" width="180"></el-table-column>
        <el-table-column prop="healthScore" label="健康评分" width="120">
          <template #default="scope">
            <el-tag :type="getHealthTagType(scope.row.healthScore)">
              {{ scope.row.healthScore }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="faultCount" label="故障数量" width="100">
          <template #default="scope">
            <el-tag v-if="scope.row.faultCount > 0" type="danger">
              {{ scope.row.faultCount }}
            </el-tag>
            <span v-else>0</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="viewReport(scope.row)">查看详情</el-button>
            <el-button size="small" @click="downloadReport(scope.row, 'pdf')">PDF</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        style="margin-top: 20px;"
        @size-change="loadReports"
        @current-change="loadReports"
      ></el-pagination>
    </el-card>

    <!-- 报告详情对话框 -->
    <el-dialog v-model="reportDialogVisible" title="巡检报告详情" width="900px">
      <div v-if="selectedReport" class="report-content">
        <h2>设备巡检报告</h2>
        <el-descriptions :column="2" border style="margin-top: 20px;">
          <el-descriptions-item label="设备名称">{{ selectedReport.deviceName }}</el-descriptions-item>
          <el-descriptions-item label="巡检时间">{{ selectedReport.inspectTime }}</el-descriptions-item>
          <el-descriptions-item label="健康评分">
            <el-tag :type="getHealthTagType(selectedReport.healthScore)">
              {{ selectedReport.healthScore }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <h3 style="margin-top: 20px;">故障列表</h3>
        <el-table :data="selectedReport.faults" border style="margin-top: 10px;">
          <el-table-column prop="level" label="等级" width="100">
            <template #default="scope">
              <el-tag :type="getFaultLevelType(scope.row.level)">
                {{ scope.row.level }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" min-width="200"></el-table-column>
          <el-table-column prop="repairSuggestion" label="修复建议" min-width="200"></el-table-column>
        </el-table>

        <h3 style="margin-top: 20px;">修复结果</h3>
        <el-table :data="selectedReport.repairResults" border style="margin-top: 10px;">
          <el-table-column prop="fault" label="故障" min-width="200"></el-table-column>
          <el-table-column prop="result" label="结果" min-width="300"></el-table-column>
          <el-table-column prop="success" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.success ? 'success' : 'danger'">
                {{ scope.row.success ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { ElMessage } from 'element-plus';

const reports = ref([]);
const devices = ref([]);
const filterForm = ref({
  deviceId: null,
  dateRange: null
});
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const reportDialogVisible = ref(false);
const selectedReport = ref(null);

// 加载报告列表
const loadReports = async () => {
  try {
    // 实际应该调用后端API获取报告列表
    // 这里模拟数据
    const { data } = await axios.get('/api/device');
    devices.value = data.data || [];
    
    // 模拟报告数据（实际应该从数据库查询）
    reports.value = [
      {
        id: 1,
        deviceId: 1,
        deviceName: '华为AR1000路由器',
        inspectTime: '2024-01-15 10:30:00',
        healthScore: 85,
        faultCount: 2,
        faults: [
          { level: 'P1', description: '接口G0/0/1状态为down', repairSuggestion: '执行 undo shutdown 命令启用接口' },
          { level: 'P2', description: 'CPU使用率过高：85%', repairSuggestion: '检查进程占用，优化配置' }
        ],
        repairResults: [
          { fault: '接口G0/0/1状态为down', result: '修复成功：接口已启用', success: true }
        ]
      }
    ];
    total.value = reports.value.length;
  } catch (e) {
    ElMessage.error('加载报告失败');
  }
};

const resetFilter = () => {
  filterForm.value = {
    deviceId: null,
    dateRange: null
  };
  loadReports();
};

const getHealthTagType = (score) => {
  if (score >= 80) return 'success';
  if (score >= 60) return 'warning';
  return 'danger';
};

const getFaultLevelType = (level) => {
  if (level === 'P0') return 'danger';
  if (level === 'P1') return 'warning';
  if (level === 'P2') return 'info';
  return '';
};

const viewReport = (report) => {
  selectedReport.value = report;
  reportDialogVisible.value = true;
};

// 导出PDF
const exportPDF = () => {
  ElMessage.info('PDF导出功能需要后端支持，请调用后端API');
  // 实际应该调用后端API生成PDF
  // window.open(`/api/report/export/pdf?deviceId=${filterForm.value.deviceId}`);
};

// 导出Excel
const exportExcel = () => {
  ElMessage.info('Excel导出功能需要后端支持，请调用后端API');
  // 实际应该调用后端API生成Excel
  // window.open(`/api/report/export/excel?deviceId=${filterForm.value.deviceId}`);
};

// 导出Markdown
const exportMarkdown = () => {
  if (reports.value.length === 0) {
    ElMessage.warning('没有可导出的报告');
    return;
  }
  
  let markdown = '# 设备巡检报告\n\n';
  markdown += `生成时间：${new Date().toLocaleString()}\n\n`;
  
  reports.value.forEach(report => {
    markdown += `## ${report.deviceName}\n\n`;
    markdown += `- 巡检时间：${report.inspectTime}\n`;
    markdown += `- 健康评分：${report.healthScore}\n`;
    markdown += `- 故障数量：${report.faultCount}\n\n`;
    
    if (report.faults && report.faults.length > 0) {
      markdown += '### 故障列表\n\n';
      report.faults.forEach(fault => {
        markdown += `- **${fault.level}** ${fault.description}\n`;
        markdown += `  - 修复建议：${fault.repairSuggestion}\n\n`;
      });
    }
  });
  
  // 下载Markdown文件
  const blob = new Blob([markdown], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `巡检报告_${new Date().toISOString().split('T')[0]}.md`;
  link.click();
  URL.revokeObjectURL(url);
  
  ElMessage.success('Markdown文件已下载');
};

const downloadReport = (report, format) => {
  // 实现下载逻辑
};
</script>
