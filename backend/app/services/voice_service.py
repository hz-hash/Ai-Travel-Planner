"""语音识别与语音规划服务"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import io
import json
import math
import wave
from datetime import datetime
from email.utils import formatdate
from typing import List, Optional, Tuple
from urllib.parse import urlencode

import websockets
from dateutil import parser as date_parser

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
    if not form.start_date:
        missing.append("start_date")
    if not form.end_date:
        missing.append("end_date")
    if require_travel_days:
        has_days = bool(form.travel_days) or (form.start_date and form.end_date)
        if not has_days:
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


class VoiceService:
    """科大讯飞语音识别与语音驱动行程规划"""

    FRAME_SIZE = 1280  # 每帧字节数
    FRAME_INTERVAL = 0.04  # 40ms

    def __init__(self):
        self.settings = get_settings()
        self.llm = get_llm()

    def _ensure_credentials(self):
        if not (
            self.settings.iflytek_app_id
            and self.settings.iflytek_api_key
            and self.settings.iflytek_api_secret
        ):
            raise VoiceServiceError("未配置科大讯飞语音识别凭证")

    def _build_ws_url(self) -> str:
        host = self.settings.iflytek_host or "iat-api.xfyun.cn"
        path = self.settings.iflytek_path or "/v2/iat"
        date_str = formatdate(timeval=None, usegmt=True)
        signature_origin = f"host: {host}\ndate: {date_str}\nGET {path} HTTP/1.1"
        signature_sha = base64.b64encode(
            hmac.new(
                self.settings.iflytek_api_secret.encode("utf-8"),
                signature_origin.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()
        ).decode("utf-8")
        authorization_origin = (
            f'api_key="{self.settings.iflytek_api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature="{signature_sha}"'
        )
        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")
        query = urlencode({"authorization": authorization, "date": date_str, "host": host})
        return f"wss://{host}{path}?{query}"

    @staticmethod
    def _pcm_from_wav(audio_bytes: bytes) -> bytes:
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wav_reader:
                channels = wav_reader.getnchannels()
                sample_width = wav_reader.getsampwidth()
                frame_rate = wav_reader.getframerate()
                if channels != 1:
                    raise VoiceServiceError("请提供单声道音频")
                if sample_width != 2:
                    raise VoiceServiceError("请使用16位PCM编码音频")
                if frame_rate != 16000:
                    raise VoiceServiceError("请提供16k采样率音频")
                frames = wav_reader.readframes(wav_reader.getnframes())
                if not frames:
                    raise VoiceServiceError("音频数据为空")
                return frames
        except wave.Error as exc:
            raise VoiceServiceError(f"音频格式解析失败: {exc}") from exc

    async def transcribe_audio(self, audio_bytes: bytes) -> str:
        """上传音频到科大讯飞并返回识别文本"""
        self._ensure_credentials()
        pcm_data = self._pcm_from_wav(audio_bytes)
        ws_url = self._build_ws_url()
        transcript_parts: List[str] = []

        try:
            async with websockets.connect(
                ws_url,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=10,
                max_queue=4,
                extra_headers={"origin": "https://www.xfyun.cn"},
            ) as ws:
                await self._stream_audio(ws, pcm_data)
                async for message in ws:
                    payload = json.loads(message)
                    if payload.get("code", -1) != 0:
                        raise VoiceServiceError(
                            f"科大讯飞返回错误: {payload.get('message')} ({payload.get('code')})"
                        )
                    data = payload.get("data", {})
                    result = data.get("result") or {}
                    text = self._extract_text(result)
                    if text:
                        transcript_parts.append(text)
                    if result.get("ls") or data.get("status") == 2:
                        break
        except VoiceServiceError:
            raise
        except Exception as exc:
            raise VoiceServiceError(f"语音识别请求失败: {exc}") from exc

        transcript = "".join(transcript_parts).strip()
        if not transcript:
            raise VoiceServiceError("未识别到有效语音内容,请重试")
        return transcript

    async def _stream_audio(self, ws, pcm_data: bytes):
        total = len(pcm_data)
        offset = 0
        frame_count = math.ceil(total / self.FRAME_SIZE)

        while offset < total:
            chunk = pcm_data[offset : offset + self.FRAME_SIZE]
            status = 0 if offset == 0 else 1
            payload = {
                "data": {
                    "status": status,
                    "format": "audio/L16;rate=16000",
                    "encoding": "raw",
                    "audio": base64.b64encode(chunk).decode("utf-8"),
                }
            }
            if status == 0:
                payload["common"] = {"app_id": self.settings.iflytek_app_id}
                payload["business"] = {
                    "language": self.settings.iflytek_language,
                    "domain": self.settings.iflytek_domain,
                    "accent": self.settings.iflytek_accent,
                    "ptt": 1,  # 标点
                }
            await ws.send(json.dumps(payload))
            offset += self.FRAME_SIZE
            await asyncio.sleep(self.FRAME_INTERVAL)

        await ws.send(
            json.dumps(
                {
                    "data": {
                        "status": 2,
                        "format": "audio/L16;rate=16000",
                        "encoding": "raw",
                        "audio": "",
                    }
                }
            )
        )

    @staticmethod
    def _extract_text(result: dict) -> str:
        words = []
        for ws_node in result.get("ws", []):
            for cw in ws_node.get("cw", []):
                token = cw.get("w")
                if token:
                    words.append(token)
        return "".join(words)

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
        return data

    def _build_trip_request(self, form: VoiceFormSuggestion) -> TripRequest:
        missing = _format_missing_fields(form, require_travel_days=True)
        if missing:
            raise VoiceServiceError(f"缺少必要字段: {', '.join(missing)}")

        start = form.start_date or ""
        end = form.end_date or ""
        start_iso = _normalize_date(start)
        end_iso = _normalize_date(end)
        if not start_iso or not end_iso:
            raise VoiceServiceError("无法解析语音中的日期,请补充后重试")

        travel_days = form.travel_days or _calc_days(start_iso, end_iso)
        if not travel_days:
            raise VoiceServiceError("无法确定旅行天数,请补充后重试")

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

    def get_missing_fields(self, suggestion: VoiceFormSuggestion, require_travel_days: bool = False) -> List[str]:
        return _format_missing_fields(suggestion, require_travel_days)


_voice_service: Optional[VoiceService] = None


def get_voice_service() -> VoiceService:
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service
