export class VoiceRecorder {
  private audioContext: AudioContext | null = null
  private mediaStream: MediaStream | null = null
  private sourceNode: MediaStreamAudioSourceNode | null = null
  private processorNode: ScriptProcessorNode | null = null
  private buffers: Float32Array[] = []
  private readonly targetSampleRate = 16000

  async start() {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error('当前浏览器不支持麦克风录音')
    }

    this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    this.audioContext = new AudioContext()
    this.sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream)
    this.processorNode = this.audioContext.createScriptProcessor(4096, 1, 1)

    this.buffers = []
    this.processorNode.onaudioprocess = (event) => {
      const channelData = event.inputBuffer.getChannelData(0)
      this.buffers.push(new Float32Array(channelData))
    }

    this.sourceNode.connect(this.processorNode)
    this.processorNode.connect(this.audioContext.destination)
  }

  async stop(): Promise<Blob> {
    if (!this.processorNode || !this.audioContext) {
      throw new Error('录音尚未开始')
    }

    this.processorNode.disconnect()
    this.sourceNode?.disconnect()
    this.processorNode.onaudioprocess = null
    this.mediaStream?.getTracks().forEach((track) => track.stop())
    await this.audioContext.close()

    const audioContextSampleRate = this.audioContext.sampleRate || 44100
    const merged = this.mergeBuffers(this.buffers)
    if (!merged.length) {
      throw new Error('未捕获到有效音频')
    }
    const resampled = this.downsampleBuffer(merged, audioContextSampleRate, this.targetSampleRate)
    const wavBuffer = this.encodeWav(resampled, this.targetSampleRate)
    this.cleanup()
    return new Blob([wavBuffer], { type: 'audio/wav' })
  }

  dispose() {
    if (this.processorNode) {
      this.processorNode.disconnect()
      this.processorNode.onaudioprocess = null
    }
    if (this.sourceNode) {
      this.sourceNode.disconnect()
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop())
    }
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close()
    }
    this.cleanup()
  }

  private cleanup() {
    this.audioContext = null
    this.mediaStream = null
    this.sourceNode = null
    this.processorNode = null
    this.buffers = []
  }

  private mergeBuffers(buffers: Float32Array[]): Float32Array {
    const length = buffers.reduce((acc, cur) => acc + cur.length, 0)
    const result = new Float32Array(length)
    let offset = 0
    for (const buffer of buffers) {
      result.set(buffer, offset)
      offset += buffer.length
    }
    return result
  }

  private downsampleBuffer(buffer: Float32Array, sampleRate: number, outSampleRate: number): Float32Array {
    if (outSampleRate === sampleRate) {
      return buffer
    }
    const ratio = sampleRate / outSampleRate
    const newLength = Math.round(buffer.length / ratio)
    const result = new Float32Array(newLength)
    let offsetResult = 0
    let offsetBuffer = 0

    while (offsetResult < result.length) {
      const nextOffsetBuffer = Math.round((offsetResult + 1) * ratio)
      let accum = 0
      let count = 0
      for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
        accum += buffer[i]
        count++
      }
      result[offsetResult] = count ? accum / count : 0
      offsetResult++
      offsetBuffer = nextOffsetBuffer
    }

    return result
  }

  private encodeWav(samples: Float32Array, sampleRate: number): ArrayBuffer {
    const buffer = new ArrayBuffer(44 + samples.length * 2)
    const view = new DataView(buffer)

    const writeString = (offset: number, str: string) => {
      for (let i = 0; i < str.length; i++) {
        view.setUint8(offset + i, str.charCodeAt(i))
      }
    }

    writeString(0, 'RIFF')
    view.setUint32(4, 36 + samples.length * 2, true)
    writeString(8, 'WAVE')
    writeString(12, 'fmt ')
    view.setUint32(16, 16, true)
    view.setUint16(20, 1, true) // PCM
    view.setUint16(22, 1, true) // 单声道
    view.setUint32(24, sampleRate, true)
    view.setUint32(28, sampleRate * 2, true)
    view.setUint16(32, 2, true)
    view.setUint16(34, 16, true)
    writeString(36, 'data')
    view.setUint32(40, samples.length * 2, true)

    let offset = 44
    for (let i = 0; i < samples.length; i++, offset += 2) {
      let s = Math.max(-1, Math.min(1, samples[i]))
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true)
    }

    return buffer
  }
}
