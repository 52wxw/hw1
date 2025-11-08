#!/bin/bash
# 初始化FISCO BCOS单节点链并部署合约

# 创建节点目录
mkdir -p /data/node
cd /data/node

# 生成配置
fisco-bcos genesis -g genesis.json -p 30303 -r 8545 -b 2020000000

# 生成证书
fisco-bcos cert -o .

# 启动节点（后台运行）
fisco-bcos node -c config.ini -d

# 等待节点启动
sleep 10

# 部署合约并记录地址
CONTRACT_ADDRESS=$(fisco-bcos deploy --abi /app/contract/LogStore.abi --bin /app/contract/LogStore.bin --url http://localhost:8545 | grep "contract address" | awk '{print $3}')

# 输出合约地址（供用户配置到.env）
echo "合约部署成功，地址：$CONTRACT_ADDRESS"
echo "请将此地址配置到.env的BLOCKCHAIN_CONTRACT_ADDRESS"

# 保持节点运行
tail -f /data/node/log/log*
