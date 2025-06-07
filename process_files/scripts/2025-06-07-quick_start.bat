@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM A2A-MCP 快速启动脚本 (Windows版本)
REM 一键启动项目的常用模式

title A2A-MCP 服务器框架快速启动

:main_menu
cls
echo ===============================================
echo    A2A-MCP 服务器框架快速启动
echo ===============================================
echo.
echo 请选择启动模式：
echo.
echo 1) 🔧 安装所有依赖
echo 2) 🚀 单代理模式 (AgentRAG + 前端)
echo 3) 🌐 多代理模式 (完整系统)
echo 4) 🛑 停止所有服务
echo 5) ❓ 显示帮助
echo 0) 退出
echo.

set /p choice="请输入选项 (0-5): "

if "%choice%"=="1" goto install_deps
if "%choice%"=="2" goto single_mode
if "%choice%"=="3" goto multi_mode
if "%choice%"=="4" goto stop_services
if "%choice%"=="5" goto show_help
if "%choice%"=="0" goto exit_script

echo 无效选项，请重新选择
timeout /t 2 /nobreak >nul
goto main_menu

:install_deps
echo.
echo [INFO] 正在安装所有依赖...
call start_project.bat install
echo.
echo [INFO] ✅ 依赖安装完成！
pause
goto main_menu

:single_mode
echo.
echo [INFO] 启动单代理模式...
call start_project.bat single
echo.
echo [INFO] ✅ 单代理模式已启动！
echo [INFO] 🌐 前端地址: http://localhost:5173
echo [INFO] 🤖 代理地址: http://localhost:10005
echo.
echo 提示：请在浏览器中访问前端地址开始使用
pause
goto main_menu

:multi_mode
echo.
echo [INFO] 启动多代理模式...
call start_project.bat multi
echo.
echo [INFO] ✅ 多代理模式已启动！
echo [INFO] 🌐 前端地址: http://localhost:5173
echo [INFO] 🤖 代理地址:
echo [INFO]    - AgentRAG: http://localhost:10005
echo [INFO]    - DeepSearch: http://localhost:10004
echo [INFO]    - LNGExpert: http://localhost:10003
echo [INFO]    - HostAgent: http://localhost:13000
echo.
echo 提示：请在浏览器中访问前端地址开始使用
pause
goto main_menu

:stop_services
echo.
echo [INFO] 停止所有服务...
call start_project.bat stop
echo.
echo [INFO] ✅ 所有服务已停止
pause
goto main_menu

:show_help
echo.
echo [INFO] 显示详细帮助...
call start_project.bat help
echo.
pause
goto main_menu

:exit_script
echo.
echo 再见！
timeout /t 2 /nobreak >nul
exit /b 0
