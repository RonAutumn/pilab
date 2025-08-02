# PiLab Storage System

A comprehensive storage and monitoring system for PiLab camera captures with Supabase integration, real-time dashboards, and automated retention policies.

## 🚀 Quick Start Guide

### Prerequisites

- Docker and Docker Compose
- Python 3.8+
- Git

### 1. Local Supabase Environment Setup

The PiLab Storage System uses a local Supabase environment for development and testing.

```bash
# Clone the repository
git clone <repository-url>
cd pilab

# Start the local Supabase environment
docker-compose -f infra/supabase/docker-compose.yml up -d

# Wait for services to start (about 30 seconds)
docker-compose -f infra/supabase/docker-compose.yml logs -f
```

### 2. Database Schema Setup

```bash
# Apply the database migrations
docker exec -i pilab-postgres psql -U postgres -d pilab_dev < supabase/migrations/20240801_create_storage_audit_log.sql
docker exec -i pilab-postgres psql -U postgres -d pilab_dev < supabase/migrations/20240801_verify_rls_policies.sql
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```bash
# Supabase Configuration
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Storage Configuration
STORAGE_BUCKET=pilab-dev
MAX_FILE_SIZE=26214400  # 25MB in bytes

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_DIR=logs

# Retry Configuration
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_DELAY=1.0
RETRY_MAX_DELAY=60.0
RETRY_JITTER=0.1

# Chunked Processing
CHUNK_SIZE=100
MAX_CHUNKS=1000
CHUNK_DELAY=0.1
FAIL_FAST_THRESHOLD=0.1

# Dashboard Configuration
FLASK_PORT=5000
FLASK_DEBUG=False
FLASK_SECRET_KEY=your_secret_key_here
```

### 4. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install additional dashboard dependencies
pip install flask flask-socketio python-socketio
```

### 5. Test the System

```bash
# Run the integration tests
python tests/test_storage_integration.py

# Test the dashboard
python dashboard/start_dashboard.py --help
```

## 📁 Project Structure

```
pilab/
├── src/                          # Core source code
│   ├── supabase_client.py       # Supabase integration
│   ├── storage_service.py       # Storage operations
│   └── ...
├── dashboard/                    # Dashboard components
│   ├── app.py                   # Flask-SocketIO web dashboard
│   ├── cli_dashboard.py         # Command-line dashboard
│   ├── utils/                   # Dashboard utilities
│   │   ├── logging_utils.py     # Structured logging
│   │   ├── retry.py            # Retry logic
│   │   └── chunked_processing.py # Bulk operations
│   └── templates/               # Web dashboard templates
├── scripts/                     # Monitoring and maintenance scripts
│   ├── storage_monitor.py       # Storage monitoring
│   ├── retention_enforcer.py    # Retention policy enforcement
│   └── audit_logger.py          # Audit logging
├── supabase/                    # Database migrations
│   └── migrations/
├── tests/                       # Test suite
│   └── test_storage_integration.py
└── logs/                        # Application logs
```

## 🔧 Core Features

### 1. Storage Management

- **Automatic Uploads**: Integrate with PiLab capture pipeline using `--supabase` flag
- **File Deduplication**: SHA-256 hashing prevents duplicate uploads
- **Metadata Tracking**: Comprehensive capture metrics and EXIF data
- **Retention Policies**: Automated cleanup of old files with audit trails

### 2. Real-Time Monitoring

- **Web Dashboard**: Flask-SocketIO powered dashboard with live updates
- **CLI Dashboard**: Terminal-based monitoring with configurable intervals
- **Health Checks**: `/api/health` and `/api/metrics` endpoints
- **Alert System**: Automatic notifications for failures and capacity issues

### 3. Error Handling & Reliability

- **Retry Logic**: Exponential backoff with jitter for transient failures
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Chunked Processing**: Bulk operations to prevent memory issues
- **Graceful Degradation**: Fallback mechanisms for service failures

### 4. Security & Compliance

- **Row-Level Security (RLS)**: Database-level access control
- **Audit Logging**: Complete audit trail for all operations
- **Service Role Isolation**: Proper key management and access patterns
- **Input Validation**: Comprehensive validation for all inputs

## 🎯 Usage Examples

### Basic Upload

```python
from src.supabase_client import create_pilab_client

# Initialize client
client = create_pilab_client()

# Upload an image
result = client.upload_and_log(
    file_path="captures/image_001.jpg",
    shot_type="timelapse",
    metadata={
        "brightness": 0.75,
        "sharpness": 0.82,
        "contrast": 0.68
    }
)

print(f"Upload successful: {result['filename']}")
```

### Storage Monitoring

```python
from scripts.storage_monitor import StorageMonitor
from src.supabase_client import create_pilab_client

# Initialize monitor
client = create_pilab_client()
monitor = StorageMonitor(client)

# Check storage usage
usage = monitor.monitor_storage_usage('pilab-dev')
print(f"Total files: {usage['total_files']}")
print(f"Total size: {usage['total_size_mb']} MB")

# Enforce retention policy (30 days)
result = monitor.enforce_retention_policy('pilab-dev', 30, dry_run=True)
print(f"Files to delete: {result['files_soft_deleted']}")
```

### Dashboard Usage

```bash
# Start web dashboard
python dashboard/start_dashboard.py web

# Start CLI dashboard
python dashboard/start_dashboard.py cli --interval 30

# Access web dashboard
# Open http://localhost:5000 in your browser
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python tests/test_storage_integration.py

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Test Categories

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: End-to-end workflow testing
3. **Performance Tests**: Load and stress testing
4. **Security Tests**: RLS and access control testing

### Test Data

The test suite includes:
- Mock Supabase responses
- Sample image files
- Database fixtures
- Performance benchmarks

## 🔍 Monitoring & Troubleshooting

### Log Files

- `logs/pilab.dashboard.log` - Dashboard application logs
- `logs/pilab.storage_monitor.log` - Storage monitoring logs
- `logs/pilab.test.integration.log` - Integration test logs

### Common Issues

#### Connection Errors

```bash
# Check Supabase services
docker-compose -f infra/supabase/docker-compose.yml ps

# Check logs
docker-compose -f infra/supabase/docker-compose.yml logs supabase
```

#### Permission Errors

```bash
# Verify RLS policies
docker exec pilab-postgres psql -U postgres -d pilab_dev -c "\dp+ captures"

# Check service role permissions
docker exec pilab-postgres psql -U postgres -d pilab_dev -c "SELECT * FROM pg_policies WHERE tablename = 'captures';"
```

#### Performance Issues

```bash
# Monitor chunked processing
export CHUNK_SIZE=50
export CHUNK_DELAY=0.2

# Check system resources
docker stats pilab-postgres
```

### Health Checks

```bash
# Check system health
curl http://localhost:5000/api/health

# Get metrics
curl http://localhost:5000/api/metrics

# Check storage usage
curl http://localhost:5000/api/storage/usage
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SUPABASE_URL` | `http://localhost:54321` | Supabase instance URL |
| `SUPABASE_ANON_KEY` | - | Anonymous API key |
| `SUPABASE_SERVICE_ROLE_KEY` | - | Service role API key |
| `STORAGE_BUCKET` | `pilab-dev` | Storage bucket name |
| `LOG_LEVEL` | `INFO` | Logging level |
| `RETRY_MAX_ATTEMPTS` | `3` | Maximum retry attempts |
| `CHUNK_SIZE` | `100` | Chunk size for bulk operations |

### Dashboard Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_PORT` | `5000` | Web dashboard port |
| `FLASK_DEBUG` | `False` | Debug mode |
| `FLASK_SECRET_KEY` | - | Flask secret key |

## 📊 Metrics & Monitoring

### Available Metrics

- `pilab_storage_files_total` - Total number of files
- `pilab_storage_size_bytes` - Total storage size
- `pilab_uploads_total` - Total upload attempts
- `pilab_uploads_success_total` - Successful uploads
- `pilab_uploads_failed_total` - Failed uploads
- `pilab_captures_total` - Total captures

### Dashboard Features

- **Real-time Updates**: Live data via WebSocket connections
- **Interactive Charts**: Storage usage and upload metrics
- **Alert System**: Automatic notifications for issues
- **Export Functionality**: CSV and JSON data export
- **Responsive Design**: Works on desktop and mobile

## 🔒 Security Considerations

### Row-Level Security (RLS)

All tables have RLS enabled with appropriate policies:

- **Anonymous Access**: Read-only access to public data
- **Service Role**: Full access for backend operations
- **Audit Logging**: All access attempts are logged

### Key Management

- Never expose service role keys to clients
- Use environment variables for sensitive data
- Rotate keys regularly
- Monitor key usage

### Data Protection

- All sensitive data is encrypted at rest
- Network communication uses HTTPS
- Input validation prevents injection attacks
- Audit trails track all data access

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

### Code Standards

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Include docstrings for all classes and methods
- Write comprehensive tests
- Update documentation for API changes

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:

1. Check the troubleshooting section above
2. Review the logs for error details
3. Run the integration tests
4. Create an issue with detailed information

## 🔄 Changelog

### v1.0.0 (2024-08-01)
- Initial release of PiLab Storage System
- Complete Supabase integration
- Real-time dashboard implementation
- Comprehensive error handling and retry logic
- RLS compliance and security features
- Automated retention policies
- Integration test suite
