#!/usr/bin/env python3

import sounddevice as sd
import numpy as np
import threading
from pynput import keyboard
import wavio
import time
import subprocess

# Global variables to manage recording state and the recording thread
is_recording = False
recording_thread = None
frames = []  # A list to hold recorded frames


def transcribe_audio(audio_path='recording.wav'):
    whisper_path = '/usr/local/bin/whisper'  # Explicitly set the path to the Whisper executable
    output_dir = '.'  # Specify the current directory as the output directory
    # Specify the language as English and request the output in text format
    result = subprocess.run(
        [whisper_path, audio_path, '--model', 'small.en', '--language', 'en', '--output_dir', output_dir,
         '--output_format', 'txt'], capture_output=True, text=True)

    # Calculate and print the time taken for transcription
    end_time = time.time()

    # Print any error messages
    # if result.stderr.strip():
    #     print("Error during transcription:", result.stderr)

    # Attempt to read and print the transcription from the .txt file
    output_text_path = audio_path.replace('.wav', '.txt')  # Assuming the .txt file is named similarly to the .wav file
    try:
        with open(output_text_path, 'r') as file:
            transcription = file.read()
            print("Transcription result:\n", transcription)
    except FileNotFoundError:
        print("Transcription text file not found.")


def print_recording_status():
    while is_recording:
        print("Recording...")
        time.sleep(5)  # Wait for 5 seconds before printing again

# Correct the callback function
def callback(indata, frame_count, time_info, status):
    if is_recording:
        frames.append(indata.copy())  # Correctly append the numpy array to the frames list

def record_audio():
    global is_recording, recording_thread, frames
    fs = 44100  # Sample rate

    print("Start Recording...")
    frames.clear()  # Ensure frames list is empty before starting a new recording
    with sd.InputStream(callback=callback, samplerate=fs, channels=2):
        recording_thread = threading.Thread(target=print_recording_status)
        recording_thread.start()

        # Wait for the recording to stop
        while is_recording:
            time.sleep(1)

    recording_thread.join()  # Ensure the status thread has finished
    recording = np.concatenate(frames, axis=0) if frames else np.array([])  # Safely handle concatenation
    print("Recording stopped.")
    wavio.write('recording.wav', recording, fs, sampwidth=2)  # Save as WAV file

    # Start timing the transcription process
    start_time = time.time()
    transcribe_audio('recording.wav')
    # Calculate and print the time taken for transcription after transcription result is printed
    end_time = time.time()
    print("Total time from recording stop to transcription print:", end_time - start_time, "seconds")

def on_press(key):
    global is_recording

    try:
        if key == keyboard.Key.alt:
            if not is_recording:
                # Start recording
                is_recording = True
                threading.Thread(target=record_audio).start()
            else:
                # Stop recording, this will automatically lead to transcription
                is_recording = False
    except AttributeError:
        pass

# Setting up listener for keyboard
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
