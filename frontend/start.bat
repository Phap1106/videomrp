@echo off
echo Starting AI Video Tool Frontend...

REM Fix Next.js config
if exist "next.config.ts" (
    echo Removing next.config.ts...
    del next.config.ts
)

if not exist "next.config.js" (
    echo Creating next.config.js...
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
)

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)

REM Start dev server
echo Starting development server...
echo.
echo Frontend will run at: http://localhost:3000
echo Backend API should be at: http://localhost:5000
echo.
npm run dev