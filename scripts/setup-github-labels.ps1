# GitHub Issues ラベル・マイルストーンを手動セットアップするスクリプト
# 用法: .\scripts\setup-github-labels.ps1
# 前提: gh CLI がインストール済みで、個人アカウントで認証済み

$ErrorActionPreference = "Stop"

$labels = @(
    @{ name = "balance";   color = "d4c5f9"; description = "数値バランス調整" },
    @{ name = "rules";     color = "0075ca"; description = "ルール文書の追加・修正" },
    @{ name = "simulator"; color = "0e8a16"; description = "シムコード追加・改修" },
    @{ name = "visual";    color = "fbca04"; description = "グラフ・可視化改善" },
    @{ name = "playtest";  color = "5319e7"; description = "テストプレイ後フィードバック" },
    @{ name = "bug";       color = "d73a4a"; description = "シムのバグ・計算ミス" }
)

Write-Host "Creating labels..."
foreach ($l in $labels) {
    gh label create $l.name --color $l.color --description $l.description --force
    Write-Host "  label: $($l.name)"
}

Write-Host "Creating milestone..."
gh api repos/:owner/:repo/milestones -f title="第1回テストプレイ" -f description="初回テストプレイに向けた準備" -f state="open" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  (milestone may already exist — check GitHub UI)"
} else {
    Write-Host "  milestone: 第1回テストプレイ"
}

Write-Host "Done."
