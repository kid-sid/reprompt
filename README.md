# 🤖 Reprompt Chatbot

A FastAPI-powered AI prompt optimization application that helps users create more effective prompts using two different optimization techniques: **Lazy** and **Pro** modes.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   OpenAI API    │
│   (HTML/JS)     │◄──►│   Backend       │◄──►│   (GPT-3.5/4)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Redis Cache   │
                       │   (Optional)    │
                       └─────────────────┘
```

## 📁 Project Structure

```
reprompt/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration settings and environment variables
├── requirements.txt       # Python dependencies
├── static/
│   └── index.html        # Frontend interface with lazy/pro toggle
├── models/
│   ├── lazy_inference.py # Simple prompt optimization (GPT-3.5)
│   └── pro_inference.py  # Advanced prompt optimization (GPT-4)
├── services/
│   ├── openai_service.py # OpenAI client configuration
│   └── redis.py          # Redis caching service
├── routes/
│   └── inference_router.py # API endpoints and routing logic
├── schemas/
│   └── inference_schema.py # Pydantic models for request/response
└── utils/
    └── helpers.py        # Utility functions
```

## 🎯 Core Features

### 1. **Dual Optimization Modes**

#### 🐌 **Lazy Mode**
- **Model**: GPT-3.5-turbo
- **Technique**: Simple and straightforward optimization
- **Use Case**: Quick, basic prompt improvements
- **Features**: 
  - Basic clarity and specificity improvements
  - Fast response times
  - Cost-effective

#### ⚡ **Pro Mode**
- **Model**: GPT-4o
- **Technique**: Advanced AI optimization strategies
- **Use Case**: Sophisticated prompt engineering
- **Features**:
  - Chain-of-thought reasoning
  - Role-based prompting
  - Context window optimization
  - Output format specification
  - Constraint-based prompting

### 2. **Smart Caching System**
- **Redis Integration**: Optional caching for optimized prompts
- **Cache Key**: MD5 hash of prompt + inference type
- **TTL**: Configurable cache expiration (default: 1 hour)
- **Benefits**: Reduced API calls, faster responses, cost savings

### 3. **User Experience**
- **Modern UI**: Clean, responsive interface with dark/light themes
- **Real-time Toggle**: Switch between Lazy and Pro modes instantly
- **Persistent Settings**: Remembers user preferences
- **Visual Feedback**: Loading states and error handling

## 🔧 Technical Components

### **Backend (FastAPI)**

#### **Configuration Management**
```python
# config.py
class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    LAZY_MODEL: str = "gpt-3.5-turbo"
    PRO_MODEL: str = "gpt-4o"
    MAX_TOKENS: int = 1000
    TEMPERATURE: float = 0.7
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
```

#### **Inference Modules**
- **Lazy Inference**: Simple prompt optimization with basic instructions
- **Pro Inference**: Advanced optimization with system prompts and detailed requirements

#### **API Endpoints**
- `POST /api/v1/optimize-prompt` - Main optimization endpoint
- `GET /api/v1/models` - Available models and techniques
- `GET /api/v1/health` - Health check
- `GET /api/v1/cache/stats` - Cache statistics
- `DELETE /api/v1/cache/clear` - Clear cache
- `GET /api/v1/history/{user_id}` - User prompt history

### **Frontend (HTML/JavaScript)**

#### **Key Features**
- **Theme Toggle**: Dark/light mode switching
- **Inference Toggle**: Lazy/Pro mode switching
- **Real-time Updates**: Dynamic UI based on selected mode
- **Local Storage**: Persistent user preferences
- **Responsive Design**: Works on all screen sizes

#### **API Integration**
```javascript
// Example API call
const response = await fetch('/api/v1/optimize-prompt', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        prompt: "Write a story",
        inference_type: "pro", // or "lazy"
        max_tokens: 512
    })
});
```

### **Caching Layer (Redis)**

#### **Cache Features**
- **Prompt Optimization Cache**: Stores optimized results
- **User History**: Tracks user's optimization history
- **Session Management**: User session data caching
- **Statistics**: Cache hit/miss metrics

#### **Cache Keys**
- `prompt_optimization:{md5_hash}` - Optimized prompt results
- `prompt_history:{user_id}` - User optimization history
- `user_session:{session_id}` - User session data

## 🚀 Getting Started

### **Prerequisites**
- Python 3.8+
- Redis (optional, for caching)
- OpenAI API key

### **Installation**

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

4. **Set up environment variables**
```bash
# Create .env file
OPENAI_API_KEY=your_openai_api_key_here
LAZY_MODEL=gpt-3.5-turbo
PRO_MODEL=gpt-4o
MAX_TOKENS=1000
TEMPERATURE=0.7
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
```

5. **Start Redis (optional)**
```bash
# Install Redis or use Docker
docker run -d -p 6379:6379 redis:alpine
```

6. **Run the application**
```bash
uvicorn main:app --reload
```

7. **Access the application**
- Frontend: http://localhost:8000/static/index.html
- API Docs: http://localhost:8000/docs

## 📊 API Usage

### **Optimize Prompt**
```bash
curl -X POST "http://localhost:8000/api/v1/optimize-prompt" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a story about a cat",
    "inference_type": "pro",
    "max_tokens": 512
  }'
```

### **Response Format**
```json
{
  "output": "Create a compelling narrative about a feline protagonist...",
  "tokens_used": 0,
  "inference_type": "pro",
  "model_used": "gpt-4o",
  "cached": false
}
```

## 🔄 Workflow

1. **User Input**: User enters a prompt in the frontend
2. **Mode Selection**: User chooses between Lazy or Pro mode
3. **Cache Check**: System checks Redis for existing optimization
4. **API Call**: If not cached, calls appropriate OpenAI model
5. **Optimization**: Applies selected optimization technique
6. **Caching**: Stores result in Redis for future use
7. **Response**: Returns optimized prompt to user

## 🎨 Customization

### **Adding New Models**
1. Update `config.py` with new model settings
2. Create new inference module in `models/`
3. Add routing logic in `routes/inference_router.py`
4. Update frontend to include new mode

### **Custom Optimization Techniques**
- Modify prompting strategies in inference modules
- Add new system prompts for different use cases
- Implement custom validation and preprocessing

### **Cache Configuration**
- Adjust TTL values in `services/redis.py`
- Modify cache key generation strategies
- Add new cache patterns for different data types

## 🔒 Security Considerations

- **API Key Management**: Store OpenAI API key in environment variables
- **Input Validation**: Validate and sanitize user prompts
- **Rate Limiting**: Implement rate limiting for API endpoints
- **Error Handling**: Graceful error handling without exposing sensitive data

## 📈 Performance Optimization

- **Caching Strategy**: Intelligent caching reduces API calls
- **Async Processing**: FastAPI provides high-performance async operations
- **Connection Pooling**: Redis connection pooling for better performance
- **Response Compression**: Enable gzip compression for faster responses

## 🧪 Testing

### **Manual Testing**
1. Test both Lazy and Pro modes
2. Verify caching functionality
3. Test error scenarios
4. Validate frontend responsiveness

### **API Testing**
```bash
# Test health endpoint
curl http://localhost:8000/api/v1/health

# Test models endpoint
curl http://localhost:8000/api/v1/models

# Test cache stats
curl http://localhost:8000/api/v1/cache/stats
```

## 🚀 Deployment

### **Production Considerations**
- Use production ASGI server (Gunicorn + Uvicorn)
- Set up proper logging
- Configure Redis for production
- Implement monitoring and alerting
- Set up CI/CD pipeline

### **Docker Deployment**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the configuration options in `config.py`

---

**Built with ❤️ using FastAPI, OpenAI, and Redis**
