from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import (
    PrivateUser, CorporateUser, EntriKendaraan,
    Motor, MobilBensin, MobilDiesel, Truk, Bus, STANDAR_NASIONAL
)

app = Flask(__name__)
app.secret_key = "carbondrive-secret-key-2024"

# Menyimpan objek User di memory selama server berjalan
# key: username, value: User object
_sessions: dict = {}


def current_user():
    username = session.get("username")
    return _sessions.get(username)


# ─── Auth ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if current_user():
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    username  = request.form.get("username", "").strip() or "Guest"
    tipe_akun = request.form.get("account_type", "1")

    user = PrivateUser(username) if tipe_akun == "1" else CorporateUser(username)
    user.tracker.muat_dari_file()
    _sessions[username] = user
    session["username"] = username

    flash(f"Selamat datang, {username}! 🌱", "success")
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    user = current_user()
    if user:
        user.tracker.simpan_ke_file()
        _sessions.pop(session.get("username"), None)
    session.clear()
    flash("Data tersimpan. Sampai jumpa!", "success")
    return redirect(url_for("index"))


# ─── Dashboard ───────────────────────────────────────────────────────────────

@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("index"))

    tracker     = user.tracker
    status_list = tracker.bandingkan_nasional()

    # Gabungkan entri dengan status nasionalnya
    entri_data = []
    for i, e in enumerate(tracker.entri):
        status_info = next(
            (s for s in status_list if s["nama"] == e.kendaraan.nama), None
        )
        entri_data.append({"idx": i, "entri": e, "status": status_info})

    # Proyeksi tahunan per kendaraan (hanya yang ada km-nya)
    proyeksi_per_kendaraan = []
    for e in tracker.entri:
        if e.total_km > 0:
            emi_tahun = round(e.emisi_efektif(user.account_type) * 52, 2)
            batas     = STANDAR_NASIONAL.get(
                e.kendaraan.label_tipe(), {}
            ).get("batas_emisi_tahun")
            proyeksi_per_kendaraan.append({
                "nama":         e.kendaraan.nama,
                "km_minggu":    e.total_km,
                "km_driver":    e.rata_km_per_driver() if user.account_type != "Pribadi" else None,
                "emisi_minggu": e.emisi_efektif(user.account_type),
                "emisi_tahun":  emi_tahun,
                "batas":        batas,
                "status_proj":  (
                    "AMAN" if batas and emi_tahun <= batas
                    else ("MELEWATI" if batas else None)
                ),
            })

    # Ada snapshot "Aktif" yang belum dikunci?
    ada_snapshot_aktif = (
        bool(tracker.riwayat) and
        tracker.riwayat[-1].get("status") == "Aktif"
    )

    # Ambil hasil compare dari session jika ada
    compare_hasil   = session.pop("compare_hasil", None)
    compare_periode = session.pop("compare_periode", None)

    return render_template(
        "dashboard.html",
        user=user,
        tracker=tracker,
        entri_data=entri_data,
        emisi_mingguan=tracker.emisi_ternormalisasi(),
        proyeksi=tracker.proyeksi_tahunan(),
        proyeksi_per_kendaraan=proyeksi_per_kendaraan,
        ada_snapshot_aktif=ada_snapshot_aktif,
        compare_hasil=compare_hasil,
        compare_periode=compare_periode,
        standar=STANDAR_NASIONAL,
    )


# ─── Tambah Kendaraan ────────────────────────────────────────────────────────

@app.route("/tambah_kendaraan", methods=["POST"])
def tambah_kendaraan():
    user = current_user()
    if not user:
        return redirect(url_for("index"))

    tipe = request.form.get("tipe", "")
    try:
        kendaraan = None

        if tipe == "motor":
            cc    = int(request.form.get("cc", 0))
            modif = request.form.get("modif") == "y"
            if cc <= 0:
                raise ValueError("CC mesin harus lebih dari 0.")
            kendaraan = Motor(cc, modif)
        elif tipe == "mobil_bensin":
            pnp = int(request.form.get("pnp", 1))
            kendaraan = MobilBensin(pnp)
        elif tipe == "mobil_diesel":
            pnp = int(request.form.get("pnp", 1))
            kendaraan = MobilDiesel(pnp)
        elif tipe == "truk":
            kap = float(request.form.get("kapasitas_truk", 5.0))
            kendaraan = Truk(kap)
        elif tipe == "bus":
            kursi = int(request.form.get("kapasitas_bus", 40))
            kendaraan = Bus(kursi)
        else:
            flash("Jenis kendaraan tidak valid.", "danger")
            return redirect(url_for("dashboard"))

        if any(e.kendaraan.nama == kendaraan.nama for e in user.tracker.entri):
            flash(f"Kendaraan '{kendaraan.nama}' sudah terdaftar.", "warning")
            return redirect(url_for("dashboard"))

        if user.account_type != "Pribadi":
            jml_unit = int(request.form.get("jml_unit", 1))
            jml_drv  = int(request.form.get("jml_driver", 1))
            if jml_unit <= 0 or jml_drv <= 0:
                raise ValueError("Jumlah unit dan driver harus lebih dari 0.")
            entri = EntriKendaraan(kendaraan, jml_unit, jml_drv)
        else:
            entri = EntriKendaraan(kendaraan)

        user.tracker.tambah_entri(entri)
        user.tracker.simpan_ke_file()
        flash(f"Kendaraan '{kendaraan.nama}' berhasil ditambahkan!", "success")

    except (ValueError, TypeError) as e:
        flash(f"Input tidak valid: {e}", "danger")

    return redirect(url_for("dashboard"))


# ─── Tambah KM ───────────────────────────────────────────────────────────────

@app.route("/tambah_km", methods=["POST"])
def tambah_km():
    user = current_user()
    if not user:
        return redirect(url_for("index"))

    try:
        idx = int(request.form.get("idx", -1))
        km  = float(request.form.get("km", 0))
        if km <= 0:
            raise ValueError("Jarak harus lebih dari 0.")

        if user.tracker.input_jarak(idx, km):
            nama = user.tracker.entri[idx].kendaraan.nama
            user.tracker.simpan_ke_file()
            flash(f"{km} km berhasil ditambahkan ke '{nama}'.", "success")
        else:
            flash("Kendaraan tidak ditemukan.", "danger")

    except (ValueError, TypeError) as e:
        flash(f"Input tidak valid: {e}", "danger")

    return redirect(url_for("dashboard"))


# ─── Simpan Siklus Mingguan ──────────────────────────────────────────────────

@app.route("/simpan_siklus", methods=["POST"])
def simpan_siklus():
    user = current_user()
    if not user:
        return redirect(url_for("index"))

    if not any(e.total_km > 0 for e in user.tracker.entri):
        flash("Belum ada data KM berjalan. Input jarak terlebih dahulu.", "warning")
        return redirect(url_for("dashboard"))

    result = user.tracker.simpan_snapshot()
    if result == "update":
        flash("Data siklus minggu ini berhasil diperbarui di riwayat. 🔄", "success")
    else:
        flash("Data siklus minggu ini berhasil disimpan ke riwayat! 💾", "success")

    return redirect(url_for("dashboard"))


# ─── Compare Periode ─────────────────────────────────────────────────────────

@app.route("/compare", methods=["POST"])
def compare():
    user = current_user()
    if not user:
        return redirect(url_for("index"))

    periode = request.form.get("periode", "minggu")
    hasil   = user.tracker.bandingkan_periode(periode)

    if hasil:
        session["compare_hasil"]   = hasil
        session["compare_periode"] = periode
    else:
        flash(
            "Tidak ada data arsip yang tersedia untuk dibandingkan. "
            "Lakukan Simpan Siklus (💾) terlebih dahulu, kemudian Reset untuk mengunci data.",
            "info"
        )

    return redirect(url_for("dashboard"))


# ─── Reset ───────────────────────────────────────────────────────────────────

@app.route("/reset", methods=["POST"])
def reset():
    user = current_user()
    if not user:
        return redirect(url_for("index"))

    if not any(e.total_km > 0 for e in user.tracker.entri):
        flash("Tidak ada data km yang perlu direset.", "info")
    else:
        user.tracker.reset_data()
        flash("Log berjalan dikosongkan. Siap memulai siklus minggu baru! ✅", "success")

    return redirect(url_for("dashboard"))


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)