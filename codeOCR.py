import cv2
import os
import pytesseract
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import datetime
from dotenv import load_dotenv
from codeFirebase import main_collection, customerId, send_data

# Load variabel lingkungan dari file .env
load_dotenv()

# Inisialisasi kamera Raspberry Pi
camera = PiCamera()

# Mengatur resolusi gambar yang akan diambil
camera.resolution = (640, 480)

# Mengatur jumlah frame per detik untuk kamera
camera.framerate = 30

# Kecerahan di tempat yang terang
brightness = 65

# Kecerahan di tempat yang redup
# brightness = 155

# Mengambil data waktu sekarang
current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Tentukan lokasi atau direktori tempat menyimpan foto
path_to_directory = "/home/pi/Documents/main/image/"

# Membuat nama file yang akan disimpan
filename = f"{path_to_directory}{current_time}.jpg"

# Fungsi untuk mengatur kecerahan gambar
def adjust_brightness(image, brightness):
    # Convert gambar ke format YUV (YCbCr)
    image_yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
    # Menerapkan penyesuaian kecerahan
    image_yuv[:,:,0] = cv2.add(image_yuv[:,:,0], brightness)
    # Konversi gambar kembali ke format BGR
    return cv2.cvtColor(image_yuv, cv2.COLOR_YUV2BGR)

# Fungsi untuk mengambil gambar
def capture_image_with_delay(camera, brightness, filename):
    # Membuat objek untuk menangkap gambar dari kamera
    rawCapture = PiRGBArray(camera, size=(640, 480))
    camera.capture(rawCapture, format="bgr")
    image = rawCapture.array
    
    # Mengatur kecerahan gambar
    adjusted_image = adjust_brightness(image, brightness)
    # Menyimpan gambar yang telah diambil ke dalam file dengan nama tertentu
    cv2.imwrite(filename, adjusted_image)
    print("Image captured and saved as:", filename)
    return adjusted_image

# Preprocessing Image for OCR
def preprocess_image_for_ocr(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

# OCR Image
def ocr_image(captured_image, filename):
    preprocessed_image = preprocess_image_for_ocr(captured_image)                                               
    result_ocr = pytesseract.image_to_string(preprocessed_image)
    text_array = result_ocr.split()
    print("OCR Result = ")
    print(text_array)
    
    # Filter teks yang hanya berisi angka
    filtered_text_array = [word for word in text_array if word.isdigit()]
    
    print("Filtered OCR Result = ")
    print(filtered_text_array)
    
    return handle_ocr_result(filtered_text_array, filename)                                                                     

def handle_ocr_result(text_array,filename):
    if text_array:
        try:
            # Extract kWh and customer ID
            index_length_5 = [i for i, word in enumerate(text_array) if len(word) == 5]
            index_length_8 = [i for i, word in enumerate(text_array) if len(word) == 8]

            if index_length_5:
                total_kwh = int(text_array[index_length_5[0]])
                print("Total kWh Listrik:", total_kwh)
            else:
                print("tidak ditemukan total kWh Listrik")
                return False
            
            if index_length_8:
                id_customer = text_array[index_length_8[0]]
                print("Id Pelanggan:", id_customer)
            else:
                print("tidak ditemukan Id Pelanggan")
                return False
            
            # Send data to Firebase
            if index_length_5 and index_length_8:
                send_data(main_collection, id_customer, total_kwh, filename)
                return True
            elif index_length_5 and not index_length_8:
                send_data(main_collection, customerId, total_kwh, filename)
                return True
            else:
                print("Terjadi kesalahan saat melakukan ekstraksi gambar")
                return False 
            
        except ValueError:
            print("Teks yang terbaca tidak valid untuk diubah menjadi bilangan bulat.")
            return False
    else:
        print("Tidak ada teks yang berhasil diekstraksi dari gambar.")
        return False


success = False
count = 0
while not success and count < 10:
    captured_image = capture_image_with_delay(camera, brightness, filename)
    success = ocr_image(captured_image, filename)
    if not success:
        print("Gagal melakukan OCR, mencoba lagi...")
        print(count)
        count += 1
    
    if count == 10:
        time.sleep(86400)
        count+= 0
