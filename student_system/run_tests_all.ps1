param(
    [switch]$Full = $false,
    [switch]$UnitOnly = $false,
    [switch]$ApiOnly = $false,
    [switch]$NoClean = $false
)

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptStart = Get-Date

$env:PYTHONPATH = "$root\__pypackages__;$root"
$env:SECRET_KEY = "test-secret-key-for-pytest"
$env:FLASK_ENV = "development"
$env:DATABASE_URL = "postgresql://postgres:114514@57c42474b0ea.ofalias.net:52112/student_manage_test"
$python = "C:\Python314\python.exe"

# 清理覆盖率数据
if (-not $NoClean) {
    Remove-Item -Path "$root\.coverage" -ErrorAction SilentlyContinue
    Remove-Item -Path "$root\.coverage.*" -ErrorAction SilentlyContinue
    Remove-Item -Path "$root\coverage_reports" -Recurse -ErrorAction SilentlyContinue
}

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " SIMS 全面测试体系" -ForegroundColor Cyan
Write-Host " Python: $python" -ForegroundColor Gray
Write-Host " 数据库: $env:DATABASE_URL" -ForegroundColor Gray
Write-Host "=========================================" -ForegroundColor Cyan

$global:totalPass = 0
$global:totalFail = 0

Function Run-Test {
    param([string]$Label, [string]$Files)
    Write-Host "`n>>> [$Label] $Files" -ForegroundColor Yellow
    $start = Get-Date
    $result = & $python -m pytest $Files.Split(" ") 2>&1
    $exitCode = $LASTEXITCODE
    $duration = (Get-Date) - $start
    
    $passed = 0; $failed = 0
    if ($result -match "(\d+) passed") { $passed = [int]$Matches[1] }
    if ($result -match "(\d+) failed") { $failed = [int]$Matches[1] }
    if ($result -match "(\d+) error") { $failed += [int]$Matches[1] }
    
    $global:totalPass += $passed
    $global:totalFail += $failed
    
    $statusColor = if ($failed -eq 0) { "Green" } else { "Red" }
    Write-Host "  [$Label] $passed passed, $failed failed ($($duration.TotalSeconds.ToString('F1'))s)" -ForegroundColor $statusColor
    
    # 输出 TOTAL 覆盖率行
    $result | Select-String -Pattern "^TOTAL\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)%" | ForEach-Object {
        $pct = $_.Matches.Groups[1].Value
        Write-Host "  [覆盖] $pct%" -ForegroundColor $(if ($pct -eq "100") {"Green"} else {"Cyan"})
    }
    
    if ($failed -gt 0) {
        $result | Select-String -Pattern "(FAILED|ERROR.*test_)" | Select-Object -First 5 | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
    }
    return $exitCode
}

# === 单元测试 ===
if (-not $ApiOnly) {
    Write-Host "`n┌──────────────────────────────────────┐" -ForegroundColor Cyan
    Write-Host "│  单元测试                              │" -ForegroundColor Cyan
    Write-Host "└──────────────────────────────────────┘" -ForegroundColor Cyan

    Run-Test -Label "基础模块" -Files "tests/unit/test_utils.py tests/unit/test_config.py tests/unit/test_entity_base.py tests/unit/test_main.py tests/unit/test_middleware.py tests/unit/test_middleware_advanced.py tests/unit/test_advanced_coverage.py"
    Run-Test -Label "服务层-CRUD" -Files "tests/unit/services/test_department_service.py tests/unit/services/test_major_service.py tests/unit/services/test_class_service.py tests/unit/services/test_course_service.py tests/unit/services/test_teacher_service.py"
    Run-Test -Label "服务层-业务A" -Files "tests/unit/services/test_auth_service.py tests/unit/services/test_csv_service.py tests/unit/services/test_student_service.py"
    Run-Test -Label "服务层-业务B" -Files "tests/unit/services/test_user_service.py tests/unit/services/test_dorm_service.py tests/unit/services/test_enrollment_service.py tests/unit/services/test_grade_service.py"
    Run-Test -Label "服务层-业务C" -Files "tests/unit/services/test_payment_service.py tests/unit/services/test_reward_service.py tests/unit/services/test_semester_service.py tests/unit/services/test_query_service.py tests/unit/services/test_statistics_service.py tests/unit/services/test_teaching_service.py tests/unit/services/test_curriculum_service.py"
    Run-Test -Label "仓库层" -Files "tests/unit/repositories/"
}

# === API 集成测试 ===
if (-not $UnitOnly) {
    Write-Host "`n┌──────────────────────────────────────┐" -ForegroundColor Cyan
    Write-Host "│  API 集成测试                          │" -ForegroundColor Cyan
    Write-Host "└──────────────────────────────────────┘" -ForegroundColor Cyan

    Run-Test -Label "管理API" -Files "tests/test_auth_api.py tests/test_department_api.py tests/test_class_api.py tests/test_major_api.py tests/test_course_api.py tests/test_teacher_api.py tests/test_semester_api.py"
    Run-Test -Label "业务API-A" -Files "tests/test_student_api.py tests/test_teaching_api.py tests/test_curriculum_api.py tests/test_dorm_api.py tests/test_payment_api.py tests/test_reward_api.py"
    Run-Test -Label "业务API-B" -Files "tests/test_csv_api.py tests/test_query_api.py tests/test_statistics_api.py tests/test_user_api.py tests/test_enrollment_api.py"
    Run-Test -Label "E2E+前端" -Files "tests/test_data_integrity.py tests/test_frontend_pages.py tests/test_e2e_flows.py"
}

# === 最终报告 ===
Write-Host "`n=========================================" -ForegroundColor Magenta
Write-Host " 测试完成: $global:totalPass passed, $global:totalFail failed" -ForegroundColor $(if ($global:totalFail -eq 0) {"Green"} else {"Red"})

# 输出覆盖率
$report = & $python -m coverage report -m 2>&1
$totalLine = $report | Select-String -Pattern "^TOTAL"
if ($totalLine) {
    $parts = $totalLine.ToString() -split '\s+'
    if ($parts.Count -ge 5) {
        $totalCov = $parts[$parts.Count-1] -replace '%', ''
        Write-Host " 总体覆盖率: $totalCov%" -ForegroundColor $(if ($totalCov -eq 100) {"Green"} else {"Yellow"})
    }
}

# 显示未达100%模块
$report | Select-String -Pattern "^\w+.*\d+%" | ForEach-Object {
    $line = $_.ToString().Trim()
    if ($line -match "(\d+)%$") {
        $pct = [int]$Matches[1]
        if ($pct -lt 100) {
            Write-Host "  $line" -ForegroundColor $(if ($pct -ge 80) {"Green"} elseif ($pct -ge 50) {"Yellow"} else {"Red"})
        }
    }
}

# 生成HTML
& $python -m coverage html -d coverage_reports/html 2>&1 | Out-Null
Write-Host "HTML报告: file:///$($root.Replace('\','/'))/coverage_reports/html/index.html" -ForegroundColor Cyan

$totalDuration = (Get-Date) - $scriptStart
Write-Host "总耗时: $($totalDuration.TotalMinutes.ToString('F1')) 分钟" -ForegroundColor Gray

if ($global:totalFail -gt 0) { exit 1 }
