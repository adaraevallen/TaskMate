from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import calendar
import json
import os
import time
import uuid

# ==========================================
# PENGATURAN APLIKASI TASKMATE
# ==========================================

app = Flask(__name__)
app.secret_key = os.environ.get(
    "TASKMATE_SECRET_KEY",
    "kunci-lokal-taskmate"
)

FOLDER = os.path.dirname(os.path.abspath(__file__))

TUGAS_FILE = os.path.join(FOLDER, "tugas.json")
KALENDER_FILE = os.path.join(FOLDER, "kalender.json")
FOKUS_FILE = os.path.join(FOLDER, "fokus.json")


# ==========================================
# FUNGSI MEMBACA DAN MENYIMPAN DATA
# ==========================================

def baca_data(lokasi):
    if not os.path.exists(lokasi):
        return []

    try:
        with open(lokasi, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, list) else []

    except (json.JSONDecodeError, OSError):
        return []


def simpan_data(lokasi, data):
    with open(lokasi, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


# ==========================================
# 1. HALAMAN DAFTAR TUGAS
# ==========================================

@app.route("/")
def index():
    tugas = baca_data(TUGAS_FILE)

    tugas.sort(
        key=lambda item: item.get("tenggat", "9999-12-31")
    )

    return render_template(
        "index.html",
        tugas=tugas
    )


@app.route("/tambah", methods=["POST"])
def tambah_tugas():
    judul = request.form.get("judul", "").strip()
    mata_kuliah = request.form.get("mata_kuliah", "").strip()
    tenggat = request.form.get("tenggat", "").strip()

    try:
        datetime.strptime(tenggat, "%Y-%m-%d")
        tanggal_valid = True
    except ValueError:
        tanggal_valid = False

    if judul and tanggal_valid:
        tugas = baca_data(TUGAS_FILE)

        tugas.append({
            "id": str(uuid.uuid4()),
            "judul": judul,
            "mata_kuliah": mata_kuliah or "Umum",
            "tenggat": tenggat,
            "selesai": False
        })

        simpan_data(TUGAS_FILE, tugas)

    return redirect(url_for("index"))


@app.route("/status/<task_id>", methods=["POST"])
def ubah_status(task_id):
    tugas = baca_data(TUGAS_FILE)

    for item in tugas:
        if item.get("id") == task_id:
            item["selesai"] = not item.get("selesai", False)
            break

    simpan_data(TUGAS_FILE, tugas)

    return redirect(url_for("index"))


@app.route("/hapus/<task_id>", methods=["POST"])
def hapus_tugas(task_id):
    tugas = [
        item for item in baca_data(TUGAS_FILE)
        if item.get("id") != task_id
    ]

    simpan_data(TUGAS_FILE, tugas)

    return redirect(url_for("index"))


# ==========================================
# 2. KALENDER AKADEMIK
# ==========================================

@app.route("/kalender")
def kalender():
    hari_ini = datetime.now().date()

    try:
        tahun = int(
            request.args.get("tahun", hari_ini.year)
        )

        bulan = int(
            request.args.get("bulan", hari_ini.month)
        )

        if not 1900 <= tahun <= 2200:
            raise ValueError

        if not 1 <= bulan <= 12:
            raise ValueError

    except ValueError:
        tahun = hari_ini.year
        bulan = hari_ini.month

    nama_bulan = [
        "Januari", "Februari", "Maret", "April",
        "Mei", "Juni", "Juli", "Agustus",
        "September", "Oktober", "November", "Desember"
    ]

    minggu = calendar.Calendar(
        firstweekday=6
    ).monthdayscalendar(tahun, bulan)

    agenda = [
        item for item in baca_data(KALENDER_FILE)
        if item.get("tanggal", "").startswith(
            f"{tahun:04d}-{bulan:02d}"
        )
    ]

    agenda_per_tanggal = {}

    for item in agenda:
        tanggal = item.get("tanggal", "")

        agenda_per_tanggal.setdefault(
            tanggal, []
        ).append(item)

    bulan_lalu = bulan - 1
    tahun_lalu = tahun

    if bulan_lalu == 0:
        bulan_lalu = 12
        tahun_lalu -= 1

    bulan_depan = bulan + 1
    tahun_depan = tahun

    if bulan_depan == 13:
        bulan_depan = 1
        tahun_depan += 1

    return render_template(
        "kalender.html",
        minggu=minggu,
        tahun=tahun,
        bulan=bulan,
        nama_bulan=nama_bulan[bulan - 1],
        agenda=agenda,
        agenda_per_tanggal=agenda_per_tanggal,
        bulan_lalu=bulan_lalu,
        tahun_lalu=tahun_lalu,
        bulan_depan=bulan_depan,
        tahun_depan=tahun_depan,
        hari_ini=hari_ini.isoformat()
    )


@app.route("/kalender/tambah", methods=["POST"])
def tambah_agenda():
    judul = request.form.get("judul", "").strip()
    tanggal = request.form.get("tanggal", "").strip()
    kategori = request.form.get("kategori", "Lainnya").strip()
    catatan = request.form.get("catatan", "").strip()

    try:
        datetime.strptime(tanggal, "%Y-%m-%d")
        tanggal_valid = True
    except ValueError:
        tanggal_valid = False

    if judul and tanggal_valid:
        agenda = baca_data(KALENDER_FILE)

        agenda.append({
            "id": str(uuid.uuid4()),
            "judul": judul,
            "tanggal": tanggal,
            "kategori": kategori or "Lainnya",
            "catatan": catatan
        })

        simpan_data(KALENDER_FILE, agenda)

        return redirect(
            url_for(
                "kalender",
                tahun=int(tanggal[:4]),
                bulan=int(tanggal[5:7])
            )
        )

    return redirect(url_for("kalender"))


@app.route("/kalender/hapus/<agenda_id>", methods=["POST"])
def hapus_agenda(agenda_id):
    agenda = [
        item for item in baca_data(KALENDER_FILE)
        if item.get("id") != agenda_id
    ]

    simpan_data(KALENDER_FILE, agenda)

    return redirect(url_for("kalender"))


# ==========================================
# 3. TIMER BELAJAR
# ==========================================

@app.route("/fokus")
def fokus():
    sekarang = time.time()

    deadline = session.get("timer_deadline")
    jenis = session.get("timer_jenis", "Belajar")

    berjalan = deadline is not None
    sisa = 0

    if berjalan:
        sisa = max(0, int(deadline - sekarang))

        if sisa == 0:
            durasi = 25 if jenis == "Belajar" else 5

            riwayat = baca_data(FOKUS_FILE)

            riwayat.append({
                "id": str(uuid.uuid4()),
                "jenis": jenis,
                "durasi": durasi,
                "waktu": datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                )
            })

            simpan_data(FOKUS_FILE, riwayat)

            session.pop("timer_deadline", None)
            session.pop("timer_jenis", None)

            return redirect(url_for("fokus"))

    menit = sisa // 60
    detik = sisa % 60

    riwayat = baca_data(FOKUS_FILE)

    riwayat.sort(
        key=lambda item: item.get("waktu", ""),
        reverse=True
    )

    return render_template(
        "fokus.html",
        jenis=jenis,
        berjalan=berjalan,
        menit=menit,
        detik=detik,
        riwayat=riwayat[:10]
    )


@app.route("/fokus/mulai", methods=["POST"])
def mulai_fokus():
    jenis = request.form.get("jenis", "Belajar")

    if jenis not in ["Belajar", "Istirahat"]:
        jenis = "Belajar"

    durasi = 25 if jenis == "Belajar" else 5

    session["timer_jenis"] = jenis
    session["timer_deadline"] = time.time() + durasi * 60

    return redirect(url_for("fokus"))


@app.route("/fokus/reset", methods=["POST"])
def reset_fokus():
    session.pop("timer_deadline", None)
    session.pop("timer_jenis", None)

    return redirect(url_for("fokus"))


# ==========================================
# MENJALANKAN WEBSITE
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)