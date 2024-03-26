import cv2
import os
import pytesseract
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import datetime
from dotenv import load_dotenv 
from codeFirebase import main_collection,customerId,send_data

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

# Menyusun nama file yang akan disimpan
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
    # cv2.imwrite(filename, preprocessed_image)
    print("Image captured and saved as:", filename)

    return adjusted_image
    # return preprocessed_image

# OCR Image
def ocr_image(captured_image):
    result_ocr = pytesseract.image_to_string(captured_image)

    # Memisahkan hasil dari OCR dan memasukannya ke array
    text_array = result_ocr.split()

    print("OCR Result = ")
    print(text_array)

    kWh = None
    if text_array:
        try:
            # # Mencari indeks dengan panjang terpanjang
            # max_length_index = max(range(len(text_array)), key=lambda i: len(text_array[i]))

            # # Mencetak indeks dan kata dengan panjang terpanjang
            # print("Index dengan panjang terpanjang:", max_length_index)
            # print("Kata dengan panjang terpanjang:", text_array[max_length_index])
            # print("index yang terpanjang", len(text_array[max_length_index]))

            # Mencari total kwh
            index_length_5 = [i for i, word in enumerate(text_array) if len(word) == 5]
            if index_length_5:
                # print("Index dengan panjang 5:", index_length_5)
                print("Total kWh Listrik:", text_array[index_length_5[0]])
                total_kwh = int(text_array[index_length_5[0]])
            else:
                print("tidak ditemukan total kWh Listrik")

            # Mencari id pelanggan
            index_length_8 = [i for i, word in enumerate(text_array) if len(word) == 8]
            if index_length_8:
                # print("Index dengan panjang 8:", index_length_8)
                print("Id Pelanggan:", text_array[index_length_8[0]])
                id_customer = text_array[index_length_8[0]]
            else:
                print("tidak ditemukan Id Pelanggan")

            if index_length_5 and index_length_8:
                print("1")
                send_data(main_collection,id_customer,total_kwh)
            elif index_length_5 and not index_length_8:
                print("2")
                send_data(main_collection,customerId,total_kwh)
            else:
                print("Terjadi kesalahan saat melakukan ekstraksi gambar")
            # kWh = int(text_array[max_length_index])
            # send_data(main_collection,customerId,kWh)
        except ValueError:
            print("Teks yang terbaca tidak valid untuk diubah menjadi bilangan bulat.")
    else:
        print("Tidak ada teks yang berhasil diekstraksi dari gambar.")


# Memanggil fungsi untuk mengambil gambar dengan penyesuaian kecerahan
captured_image = capture_image_with_delay(camera, brightness, filename)

# Menjalankan OCR
ocr_image(captured_image)