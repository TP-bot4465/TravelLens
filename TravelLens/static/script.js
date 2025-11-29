// ============================================================
// 1. HERO SLIDER
// ============================================================
const slider = document.getElementById("hero-slider");
if (slider) {
  const slides = slider.querySelectorAll(".slide");
  let current = 0;
  if (slides.length > 0) {
    setInterval(() => {
      slides[current].classList.remove("active");
      current = (current + 1) % slides.length;
      slides[current].classList.add("active");
    }, 4000);
  }
}

// ============================================================
// 2. CAMERA & UPLOAD HANDLING
// ============================================================
const form = document.getElementById("upload-form");
const imageInput = document.getElementById("image-input");
const uploadPlaceholder = document.getElementById("upload-placeholder");
const previewContainer = document.getElementById("preview-container");
const previewImg = document.getElementById("preview-img");
const removeImgBtn = document.getElementById("remove-img-btn");
const statusEl = document.getElementById("status");
const resultTextEl = document.getElementById("result-text");
const submitBtn = document.getElementById("submit-btn");

const openCameraBtn = document.getElementById("open-camera-btn");
const closeCameraBtn = document.getElementById("close-camera-btn");
const snapBtn = document.getElementById("snap-btn");
const cameraContainer = document.getElementById("camera-container");
const videoFeed = document.getElementById("video-feed");
const canvas = document.getElementById("canvas");

let stream = null;
let capturedBlob = null; 

// A. File Upload
if (imageInput) {
  imageInput.addEventListener("change", () => {
    const file = imageInput.files[0];
    if (!file) return;
    
    capturedBlob = null; 
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      uploadPlaceholder.classList.add("hidden");
      previewContainer.classList.remove("hidden");
    };
    reader.readAsDataURL(file);
  });
}

// B. Open Camera (Fallback Logic)
if (openCameraBtn) {
    openCameraBtn.addEventListener("click", async () => {
        try {
            statusEl.textContent = "Đang khởi động camera...";
            // Thu mo camera sau
            const constraints = { video: { facingMode: "environment" } };
            try {
                stream = await navigator.mediaDevices.getUserMedia(constraints);
            } catch (e) {
                console.warn("Lỗi camera sau, thử camera mặc định...");
                stream = await navigator.mediaDevices.getUserMedia({ video: true });
            }

            videoFeed.srcObject = stream;
            
            uploadPlaceholder.classList.add("hidden");
            cameraContainer.classList.remove("hidden");
            statusEl.textContent = ""; 

        } catch (err) {
            alert("Lỗi Camera: " + err.message);
            statusEl.textContent = "Không thể truy cập camera.";
            statusEl.style.color = "red";
        }
    });
}

// C. Close Camera
if (closeCameraBtn) {
    closeCameraBtn.addEventListener("click", stopCamera);
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
    cameraContainer.classList.add("hidden");
    uploadPlaceholder.classList.remove("hidden");
}

// D. Snap Photo
if (snapBtn) {
    snapBtn.addEventListener("click", () => {
        canvas.width = videoFeed.videoWidth;
        canvas.height = videoFeed.videoHeight;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(videoFeed, 0, 0, canvas.width, canvas.height);
        
        canvas.toBlob((blob) => {
            capturedBlob = blob; 
            previewImg.src = URL.createObjectURL(blob);
            stopCamera();
            uploadPlaceholder.classList.add("hidden");
            previewContainer.classList.remove("hidden");
        }, "image/jpeg", 0.9);
    });
}

// E. Reset
if (removeImgBtn) {
  removeImgBtn.addEventListener("click", () => {
    imageInput.value = ""; 
    capturedBlob = null;
    previewImg.src = "";
    previewContainer.classList.add("hidden");
    uploadPlaceholder.classList.remove("hidden");
    statusEl.textContent = "Kết quả phân tích sẽ hiển thị tại đây...";
    resultTextEl.innerHTML = "";
  });
}

// ============================================================
// 3. FORM SUBMISSION
// ============================================================
if (form) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    let fileToSend = null;
    if (capturedBlob) {
        fileToSend = capturedBlob;
    } else if (imageInput.files.length > 0) {
        fileToSend = imageInput.files[0];
    }

    if (!fileToSend) {
      statusEl.textContent = "Vui lòng chọn ảnh.";
      statusEl.style.color = "red";
      return;
    }

    const choice = document.querySelector("input[name='choice']:checked").value;
    const formData = new FormData();
    formData.append("image", fileToSend, "captured.jpg");
    formData.append("choice", choice);

    statusEl.textContent = "Đang phân tích...";
    statusEl.style.color = "#0077B6";
    resultTextEl.innerHTML = "";
    if (submitBtn) submitBtn.disabled = true;

    try {
      const resp = await fetch("/predict", { method: "POST", body: formData });
      const data = await resp.json();
      if (submitBtn) submitBtn.disabled = false;

      if (!data.success) {
        statusEl.textContent = data.error || "Có lỗi xảy ra.";
        statusEl.style.color = "red";
        return;
      }

      if (data.low_confidence) {
        statusEl.textContent = "Độ tin cậy thấp.";
        statusEl.style.color = "orange";
      } else {
        statusEl.textContent = "Hoàn tất.";
        statusEl.style.color = "#28a745";
      }

      // Logic Button Google Maps
      let mapButtonHtml = "";
      if (data.kind === "địa điểm" && data.confidence > 0.8) {
          const mapUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(data.class_name)}`;
          mapButtonHtml = `
            <div class="map-btn-container">
                <a href="${mapUrl}" target="_blank" class="btn btn-map">
                    <i class="ri-map-pin-2-fill"></i> Chỉ đường tới ${data.class_name}
                </a>
            </div>
          `;
      }

      // Parse Markdown for Description
      let formattedMessage = data.message;
      if (typeof marked !== 'undefined') {
          formattedMessage = marked.parse(data.message);
      }

      resultTextEl.innerHTML = `
        <div class="story-content">
            ${formattedMessage}
        </div>
        ${mapButtonHtml}
        <p class="meta" style="color:#666; font-size:0.85rem; margin-top:20px; border-top:1px dashed #ddd; padding-top:10px; text-align: center;">
           Đối tượng: <strong>${data.class_name}</strong> • Độ tin cậy: ${(data.confidence * 100).toFixed(1)}%
        </p>
      `;

    } catch (err) {
      console.error(err);
      statusEl.textContent = "Lỗi kết nối.";
      statusEl.style.color = "red";
      if (submitBtn) submitBtn.disabled = false;
    }
  });
}

// ============================================================
// 4. CHATBOT LOGIC
// ============================================================
const chatPopup = document.getElementById("chat-popup");
const chatLauncherBtn = document.getElementById("chat-launcher-btn");
const chatCloseBtn = document.getElementById("chat-close-btn");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatMessages = document.getElementById("chat-messages");
const chatNav = document.getElementById("chat-nav");

function toggleChat() {
  chatPopup.classList.toggle("hidden");
}

if (chatLauncherBtn) chatLauncherBtn.addEventListener("click", toggleChat);
if (chatCloseBtn) chatCloseBtn.addEventListener("click", toggleChat);
if (chatNav) chatNav.addEventListener("click", (e) => { e.preventDefault(); toggleChat(); });

if (chatForm) {
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;

    appendMessage("user", text);
    chatInput.value = "";
    appendMessage("bot", "Đang tìm kiếm thông tin...");
    const thinkingBubble = chatMessages.lastElementChild.querySelector(".bubble");

    try {
      const resp = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await resp.json();
      
      if (data.success) {
        if (typeof marked !== 'undefined') {
           // Parse Markdown for Bot Reply
           thinkingBubble.innerHTML = marked.parse(data.answer);
        } else {
           thinkingBubble.textContent = data.answer;
        }
      } else {
        thinkingBubble.textContent = "Lỗi xử lý.";
      }
    } catch (err) {
      thinkingBubble.textContent = "Lỗi kết nối.";
    }
  });
}

function appendMessage(role, text) {
  const div = document.createElement("div");
  div.className = `chat-message ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  // Initial text content to avoid XSS before markdown parsing
  bubble.innerHTML = text; 
  div.appendChild(bubble);
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}