"""配置管理模块"""

import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 加载环境变量
# 首先尝试加载当前目录的.env
load_dotenv()

# 再尝试加载 backend/.env(如果存在)
backend_env = Path(__file__).resolve().parent.parent / ".env"
if backend_env.exists():
    load_dotenv(backend_env, override=False)

# 然后尝试加载AiTravelPlanner的.env(如果存在)
aitravelplanner_env = Path(__file__).parent.parent.parent.parent / "ai-travel-planner" / ".env"
if aitravelplanner_env.exists():
    load_dotenv(aitravelplanner_env, override=False)  # 不覆盖已有的环境变量


class Settings(BaseSettings):
    """应用配置"""

    # 应用基本配置
    app_name: str = "AiTravelPlanner智能旅行助手"
    app_version: str = "1.0.0"
    debug: bool = False

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS配置 - 使用字符串,在代码中分割
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"

    # 高德地图API配置
    amap_api_key: str = ""

    # Unsplash API配置
    unsplash_access_key: str = ""
    unsplash_secret_key: str = ""

    # LLM配置 (从环境变量读取,由AiTravelPlanner管理)
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4"

    # 阿里云百炼语音识别配置
    bailian_api_key: str = ""
    bailian_base_url: str = ""
    bailian_model: str = ""
    bailian_workspace_id: str = ""
    bailian_format: str = "pcm"
    bailian_sample_rate: int = 16000
    bailian_language: str = "zh"

    # 日志配置
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # 忽略额外的环境变量

    def get_cors_origins_list(self) -> List[str]:
        """获取CORS origins列表"""
        return [origin.strip() for origin in self.cors_origins.split(',')]


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings


# 验证必要的配置
def validate_config():
    """验证配置是否完整"""
    errors = []
    warnings = []

    if not settings.amap_api_key:
        errors.append("AMAP_API_KEY未配置")

    # AiTravelPlannerLLM会自动从LLM_API_KEY读取,不强制要求OPENAI_API_KEY
    llm_api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not llm_api_key:
        warnings.append("LLM_API_KEY或OPENAI_API_KEY未配置,LLM功能可能无法使用")

    bailian_api_key = os.getenv("BAILIAN_API_KEY") or settings.bailian_api_key
    if not bailian_api_key:
        warnings.append("BAILIAN_API_KEY未配置,语音输入功能不可用")

    if errors:
        error_msg = "配置错误:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)

    if warnings:
        print("\n⚠️  配置警告:")
        for w in warnings:
            print(f"  - {w}")

    return True


# 打印配置信息(用于调试)
def print_config():
    """打印当前配置(隐藏敏感信息)"""
    print(f"应用名称: {settings.app_name}")
    print(f"版本: {settings.app_version}")
    print(f"服务器: {settings.host}:{settings.port}")
    print(f"高德地图API Key: {'已配置' if settings.amap_api_key else '未配置'}")

    # 检查LLM配置
    llm_api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    llm_base_url = os.getenv("LLM_BASE_URL") or settings.openai_base_url
    llm_model = os.getenv("LLM_MODEL_ID") or settings.openai_model

    print(f"LLM API Key: {'已配置' if llm_api_key else '未配置'}")
    print(f"LLM Base URL: {llm_base_url}")
    print(f"LLM Model: {llm_model}")

    bailian_api_key = os.getenv("BAILIAN_API_KEY") or settings.bailian_api_key
    bailian_base_url = os.getenv("BAILIAN_BASE_URL") or settings.bailian_base_url
    bailian_model = os.getenv("BAILIAN_MODEL") or settings.bailian_model
    bailian_workspace = os.getenv("BAILIAN_WORKSPACE_ID") or settings.bailian_workspace_id

    has_voice = bool(bailian_api_key)
    print(f"语音识别: {'已启用' if has_voice else '未配置'}")
    if has_voice:
        print(f"  - 模型111: {bailian_model or '默认'}")
        print(f"  - 服务: {bailian_base_url}")
        if bailian_workspace:
            print(f"  - 工作空间: {bailian_workspace}")
    print(f"日志级别: {settings.log_level}")

