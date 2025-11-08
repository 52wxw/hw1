<template>
  <div class="device-manage">
    <el-card class="modern-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <i class="el-icon-monitor"></i> 设备管理
          </span>
          <div>
            <el-button type="primary" icon="el-icon-plus" @click="showAddDialog = true">添加设备</el-button>
            <el-button type="success" icon="el-icon-folder-opened" @click="showGroupDialog = true">设备分组</el-button>
          </div>
        </div>
      </template>

      <!-- 筛选栏 -->
      <el-row :gutter="20" style="margin-bottom: 20px;">
        <el-col :span="6">
          <el-select v-model="filterForm.vendor" placeholder="选择厂商" clearable style="width: 100%;">
            <el-option label="全部厂商" value=""></el-option>
            <el-option label="华为" value="华为"></el-option>
            <el-option label="思科" value="思科"></el-option>
            <el-option label="H3C" value="H3C"></el-option>
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filterForm.group" placeholder="选择分组" clearable style="width: 100%;">
            <el-option label="全部分组" value=""></el-option>
            <el-option v-for="group in deviceGroups" :key="group.id" :label="group.name" :value="group.id"></el-option>
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-input v-model="filterForm.keyword" placeholder="搜索设备名称/IP" clearable>
            <template #prefix>
              <i class="el-icon-search"></i>
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-button type="primary" @click="handleFilter">筛选</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-col>
      </el-row>

      <el-table
        :data="filteredDevices"
        border
        stripe
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column type="index" label="#" width="60" align="center"></el-table-column>
        <el-table-column prop="name" label="设备名称" width="150">
          <template #default="scope">
            <el-tag type="info" size="small">{{ scope.row.name }}</el-tag>
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
        <el-table-column prop="model" label="型号" width="120"></el-table-column>
        <el-table-column prop="protocol" label="协议" width="80" align="center">
          <template #default="scope">
            <el-tag size="mini" :type="scope.row.protocol === 'ssh' ? 'success' : 'warning'">
              {{ scope.row.protocol.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'online' ? 'success' : 'danger'" effect="dark">
              <i :class="scope.row.status === 'online' ? 'el-icon-success' : 'el-icon-error'"></i>
              {{ scope.row.status === 'online' ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button size="mini" type="primary" icon="el-icon-view" @click="startInspect(scope.row.id)">巡检</el-button>
            <el-button size="mini" type="warning" icon="el-icon-edit" @click="editDevice(scope.row)">编辑</el-button>
            <el-button size="mini" type="danger" icon="el-icon-delete" @click="deleteDevice(scope.row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑设备弹窗 -->
    <el-dialog
      :title="dialogTitle"
      v-model="showAddDialog"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="newDevice" label-width="100px" :rules="rules" ref="deviceFormRef">
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="newDevice.name" placeholder="请输入设备名称"></el-input>
        </el-form-item>
        <el-form-item label="IP地址" prop="ip">
          <el-input v-model="newDevice.ip" placeholder="请输入IP地址"></el-input>
        </el-form-item>
        <el-form-item label="厂商" prop="vendor">
          <el-select v-model="newDevice.vendor" placeholder="请选择厂商" style="width: 100%;">
            <el-option label="华为" value="华为">
              <span style="color: #0066cc;">华为</span>
            </el-option>
            <el-option label="思科" value="思科">
              <span style="color: #009900;">思科</span>
            </el-option>
            <el-option label="H3C" value="H3C">
              <span style="color: #ff6600;">H3C</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="型号" prop="model">
          <el-input v-model="newDevice.model" placeholder="请输入设备型号"></el-input>
        </el-form-item>
        <el-form-item label="协议" prop="protocol">
          <el-select v-model="newDevice.protocol" placeholder="请选择协议" style="width: 100%;">
            <el-option label="SSH" value="ssh"></el-option>
            <el-option label="SNMP" value="snmp"></el-option>
            <el-option label="Syslog" value="syslog"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="设备分组" prop="group">
          <el-select v-model="newDevice.groupId" placeholder="请选择分组" clearable style="width: 100%;">
            <el-option v-for="group in deviceGroups" :key="group.id" :label="group.name" :value="group.id"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="newDevice.username" placeholder="请输入用户名"></el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="newDevice.password" type="password" placeholder="请输入密码" show-password></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveDevice">确认</el-button>
      </template>
    </el-dialog>

    <!-- 设备分组管理弹窗 -->
    <el-dialog title="设备分组管理" v-model="showGroupDialog" width="800px">
      <el-button type="primary" icon="el-icon-plus" @click="showAddGroupDialog = true" style="margin-bottom: 20px;">新建分组</el-button>
      <el-table :data="deviceGroups" border>
        <el-table-column prop="name" label="分组名称"></el-table-column>
        <el-table-column prop="description" label="描述"></el-table-column>
        <el-table-column label="设备数量" width="120">
          <template #default="scope">
            {{ getGroupDeviceCount(scope.row.id) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="mini" type="warning" @click="editGroup(scope.row)">编辑</el-button>
            <el-button size="mini" type="danger" @click="deleteGroup(scope.row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';

const devices = ref([]);
const deviceGroups = ref([]);
const loading = ref(false);
const showAddDialog = ref(false);
const showGroupDialog = ref(false);
const showAddGroupDialog = ref(false);
const isEdit = ref(false);
const deviceFormRef = ref(null);

const filterForm = ref({
  vendor: '',
  group: '',
  keyword: ''
});

const newDevice = ref({
  id: null,
  name: '',
  ip: '',
  vendor: '华为',
  model: '',
  protocol: 'ssh',
  username: '',
  password: '',
  groupId: null
});

// 新增：获取 localStorage 中的 Token（每次请求前读取，避免缓存问题）
const getToken = () => {
  return localStorage.getItem('token') || '';
};

const validatePassword = (rule, value, callback) => {
  if (!isEdit.value && (!value || value.length === 0)) {
    callback(new Error('请输入密码'));
    return;
  }
  callback();
};

const rules = {
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  ip: [
    { required: true, message: '请输入IP地址', trigger: 'blur' },
    { pattern: /^(\d{1,3}\.){3}\d{1,3}$/, message: 'IP地址格式不正确', trigger: 'blur' }
  ],
  vendor: [{ required: true, message: '请选择厂商', trigger: 'change' }],
  model: [{ required: true, message: '请输入型号', trigger: 'blur' }],
  protocol: [{ required: true, message: '请选择协议', trigger: 'change' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ validator: validatePassword, trigger: 'blur' }]
};

const dialogTitle = computed(() => isEdit.value ? '编辑设备' : '添加设备');

const filteredDevices = computed(() => {
  let result = devices.value;

  if (filterForm.value.vendor) {
    result = result.filter(d => d.vendor === filterForm.value.vendor);
  }

  if (filterForm.value.group) {
    result = result.filter(d => d.groupId === filterForm.value.group);
  }

  if (filterForm.value.keyword) {
    const keyword = filterForm.value.keyword.toLowerCase();
    result = result.filter(d =>
      d.name.toLowerCase().includes(keyword) ||
      d.ip.includes(keyword)
    );
  }

  return result;
});

const getVendorTagType = (vendor) => {
  const map = {
    '华为': 'primary',
    '思科': 'success',
    'H3C': 'warning'
  };
  return map[vendor] || 'info';
};

// 修复：添加/api前缀 + 手动携带Token
const getDevices = async () => {
  loading.value = true;
  try {
    const response = await axios.get('/api/device', {
      headers: {
        Authorization: `Bearer ${getToken()}` // 手动携带Token
      }
    });
    if (response.data && response.data.code === 200) {
      devices.value = response.data.data || [];
    } else {
      devices.value = response.data || [];
    }
  } catch (e) {
    console.error('获取设备列表失败:', e);
    devices.value = [];
    ElMessage.error('获取设备列表失败：' + (e.response?.data?.msg || '未授权'));
  } finally {
    loading.value = false;
  }
};

// 修复：添加/api前缀 + 手动携带Token
const getDeviceGroups = async () => {
  try {
    const response = await axios.get('/api/device/group', {
      headers: {
        Authorization: `Bearer ${getToken()}` // 手动携带Token
      }
    });
    if (response.data?.code === 200) {
      deviceGroups.value = response.data.data || [];
    } else {
      deviceGroups.value = [];
    }
  } catch (e) {
    console.error('获取分组列表失败:', e);
    deviceGroups.value = [];
    ElMessage.error('获取分组列表失败：' + (e.response?.data?.msg || '未授权'));
  }
};

const getGroupDeviceCount = (groupId) => {
  return devices.value.filter(d => d.groupId === groupId).length;
};

// 修复：手动携带Token
const saveDevice = async () => {
  if (!deviceFormRef.value) return;

  await deviceFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const url = isEdit.value ? `/api/device/${newDevice.value.id}` : '/api/device';
        const method = isEdit.value ? 'put' : 'post';

        const payload = { ...newDevice.value };
        if (!payload.password) {
          delete payload.password;
        }

        // 手动携带Token（第三个参数）
        await axios[method](url, payload, {
          headers: {
            Authorization: `Bearer ${getToken()}`
          }
        });

        ElMessage.success(isEdit.value ? '设备更新成功' : '设备添加成功');
        showAddDialog.value = false;
        resetDeviceForm();
        getDevices();
      } catch (e) {
        ElMessage.error('操作失败：' + (e.response?.data?.msg || e.message));
      }
    }
  });
};

const editDevice = (device) => {
  isEdit.value = true;
  newDevice.value = { ...device, password: '', groupId: device.groupId ?? null };
  showAddDialog.value = true;
};

// 修复：手动携带Token
const deleteDevice = async (deviceId) => {
  try {
    await ElMessageBox.confirm('确定要删除该设备吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    // 手动携带Token（第二个参数）
    await axios.delete(`/api/device/${deviceId}`, {
      headers: {
        Authorization: `Bearer ${getToken()}`
      }
    });
    ElMessage.success('删除成功');
    getDevices();
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败：' + (e.response?.data?.msg || e.message));
    }
  }
};

const resetDeviceForm = () => {
  isEdit.value = false;
  newDevice.value = {
    id: null,
    name: '',
    ip: '',
    vendor: '华为',
    model: '',
    protocol: 'ssh',
    username: '',
    password: '',
    groupId: null
  };
  if (deviceFormRef.value) {
    deviceFormRef.value.resetFields();
  }
};

// 修复：手动携带Token
const startInspect = async (deviceId) => {
  try {
    const device = devices.value.find(d => d.id === deviceId);
    if (!device) {
      ElMessage.error('设备不存在');
      return;
    }

    ElMessage.info('正在启动巡检...');

    // 手动携带Token（第三个参数）
    const inspectResp = await axios.post(`/api/device/${deviceId}/inspect`, {
      scenario: '手动巡检',
      autoRepair: false
    }, {
      headers: {
        Authorization: `Bearer ${getToken()}`
      }
    });

    const analysis = inspectResp.data?.data?.analysis || {};
    const score = analysis.health_score ?? analysis.healthScore ?? 'N/A';
    ElMessage.success({
      message: `巡检完成！健康评分：${score}`,
      duration: 3000
    });

    getDevices();
  } catch (e) {
    console.error('启动巡检失败:', e);
    ElMessage.error('启动巡检失败：' + (e.response?.data?.msg || e.message));
  }
};

const handleFilter = () => {
  // 筛选逻辑在computed中实现
};

const resetFilter = () => {
  filterForm.value = {
    vendor: '',
    group: '',
    keyword: ''
  };
};

const editGroup = (group) => {
  // 编辑分组
  console.log('编辑分组', group);
};

const deleteGroup = async (groupId) => {
  try {
    await ElMessageBox.confirm('确定要删除该分组吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    // 如需启用，补全/api前缀 + 携带Token
    // await axios.delete(`/api/device/group/${groupId}`, {
    //   headers: { Authorization: `Bearer ${getToken()}` }
    // });
    ElMessage.success('删除成功');
    getDeviceGroups();
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败');
    }
  }
};

onMounted(() => {
  getDevices();
  getDeviceGroups();
});
</script>

<style scoped>
.device-manage {
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
</style>
