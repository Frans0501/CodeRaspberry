import os  
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import firestore
from google.oauth2 import service_account
from time import sleep
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load variabel lingkungan dari file .env
load_dotenv()

# Path ke file JSON kunci layanan Firebase
cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
firebase_admin.initialize_app(cred)

# Inisialisasi Firestore
db = firestore.Client()

# Konfigurasi firebase credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Main Collection
main_collection = db.collection(os.getenv("COLLECTION"))

# Sub Collection
subcollection_ref = main_collection.document(os.getenv("ID")).collection(os.getenv("SUBCOLLECTION"))
customerId = os.getenv("ID")

# Pengecekan koneksi ke Firebase
def check_connection_firebase():
    first_document = main_collection.limit(1).get()
    # Cek apakah berhasil mengambil dokumen
    if first_document:
        print("Terhubung dengan Firebase. Dokumen pertama:")
    else:
        print("Gagal terhubung dengan Firebase.")

# Membuat customer baru
def create_customer():
    # Buat format nama dokumen dari tanggal saat ini
    document_name = f"customer " +os.getenv("ID")

    # Referensi dokumen dengan nama sesuai tanggal saat ini
    kirim_doc = main_collection.document(document_name)

    # Data yang akan dikirim ke Firestore
    data = {
        'alamat':os.getenv("ALAMAT"),
        'id_pelanggan':os.getenv("ID"),
        'kota':os.getenv("KOTA"),
        'provinsi':os.getenv("PROVINSI"),
    }

    # Kirim data ke Firestore dengan nama dokumen sesuai tanggal saat ini
    kirim_doc.set(data)

    print("Data terkirim pada dokumen", document_name, ":", data)

# Mengirim Data ke SubCollection
def send_data(collection,id,kWh ):
    nameDoc, kwh_last_month = get_last_data(collection,id)
    subcollection_ref = main_collection.document(nameDoc).collection(os.getenv("SUBCOLLECTION"))
    
    # Waktu sekarang
    current_time = datetime.now()

    # Buat format nama dokumen dari tanggal saat ini untuk tempat menyimpan data
    document_name = current_time.strftime("%Y-%m-%d-%H-%M-%S")

    # Referensi dokumen dengan nama sesuai tanggal saat ini di dalam subkoleksi
    kirim_doc = subcollection_ref.document(document_name)

    # Variable deadline pembayaran
    time_deadline = current_time + timedelta(days=14)
    deadline = time_deadline.strftime("%d-%m-%Y")

    # Variable total pembayaran
    gap_kwh = kWh - kwh_last_month
    total_price = int(gap_kwh * 1444.70)

    # Data yang akan dikirim ke Firestore
    data = {
        'timestamp': current_time,
        'deadline' : deadline,
        'total_kwh_this_month': kWh,
        'gap_kwh' : gap_kwh,
        'total_kwh_last_month':kwh_last_month,
        'total_price' : total_price,
        'status': False
    }

    # Kirim data ke Firestore dengan nama dokumen sesuai tanggal saat ini di dalam subkoleksi
    kirim_doc.set(data)
    print("Dokumen name :", document_name, "subkoleksi:", data)
    
# Mendapatkan Data terakhir dari Subcollection
def get_last_data(collection, id):
    # Ambil semua dokumen dari koleksi yang diberikan
    all_docs_id = collection.stream()
    all_docs = collection.stream()

    # Check apakah id pelanggan sudah ada?
    customer_found = False
    for docId in all_docs_id:
        dataId = docId.to_dict()
        if (dataId.get('id_pelanggan') == id):
            customer_found = True
            break

    if not customer_found:
        create_customer()

    # Mengambil semua data dalam document
    for doc in all_docs:
        # Tampilkan data dari dokumen
        data = doc.to_dict()
        if data.get('id_pelanggan') == id:  
            # Ambil semua subkoleksi dari dokumen
            subcollections = list(doc.reference.collections())
            nameDoc = doc.id
            # Jika terdapat data dalam subkoleksi
            if subcollections:
                # Iterasi melalui setiap subkoleksi
                for subcollection in subcollections:
                    # Ambil semua dokumen dari subkoleksi
                    subcollection_docs = subcollection.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).stream()
                    # Iterasi melalui setiap dokumen dalam subkoleksi
                    for sub_doc in subcollection_docs:
                        last_data_subCollection = sub_doc.to_dict()
                        last_month = last_data_subCollection.get("total_kwh_this_month")
            else:
                last_month = 0
            return nameDoc, last_month
    print("Data tidak ditemukan")
    return None

#Run Program
# if __name__ == "__main__":
    # check_connection_firebase()
    # send_data(main_collection,customerId,1100)
    # get_last_data(main_collection,customerId)