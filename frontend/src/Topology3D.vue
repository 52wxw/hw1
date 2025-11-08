<template>
  <div class="topology-container">
    <el-card class="topology-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span><i class="el-icon-share"></i> 3D 网络拓扑</span>
          <el-button type="primary" size="small" @click="refresh">刷新拓扑</el-button>
        </div>
      </template>
      <div id="three-container" class="three-wrapper"></div>
    </el-card>
  </div>
</template>

<script setup>
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { onMounted, onUnmounted } from 'vue';
import axios from 'axios';

let scene, camera, renderer, controls;
const nodeMeshes = new Map();
const linkLines = [];

const vendorColorMap = {
  '华为': 0x0066cc,
  '思科': 0x009900,
  'H3C': 0xff6600
};

const initScene = () => {
  const container = document.getElementById('three-container');
  const width = container.clientWidth;
  const height = container.clientHeight;

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x101822);

  camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
  camera.position.set(0, 60, 120);

  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(width, height);
  container.appendChild(renderer.domElement);

  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambientLight);
  const dirLight = new THREE.DirectionalLight(0xffffff, 0.6);
  dirLight.position.set(30, 60, 40);
  scene.add(dirLight);

  const grid = new THREE.GridHelper(200, 20, 0x444444, 0x222222);
  scene.add(grid);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.maxDistance = 300;

  const animate = () => {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  };
  animate();

  window.addEventListener('resize', onResize);
};

const onResize = () => {
  const container = document.getElementById('three-container');
  if (!container || !renderer || !camera) return;
  const width = container.clientWidth;
  const height = container.clientHeight;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
};

const clearScene = () => {
  nodeMeshes.forEach((mesh) => scene.remove(mesh));
  nodeMeshes.clear();
  linkLines.forEach((line) => scene.remove(line));
  linkLines.length = 0;
};

const createTextSprite = (text) => {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  const fontSize = 52;
  ctx.font = `${fontSize}px sans-serif`;
  const textWidth = ctx.measureText(text).width;
  canvas.width = textWidth + 60;
  canvas.height = fontSize * 2;
  ctx.font = `${fontSize}px sans-serif`;
  ctx.fillStyle = '#ffffff';
  ctx.strokeStyle = 'rgba(0,0,0,0.6)';
  ctx.lineWidth = 8;
  ctx.strokeText(text, 20, fontSize);
  ctx.fillText(text, 20, fontSize);

  const texture = new THREE.CanvasTexture(canvas);
  const material = new THREE.SpriteMaterial({ map: texture, transparent: true });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(canvas.width / 10, canvas.height / 10, 1);
  return sprite;
};

const renderTopology = (nodes, links) => {
  clearScene();

  const positionMap = new Map();

  nodes.forEach((node) => {
    const color = vendorColorMap[node.vendor] || 0x00aaff;
    const geometry = new THREE.SphereGeometry(4, 32, 32);
    const material = new THREE.MeshStandardMaterial({
      color,
      emissive: node.status === 'online' ? 0x1a8333 : 0x83331a,
      emissiveIntensity: node.status === 'online' ? 0.4 : 0.2
    });
    const sphere = new THREE.Mesh(geometry, material);
    sphere.position.set(node.x, node.y + 4, node.z);
    scene.add(sphere);
    nodeMeshes.set(node.id, sphere);
    positionMap.set(node.id, sphere.position);

    const label = createTextSprite(`${node.name} (${node.ip})`);
    label.position.set(node.x, node.y + 12, node.z);
    scene.add(label);
    linkLines.push(label);
  });

  links.forEach((link) => {
    const start = positionMap.get(link.sourceDeviceId);
    const end = positionMap.get(link.targetDeviceId);

    if (!start || !end) return;

    const points = [start.clone(), end.clone()];
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const material = new THREE.LineBasicMaterial({
      color: link.status.toLowerCase() === 'up' ? 0x66ccff : 0xff5555,
      linewidth: 2
    });
    const line = new THREE.Line(geometry, material);
    scene.add(line);
    linkLines.push(line);
  });
};

const fetchTopology = async () => {
  try {
    const { data } = await axios.get('/api/topology');
    if (data.code === 200) {
      renderTopology(data.data.nodes || [], data.data.links || []);
    }
  } catch (error) {
    console.error('拓扑数据获取失败', error);
  }
};

const refresh = () => {
  fetchTopology();
};

onMounted(() => {
  initScene();
  fetchTopology();
});

onUnmounted(() => {
  window.removeEventListener('resize', onResize);
  if (renderer) {
    renderer.dispose();
  }
  clearScene();
});
</script>

<style scoped>
.topology-container {
  padding: 0 20px 20px;
}

.topology-card {
  border-radius: 12px;
  border: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.three-wrapper {
  width: 100%;
  height: 620px;
}
</style>
