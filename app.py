import openpyxl
from flask import Flask, render_template, request, redirect

FILE_NAME = "data_tagihan.xlsx"

app = Flask(__name__)

# Nama file Excel
FILE_NAME = "data_tagihan.xlsx"

# Inisialisasi workbook baru
def initialize_excel():
    try:
        # Jika file sudah ada, buka file tersebut
        workbook = openpyxl.load_workbook(FILE_NAME)
    except FileNotFoundError:
        # Jika file tidak ada, buat workbook baru
        workbook = openpyxl.Workbook()
        workbook.save(FILE_NAME)

    # Membuat sheet 'Laporan Bulanan' jika belum ada
    if "Laporan Bulanan" not in workbook.sheetnames:
        sheet = workbook.create_sheet("Laporan Bulanan")
        sheet.append(["Nama BDM", "Bulan", "Nominal Cicilan"])

    # Membuat sheet 'Perhitungan Otomatis' jika belum ada
    if "Perhitungan Otomatis" not in workbook.sheetnames:
        sheet = workbook.create_sheet("Perhitungan Otomatis")
        sheet.append(["Nama BDM", "Total Tagihan Tersisa"])

    # Menyimpan workbook
    workbook.save(FILE_NAME)

initialize_excel()

@app.route('/')
def form():
    return render_template("form.html")

@app.route('/submit', methods=["POST"])
def submit():
    bdm_name = request.form["bdm_name"]
    nominal = int(request.form["nominal"])
    duration = int(request.form["duration"])

    monthly_payment = nominal // duration

    workbook = openpyxl.load_workbook(FILE_NAME)
    laporan_sheet = workbook["Laporan Bulanan"]
    for month in range(1, duration + 1):
        laporan_sheet.append([bdm_name, month, monthly_payment])

    perhitungan_sheet = workbook["Perhitungan Otomatis"]
    perhitungan_sheet.append([bdm_name, nominal])

    workbook.save(FILE_NAME)

    return redirect('/report')

@app.route('/report')
def report():
    workbook = openpyxl.load_workbook(FILE_NAME)
    laporan_sheet = workbook["Laporan Bulanan"]
    reports = [
        {"name": row[0], "month": row[1], "nominal": row[2]}
        for row in laporan_sheet.iter_rows(min_row=2, values_only=True)
    ]

    perhitungan_sheet = workbook["Perhitungan Otomatis"]
    summaries = [
        {"bdm_name": row[0], "remaining": row[1]}
        for row in perhitungan_sheet.iter_rows(min_row=2, values_only=True)
    ]

    return render_template("report.html", reports=reports, summaries=summaries)

@app.route('/mark_paid', methods=["POST"])
def mark_paid():
    bdm_name = request.form["bdm_name"]
    nominal = int(request.form["nominal"])

    workbook = openpyxl.load_workbook(FILE_NAME)
    perhitungan_sheet = workbook["Perhitungan Otomatis"]
    for row in perhitungan_sheet.iter_rows(min_row=2):
        if row[0].value == bdm_name:
            row[1].value -= nominal
            break

    workbook.save(FILE_NAME)

    return redirect('/report')

if __name__ == "__main__":
    app.run(debug=True)
