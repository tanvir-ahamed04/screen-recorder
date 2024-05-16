import tkinter as tk
import cv2
import pyautogui
import numpy as np
from threading import Thread
import pyaudio
import wave
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip
from datetime import datetime
import os  

class ScreenRecorder:
    def __init__(self):
        self.SCREEN_SIZE = pyautogui.size()
        self.codec = cv2.VideoWriter_fourcc(*"XVID")
        self.video_output = None
        self.audio_output = None
        self.is_recording = False
        self.audio_thread = None
        self.video_filename = ""
        self.audio_filename = ""
        self.frames = []

    def get_unique_filename(self, extension):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"recorded_{timestamp}.{extension}"

    def start_audio_recording(self):
        self.audio_output = self.audio_filename
        audio = pyaudio.PyAudio()

        stream = audio.open(format=pyaudio.paInt16, channels=2, rate=44100, input=True, frames_per_buffer=1024)

        while self.is_recording:
            data = stream.read(1024)
            self.frames.append(data)
        
        stream.stop_stream()
        stream.close()
        audio.terminate()

        with wave.open(self.audio_output, 'wb') as wf:
            wf.setnchannels(2)
            wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(44100)
            wf.writeframes(b''.join(self.frames))

    def start_recording(self, with_audio):
        self.video_filename = self.get_unique_filename("avi")
        if with_audio:
            self.audio_filename = self.get_unique_filename("wav")
        
        self.video_output = cv2.VideoWriter(self.video_filename, self.codec, 20.0, self.SCREEN_SIZE)
        
        if not self.video_output.isOpened():
            print("Error: Could not open video file for writing.")
            self.video_output = None
            return

        self.is_recording = True
        if with_audio:
            self.audio_thread = Thread(target=self.start_audio_recording)
            self.audio_thread.start()

        while self.is_recording:
            img = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            if self.video_output:  
                self.video_output.write(frame)

        if with_audio:
            self.audio_thread.join()
            self.combine_audio_video(self.video_filename, self.audio_filename)

    def stop_recording(self):
        self.is_recording = False
        if self.video_output:
            self.video_output.release()
            self.video_output = None
        cv2.destroyAllWindows()

    def combine_audio_video(self, video_filename, audio_filename):
        try:
            video_clip = VideoFileClip(video_filename)
            audio_clip = AudioFileClip(audio_filename)
            final_clip = CompositeVideoClip([video_clip.set_audio(audio_clip)])
            final_output = video_filename.replace(".avi", ".mp4")
            final_clip.write_videofile(final_output, codec="libx264")
            
            os.remove(video_filename)
            os.remove(audio_filename)
        except Exception as e:
            print(f"Error combining video and audio: {e}")

def start_recording_thread(recorder, with_audio):
    recording_thread = Thread(target=recorder.start_recording, args=(with_audio,))
    recording_thread.start()
    return recording_thread

def main():
    recorder = ScreenRecorder()
    
    root = tk.Tk()
    root.title("Screen Recorder")

    
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = screen_width // 2
    window_height = screen_height // 2

    root.geometry(f"{window_width}x{window_height}")

    start_audio_button = tk.Button(root, text="Start Video with Voice", command=lambda: start_recording_thread(recorder, True), bg="green")
    start_audio_button.pack(pady=10)

    start_no_audio_button = tk.Button(root, text="Start Video without Voice", command=lambda: start_recording_thread(recorder, False), bg="blue")
    start_no_audio_button.pack(pady=10)

    stop_button = tk.Button(root, text="Stop the Video", command=recorder.stop_recording, bg="red")
    stop_button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
