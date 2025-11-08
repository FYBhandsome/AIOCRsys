# 切换认证模式脚本
# 用于快速启用/禁用认证功能

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('disable', 'enable')]
    [string]$Mode
)

$envFile = "visual_model\.env"
$routerFile = "fronted\front\src\router\index.js"

function Show-Menu {
    Write-Host "`n==================================" -ForegroundColor Cyan
    Write-Host "   认证模式切换工具" -ForegroundColor Yellow
    Write-Host "==================================" -ForegroundColor Cyan
    Write-Host "1. 禁用认证（开发测试模式）" -ForegroundColor Green
    Write-Host "2. 启用认证（生产模式）" -ForegroundColor Red
    Write-Host "3. 查看当前状态" -ForegroundColor Blue
    Write-Host "4. 身份切换功能说明 🎭" -ForegroundColor Magenta
    Write-Host "5. 退出" -ForegroundColor Gray
    Write-Host "==================================" -ForegroundColor Cyan
}

function Get-CurrentStatus {
    Write-Host "`n当前配置状态：" -ForegroundColor Yellow
    
    # 检查后端配置
    if (Test-Path $envFile) {
        $content = Get-Content $envFile -Raw
        if ($content -match "DISABLE_AUTH=True") {
            Write-Host "  后端: " -NoNewline
            Write-Host "认证已禁用 ✓" -ForegroundColor Green
        } else {
            Write-Host "  后端: " -NoNewline
            Write-Host "认证已启用 ✓" -ForegroundColor Red
        }
    } else {
        Write-Host "  后端: " -NoNewline
        Write-Host ".env 文件不存在" -ForegroundColor Yellow
    }
    
    # 检查前端配置
    if (Test-Path $routerFile) {
        $content = Get-Content $routerFile -Raw -Encoding UTF8
        $pattern = 'DISABLE_AUTH = import\.meta\.env\.DEV && true'
        if ($content -like "*$pattern*") {
            Write-Host "  前端: " -NoNewline
            Write-Host "认证已禁用 ✓" -ForegroundColor Green
        } else {
            Write-Host "  前端: " -NoNewline
            Write-Host "认证已启用 ✓" -ForegroundColor Red
        }
    }
}

function Show-RoleSwitcherInfo {
    Write-Host "`n" -NoNewline
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "     🎭 身份切换功能说明" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "当认证被禁用时，系统会在顶部导航栏显示" -ForegroundColor White
    Write-Host "身份切换器，支持快速切换不同角色：" -ForegroundColor White
    Write-Host ""
    Write-Host "  👨‍🎓 学生" -ForegroundColor Blue -NoNewline
    Write-Host "   - 查看成绩、上传证书"
    Write-Host "  👨‍🏫 教师" -ForegroundColor Green -NoNewline
    Write-Host "   - 管理班级、录入成绩"
    Write-Host "  👨‍💼 管理员" -ForegroundColor Yellow -NoNewline
    Write-Host " - 系统管理、规则配置"
    Write-Host ""
    Write-Host "✨ 特点：" -ForegroundColor Cyan
    Write-Host "  • 无需重新登录，即时切换身份"
    Write-Host "  • 自动跳转到对应角色的仪表盘"
    Write-Host "  • 仅在开发模式下显示"
    Write-Host "  • 直观的角色图标和功能说明"
    Write-Host ""
    Write-Host "📝 使用方法：" -ForegroundColor Cyan
    Write-Host "  1. 确保已禁用认证（选项1）"
    Write-Host "  2. 启动前后端服务"
    Write-Host "  3. 访问 http://localhost:5173"
    Write-Host "  4. 点击顶部的角色按钮进行切换"
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
}

function Disable-Auth {
    Write-Host "`n正在禁用认证..." -ForegroundColor Yellow
    
    # 后端配置
    if (-not (Test-Path $envFile)) {
        Copy-Item "visual_model\.env.example" $envFile
        Write-Host "  创建 .env 文件" -ForegroundColor Green
    }
    
    $content = Get-Content $envFile -Raw
    if ($content -match "DISABLE_AUTH=") {
        $content = $content -replace "DISABLE_AUTH=False", "DISABLE_AUTH=True"
        $content = $content -replace "DISABLE_AUTH=false", "DISABLE_AUTH=True"
    } else {
        $content += "`nDISABLE_AUTH=True`n"
    }
    $content | Set-Content $envFile -NoNewline
    Write-Host "  后端配置已更新 ✓" -ForegroundColor Green
    
    # 前端配置
    $content = Get-Content $routerFile -Raw -Encoding UTF8
    $oldPattern = 'DISABLE_AUTH = import.meta.env.DEV && false'
    $newPattern = 'DISABLE_AUTH = import.meta.env.DEV && true'
    $content = $content.Replace($oldPattern, $newPattern)
    [System.IO.File]::WriteAllText($routerFile, $content, [System.Text.UTF8Encoding]::new($false))
    Write-Host "  前端配置已更新 ✓" -ForegroundColor Green
    
    Write-Host "`n✓ 认证已禁用（开发测试模式）" -ForegroundColor Green
    Write-Host "⚠️  请重启前后端服务以使配置生效" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 提示：现在可以使用顶部的身份切换器快速切换角色！" -ForegroundColor Cyan
    Write-Host "   输入选项 4 查看详细说明" -ForegroundColor Cyan
}

function Enable-Auth {
    Write-Host "`n正在启用认证..." -ForegroundColor Yellow
    
    # 后端配置
    if (Test-Path $envFile) {
        $content = Get-Content $envFile -Raw
        $content = $content -replace "DISABLE_AUTH=True", "DISABLE_AUTH=False"
        $content = $content -replace "DISABLE_AUTH=true", "DISABLE_AUTH=False"
        $content | Set-Content $envFile -NoNewline
        Write-Host "  后端配置已更新 ✓" -ForegroundColor Green
    }
    
    # 前端配置
    $content = Get-Content $routerFile -Raw -Encoding UTF8
    $oldPattern = 'DISABLE_AUTH = import.meta.env.DEV && true'
    $newPattern = 'DISABLE_AUTH = import.meta.env.DEV && false'
    $content = $content.Replace($oldPattern, $newPattern)
    [System.IO.File]::WriteAllText($routerFile, $content, [System.Text.UTF8Encoding]::new($false))
    Write-Host "  前端配置已更新 ✓" -ForegroundColor Green
    
    Write-Host "`n✓ 认证已启用（生产模式）" -ForegroundColor Green
    Write-Host "⚠️  请重启前后端服务以使配置生效" -ForegroundColor Yellow
}

# 主逻辑
if ($Mode -eq 'disable') {
    Disable-Auth
    exit
}

if ($Mode -eq 'enable') {
    Enable-Auth
    exit
}

# 交互式菜单
while ($true) {
    Show-Menu
    $choice = Read-Host "`n请选择操作 (1-5)"
    
    switch ($choice) {
        '1' {
            Disable-Auth
            pause
        }
        '2' {
            Enable-Auth
            pause
        }
        '3' {
            Get-CurrentStatus
            pause
        }
        '4' {
            Show-RoleSwitcherInfo
            pause
        }
        '5' {
            Write-Host "`n再见！" -ForegroundColor Cyan
            exit
        }
        default {
            Write-Host "`n无效的选择，请重试" -ForegroundColor Red
            pause
        }
    }
}
