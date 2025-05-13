import requests
import os

# Create directory if it doesn't exist
os.makedirs("kokoro-tts-web", exist_ok=True)
os.chdir("kokoro-tts-web")

# URLs and filenames
files = {
    "voices-v1.0.bin": "https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin",
    "kokoro-v1.0.onnx": "https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx"
}

# Download function
def download_file(url, filename):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

# Download all files
for filename, url in files.items():
    print(f"Downloading {filename}...")
    download_file(url, filename)
    print(f"Downloaded {filename} ({os.path.getsize(filename)/1024/1024:.2f} MB)")

print("All files downloaded successfully!")
