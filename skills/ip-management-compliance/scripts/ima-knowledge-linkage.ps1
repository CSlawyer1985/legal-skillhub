# IMA知识库联动 - PowerShell脚本
# 功能：从IMA知识库检索资料辅助专利评估分析
#
# 使用方式：
#   .\ima-knowledge-linkage.ps1 -Action ListKB
#   .\ima-knowledge-linkage.ps1 -Action Search -Query "淫羊藿 提取" -KBId "kb_xxx"
#   .\ima-knowledge-linkage.ps1 -Action SearchAll -Query "酶解 发酵"

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("ListKB", "Search", "SearchAll", "Help")]
    [string]$Action,

    [Parameter(Mandatory=$false)]
    [string]$Query,

    [Parameter(Mandatory=$false)]
    [string]$KBId,

    [Parameter(Mandatory=$false)]
    [string]$OutputFile
)

# ============================================================================
# 配置
# ============================================================================

$ErrorActionPreference = "Stop"
$IMA_BASE_URL = "https://ima.qq.com"

# ============================================================================
# 凭证加载
# ============================================================================

function Load-IMACredentials {
    $clientId = $env:IMA_OPENAPI_CLIENTID
    $apiKey = $env:IMA_OPENAPI_APIKEY

    if (-not $clientId -or -not $apiKey) {
        $configDir = "$HOME/.config/ima"
        if (Test-Path "$configDir/client_id") {
            $clientId = Get-Content "$configDir/client_id" -Raw -Encoding UTF8 | ForEach-Object { $_.Trim() }
        }
        if (Test-Path "$configDir/api_key") {
            $apiKey = Get-Content "$configDir/api_key" -Raw -Encoding UTF8 | ForEach-Object { $_.Trim() }
        }
    }

    return @{
        ClientId = $clientId
        ApiKey = $apiKey
    }
}

# ============================================================================
# API调用
# ============================================================================

function Invoke-IMAApi {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path,

        [Parameter(Mandatory=$true)]
        [hashtable]$Body
    )

    $creds = Load-IMACredentials

    if (-not $creds.ClientId -or -not $creds.ApiKey) {
        throw "IMA凭证未配置。请先配置 Client ID 和 API Key"
    }

    $url = "$IMA_BASE_URL/$Path"
    $headers = @{
        "ima-openapi-clientid" = $creds.ClientId
        "ima-openapi-apikey" = $creds.ApiKey
    }

    $jsonBody = $Body | ConvertTo-Json -Depth 10 -Compress

    # PowerShell 5.1 处理
    $psVersion = $PSVersionTable.PSVersion.Major
    if ($psVersion -le 5) {
        Write-Verbose "检测到 PowerShell $psVersion，使用 UTF-8 字节数组模式"
        $utf8Bytes = [System.Text.Encoding]::UTF8.GetBytes($jsonBody)
        try {
            $response = Invoke-RestMethod -Uri $url -Method Post -Body $utf8Bytes `
                -ContentType "application/json; charset=utf-8" -Headers $headers -TimeoutSec 30
        } catch {
            throw "API调用失败: $_"
        }
    } else {
        try {
            $response = Invoke-RestMethod -Uri $url -Method Post -Body $jsonBody `
                -ContentType "application/json; charset=utf-8" -Headers $headers -TimeoutSec 30
        } catch {
            throw "API调用失败: $_"
        }
    }

    if ($response.retcode -ne 0) {
        throw "API返回错误: $($response.errmsg)"
    }

    return $response.data
}

# ============================================================================
# 功能函数
# ============================================================================

function Get-IMAKnowledgeBases {
    $data = Invoke-IMAApi -Path "openapi/wiki/v1/search_knowledge_base" -Body @{
        query = ""
        cursor = ""
        limit = 50
    }

    return $data.list
}

function Search-IMAKnowledge {
    param(
        [Parameter(Mandatory=$true)]
        [string]$KBId,

        [Parameter(Mandatory=$true)]
        [string]$Query
    )

    $data = Invoke-IMAApi -Path "openapi/wiki/v1/search_knowledge" -Body @{
        query = $Query
        knowledge_base_id = $KBId
        cursor = ""
    }

    return @{
        List = $data.list
        NextCursor = $data.next_cursor
        IsEnd = $data.is_end
    }
}

# ============================================================================
# 格式化输出
# ============================================================================

function Format-KnowledgeBaseList {
    param([Parameter(Mandatory=$true)] $List)

    $output = @"

📚 可用的知识库：

"@

    for ($i = 0; $i -lt $List.Count; $i++) {
        $kb = $List[$i]
        $num = $i + 1
        $output += "$num. **$($kb.name)** — $($kb.description)"
        $output += "`n   ID: $($kb.id)`n"
    }

    $output += @"

请选择要检索的知识库（输入编号）:
"@

    return $output
}

function Format-SearchResults {
    param(
        [Parameter(Mandatory=$true)] $Results,
        [Parameter(Mandatory=$true)] [string]$Query
    )

    $items = $Results.List

    if ($items.Count -eq 0) {
        return "🔍 搜索「$Query」的结果：`n`n未找到相关内容"
    }

    $output = "🔍 搜索「$Query」的结果：`n`n"

    for ($i = 0; $i -lt $items.Count; $i++) {
        $item = $items[$i]
        $num = $i + 1

        # 清理高亮标签
        $highlight = $item.highlight_content -replace '<em>', '**' -replace '</em>', '**'

        $output += "$num. 📄 **$($item.title)**"
        if ($item.parent_folder_id) {
            $output += "`n   文件夹: $($item.parent_folder_id)"
        }
        if ($highlight) {
            $output += "`n   > $highlight"
        }
        $output += "`n`n"
    }

    $output += "---`n共找到 $($items.Count) 条相关结果`n"

    return $output
}

# ============================================================================
# 主逻辑
# ============================================================================

function Main {
    # 凭证检查
    $creds = Load-IMACredentials
    if (-not $creds.ClientId -or -not $creds.ApiKey) {
        Write-Host "❌ IMA凭证未配置" -ForegroundColor Red
        Write-Host ""
        Write-Host "请先配置 IMA OpenAPI 凭证："
        Write-Host "1. 打开 https://ima.qq.com/agent-interface 获取 Client ID 和 API Key"
        Write-Host "2. 创建配置文件:"
        Write-Host "   mkdir -p ~/.config/ima"
        Write-Host "   echo 'your_client_id' > ~/.config/ima/client_id"
        Write-Host "   echo 'your_api_key' > ~/.config/ima/api_key"
        return
    }

    switch ($Action) {
        "Help" {
            Write-Host @"

IMA知识库联动脚本 - 帮助

用法:
  .\ima-knowledge-linkage.ps1 -Action <操作> [参数]

操作:
  ListKB        列出所有知识库
  Search        在指定知识库中搜索
  SearchAll     在所有知识库中搜索
  Help          显示帮助

参数:
  -Query        搜索关键词（用于 Search/SearchAll）
  -KBId         知识库ID（用于 Search）
  -OutputFile   输出文件路径（可选）

示例:
  # 列出所有知识库
  .\ima-knowledge-linkage.ps1 -Action ListKB

  # 在指定知识库中搜索
  .\ima-knowledge-linkage.ps1 -Action Search -KBId "kb_xxx" -Query "淫羊藿 提取"

  # 在所有知识库中搜索
  .\ima-knowledge-linkage.ps1 -Action SearchAll -Query "酶解 发酵"

"@
        }

        "ListKB" {
            Write-Host "正在获取知识库列表..." -ForegroundColor Cyan
            $kbList = Get-IMAKnowledgeBases
            $output = Format-KnowledgeBaseList -List $kbList
            Write-Host $output

            # 如果指定了输出文件
            if ($OutputFile) {
                $output | Out-File -FilePath $OutputFile -Encoding UTF8
                Write-Host "`n结果已保存到: $OutputFile" -ForegroundColor Green
            }
        }

        "Search" {
            if (-not $Query) {
                Write-Host "❌ Search 操作需要 -Query 参数" -ForegroundColor Red
                return
            }
            if (-not $KBId) {
                Write-Host "❌ Search 操作需要 -KBId 参数" -ForegroundColor Red
                return
            }

            Write-Host "正在搜索..." -ForegroundColor Cyan
            $results = Search-IMAKnowledge -KBId $KBId -Query $Query
            $output = Format-SearchResults -Results $results -Query $Query
            Write-Host $output

            if ($OutputFile) {
                $output | Out-File -FilePath $OutputFile -Encoding UTF8
                Write-Host "`n结果已保存到: $OutputFile" -ForegroundColor Green
            }
        }

        "SearchAll" {
            if (-not $Query) {
                Write-Host "❌ SearchAll 操作需要 -Query 参数" -ForegroundColor Red
                return
            }

            Write-Host "正在获取知识库列表..." -ForegroundColor Cyan
            $kbList = Get-IMAKnowledgeBases

            $allResults = @()

            foreach ($kb in $kbList) {
                Write-Host "正在搜索知识库: $($kb.name)..." -ForegroundColor DarkCyan
                $results = Search-IMAKnowledge -KBId $kb.id -Query $Query
                foreach ($item in $results.List) {
                    $item | Add-Member -NotePropertyName "KnowledgeBaseName" -NotePropertyValue $kb.name -Force
                    $item | Add-Member -NotePropertyName "KnowledgeBaseId" -NotePropertyValue $kb.id -Force
                    $allResults += $item
                }
            }

            Write-Host ""
            if ($allResults.Count -eq 0) {
                Write-Host "未找到相关内容"
            } else {
                Write-Host "🔍 在 $($kbList.Count) 个知识库中搜索「$Query」的结果：`n" -ForegroundColor Yellow
                for ($i = 0; $i -lt $allResults.Count; $i++) {
                    $item = $allResults[$i]
                    $num = $i + 1
                    $highlight = $item.highlight_content -replace '<em>', '**' -replace '</em>', '**'

                    Write-Host "$num. 📄 **$($item.title)** (来自: $($item.KnowledgeBaseName))"
                    if ($highlight) {
                        Write-Host "   > $highlight"
                    }
                    Write-Host ""
                }
                Write-Host "---"
                Write-Host "共找到 $($allResults.Count) 条相关结果" -ForegroundColor Green
            }

            if ($OutputFile) {
                $allResults | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputFile -Encoding UTF8
                Write-Host "`n结果已保存到: $OutputFile" -ForegroundColor Green
            }
        }
    }
}

# 运行主逻辑
Main
