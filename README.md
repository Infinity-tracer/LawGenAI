# NyayAssist - Legal AI Assistant 🏛️⚖️

A comprehensive AI-powered legal assistant platform for India, featuring PDF document analysis and Indian Kanoon case law search capabilities.

## 📋 Project Overview

NyayAssist consists of two main components:

1. **Backend API** (`Naya/NyayAssist/`) - FastAPI-based REST API with MySQL database integration
2. **Frontend App** (`nyayasist/`) - React + TypeScript web application

## ✨ Features

- **PDF Chat** - Upload legal documents and ask questions using AI-powered analysis
- **Indian Kanoon Integration** - Search Indian case law database directly
- **User Authentication** - Secure user registration and login system
- **Session Management** - Track chat sessions and conversation history
- **Access Logging** - Comprehensive API access logging and analytics
- **Feedback System** - Collect user feedback on AI responses

## 🏗️ Architecture

```
LawGenAI/
├── Naya/NyayAssist/          # Backend API
│   ├── api_with_db.py        # Main FastAPI application
│   ├── api.py                # Simplified API (without DB)
│   ├── app.py                # Streamlit app
│   ├── setup_database.py     # Database initialization script
│   ├── database/             # Database models and services
│   │   ├── db_config.py      # Database configuration
│   │   ├── db_service.py     # Database operations
│   │   ├── models.py         # SQLAlchemy models
│   │   └── schema.sql        # SQL schema
│   ├── middleware/           # Custom middleware
│   │   └── logging_middleware.py
│   └── faiss_index/          # Vector store for PDF embeddings
│
└── nyayasist/                # Frontend React App
    ├── App.tsx               # Main application component
    ├── components/           # React components
    │   ├── Auth.tsx          # Authentication component
    │   ├── Chat.tsx          # Chat interface
    │   ├── Landing.tsx       # Landing page
    │   └── Icons.tsx         # Icon components
    └── utils/                # Utility functions
        ├── apiService.ts     # API client functions
        └── crypto.ts         # Encryption utilities
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- npm or yarn

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd Naya/NyayAssist
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the `Naya/NyayAssist/` directory:
   ```env
   # Google AI API Key (for Gemini)
   GOOGLE_API_KEY=your_google_api_key
   
   # Indian Kanoon API Token
   KANOON_API_TOKEN=your_kanoon_api_token
   
   # MySQL Database Configuration
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_DATABASE=nyayassist_db
   ```

5. **Initialize the database:**
   ```bash
   python setup_database.py
   ```

6. **Run the API server:**
   ```bash
   python api_with_db.py
   ```
   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd nyayasist
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run the development server:**
   ```bash
   npm run dev
   ```
   The frontend will be available at `http://localhost:5173`

## 📡 API Endpoints

### User Management
- `POST /api/users/register` - Register a new user
- `POST /api/users/login` - User login

### Sessions
- `POST /api/sessions/create` - Create a new chat session

### PDF Operations
- `POST /api/pdf/upload` - Upload PDF files for processing
- `POST /api/pdf/chat` - Chat with uploaded PDFs

### Indian Kanoon Search
- `POST /api/kanoon/search` - Search Indian case law

### Feedback
- `POST /api/feedback` - Submit feedback on AI responses

### System
- `GET /` - API status
- `GET /health` - Health check endpoint

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **MySQL** - Relational database
- **LangChain** - LLM framework for document processing
- **FAISS** - Vector similarity search
- **HuggingFace** - Sentence transformers for embeddings
- **Google Gemini** - Large Language Model
- **PyPDF2** - PDF text extraction

### Frontend
- **React 19** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Build tool and dev server
- **TailwindCSS** - Utility-first CSS framework

## 📦 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google AI API key for Gemini | Yes |
| `KANOON_API_TOKEN` | Indian Kanoon API token | Yes |
| `MYSQL_HOST` | MySQL server host | Yes |
| `MYSQL_PORT` | MySQL server port | No (default: 3306) |
| `MYSQL_USER` | MySQL username | Yes |
| `MYSQL_PASSWORD` | MySQL password | Yes |
| `MYSQL_DATABASE` | MySQL database name | No (default: nyayassist_db) |

## 🗄️ Database Schema

The application uses the following main tables:
- `users` - User accounts
- `user_sessions` - Authentication sessions
- `chat_sessions` - Chat conversation sessions
- `messages` - Individual chat messages
- `llm_outputs` - AI model responses
- `kanoon_queries` - Indian Kanoon search logs
- `pdf_uploads` - Uploaded PDF metadata
- `feedback` - User feedback
- `access_logs` - API access logs
- `analytics` - Usage analytics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

- NyayAssist Team

## 🙏 Acknowledgments

- [Indian Kanoon](https://indiankanoon.org/) - For providing access to Indian case law
- [Google AI](https://ai.google/) - For Gemini LLM
- [LangChain](https://langchain.com/) - For the LLM framework
