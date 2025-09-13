# 🤖 Reprompt - AI Prompt Optimizer

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)](https://openai.com)
[![Supabase](https://img.shields.io/badge/Supabase-Auth-purple.svg)](https://supabase.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-ready FastAPI application that optimizes user prompts using AI to make them more efficient and effective. Features dual inference modes (Lazy/Pro), user authentication, Redis caching, prompt history, feedback system, and a modern web interface.

## ✨ Features

### 🔐 **Authentication System**
- **User Registration & Login** with email/password
- **JWT Token Management** with access and refresh tokens
- **Protected Routes** with authentication middleware
- **User Profile Management** with Supabase integration
- **Secure Session Handling** with automatic token refresh
- **Rate Limiting** (5 requests/minute) for auth operations
- **Security Features** including failed login tracking and account lockout

### 🤖 **AI Inference Engine**
- **Dual Mode Operation**:
  - **Lazy Mode**: Fast, cost-effective optimization (gpt-4o-mini, 250 tokens)
  - **Pro Mode**: Advanced, detailed optimization (gpt-4o, 2500 tokens)
- **Smart Parameter Configuration** based on mode selection
- **Input Validation & Sanitization** for security
- **Comprehensive Error Handling** with detailed logging
- **OpenAI API Rate Limiting** (60 requests/minute) for external API protection
- ⚠️ **Note**: Inference endpoints need rate limiting implementation

### 📝 **Prompt History & Feedback**
- **Complete Prompt History** with CRUD operations
- **User-specific History** with pagination and search
- **Like/Dislike Feedback** system with analytics
- **Feedback Statistics** and user summaries
- **Database Integration** with proper relationships and RLS

### 🚀 **Performance & Infrastructure**
- **Redis Caching** for optimized response times
- **Rate Limiting** for authentication and OpenAI API calls
- **CORS Configuration** for cross-origin requests
- **Health Check Endpoints** for monitoring
- **Structured Logging** with Loguru
- **Environment-based Configuration** for different deployments

### 🌐 **Modern Web Interface**
- **Responsive Design** with dark/light theme toggle
- **Real-time Chat Interface** with message history
- **Mode Selection** (Lazy/Pro) with visual indicators
- **Authentication UI** with login/register forms
- **Loading States & Error Handling** for better UX

### 🛡️ **Security & Guardrails**
- **Comprehensive Security Documentation** with guardrails prompts
- **Input Validation** and sanitization
- **Error Handling** without information leakage
- **JWT Authentication** with secure token management
- **Content Filtering Guidelines** (documentation ready)
- **Quality Control Standards** (documentation ready)

## 🏗️ Architecture

```
reprompt/
├── 📁 routes/              # API route handlers
│   ├── auth_router.py      # Authentication endpoints
│   ├── inference_router.py # AI inference endpoints
│   ├── prompt_history_router.py # Prompt history management
│   └── feedback_router.py  # Feedback system endpoints
├── 📁 services/            # Business logic services
│   ├── auth_service.py     # Authentication service with rate limiting
│   ├── openai_service.py   # OpenAI API integration with rate limiting
│   ├── redis.py           # Redis caching service
│   ├── prompt_history_service.py # Prompt history management
│   └── feedback_service.py # Feedback system service
├── 📁 models/              # AI model implementations
│   ├── lazy_inference.py  # Fast optimization model
│   └── pro_inference.py   # Advanced optimization model
├── 📁 schemas/             # Pydantic data models
│   ├── auth_schema.py     # Authentication schemas
│   ├── inference_schema.py # Inference schemas
│   ├── prompt_history_schema.py # Prompt history schemas
│   └── feedback_schema.py # Feedback schemas
├── 📁 static/              # Frontend assets
│   ├── chatbot.html       # Main chat interface
│   ├── auth.html          # Authentication page
│   ├── chatbot.js         # Frontend JavaScript
│   └── auth.js            # Auth JavaScript
├── 📁 prompts/             # AI context and guardrails
│   ├── guardrails/        # Security and quality control prompts
│   │   ├── security.md    # Security guidelines and prompts
│   │   ├── content_filter.md # Content filtering rules
│   │   ├── quality_control.md # Quality control standards
│   │   ├── rate_limiting.md # Rate limiting guidelines
│   │   └── README.md      # Guardrails overview
│   ├── core/              # Core inference context
│   │   ├── context.md     # Core context definitions
│   │   ├── examples.md    # Example prompts and responses
│   │   ├── requirements.md # Prompt requirements
│   │   └── tone.md        # Tone and style guidelines
│   ├── enhancements/      # Prompt enhancement strategies
│   │   ├── audience.md    # Audience-specific adaptations
│   │   ├── constraints.md # Constraint handling
│   │   ├── objectives.md  # Objective setting
│   │   └── terminology.md # Terminology guidelines
│   ├── domain_specific/   # Domain-specific contexts
│   │   ├── academic.md    # Academic writing context
│   │   ├── business.md    # Business communication context
│   │   ├── marketing.md   # Marketing content context
│   │   └── technical.md   # Technical documentation context
│   └── README.md          # Prompts directory overview
├── 📁 testing/             # Test suite
├── 📁 utils/               # Utility functions
├── 📁 database/            # Database schemas
├── main.py                 # FastAPI application entry point
├── config.py               # Configuration management
└── requirements.txt        # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **OpenAI API Key**
- **Supabase Project** (for authentication)
- **Redis Server** (optional, for caching)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd reprompt
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Create .env file with the following variables:
   ```

5. **Set up environment variables**
   ```env
   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Supabase Configuration
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
   
   # Redis Configuration (Optional)
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_PASSWORD=your_redis_password
   
   # Server Configuration
   HOST=0.0.0.0
   PORT=8001
   LOG_LEVEL=INFO
   
   # Security Configuration
   JWT_SECRET_KEY=your_jwt_secret_key_here
   CORS_ORIGINS=["http://localhost:3000", "http://localhost:8001"]
   ```

6. **Set up database**
   ```bash
   # Run the SQL scripts in database/ folder in your Supabase project
   # - supabase.sql (main database setup)
   # - prompt_history.sql (prompt history tables)
   # - feedback.sql (feedback system tables)
   ```

7. **Run the application**
   ```bash
   python main.py
   ```

8. **Access the application**
   - **API Documentation**: http://localhost:8001/docs
   - **Web Interface**: http://localhost:8001/static/chatbot.html
   - **Authentication**: http://localhost:8001/static/auth.html

## 📖 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/signup` | Register a new user |
| `POST` | `/api/v1/auth/login` | Authenticate user |
| `POST` | `/api/v1/auth/logout` | Logout user |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |
| `GET` | `/api/v1/auth/profile` | Get user profile |
| `GET` | `/api/v1/auth/validate` | Validate JWT token |

### Inference Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/optimize-prompt` | Optimize user prompt |
| `GET` | `/api/v1/cache/stats` | Get cache statistics |
| `DELETE` | `/api/v1/cache/clear` | Clear cache |

### Prompt History Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/prompt-history` | Get user's prompt history |
| `POST` | `/api/v1/prompt-history` | Save prompt optimization |
| `GET` | `/api/v1/prompt-history/{id}` | Get specific prompt history |
| `PUT` | `/api/v1/prompt-history/{id}` | Update prompt history |
| `DELETE` | `/api/v1/prompt-history/{id}` | Delete prompt history |

### Feedback Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/feedback` | Submit feedback |
| `GET` | `/api/v1/feedback/stats` | Get feedback statistics |
| `GET` | `/api/v1/feedback/user/{user_id}` | Get user feedback summary |

### Example API Usage

**Register a new user:**
```bash
curl -X POST "http://localhost:8001/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

**Login:**
```bash
curl -X POST "http://localhost:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

**Optimize a prompt:**
```bash
curl -X POST "http://localhost:8001/api/v1/optimize-prompt" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "prompt": "Write a story about a robot",
    "inference_type": "pro",
    "max_tokens": 1000
  }'
```

**Get prompt history:**
```bash
curl -X GET "http://localhost:8001/api/v1/prompt-history" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | - | ✅ |
| `SUPABASE_URL` | Supabase project URL | - | ✅ |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | - | ✅ |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | - | ✅ |
| `REDIS_HOST` | Redis server host | localhost | ❌ |
| `REDIS_PORT` | Redis server port | 6379 | ❌ |
| `REDIS_PASSWORD` | Redis password | - | ❌ |
| `HOST` | Server host | 0.0.0.0 | ❌ |
| `PORT` | Server port | 8001 | ❌ |
| `JWT_SECRET_KEY` | JWT secret key | - | ✅ |
| `CORS_ORIGINS` | CORS allowed origins | ["*"] | ❌ |

### Model Configuration

| Mode | Model | Max Tokens | Temperature | Use Case |
|------|-------|------------|-------------|----------|
| **Lazy** | gpt-4o-mini | 250 | 0.3 | Quick, cost-effective optimization |
| **Pro** | gpt-4o | 2500 | 0.7 | Detailed, advanced optimization |

### Rate Limiting Configuration

| Service | Rate Limit | Window | Purpose |
|---------|------------|--------|---------|
| **Authentication** | 5 requests | 1 minute | Prevent brute force attacks |
| **OpenAI API** | 60 requests | 1 minute | Respect OpenAI limits |
| **Inference Endpoints** | ⚠️ **NOT IMPLEMENTED** | - | **CRITICAL GAP** |

## 🚀 Deployment

### Production Deployment

1. **Set up production environment variables**
2. **Configure reverse proxy** (nginx/Apache)
3. **Set up SSL certificates**
4. **Configure Redis for caching**
5. **Set up monitoring and logging**
6. **⚠️ CRITICAL: Implement rate limiting for inference endpoints**

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8001

CMD ["python", "main.py"]
```

### Environment-specific Configuration

- **Development**: Debug logging, CORS enabled
- **Staging**: Production-like with test data
- **Production**: Optimized performance, security hardening

## 📊 Performance Metrics

- **Response Time**: < 2s (Lazy), < 5s (Pro)
- **Rate Limit**: 60 requests/minute (OpenAI), 5 requests/minute (Auth)
- **Concurrent Users**: Limited by OpenAI rate limits
- **Cache Hit Rate**: Depends on Redis usage
- **Uptime**: 99.9% (with proper infrastructure)

## 🔒 Security Features

- **JWT Authentication** with secure token management
- **Input Validation** and sanitization
- **Rate Limiting** for authentication and OpenAI API calls
- **CORS Configuration** for secure cross-origin requests
- **Environment Variable Protection** for sensitive data
- **Error Handling** without information leakage
- **Guardrails Documentation** for security, content filtering, and quality control

### 🚨 Security Considerations

- **Rate Limiting Gap**: Inference endpoints need rate limiting implementation
- **Cost Protection**: Implement user-based limits to prevent expensive API abuse
- **Guardrails**: Security prompts documented but not actively enforced

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest black isort pylint

# Run code formatting
black .
isort .

# Run linting
pylint .

# Run tests
pytest testing/
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Create GitHub issues for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas

## 🎯 Roadmap

### Phase 2 (Next Release) - Security Focus
- 🔥 **CRITICAL**: Implement inference endpoint rate limiting
- 🔥 **CRITICAL**: Add user-based rate limiting system
- 🔥 **CRITICAL**: Implement Redis-based distributed rate limiting
- [ ] Frontend integration for prompt history management
- [ ] Frontend integration for feedback display
- [ ] Advanced caching strategies and analytics
- [ ] User dashboard and preferences

### Phase 3 (Future)
- [ ] Custom model fine-tuning
- [ ] Multi-language support
- [ ] Advanced prompt templates
- [ ] Team collaboration features
- [ ] Enterprise features
- [ ] Active guardrails enforcement
- [ ] Monitoring using Grafana

## 🚨 Important Notes

### Production Readiness
This application is **production-ready** with comprehensive features, but has **critical security gaps** that must be addressed before deployment:

1. **Rate Limiting**: Inference endpoints are completely unprotected
2. **Cost Risk**: Users can make unlimited expensive OpenAI API calls
3. **Security**: Guardrails are documented but not actively enforced

### Immediate Action Required
Before production deployment, implement:
- Rate limiting for inference endpoints
- User-based usage limits
- Active guardrails enforcement
- Cost monitoring and alerts

---

**Built with ❤️ using FastAPI, OpenAI, Supabase, and Redis**