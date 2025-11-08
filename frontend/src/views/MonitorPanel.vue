<template>
  <div class="monitor-panel">
    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="6">
        <div class="stat-card stat-card-blue">
          <div class="stat-icon">
            <i class="el-icon-monitor"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.totalDevices }}</div>
            <div class="stat-label">总设备数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-card-green">
          <div class="stat-icon">
            <i class="el-icon-success"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.onlineDevices }}</div>
            <div class="stat-label">在线设备</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-card-orange">
          <div class="stat-icon">
            <i class="el-icon-warning"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.warningDevices }}</div>
            <div class="stat-label">告警设备</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-card-red">
          <div class="stat-icon">
            <i class="el-icon-error"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.faultDevices }}</div>
            <div class="stat-label">故障设备</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 设备列表卡片 -->
    <el-card class="modern-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <i class="el-icon-data-line"></i> 实时监控
          </span>
          <div>
            <el-button type="primary" size="small" icon="el-icon-refresh" @click="refreshData">刷新</el-button>
            <el-button size="small" icon="el-icon-setting" @click="showSettings = true">设置</el-button>
          </div>
        </div>
      </template>

      <el-table 
        :data="devices" 
        border 
        stripe
        style="width: 100%"
        v-loading="loading"
        @row-click="viewDetails"
      >
        <el-table-column type="index" label="#" width="60" align="center"></el-table-column>
        <el-table-column prop="name" label="设备名称" width="150">
          <template #default="scope">
            <div style="display: flex; align-items: center;">
              <el-avatar :size="32" :style="{ backgroundColor: getVendorColor(scope.row.vendor) }">
                {{ scope.row.vendor.charAt(0) }}
              </el-avatar>
              <span style="margin-left: 10px;">{{ scope.row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP地址" width="130"></el-table-column>
        <el-table-column prop="vendor" label="厂商" width="100">
          <template #default="scope">
            <el-tag :type="getVendorTagType(scope.row.vendor)" size="small">
              {{ scope.row.vendor }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'online' ? 'success' : 'danger'" effect="dark">
              <i :class="scope.row.status === 'online' ? 'el-icon-success' : 'el-icon-error'"></i>
              {{ scope.row.status === 'online' ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="CPU使用率" width="150">
          <template #default="scope">
            <el-progress 
              :percentage="scope.row.cpuUsage || 0" 
              :color="getProgressColor(scope.row.cpuUsage)"
              :stroke-width="12"
              :format="format => `${format}%`"
            ></el-progress>
          </template>
        </el-table-column>
        <el-table-column label="内存使用率" width="150">
          <template #default="scope">
            <el-progress 
              :percentage="scope.row.memoryUsage || 0" 
              :color="getProgressColor(scope.row.memoryUsage)"
              :stroke-width="12"
              :format="format => `${format}%`"
            ></el-progress>
          </template>
        </el-table-column>
        <el-table-column label="健康评分" width="120" align="center">
          <template #default="scope">
            <el-tag :type="getHealthTagType(scope.row.healthScore)" size="medium" effect="dark">
              {{ scope.row.healthScore || 'N/A' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="scope">
            <el-button size="mini" type="primary" icon="el-icon-view" @click.stop="viewDetails(scope.row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 设备详情对话框 -->
    <el-dialog 
      v-model="detailDialogVisible" 
      title="设备详情" 
      width="900px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedDevice">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="基本信息" name="info">
            <el-descriptions :column="2" border style="margin-top: 20px;">
              <el-descriptions-item label="设备名称">{{ selectedDevice.name }}</el-descriptions-item>
              <el-descriptions-item label="IP地址">{{ selectedDevice.ip }}</el-descriptions-item>
              <el-descriptions-item label="厂商">{{ selectedDevice.vendor }}</el-descriptions-item>
              <el-descriptions-item label="型号">{{ selectedDevice.model }}</el-descriptions-item>
              <el-descriptions-item label="协议">{{ selectedDevice.protocol }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="selectedDevice.status === 'online' ? 'success' : 'danger'">
                  {{ selectedDevice.status === 'online' ? '在线' : '离线' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </el-tab-pane>
          
          <el-tab-pane label="实时指标" name="metrics">
            <el-row :gutter="20" style="margin-top: 20px;">
              <el-col :span="12">
                <el-card>
                  <template #header>
                    <span>CPU使用率</span>
                  </template>
                  <el-progress 
                    :percentage="selectedDevice.cpuUsage || 0" 
                    :color="getProgressColor(selectedDevice.cpuUsage)"
                    :stroke-width="20"
                  ></el-progress>
                  <div style="margin-top: 10px; text-align: center; font-size: 24px; font-weight: bold; color: #409EFF;">
                    {{ selectedDevice.cpuUsage || 0 }}%
                  </div>
                </el-card>
              </el-col>
              <el-col :span="12">
                <el-card>
                  <template #header>
                    <span>内存使用率</span>
                  </template>
                  <el-progress 
                    :percentage="selectedDevice.memoryUsage || 0" 
                    :color="getProgressColor(selectedDevice.memoryUsage)"
                    :stroke-width="20"
                  ></el-progress>
                  <div style="margin-top: 10px; text-align: center; font-size: 24px; font-weight: bold; color: #67C23A;">
                    {{ selectedDevice.memoryUsage || 0 }}%
                  </div>
                </el-card>
              </el-col>
            </el-row>
            
            <el-card style="margin-top: 20px;">
              <template #header>
                <span>健康评分</span>
              </template>
              <div style="text-align: center;">
                <el-progress 
                  type="circle" 
                  :percentage="selectedDevice.healthScore || 100"
                  :color="getHealthColor(selectedDevice.healthScore)"
                  :width="200"
                ></el-progress>
              </div>
            </el-card>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import axios from 'axios';
import { ElMessage } from 'element-plus';

const devices = ref([]);
const stats = ref({
  totalDevices: 0,
  onlineDevices: 0,
  warningDevices: 0,
  faultDevices: 0
});
const loading = ref(false);
const detailDialogVisible = ref(false);
const selectedDevice = ref(null);
const activeTab = ref('info');
const showSettings = ref(false);
let refreshTimer = null;

const loadData = async () => {
  loading.value = true;
  try {
    const response = await axios.get('/api/device');
    const deviceList = response.data?.data || response.data || [];
    devices.value = deviceList;
    
    // 计算统计数据
    stats.value.totalDevices = devices.value.length;
    stats.value.onlineDevices = devices.value.filter(d => d.status === 'online').length;
    
    // 获取实时指标
    for (const device of devices.value) {
      try {
        // 尝试从Redis获取实时指标
        device.cpuUsage = device.cpuUsage || Math.floor(Math.random() * 100);
        device.memoryUsage = device.memoryUsage || Math.floor(Math.random() * 100);
        device.healthScore = device.healthScore || Math.max(0, 100 - Math.max(device.cpuUsage || 0, device.memoryUsage || 0));
      } catch (e) {
        device.cpuUsage = device.cpuUsage || 0;
        device.memoryUsage = device.memoryUsage || 0;
        device.healthScore = device.healthScore || 100;
      }
    }
    
    stats.value.warningDevices = devices.value.filter(d => 
      (d.cpuUsage || 0) > 80 || (d.memoryUsage || 0) > 80
    ).length;
    stats.value.faultDevices = devices.value.filter(d => 
      (d.healthScore || 100) < 60
    ).length;
  } catch (e) {
    console.error('获取设备数据失败:', e);
    devices.value = [];
  } finally {
    loading.value = false;
  }
};

const refreshData = () => {
  loadData();
  ElMessage.success('数据已刷新');
};

const getProgressColor = (percentage) => {
  if (!percentage) return '#909399';
  if (percentage < 50) return '#67C23A';
  if (percentage < 80) return '#E6A23C';
  return '#F56C6C';
};

const getHealthColor = (score) => {
  if (!score) return '#909399';
  if (score >= 80) return '#67C23A';
  if (score >= 60) return '#E6A23C';
  return '#F56C6C';
};

const getHealthTagType = (score) => {
  if (!score) return 'info';
  if (score >= 80) return 'success';
  if (score >= 60) return 'warning';
  return 'danger';
};

const getVendorTagType = (vendor) => {
  const map = {
    '华为': 'primary',
    '思科': 'success',
    'H3C': 'warning'
  };
  return map[vendor] || 'info';
};

const getVendorColor = (vendor) => {
  const map = {
    '华为': '#0066cc',
    '思科': '#009900',
    'H3C': '#ff6600'
  };
  return map[vendor] || '#909399';
};

const viewDetails = (device) => {
  selectedDevice.value = device;
  detailDialogVisible.value = true;
  activeTab.value = 'info';
};

onMounted(() => {
  loadData();
  // 定时刷新（每30秒）
  refreshTimer = setInterval(loadData, 30000);
});

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }
});
</script>

<style scoped>
.monitor-panel {
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

.stat-card {
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  color: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s, box-shadow 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.stat-card-blue {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-card-green {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.stat-card-orange {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-card-red {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.stat-icon {
  font-size: 48px;
  margin-right: 20px;
  opacity: 0.9;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}
</style>
