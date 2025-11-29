import os
import traceback
import numpy as np
from PIL import Image
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from ultralytics import YOLO
from tavily import TavilyClient
import google.genai as genai
from dotenv import load_dotenv

# ==============================================================================
# 1. CẤU HÌNH & KHỞI TẠO (CONFIGURATION & INIT)
# ==============================================================================

# Nạp biến môi trường từ file .env
load_dotenv()

# Từ điển ánh xạ (Mapping) tên Class YOLO sang Tiếng Việt chuẩn hiển thị
NAME_MAPPING = {
    # --- MÓN ĂN (FOOD) ---
    "Banh_Beo": "Bánh Bèo",
    "Banh_Can": "Bánh Căn",
    "Banh_Gio": "Bánh Giò",
    "Banh_Mi": "Bánh Mì",
    "Banh_Trang_Nuong": "Bánh Tráng Nướng",
    "Banh_Xeo": "Bánh Xèo",
    "Bap_Xao": "Bắp Xào",
    "Bun_Bo": "Bún Bò Huế",
    "Bun_Cha": "Bún Chả",
    "Bun_Dau": "Bún Đậu Mắm Tôm",
    "Bun_Mam": "Bún Mắm",
    "Bun_Thit_Nuong": "Bún Thịt Nướng",
    "Cao_Lau": "Cao Lầu",
    "Chao_Long": "Cháo Lòng",
    "Com_Tam": "Cơm Tấm",
    "Goi_Cuon": "Gỏi Cuốn",
    "Hu_Tieu": "Hủ Tiếu",
    "Mi_Quang": "Mì Quảng",
    "Pha_Lau": "Phá Lấu",
    "Pho": "Phở",
    "Unknown": "Không xác định", # Class đặc biệt khi model không nhận diện được

    # --- ĐỊA ĐIỂM (PLACE) ---
    "Bao_Tang_Chung_Tich_Chien_Tranh": "Bảo Tàng Chứng Tích Chiến Tranh",
    "Bao_Tang_Lich_Su": "Bảo Tàng Lịch Sử TP.HCM",
    "Bao_Tang_My_Thuat": "Bảo Tàng Mỹ Thuật TP.HCM",
    "Bao_Tang_Thanh_Pho": "Bảo Tàng Thành Phố Hồ Chí Minh",
    "Ben_Nha_Rong": "Bến Nhà Rồng",
    "Bitexco": "Tháp Bitexco Financial Tower",
    "Bui_Vien_Tay": "Phố Đi Bộ Bùi Viện",
    "Buu_Dien_TPHCM": "Bưu Điện Trung Tâm Sài Gòn",
    "Cau_Mong": "Cầu Mống",
    "Cho_Ben_Thanh": "Chợ Bến Thành",
    "Cho_Binh_Tay": "Chợ Bình Tây (Chợ Lớn)",
    "Chua_Ba_Thien_Hau": "Chùa Bà Thiên Hậu",
    "Chua_Buu_Long": "Chùa Bửu Long",
    "Chua_Ngoc_Hoang": "Chùa Ngọc Hoàng",
    "Chua_Phap_Hoa": "Chùa Pháp Hoa",
    "Chua_Vinh_Nghiem": "Chùa Vĩnh Nghiêm",
    "Cot_Co_Thu_Ngu": "Cột Cờ Thủ Ngữ",
    "Dinh_Doc_Lap": "Dinh Độc Lập",
    "Ho_Con_Rua": "Hồ Con Rùa",
    "Landmark_81": "Landmark 81",
    "Nha_Hat_Thanh_Pho": "Nhà Hát Thành Phố",
    "Nha_Tho_Duc_Ba": "Nhà Thờ Đức Bà",
    "Nha_Tho_Giao_Xu_Tan_Dinh": "Nhà Thờ Tân Định (Nhà Thờ Màu Hồng)",
    "Thao_Cam_Vien": "Thảo Cầm Viên",
    "UBND_TPHCM": "Trụ sở UBND TP.HCM"
}

def init_app():
    """Khởi tạo Flask App, load Models và API Clients."""
    app = Flask(__name__)

    # 1. Load YOLO Models (Food & Place)
    model_paths = {
        "food": os.path.join("food", "best.pt"),
        "place": os.path.join("place", "best.pt"),
    }
    app.models = {}
    for k, v in model_paths.items():
        if os.path.exists(v):
            try:
                app.models[k] = YOLO(v)
                print(f"[INFO] Đã load model thành công: {v}")
            except Exception as e:
                print(f"[ERROR] Lỗi load model {v}: {e}")
        else:
            print(f"[WARNING] Không tìm thấy file model {v}")

    # 2. Khởi tạo API Clients (Tavily & Gemini)
    tavily_key = os.getenv("TAVILY_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not tavily_key: print("[WARNING] Thiếu TAVILY_API_KEY trong .env")
    if not gemini_key: print("[WARNING] Thiếu GEMINI_API_KEY trong .env")

    app.tavily = TavilyClient(api_key=tavily_key)
    app.gemini = genai.Client(api_key=gemini_key)

    # 3. Cấu hình Whitelist Domains cho Tavily Search
    raw_domains = os.getenv(
        "TRAVEL_DOMAINS",
        "vi.wikipedia.org,dulich.vnexpress.net,vnexpress.net,"
        "dulich.tuoitre.vn,tripadvisor.com.vn,booking.com,traveloka.com",
    )
    app.allowed_domains = [d.strip() for d in raw_domains.split(",")]

    return app

# Khởi tạo ứng dụng toàn cục
app = init_app()

# ==============================================================================
# 2. LOGIC XỬ LÝ CHÍNH (CORE LOGIC)
# ==============================================================================

def run_yolo_model(app, image: Image.Image, choice: str):
    """
    Chạy model YOLO để nhận diện vật thể trong ảnh.
    Returns: (Tên hiển thị, Độ tin cậy, Loại phân lớp)
    """
    model_key = "food" if choice == "food" else "place"
    kind = "món ăn" if model_key == "food" else "địa điểm"

    if model_key not in app.models:
        return "Unknown", 0.0, kind

    try:
        model = app.models[model_key]
        img_np = np.array(image)
        
        # Chạy inference (tắt verbose để đỡ rác log)
        results = model(img_np, verbose=False)[0]
        
        # Lấy class có xác suất cao nhất
        probs = results.probs.data.cpu().numpy()
        class_id = int(np.argmax(probs))
        conf = float(probs[class_id])
        
        # Lấy tên gốc từ model (ví dụ: "Banh_Mi")
        raw_name = results.names[class_id]
        
        # Ánh xạ sang tên đẹp (ví dụ: "Bánh Mì")
        # Nếu không có trong dict thì replace dấu "_" thành khoảng trắng
        pretty_name = NAME_MAPPING.get(raw_name, raw_name.replace("_", " "))
        
        return pretty_name, conf, kind
    except Exception as e:
        print(f"[ERROR] YOLO Inference: {e}")
        return "Error", 0.0, kind

def fetch_context(app, name: str, kind: str) -> str:
    """
    Tìm kiếm thông tin bổ sung về đối tượng từ Internet (Tavily).
    """
    if kind == "món ăn":
        query = f"Món ăn {name} Việt Nam nguồn gốc hương vị giá cả"
        domains = None # Món ăn thì tìm rộng hơn
    else:
        query = f"Địa điểm du lịch {name} tại Thành phố Hồ Chí Minh lịch sử kiến trúc"
        domains = app.allowed_domains # Địa điểm thì giới hạn domain du lịch

    try:
        resp = app.tavily.search(
            query,
            search_depth="advanced",
            max_results=3,
            include_domains=domains
        )
        results = (resp or {}).get("results", [])
        if not results: return ""
        return results[0].get("content", "").strip()
    except Exception as e:
        print(f"[ERROR] Tavily Search: {e}")
        return ""

def summarize_with_gemini(app, name: str, kind: str, context: str) -> str:
    """
    Sử dụng Gemini để tổng hợp thông tin thành đoạn giới thiệu hấp dẫn.
    """
    prompt = f"""
    Dựa trên thông tin: {context}
    Hãy viết đoạn giới thiệu hấp dẫn về {kind} "{name}".
    - Bối cảnh: TP.HCM (nếu là địa điểm), hoặc Việt Nam (nếu là món ăn).
    - Độ dài: 5-6 câu.
    - Giọng văn: Chuyên nghiệp, như hướng dẫn viên du lịch.
    - Tuyệt đối KHÔNG sử dụng biểu tượng cảm xúc (emoji).
    """
    try:
        resp = app.gemini.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        return (resp.text or "").strip()
    except Exception as e:
        print(f"[ERROR] Gemini Generate: {e}")
        return "Hệ thống đang bận, vui lòng thử lại sau."

def format_chat_answer(app, user_message: str) -> tuple[str, list]:
    """
    Logic Chatbot: Phân loại ý định -> Tìm kiếm (nếu cần) -> Trả lời.
    """
    now = datetime.now()
    today_str = now.strftime("%A, %d/%m/%Y %H:%M")
    
    # Bước 1: Phân loại ý định (Chat xã giao hay Tìm kiếm thông tin)
    intent_prompt = f"""
    Thời gian hiện tại: {today_str} (Giờ Việt Nam).
    Câu hỏi: "{user_message}"
    Nhiệm vụ: Phân loại "CHAT" hoặc "SEARCH".
    Format Output: ACTION | CONTENT
    """
    try:
        intent_resp = app.gemini.models.generate_content(model="gemini-2.5-flash", contents=intent_prompt)
        intent_text = (intent_resp.text or "").strip()
        if "|" in intent_text:
            action, content = [x.strip() for x in intent_text.split("|", 1)]
        else:
            action, content = "SEARCH", user_message
    except:
        action, content = "SEARCH", user_message

    # Nếu là CHAT xã giao
    if action == "CHAT":
        if len(content.split()) > 3: return content, []
        chat_resp = app.gemini.models.generate_content(model="gemini-2.5-flash", contents=f"Trả lời thân thiện: {user_message}")
        return chat_resp.text.strip(), []

    # Bước 2: Tìm kiếm thông tin (nếu là SEARCH)
    try:
        search_resp = app.tavily.search(content, search_depth="advanced", max_results=5)
        results = search_resp.get("results", [])
    except:
        return "Lỗi kết nối mạng.", []

    # Bước 3: Tổng hợp câu trả lời với định dạng Markdown
    sources = [{"title": r.get("title", "Nguồn"), "url": r.get("url")} for r in results if r.get("url")][:3]
    context_text = "\n".join([f"- [{r.get('title')}]: {r.get('content','')}" for r in results])
    
    final_prompt = f"""
    Thông tin tìm được: {context_text}
    Câu hỏi người dùng: "{user_message}"
    
    Yêu cầu trả lời:
    1. Trình bày ngắn gọn, súc tích.
    2. BẮT BUỘC sử dụng định dạng Markdown:
       - Sử dụng gạch đầu dòng (-) cho các ý chính.
       - In đậm (**text**) các thông số quan trọng (nhiệt độ, giá tiền, tên riêng).
    3. Không sử dụng emoji.
    """
    try:
        final_resp = app.gemini.models.generate_content(model="gemini-2.5-flash", contents=final_prompt)
        return final_resp.text.strip(), sources
    except:
        return "Lỗi tổng hợp câu trả lời.", []

# ==============================================================================
# 3. FLASK ROUTES (ĐỊNH TUYẾN API)
# ==============================================================================

@app.route("/")
def index():
    """Render trang chủ."""
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def api_predict():
    """API xử lý phân tích ảnh (Upload hoặc Camera)."""
    # Validate dữ liệu đầu vào
    if "image" not in request.files:
        return jsonify({"success": False, "error": "Thiếu dữ liệu ảnh"}), 400
    
    img_file = request.files["image"]
    choice = request.form.get("choice", "food")
    
    if not img_file.filename:
        return jsonify({"success": False, "error": "Chưa chọn file"}), 400

    try:
        # Chuyển đổi ảnh sang RGB để tương thích với model
        image = Image.open(img_file.stream).convert("RGB")
    except Exception as e:
        return jsonify({"success": False, "error": "File ảnh bị lỗi"}), 400

    # 1. Chạy nhận diện YOLO
    class_name, conf, kind = run_yolo_model(app, image, choice)
    
    # 2. Xử lý trường hợp KHÔNG XÁC ĐỊNH (Unknown Class)
    # Trả về ngay lập tức để tiết kiệm API call
    if class_name == "Không xác định":
        return jsonify({
            "success": True, 
            "low_confidence": True, # Bật cờ này để Frontend hiện cảnh báo vàng
            "confidence": conf, 
            "class_name": "Không xác định", 
            # Đổi kind thành "unknown" để Frontend không hiện nút Map (điều kiện map là kind === "địa điểm")
            "kind": "unknown", 
            "message": "Xin lỗi, mình không nhận diện được đối tượng trong ảnh này. Bạn vui lòng thử lại với hình ảnh rõ nét hơn nhé!"
        })

    # 3. Xử lý trường hợp ĐỘ TIN CẬY THẤP (< 80%)
    if conf < 0.8:
        return jsonify({
            "success": True, 
            "low_confidence": True,
            "confidence": conf, 
            "class_name": class_name, 
            "kind": kind,
            "message": f"Hệ thống chưa chắc chắn về kết quả này (Độ tin cậy thấp)."
        })

    # 4. Nếu kết quả tốt -> Gọi Tavily & Gemini để lấy thông tin
    context = fetch_context(app, class_name, kind)
    intro = summarize_with_gemini(app, class_name, kind, context)

    return jsonify({
        "success": True, 
        "low_confidence": False,
        "confidence": conf, 
        "class_name": class_name, 
        "kind": kind,
        "message": intro
    })

@app.route("/chat", methods=["POST"])
def api_chat():
    """API xử lý Chatbot thông minh."""
    try:
        data = request.get_json(force=True)
        user_msg = data.get("message", "").strip()
        if not user_msg: return jsonify({"success": False, "error": "Tin nhắn rỗng"}), 400
        
        answer, sources = format_chat_answer(app, user_msg)
        return jsonify({"success": True, "answer": answer, "sources": sources})
    except:
        return jsonify({"success": False, "error": "Lỗi Server"}), 500

if __name__ == "__main__":
    # Chạy server (Debug mode bật để dễ sửa lỗi)
    app.run(host="0.0.0.0", port=5000, debug=True)