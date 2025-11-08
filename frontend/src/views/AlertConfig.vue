<template>
  <div class="alert-config">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>告警配置</span>
          <el-button type="primary" @click="showAddDialog = true">添加告警规则</el-button>
        </div>
      </template>

      <!-- 告警配置列表 -->
      <el-table :data="alertConfigs" border style="width: 100%">
        <el-table-column prop="name" label="规则名称" width="150"></el-table-column>
        <el-table-column prop="deviceName" label="设备" width="150"></el-table-column>
        <el-table-column prop="metric" label="监控指标" width="120"></el-table-column>
        <el-table-column prop="comparison" label="比较符" width="100">
          <template #default="scope">
            <el-tag>{{ scope.row.comparison === '>' ? '大于' : scope.row.comparison === '<' ? '小于' : '等于' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="threshold" label="阈值" width="100"></el-table-column>
        <el-table-column prop="channels" label="告警渠道" width="200">
          <template #default="scope">
            <el-tag 
              v-for="channel in scope.row.channels" 
              :key="channel" 
              style="margin-right: 5px;"
            >
              {{ getChannelName(channel) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="enabled" label="状态" width="100">
          <template #default="scope">
            <el-switch 
              v-model="scope.row.enabled" 
              @change="toggleConfig(scope.row)"
            ></el-switch>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" @click="editConfig(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteConfig(scope.row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 告警记录 -->
      <h3 style="margin-top: 30px;">告警记录</h3>
      <el-table :data="alertRecords" border style="width: 100%; margin-top: 10px;">
        <el-table-column prop="deviceId" label="设备ID" width="100"></el-table-column>
        <el-table-column prop="metricValue" label="指标值" width="100"></el-table-column>
        <el-table-column prop="alertLevel" label="告警等级" width="100">
          <template #default="scope">
            <el-tag :type="getAlertLevelType(scope.row.alertLevel)">
              {{ scope.row.alertLevel }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="告警消息" min-width="200"></el-table-column>
        <el-table-column prop="sendStatus" label="发送状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.sendStatus === 'success' ? 'success' : 'danger'">
              {{ scope.row.sendStatus }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="时间" width="180"></el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑告警配置对话框 -->
    <el-dialog 
      v-model="showAddDialog" 
      :title="editingConfig ? '编辑告警规则' : '添加告警规则'" 
      width="600px"
    >
      <el-form :model="alertForm" label-width="120px">
        <el-form-item label="规则名称">
          <el-input v-model="alertForm.name"></el-input>
        </el-form-item>
        <el-form-item label="设备">
          <el-select v-model="alertForm.deviceId" placeholder="选择设备（留空表示所有设备）" clearable>
            <el-option 
              v-for="device in devices" 
              :key="device.id" 
              :label="device.name" 
              :value="device.id"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="监控指标">
          <el-select v-model="alertForm.metric">
            <el-option label="CPU使用率" value="cpu_usage"></el-option>
            <el-option label="内存使用率" value="memory_usage"></el-option>
            <el-option label="接口Down" value="interface_down"></el-option>
            <el-option label="健康评分" value="health_score"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="比较符">
          <el-select v-model="alertForm.comparison">
            <el-option label="大于" value=">"></el-option>
            <el-option label="小于" value="<"></el-option>
            <el-option label="等于" value="="></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="阈值">
          <el-input-number v-model="alertForm.threshold" :min="0" :max="100"></el-input-number>
        </el-form-item>
        <el-form-item label="告警渠道">
          <el-checkbox-group v-model="alertForm.channels">
            <el-checkbox label="email">邮件</el-checkbox>
            <el-checkbox label="wechat">企业微信</el-checkbox>
            <el-checkbox label="dingtalk">钉钉</el-checkbox>
            <el-checkbox label="sms">短信</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveConfig">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';

const alertConfigs = ref([]);
const alertRecords = ref([]);
const devices = ref([]);
const showAddDialog = ref(false);
const editingConfig = ref(null);

const alertForm = ref({
  name: '',
  deviceId: null,
  metric: 'cpu_usage',
  comparison: '>',
  threshold: 80,
  channels: ['email']
});

// 加载数据
const loadData = async () => {
  try {
    // 加载设备列表
    const deviceRes = await axios.get('/api/device');
    devices.value = deviceRes.data.data || [];
    
    // 加载告警配置
    const configRes = await axios.get('http://localhost:8004/api/alert/config/list');
    alertConfigs.value = configRes.data.data || [];
    
    // 加载告警记录
    const recordRes = await axios.get('http://localhost:8004/api/alert/record/list');
    alertRecords.value = recordRes.data.data || [];
  } catch (e) {
    ElMessage.error('加载数据失败');
  }
};

const getChannelName = (channel) => {
  const names = {
    'email': '邮件',
    'wechat': '企业微信',
    'dingtalk': '钉钉',
    'sms': '短信'
  };
  return names[channel] || channel;
};

const getAlertLevelType = (level) => {
  if (level === 'critical') return 'danger';
  if (level === 'warning') return 'warning';
  return 'info';
};

const saveConfig = async () => {
  try {
    const url = editingConfig.value 
      ? `http://localhost:8004/api/alert/config/${editingConfig.value.id}`
      : 'http://localhost:8004/api/alert/config/add';
    
    const method = editingConfig.value ? 'put' : 'post';
    
    await axios[method](url, alertForm.value);
    ElMessage.success(editingConfig.value ? '更新成功' : '添加成功');
    showAddDialog.value = false;
    loadData();
  } catch (e) {
    ElMessage.error('保存失败');
  }
};

const editConfig = (config) => {
  editingConfig.value = config;
  alertForm.value = {
    name: config.name,
    deviceId: config.deviceId,
    metric: config.metric,
    comparison: config.comparison,
    threshold: config.threshold,
    channels: typeof config.channels === 'string' ? JSON.parse(config.channels) : config.channels
  };
  showAddDialog.value = true;
};

const deleteConfig = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个告警规则吗？', '提示', {
      type: 'warning'
    });
    await axios.delete(`http://localhost:8004/api/alert/config/${id}`);
    ElMessage.success('删除成功');
    loadData();
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败');
    }
  }
};

const toggleConfig = async (config) => {
  try {
    await axios.put(`http://localhost:8004/api/alert/config/${config.id}`, {
      enabled: config.enabled
    });
    ElMessage.success('状态更新成功');
  } catch (e) {
    ElMessage.error('更新失败');
    config.enabled = !config.enabled; // 回滚
  }
};

onMounted(() => {
  loadData();
});
</script>

<style scoped>
.alert-config {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>

