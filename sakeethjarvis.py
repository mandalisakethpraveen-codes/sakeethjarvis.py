import datetime
import logging
import os
import random
from pathlib import Path
from typing import Optional

import pyautogui
import pyjokes
import pyttsx3
import speech_recognition as sr
import webbrowser as wb
import wikipedia

# Configure logging instead of printing raw exceptions
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class VoiceAssistant:
    def __init__(self, name_file: str = "assistant_name.txt") -> None:
        self.name_file = Path(name_file)
        self.engine = pyttsx3.init()
        self.configure_engine()
        self.assistant_name = self.load_name()

    def configure_engine(self) -> None:
        """Initializes TTS engine properties safely."""
        voices = self.engine.getProperty("voices")
        if len(voices) > 1:
            self.engine.setProperty("voice", voices[1].id)
        self.engine.setProperty("rate", 150)
        self.engine.setProperty("volume", 1.0)

    def speak(self, text: str) -> None:
        """Outputs text-to-speech and logs output."""
        logging.info(f"Assistant: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def load_name(self) -> str:
        """Loads assistant name from file or defaults to 'Jarvis'."""
        if self.name_file.exists():
            try:
                return self.name_file.read_text(encoding="utf-8").strip()
            except Exception as e:
                logging.error(f"Failed to load name file: {e}")
        return "Jarvis"

    def set_name(self) -> None:
        """Sets and persists a new assistant name."""
        self.speak("What would you like to name me?")
        new_name = self.take_command()
        if new_name:
            try:
                self.name_file.write_text(new_name, encoding="utf-8")
                self.assistant_name = new_name
                self.speak(f"Alright, I will be called {self.assistant_name} from now on.")
            except Exception as e:
                logging.error(f"Could not save assistant name: {e}")
                self.speak("Failed to save the new name locally.")
        else:
            self.speak("Sorry, I couldn't catch that.")

    def greet(self) -> None:
        """Greets the user based on the time of day."""
        hour = datetime.datetime.now().hour
        if 4 <= hour < 12:
            greeting = "Good morning!"
        elif 12 <= hour < 16:
            greeting = "Good afternoon!"
        elif 16 <= hour < 24:
            greeting = "Good evening!"
        else:
            greeting = "Good night!"

        self.speak(f"Welcome back, sir! {greeting}")
        self.speak(f"{self.assistant_name} at your service. How may I assist you?")

    def take_command(self) -> Optional[str]:
        """Captures audio input and converts it to text using speech recognition."""
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            logging.info("Listening...")
            recognizer.pause_threshold = 1
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            except sr.WaitTimeoutError:
                logging.warning("Listening timed out.")
                return None

        try:
            logging.info("Recognizing...")
            query = recognizer.recognize_google(audio, language="en-US")
            logging.info(f"User said: {query}")
            return query.lower()
        except sr.UnknownValueError:
            self.speak("Sorry, I did not understand that.")
        except sr.RequestError:
            self.speak("Speech recognition service is currently unreachable.")
        except Exception as e:
            logging.error(f"Unexpected recognition error: {e}")
        return None

    def tell_time(self) -> None:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        self.speak(f"The current time is {current_time}")

    def tell_date(self) -> None:
        now = datetime.datetime.now()
        date_str = now.strftime("%B %d, %Y")
        self.speak(f"Today's date is {date_str}")

    def take_screenshot(self) -> None:
        """Takes a screenshot with a unique timestamp filename."""
        pictures_dir = Path.home() / "Pictures"
        pictures_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = pictures_dir / f"screenshot_{timestamp}.png"
        
        img = pyautogui.screenshot()
        img.save(file_path)
        self.speak(f"Screenshot saved successfully.")
        logging.info(f"Screenshot saved to {file_path}")

    def play_music(self, song_keyword: Optional[str] = None) -> None:
        """Plays audio files safely from the user's Music directory."""
        music_dir = Path.home() / "Music"
        if not music_dir.exists():
            self.speak("Music directory not found.")
            return

        valid_extensions = {".mp3", ".wav", ".flac", ".m4a"}
        songs = [f for f in music_dir.iterdir() if f.is_file() and f.suffix.lower() in valid_extensions]

        if song_keyword:
            songs = [s for s in songs if song_keyword.lower() in s.stem.lower()]

        if songs:
            chosen_song = random.choice(songs)
            logging.info(f"Playing: {chosen_song}")
            self.speak(f"Playing {chosen_song.stem}")
            os.startfile(chosen_song) if hasattr(os, "startfile") else wb.open(chosen_song.as_uri())
        else:
            self.speak("No matching audio files were found.")

    def search_wikipedia(self, query: str) -> None:
        clean_query = query.replace("wikipedia", "").strip()
        if not clean_query:
            self.speak("What topic would you like me to search on Wikipedia?")
            return

        self.speak("Searching Wikipedia...")
        try:
            summary = wikipedia.summary(clean_query, sentences=2)
            self.speak(summary)
        except wikipedia.exceptions.DisambiguationError:
            self.speak("Multiple results found. Please be more specific.")
        except wikipedia.exceptions.PageError:
            self.speak("I couldn't find any page matching that request.")
        except Exception as e:
            logging.error(f"Wikipedia API error: {e}")
            self.speak("An error occurred while fetching information.")

    def run(self) -> None:
        """Main execution loop."""
        self.greet()
        
        while True:
            query = self.take_command()
            if not query:
                continue

            if "time" in query:
                self.tell_time()
            elif "date" in query:
                self.tell_date()
            elif "wikipedia" in query:
                self.search_wikipedia(query)
            elif "play music" in query:
                song = query.replace("play music", "").strip()
                self.play_music(song if song else None)
            elif "open youtube" in query:
                wb.open("https://youtube.com")
            elif "open google" in query:
                wb.open("https://google.com")
            elif "change your name" in query:
                self.set_name()
            elif "screenshot" in query:
                self.take_screenshot()
            elif "joke" in query:
                joke = pyjokes.get_joke()
                self.speak(joke)
            elif "shutdown" in query:
                self.speak("Shutting down the system. Goodbye!")
                os.system("shutdown /s /f /t 1")
                break
            elif "restart" in query:
                self.speak("Restarting the system.")
                os.system("shutdown /r /f /t 1")
                break
            elif any(k in query for k in ["offline", "exit", "quit", "stop"]):
                self.speak("Going offline. Have a great day!")
                break


if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()
