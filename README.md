# 🤖 Reprompt - AI Prompt Optimization Platform

A **production-ready FastAPI application** that provides AI-powered prompt optimization with **dual inference modes** and **complete authentication system**. Built with modern best practices including rate limiting, comprehensive error handling, and robust input validation.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   OpenAI API    │
│   (HTML/JS)     │◄──►│   Backend       │◄──►│   (GPT-4o/4)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Redis Cache   │    │   Supabase      │
                       │   (Optional)    │    │   (Auth/DB)     │
                       └─────────────────┘    └─────────────────┘
                              │                       │
                              │                       │
                              ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Cache Layer   │    │   User Auth     │
                       │   (Prompt      │    │   & Database    │
                       │    Results)     │    │   Management    │
                       └─────────────────┘    └─────────────────┘
```

## 🎯 Core Features

### **1. Dual AI Inference Modes**

#### 🚀 **Lazy Mode (Fast & Efficient)**
- **Model**: `gpt-4o-mini`
- **Max Tokens**: 250
- **Temperature**: 0.3
- **Use Case**: Quick, cost-effective prompt optimization
- **Features**: Basic clarity improvements, fast responses

#### ⚡ **Pro Mode (High Quality & Detailed)**
- **Model**: `gpt-4`
- **Max Tokens**: 2500
- **Temperature**: 0.7
- **Use Case**: Sophisticated prompt engineering
- **Features**: Advanced techniques, detailed optimization

### **2. Complete Authentication System**
- **User Registration & Login** with email/password
- **JWT Token Management** (access + refresh tokens)
- **Protected Endpoints** with role-based access
- **Supabase Integration** for user management
- **Session Management** and logout functionality

### **3. Production-Ready Infrastructure**
- **Rate Limiting** (60 requests/minute)
- **Comprehensive Error Handling**
- **Input Validation & Sanitization**
- **Structured Logging** with Loguru
- **Health Checks** and monitoring
- **CORS Configuration**

## 📁 Project Structure

```
reprompt/
├── main.py                    # FastAPI application entry point
├── config.py                  # Configuration with mode-based settings
├── requirements.txt           # Python dependencies
├── .env                      # Environment variables (create this)
├── static/
│   └── index.html           # Frontend interface
├── models/
│   ├── lazy_inference.py    # Lazy mode optimization
│   ├── pro_inference.py     # Pro mode optimization
│   └── load_model.py        # Model loading utilities
├── services/
│   ├── openai_service.py    # Production OpenAI service
│   ├── auth_service.py      # Supabase authentication
│   └── redis.py             # Redis caching service
├── routes/
│   ├── inference_router.py  # AI inference endpoints
│   └── auth_router.py       # Authentication endpoints
├── schemas/
│   ├── inference_schema.py  # Request/response models
│   └── auth_schema.py       # Authentication models
├── utils/
│   └── helpers.py           # Production utility functions
└── testing/                  # Test files and utilities
```

## 🚀 Getting Started

### **Prerequisites**
- Python 3.8+
- Redis (optional, for caching)
- OpenAI API key
- Supabase account and project

### **Installation**

1. **Clone the repository**
```bash
git clone <repository-url>
cd reprompt
```

2. **Create virtual environment**
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix/MacOS:
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
# Create .env file
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# Optional Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
```

5. **Start Redis (optional)**
```bash
# Using Docker
docker run -d -p 6379:6379 redis:alpine

# Or install Redis locally
```

6. **Run the application**
```bash
python main.py
# Or
uvicorn main:app --reload --port 8001
```

7. **Access the application**
- Frontend: http://localhost:8001/frontend
- API Docs: http://localhost:8001/docs
- Health Check: http://localhost:8001/health

## 🔐 Authentication API

### **User Registration**
```bash
curl -X POST "http://localhost:8001/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

### **User Login**
```bash
curl -X POST "http://localhost:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

### **Get User Profile (Protected)**
```bash
curl -X GET "http://localhost:8001/api/v1/auth/profile" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### **Refresh Token**
```bash
curl -X POST "http://localhost:8001/api/v1/auth/refresh" \
  -H "Authorization: Bearer YOUR_REFRESH_TOKEN"
```

### **Logout**
```bash
curl -X POST "http://localhost:8001/api/v1/auth/logout" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🤖 AI Inference API

### **Optimize Prompt**
```bash
curl -X POST "http://localhost:8001/api/v1/inference/optimize-prompt" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a story about a cat",
    "inference_type": "pro"
  }'
```

### **Response Format**
```json
{
  "output": "Create a compelling narrative about a feline protagonist...",
  "tokens_used": 0,
  "inference_type": "pro",
  "model_used": "gpt-4"
}
```

### **Available Endpoints**
- `POST /api/v1/inference/optimize-prompt` - Main optimization endpoint
- `GET /api/v1/inference/models` - Available models and techniques
- `GET /api/v1/inference/health` - Inference service health

## ⚙️ Configuration

### **Mode-Based Configuration**
```python
# config.py
class Settings(BaseSettings):
    # Lazy Mode (Fast & Efficient)
    LAZY_MODEL = "gpt-4o-mini"
    LAZY_MAX_TOKENS = 250
    LAZY_TEMPERATURE = 0.3
    
    # Pro Mode (High Quality & Detailed)
    PRO_MODEL = "gpt-4"
    PRO_MAX_TOKENS = 2500
    PRO_TEMPERATURE = 0.7
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    
    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    
    # Redis Configuration (Optional)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
```

## 🔧 Development & Testing

### **Running Tests**
```bash
# Test OpenAI service
python testing/test_openai_service.py

# Test authentication
python testing/test_auth_service_direct.py

# Test HTTP endpoints
python testing/test_http_endpoints.py
```

### **Code Quality Features**
- **Type Hints** throughout the codebase
- **Comprehensive Error Handling** with custom exceptions
- **Input Validation** and sanitization
- **Structured Logging** with Loguru
- **Rate Limiting** for API protection
- **Health Checks** for monitoring

## 🚀 Production Deployment

### **Environment Variables**
```bash
# Required
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=eyJ...

# Optional
REDIS_HOST=redis.example.com
REDIS_PORT=6379
REDIS_PASSWORD=secure_password
```

### **Production Server**
```bash
# Using Gunicorn + Uvicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001

# Or using Uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4
```

### **Docker Deployment**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

## 🔒 Security Features

- **JWT Token Authentication** with refresh mechanism
- **Password Hashing** via Supabase
- **Input Sanitization** and validation
- **Rate Limiting** to prevent abuse
- **CORS Configuration** for frontend security
- **Environment Variable** management

## 📊 Monitoring & Health

### **Health Endpoints**
- `GET /health` - Application health
- `GET /api/v1/inference/health` - Inference service health
- `GET /api/v1/auth/health` - Authentication service health

### **Logging**
- **Structured Logging** with Loguru
- **Request/Response Logging** for debugging
- **Error Tracking** with detailed context
- **Performance Monitoring** for API calls

## 🧪 Testing Strategy

### **Test Coverage**
- **Unit Tests** for individual services
- **Integration Tests** for API endpoints
- **Authentication Tests** for security
- **Performance Tests** for rate limiting

### **Test Files**
- `test_openai_service.py` - OpenAI service testing
- `test_auth_service_direct.py` - Authentication testing
- `test_http_endpoints.py` - API endpoint testing
- `test_curl.py` - cURL-based testing

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### **Development Guidelines**
- Follow **PEP 8** style guidelines
- Add **type hints** to all functions
- Include **docstrings** for all public methods
- Write **tests** for new functionality
- Update **README.md** for new features

## 📈 Roadmap

### **Phase 1 (Current)**
- ✅ Dual inference modes (Lazy/Pro)
- ✅ Complete authentication system
- ✅ Production-ready infrastructure
- ✅ Comprehensive error handling

### **Phase 2 (Planned)**
- 🔄 Redis caching integration
- 🔄 User prompt history
- 🔄 Advanced analytics dashboard
- 🔄 Multi-language support

### **Phase 3 (Future)**
- 📋 Custom model fine-tuning
- 📋 Batch processing capabilities
- 📋 API rate limit management
- 📋 Advanced caching strategies

## 🆘 Support & Troubleshooting

### **Common Issues**

#### **OpenAI API Errors**
```bash
# Check API key configuration
echo $OPENAI_API_KEY

# Verify API key format (should start with 'sk-')
```

#### **Supabase Connection Issues**
```bash
# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY

# Verify Supabase project is active
```

#### **Redis Connection Issues**
```bash
# Check Redis service
redis-cli ping

# Verify Redis configuration
redis-cli -h localhost -p 6379 ping
```

### **Getting Help**
- **Create an issue** in the repository
- **Check API documentation** at `/docs`
- **Review logs** for detailed error messages
- **Test individual services** using test files

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** for the excellent web framework
- **OpenAI** for powerful AI models
- **Supabase** for authentication and database
- **Loguru** for structured logging
- **Pydantic** for data validation

---

**Built with ❤️ using modern Python best practices**

**Version**: 2.0.0  
**Last Updated**: September 2024  
**Status**: Production Ready 🚀
