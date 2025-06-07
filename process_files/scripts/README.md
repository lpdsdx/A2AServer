# 启动脚本目录

**创建时间**: 2025-06-07  
**目录用途**: 存放项目启动和管理脚本

## 脚本文件说明

### 完整功能脚本
- **`2025-06-07-start_project.sh`** - Linux/macOS完整启动脚本
- **`2025-06-07-start_project.bat`** - Windows完整启动脚本

### 快速启动脚本  
- **`2025-06-07-quick_start.sh`** - Linux/macOS交互式菜单
- **`2025-06-07-quick_start.bat`** - Windows交互式菜单

## 使用方法

### Linux/macOS 系统

#### 快速启动 (推荐)
```bash
cd process_files/scripts
./2025-06-07-quick_start.sh
```

#### 完整功能使用
```bash
cd process_files/scripts

# 安装依赖
./2025-06-07-start_project.sh install

# 启动单代理模式
./2025-06-07-start_project.sh single

# 启动多代理模式
./2025-06-07-start_project.sh multi

# 停止所有服务
./2025-06-07-start_project.sh stop

# 查看帮助
./2025-06-07-start_project.sh help
```

### Windows 系统

#### 快速启动 (推荐)
```cmd
cd process_files\scripts
2025-06-07-quick_start.bat
```

#### 完整功能使用
```cmd
cd process_files\scripts

REM 安装依赖
2025-06-07-start_project.bat install

REM 启动单代理模式
2025-06-07-start_project.bat single

REM 启动多代理模式
2025-06-07-start_project.bat multi

REM 停止所有服务
2025-06-07-start_project.bat stop

REM 查看帮助
2025-06-07-start_project.bat help
```

## 脚本功能特性

### 1. 依赖管理
- 自动检测系统依赖 (Python, Node.js, npm)
- 一键安装后端和前端依赖
- 智能错误提示和解决建议

### 2. 服务管理
- 后台启动所有服务
- 统一的进程管理 (PID文件)
- 优雅的服务停止机制
- 实时服务状态检查

### 3. 日志管理
- 统一日志目录 (`../../logs/`)
- 按服务分类的日志文件
- 支持实时日志查看
- 便于问题排查和调试

### 4. 启动模式
- **单代理模式**: AgentRAG + 单代理前端
- **多代理模式**: 多个代理 + 主机代理 + 多代理前端
- **组件模式**: 可单独启动任意代理或前端

## 端口配置

| 组件 | 端口 | 说明 |
|------|------|------|
| AgentRAG | 10005 | RAG代理服务 |
| DeepSearch | 10004 | 搜索代理服务 |
| LNGExpert | 10003 | LNG专家代理服务 |
| Reference | 10006 | 参考代理服务 |
| hostAgentAPI | 13000 | 多代理协调服务 |
| 前端界面 | 5173 | Vite开发服务器 |

## 注意事项

### 路径问题
- 脚本需要在项目根目录的相对路径下运行
- 日志文件会创建在项目根目录的 `logs/` 目录
- 确保脚本有足够的文件系统权限

### 环境配置
- 各代理目录需要配置 `.env` 文件
- 确保API密钥等敏感信息已正确配置
- 检查端口是否被其他程序占用

### 依赖要求
- Python 3.10+
- Node.js 16+
- npm 最新版本
- 足够的系统资源 (内存4GB+推荐)

## 故障排除

### 常见问题
1. **权限错误**: 确保脚本有执行权限 (`chmod +x *.sh`)
2. **端口冲突**: 检查端口占用情况，停止冲突程序
3. **依赖缺失**: 重新运行 `install` 命令
4. **API密钥错误**: 检查各代理的 `.env` 文件配置

### 日志查看
```bash
# 查看特定服务日志
./2025-06-07-start_project.sh logs AgentRAG

# 查看所有日志文件
ls -la ../../logs/
```

## 版本信息

- **创建日期**: 2025-06-07
- **版本**: v1.0
- **兼容性**: 支持 Linux/macOS 和 Windows
- **依赖**: A2A-MCP 项目框架

## 相关文档

- [启动脚本使用说明](../documentation/2025-06-07-启动脚本使用说明.md)
- [项目启动指南](../documentation/2025-06-07-项目启动指南.md)
- [项目架构分析](../analysis/2025-06-07-项目架构分析.md)
- [开发总结](../daily_summaries/2025-06-07-启动脚本开发总结.md)
