@echo off
echo Fixing Next.js configuration...

REM 1. Xóa file config cũ
if exist "next.config.ts" del next.config.ts

REM 2. Tạo next.config.js mới
echo /** @type {import('next').NextConfig} */ > next.config.js
echo const nextConfig = { >> next.config.js
echo   reactStrictMode: true, >> next.config.js
echo   swcMinify: true, >> next.config.js
echo   images: { >> next.config.js
echo     domains: ['localhost'], >> next.config.js
echo   }, >> next.config.js
echo   async rewrites() { >> next.config.js
echo     return [ >> next.config.js
echo       { >> next.config.js
echo         source: '/api/:path*', >> next.config.js
echo         destination: 'http://localhost:5000/api/:path*', >> next.config.js
echo       }, >> next.config.js
echo     ]; >> next.config.js
echo   }, >> next.config.js
echo }; >> next.config.js
echo. >> next.config.js
echo module.exports = nextConfig; >> next.config.js

REM 3. Cập nhật package.json để đảm bảo script đúng
if exist "package.json" (
    echo Updating package.json...
    powershell -Command "(Get-Content package.json) -replace '\"next\": \".*?\"', '\"next\": \"^14.0.0\"' | Set-Content package.json"
)

REM 4. Cài đặt dependencies
echo Installing/updating dependencies...
call npm install

echo.
echo ====================================
echo Fix completed!
echo.
echo Run: npm run dev
echo ====================================
pause