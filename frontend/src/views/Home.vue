<template>
  <div class="home-container">
    <div class="top-grid">
      <div class="page-header">
        <div class="icon-wrapper">
          <span class="icon">✈️</span>
        </div>
        <div>
          <h1 class="page-title">智能旅行助手</h1>
          <p class="page-subtitle">基于AI的个性化旅行规划,让每一次出行都完美无忧</p>
          <ul class="highlights">
            <li>⚡ 语音秒填资料</li>
            <li>🧭 AI 智能行程排布</li>
            <li>📍 高德实时出行信息</li>
          </ul>
        </div>
      </div>

      <div class="voice-panel">
        <div class="section-header">
          <span class="section-icon">🎙️</span>
          <span class="section-title">语音快速输入</span>
        </div>

        <p class="voice-hint">
          {{ voiceState.statusText }}
        </p>

        <div class="voice-actions">
          <a-button
            type="primary"
            size="large"
            :danger="voiceState.recording"
            :loading="voiceState.recording"
            @click="toggleVoiceRecording"
          >
            <template #icon>
              <span v-if="voiceState.recording">⏹</span>
              <span v-else>🎙️</span>
            </template>
            {{ voiceState.recording ? '停止录音' : '开始语音输入' }}
          </a-button>
          <a-button
            size="large"
            :disabled="!voiceState.suggestion || voiceState.uploading"
            @click="applyVoiceSuggestion"
          >
            <template #icon>🪄</template>
            使用语音填充表单
          </a-button>
          <a-button
            size="large"
            type="dashed"
            :disabled="!canGenerateFromVoice || voiceState.planning"
            @click="generatePlanFromVoice"
          >
            <template #icon>⚡</template>
            语音直接生成行程
          </a-button>
        </div>

        <a-alert
          v-if="!voiceState.supported"
          type="warning"
          message="浏览器暂不支持录音,建议使用最新版 Chrome/Edge"
          show-icon
          class="voice-alert"
        />
        <a-alert
          v-else-if="voiceState.error"
          type="error"
          :message="voiceState.error"
          show-icon
          closable
          class="voice-alert"
          @close="voiceState.error = ''"
        />

        <div class="voice-status" v-if="voiceState.uploading || voiceState.planning">
          <a-spin
            :tip="voiceState.uploading ? '语音识别中...' : 'AI 正在根据语音生成行程...'"
          />
        </div>

        <div v-if="voiceState.transcript" class="voice-result-card">
          <h4>识别文本</h4>
          <p class="voice-transcript">{{ voiceState.transcript }}</p>

          <div class="missing-fields" v-if="voiceState.missing.length">
            <span>仍需补充:</span>
            <a-tag
              v-for="field in voiceState.missing"
              :key="field"
              color="volcano"
            >
              {{ field }}
            </a-tag>
          </div>

          <div class="voice-suggestion-grid" v-if="voiceState.suggestion">
            <div class="voice-suggestion-item">
              <span class="label">目的地</span>
              <span class="value">{{ voiceState.suggestion?.city || '未识别' }}</span>
            </div>
            <div class="voice-suggestion-item">
              <span class="label">开始日期</span>
              <span class="value">{{ voiceState.suggestion?.start_date || '-' }}</span>
            </div>
            <div class="voice-suggestion-item">
              <span class="label">结束日期</span>
              <span class="value">{{ voiceState.suggestion?.end_date || '-' }}</span>
            </div>
            <div class="voice-suggestion-item">
              <span class="label">旅行天数</span>
              <span class="value">{{ voiceState.suggestion?.travel_days || '-' }}</span>
            </div>
            <div class="voice-suggestion-item">
              <span class="label">交通方式</span>
              <span class="value">{{ voiceState.suggestion?.transportation || '默认' }}</span>
            </div>
            <div class="voice-suggestion-item">
              <span class="label">住宿偏好</span>
              <span class="value">{{ voiceState.suggestion?.accommodation || '默认' }}</span>
            </div>
          </div>

          <div
            class="voice-preferences"
            v-if="voiceState.suggestion?.preferences && voiceState.suggestion.preferences.length"
          >
            <span class="label">偏好:</span>
            <div class="preference-tags-inline">
              <a-tag
                v-for="tag in voiceState.suggestion.preferences"
                :key="tag"
                color="geekblue"
              >
                {{ tag }}
              </a-tag>
            </div>
          </div>
        </div>
      </div>
    </div>

    <a-card class="form-card" :bordered="false">
      <a-form
        :model="formData"
        layout="vertical"
        @finish="handleSubmit"
      >
        <div class="form-body">
          <!-- 第一步:目的地和日期 -->
          <div class="form-section form-section--half">
            <div class="section-header">
            <span class="section-icon">📍</span>
            <span class="section-title">目的地与日期</span>
          </div>

          <a-row :gutter="24">
            <a-col :span="8">
              <a-form-item name="city" :rules="[{ required: true, message: '请输入目的地城市' }]">
                <template #label>
                  <span class="form-label">目的地城市</span>
                </template>
                <a-input
                  v-model:value="formData.city"
                  placeholder="例如: 北京"
                  size="large"
                  class="custom-input"
                >
                  <template #prefix>
                    <span style="color: #1890ff;">🏙️</span>
                  </template>
                </a-input>
              </a-form-item>
            </a-col>
            <a-col :span="6">
              <a-form-item name="start_date" :rules="[{ required: true, message: '请选择开始日期' }]">
                <template #label>
                  <span class="form-label">开始日期</span>
                </template>
                <a-date-picker
                  v-model:value="formData.start_date"
                  style="width: 100%"
                  size="large"
                  class="custom-input"
                  placeholder="选择日期"
                />
              </a-form-item>
            </a-col>
            <a-col :span="6">
              <a-form-item name="end_date" :rules="[{ required: true, message: '请选择结束日期' }]">
                <template #label>
                  <span class="form-label">结束日期</span>
                </template>
                <a-date-picker
                  v-model:value="formData.end_date"
                  style="width: 100%"
                  size="large"
                  class="custom-input"
                  placeholder="选择日期"
                />
              </a-form-item>
            </a-col>
            <a-col :span="4">
              <a-form-item>
                <template #label>
                  <span class="form-label">旅行天数</span>
                </template>
                <div class="days-display-compact">
                  <span class="days-value">{{ formData.travel_days }}</span>
                  <span class="days-unit">天</span>
                </div>
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <!-- 第二步:偏好设置 -->
        <div class="form-section form-section--half">
          <div class="section-header">
            <span class="section-icon">⚙️</span>
            <span class="section-title">偏好设置</span>
          </div>

          <a-row :gutter="24">
            <a-col :span="8">
              <a-form-item name="transportation">
                <template #label>
                  <span class="form-label">交通方式</span>
                </template>
                <a-select v-model:value="formData.transportation" size="large" class="custom-select">
                  <a-select-option value="公共交通">🚇 公共交通</a-select-option>
                  <a-select-option value="自驾">🚗 自驾</a-select-option>
                  <a-select-option value="步行">🚶 步行</a-select-option>
                  <a-select-option value="混合">🔀 混合</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item name="accommodation">
                <template #label>
                  <span class="form-label">住宿偏好</span>
                </template>
                <a-select v-model:value="formData.accommodation" size="large" class="custom-select">
                  <a-select-option value="经济型酒店">💰 经济型酒店</a-select-option>
                  <a-select-option value="舒适型酒店">🏨 舒适型酒店</a-select-option>
                  <a-select-option value="豪华酒店">⭐ 豪华酒店</a-select-option>
                  <a-select-option value="民宿">🏡 民宿</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item name="preferences">
                <template #label>
                  <span class="form-label">旅行偏好</span>
                </template>
                <div class="preference-tags">
                  <a-checkbox-group v-model:value="formData.preferences" class="custom-checkbox-group">
                    <a-checkbox value="历史文化" class="preference-tag">🏛️ 历史文化</a-checkbox>
                    <a-checkbox value="自然风光" class="preference-tag">🏞️ 自然风光</a-checkbox>
                    <a-checkbox value="美食" class="preference-tag">🍜 美食</a-checkbox>
                    <a-checkbox value="购物" class="preference-tag">🛍️ 购物</a-checkbox>
                    <a-checkbox value="艺术" class="preference-tag">🎨 艺术</a-checkbox>
                    <a-checkbox value="休闲" class="preference-tag">☕ 休闲</a-checkbox>
                  </a-checkbox-group>
                </div>
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <!-- 第三步:额外要求 -->
        <div class="form-section form-section--full">
          <div class="section-header">
            <span class="section-icon">💬</span>
            <span class="section-title">额外要求</span>
          </div>

          <a-form-item name="free_text_input">
            <a-textarea
              v-model:value="formData.free_text_input"
              placeholder="请输入您的额外要求,例如:想去看升旗、需要无障碍设施、对海鲜过敏等..."
              :rows="3"
              size="large"
              class="custom-textarea"
            />
          </a-form-item>
        </div>

        </div>

        <!-- 提交按钮 -->
        <a-form-item class="submit-wrapper">
          <a-button
            type="primary"
            html-type="submit"
            :loading="loading"
            size="large"
            block
            class="submit-button"
          >
            <template v-if="!loading">
              <span class="button-icon">🚀</span>
              <span>开始规划我的旅行</span>
            </template>
            <template v-else>
              <span>正在生成中...</span>
            </template>
          </a-button>
        </a-form-item>

        <!-- 加载进度条 -->
        <a-form-item v-if="loading" class="progress-wrapper">
          <div class="loading-container">
            <a-progress
              :percent="loadingProgress"
              status="active"
              :stroke-color="{
                '0%': '#667eea',
                '100%': '#764ba2',
              }"
              :stroke-width="10"
            />
            <p class="loading-status">
              {{ loadingStatus }}
            </p>
          </div>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import dayjs, { type Dayjs } from 'dayjs'
import { generateTripPlan, planTripByVoice, transcribeVoiceInput } from '@/services/api'
import { VoiceRecorder } from '@/services/voiceRecorder'
import type { TripFormData, VoiceFormSuggestion } from '@/types'

const router = useRouter()
const loading = ref(false)
const loadingProgress = ref(0)
const loadingStatus = ref('')

const defaultVoiceHint =
  '点击开始语音输入,描述目的地、日期、预算、同行人数与偏好,系统会自动填表并生成行程'

const voiceRecorder = ref<VoiceRecorder | null>(null)
const lastVoiceBlob = ref<Blob | null>(null)
const voiceState = reactive({
  supported: typeof window !== 'undefined' && !!navigator?.mediaDevices,
  recording: false,
  uploading: false,
  planning: false,
  transcript: '',
  statusText: defaultVoiceHint,
  error: '',
  missing: [] as string[],
  suggestion: null as VoiceFormSuggestion | null
})

const canGenerateFromVoice = computed(
  () => !!lastVoiceBlob.value && !voiceState.recording && !voiceState.uploading && voiceState.supported
)

type TripFormState = Omit<TripFormData, 'start_date' | 'end_date'> & {
  start_date: Dayjs | null
  end_date: Dayjs | null
}

const formData = reactive<TripFormState>({
  city: '',
  start_date: null,
  end_date: null,
  travel_days: 1,
  transportation: '公共交通',
  accommodation: '经济型酒店',
  preferences: [],
  free_text_input: ''
})

// 监听日期变化,自动计算旅行天数
watch([() => formData.start_date, () => formData.end_date], ([start, end]) => {
  if (start && end) {
    const days = end.diff(start, 'day') + 1
    if (days > 0 && days <= 30) {
      formData.travel_days = days
    } else if (days > 30) {
      message.warning('旅行天数不能超过30天')
      formData.end_date = null
    } else {
      message.warning('结束日期不能早于开始日期')
      formData.end_date = null
    }
  }
})

const toggleVoiceRecording = async () => {
  if (!voiceState.supported) {
    message.error('当前浏览器不支持语音录制,请改用最新版 Chrome/Edge')
    return
  }
  if (voiceState.recording) {
    await finishVoiceRecording()
  } else {
    await startVoiceRecording()
  }
}

const startVoiceRecording = async () => {
  try {
    voiceState.error = ''
    voiceState.statusText = '正在初始化麦克风...'
    voiceRecorder.value = new VoiceRecorder()
    await voiceRecorder.value.start()
    voiceState.recording = true
    voiceState.statusText = '🎙️ 正在录音,请描述目的地、日期、预算与偏好'
  } catch (error: any) {
    voiceState.error = error?.message || '无法访问麦克风,请检查权限'
    voiceState.statusText = defaultVoiceHint
    voiceRecorder.value?.dispose()
    voiceRecorder.value = null
    message.error(voiceState.error)
  }
}

const finishVoiceRecording = async () => {
  if (!voiceRecorder.value) return
  try {
    voiceState.statusText = '正在封装音频...'
    const blob = await voiceRecorder.value.stop()
    lastVoiceBlob.value = blob
    await analyzeVoiceBlob(blob)
  } catch (error: any) {
    voiceState.error = error?.message || '处理录音失败,请重试'
    message.error(voiceState.error)
  } finally {
    voiceState.recording = false
    voiceRecorder.value?.dispose()
    voiceRecorder.value = null
  }
}

const analyzeVoiceBlob = async (blob: Blob) => {
  voiceState.uploading = true
  voiceState.statusText = '⏳ 正在上传并识别语音...'
  try {
    const result = await transcribeVoiceInput(blob)
    voiceState.transcript = result.transcript || ''
    voiceState.suggestion = result.form
    voiceState.missing = result.missing_fields || []
    voiceState.statusText =
      voiceState.missing.length > 0
        ? '语音识别成功,请补充缺失字段后提交'
        : '语音识别成功,可一键填充表单'
    message.success(result.message || '语音解析成功')
  } catch (error: any) {
    voiceState.error = error?.message || '语音解析失败,请稍后重试'
    voiceState.statusText = defaultVoiceHint
    message.error(voiceState.error)
  } finally {
    voiceState.uploading = false
  }
}

const applyVoiceSuggestion = () => {
  if (!voiceState.suggestion) {
    message.warning('请先完成语音识别')
    return
  }
  const suggestion = voiceState.suggestion
  if (suggestion.city) formData.city = suggestion.city
  if (suggestion.start_date) formData.start_date = dayjs(suggestion.start_date)
  if (suggestion.end_date) formData.end_date = dayjs(suggestion.end_date)
  if (suggestion.travel_days) formData.travel_days = suggestion.travel_days
  if (suggestion.transportation) formData.transportation = suggestion.transportation
  if (suggestion.accommodation) formData.accommodation = suggestion.accommodation
  if (suggestion.preferences && suggestion.preferences.length > 0) {
    formData.preferences = [...suggestion.preferences]
  }
  if (suggestion.free_text_input) {
    formData.free_text_input = suggestion.free_text_input
  }
  message.success('已根据语音结果填充表单,可继续微调后生成行程')
}

const generatePlanFromVoice = async () => {
  if (!lastVoiceBlob.value) {
    message.warning('请先完成语音录制并识别')
    return
  }
  voiceState.planning = true
  voiceState.error = ''
  voiceState.statusText = '🤖 AI 正在根据语音自动生成行程...'
  try {
    const result = await planTripByVoice(lastVoiceBlob.value)
    if (result.success && result.data) {
      voiceState.transcript = result.transcript || voiceState.transcript
      voiceState.suggestion = result.form
      voiceState.missing = result.missing_fields || []
      sessionStorage.setItem('tripPlan', JSON.stringify(result.data))
      message.success('语音行程生成成功!')
      router.push('/result')
    } else {
      throw new Error(result.message || '语音行程生成失败')
    }
  } catch (error: any) {
    voiceState.error = error?.message || '语音行程生成失败,请补充信息后重试'
    message.error(voiceState.error)
  } finally {
    voiceState.planning = false
    voiceState.statusText = defaultVoiceHint
  }
}

const handleSubmit = async () => {
  const startDate = formData.start_date
  const endDate = formData.end_date
  if (!startDate || !endDate) {
    message.error('请选择完整的开始与结束日期')
    return
  }

  loading.value = true
  loadingProgress.value = 0
  loadingStatus.value = '正在初始化...'

  const progressInterval = setInterval(() => {
    if (loadingProgress.value < 90) {
      loadingProgress.value += 10
      if (loadingProgress.value <= 30) {
        loadingStatus.value = '🔍 正在搜索景点...'
      } else if (loadingProgress.value <= 50) {
        loadingStatus.value = '🌤️ 正在查询天气...'
      } else if (loadingProgress.value <= 70) {
        loadingStatus.value = '🏨 正在推荐酒店...'
      } else {
        loadingStatus.value = '📋 正在生成行程计划...'
      }
    }
  }, 500)

  try {
    const requestData: TripFormData = {
      city: formData.city,
      start_date: startDate.format('YYYY-MM-DD'),
      end_date: endDate.format('YYYY-MM-DD'),
      travel_days: formData.travel_days,
      transportation: formData.transportation,
      accommodation: formData.accommodation,
      preferences: formData.preferences,
      free_text_input: formData.free_text_input
    }

    const response = await generateTripPlan(requestData)

    clearInterval(progressInterval)
    loadingProgress.value = 100
    loadingStatus.value = '✅ 完成!'

    if (response.success && response.data) {
      sessionStorage.setItem('tripPlan', JSON.stringify(response.data))
      message.success('旅行计划生成成功!')
      setTimeout(() => {
        router.push('/result')
      }, 500)
    } else {
      message.error(response.message || '生成失败,请稍后重试')
    }
  } catch (error: any) {
    clearInterval(progressInterval)
    message.error(error.message || '生成旅行计划失败,请稍后重试')
  } finally {
    setTimeout(() => {
      loading.value = false
      loadingProgress.value = 0
      loadingStatus.value = ''
    }, 1000)
  }
}

onBeforeUnmount(() => {
  voiceRecorder.value?.dispose()
})
</script>


<style scoped>
.home-container {
  min-height: calc(100vh - 140px);
  padding: 16px 20px 32px;
  background: #f4f6fb;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.top-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.page-header {
  background: #ffffff;
  border-radius: 20px;
  padding: 20px 24px;
  display: flex;
  gap: 16px;
  align-items: center;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.1);
}

.icon-wrapper {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon {
  font-size: 32px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: #1e1e2f;
  margin: 0;
}

.page-subtitle {
  font-size: 15px;
  color: #5f6c7b;
  margin: 4px 0 0;
}

.highlights {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  margin: 12px 0 0;
  padding: 0;
  list-style: none;
  color: #475569;
  font-size: 13px;
}

.voice-panel {
  background: #ffffff;
  border-radius: 20px;
  padding: 20px 24px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.1);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.voice-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.voice-alert,
.voice-status {
  margin-top: 8px;
}

.voice-result-card {
  border: 1px dashed #d4d8f0;
  border-radius: 14px;
  padding: 12px;
  background: #f8f9ff;
}

.form-card {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  border-radius: 22px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
  background: #ffffff;
}

.form-body {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.form-section {
  flex: 1 1 320px;
  padding: 16px;
  background: #fdfdff;
  border-radius: 16px;
  border: 1px solid #e4e6ef;
}

.form-section--half {
  flex: 1 1 calc(50% - 8px);
  min-width: 340px;
}

.form-section--full {
  flex: 1 1 100%;
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 14px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e6ef;
}

.section-icon {
  font-size: 20px;
  margin-right: 10px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #2d2f43;
}

.form-label {
  font-size: 14px;
  font-weight: 600;
  color: #4a5568;
}

.custom-input :deep(.ant-input),
.custom-input :deep(.ant-picker) {
  border-radius: 10px;
  border: 1px solid #dfe3f0;
}

.custom-input :deep(.ant-input:hover),
.custom-input :deep(.ant-picker:hover) {
  border-color: #7f8ff5;
}

.custom-select :deep(.ant-select-selector) {
  border-radius: 10px !important;
  border: 1px solid #dfe3f0 !important;
}

.days-display-compact {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  color: #fff;
}

.preference-tags,
.custom-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preference-tag :deep(.ant-checkbox-wrapper) {
  margin: 0 !important;
  padding: 6px 14px;
  border: 1px solid #dfe3f0;
  border-radius: 18px;
  background: #fff;
}

.custom-textarea :deep(.ant-input) {
  border-radius: 12px;
  border: 1px solid #dfe3f0;
}

.submit-wrapper {
  margin-top: 8px;
}

.submit-button {
  height: 48px;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #6366f1 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 10px 20px rgba(99, 102, 241, 0.25);
}

.progress-wrapper {
  margin: 0;
}

.loading-container {
  background: #fdfdff;
  border-radius: 12px;
  border: 1px dashed #c7cffc;
  padding: 16px;
}

.loading-status {
  margin-top: 8px;
  color: #4c51bf;
  font-size: 14px;
}

@media (max-width: 1024px) {
  .form-section--half {
    flex: 1 1 100%;
  }
  .page-header,
  .voice-panel {
    padding: 16px;
  }
}
</style>
