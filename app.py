import sqlite3
import openpyxl
from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

# Konstanta nama file Excel
FILE_NAME = "data_tagihan.xlsx"

# Inisialisasi aplikasi Flask
app = Flask(__name__)
app.secret_key = "your_secret_key"

def init_sqlite_db():
    conn = sqlite3.connect("billing_system.db")
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        nama TEXT,
        alamat TEXT,
        no_hp TEXT,
        email TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS obrolan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()



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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if not username or not password:
            flash("Username dan password tidak boleh kosong!")
            return redirect('/login')

        conn = sqlite3.connect("billing_system.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[2], password):
            session['username'] = username
            return redirect('/form')
        else:
            flash("Username atau password salah!")

        conn.close()
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
                INSERT INTO users (username, password, nama, alamat, no_hp, email) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, hashed_password, nama, alamat, no_hp, email))
            conn.commit()
            flash("Pendaftaran berhasil! Silakan login.")
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
    contract_no = request.form["contract_no"]
    date = request.form["date"]
    bdm_name = request.form["bdm_name"]
    nominal = int(request.form["nominal"])
    duration = int(request.form["duration"])
    vendor_name = request.form.get("vendor_name", "")
    phone = request.form.get("phone", "")

    monthly_payment = nominal // duration
    workbook = openpyxl.load_workbook(FILE_NAME)
    unpaid_sheet = workbook["Data Cicilan yang Belum Dibayar"]

    for month in range(1, duration + 1):
        unpaid_sheet.append([contract_no, date, bdm_name, month, monthly_payment, vendor_name, phone, "Belum Dibayar"])

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

    for row in unpaid_sheet.iter_rows(min_row=2, values_only=True):
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
        total_unpaid += row[4]

    paid_reports = [
        {
            "contract_no": row[0],
            "date": row[1],
            "name": row[2],
            "month": row[3],
            "nominal": row[4],
            "vendor": row[5],
            "phone": row[6],
            "status": "Pembayaran Selesai",
        }
        for row in paid_sheet.iter_rows(min_row=2, values_only=True)
    ]

    return render_template("report.html", unpaid_reports=unpaid_reports, paid_reports=paid_reports, total_unpaid=total_unpaid)

@app.route('/mark_paid', methods=['POST'])
def mark_paid():
    bdm_name = request.form["bdm_name"]
    month = int(request.form["month"])

    workbook = openpyxl.load_workbook(FILE_NAME)
    unpaid_sheet = workbook["Data Cicilan yang Belum Dibayar"]
    paid_sheet = workbook["Data Cicilan yang Sudah Dibayar"]

    for row in unpaid_sheet.iter_rows(min_row=2, values_only=False):
        if row[2].value == bdm_name and row[3].value == month:
            data = [cell.value for cell in row]
            # Ubah status pembayaran menjadi "Pembayaran Selesai"
            data[-1] = "Pembayaran Selesai"
            paid_sheet.append(data)
            unpaid_sheet.delete_rows(row[0].row)
            workbook.save(FILE_NAME)
            flash("Data berhasil dipindahkan ke laporan cicilan yang sudah dibayar.")
            return redirect('/report')

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

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
