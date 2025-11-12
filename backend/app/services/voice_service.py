"""语音识别与语音规划服务"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import os
import wave
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from dateutil import parser as date_parser

try:
    import dashscope
    from dashscope import MultiModalConversation
except ImportError:  # pragma: no cover
    dashscope = None
    MultiModalConversation = None

from ..agents.trip_planner_agent import get_trip_planner_agent
from ..config import get_settings
from ..models.schemas import TripPlan, TripRequest, VoiceFormSuggestion
from ..services.llm_service import get_llm


class VoiceServiceError(Exception):
    """语音服务异常"""


VOICE_FORM_SYSTEM_PROMPT = """
你是一名精通中文的旅行表单抽取助手,需要从用户的自然语言输入中提取旅行规划所需字段。
输出要求:
1. 严格返回一个JSON对象,不要添加任何多余文字。
2. JSON键名固定为: city, start_date, end_date, travel_days, transportation, accommodation, preferences, free_text_input。
3. 日期使用YYYY-MM-DD格式; 如果无法确定,对应值设为null。
4. preferences是字符串数组,只包含与用户偏好相关的短标签,例如["美食","亲子","自然","动漫","购物","户外","历史文化","夜生活"]。
5. free_text_input用于保留预算、同行人、特殊需求等额外信息。
6. 如果用户未提及某字段,值设为null,不要编造。
"""


def _safe_json_loads(text: str) -> dict:
    """提取并解析JSON字符串"""
    if not text:
        return {}
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def _format_missing_fields(form: VoiceFormSuggestion, require_travel_days: bool = False) -> List[str]:
    """计算缺失字段"""
    missing = []
    if not form.city:
        missing.append("city")
    has_start = bool(form.start_date)
    if not has_start:
        missing.append("start_date")

    has_end = bool(form.end_date)
    has_travel_days = _valid_travel_days(form.travel_days)
    if not has_end and not has_travel_days:
        missing.append("end_date")
    if require_travel_days:
        has_duration_hint = has_travel_days or (has_start and has_end)
        if not has_duration_hint:
            missing.append("travel_days")
    return missing


def _normalize_preferences(preferences: Optional[List[str]]) -> List[str]:
    """清洗偏好标签"""
    if not preferences:
        return []
    cleaned = []
    seen = set()
    for item in preferences:
        if not item:
            continue
        token = item.strip()
        if not token or token in seen:
            continue
        cleaned.append(token)
        seen.add(token)
    return cleaned


def _normalize_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        parsed = date_parser.parse(value, fuzzy=True).date()
        return parsed.isoformat()
    except Exception:
        return None


def _calc_days(start: str, end: str) -> Optional[int]:
    try:
        start_dt = datetime.fromisoformat(start).date()
        end_dt = datetime.fromisoformat(end).date()
        delta = (end_dt - start_dt).days
        if delta < 0:
            return None
        return delta + 1
    except ValueError:
        return None


def _valid_travel_days(value: Optional[int]) -> bool:
    return isinstance(value, int) and value > 0


def _infer_end_date(start_iso: Optional[str], travel_days: Optional[int]) -> Optional[str]:
    if not start_iso or not _valid_travel_days(travel_days):
        return None
    try:
        start_dt = datetime.fromisoformat(start_iso).date()
    except ValueError:
        return None
    offset = timedelta(days=travel_days - 1)
    return (start_dt + offset).isoformat()


class VoiceService:
    """阿里云百炼语音识别与语音驱动行程规划"""

    def __init__(self):
        self.settings = get_settings()
        self.llm = get_llm()

    def _resolve_bailian_config(self) -> dict:
        api_key = os.getenv("BAILIAN_API_KEY") or self.settings.bailian_api_key
        base_url = os.getenv("BAILIAN_BASE_URL") or self.settings.bailian_base_url
        model = os.getenv("BAILIAN_MODEL") or self.settings.bailian_model
        workspace = os.getenv("BAILIAN_WORKSPACE_ID") or self.settings.bailian_workspace_id
        fmt = (os.getenv("BAILIAN_FORMAT") or self.settings.bailian_format or "wav").lower()
        sample_rate_raw = os.getenv("BAILIAN_SAMPLE_RATE")
        sample_rate = self.settings.bailian_sample_rate or 16000
        if sample_rate_raw:
            try:
                sample_rate = int(sample_rate_raw)
            except ValueError as exc:
                raise VoiceServiceError("BAILIAN_SAMPLE_RATE必须是整数") from exc
        language = os.getenv("BAILIAN_LANGUAGE") or getattr(self.settings, "bailian_language", "zh")
        return {
            "api_key": api_key,
            "base_url": base_url,
            "model": model,
            "workspace": workspace,
            "format": fmt,
            "sample_rate": int(sample_rate),
            "language": (language or "zh").strip() or "zh",
        }

    def _ensure_credentials(self) -> dict:
        config = self._resolve_bailian_config()
        if not config["api_key"]:
            raise VoiceServiceError("未配置阿里云百炼API Key")
        if not config["model"]:
            raise VoiceServiceError("未配置阿里云百炼语音识别模型")
        if not config["base_url"]:
            raise VoiceServiceError("未配置阿里云百炼接口地址")
        return config

    @staticmethod
    def _http_base_url(base_url: str) -> str:
        base = base_url
        if isinstance(base, dict):
            base = base.get("base_url") or base.get("url")
        if base is None:
            base = ""
        base = str(base).strip()
        if not base:
            base = "https://dashscope.aliyuncs.com/api/v1"
        try:
            if base.startswith("wss://"):
                base = "https://" + base[len("wss://") :]
            elif base.startswith("ws://"):
                base = "http://" + base[len("ws://") :]
        except AttributeError:
            base = str(base)
            if base.startswith("wss://"):
                base = "https://" + base[len("wss://") :]
            elif base.startswith("ws://"):
                base = "http://" + base[len("ws://") :]
        base = base.rstrip("/")
        if base.endswith("/api-ws/v1/inference"):
            base = base[: -len("/api-ws/v1/inference")] + "/api/v1"
        return base

    @staticmethod
    def _ensure_dashscope_sdk():
        if dashscope is None or MultiModalConversation is None:
            raise VoiceServiceError("未安装dashscope依赖,请执行 pip install dashscope")

    @staticmethod
    def _build_dashscope_messages(
        audio_base64: str,
        audio_format: str,
    ) -> List[dict]:
        if not audio_base64:
            raise VoiceServiceError("音频数据为空,无法发送至语音识别服务")

        fmt = (audio_format or "wav").lower()
        mime_map = {"wav": "audio/wav", "pcm": "audio/pcm", "mp3": "audio/mpeg"}
        mime = mime_map.get(fmt, f"audio/{fmt}")
        audio_data_uri = f"data:{mime};base64,{audio_base64}"

        return [
            {"role": "user", "content": [{"audio": audio_data_uri}]},
        ]

    def _extract_dashscope_text(self, response) -> str:
        status_code = getattr(response, "status_code", None)
        if status_code and status_code != 200:
            message = getattr(response, "message", "阿里云百炼接口调用失败")
            raise VoiceServiceError(f"阿里云百炼返回错误[{status_code}]: {message}")

        output = getattr(response, "output", None) or {}
        choices = output.get("choices") or []
        texts: List[str] = []
        for choice in choices:
            message = (choice or {}).get("message") or {}
            for item in message.get("content") or []:
                text = item.get("text")
                if text:
                    texts.append(text)

        transcript = "".join(texts).strip()
        if transcript:
            return transcript

        fallback_text = output.get("text")
        if isinstance(fallback_text, str):
            return fallback_text.strip()
        return ""

    @staticmethod
    def _pcm_from_wav(audio_bytes: bytes, expected_rate: int = 16000) -> bytes:
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wav_reader:
                channels = wav_reader.getnchannels()
                sample_width = wav_reader.getsampwidth()
                frame_rate = wav_reader.getframerate()
                if channels != 1:
                    raise VoiceServiceError("请提供单声道音频")
                if sample_width != 2:
                    raise VoiceServiceError("请使用16位PCM编码音频")
                if frame_rate != expected_rate:
                    raise VoiceServiceError(f"请提供{expected_rate // 1000}k采样率音频")
                frames = wav_reader.readframes(wav_reader.getnframes())
                if not frames:
                    raise VoiceServiceError("音频数据为空")
                return frames
        except wave.Error as exc:
            raise VoiceServiceError(f"音频格式解析失败: {exc}") from exc

    async def transcribe_audio(self, audio_bytes: bytes) -> str:
        """上传音频到阿里云百炼并返回识别文本"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._transcribe_sync, audio_bytes)

    def _transcribe_sync(self, audio_bytes: bytes) -> str:
        config = self._ensure_credentials()
        self._ensure_dashscope_sdk()

        sample_rate = config["sample_rate"]
        pcm_frames = self._pcm_from_wav(audio_bytes, sample_rate)

        audio_format = (config.get("format") or "wav").lower()
        payload_bytes = pcm_frames if audio_format == "pcm" else audio_bytes
        if not payload_bytes:
            raise VoiceServiceError("音频数据为空,无法提交识别")

        audio_base64 = base64.b64encode(payload_bytes).decode("utf-8")

        try:
            dashscope.base_http_api_url = self._http_base_url(config["base_url"])

            messages = self._build_dashscope_messages(audio_base64, audio_format)
            asr_options = {"enable_itn": True}
            if config.get("language"):
                asr_options["language"] = config["language"]

            response = MultiModalConversation.call(
                api_key=config["api_key"],
                model=config["model"],
                messages=messages,
                result_format="message",
                asr_options=asr_options,
            )
        except Exception as exc:
            raise VoiceServiceError(f"语音识别请求失败: {exc}") from exc

        transcript = self._extract_dashscope_text(response)
        if not transcript:
            raise VoiceServiceError("语音识别成功，但未检测到文字内容，请清晰描述后再试")
        return transcript

    async def parse_form_suggestion(self, transcript: str) -> VoiceFormSuggestion:
        if not transcript:
            return VoiceFormSuggestion()

        loop = asyncio.get_running_loop()
        try:
            data = await loop.run_in_executor(None, self._parse_form_sync, transcript)
        except VoiceServiceError as exc:
            print(f"[VoiceService] 解析语音文本失败: {exc}")
            return VoiceFormSuggestion()
        form = VoiceFormSuggestion(**data) if data else VoiceFormSuggestion()

        form.start_date = _normalize_date(form.start_date)
        form.end_date = _normalize_date(form.end_date)
        if not form.end_date:
            inferred_end = _infer_end_date(form.start_date, form.travel_days)
            if inferred_end:
                form.end_date = inferred_end
        if not _valid_travel_days(form.travel_days) and form.start_date and form.end_date:
            inferred_days = _calc_days(form.start_date, form.end_date)
            if inferred_days:
                form.travel_days = inferred_days
        form.preferences = _normalize_preferences(form.preferences)
        return form

    def _parse_form_sync(self, transcript: str) -> dict:
        messages = [
            {"role": "system", "content": VOICE_FORM_SYSTEM_PROMPT.strip()},
            {"role": "user", "content": transcript.strip()},
        ]
        try:
            response_text = self.llm.invoke(messages, temperature=0.2, max_tokens=512)
        except Exception as exc:
            raise VoiceServiceError(f"LLM解析语音文本失败: {exc}") from exc
        data = _safe_json_loads(response_text)
        if not data:
            raise VoiceServiceError("LLM未返回有效JSON,请重试")

        prefs = data.get("preferences")
        if prefs is None:
            data["preferences"] = []
        elif isinstance(prefs, str):
            data["preferences"] = [prefs]
        elif not isinstance(prefs, list):
            data["preferences"] = []

        return data

    def _build_trip_request(self, form: VoiceFormSuggestion) -> TripRequest:
        missing = _format_missing_fields(form, require_travel_days=True)
        if missing:
            raise VoiceServiceError(f"缺少必要字段: {', '.join(missing)}")

        start = form.start_date or ""
        start_iso = _normalize_date(start)
        if not start_iso:
            raise VoiceServiceError("无法解析语音中的日期,请补充后重试")

        end_iso = _normalize_date(form.end_date or "")
        input_travel_days = form.travel_days if _valid_travel_days(form.travel_days) else None
        if not end_iso:
            inferred_end = _infer_end_date(start_iso, input_travel_days)
            if inferred_end:
                end_iso = inferred_end
                if not form.end_date:
                    form.end_date = inferred_end
        if not end_iso:
            raise VoiceServiceError("无法解析语音中的日期,请补充后重试")

        travel_days = input_travel_days or _calc_days(start_iso, end_iso)
        if not travel_days:
            raise VoiceServiceError("无法确定旅行天数,请补充后重试")
        if input_travel_days is None:
            form.travel_days = travel_days

        transportation = form.transportation or "公共交通"
        accommodation = form.accommodation or "舒适型酒店"
        preferences = form.preferences or []
        free_text = form.free_text_input or ""

        return TripRequest(
            city=form.city or "",
            start_date=start_iso,
            end_date=end_iso,
            travel_days=travel_days,
            transportation=transportation,
            accommodation=accommodation,
            preferences=preferences,
            free_text_input=free_text,
        )

    async def plan_trip_from_voice(self, audio_bytes: bytes) -> Tuple[str, VoiceFormSuggestion, TripPlan]:
        transcript = await self.transcribe_audio(audio_bytes)
        suggestion = await self.parse_form_suggestion(transcript)

        missing = _format_missing_fields(suggestion, require_travel_days=True)
        if missing:
            raise VoiceServiceError(f"语音信息不完整,缺少: {', '.join(missing)}")

        trip_request = self._build_trip_request(suggestion)

        loop = asyncio.get_running_loop()
        agent = get_trip_planner_agent()
        trip_plan: TripPlan = await loop.run_in_executor(None, agent.plan_trip, trip_request)
        return transcript, suggestion, trip_plan

    async def plan_trip_from_transcript(self, transcript: str) -> Tuple[str, VoiceFormSuggestion, TripPlan]:
        clean_text = (transcript or "").strip()
        if not clean_text:
            raise VoiceServiceError("请输入有效的语音文本")

        suggestion = await self.parse_form_suggestion(clean_text)
        missing = _format_missing_fields(suggestion, require_travel_days=True)
        if missing:
            raise VoiceServiceError(f"语音信息不完整,缺少: {', '.join(missing)}")

        trip_request = self._build_trip_request(suggestion)
        loop = asyncio.get_running_loop()
        agent = get_trip_planner_agent()
        trip_plan: TripPlan = await loop.run_in_executor(None, agent.plan_trip, trip_request)
        return clean_text, suggestion, trip_plan

    def get_missing_fields(self, suggestion: VoiceFormSuggestion, require_travel_days: bool = False) -> List[str]:
        return _format_missing_fields(suggestion, require_travel_days)


_voice_service: Optional[VoiceService] = None


def get_voice_service() -> VoiceService:
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service
