#!/bin/bash

# A2A-MCP 服务器框架启动脚本
# 支持单代理、多代理、MCP、前端等组件的启动

# 移除 set -e，改为手动错误处理，避免脚本意外退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT=$(pwd)

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_step "检查系统依赖..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装，请先安装 Python 3.10+"
        exit 1
    fi
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装，请先安装 Node.js 16+"
        exit 1
    fi
    
    # 检查npm
    if ! command -v npm &> /dev/null; then
        log_error "npm 未安装，请先安装 npm"
        exit 1
    fi
    
    # 检查pip
    if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
        log_error "pip 未安装，请先安装 pip"
        exit 1
    fi
    
    log_info "系统依赖检查完成"
}

# 安装后端依赖
install_backend_deps() {
    log_step "安装后端依赖..."
    
    cd "$PROJECT_ROOT/backend/A2AServer"
    if [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
        pip install . || pip3 install .
        log_info "A2AServer 依赖安装完成"
    else
        log_warn "未找到 A2AServer 安装文件"
    fi
    
    # 安装 hostAgentAPI 依赖
    cd "$PROJECT_ROOT/frontend/hostAgentAPI"
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt || pip3 install -r requirements.txt
        log_info "hostAgentAPI 依赖安装完成"
    else
        log_warn "未找到 hostAgentAPI requirements.txt"
    fi
    
    cd "$PROJECT_ROOT"
}

# 安装前端依赖
install_frontend_deps() {
    log_step "安装前端依赖..."
    
    # 安装单代理前端依赖
    cd "$PROJECT_ROOT/frontend/single_agent"
    if [ -f "package.json" ]; then
        npm install
        log_info "单代理前端依赖安装完成"
    fi
    
    # 安装多代理前端依赖
    cd "$PROJECT_ROOT/frontend/multiagent_front"
    if [ -f "package.json" ]; then
        npm install
        log_info "多代理前端依赖安装完成"
    fi
    
    cd "$PROJECT_ROOT"
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # 端口被占用
    else
        return 1  # 端口空闲
    fi
}

# 等待服务启动
wait_for_service() {
    local port=$1
    local service_name=$2
    local max_wait=30
    local count=0

    log_info "等待 $service_name 启动 (端口: $port)..."

    while [ $count -lt $max_wait ]; do
        if check_port $port; then
            log_info "$service_name 启动成功！"
            return 0
        fi
        sleep 1
        count=$((count + 1))
        echo -n "."
    done

    echo ""
    log_error "$service_name 启动失败或超时"
    return 1
}

# 启动单个代理
start_agent() {
    local agent_name=$1
    local port=$2
    local agent_path="$PROJECT_ROOT/backend/$agent_name"

    if [ ! -d "$agent_path" ]; then
        log_error "代理目录不存在: $agent_path"
        return 1
    fi

    # 检查端口是否已被占用
    if check_port $port; then
        log_warn "$agent_name 端口 $port 已被占用，跳过启动"
        return 0
    fi

    log_step "启动 $agent_name 代理 (端口: $port)..."

    cd "$agent_path"

    # 检查是否有 .env 文件
    if [ ! -f ".env" ]; then
        log_warn "$agent_name 缺少 .env 文件，请确保已配置 API 密钥"
    fi

    # 检查main.py是否存在
    if [ ! -f "main.py" ]; then
        log_error "$agent_name 目录中未找到 main.py 文件"
        return 1
    fi

    # 后台启动代理，设置PYTHONPATH以使用工作区内的代码
    nohup env PYTHONPATH="$PROJECT_ROOT/backend/A2AServer/src:$PYTHONPATH" python main.py --port $port > "$PROJECT_ROOT/logs/${agent_name}.log" 2>&1 &
    local pid=$!
    echo $pid > "$PROJECT_ROOT/logs/${agent_name}.pid"

    log_info "$agent_name 已启动 (PID: $pid, 端口: $port)"

    # 等待服务启动
    if wait_for_service $port "$agent_name"; then
        return 0
    else
        log_error "$agent_name 启动失败，请检查日志: $PROJECT_ROOT/logs/${agent_name}.log"
        return 1
    fi
}

# 启动主机代理
start_host_agent() {
    local port=13000

    # 检查端口是否已被占用
    if check_port $port; then
        log_warn "主机代理端口 $port 已被占用，跳过启动"
        return 0
    fi

    log_step "启动主机代理 (端口: $port)..."

    cd "$PROJECT_ROOT/frontend/hostAgentAPI"

    # 检查api.py是否存在
    if [ ! -f "api.py" ]; then
        log_error "hostAgentAPI 目录中未找到 api.py 文件"
        return 1
    fi

    # 后台启动主机代理
    nohup python api.py > "$PROJECT_ROOT/logs/hostAgent.log" 2>&1 &
    local pid=$!
    echo $pid > "$PROJECT_ROOT/logs/hostAgent.pid"

    log_info "主机代理已启动 (PID: $pid, 端口: $port)"

    # 等待服务启动
    if wait_for_service $port "主机代理"; then
        return 0
    else
        log_error "主机代理启动失败，请检查日志: $PROJECT_ROOT/logs/hostAgent.log"
        return 1
    fi
}

# 启动前端
start_frontend() {
    local frontend_type=$1
    local frontend_path="$PROJECT_ROOT/frontend/$frontend_type"
    local port=5173  # Vite默认端口

    if [ ! -d "$frontend_path" ]; then
        log_error "前端目录不存在: $frontend_path"
        return 1
    fi

    # 检查端口是否已被占用
    if check_port $port; then
        log_warn "$frontend_type 前端端口 $port 已被占用，跳过启动"
        return 0
    fi

    log_step "启动 $frontend_type 前端..."

    cd "$frontend_path"

    # 检查package.json是否存在
    if [ ! -f "package.json" ]; then
        log_error "$frontend_type 目录中未找到 package.json 文件"
        return 1
    fi

    # 检查node_modules是否存在
    if [ ! -d "node_modules" ]; then
        log_warn "$frontend_type 缺少 node_modules，正在安装依赖..."
        npm install
    fi

    # 后台启动前端
    nohup npm run dev > "$PROJECT_ROOT/logs/${frontend_type}.log" 2>&1 &
    local pid=$!
    echo $pid > "$PROJECT_ROOT/logs/${frontend_type}.pid"

    log_info "$frontend_type 前端已启动 (PID: $pid)"

    # 等待前端启动（前端启动较慢）
    if wait_for_service $port "$frontend_type 前端"; then
        return 0
    else
        log_error "$frontend_type 前端启动失败，请检查日志: $PROJECT_ROOT/logs/${frontend_type}.log"
        return 1
    fi
}

# 创建日志目录
create_log_dir() {
    if [ ! -d "$PROJECT_ROOT/logs" ]; then
        mkdir -p "$PROJECT_ROOT/logs"
        log_info "创建日志目录: $PROJECT_ROOT/logs"
    fi
}

# 停止所有服务
stop_all_services() {
    log_step "停止所有服务..."
    
    # 停止所有后台进程
    for pidfile in "$PROJECT_ROOT/logs"/*.pid; do
        if [ -f "$pidfile" ]; then
            local pid=$(cat "$pidfile")
            local service_name=$(basename "$pidfile" .pid)
            
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid"
                log_info "已停止 $service_name (PID: $pid)"
            else
                log_warn "$service_name 进程 (PID: $pid) 不存在"
            fi
            
            rm -f "$pidfile"
        fi
    done
    
    log_info "所有服务已停止"
}

# 检查服务状态
check_services_status() {
    log_step "检查服务状态..."
    
    for pidfile in "$PROJECT_ROOT/logs"/*.pid; do
        if [ -f "$pidfile" ]; then
            local pid=$(cat "$pidfile")
            local service_name=$(basename "$pidfile" .pid)
            
            if kill -0 "$pid" 2>/dev/null; then
                log_info "$service_name 正在运行 (PID: $pid)"
            else
                log_warn "$service_name 未运行"
            fi
        fi
    done
}

# 显示帮助信息
show_help() {
    echo "A2A-MCP 服务器框架启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  install           安装所有依赖"
    echo "  single            启动单代理模式"
    echo "  multi             启动多代理模式"
    echo "  agent <name>      启动指定代理"
    echo "  frontend <type>   启动前端 (single_agent 或 multiagent_front)"
    echo "  stop              停止所有服务"
    echo "  status            检查服务状态"
    echo "  logs <service>    查看指定服务日志"
    echo "  logs-all          显示所有日志文件"
    echo "  help              显示此帮助信息"
    echo ""
    echo "可用代理:"
    echo "  AgentRAG          RAG代理 (端口: 10005)"
    echo "  DeepSearch        搜索代理 (端口: 10004)"
    echo "  LNGExpert         LNG专家代理 (端口: 10003)"
    echo "  Reference         参考代理 (端口: 10006)"
    echo ""
    echo "示例:"
    echo "  $0 install        # 安装所有依赖"
    echo "  $0 single         # 启动单代理模式"
    echo "  $0 multi          # 启动多代理模式"
    echo "  $0 agent AgentRAG # 启动RAG代理"
    echo "  $0 stop           # 停止所有服务"
}

# 查看日志
show_logs() {
    local service_name=$1
    local log_file="$PROJECT_ROOT/logs/${service_name}.log"

    if [ -f "$log_file" ]; then
        log_info "显示 $service_name 日志 (按 Ctrl+C 退出):"
        echo "----------------------------------------"
        tail -f "$log_file"
    else
        log_error "日志文件不存在: $log_file"
        echo ""
        log_info "可用的日志文件:"
        if [ -d "$PROJECT_ROOT/logs" ]; then
            ls -la "$PROJECT_ROOT/logs"/*.log 2>/dev/null || log_warn "暂无日志文件"
        else
            log_warn "日志目录不存在"
        fi
    fi
}

# 显示所有日志文件
show_all_logs() {
    log_info "所有服务日志文件:"
    if [ -d "$PROJECT_ROOT/logs" ]; then
        for log_file in "$PROJECT_ROOT/logs"/*.log; do
            if [ -f "$log_file" ]; then
                local service_name=$(basename "$log_file" .log)
                local file_size=$(du -h "$log_file" | cut -f1)
                log_info "  - $service_name: $log_file ($file_size)"
            fi
        done
    else
        log_warn "日志目录不存在"
    fi
}

# 启动单代理模式
start_single_mode() {
    log_step "启动单代理模式..."

    create_log_dir

    # 启动 AgentRAG
    if start_agent "AgentRAG" 10005; then
        log_info "AgentRAG 代理启动成功"
    else
        log_error "AgentRAG 代理启动失败，请检查日志"
        return 1
    fi

    # 启动单代理前端
    if start_frontend "single_agent"; then
        log_info "单代理前端启动成功"
    else
        log_error "单代理前端启动失败，请检查日志"
        return 1
    fi

    echo ""
    log_info "🎉 单代理模式启动完成!"
    log_info "🌐 请访问 http://localhost:5173 使用单代理界面"
    log_info "🤖 代理地址: http://localhost:10005"
    echo ""
    log_info "💡 提示: 使用 '$0 stop' 停止所有服务"
    log_info "📋 查看状态: '$0 status'"
    log_info "📝 查看日志: '$0 logs <服务名>'"
}

# 启动多代理模式
start_multi_mode() {
    log_step "启动多代理模式..."

    create_log_dir

    local failed_services=()

    # 启动多个代理
    log_step "启动代理服务..."

    if start_agent "AgentRAG" 10005; then
        log_info "✅ AgentRAG 代理启动成功"
    else
        log_error "❌ AgentRAG 代理启动失败"
        failed_services+=("AgentRAG")
    fi

    if start_agent "DeepSearch" 10004; then
        log_info "✅ DeepSearch 代理启动成功"
    else
        log_error "❌ DeepSearch 代理启动失败"
        failed_services+=("DeepSearch")
    fi

    if start_agent "LNGExpert" 10003; then
        log_info "✅ LNGExpert 代理启动成功"
    else
        log_error "❌ LNGExpert 代理启动失败"
        failed_services+=("LNGExpert")
    fi

    # 启动主机代理
    log_step "启动主机代理..."
    if start_host_agent; then
        log_info "✅ 主机代理启动成功"
    else
        log_error "❌ 主机代理启动失败"
        failed_services+=("HostAgent")
    fi

    # 启动多代理前端
    log_step "启动多代理前端..."
    if start_frontend "multiagent_front"; then
        log_info "✅ 多代理前端启动成功"
    else
        log_error "❌ 多代理前端启动失败"
        failed_services+=("MultiAgent Frontend")
    fi

    echo ""
    if [ ${#failed_services[@]} -eq 0 ]; then
        log_info "🎉 多代理模式启动完成!"
    else
        log_warn "⚠️  多代理模式部分启动完成，以下服务启动失败:"
        for service in "${failed_services[@]}"; do
            log_error "  - $service"
        done
    fi

    echo ""
    log_info "🌐 请访问 http://localhost:5173 使用多代理界面"
    log_info "🤖 代理地址:"
    log_info "  - AgentRAG: http://localhost:10005"
    log_info "  - DeepSearch: http://localhost:10004"
    log_info "  - LNGExpert: http://localhost:10003"
    log_info "  - HostAgent: http://localhost:13000"
    echo ""
    log_info "💡 提示: 使用 '$0 stop' 停止所有服务"
    log_info "📋 查看状态: '$0 status'"
    log_info "📝 查看日志: '$0 logs <服务名>'"
}

# 主函数
main() {
    case "$1" in
        "install")
            check_dependencies
            install_backend_deps
            install_frontend_deps
            log_info "所有依赖安装完成!"
            ;;
        "single")
            check_dependencies
            start_single_mode
            ;;
        "multi")
            check_dependencies
            start_multi_mode
            ;;
        "agent")
            if [ -z "$2" ]; then
                log_error "请指定代理名称"
                show_help
                exit 1
            fi

            create_log_dir

            case "$2" in
                "AgentRAG")
                    start_agent "AgentRAG" 10005
                    ;;
                "DeepSearch")
                    start_agent "DeepSearch" 10004
                    ;;
                "LNGExpert")
                    start_agent "LNGExpert" 10003
                    ;;
                "Reference")
                    start_agent "Reference" 10006
                    ;;
                *)
                    log_error "未知的代理名称: $2"
                    show_help
                    exit 1
                    ;;
            esac
            ;;
        "frontend")
            if [ -z "$2" ]; then
                log_error "请指定前端类型"
                show_help
                exit 1
            fi

            create_log_dir

            case "$2" in
                "single_agent"|"single")
                    start_frontend "single_agent"
                    log_info "单代理前端已启动，访问: http://localhost:5173"
                    ;;
                "multiagent_front"|"multi")
                    start_frontend "multiagent_front"
                    log_info "多代理前端已启动，访问: http://localhost:5173"
                    ;;
                *)
                    log_error "未知的前端类型: $2"
                    show_help
                    exit 1
                    ;;
            esac
            ;;
        "stop")
            stop_all_services
            ;;
        "status")
            check_services_status
            ;;
        "logs")
            if [ -z "$2" ]; then
                log_error "请指定服务名称"
                echo ""
                show_all_logs
                exit 1
            fi
            show_logs "$2"
            ;;
        "logs-all")
            show_all_logs
            ;;
        "help"|"-h"|"--help"|"")
            show_help
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
