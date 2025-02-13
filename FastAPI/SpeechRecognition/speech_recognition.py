import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydub import AudioSegment
from pydub.audio_segment import AudioSegment as aud
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level to INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Define the format of the logs
)

logger = logging.getLogger(__name__)

class SpeechToText:
    def __init__(self):
        self.recogniser = sr.Recognizer()

    def __segment(self, path_to_file: str, target_parts:int = 4, silence_thresh: int = -100, min_silence_len: int = 600) -> list[str]:
        audio = AudioSegment.from_file(path_to_file)
        chunks = split_on_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)

        total_duration_sec = len(audio) / 1000.0
        while total_duration_sec / target_parts < 15 and total_duration_sec > 15:
            target_parts -= 1

        segments = []
        chunk_length = len(chunks) // target_parts
        for i in range(target_parts):
            start_idx = i * chunk_length
            if i < target_parts - 1:
                end_idx = (i + 1) * chunk_length
            else:
                end_idx = len(chunks)
            combined = sum(chunks[start_idx:end_idx])
            segments.append(combined)
        
        audio_files = []
        for i, segment in enumerate(segments):
            if segment:
                segment.export(f"temp\segment_{i+1}.wav", format="wav")
                audio_files.append(f"temp\segment_{i+1}.wav")
        
        return audio_files

    def recognize(self, path_to_file: str, remove_file: bool = False) -> tuple[str, str] | str | None:
        with sr.AudioFile(path_to_file) as source:
            audio = self.recogniser.record(source)
        try:
            text = self.recogniser.recognize_google(audio, language="fa-IR")
            if not remove_file:
                return path_to_file, text
            else:
                os.remove(path_to_file)
                return text
        except sr.UnknownValueError:
            print("Google Web Speech could not understand the audio.")
        except sr.RequestError as e:
            print(f"Could not request results from Google Web Speech service; {e}")
        return None
    
    def __convert_to_wav(self, path_to_file: str, file_format: str) -> str:
        path_wav = '/'.join(path_to_file.split('/')[:-1]) + '/audio.wav'
        if file_format == "ogg":
            audio: aud = AudioSegment.from_ogg(path_to_file)
        else:
            audio: aud = AudioSegment.from_file(path_to_file, format=file_format)
        audio.export(out_f=path_wav, format="wav")
        return path_wav

    def recognizer(self, path_to_file: str, remove_file: bool = False) -> str | None:
        file_format = path_to_file[path_to_file.rfind(".") + 1:]

        if file_format != "wav":
            path_to_wav = self.__convert_to_wav(path_to_file, file_format)

        with sr.AudioFile(path_to_wav) as source:
            audio = self.recogniser.record(source)
        try:
            text = self.recogniser.recognize_google(audio, language="fa-IR")
            if remove_file:
                os.remove(path_to_wav)
                os.remove(path_to_file)
            return text
        except sr.UnknownValueError:
            print("Google Web Speech could not understand the audio.")
        except sr.RequestError as e:
            print(f"Could not request results from Google Web Speech service; {e}")

    def parallel_recognize(self, path_to_file: str, remove_file: bool = False) -> str | None:
        if not os.path.exists("temp"):
            os.makedirs("temp")

        audio_files = self.__segment(path_to_file)
        if not audio_files:
            return None
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.recognize, audio_file) for audio_file in audio_files]
            results = []
            for future in as_completed(futures):
                file_name, result = future.result()
                results.append([file_name, result])
            results.sort(key=lambda x: int(x[0].split("_")[-1].split(".")[0]))
            text = "".join([result + " " for _, result in results])

        for audio_file in audio_files:
            os.remove(audio_file)
        if remove_file:
            os.remove(path_to_file)
        return text


if __name__ == "__main__":
    import time
    t = time.time()
    audio_file = r"path\to\audio\file"
    stt = SpeechToText()
    text = stt.parallel_recognize(audio_file, remove_file=False)
    print(text)
    print("Time taken:", time.time() - t)
