import axios from 'axios'
import type {
  TripFormData,
  TripPlanResponse,
  VoicePlanResponse,
  VoiceTranscriptionResponse
} from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2分钟超时
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    console.log('发送请求:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    console.log('收到响应:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('响应错误:', error.response?.status, error.message)
    return Promise.reject(error)
  }
)

/**
 * 生成旅行计划
 */
export async function generateTripPlan(formData: TripFormData): Promise<TripPlanResponse> {
  try {
    const response = await apiClient.post<TripPlanResponse>('/api/trip/plan', formData)
    return response.data
  } catch (error: any) {
    console.error('生成旅行计划失败:', error)
    throw new Error(error.response?.data?.detail || error.message || '生成旅行计划失败')
  }
}

/**
 * 健康检查
 */
export async function healthCheck(): Promise<any> {
  try {
    const response = await apiClient.get('/health')
    return response.data
  } catch (error: any) {
    console.error('健康检查失败:', error)
    throw new Error(error.message || '健康检查失败')
  }
}

/**
 * 上传语音并获取解析结果
 */
export async function transcribeVoiceInput(audioBlob: Blob): Promise<VoiceTranscriptionResponse> {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'voice-input.wav')
  try {
    const response = await apiClient.post<VoiceTranscriptionResponse>('/api/voice/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  } catch (error: any) {
    console.error('语音解析失败:', error)
    throw new Error(error.response?.data?.detail || error.message || '语音解析失败')
  }
}

/**
 * 语音直接生成旅行计划
 */
export async function planTripByVoice(audioBlob: Blob): Promise<VoicePlanResponse> {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'voice-plan.wav')
  try {
    const response = await apiClient.post<VoicePlanResponse>('/api/voice/plan', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  } catch (error: any) {
    console.error('语音生成旅行计划失败:', error)
    throw new Error(error.response?.data?.detail || error.message || '语音生成旅行计划失败')
  }
}

export default apiClient

