<template>
  <div class="topology-container">
    <el-card>
      <div slot="header">3D网络拓扑图</div>
      <div id="three-container" style="width:100%;height:600px;"></div>
      <el-button @click="refresh">刷新拓扑</el-button>
    </el-card>
  </div>
</template>

<script setup>
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { onMounted, onUnmounted } from 'vue';
import axios from 'axios';

let scene, camera, renderer, controls;
let deviceLabels = []; // 存储设备标签，用于刷新时清理

// 初始化3D场景
const initScene = () => {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x1e1e1e);
  
  camera = new THREE.PerspectiveCamera(75, window.innerWidth / 600, 0.1, 1000);
  camera.position.set(0, 10, 20);
  
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(window.innerWidth, 600);
  document.getElementById('three-container').appendChild(renderer.domElement);
  
  // 光源
  const dirLight = new THREE.DirectionalLight(0xffffff, 1);
  dirLight.position.set(10, 10, 10);
  scene.add(dirLight);
  
  // 控制器
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  
  // 地面
  const groundGeo = new THREE.PlaneGeometry(50, 50);
  const groundMat = new THREE.MeshBasicMaterial({ color: 0x333333 });
  const ground = new THREE.Mesh(groundGeo, groundMat);
  ground.rotation.x = -Math.PI / 2;
  scene.add(ground);
  
  // 动画循环
  const animate = () => {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  };
  animate();
};

// 绘制设备节点
const drawDevices = async () => {
  // 清理旧标签
  deviceLabels.forEach(div => div.remove());
  deviceLabels = [];
  
  try {
    const { data } = await axios.get('/api/device');
    const devices = data.data || [];
    
    const geo = new THREE.BoxGeometry(2, 2, 2);
    devices.forEach((dev, i) => {
      // 按状态和厂商着色（在线绿色，离线红色）
      const baseColor = dev.status === 'online' ? 0x00ff00 : 0xff0000;
      const vendorColor = { "华为": 0x0066cc, "思科": 0x009900 }[dev.vendor] || baseColor;
      const mat = new THREE.MeshBasicMaterial({ color: vendorColor });
      const cube = new THREE.Mesh(geo, mat);
      cube.position.set(i * 5 - 10, 1, 0);
      scene.add(cube);
      
      // 设备标签（挂载到three-container内）
      const container = document.getElementById('three-container');
      const div = document.createElement('div');
      div.className = 'device-label';
      div.style.cssText = `position:absolute; color:white; font-size:12px; pointer-events:none;`;
      div.innerHTML = `${dev.name}(${dev.ip})<br>${dev.status}`;
      container.appendChild(div);
      deviceLabels.push(div);
      
      // 标签位置更新
      const updateLabel = () => {
        const pos = new THREE.Vector3();
        pos.setFromMatrixPosition(cube.matrixWorld);
        pos.project(camera);
        const x = (pos.x * 0.5 + 0.5) * container.clientWidth;
        const y = (-pos.y * 0.5 + 0.5) * container.clientHeight;
        div.style.left = `${x}px`;
        div.style.top = `${y}px`;
      };
      controls.addEventListener('change', updateLabel);
    });
  } catch (e) {
    console.error("绘制设备失败：", e);
  }
};

// 绘制链路
const drawLinks = async () => {
  try {
    const { data } = await axios.get('/api/links');
    const links = data.data || [];
    
    const lineMat = new THREE.LineBasicMaterial({ color: 0xcccccc });
    links.forEach(link => {
      const start = new THREE.Vector3(link.src_x, 1, link.src_z);
      const end = new THREE.Vector3(link.dst_x, 1, link.dst_z);
      const lineGeo = new THREE.BufferGeometry().setFromPoints([start, end]);
      const line = new THREE.Line(lineGeo, lineMat);
      scene.add(line);
    });
  } catch (e) {
    console.error("绘制链路失败：", e);
  }
};

// 刷新拓扑
const refresh = () => {
  // 清空场景（保留光源和地面）
  scene.children = scene.children.filter(child => 
    child.type === 'DirectionalLight' || (child.type === 'Mesh' && child.geometry.type === 'PlaneGeometry')
  );
  drawDevices();
  drawLinks();
};

onMounted(() => {
  initScene();
  drawDevices();
  drawLinks();
});

// 组件卸载时清理
onUnmounted(() => {
  deviceLabels.forEach(div => div.remove());
  if (renderer) renderer.dispose();
});
</script>
