#!/usr/bin/env bash


set -o errexit  # Exit on error
set -o pipefail # Exit on pipe failure
set -o nounset  # Exit on undefined variable

echo "🏥 Starting Hospital API Build Process..."

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install production dependencies
echo "📦 Installing production packages..."
pip install gunicorn psycopg2-binary whitenoise dj-database-url python-decouple

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --no-input

# Run database migrations
echo "🗄️  Running database migrations..."
python manage.py migrate --noinput

# Create cache table (if using database cache)
echo "💾 Creating cache table..."
python manage.py createcachetable || true

# Create superuser if it doesn't exist (for initial setup)
echo "👤 Creating default superuser (if needed)..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@hospital.com',
        password='changeme123',
        first_name='Admin',
        last_name='User',
        role='admin'
    )
    print('✅ Default superuser created: username=admin, password=changeme123')
else:
    print('ℹ️  Superuser already exists')
EOF

# Create default departments (optional)
echo "🏢 Setting up default data..."
python manage.py shell << EOF
from hospital.models import Department
departments = [
    {'name': 'Emergency', 'floor_number': 1, 'description': 'Emergency Department'},
    {'name': 'Cardiology', 'floor_number': 3, 'description': 'Heart and Cardiovascular'},
    {'name': 'Neurology', 'floor_number': 4, 'description': 'Brain and Nervous System'},
    {'name': 'Orthopedics', 'floor_number': 5, 'description': 'Bones and Joints'},
    {'name': 'Pediatrics', 'floor_number': 2, 'description': 'Children Healthcare'},
]
for dept in departments:
    Department.objects.get_or_create(
        name=dept['name'],
        defaults={
            'floor_number': dept['floor_number'],
            'description': dept['description']
        }
    )
print('✅ Default departments created')
EOF

# Compress static files (if django-compressor is installed)
if pip list | grep -q django-compressor; then
    echo "🗜️  Compressing static files..."
    python manage.py compress --force || true
fi

# Clear expired sessions
echo "🧹 Clearing expired sessions..."
python manage.py clearsessions || true

# Generate API documentation (if drf-spectacular is installed)
if pip list | grep -q drf-spectacular; then
    echo "📚 Generating API schema..."
    python manage.py spectacular --color --file schema.yml || true
fi

# Check for security issues
echo "🔒 Running security checks..."
python manage.py check --deploy --fail-level WARNING || true

echo "✅ Build completed successfully!"
echo ""
echo "🚀 Your Hospital API is ready to deploy!"
echo ""
echo "⚠️  IMPORTANT: Change the default admin password after first login!"
echo "   Username: admin"
echo "   Password: changeme123"
echo ""