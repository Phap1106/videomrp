video-reup-ai-tool/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── ai_prompts.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints.py
│   │   │   └── middleware.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── video_downloader.py
│   │   │   ├── content_analyzer.py
│   │   │   ├── scene_detector.py
│   │   │   ├── video_editor.py
│   │   │   ├── platform_detector.py
│   │   │   ├── copyright_checker.py
│   │   │   ├── text_detector.py
│   │   │   └── watermark_remover.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py
│   │   │   ├── logger.py
│   │   │   └── paths.py
│   │   ├── workers/
│   │   │   ├── __init__.py
│   │   │   ├── video_worker.py
│   │   │   └── celery_config.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── ffmpeg_ops.py
│   │       ├── file_utils.py
│   │       └── video_utils.py
│   ├── migrations/
│   │   └── versions/
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── gunicorn_conf.py
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── globals.css
│   │   ├── components/
│   │   │   ├── VideoUploader.tsx
│   │   │   ├── VideoPlayer.tsx
│   │   │   ├── JobList.tsx
│   │   │   ├── PlatformSelector.tsx
│   │   │   ├── VideoTypeSelector.tsx
│   │   │   ├── EditingOptions.tsx
│   │   │   ├── AnalysisResults.tsx
│   │   │   └── LoadingSpinner.tsx
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   ├── constants.ts
│   │   │   └── utils.ts
│   │   ├── hooks/
│   │   │   ├── useVideoJobs.ts
│   │   │   └── useWebSocket.ts
│   │   └── types/
│   │       └── index.ts
│   ├── public/
│   ├── Dockerfile
│   ├── next.config.js
│   ├── package.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── tsconfig.json
│   └── .env.example
├── nginx/
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── README.md
├── INSTALLATION.md
└── setup.sh