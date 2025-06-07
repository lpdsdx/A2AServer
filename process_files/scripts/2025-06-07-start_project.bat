@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM A2A-MCP 服务器框架启动脚本 (Windows版本)
REM 支持单代理、多代理、MCP、前端等组件的启动

set PROJECT_ROOT=%cd%

REM 创建日志目录
if not exist "%PROJECT_ROOT%\logs" (
    mkdir "%PROJECT_ROOT%\logs"
    echo [INFO] 创建日志目录: %PROJECT_ROOT%\logs
)

REM 检查依赖
:check_dependencies
echo [STEP] 检查系统依赖...

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 未安装，请先安装 Python 3.10+
    exit /b 1
)

node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js 未安装，请先安装 Node.js 16+
    exit /b 1
)

npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm 未安装，请先安装 npm
    exit /b 1
)

pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip 未安装，请先安装 pip
    exit /b 1
)

echo [INFO] 系统依赖检查完成
goto :eof

REM 安装后端依赖
:install_backend_deps
echo [STEP] 安装后端依赖...

cd /d "%PROJECT_ROOT%\backend\A2AServer"
if exist "setup.py" (
    pip install .
    echo [INFO] A2AServer 依赖安装完成
) else if exist "pyproject.toml" (
    pip install .
    echo [INFO] A2AServer 依赖安装完成
) else (
    echo [WARN] 未找到 A2AServer 安装文件
)

cd /d "%PROJECT_ROOT%\frontend\hostAgentAPI"
if exist "requirements.txt" (
    pip install -r requirements.txt
    echo [INFO] hostAgentAPI 依赖安装完成
) else (
    echo [WARN] 未找到 hostAgentAPI requirements.txt
)

cd /d "%PROJECT_ROOT%"
goto :eof

REM 安装前端依赖
:install_frontend_deps
echo [STEP] 安装前端依赖...

cd /d "%PROJECT_ROOT%\frontend\single_agent"
if exist "package.json" (
    npm install
    echo [INFO] 单代理前端依赖安装完成
)

cd /d "%PROJECT_ROOT%\frontend\multiagent_front"
if exist "package.json" (
    npm install
    echo [INFO] 多代理前端依赖安装完成
)

cd /d "%PROJECT_ROOT%"
goto :eof

REM 启动单个代理
:start_agent
set agent_name=%1
set port=%2
set agent_path=%PROJECT_ROOT%\backend\%agent_name%

if not exist "%agent_path%" (
    echo [ERROR] 代理目录不存在: %agent_path%
    goto :eof
)

echo [STEP] 启动 %agent_name% 代理 (端口: %port%)...

cd /d "%agent_path%"

if not exist ".env" (
    echo [WARN] %agent_name% 缺少 .env 文件，请确保已配置 API 密钥
)

REM 后台启动代理
start /b python main.py --port %port% > "%PROJECT_ROOT%\logs\%agent_name%.log" 2>&1

echo [INFO] %agent_name% 已启动 (端口: %port%)
timeout /t 2 /nobreak >nul
goto :eof

REM 启动主机代理
:start_host_agent
echo [STEP] 启动主机代理 (端口: 13000)...

cd /d "%PROJECT_ROOT%\frontend\hostAgentAPI"

REM 后台启动主机代理
start /b python api.py > "%PROJECT_ROOT%\logs\hostAgent.log" 2>&1

echo [INFO] 主机代理已启动 (端口: 13000)
timeout /t 2 /nobreak >nul
goto :eof

REM 启动前端
:start_frontend
set frontend_type=%1
set frontend_path=%PROJECT_ROOT%\frontend\%frontend_type%

if not exist "%frontend_path%" (
    echo [ERROR] 前端目录不存在: %frontend_path%
    goto :eof
)

echo [STEP] 启动 %frontend_type% 前端...

cd /d "%frontend_path%"

REM 后台启动前端
start /b npm run dev > "%PROJECT_ROOT%\logs\%frontend_type%.log" 2>&1

echo [INFO] %frontend_type% 前端已启动
timeout /t 3 /nobreak >nul
goto :eof

REM 启动单代理模式
:start_single_mode
echo [STEP] 启动单代理模式...

call :start_agent AgentRAG 10005
call :start_frontend single_agent

echo [INFO] 单代理模式启动完成!
echo [INFO] 请访问 http://localhost:5173 使用单代理界面
echo [INFO] 代理地址: http://localhost:10005
goto :eof

REM 启动多代理模式
:start_multi_mode
echo [STEP] 启动多代理模式...

call :start_agent AgentRAG 10005
call :start_agent DeepSearch 10004
call :start_agent LNGExpert 10003
call :start_host_agent
call :start_frontend multiagent_front

echo [INFO] 多代理模式启动完成!
echo [INFO] 请访问 http://localhost:5173 使用多代理界面
echo [INFO] 代理地址:
echo [INFO]   - AgentRAG: http://localhost:10005
echo [INFO]   - DeepSearch: http://localhost:10004
echo [INFO]   - LNGExpert: http://localhost:10003
echo [INFO]   - HostAgent: http://localhost:13000
goto :eof

REM 停止所有服务
:stop_all_services
echo [STEP] 停止所有服务...

REM 停止Python进程
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1

REM 清理日志文件
if exist "%PROJECT_ROOT%\logs\*.log" (
    del /q "%PROJECT_ROOT%\logs\*.log"
)

echo [INFO] 所有服务已停止
goto :eof

REM 显示帮助信息
:show_help
echo A2A-MCP 服务器框架启动脚本 (Windows版本)
echo.
echo 用法: %0 [选项]
echo.
echo 选项:
echo   install           安装所有依赖
echo   single            启动单代理模式
echo   multi             启动多代理模式
echo   agent ^<name^>      启动指定代理
echo   frontend ^<type^>   启动前端 (single_agent 或 multiagent_front)
echo   stop              停止所有服务
echo   help              显示此帮助信息
echo.
echo 可用代理:
echo   AgentRAG          RAG代理 (端口: 10005)
echo   DeepSearch        搜索代理 (端口: 10004)
echo   LNGExpert         LNG专家代理 (端口: 10003)
echo   Reference         参考代理 (端口: 10006)
echo.
echo 示例:
echo   %0 install        # 安装所有依赖
echo   %0 single         # 启动单代理模式
echo   %0 multi          # 启动多代理模式
echo   %0 agent AgentRAG # 启动RAG代理
echo   %0 stop           # 停止所有服务
goto :eof

REM 主函数
if "%1"=="install" (
    call :check_dependencies
    call :install_backend_deps
    call :install_frontend_deps
    echo [INFO] 所有依赖安装完成!
) else if "%1"=="single" (
    call :check_dependencies
    call :start_single_mode
) else if "%1"=="multi" (
    call :check_dependencies
    call :start_multi_mode
) else if "%1"=="agent" (
    if "%2"=="" (
        echo [ERROR] 请指定代理名称
        call :show_help
        exit /b 1
    )
    if "%2"=="AgentRAG" (
        call :start_agent AgentRAG 10005
    ) else if "%2"=="DeepSearch" (
        call :start_agent DeepSearch 10004
    ) else if "%2"=="LNGExpert" (
        call :start_agent LNGExpert 10003
    ) else if "%2"=="Reference" (
        call :start_agent Reference 10006
    ) else (
        echo [ERROR] 未知的代理名称: %2
        call :show_help
        exit /b 1
    )
) else if "%1"=="frontend" (
    if "%2"=="" (
        echo [ERROR] 请指定前端类型
        call :show_help
        exit /b 1
    )
    if "%2"=="single_agent" (
        call :start_frontend single_agent
        echo [INFO] 单代理前端已启动，访问: http://localhost:5173
    ) else if "%2"=="single" (
        call :start_frontend single_agent
        echo [INFO] 单代理前端已启动，访问: http://localhost:5173
    ) else if "%2"=="multiagent_front" (
        call :start_frontend multiagent_front
        echo [INFO] 多代理前端已启动，访问: http://localhost:5173
    ) else if "%2"=="multi" (
        call :start_frontend multiagent_front
        echo [INFO] 多代理前端已启动，访问: http://localhost:5173
    ) else (
        echo [ERROR] 未知的前端类型: %2
        call :show_help
        exit /b 1
    )
) else if "%1"=="stop" (
    call :stop_all_services
) else if "%1"=="help" (
    call :show_help
) else if "%1"=="-h" (
    call :show_help
) else if "%1"=="--help" (
    call :show_help
) else if "%1"=="" (
    call :show_help
) else (
    echo [ERROR] 未知选项: %1
    call :show_help
    exit /b 1
)
