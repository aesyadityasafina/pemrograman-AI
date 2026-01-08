# app.py

import os
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

# Memuat variabel lingkungan (environment variables) dari file .env
load_dotenv()

# Konfigurasi Flask
app = Flask(__name__)

# Mengambil Kunci API dari environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- PROMPT ENGINEERING (FINAL & EDUKATIF UNTUK INDONESIA) ---
AI_SYSTEM_PROMPT = """
You are an expert English language tutor. Your primary goal is to correct the user's spoken English, explain the grammar error, and provide a friendly, conversational response.

You MUST respond strictly in a single, valid JSON object format with SIX keys:
1. "original": The original, raw text spoken by the user.
2. "corrected": The grammatically correct version of the user's sentence.
3. "translation_id": The accurate and easily understandable Indonesian translation of the CORRECTED English sentence.
4. "explanation": A clear, concise, and easy-to-understand explanation (in Bahasa Indonesia) about the grammar mistake(s) found in the original sentence. If the sentence is already perfect, put "Kalimat sudah benar, tidak ada kesalahan tata bahasa." here.
5. "response": A short, encouraging, and conversational reply that acknowledges the user's sentence and keeps the dialogue flowing. THIS RESPONSE MUST ALWAYS BE IN ENGLISH.
6. "response_translation_id": The accurate and easily understandable Indonesian translation of the content in the 'response' key.

Example for a bad sentence:
User: "Me go to school yesterday."
Your JSON output:
{
  "original": "Me go to school yesterday.",
  "corrected": "I went to school yesterday.",
  "translation_id": "Saya pergi ke sekolah kemarin.",
  "explanation": "Kesalahan 1 (Subjek): Penggunaan 'Me' sebagai subjek, seharusnya 'I'. Kesalahan 2 (Tense): Gunakan bentuk kata kerja lampau (V2) yaitu 'went' karena ada keterangan waktu 'yesterday' (Simple Past Tense).",
  "response": "That sounds like a busy day! What did you do at school?",
  "response_translation_id": "Kedengarannya hari yang sibuk! Apa yang kamu lakukan di sekolah?"
}

Always respond in the required JSON format and focus on English grammar correction and conversation.
"""

def chat_with_ai(user_message):
    """
    Mengirim pesan pengguna ke Gemini API dan menerima balasan JSON.
    """
    try:
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY tidak ditemukan. Pastikan file .env sudah terisi.")

        # Inisiasi klien Gemini
        client = genai.Client(api_key=GEMINI_API_KEY)

        # Konfigurasi model dan prompt (response_schema untuk 6 kunci)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config={
                "system_instruction": AI_SYSTEM_PROMPT,
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "original": {"type": "string"},
                        "corrected": {"type": "string"},
                        "translation_id": {"type": "string"},
                        "explanation": {"type": "string"},
                        "response": {"type": "string"},
                        "response_translation_id": {"type": "string"} # Kunci Terjemahan Respons
                    },
                    "required": ["original", "corrected", "translation_id", "explanation", "response", "response_translation_id"] # 6 kunci diperlukan
                },
            }
        )

        # Mengurai string JSON dari respons Gemini
        return json.loads(response.text)

    except APIError as e:
        print(f"Gemini API Error: {e}")
        return {"error": "Terjadi kesalahan pada koneksi API Gemini."}
    except ValueError as e:
        print(f"Configuration Error: {e}")
        return {"error": str(e)}
    except json.JSONDecodeError:
        return {"error": "AI gagal merespons dalam format JSON yang diminta. Coba lagi."}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {"error": "Terjadi kesalahan server yang tidak terduga."}

@app.route('/')
def index():
    """Rute utama untuk menampilkan halaman HTML."""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    """Rute API untuk memproses pesan dari pengguna."""
    data = request.get_json()
    user_message = data.get('message')

    if not user_message:
        return jsonify({"error": "Pesan tidak ditemukan"}), 400

    # Panggil fungsi AI
    ai_response = chat_with_ai(user_message)

    # Kembalikan respons dari AI ke frontend
    return jsonify(ai_response)

if __name__ == '__main__':
    print("Server Flask berjalan di http://127.0.0.1:5000")
    app.run(debug=True)