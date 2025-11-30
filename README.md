# 📸 TravelLens - Trợ Lý Du Lịch AI Việt Nam

   

**TravelLens** là một ứng dụng web thông minh giúp khách du lịch khám phá văn hóa và ẩm thực Việt Nam thông qua hình ảnh. Ứng dụng kết hợp sức mạnh của **Thị giác máy tính (Computer Vision)** để nhận diện đối tượng và **AI tạo sinh (Generative AI)** để cung cấp thông tin ngữ cảnh phong phú theo thời gian thực.

-----

## Tính Năng Nổi Bật

  * **Nhận diện thông minh (Object Detection):**
  
      * Tích hợp 2 mô hình **YOLOv11** được huấn luyện riêng biệt.
      
      * Nhận diện chính xác các **món ăn đặc sản Việt Nam** (Phở, Bánh mì, Bún bò...).
      
      * Nhận diện các **địa điểm du lịch, di tích** nổi tiếng tại TP.HCM (Dinh Độc Lập, Chợ Bến Thành...).
      
  * **Tổng hợp thông tin (AI Context):**
  
      * Sử dụng **Tavily Search API** để tìm kiếm thông tin mới nhất về đối tượng.
      
      * Sử dụng **Google Gemini 2.5 Flash** để tổng hợp và viết lời giới thiệu hấp dẫn như một hướng dẫn viên du lịch chuyên nghiệp.
      
  * **Đa dạng đầu vào:**
  
      * Hỗ trợ tải ảnh từ thư viện.
      
      * Tích hợp Camera chụp ảnh trực tiếp trên trình duyệt.
      
  * **Chatbot AI:** Trợ lý ảo tích hợp sẵn để trả lời mọi câu hỏi về du lịch và ăn uống.
  
  * **Điều hướng:** Tự động liên kết với Google Maps để chỉ đường đến địa điểm nhận diện được.
-----


##  Công Nghệ Sử Dụng


### Backend


  * **Ngôn ngữ:** Python 3.x
  * **Framework:** Flask
  * **Computer Vision:** [Ultralytics YOLOv11](https://github.com/ultralytics/ultralytics)
  * **LLM & Search:**
      * Google Gemini API (Generative AI)
      * Tavily API (AI Search Engine)

### Frontend

  * **Giao diện:** HTML5, CSS3 (Responsive Design).
  * **Logic:** JavaScript (Vanilla JS) xử lý Camera stream và AJAX request.
  * **Design:** Phong cách hiện đại, clean UI.

-----

##  Cấu Trúc Dự Án

```bash
TravelLens/
├── food/
│   └── best.pt          # Model YOLOv11 chuyên nhận diện Món ăn
├── place/
│   └── best.pt          # Model YOLOv11 chuyên nhận diện Địa điểm
├── static/
│   ├── images/          # Tài nguyên hình ảnh
│   ├── style.css        # CSS Stylesheet
│   └── script.js        # Logic Frontend (Camera, Upload, Chat)
├── templates/
│   └── index.html       # Giao diện chính (UI)
├── .env                 # Cấu hình API Keys (Không commit file này)
├── app.py               # Flask Server & Logic xử lý chính
├── requirements.txt     # Danh sách thư viện phụ thuộc
└── README.md            # Tài liệu dự án
```

-----

##  Hướng Dẫn Cài Đặt

Làm theo các bước sau để chạy dự án trên máy cục bộ:

### 1\. Clone dự án

```bash
git clone https://github.com/your-username/TravelLens.git
cd TravelLens
```

### 2\. Thiết lập môi trường ảo (Khuyên dùng)

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3\. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### 4\. Cấu hình biến môi trường

Tạo file `.env` tại thư mục gốc và điền API Key của bạn vào:

```env
# Lấy key miễn phí tại: https://aistudio.google.com/
GEMINI_API_KEY=your_gemini_api_key_here

# Lấy key miễn phí tại: https://tavily.com/
TAVILY_API_KEY=your_tavily_api_key_here
```

### 5\. Chuẩn bị Model YOLO

Đảm bảo bạn đã có file weights (`best.pt`) đã được huấn luyện và đặt đúng vào thư mục:

  * `food/best.pt`
  * `place/best.pt`

### 6\. Khởi chạy ứng dụng

```bash
python app.py
```

Mở trình duyệt và truy cập: `http://localhost:5000`

-----


##  Demo

**Trang chủ**
<img width="1887" height="900" alt="image" src="https://github.com/user-attachments/assets/8d5ddef7-5a07-4346-927d-92774be6fd77" />


**Nhận dạng món ăn**
<img width="1264" height="650" alt="image" src="https://github.com/user-attachments/assets/747ec42a-4c19-40e2-ae54-c55b352c15ef" />

**Nhận dạng địa điểm**
<img width="1257" height="640" alt="image" src="https://github.com/user-attachments/assets/c3767811-f50f-4caf-b80f-e2e1f4c31412" />

**Chatbot**
<img width="1882" height="883" alt="image" src="https://github.com/user-attachments/assets/157c2284-fe7a-42da-be2b-c33abfc5e6a9" />


-----

##  Đóng Góp (Contributing)

Mọi đóng góp để cải thiện dự án đều được hoan nghênh.

1.  Fork dự án.
2.  Tạo Branch mới (`git checkout -b feature/NewFeature`).
3.  Commit thay đổi (`git commit -m 'Add NewFeature'`).
4.  Push lên Branch (`git push origin feature/NewFeature`).
5.  Tạo Pull Request.


-----

### Liên Hệ

  * **Tác giả:** Phong
  * **Lĩnh vực:** Khoa học máy tính (Data & AI)

thêm icon của 1 số thư viện như python, tavily ,...
