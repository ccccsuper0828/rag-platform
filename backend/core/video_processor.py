import os
import whisper
import ffmpeg
from llama_index.core import Document
from typing import Optional

class VideoProcessor:
    def __init__(self, model_size="base"):
        # 注意：Whisper 很占内存，不要在非视频流程里提前加载。
        # 这里改为“延迟加载”，第一次真正处理视频时才加载模型。
        self.model_size = model_size
        self._model: Optional[object] = None

    def _ensure_model(self):
        if self._model is None:
            # 可选: tiny, base, small, medium, large
            # "base" 是一个很好的平衡点，速度快且精度尚可
            print(f"Loading Whisper model: {self.model_size}...")
            self._model = whisper.load_model(self.model_size)
            print("Whisper model loaded.")

    def process(self, video_path: str) -> list[Document]:
        """
        处理视频文件：
        1. 提取音频
        2. 语音转文字
        3. 返回 LlamaIndex Document 对象列表
        """
        try:
            print(f"Processing video: {video_path}")
            self._ensure_model()
            # 1. 提取音频路径
            audio_path = f"{video_path}.mp3"
            
            # 使用 ffmpeg 提取音频，如果已存在则覆盖
            # -y: overwrite output files
            # -vn: disable video recording
            (
                ffmpeg
                .input(video_path)
                .output(audio_path, format='mp3', acodec='mp3', ar='16k')
                .overwrite_output()
                .run(quiet=True)
            )
            print(f"Audio extracted to: {audio_path}")

            # 2. 转录
            # result 包含 'text' 和 'segments'
            print("Transcribing audio...")
            result = self._model.transcribe(audio_path)  # type: ignore[attr-defined]
            full_text = result['text']
            
            # 我们也可以保留带时间戳的 segments，但这对于纯文本 RAG 稍显复杂
            # 这里 MVP 阶段我们先返回全文，并在 metadata 中标记
            
            doc = Document(
                text=full_text,
                metadata={
                    "file_name": os.path.basename(video_path),
                    "file_type": "video",
                    "source": video_path
                }
            )
            
            # 清理临时音频文件
            if os.path.exists(audio_path):
                os.remove(audio_path)
                
            return [doc], full_text

        except Exception as e:
            print(f"Error processing video {video_path}: {str(e)}")
            return [], ""

