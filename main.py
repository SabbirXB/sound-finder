import os
import subprocess
import requests
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()

# আপনার AudD.io থেকে নেওয়া ফ্রি টোকেন এখানে বসান
AUDD_API_TOKEN = "YOUR_AUDD_API_KEY_HERE"

class URLRequest(BaseModel):
    url: str

@app.post("/detect")
def detect_music(payload: URLRequest):
    temp_audio = "temp.mp3"
    
    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format", "mp3",
        "--postprocessor-args", "ffmpeg:-t 15",
        "-o", temp_audio,
        "--force-overwrites",
        payload.url
    ]
    
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        return {"success": False, "message": "ভিডিও বা অডিও রিড করা সম্ভব হয়নি। লিঙ্কটি পাবলিক কি না চেক করুন।"}

    with open(temp_audio, "rb") as f:
        response = requests.post(
            "https://api.audd.io/",
            data={'api_token': AUDD_API_TOKEN},
            files={'file': f}
        ).json()

    if os.path.exists(temp_audio):
        os.remove(temp_audio)

    if response.get("status") == "success" and response.get("result"):
        info = response["result"]
        return {
            "success": True,
            "title": info.get("title", "অজানা গান"),
            "artist": info.get("artist", "অজানা শিল্পী"),
            "album": info.get("album", "N/A")
        }
    return {"success": False, "message": "কোনো গান শনাক্ত করা যায়নি।"}

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="bn">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Sound Detective</title>
      <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-900 text-white flex items-center justify-center min-h-screen p-4">
      <div class="bg-slate-800 p-6 rounded-2xl w-full max-w-sm text-center shadow-2xl border border-slate-700">
        <h2 class="text-xl font-bold mb-2">🎵 Sound Detective</h2>
        <p class="text-xs text-slate-400 mb-5">YouTube বা Facebook ভিডিও লিঙ্ক দিন</p>
        <input id="link" class="w-full p-3 bg-slate-900 border border-slate-600 rounded-xl text-sm text-white mb-3 outline-none" placeholder="Paste link here...">
        <button onclick="find()" id="btn" class="w-full bg-blue-600 active:bg-blue-700 p-3 rounded-xl font-bold text-sm shadow">গান খুঁজুন</button>
        <div id="out" class="mt-4 text-sm font-semibold text-slate-200"></div>
      </div>
      <script>
        async function find() {
          const l = document.getElementById('link').value;
          const out = document.getElementById('out');
          const btn = document.getElementById('btn');
          if(!l) return alert('দয়া করে একটি লিঙ্ক দিন!');
          btn.innerText = 'গান খোঁজা হচ্ছে...';
          btn.disabled = true;
          out.innerHTML = '<span class="text-yellow-400 text-xs">ভিডিও অডিও স্ক্যান করা হচ্ছে...</span>';
          
          try {
            const r = await fetch('/detect', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({url: l})
            });
            const d = await r.json();
            if(d.success) {
              out.innerHTML = `<div class="bg-slate-900 p-3 rounded-xl border border-emerald-500/30 text-left">
                <span class="text-emerald-400 text-xs font-bold uppercase">গান পাওয়া গেছে:</span><br>
                <span class="text-base font-bold text-white">🎶 ${d.title}</span><br>
                <span class="text-xs text-slate-300">🎤 শিল্পী: ${d.artist}</span><br>
                <span class="text-xs text-slate-400">💿 অ্যালবাম: ${d.album}</span>
              </div>`;
            } else {
              out.innerHTML = `<span class="text-rose-400 text-xs">${d.message}</span>`;
            }
          } catch(e) {
            out.innerHTML = '<span class="text-rose-400 text-xs">সার্ভারে কানেক্ট হতে সমস্যা হয়েছে!</span>';
          }
          btn.innerText = 'গান খুঁজুন';
          btn.disabled = false;
        }
      </script>
    </body>
    </html>
    """
