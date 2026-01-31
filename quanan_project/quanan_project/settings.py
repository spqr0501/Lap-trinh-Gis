"""
==========================================================
SETTINGS.PY - Cấu hình Django project
==========================================================

Các cấu hình quan trọng:
- DATABASE: Kết nối PostgreSQL/PostGIS
- INSTALLED_APPS: Các app được cài đặt
- MIDDLEWARE: Các middleware xử lý request/response
"""

from pathlib import Path

# Đường dẫn gốc của project
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# CẤU HÌNH BẢO MẬT
# ============================================================

# Secret key cho mã hóa session, CSRF... (KHÔNG dùng key này trong production!)
SECRET_KEY = 'dev-secret-key-123'

# Debug mode - BẬT khi phát triển, TẮT khi deploy
DEBUG = True

# Các host được phép truy cập
ALLOWED_HOSTS = ['*']

# ============================================================
# CÁC ỨNG DỤNG (APPS)
# ============================================================

INSTALLED_APPS = [
    # Apps mặc định của Django
    'django.contrib.admin',         # Trang admin
    'django.contrib.auth',          # Xác thực user
    'django.contrib.contenttypes',  # Content types
    'django.contrib.sessions',      # Session
    'django.contrib.messages',      # Messages
    'django.contrib.staticfiles',   # Static files
    
    # Apps bên thứ 3
    'corsheaders',  # Cho phép Cross-Origin requests (CORS)
    
    # App của project
    'quanan',       # App quản lý quán ăn
]

# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # CORS - phải đặt đầu tiên
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

# Cho phép tất cả domain gọi API (chỉ dùng trong development)
CORS_ALLOW_ALL_ORIGINS = True

# File routing chính
ROOT_URLCONF = 'quanan_project.urls'

# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],          # Thêm đường dẫn templates tùy chỉnh
    'APP_DIRS': True,    # Tìm templates trong app/templates/
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

# ============================================================
# CẤU HÌNH DATABASE (PostgreSQL + PostGIS)
# ============================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  # Driver PostgreSQL
        'NAME': 'quan_an',       # Tên database
        'USER': 'postgres',      # Username
        'PASSWORD': '123456',    # Password
        'HOST': 'localhost',     # Host (local)
        'PORT': '5432',          # Port mặc định PostgreSQL
    }
}

# ============================================================
# CẤU HÌNH NGÔN NGỮ VÀ TIMEZONE
# ============================================================

LANGUAGE_CODE = 'vi'              # Ngôn ngữ: Tiếng Việt
TIME_ZONE = 'Asia/Ho_Chi_Minh'    # Múi giờ Việt Nam
USE_I18N = True                   # Bật internationalization
USE_TZ = True                     # Sử dụng timezone

# ============================================================
# CẤU HÌNH STATIC FILES
# ============================================================

STATIC_URL = 'static/'           # URL cho static files

# Auto field mặc định cho primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
