"""语音输入相关API"""

from fastapi import APIRouter, File, HTTPException, UploadFile

from ...models.schemas import VoicePlanResponse, VoiceTranscriptionResponse
from ...services.voice_service import VoiceServiceError, get_voice_service

router = APIRouter(prefix="/voice", tags=["语音输入"])


@router.post(
    "/transcribe",
    response_model=VoiceTranscriptionResponse,
    summary="上传语音生成表单建议",
)
async def transcribe_voice(audio: UploadFile = File(..., description="16k PCM WAV音频")):
    if not audio:
        raise HTTPException(status_code=400, detail="请上传音频文件")

    try:
        audio_bytes = await audio.read()
        voice_service = get_voice_service()
        transcript = await voice_service.transcribe_audio(audio_bytes)
        suggestion = await voice_service.parse_form_suggestion(transcript)
        missing = voice_service.get_missing_fields(suggestion, require_travel_days=False)

        return VoiceTranscriptionResponse(
            success=True,
            message="语音解析成功",
            transcript=transcript,
            form=suggestion,
            missing_fields=missing,
        )
    except VoiceServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/plan",
    response_model=VoicePlanResponse,
    summary="语音直接生成旅行计划",
)
async def plan_by_voice(audio: UploadFile = File(..., description="16k PCM WAV音频")):
    if not audio:
        raise HTTPException(status_code=400, detail="请上传音频文件")

    try:
        audio_bytes = await audio.read()
        voice_service = get_voice_service()
        transcript, suggestion, plan = await voice_service.plan_trip_from_voice(audio_bytes)
        return VoicePlanResponse(
            success=True,
            message="语音规划成功",
            transcript=transcript,
            form=suggestion,
            missing_fields=[],
            data=plan,
        )
    except VoiceServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
