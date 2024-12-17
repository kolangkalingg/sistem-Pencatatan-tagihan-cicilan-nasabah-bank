import sqlite3
import openpyxl
from flask import Flask, render_template, request, redirect, session, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps


# Konstanta nama file Excel
FILE_NAME = "data_tagihan.xlsx"

# Inisialisasi aplikasi Flask
app = Flask(__name__)
app.secret_key = "your_secret_key"

def init_sqlite_db():
    conn = sqlite3.connect("billing_system.db")
    cursor = conn.cursor()

    # Membuat tabel users jika belum ada
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        nama TEXT,
        alamat TEXT,
        no_hp TEXT,
        email TEXT,
        role TEXT DEFAULT 'user',  -- Tambahkan kolom role dengan default 'user'
        approved INTEGER DEFAULT 0 -- Tambahkan kolom approved dengan default 0 (belum disetujui)
    )''')

    # Membuat tabel obrolan jika belum ada
    cursor.execute('''CREATE TABLE IF NOT EXISTS obrolan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()
    add_default_admin()

def add_default_admin():
    conn = sqlite3.connect("billing_system.db")
    cursor = conn.cursor()

    # Periksa apakah admin sudah ada
    cursor.execute("SELECT * FROM users WHERE role = 'admin'")
    admin = cursor.fetchone()

    if not admin:
        hashed_password = generate_password_hash("admin123")  # Password default
        cursor.execute('''
            INSERT INTO users (username, password, nama, alamat, no_hp, email, role, approved)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ("admin", hashed_password, "Admin", "Admin Address", "1234567890", "admin@example.com", "admin", 1))
        conn.commit()

    conn.close()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session.get('role') != 'admin':
            flash("Hanya admin yang dapat mengakses halaman ini.")
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

def initialize_excel():
    try:
        workbook = openpyxl.load_workbook(FILE_NAME)
    except FileNotFoundError:
        workbook = openpyxl.Workbook()

    if "Data Cicilan yang Belum Dibayar" not in workbook.sheetnames:
        sheet = workbook.create_sheet("Data Cicilan yang Belum Dibayar")
        sheet.append([
            "No Kontrak", "Hari dan Tanggal", "Nama BDM", 
            "Bulan", "Nominal Cicilan", "Vendor", 
            "No HP", "Status Pembayaran"
        ])

    if "Data Cicilan yang Sudah Dibayar" not in workbook.sheetnames:
        sheet = workbook.create_sheet("Data Cicilan yang Sudah Dibayar")
        sheet.append([
            "No Kontrak", "Hari dan Tanggal", "Nama BDM", 
            "Bulan", "Nominal Cicilan", "Vendor", 
            "No HP", "Status Pembayaran"
        ])

    workbook.save(FILE_NAME)

init_sqlite_db()
initialize_excel()

def validate_row(row):
    """
    Validates a row of data to ensure all required fields are present and valid.
    Returns True if valid, False otherwise.
    """
    try:
        if row[0] is None or not isinstance(row[0], (int, str)):  # Contract No
            return False
        if row[1] is not None and not isinstance(row[1], str):  # Date
            return False
        if row[4] is not None and not isinstance(row[4], (int, float)):  # Nominal
            return False
        return True
    except IndexError:
        return False

def update_calculation_sheet():
    workbook = openpyxl.load_workbook(FILE_NAME)

    # Jika sheet belum ada, buat sheet baru
    if "Perhitungan Otomatis" not in workbook.sheetnames:
        calc_sheet = workbook.create_sheet("Perhitungan Otomatis")
        calc_sheet.append(["Nama BDM", "Sisa Bulan", "Sisa Nominal"])

    calc_sheet = workbook["Perhitungan Otomatis"]
    unpaid_sheet = workbook["Data Cicilan yang Belum Dibayar"]

    # Reset isi sheet "Perhitungan Otomatis"
    calc_sheet.delete_rows(2, calc_sheet.max_row)

    # Hitung total per BDM
    bdm_data = {}
    for row in unpaid_sheet.iter_rows(min_row=2, values_only=True):
        if row[2] is None or row[4] is None:
            continue
        bdm_name = row[2]
        nominal = row[4]

        if bdm_name in bdm_data:
            bdm_data[bdm_name]["sisa_bulan"] += 1
            bdm_data[bdm_name]["sisa_nominal"] += nominal
        else:
            bdm_data[bdm_name] = {"sisa_bulan": 1, "sisa_nominal": nominal}

    # Tambahkan hasil ke sheet
    for bdm, data in bdm_data.items():
        calc_sheet.append([bdm, data["sisa_bulan"], data["sisa_nominal"]])

    workbook.save(FILE_NAME)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect("billing_system.db")
        cursor = conn.cursor()

        cursor.execute("SELECT id, username, password, role, approved FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            if user[4] == 1:  # Cek apakah pengguna sudah disetujui
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[3]
                flash("Login berhasil!")
                return redirect('/')
            else:
                flash("Akun Anda belum disetujui oleh admin.")
        else:
            flash("Username atau password salah!")
    return render_template("login.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        nama = request.form['nama'].strip()
        alamat = request.form['alamat'].strip()
        no_hp = request.form['no_hp'].strip()
        email = request.form['email'].strip()

        if not username or not password or not nama or not alamat or not no_hp or not email:
            flash("Semua field harus diisi!")
            return redirect('/register')

        conn = sqlite3.connect("billing_system.db")
        cursor = conn.cursor()
        hashed_password = generate_password_hash(password)

        try:
            cursor.execute('''
                INSERT INTO users (username, password, nama, alamat, no_hp, email, approved) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, hashed_password, nama, alamat, no_hp, email, 0))  # Default approved = 0
            conn.commit()
            flash("Pendaftaran berhasil! Tunggu persetujuan admin.")
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash("Username sudah terdaftar!")
        finally:
            conn.close()
    return render_template("register.html")



@app.route('/')
def index():
    if 'username' in session:
        return redirect('/form')
    return redirect('/login')

@app.route('/form')
def form():
    if 'username' not in session:
        return redirect('/login')

    conn = sqlite3.connect("billing_system.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nama, email FROM users WHERE username = ?", (session['username'],))
    user_info = cursor.fetchone()
    conn.close()

    return render_template("form.html", user_info=user_info)


@app.route('/submit', methods=["POST"])
def submit():
    if 'username' not in session:
        flash("Anda harus login untuk mengakses fitur ini.")
        return redirect('/login')

    try:
        # Ambil data form
        contract_no = request.form["contract_no"]
        date = request.form["date"]
        bdm_name = request.form["bdm_name"]
        nominal = int(request.form["nominal"])
        duration = int(request.form["duration"])
        vendor_name = request.form.get("vendor_name", "")
        phone = request.form.get("phone", "")

        # Hitung cicilan per bulan
        monthly_payment = nominal // duration

        # Load workbook dan sheet
        workbook = openpyxl.load_workbook(FILE_NAME)
        unpaid_sheet = workbook["Data Cicilan yang Belum Dibayar"]

        # Ambil nama user
        current_user = session['username']

        # Cari baris terakhir yang digunakan
        last_row = unpaid_sheet.max_row

        # Tambahkan nama user sebagai header
        header_row = last_row + 2
        unpaid_sheet.cell(row=header_row, column=1, value=f"Diinput oleh: {current_user}")
        unpaid_sheet.merge_cells(start_row=header_row, start_column=1, end_row=header_row, end_column=8)

        # Tambahkan data cicilan di bawah header
        for month in range(1, duration + 1):
            unpaid_sheet.append([
                contract_no, date, bdm_name, month, monthly_payment, vendor_name, phone, "Belum Dibayar"
            ])

        # Tambahkan spasi kosong (baris kosong) setelah data
        unpaid_sheet.append(["" for _ in range(8)])
        unpaid_sheet.append(["" for _ in range(8)])

        # Update sheet perhitungan otomatis
        update_calculation_sheet(workbook)

        # Simpan workbook
        workbook.save(FILE_NAME)
        flash("Data berhasil ditambahkan!")

    except Exception as e:
        flash(f"Terjadi kesalahan: {str(e)}")

    return redirect('/report')


def update_calculation_sheet(workbook):
    """
    Fungsi untuk memperbarui sheet "Perhitungan Otomatis" dengan total sisa bulan dan nominal.
    """
    if "Perhitungan Otomatis" not in workbook.sheetnames:
        calc_sheet = workbook.create_sheet("Perhitungan Otomatis")
        calc_sheet.append(["Nama BDM", "Sisa Bulan", "Sisa Nominal"])
    else:
        calc_sheet = workbook["Perhitungan Otomatis"]
        calc_sheet.delete_rows(2, calc_sheet.max_row)  # Reset isi sheet

    unpaid_sheet = workbook["Data Cicilan yang Belum Dibayar"]
    bdm_totals = {}

    # Hitung sisa bulan dan nominal untuk setiap BDM
    for row in unpaid_sheet.iter_rows(min_row=2, values_only=True):
        if not row or row[2] is None:
            continue
        bdm_name = row[2]
        nominal = row[4]

        if bdm_name in bdm_totals:
            bdm_totals[bdm_name]['sisa_bulan'] += 1
            bdm_totals[bdm_name]['sisa_nominal'] += nominal
        else:
            bdm_totals[bdm_name] = {'sisa_bulan': 1, 'sisa_nominal': nominal}

    # Masukkan hasil perhitungan ke sheet
    for bdm, data in bdm_totals.items():
        calc_sheet.append([bdm, data['sisa_bulan'], data['sisa_nominal']])

    workbook.save(FILE_NAME)
    flash("Data berhasil ditambahkan!")
    return redirect('/report')


@app.route('/report')
def report():
    if 'username' not in session:
        return redirect('/login')

    workbook = openpyxl.load_workbook(FILE_NAME)
    unpaid_sheet = workbook["Data Cicilan yang Belum Dibayar"]
    paid_sheet = workbook["Data Cicilan yang Sudah Dibayar"]

    unpaid_reports = []
    total_unpaid = 0

    for idx, row in enumerate(unpaid_sheet.iter_rows(min_row=2, values_only=True), start=2):
        if not validate_row(row):
            # Gantikan log_error dengan print jika ingin tetap melihat pesan error di konsol
            print(f"Invalid row in Unpaid Sheet at line {idx}: {row}")
            continue

        unpaid_reports.append({
            "contract_no": row[0],
            "date": row[1],
            "name": row[2],
            "month": row[3],
            "nominal": row[4],
            "vendor": row[5],
            "phone": row[6],
            "status": row[7],
        })
        total_unpaid += row[4] if row[4] is not None else 0

    paid_reports = []
    for idx, row in enumerate(paid_sheet.iter_rows(min_row=2, values_only=True), start=2):
    # Lewati baris yang mengandung "Diinput oleh"
        if row[0] and "Diinput oleh" in row[0]:
            continue  # Baris dilewati

        if not validate_row(row):
            print(f"Invalid row in Paid Sheet at line {idx}: {row}")
            continue

        paid_reports.append({
            "contract_no": row[0],
            "date": row[1],
            "name": row[2],
            "month": row[3],
            "nominal": row[4],
            "vendor": row[5],
            "phone": row[6],
            "status": "Pembayaran Selesai",
        })


    return render_template(
        "report.html", 
        unpaid_reports=unpaid_reports, 
        paid_reports=paid_reports, 
        total_unpaid=total_unpaid
    )


@app.route('/mark_paid', methods=['POST'])
def mark_paid():
    # Validasi session login
    if 'username' not in session:
        flash("Anda harus login untuk mengakses fitur ini.")
        return redirect('/login')

    # Ambil input dari form
    bdm_name = request.form["bdm_name"].strip()
    month = int(request.form["month"])
    current_user = session['username']  # Nama user yang sedang login

    # Buka workbook Excel
    workbook = openpyxl.load_workbook(FILE_NAME)
    unpaid_sheet = workbook.get_sheet_by_name("Data Cicilan yang Belum Dibayar")
    paid_sheet = workbook.get_sheet_by_name("Data Cicilan yang Sudah Dibayar")

    row_to_delete = None  # Untuk menyimpan baris yang akan dihapus
    data_to_transfer = None  # Untuk menyimpan data yang akan dipindahkan

    # Cari data cicilan di sheet "Data Cicilan yang Belum Dibayar"
    for row in unpaid_sheet.iter_rows(min_row=2, values_only=False):
        if row[2].value == bdm_name and row[3].value == month:
            # Ambil data dan tandai baris untuk dihapus
            data_to_transfer = [cell.value for cell in row]
            row_to_delete = row[0].row
            break

    # Jika data ditemukan
    if data_to_transfer and row_to_delete:
        # Tambahkan informasi "Diinput oleh" di sheet "Data Cicilan yang Sudah Dibayar"
        paid_sheet.append(["Diinput oleh: " + current_user] + [""] * 7)  # Header user
        paid_sheet.append(data_to_transfer[:-1] + ["Pembayaran Selesai"])  # Data pembayaran

        # Hapus baris di sheet "Data Cicilan yang Belum Dibayar"
        unpaid_sheet.delete_rows(row_to_delete)

        # Simpan workbook
        workbook.save(FILE_NAME)
        flash("Data berhasil dipindahkan ke laporan cicilan yang sudah dibayar.")
    else:
        flash("Data tidak ditemukan atau sudah dibayar.")

    return redirect('/report')


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session:
        return redirect('/login')

    conn = sqlite3.connect("billing_system.db")
    cursor = conn.cursor()

    if request.method == 'POST':
        message = request.form['message'].strip()
        if message:
            cursor.execute("INSERT INTO obrolan (username, message) VALUES (?, ?)", (session['username'], message))
            conn.commit()

    cursor.execute("SELECT username, message, timestamp FROM obrolan ORDER BY timestamp ASC")
    chat_history = cursor.fetchall()

    conn.close()
    return render_template("chat.html", chat_history=chat_history)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

@app.route('/admin_requests')
def admin_requests():
    if 'username' not in session or session.get('role') != 'admin':
        flash("Anda tidak memiliki akses ke halaman ini.")
        return redirect('/')

    conn = sqlite3.connect("billing_system.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE approved = 0")
    pending_users = cursor.fetchall()
    conn.close()

    return render_template("admin_requests.html", pending_users=pending_users)


@app.route('/approve_user/<int:user_id>', methods=['POST'])
def approve_user(user_id):
    if 'username' not in session or session.get('role') != 'admin':
        flash("Anda tidak memiliki akses untuk tindakan ini.")
        return redirect('/')  # Mengganti redirect('') dengan URL root yang masuk akal

    conn = sqlite3.connect("billing_system.db")
    cursor = conn.cursor()

    # Set kolom approved menjadi 1 untuk user yang sesuai
    cursor.execute("UPDATE users SET approved = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    flash("Pengguna berhasil disetujui.")
    return redirect('/admin_requests')


@app.route('/view_users')
@admin_required
def view_users():
    print("Fungsi view_users dipanggil!")  # Tambahkan ini untuk debugging
    conn = sqlite3.connect("billing_system.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()

    return render_template("view_users.html", users=users)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
