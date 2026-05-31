# 部署指南

基于第一性原理的Agent可靠记忆系统 - 部署说明

## 部署方式

### 方式1：本地开发部署

```bash
# 1. 克隆/下载项目
cd /path/to/memory-system

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 配置

# 4. 创建必要的目录
mkdir -p data logs

# 5. 运行测试
python test_phase5_unit_tests.py

# 6. 启动API服务
python examples/api_server.py
```

### 方式2：Docker部署

```bash
# 1. 构建镜像
docker build -t agent-memory-system:latest .

# 2. 运行容器
docker run -d \
  --name agent-memory \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  --health-cmd "python -c 'import requests; requests.get(\"http://localhost:5000/health\")'" \
  --health-interval 30s \
  --health-timeout 10s \
  --health-retries 3 \
  agent-memory-system:latest

# 3. 查看状态
docker ps
docker logs agent-memory -f
```

### 方式3：Docker Compose部署

```bash
# 1. 启动服务
docker-compose up -d

# 2. 查看状态
docker-compose ps

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down
```

### 方式4：Kubernetes部署

```bash
# 1. 构建镜像（可选，如果已有镜像）
docker build -t agent-memory-system:latest .

# 2. 应用配置
kubectl apply -f deploy/kubernetes.yaml

# 3. 查看状态
kubectl get pods -n agent-memory-system
kubectl get svc -n agent-memory-system

# 4. 查看日志
kubectl logs -f deployment/memory-system -n agent-memory-system
```

## 配置说明

### 环境变量

所有配置项都可以通过环境变量设置：

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `LOG_LEVEL` | INFO | 日志级别 |
| `LOG_DIR` | ./logs | 日志目录 |
| `DATA_DIR` | ./data | 数据目录 |
| `L1_MAX_ITEMS` | 100 | L1单任务最大数量 |
| `L2_CLEANUP_DAYS` | 30 | L2清理周期（天） |
| `L2_SIMILARITY_THRESHOLD` | 0.7 | L2相似度阈值 |
| `API_HOST` | 0.0.0.0 | API监听地址 |
| `API_PORT` | 5000 | API监听端口 |

### 配置热更新

可以通过API触发配置热更新：

```bash
curl -X POST http://localhost:5000/api/v1/config/reload
```

## 监控与日志

### 健康检查

访问健康检查端点：

```bash
curl http://localhost:5000/health
```

响应示例：

```json
{
  "status": "healthy",
  "timestamp": 1700000000,
  "version": "1.0.0"
}
```

### 查看统计

```bash
curl http://localhost:5000/api/v1/stats
```

### 日志查看

```bash
# 本地开发
tail -f logs/agent-memory-*.log

# Docker
docker logs agent-memory -f

# Kubernetes
kubectl logs -f deployment/memory-system -n agent-memory-system
```

## 数据备份与恢复

### 备份数据

```bash
# 备份数据目录
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Docker中备份
docker exec agent-memory tar -czf /tmp/data-backup.tar.gz /app/data
docker cp agent-memory:/tmp/data-backup.tar.gz ./backup/
```

### 恢复数据

```bash
# 恢复数据
tar -xzf backup-20260525.tar.gz -C ./

# Docker中恢复
docker cp ./data-backup.tar.gz agent-memory:/tmp/
docker exec agent-memory tar -xzf /tmp/data-backup.tar.gz -C /app/
```

## 性能优化

### 垂直扩展

增加容器资源：

```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2"
```

### 水平扩展

增加副本数：

```bash
# Kubernetes
kubectl scale deployment/memory-system --replicas=5 -n agent-memory-system

# Docker Compose
docker-compose up -d --scale memory-system=3
```

## 故障排查

### 常见问题

#### 问题：API服务无法启动
- 检查端口是否被占用：`netstat -tlnp | grep 5000`
- 检查依赖是否完整：`pip list | grep flask`
- 查看日志：`tail -f logs/agent-memory-*.log`

#### 问题：健康检查失败
- 检查服务是否正常运行：`ps aux | grep python`
- 检查数据库文件权限：`ls -la data/`

#### 问题：内存占用过高
- 减少L1最大数量：`L1_MAX_ITEMS=50`
- 启用更频繁的清理：`L2_CLEANUP_DAYS=7`
- 增加系统监控

## 安全建议

1. **网络安全**：
   - 使用反向代理（Nginx）
   - 启用HTTPS
   - 配置防火墙规则

2. **数据安全**：
   - 定期备份数据
   - 使用加密存储（生产环境）
   - 配置访问控制

3. **API安全**：
   - 添加认证机制
   - 配置限流策略
   - 审计API访问日志
