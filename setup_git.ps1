# Git Setup Script for CDR Analysis Pro

Write-Host "🚀 Setting up Git repository..." -ForegroundColor Cyan

# Initialize git repository
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: CDR Analysis Pro with tower location and bill analysis"

# Rename branch to main
git branch -M main

# Add remote
git remote add origin https://github.com/Sneha-Suresh-git/CDR-sneha.git

# Push to GitHub
Write-Host "📤 Pushing to GitHub..." -ForegroundColor Green
git push -u origin main

Write-Host "✅ Done! Your repository is now on GitHub!" -ForegroundColor Green
Write-Host "🌐 Visit: https://github.com/Sneha-Suresh-git/CDR-sneha" -ForegroundColor Cyan
