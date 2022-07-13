# Speech recognition app
> TKinter application which performs speech recognition into text. VOSK models are used 

## Table of Contents
* [General Info](#general-information)
* [Technologies Used](#technologies-used)
* [Features](#features)
* [Screenshots](#screenshots)
* [Setup](#setup)
* [Usage](#usage)
* [Project Status](#project-status)
* [Room for Improvement](#room-for-improvement)
* [Acknowledgements](#acknowledgements)
* [Contact](#contact)
<!-- * [License](#license) -->

## General Information
- The application is built using Python, VOSK speech recognition models.
- PyAudio is used to capture audio from microphone in one thread.
- Audio is stored in a queue and processed in a separate thread using vosk model and KaldiRecognizer.
- Recognized text is dislayed in the text widget.
- There are menues for choosing a vosk model (several default ones: English, Ukrainian and German) and an audio device.  

## Technologies Used
- Python - version 3.9
- vosk - version 0.3.42
- PyAudio - version 0.2.11 (installed from .whl file)
- Python threading

## Screenshots
![Example screenshot](https://live.staticflickr.com/65535/52212922397_71526c6f18_o_d.jpg)

## Setup
PyAudio needs to be installed.
+ requirements.txt


## Usage
<!-- Provide various use cases and code examples here. -->


## Project Status
This project is for testing purposes.


## Contact
Created by Dmytro Zelenkov - feel free to contact me!

