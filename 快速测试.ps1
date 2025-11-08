# 快速测试脚本
# 用于一键测试认证系统

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('all', 'backend', 'frontend', 'switch')]
    [string]$Test = 'all'
)

$ErrorActionPreference = "Continue"

function Write-ColorText {
    param(
        [string]$Text,
        [string]$Color = "White"
    )
    Write-Host $Text -ForegroundColor $Color
}

function Write-Header {
    param([string]$Text)
    Write-Host "`n" -NoNewline
    Write-ColorText "==========================================" "Cyan"
    Write-ColorText "  $Text" "Yellow"
    Write-ColorText "==========================================" "Cyan"
}

function Test-ServerRunning {
    param([string]$Url, [string]$Name)
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-ColorText "✓ $Name 运行正常" "Green"
            return $true
        }
    }
    catch {
        Write-ColorText "✗ $Name 未运行" "Red"
        return $false
    }
    return $false
}

function Show-Menu {
    Write-Header "认证系统快速测试"
    Write-Host ""
    Write-Host "1. 检查服务状态" -ForegroundColor Green
    Write-Host "2. 测试后端API" -ForegroundColor Green
    Write-Host "3. 打开前端测试页面" -ForegroundColor Green
    Write-Host "4. 切换认证模式" -ForegroundColor Yellow
    Write-Host "5. 启动后端服务" -ForegroundColor Cyan
    Write-Host "6. 启动前端服务" -ForegroundColor Cyan
    Write-Host "7. 查看当前配置" -ForegroundColor Blue
    Write-Host "8. 完整测试流程" -ForegroundColor Magenta
    Write-Host "9. 退出" -ForegroundColor Gray
    Write-Host ""
    Write-ColorText "==========================================" "Cyan"
}

function Check-ServiceStatus {
    Write-Header "检查服务状态"
    
    Write-Host "`n检查后端服务..."
    $backendRunning = Test-ServerRunning "http://localhost:8001/health" "后端服务 (8001)"
    
    Write-Host "`n检查前端服务..."
    $frontendRunning = Test-ServerRunning "http://localhost:5173" "前端服务 (5173)"
    
    if ($backendRunning -and $frontendRunning) {
        Write-Host "`n"
        Write-ColorText "✓ 所有服务运行正常！可以开始测试" "Green"
    }
    elseif ($backendRunning) {
        Write-Host "`n"
        Write-ColorText "⚠ 后端运行，但前端未启动" "Yellow"
        Write-ColorText "提示: cd fronted\front && npm run dev" "Cyan"
    }
    elseif ($frontendRunning) {
        Write-Host "`n"
        Write-ColorText "⚠ 前端运行，但后端未启动" "Yellow"
        Write-ColorText "提示: cd visual_model && python main.py" "Cyan"
    }
    else {
        Write-Host "`n"
        Write-ColorText "✗ 服务均未启动，请先启动服务" "Red"
        Write-ColorText "提示: 选择选项 5 和 6" "Cyan"
    }
}

function Test-BackendAPI {
    Write-Header "测试后端API"
    
    if (-not (Test-ServerRunning "http://localhost:8001/health" "后端服务")) {
        Write-ColorText "请先启动后端服务" "Red"
        return
    }
    
    Write-Host "`n运行Python测试脚本..."
    Write-Host ""
    
    if (Test-Path "visual_model\tests\run_tests.py") {
        python visual_model\tests\run_tests.py
    }
    else {
        Write-ColorText "✗ 测试脚本不存在: visual_model\tests\run_tests.py" "Red"
    }
}

function Open-FrontendTest {
    Write-Header "打开前端测试页面"
    
    if (Test-Path "test_auth_frontend.html") {
        Write-ColorText "正在打开测试页面..." "Cyan"
        Start-Process "test_auth_frontend.html"
        Write-Host ""
        Write-ColorText "✓ 测试页面已在浏览器中打开" "Green"
        Write-ColorText "提示: 确保后端服务已启动" "Yellow"
    }
    else {
        Write-ColorText "✗ 测试页面不存在: test_auth_frontend.html" "Red"
    }
}

function Switch-AuthMode {
    Write-Header "切换认证模式"
    
    if (Test-Path "切换认证模式.ps1") {
        .\切换认证模式.ps1
    }
    else {
        Write-ColorText "✗ 切换脚本不存在: 切换认证模式.ps1" "Red"
    }
}

function Start-Backend {
    Write-Header "启动后端服务"
    
    if (Test-ServerRunning "http://localhost:8001/health" "后端服务") {
        Write-ColorText "后端服务已在运行中" "Yellow"
        return
    }
    
    Write-Host ""
    Write-ColorText "正在新窗口中启动后端服务..." "Cyan"
    
    $backendPath = Join-Path $PSScriptRoot "visual_model"
    if (Test-Path $backendPath) {
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; Write-Host '启动后端服务...' -ForegroundColor Cyan; python main.py"
        Write-ColorText "✓ 后端服务正在启动，请稍候..." "Green"
        Write-ColorText "提示: 后端将运行在 http://localhost:8001" "Cyan"
        
        # 等待服务启动
        Write-Host "`n等待后端启动..."
        Start-Sleep -Seconds 3
        for ($i = 1; $i -le 10; $i++) {
            Write-Host "." -NoNewline
            Start-Sleep -Seconds 1
            if (Test-ServerRunning "http://localhost:8001/health" "后端服务" -ErrorAction SilentlyContinue) {
                Write-Host ""
                Write-ColorText "✓ 后端服务已成功启动！" "Green"
                return
            }
        }
        Write-Host ""
        Write-ColorText "⚠ 后端服务可能仍在启动中，请稍候并手动检查" "Yellow"
    }
    else {
        Write-ColorText "✗ 后端目录不存在: $backendPath" "Red"
    }
}

function Start-Frontend {
    Write-Header "启动前端服务"
    
    if (Test-ServerRunning "http://localhost:5173" "前端服务") {
        Write-ColorText "前端服务已在运行中" "Yellow"
        return
    }
    
    Write-Host ""
    Write-ColorText "正在新窗口中启动前端服务..." "Cyan"
    
    $frontendPath = Join-Path $PSScriptRoot "fronted\front"
    if (Test-Path $frontendPath) {
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; Write-Host '启动前端服务...' -ForegroundColor Cyan; npm run dev"
        Write-ColorText "✓ 前端服务正在启动，请稍候..." "Green"
        Write-ColorText "提示: 前端将运行在 http://localhost:5173" "Cyan"
    }
    else {
        Write-ColorText "✗ 前端目录不存在: $frontendPath" "Red"
    }
}

function Show-CurrentConfig {
    Write-Header "查看当前配置"
    
    Write-Host "`n【后端配置】"
    if (Test-Path "visual_model\.env") {
        $envContent = Get-Content "visual_model\.env" | Select-String "DISABLE_AUTH"
        if ($envContent) {
            Write-Host "  $envContent"
        }
        else {
            Write-ColorText "  未找到 DISABLE_AUTH 配置" "Yellow"
        }
    }
    else {
        Write-ColorText "  .env 文件不存在" "Red"
    }
    
    Write-Host "`n【前端配置】"
    if (Test-Path "fronted\front\src\router\index.js") {
        $routerContent = Get-Content "fronted\front\src\router\index.js" | Select-String "DISABLE_AUTH" | Select-Object -First 1
        if ($routerContent) {
            Write-Host "  $routerContent"
        }
    }
    
    Write-Host "`n【服务状态】"
    $backendRunning = Test-ServerRunning "http://localhost:8001/health" "后端服务"
    $frontendRunning = Test-ServerRunning "http://localhost:5173" "前端服务"
}

function Run-FullTest {
    Write-Header "完整测试流程"
    
    Write-ColorText "`n步骤 1: 检查服务状态" "Cyan"
    Check-ServiceStatus
    
    Write-Host "`n"
    Read-Host "按回车继续..."
    
    Write-ColorText "`n步骤 2: 测试后端API" "Cyan"
    Test-BackendAPI
    
    Write-Host "`n"
    Read-Host "按回车继续..."
    
    Write-ColorText "`n步骤 3: 打开前端测试页面" "Cyan"
    Open-FrontendTest
    
    Write-Host "`n"
    Write-ColorText "完整测试流程已执行完毕！" "Green"
    Write-ColorText "请在浏览器中完成前端测试" "Yellow"
}

# 主逻辑
if ($Test -ne 'all') {
    switch ($Test) {
        'backend' { Test-BackendAPI; exit }
        'frontend' { Open-FrontendTest; exit }
        'switch' { Switch-AuthMode; exit }
    }
}

# 交互式菜单
while ($true) {
    Show-Menu
    $choice = Read-Host "`n请选择操作 (1-9)"
    
    switch ($choice) {
        '1' { Check-ServiceStatus; pause }
        '2' { Test-BackendAPI; pause }
        '3' { Open-FrontendTest; pause }
        '4' { Switch-AuthMode; pause }
        '5' { Start-Backend; pause }
        '6' { Start-Frontend; pause }
        '7' { Show-CurrentConfig; pause }
        '8' { Run-FullTest; pause }
        '9' {
            Write-ColorText "`n再见！" "Cyan"
            exit
        }
        default {
            Write-ColorText "`n无效的选择，请重试" "Red"
            pause
        }
    }
}

