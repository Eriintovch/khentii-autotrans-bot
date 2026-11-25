import os
import json
import requests
from flask import Flask, request
from google import genai
from google.genai import types

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "khentii_autotrans_2026")

client = genai.Client(api_key=GEMINI_API_KEY)

BASE_IMG_URL = "https://githubusercontent.com"
IMG_EXT = ".jpg"

POSTERS = {
    "CARGO_SERVICE": f"{BASE_IMG_URL}/Achaa_teesh{IMG_EXT}",
    "REG_CERT_CHANGE": f"{BASE_IMG_URL}/Burtgel_gerchilgee_solih{IMG_EXT}",
    "REG_DEREGISTER": f"{BASE_IMG_URL}/Burtgel_Hasalt{IMG_EXT}",
    "REG_IMPORT_NEW": f"{BASE_IMG_URL}/Burtgel_import{IMG_EXT}",
    "REG_CERT_REPLACE": f"{BASE_IMG_URL}/Burtgel_nuhult{IMG_EXT}",
    "REG_OWNER_TRANSFER": f"{BASE_IMG_URL}/Burtgel_Shiljiilt{IMG_EXT}",
    "REG_PLATE_HOLD": f"{BASE_IMG_URL}/Burtgel_UD_hadgalah{IMG_EXT}",
    "REG_PLATE_REPLACE": f"{BASE_IMG_URL}/Burtgel_UD_nuhult{IMG_EXT}",
    "REG_PLATE_CHANGE": f"{BASE_IMG_URL}/Burtgel_UDS{IMG_EXT}",
    "REG_PLATE_TRANSFER": f"{BASE_IMG_URL}/Burtgel_UDS_Shiljilt{IMG_EXT}",
    "REG_GENERAL": f"{BASE_IMG_URL}/Burtgeliin_uilchilgee{IMG_EXT}",
    "BUS_BOR_UNDUR": f"{BASE_IMG_URL}/Hot_hoorond_BU{IMG_EXT}",
    "BUS_UB": f"{BASE_IMG_URL}/Hot_hoorond_Ch{IMG_EXT}",
    "PRO_DRIVER_EXAM": f"{BASE_IMG_URL}/Mergeshsen_jolooch_1{IMG_EXT}",
    "PRO_DRIVER_INFO": f"{BASE_IMG_URL}/Mergeshsen_jolooch_2{IMG_EXT}",
    "TAX_INFO": f"{BASE_IMG_URL}/Tatwar{IMG_EXT}",
    "TECH_INSPECTION": f"{BASE_IMG_URL}/Tekhnik_vzleg{IMG_EXT}",
    "FINE_INFO": f"{BASE_IMG_URL}/Torguuli{IMG_EXT}",
    "ROAD_FEE_INFO": f"{BASE_IMG_URL}/Zamiin_huraamj{IMG_EXT}",
}

SYSTEM_PROMPT = """
Та Хэнтий аймгийн Автотээврийн төвийн албан ёсны мэдээллийн чатбот. 
Монгол хэлээр эелдэг, товч, ойлгомжтой хариул. Кирилл, латин галиг, холимог бичвэр болон үг үсгийн алдаатай асуултын утгыг заавал таньж ойлго.
Зөвхөн доорх БАТАЛГААЖСАН МЭДЛЭГИЙН САНД тулгуурлан хариул. Мэдээлэл дутуу бол 98302858 дугаараар лавлахыг зөвлө.

ХАРИУЛТЫН ФОРМАТ (ЗААВАЛ JSON ХЭЛБЭРЭЭР БУЦААНА):
{
  "reply_text": "Хэрэглэгчид очих монгол хэлээрх товч, тодорхой хариулт + Лавлах утас: 98302858",
  "poster_id": "Доорх жагсаалтаас тохирох 1 ID эсвэл NONE"
}

БОЛОМЖИТ POSTER_ID ЖАГСААЛТ:
- CARGO_SERVICE (Ачаа тээш хадгалах, илгээх, хүлээн авах)
- BUS_UB (Чингис/Өндөрхаан - Улаанбаатар хот хоорондын автобус)
- BUS_BOR_UNDUR (Бор-Өндөр - Улаанбаатар хот хоорондын автобус)
- REG_GENERAL (Бүртгэлийн үйлчилгээний ерөнхий мэдээлэл, бүрдүүлэх материал)
- REG_CERT_CHANGE (Гэрчилгээ солилт)
- REG_DEREGISTER (Бүртгэлээс хасах)
- REG_IMPORT_NEW (Импортын шинэ бүртгэл)
- REG_CERT_REPLACE (Гэрчилгээ нөхөлт / гээгдүүлсэн гэрчилгээ)
- REG_OWNER_TRANSFER (Өмчлөгч шилжүүлэлт / дугаар солихгүй)
- REG_PLATE_HOLD (Улсын дугаар хадгалалт)
- REG_PLATE_REPLACE (Улсын дугаар нөхөлт / гээгдүүлсэн дугаар)
- REG_PLATE_CHANGE (Улсын дугаар солилт / өмчлөгч солихгүй)
- REG_PLATE_TRANSFER (Улсын дугаар солилттой шилжилт)
- TECH_INSPECTION (Техникийн хяналтын үзлэг, оношилгоо)
- PRO_DRIVER_EXAM (Мэргэшсэн жолоочийн шалгалт, бүрдүүлэх материал, хураамж)
- PRO_DRIVER_INFO (Мэргэшсэн жолооч болохын давуу тал, хууль эрх зүй)
- TAX_INFO (Тээврийн хэрэгслийн албан татвар төлөх)
- FINE_INFO (Замын хөдөлгөөний зөрчлийн торгууль төлөх)
- ROAD_FEE_INFO (Хот хоорондын авто зам ашигласны хураамж төлөх)
- NONE (Дээрх постерт хамаарахгүй асуулт бол)

БАТАЛГААЖСАН МЭДЛЭГИЙН САН:
1. Чингис (Өндөрхаан) – Улаанбаатар зорчигч тээвэр (BUS_UB):
- Хуваарь: Өдөр бүр Чингис хотоос 08:00, 14:00 цагт; Улаанбаатараас 10:00, 16:00 цагт хөдөлнө.
- Тариф: Том хүн 34,200₮, Хүүхэд (6–12 нас) 17,100₮, 6 хүртэлх насны хүүхэд үнэгүй.
- Нөхцөл: 1 хүн 20 кг хүртэл ачаа үнэгүй. Кассаас болон https://transdep.mn сайтаар захиална. Ажлын цаг: 07:00–00:00.

2. Бор-Өндөр – Улаанбаатар зорчигч тээвэр (BUS_BOR_UNDUR):
- Хуваарь: УБ -> Бор-Өндөр: Даваа, Бямба гарагт 16:00 цагаас; Бор-Өндөр -> УБ: Пүрэв, Ням гарагт 09:00 цагаас хөдөлнө.
- Холбоо барих утас: 89333308, 99178059, 99299182.

3. Ачаа тээш хадгалах, илгээх үйлчилгээ (CARGO_SERVICE):
- Тариф: Өдөрт 1,100₮, Хоногт 2,200₮. Илгээмжийг 72 цагаас дээш хадгалахгүй.
- Хэнтий (Чингис хот): Өдөр бүр 07:30–20:00, Утас: 98302858.
- Улаанбаатар (Баянзүрх зорчигч тээврийн төв): Өдөр бүр 24 цаг, Утас: 95628629.

4. Техникийн хяналтын үзлэг (TECH_INSPECTION):
- Тариф: Шинэ тээврийн хэрэгсэл (насжилт 2 жил) 2,178₮; Чиргүүл, мотоцикл 11,000₮; Суудлын машин, такси, пикап 22,000₮; Ачааны машин, автобус, тусгай зориулалтын тээврийн хэрэгсэл, механизм 33,000₮.
- Бэлдэх зүйлс: Татвар, торгууль, зам ашигласны хураамжаа төлсөн байх, тээврийн хэрэгслийн бүрэн бүтэн байдлыг хангасан байх.
- Ажлын цаг: 09:00–18:00 (Цайны цаг 13:00–14:00).

5. Мэргэшсэн жолоочийн шалгалт, үнэмлэх (PRO_DRIVER_EXAM & PRO_DRIVER_INFO):
- Бүрдүүлэх материал: 1) Эрүүл мэндийн үзлэгийн хуудас (тухайн жил), 2) Шалгалтын төлбөр тушаасан баримт 9,900₮, 3) Сургалтын хөтөлбөр хангасан байх (2008.08.08-наас хойш тухайн ангилал авсан бол).
- Тэнцсэний дараах хураамж: Үнэмлэхний үнэ 12,500₮, Улсын тэмдэгтийн хураамж 1,000₮.
- Шалгалт: Онол болон жолоодлогын 2 шатлалтай. Ажлын өдрүүдэд ажлын цагаар авна. Хугацаа дууссан бол шалгалт өгч сунгана.
- Давуу тал ба Хууль: Автотээврийн тухай хуулийн 10.2.2, 19.1-р заалтын дагуу С, Д ангилал, улс хоорондын болон жуулчин тээвэр, аюултай ачаа тээвэрлэхэд мэргэшсэн жолооч шаардлагатай.

6. Тээврийн хэрэгслийн бүртгэлийн үйлчилгээ (REG_GENERAL ба 9 үйлчилгээ):
- Ажлын цаг: 09:00–18:00 (Цайны цаг 13:00–14:00).
- Ерөнхий бүрдүүлэх материал: Иргний үнэмлэх, тээврийн хэрэгслийн гэрчилгээ, худалдах/худалдан авах гэрээ (нотариатаар баталгаажуулсан), даатгал (ОСАГО), татвар/хураамж төлсөн баримт. Бүгдэд нь татвар, торгууль, замын хураамжийн өргүй байх шаардлагатай.
- Гэрчилгээ солилт (REG_CERT_CHANGE): Үзлэгт орсон байх, хуучин гэрчилгээг хураалгах, өмчлөгч өөрийн биеэр ирэх. Цахим/цаасаар авна.
- Бүртгэлээс хасах (REG_DEREGISTER): Дугаар, гэрчилгээг хураалгах (үрэгдүүлсэн бол хүчингүйд тооцуулах), өмчлөгч өөрийн биеэр ирэх. Дахин сэргээх боломжгүй.
- Импортын шинэ бүртгэл (REG_IMPORT_NEW): Үзлэгт тэнцсэн байх, бичиг баримт, хилээр оруулсан иргэн өөрөө эсвэл худалдан авсан гэрээтэй ирэх. Харьяаллын дагуу дугаар авна.
- Гэрчилгээ нөхөлт (REG_CERT_REPLACE): Үзлэгт орсон байх, хуучин гэрчилгээг хүчингүйд тооцуулж зарлуулсан бичиг, өмчлөгч өөрийн биеэр ирэх.
- Өмчлөгч шилжүүлэлт (REG_OWNER_TRANSFER): Дугаар солихгүй, үзлэгт орсон байх, шилжүүлж өгч байгаа иргэн өөрөө эсвэл гэрээтэй ирэх.
- Улсын дугаар хадгалалт (REG_PLATE_HOLD): 365 хоног хадгална, гэрээ байгуулна, өмчлөгч өөрийн биеэр ирэх.
- Улсын дугаар нөхөлт (REG_PLATE_REPLACE): Үзлэгт орсон байх, зарлуулсан бичиг (2ш дугаар хоёул гээгдсэн бол замын цагдаагийн тодорхойлолт), өмчлөгч өөрийн биеэр ирэх.
- Улсын дугаар солилт (REG_PLATE_CHANGE): Өмчлөгч солихгүй дугаар солино. Үзлэгт орсон байх, хуучин дугаараа хураалгахаар авчрах, өөрийн биеэр ирэх.
- Улсын дугаар солилттой шилжилт (REG_PLATE_TRANSFER): Харьяаллын дагуу дугаар авна, үзлэгт орсон байх, хуучин дугаараа авчрах, шилжүүлэгч өөрөө эсвэл гэрээтэй ирэх.

7. Татвар, Торгууль, Замын хураамж:
- Албан татвар (TAX_INFO): Жил бүрийн 6-р сарын 1-нээс өмнө төлнө. Суваг: E-Tax (e-tax.mta.mn), iTax, Ebarimt, Smartcar.mn, E-Mongolia, Интернэт банк, Гэрэгэ киоск, банкны салбар, Мобайл ПОС.
- Зөрчлийн торгууль (FINE_INFO): 15 хоногийн дотор төлбөл 50% хөнгөлнө. Хугацаа хэтрүүлбэл сар бүр 10% нэмэгдэнэ (50%-иас хэтрэхгүй). Суваг: E-Mongolia, Tpay.gov.mn, Ubtraffic.mn, Богд банк, Төрийн банк, Гэрэгэ, Smartcar.mn, Hotula, Ebarimt, ERTHUB. Лавлах: Цагдаагийн торгууль 7019-1302, Камерын торгууль 7011-1642.
- Авто зам ашигласны төлбөр (ROAD_FEE_INFO): roadpay.mn, e-mongolia.mn, ebarimt.mn, ezam.mn болон банкны апп-уудаар шалгаж төлнө. Зам, тээврийн хөгжлийн төвийн 24/7 лавлах: 7000-2413, 8000-2413.

8. Ерөнхий байршил ба Лавлах утас:
- Байршил: Хэнтий аймаг, Чингис хот, Хэнтий аймгийн Автотээврийн төв.
- Лавлах утас: 98302858 (Лавлах мэдээлэл 08:00–00:00).
"""

def send_message(recipient_id, text):
    url = f"https://facebook.com{PAGE_ACCESS_TOKEN}"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
    requests.post(url, json=payload)

def send_image(recipient_id, image_url):
    url = f"https://facebook.com{PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {
            "attachment": {
                "type": "image",
                "payload": {"url": image_url, "is_reusable": True}
            }
        }
    }
    requests.post(url, json=payload)

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Invalid verification token", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                if messaging_event.get("message") and messaging_event["message"].get("text"):
                    sender_id = messaging_event["sender"]["id"]
                    user_text = messaging_event["message"]["text"]
                    
                    try:
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=user_text,
                            config=types.GenerateContentConfig(
                                system_instruction=SYSTEM_PROMPT,
                                response_mime_type="application/json"
                            )
                        )
                        ai_data = json.loads(response.text)
reply_text = ai_data.get("reply_text", "Уучлаарай, 98302858 дугаараар лавлана уу.")
poster_id = ai_data.get("poster_id", "NONE")
send_message(sender_id, reply_text)
if poster_id in POSTERS and POSTERS[poster_id].startswith("http"):
send_image(sender_id, POSTERS[poster_id])
except Exception as e:
print("Error:", e)
send_message(sender_id, "Уучлаарай, систем түр ачаалалтай байна. 98302858 дугаараар холбогдоно уу.")
return "OK", 200
if name == "main":
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
