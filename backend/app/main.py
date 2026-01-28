from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from loguru import logger
import sys
import json

from app.core.config import settings
from app.db.database import engine, Base
from app.api.routes import chat, knowledge, tasks, roles, conversation_config


# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("Starting Agent System API...")
    
    # 创建数据库表
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
    
    yield
    
    # 关闭时
    logger.info("Shutting down Agent System API...")


# 创建FastAPI应用
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 添加请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求"""
    # 对于流式请求，不记录请求体以避免干扰
    if request.method == "POST" and "/stream" in request.url.path:
        logger.debug(f"POST {request.url.path} - Streaming request (body not logged)")
        response = await call_next(request)
        return response
    
    # 对于非流式请求，记录请求体
    if request.method == "POST":
        body = await request.body()
        try:
            body_dict = json.loads(body) if body else {}
            logger.debug(f"POST {request.url.path} Body: {body_dict}")
        except:
            logger.debug(f"POST {request.url.path} Body: {body}")
        
        # 由于body已经被读取，需要重新创建request
        async def receive():
            return {"type": "http.request", "body": body}
        request._receive = receive
    
    response = await call_next(request)
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理验证错误，提供更详细的错误信息"""
    logger.error(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


# 注册路由
app.include_router(chat.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(roles.router, prefix="/api")
app.include_router(conversation_config.router, prefix="/api")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Agent System API",
        "version": settings.API_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "agent-system-api"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )

