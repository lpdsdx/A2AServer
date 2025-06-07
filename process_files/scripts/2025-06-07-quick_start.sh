#!/bin/bash

# A2A-MCP 快速启动脚本
# 一键启动项目的常用模式

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== A2A-MCP 服务器框架快速启动 ===${NC}"
echo ""

# 显示选项菜单
show_menu() {
    echo "请选择启动模式："
    echo ""
    echo "1) 🔧 安装所有依赖"
    echo "2) 🚀 单代理模式 (AgentRAG + 前端)"
    echo "3) 🌐 多代理模式 (完整系统)"
    echo "4) 🛑 停止所有服务"
    echo "5) 📊 查看服务状态"
    echo "6) ❓ 显示帮助"
    echo "0) 退出"
    echo ""
}

# 等待用户输入
wait_for_input() {
    echo -e "${YELLOW}按回车键继续...${NC}"
    read
}

# 主循环
while true; do
    show_menu
    read -p "请输入选项 (0-6): " choice
    echo ""
    
    case $choice in
        1)
            echo -e "${GREEN}正在安装所有依赖...${NC}"
            ./start_project.sh install
            wait_for_input
            ;;
        2)
            echo -e "${GREEN}启动单代理模式...${NC}"
            ./start_project.sh single
            echo ""
            echo -e "${GREEN}✅ 单代理模式已启动！${NC}"
            echo "🌐 前端地址: http://localhost:5173"
            echo "🤖 代理地址: http://localhost:10005"
            wait_for_input
            ;;
        3)
            echo -e "${GREEN}启动多代理模式...${NC}"
            ./start_project.sh multi
            echo ""
            echo -e "${GREEN}✅ 多代理模式已启动！${NC}"
            echo "🌐 前端地址: http://localhost:5173"
            echo "🤖 代理地址:"
            echo "   - AgentRAG: http://localhost:10005"
            echo "   - DeepSearch: http://localhost:10004"
            echo "   - LNGExpert: http://localhost:10003"
            echo "   - HostAgent: http://localhost:13000"
            wait_for_input
            ;;
        4)
            echo -e "${GREEN}停止所有服务...${NC}"
            ./start_project.sh stop
            echo -e "${GREEN}✅ 所有服务已停止${NC}"
            wait_for_input
            ;;
        5)
            echo -e "${GREEN}检查服务状态...${NC}"
            ./start_project.sh status
            wait_for_input
            ;;
        6)
            echo -e "${GREEN}显示详细帮助...${NC}"
            ./start_project.sh help
            wait_for_input
            ;;
        0)
            echo -e "${GREEN}再见！${NC}"
            exit 0
            ;;
        *)
            echo -e "${YELLOW}无效选项，请重新选择${NC}"
            sleep 1
            ;;
    esac
    
    clear
done
