import time
import json
import matplotlib.pyplot as plt
from langchain.llms import Ollama

# 加载标注数据集（1000条故障样本）
with open("tests/fault_dataset.json", "r", encoding="utf-8") as f:
    dataset = json.load(f)

# 测试模型列表
models = [
    "deepseek-r1:7b",          # 原始模型
    "deepseek-r1:7b-finetuned",# 微调模型
    "llama3:8b",
    "qwen:7b"
]

# 性能指标存储
results = {
    "model": [],
    "accuracy": [],  # 故障识别准确率
    "avg_time": []   # 平均推理时间（秒）
}

for model in models:
    llm = Ollama(model=model, base_url="http://localhost:11434")
    correct = 0
    total_time = 0
    
    for sample in dataset[:100]:  # 取前100条测试
        # 记录推理时间
        start = time.time()
        response = llm(sample["prompt"])
        total_time += (time.time() - start)
        
        # 判断是否正确识别故障类型
        if sample["fault_type"] in response and sample["level"] in response:
            correct += 1
    
    # 计算指标
    acc = correct / 100
    avg_t = total_time / 100
    results["model"].append(model)
    results["accuracy"].append(acc)
    results["avg_time"].append(avg_t)
    print(f"模型 {model} 测试完成：准确率{acc:.2f}，平均耗时{avg_t:.2f}秒")

# 生成对比图表（保存为论文插图）
plt.figure(figsize=(12, 5))
# 准确率柱状图
plt.subplot(1, 2, 1)
plt.bar(results["model"], results["accuracy"], color='skyblue')
plt.title("模型故障识别准确率对比")
plt.ylim(0, 1.0)
plt.xticks(rotation=30)
# 推理时间柱状图
plt.subplot(1, 2, 2)
plt.bar(results["model"], results["avg_time"], color='lightgreen')
plt.title("模型平均推理时间对比（秒）")
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig("tests/model_performance.png")
plt.show()
