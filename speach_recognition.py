import speech_recognition as sr
from pydub import AudioSegment
from pydub.audio_segment import AudioSegment as aud
import os


class SpeechToText:
    def __init__(self):
        self.recogniser = sr.Recognizer()
        self.path = r"temp\audio.wav"

    def __convert_to_wav(self, path_to_file: str, file_format: str) -> str:
        if file_format == "ogg":
            audio: aud = AudioSegment.from_ogg(path_to_file)
        else:
            audio: aud = AudioSegment.from_file(path_to_file, format=file_format)
        audio.export(out_f=r"temp\audio.wav", format="wav")
        return os.path.abspath(self.path)
    
    def recognize(self, path_to_file: str) -> str | None:
        file_format = path_to_file[path_to_file.rfind(".") + 1:]

        if file_format != "wav":
            if not os.path.exists("temp"):
                os.makedirs("temp")
            self.__convert_to_wav(path_to_file, file_format)
            path_to_file = self.path

        with sr.AudioFile(path_to_file) as source:
            audio = self.recogniser.record(source)
        try:
            text = self.recogniser.recognize_google(audio, language="fa-IR")
            if os.path.exists("temp"):
                os.remove(self.path)
                os.rmdir("temp")
            return text
        except sr.UnknownValueError:
            print("Google Web Speech could not understand the audio.")
        except sr.RequestError as e:
            print(f"Could not request results from Google Web Speech service; {e}")


if __name__ == "__main__":
    stt = SpeechToText()
    text = stt.recognize("path_to_file")
    print(text)