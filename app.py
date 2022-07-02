import pyaudio
import settings
import wave
import tkinter as tk
from tkinter import messagebox
import json
from threading import Thread
from queue import Queue
from vosk import Model, KaldiRecognizer
from tkinter import PhotoImage
import functools


def catch_exception(f):
    @functools.wraps(f)
    def func(*args, **kwargs):
        '''Exception handler. In case of an error receives the name of the function which caused
        the error and displays it. Quits the program afterwards. Output is to the status label of the GUI
        or Tkinter messagebox, in case GUI windows has not been created yet.
        '''    
        try:
            return f(*args, **kwargs)
        except Exception as e:
            if action_label !=  None:
                action_label['text'] = 'Caught an exception in ' + f.__name__
            else:
                tk.messagebox.showerror('Exception', 'Exception in ' + f.__name__)
                quit()
    return func

@catch_exception
def init_audio():
    '''Function initializes default microphone as well as creates the list of available audio devices.
    Uses pyadio. The list of devices is added to the OptionMenu of the GUI window.
    '''
    global default_audio_device_index
    # Getting default input device
    default_audio_device_index = p.get_default_input_device_info()["index"] 
    
    for i in range(p.get_device_count()):
        # Constructing a menu of available audio devices, trimming long names
        temp_device = p.get_device_info_by_index(i)['name']
        device_name_in_list = temp_device[:30] + '...' if len(temp_device)>30 else temp_device
        audio_devices.append(str(p.get_device_info_by_index(i)['index']) + ': ' + device_name_in_list)
        
@catch_exception
def init_model(model_name):
    '''Function initializes VOSK speech recognition model through KaldiRecognizer.'''
    model = Model(model_name)
    global rec
    rec = KaldiRecognizer(model, settings.FRAME_RATE)
    rec.SetWords(True)

@catch_exception
def start_recording():
    '''Function is called when the recording button is pushed. It first checks the entries of frame rate and
    record duration entry fields. Then it creates a message queue and a thread for actual recording of audio.
    Another thread is created and started to perform speech recognition.
    '''
    global current_frame_rate, current_record_seconds
    # Checking for validity of frame rate and record duration
    try:
        current_frame_rate = int(frame_rate_entry.get())
        current_record_seconds = int(record_duration_entry.get())
    except:
        action_label['text'] = "Value error..."
        return(1)
    
    messages.put(True)
    # Starting a thread to record audio from microphone
    record = Thread(target=record_microphone, daemon=True)
    record.start()
    action_label['text'] = "Starting..."
    record_button["state"] = stop_button["state"]  = 'disabled'
        
    # Starting another thread to recognize audio
    transcribe = Thread(target=speech_recognition, daemon=True)
    transcribe.start()

@catch_exception
def stop_recording():
    '''Stops the recording, saves audio to file if requested and puts corresponding message
    to the messagues queue.'''
    if save_flag.get()==1:
        action_label['text'] = "Saving audio and stopping..."
        save_to_file()
        action_label['text'] = "Audio saved to file"
    else:
        action_label['text'] = "" 
    record_button["state"] = 'normal'  
    stop_button["state"] = 'disabled'
    
    messages.get()

@catch_exception
def record_microphone(chunk=1024):
    '''Actual recording. Pyadio object is initialized first to record from the chosen audio device.
    Then audi is read from the open stream in chunks and put to the recordings queue. Closes the stream 
    when the recording is stopped. 
    '''
    try:
        p = pyaudio.PyAudio()
        
        stream = p.open(format = AUDIO_FORMAT,
            channels = settings.CHANNELS,
            rate = current_frame_rate,
            input=True,
            input_device_index = int(audio_device_name.get().partition(':')[0]),
            frames_per_buffer=chunk
        )
    except:
        action_label['text'] = "Hardware error..."
        p.terminate()
        record_button["state"] = 'normal'
        return(1)

    action_label['text'] = 'Ready'
    record_button["state"] = 'disabled'
    stop_button["state"] = 'normal'
    frames=[]
    while not messages.empty():
            data = stream.read(chunk)
            frames.append(data)
            if len(frames) >= (current_frame_rate*current_record_seconds) / chunk:
               recordings.put(frames.copy())
               frames = []
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    action_label['text'] = ""
  
@catch_exception
def speech_recognition():
    '''While the messages queue is not empty the function takes audio from the recordings queue
    and runs the audio through the active VOSK model. The results of speech recognition is stored 
    in text variable and is appended to the correponding text widget of the GUI. Audio_data appends
    audio from the recordings queue to save it to file later as a complete record.
    '''
    global audio_data
    audio_data=[]    
    
    while not messages.empty():
        frames = recordings.get()
        rec.AcceptWaveform(b''.join(frames))
        results = rec.Result()
        text = json.loads(results)["text"]
        if len(text) > 0:
            text_box.insert('end', text+ '\n')
            text_box.focus()
            text_box.see("end")
       
        # Storing audio to write to file later
        audio_data += frames
                               
@catch_exception
def model_changed(event):
    '''Function is called when a model change is detected in the OptionMenu widget. It starts a separate
    thread to load a new model as it may take sufficient time for large models.'''
    # Loading new model in a separate thread 
    change_model = Thread(target=load_new_model, daemon=True)
    change_model.start()
    
    action_label['text'] = "Loading model, please wait..."
    record_button["state"] = stop_button["state"] = clear_button["state"] = 'disabled'
    model_list["state"] = audio_list["state"] = text_box["state"] = 'disabled'
    root.config(cursor='watch')
      
@catch_exception
def load_new_model():
    '''Calls a function to initialize a VOSK model'''
    init_model(model_name.get())
    record_button["state"] = clear_button["state"] = text_box["state"] = 'normal'
    stop_button["state"] = 'disabled'
    action_label['text'] = 'Ready'
    model_list["state"] = audio_list["state"] = 'normal'
    root.config(cursor='')
   
def clear_text():
    text_box.delete(1.0, 'end')

@catch_exception
def save_to_file():
    '''Function saves the recorded audio as a WAV file'''
    with wave.open("output.wav", "wb") as wf:
        wf.setnchannels(settings.CHANNELS)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(current_frame_rate)
        wf.writeframes(b''.join(audio_data))
        wf.close()


messages = Queue()
recordings = Queue()
AUDIO_FORMAT = pyaudio.paInt16
audio_devices = []
action_label = None

# Initializing list of available audio devices
p = pyaudio.PyAudio()
init_audio()  
p.terminate()
# Initializing recognition model
init_model(settings.MODEL_NAMES[0])

# ---------------------------- UI SETUP ------------------------------- #

root = tk.Tk()
root.title("Speech recognition")

# ROW 1
row = tk.Frame(root)
lab = tk.Label(row, width=22, text="Frame rate", anchor='w')
frame_rate_entry = tk.Entry(row, width=10)
frame_rate_entry.insert(0, settings.FRAME_RATE)  # default value
row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
lab.pack(side=tk.LEFT)
frame_rate_entry.pack(side=tk.LEFT, expand=tk.NO, fill=tk.X)

# ROW 2
row = tk.Frame(root)
lab = tk.Label(row, width=22, text="Records duration, s", anchor='w')
record_duration_entry = tk.Entry(row, width=10)
record_duration_entry.insert(0, settings.RECORD_SECONDS) # default value
row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
lab.pack(side=tk.LEFT)
record_duration_entry.pack(side=tk.LEFT, expand=tk.NO, fill=tk.X)

# ROW 3
row = tk.Frame(root)
lab = tk.Label(row, width=22, text="Recognition model", anchor='w')
model_name = tk.StringVar(root)
model_name.set(settings.MODEL_NAMES[0]) # default value
model_list = tk.OptionMenu(row, model_name, *settings.MODEL_NAMES, command = model_changed)
row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
lab.pack(side=tk.LEFT)
model_list.pack(side=tk.LEFT)

# ROW 4
row = tk.Frame(root)
lab = tk.Label(row, width=22, text="Audio devices", anchor='w')
audio_device_name = tk.StringVar(root)
audio_device_name.set(audio_devices[default_audio_device_index]) # default value
audio_list = tk.OptionMenu(row, audio_device_name, *audio_devices)
row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
lab.pack(side=tk.LEFT)
audio_list.pack(side=tk.LEFT)

# ROW 5
row = tk.Frame(root)
save_flag = tk.IntVar()
lab = tk.Label(row, width=22, text="Save audio to file", anchor='w')
save_box = tk.Checkbutton(row, text='Save audio to file',variable=save_flag, onvalue=1, offvalue=0)
row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
save_box.pack(side=tk.LEFT)

# ROW 6
row = tk.Frame(root)
action_label = tk.Label(row, width=50, text='Status:', fg='#ff0000', anchor='w')
row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
action_label.pack(side=tk.LEFT)

# ROW 7
row = tk.Frame(root)
record_button = tk.Button(row, text='Start', width=20, command=start_recording)
stop_button = tk.Button(row, text='Stop', state='disabled', width=20, command=stop_recording)
row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
record_button.pack(side=tk.LEFT, padx=5, pady=5)
stop_button.pack(side=tk.LEFT, padx=5, pady=5)

# ROW 8
row = tk.Frame(root)
text_box = tk.Text(
    row,
    height=10,
    width=45,
    state='normal',
    wrap=tk.WORD
)

# Adding scrollbar
sb = tk.Scrollbar(root)
sb.pack(side=tk.RIGHT, fill=tk.BOTH)
text_box.config(yscrollcommand=sb.set)
sb.config(command=text_box.yview)
row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
text_box.pack(side=tk.LEFT, expand=True, anchor='w')

# ROW 9
row = tk.Frame(root)
clear_button = tk.Button(row, text='Clear', width=20, command=clear_text)
row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
clear_button.pack(side=tk.LEFT, padx=5, pady=5)

root.geometry("430x510")
root.resizable(False, False)
root.mainloop()

#