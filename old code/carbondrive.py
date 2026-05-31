from __future__ import annotations
import os
import json
from abc import ABC, abstractmethod
from datetime import datetime

STANDAR_NASIONAL: dict[str, dict] = {
    "Motor Kecil":  {"batas_km_minggu": 60,  "batas_emisi_tahun": 195},
    "Motor Sedang": {"batas_km_minggu": 90,  "batas_emisi_tahun": 290},
    "Motor Besar":  {"batas_km_minggu": 120, "batas_emisi_tahun": 430},
    "Mobil Bensin": {"batas_km_minggu": 350, "batas_emisi_tahun": 2800},
    "Mobil Diesel": {"batas_km_minggu": 350, "batas_emisi_tahun": 2600},
    "Truk":         {"batas_km_minggu": 600, "batas_emisi_tahun": 9100},
    "Bus":          {"batas_km_minggu": 800, "batas_emisi_tahun": 13200},
}
DATA_FILE = "carbondrive_data.json"


def garis(karakter: str = "=", panjang: int = 56) -> None:
    print(karakter * panjang)


def header(judul: str) -> None:
    garis()
    print(f"  {judul}")
    garis()


def tekan_enter() -> None:
    input("\n  [Tekan Enter untuk kembali ke menu...]")


class Kendaraan(ABC):

    def __init__(self, nama: str, faktor_emisi: float) -> None:
        self._nama = nama
        self._faktor_emisi = faktor_emisi

    @property
    def nama(self) -> str:
        return self._nama

    @property
    def faktor_emisi(self) -> float:
        return self._faktor_emisi

    def hitung_emisi(self, km: float) -> float:
        return round(km * self._faktor_emisi, 4)

    @abstractmethod
    def label_tipe(self) -> str:
        pass

    def __str__(self) -> str:
        return f"{self._nama}  [faktor: {self._faktor_emisi} kg CO₂/km]"


class Motor(Kendaraan):

    _TABEL: list[tuple] = [
        (150,        "Motor Kecil",  0.055),
        (251,        "Motor Sedang", 0.075),
        (float("inf"), "Motor Besar", 0.095),
    ]

    def __init__(self, cc: int, ada_modifikasi: bool = False) -> None:
        self._cc = cc
        self._ada_modifikasi = ada_modifikasi
        tipe, faktor = "Motor Kecil", 0.055
        for batas, label, f in self._TABEL:
            if cc < batas:
                tipe, faktor = label, f
                break
        self._tipe = tipe
        if ada_modifikasi:
            faktor = round(faktor * 1.20, 4)
        suffix = " *modif" if ada_modifikasi else ""
        super().__init__(f"{tipe} {cc}cc{suffix}", round(faktor, 4))

    @property
    def cc(self) -> int:
        return self._cc

    @property
    def ada_modifikasi(self) -> bool:
        return self._ada_modifikasi

    def label_tipe(self) -> str:
        return self._tipe


class MobilBensin(Kendaraan):

    def __init__(self, jumlah_penumpang: int = 1) -> None:
        self._jumlah_penumpang = jumlah_penumpang
        super().__init__(f"Mobil Bensin ({jumlah_penumpang} pnp)", 0.180)

    @property
    def jumlah_penumpang(self) -> int:
        return self._jumlah_penumpang

    def label_tipe(self) -> str:
        return "Mobil Bensin"


class MobilDiesel(Kendaraan):

    def __init__(self, jumlah_penumpang: int = 1) -> None:
        self._jumlah_penumpang = jumlah_penumpang
        super().__init__(f"Mobil Diesel ({jumlah_penumpang} pnp)", 0.165)

    @property
    def jumlah_penumpang(self) -> int:
        return self._jumlah_penumpang

    def label_tipe(self) -> str:
        return "Mobil Diesel"


class Truk(Kendaraan):

    def __init__(self, kapasitas_ton: float = 5.0) -> None:
        self._kapasitas_ton = kapasitas_ton
        super().__init__(f"Truk {kapasitas_ton}T", 0.350)

    @property
    def kapasitas_ton(self) -> float:
        return self._kapasitas_ton

    def label_tipe(self) -> str:
        return "Truk"


class Bus(Kendaraan):

    def __init__(self, kapasitas_kursi: int = 40) -> None:
        self._kapasitas_kursi = kapasitas_kursi
        super().__init__(f"Bus {kapasitas_kursi} kursi", 0.450)

    @property
    def kapasitas_kursi(self) -> int:
        return self._kapasitas_kursi

    def label_tipe(self) -> str:
        return "Bus"


class EntriKendaraan:

    def __init__(self, kendaraan: Kendaraan,
                 jumlah_unit: int = 1, jumlah_driver: int = 1) -> None:
        self._kendaraan = kendaraan
        self._jumlah_unit = jumlah_unit
        self._jumlah_driver = jumlah_driver
        self._total_km: float = 0.0
        self._log_harian: list = []

    @property
    def kendaraan(self) -> Kendaraan:
        return self._kendaraan

    @property
    def total_km(self) -> float:
        return self._total_km

    @property
    def jumlah_unit(self) -> int:
        return self._jumlah_unit

    @property
    def jumlah_driver(self) -> int:
        return self._jumlah_driver

    def tambah_km(self, km: float, tanggal: str = None) -> None:
        tanggal = tanggal or datetime.now().strftime("%Y-%m-%d")
        self._total_km = round(self._total_km + km, 2)
        self._log_harian.append({"tanggal": tanggal, "km": km})

    def km_efektif(self, tipe_akun: str) -> float:
        if tipe_akun == "Pribadi":
            return self._total_km
        return round(self._total_km / self._jumlah_driver, 2) \
            if self._jumlah_driver > 0 else 0.0

    def rata_km_per_driver(self) -> float:
        return round(self._total_km / self._jumlah_driver, 2) \
            if self._jumlah_driver > 0 else 0.0

    def emisi_total(self) -> float:
        return self._kendaraan.hitung_emisi(self._total_km)

    def emisi_efektif(self, tipe_akun: str) -> float:
        return self._kendaraan.hitung_emisi(self.km_efektif(tipe_akun))

    def reset(self) -> None:
        self._total_km = 0.0
        self._log_harian = []

    def ke_dict(self) -> dict:
        d: dict = {
            "tipe_kelas":    type(self._kendaraan).__name__,
            "jumlah_unit":   self._jumlah_unit,
            "jumlah_driver": self._jumlah_driver,
            "total_km":      self._total_km,
            "log":           self._log_harian,
        }
        k = self._kendaraan
        if isinstance(k, Motor):
            d.update({"cc": k.cc, "modifikasi": k.ada_modifikasi})
        elif isinstance(k, (MobilBensin, MobilDiesel)):
            d["pnp"] = k.jumlah_penumpang
        elif isinstance(k, Truk):
            d["kapasitas"] = k.kapasitas_ton
        elif isinstance(k, Bus):
            d["kapasitas"] = k.kapasitas_kursi
        return d

    @staticmethod
    def dari_dict(data: dict) -> EntriKendaraan:
        tipe = data["tipe_kelas"]
        if tipe == "Motor":
            k: Kendaraan = Motor(data["cc"], data.get("modifikasi", False))
        elif tipe == "MobilBensin":
            k = MobilBensin(data.get("pnp", 1))
        elif tipe == "MobilDiesel":
            k = MobilDiesel(data.get("pnp", 1))
        elif tipe == "Truk":
            k = Truk(data.get("kapasitas", 5.0))
        elif tipe == "Bus":
            k = Bus(data.get("kapasitas", 40))
        else:
            raise ValueError(f"Tipe kendaraan tidak dikenal: {tipe}")
        entri = EntriKendaraan(k, data["jumlah_unit"], data["jumlah_driver"])
        entri._total_km = data.get("total_km", 0.0)
        entri._log_harian = data.get("log", [])
        return entri


class EmissionTracker:

    def __init__(self, pengguna) -> None:
        self._pengguna = pengguna
        self._entri:    list[EntriKendaraan] = []
        self._riwayat:  list[dict] = []

    @property
    def entri(self) -> list:
        return self._entri

    @property
    def riwayat(self) -> list:
        return self._riwayat

    def tambah_entri(self, entri: EntriKendaraan) -> None:
        self._entri.append(entri)

    def input_jarak(self, idx: int, km: float, tanggal: str = None) -> bool:
        if 0 <= idx < len(self._entri):
            self._entri[idx].tambah_km(km, tanggal)
            return True
        return False

    def total_emisi_mingguan(self) -> float:
        return round(sum(e.emisi_total() for e in self._entri), 4)

    def emisi_ternormalisasi(self) -> float:
        return round(
            sum(e.emisi_efektif(self._pengguna.account_type)
                for e in self._entri), 4
        )

    def proyeksi_tahunan(self) -> float:
        return round(self.emisi_ternormalisasi() * 52, 2)

    def bandingkan_nasional(self) -> list:
        hasil = []
        for e in self._entri:
            std = STANDAR_NASIONAL.get(e.kendaraan.label_tipe())
            if not std:
                continue
            km_eff = e.km_efektif(self._pengguna.account_type)
            batas = std["batas_km_minggu"]
            rasio = km_eff / batas if batas > 0 else 0.0
            if rasio <= 0.8:
                status = "✅ AMAN"
            elif rasio <= 1.0:
                status = "⚠️  PERHATIAN"
            else:
                status = "❌ KRITIS"
            hasil.append({
                "nama":       e.kendaraan.nama,
                "km_efektif": km_eff,
                "batas_km":   batas,
                "rasio":      round(rasio, 2),
                "status":     status,
            })
        return hasil

    # -----------------------------------------------------------------
    # FIX LOGIKA: MENYIMPAN SNAPSHOT BERDASARKAN TOMBOL SAVE (MENU 4)
    # -----------------------------------------------------------------
    def simpan_snapshot(self) -> None:
        now = datetime.now()
        record = {
            "tanggal":     now.strftime("%Y-%m-%d %H:%M:%S"),
            "minggu":      now.isocalendar()[1],
            "bulan":       now.month,
            "tahun":       now.year,
            "emisi_kg":    self.emisi_ternormalisasi(),
            "proyeksi_kg": self.proyeksi_tahunan(),
            "status":      "Aktif (Dapat ditambah sebelum Reset)",
            "entri":       [e.ke_dict() for e in self._entri],
        }

        # Jika sebelumnya sudah pernah save di siklus yang sama, kita update recordnya agar tidak duplikat
        if self._riwayat and self._riwayat[-1]["status"] == "Aktif (Dapat ditambah sebelum Reset)":
            self._riwayat[-1] = record
            print("  [Sistem] 🔄 Berhasil memperbarui arsip riwayat minggu ini!")
        else:
            self._riwayat.append(record)
            print("  [Sistem] 💾 Data berhasil dicatat ke dalam riwayat database!")
        
        self.simpan_ke_file()

    def bandingkan_periode(self, periode: str) -> dict | None:
        if not self._riwayat:
            return None
        now = datetime.now()
        cal = now.isocalendar()
        if periode == "minggu":
            mw = cal[1] - 1 if cal[1] > 1 else 52
            mt = cal[0] if cal[1] > 1 else cal[0] - 1
            cocok = [h for h in self._riwayat if h["minggu"] == mw and h["tahun"] == mt]
        elif periode == "bulan":
            bm = now.month - 1 if now.month > 1 else 12
            bt = now.year if now.month > 1 else now.year - 1
            cocok = [h for h in self._riwayat if h["bulan"] == bm and h["tahun"] == bt]
        elif periode == "tahun":
            cocok = [h for h in self._riwayat if h["tahun"] == now.year - 1]
        else:
            return None

        # Jika tidak ada data spesifik minggu/bulan lalu, ambil data arsip paling terakhir yang tersedia
        if not cocok:
            cocok = [h for h in self._riwayat if h["status"] == "Final / Locked"]

        if not cocok:
            return None

        emisi_lama = cocok[-1]["emisi_kg"]
        emisi_skrg = self.emisi_ternormalisasi()
        selisih = round(emisi_skrg - emisi_lama, 4)
        persen = round(selisih / emisi_lama * 100, 1) if emisi_lama > 0 else 0.0
        tren = "naik ⬆️" if selisih > 0 else ("turun ⬇️" if selisih < 0 else "sama ➡️")
        return {
            "periode":    periode,
            "emisi_skrg": emisi_skrg,
            "emisi_lama": emisi_lama,
            "selisih":    selisih,
            "persen":     persen,
            "tren":       tren,
        }

    # -----------------------------------------------------------------
    # FIX LOGIKA: RESET HANYA UNTUK MEMBERSIHKAN LEMBAR KERJA BERJALAN
    # -----------------------------------------------------------------
    def reset_data(self) -> None:
        if self._riwayat and self._riwayat[-1]["status"] == "Aktif (Dapat ditambah sebelum Reset)":
            self._riwayat[-1]["status"] = "Final / Locked"
            
        for e in self._entri:
            e.reset()
        self.simpan_ke_file()

    def simpan_ke_file(self) -> None:
        data = {
            "username":     self._pengguna.username,
            "account_type": self._pengguna.account_type,
            "entri":        [e.ke_dict() for e in self._entri],
            "riwayat":      self._riwayat,
        }
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as err:
            print(f"  [Peringatan] Gagal menyimpan: {err}")

    def muat_dari_file(self) -> bool:
        if not os.path.exists(DATA_FILE):
            return False
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("username") != self._pengguna.username:
                return False
            if data.get("account_type") != self._pengguna.account_type:
                return False
            self._riwayat = data.get("riwayat", [])
            self._entri.clear()
            for ed in data.get("entri", []):
                try:
                    self._entri.append(EntriKendaraan.dari_dict(ed))
                except (ValueError, KeyError):
                    continue
            return True
        except (IOError, json.JSONDecodeError):
            return False


class User(ABC):
    def __init__(self, username: str, account_type: str) -> None:
        self._username = username
        self._account_type = account_type
        self._tracker = EmissionTracker(self)

    @property
    def username(self) -> str:
        return self._username

    @property
    def account_type(self) -> str:
        return self._account_type

    @abstractmethod
    def show_menu(self) -> None:
        pass

    @abstractmethod
    def jalankan(self) -> None:
        pass

    def _pilih_kendaraan_menu(self, judul: str) -> int | None:
        if not self._tracker.entri:
            print("\n  [Info] Belum ada kendaraan/armada terdaftar.")
            return None
        print(f"\n  {judul}:")
        for i, e in enumerate(self._tracker.entri, 1):
            print(f"  {i}. {e.kendaraan.nama:<34} (total: {e.total_km} km)")
        try:
            idx = int(input("  Pilih nomor: ")) - 1
            if not (0 <= idx < len(self._tracker.entri)):
                raise ValueError("Nomor tidak valid.")
            return idx
        except ValueError as err:
            print(f"  [Error] {err}")
            return None

    def _bandingkan_periode(self) -> None:
        header("BANDINGKAN DENGAN PERIODE LALU")
        print("  1. Minggu lalu / Siklus Terkunci Sebelumnya")
        print("  2. Bulan lalu")
        print("  3. Tahun lalu")
        try:
            p = int(input("  Pilih (1-3): "))
            periode = {1: "minggu", 2: "bulan", 3: "tahun"}.get(p)
            if not periode:
                raise ValueError("Pilihan tidak valid.")
        except ValueError as err:
            print(f"  [Error] {err}")
            tekan_enter()
            return

        hasil = self._tracker.bandingkan_periode(periode)
        if not hasil:
            print(f"\n  [Info] Tidak ada data arsip {periode} lalu di database.")
            print("         Silakan lakukan Simpan Siklus Mingguan (Menu 4) terlebih dahulu.")
            tekan_enter()
            return

        is_corp = self.account_type != "Pribadi"
        lbl_now = "Emisi/driver saat ini" if is_corp else "Emisi saat ini"
        lbl_lama = f"Emisi/driver {periode} lalu" if is_corp else f"Emisi {periode} lalu"
        garis("-")
        print(f"  Perbandingan emisi — {periode} lalu vs saat ini")
        garis("-")
        print(f"  {lbl_now:<32}: {hasil['emisi_skrg']:.4f} kg CO₂")
        print(f"  {lbl_lama:<32}: {hasil['emisi_lama']:.4f} kg CO₂")
        print(f"  {'Selisih':<32}: {hasil['selisih']:+.4f} kg CO₂")
        print(f"  {'Perubahan':<32}: {hasil['persen']:+.1f}%  →  {hasil['tren']}")
        tekan_enter()

    def _reset_data(self) -> None:
        if not any(e.total_km > 0 for e in self._tracker.entri):
            print("\n  [Info] Tidak ada data km berjalan yang perlu direset.")
            tekan_enter()
            return
        konfirmasi = input(
            "\n  [!] Reset akan MENGOSONGKAN seluruh log lembar kerja berjalan\n"
            "      untuk membuka buku catatan minggu baru.\n"
            "      Pastikan Anda sudah memilih Opsi Simpan (Menu 4) sebelum melakukan reset.\n"
            "      Lanjutkan? (y/n): "
        ).strip().lower()
        if konfirmasi == "y":
            self._tracker.reset_data()
            print("  ✅ Log berjalan dikosongkan! Anda siap memulai siklus minggu baru.")
        else:
            print("  Reset dibatalkan.")
        tekan_enter()


class PrivateUser(User):
    def __init__(self, username: str) -> None:
        super().__init__(username, "Pribadi")

    def show_menu(self) -> None:
        garis()
        print(f"  MENU AKUN PRIBADI  ·  {self.username}")
        garis()
        print("  1. Setup Kendaraan")
        print("  2. Input Jarak Tempuh Harian (km)")
        print("  3. Lihat Ringkasan Mingguan")
        print("  4. SIMPAN SIKLUS MINGGUAN & PROYEKSI TAHUNAN")
        print("  5. Bandingkan dengan Periode Lalu")
        print("  6. Reset Data / Buka Lembar Minggu Baru")
        print("  0. Keluar Aplikasi")
        garis()

    def _setup_kendaraan(self) -> None:
        header("SETUP KENDARAAN PRIBADI")
        print("  Pilih jenis kendaraan:")
        print("  1. Motor")
        print("  2. Mobil Bensin")
        print("  3. Mobil Diesel")
        print("  4. Truk")
        print("  5. Bus")
        try:
            pilihan = int(input("  Pilihan (1-5): "))
        except ValueError:
            print("  [Error] Masukkan angka 1-5.")
            tekan_enter()
            return

        kendaraan: Kendaraan | None = None
        try:
            if pilihan == 1:
                # --- REFERENSI CC MOTOR NYATA DI PASARAN INDONESIA ---
                print("\n  [INFO] Referensi Kapasitas CC Motor Populer:")
                print("  - 110 cc : Beat, Scoopy, Mio, Genio")
                print("  - 125 cc : Vario 125, Lexi, Jupiter, Supra X")
                print("  - 150/160 cc : NMAX, PCX, Aerox, Vario 160, Satria FU")
                print("  - 250 cc : Ninja 250, R25, CBR250RR, XMAX")
                print("  - > 500 cc : Moge (Harley, CB500X, ER6n)\n")
                
                cc = int(input("  Masukkan Kapasitas CC Mesin: "))
                if cc <= 0:
                    raise ValueError("CC harus bernilai positif.")
                modif = input("  Ada modifikasi mesin/knalpot? (y/n): ").strip().lower() == "y"
                kendaraan = Motor(cc, modif)
            elif pilihan == 2:
                pnp = int(input("  Rata-rata jumlah penumpang: "))
                kendaraan = MobilBensin(pnp)
            elif pilihan == 3:
                pnp = int(input("  Rata-rata jumlah penumpang: "))
                kendaraan = MobilDiesel(pnp)
            elif pilihan == 4:
                kap = float(input("  Kapasitas muatan (ton): "))
                kendaraan = Truk(kap)
            elif pilihan == 5:
                kursi = int(input("  Kapasitas penumpang (kursi): "))
                kendaraan = Bus(kursi)
            else:
                print("  [Error] Pilihan tidak valid.")
                tekan_enter()
                return
        except ValueError as err:
            print(f"  [Error] Input dibatalkan: {err}")
            tekan_enter()
            return

        if any(e.kendaraan.nama == kendaraan.nama for e in self._tracker.entri):
            print(f"  [Info] '{kendaraan.nama}' sudah terdaftar.")
            tekan_enter()
            return

        self._tracker.tambah_entri(EntriKendaraan(kendaraan))
        print(f"\n  ✅ Kendaraan ditambahkan: {kendaraan}")
        tekan_enter()

    def _input_jarak(self) -> None:
        idx = self._pilih_kendaraan_menu("Pilih kendaraan untuk input jarak hari ini")
        if idx is None:
            tekan_enter()
            return
        try:
            km = float(input("  Jarak hari ini (km): "))
            if km < 0:
                raise ValueError("Jarak tidak boleh negatif.")
            self._tracker.input_jarak(idx, km)
            e = self._tracker.entri[idx]
            print(f"\n  ✅ {km} km ditambahkan ke {e.kendaraan.nama}")
            print(f"     Total minggu ini: {e.total_km} km")
        except ValueError as err:
            print(f"  [Error] {err}")
        tekan_enter()

    def _lihat_ringkasan(self) -> None:
        if not self._tracker.entri:
            print("\n  [Info] Belum ada kendaraan terdaftar.")
            tekan_enter()
            return
        header("RINGKASAN MINGGUAN")
        print(f"  Pengguna  : {self.username}  (Pribadi)")
        print(f"  Tanggal   : {datetime.now().strftime('%Y-%m-%d')}\n")

        print(f"  {'Kendaraan':<34} {'KM':>7}  {'Emisi (kg CO₂)':>15}")
        garis("-", 56)
        total_km = 0.0
        for e in self._tracker.entri:
            print(f"  {e.kendaraan.nama:<34} {e.total_km:>7.1f}  {e.emisi_total():>15.4f}")
            total_km += e.total_km
        garis("-", 56)
        print(f"  {'TOTAL':<34} {total_km:>7.1f}  {self._tracker.total_emisi_mingguan():>15.4f}")

        print(f"\n  Emisi minggu ini  : {self._tracker.emisi_ternormalisasi():.4f} kg CO₂")
        print(f"  Proyeksi / tahun  : {self._tracker.proyeksi_tahunan():.2f} kg CO₂")

        print(f"\n  STATUS vs. Standar Nasional (km/minggu):")
        garis("-", 56)
        for h in self._tracker.bandingkan_nasional():
            print(f"  {h['nama']:<32} {h['km_efektif']:>5.1f}/{h['batas_km']:<5} km  {h['status']}")
        tekan_enter()

    def _proyeksi_tahunan(self) -> None:
        if not any(e.total_km > 0 for e in self._tracker.entri):
            print("\n  [Info] Belum ada data jarak berjalan. Input jarak terlebih dahulu.")
            tekan_enter()
            return
        header("SIMPAN DATA & PROYEKSI TAHUNAN")
        
        # Eksekusi penyimpanan ke list riwayat (Ide barumu)
        self._tracker.simpan_snapshot()
        
        print("\n  Basis Proyeksi: emisi minggu ini × 52 minggu\n")
        for e in self._tracker.entri:
            emi = round(e.emisi_efektif(self.account_type) * 52, 2)
            batas = STANDAR_NASIONAL.get(e.kendaraan.label_tipe(), {}).get("batas_emisi_tahun")
            print(f"  {e.kendaraan.nama}")
            print(f"    KM/minggu      : {e.total_km:.1f} km")
            print(f"    Proyeksi/tahun : {emi:.2f} kg CO₂")
            if batas:
                st = "✅ AMAN" if emi <= batas else "❌ MELEWATI BATAS"
                print(f"    Batas nasional : {batas} kg CO₂/th  →  {st}")
            print()
        print(f"  TOTAL PROYEKSI AKTIF: {self._tracker.proyeksi_tahunan():.2f} kg CO₂/tahun")
        print("  *Petunjuk: Log berjalan aman disimpan, silakan input data susulan jika ada.")
        tekan_enter()

    def jalankan(self) -> None:
        if self._tracker.muat_dari_file():
            n = len(self._tracker.entri)
            print(f"\n  [Sistem] Data arsip dimuat. ({n} kendaraan, "
                  f"{len(self._tracker.riwayat)} snapshot riwayat ditemukan)")
        while True:
            self.show_menu()
            try:
                pilihan = int(input("  Pilihan: "))
            except ValueError:
                print("  [Error] Masukkan angka pilihan yang valid.")
                continue

            if pilihan == 0:
                self._tracker.simpan_ke_file()
                print(f"\n  Sampai jumpa, {self.username}! 🌱")
                break
            elif pilihan == 1:
                self._setup_kendaraan()
            elif pilihan == 2:
                self._input_jarak()
            elif pilihan == 3:
                self._lihat_ringkasan()
            elif pilihan == 4:
                self._proyeksi_tahunan()
            elif pilihan == 5:
                self._bandingkan_periode()
            elif pilihan == 6:
                self._reset_data()
            else:
                print("  [Error] Pilihan tidak tersedia.")


class CorporateUser(User):
    def __init__(self, username: str) -> None:
        super().__init__(username, "Perusahaan/Mitra")

    def show_menu(self) -> None:
        garis()
        print(f"  MENU AKUN MITRA  ·  {self.username}")
        garis()
        print("  1. Registrasi Armada Kendaraan")
        print("  2. Input Agregasi Jarak Harian (Total KM Armada)")
        print("  3. Lihat Ringkasan Mingguan Armada")
        print("  4. SIMPAN SIKLUS MINGGUAN & PROYEKSI TAHUNAN")
        print("  5. Bandingkan dengan Historis (Minggu/Bulan/Tahun)")
        print("  6. Reset Data / Buka Lembar Minggu Baru")
        print("  0. Keluar Aplikasi")
        garis()

    def _registrasi_armada(self) -> None:
        header("REGISTRASI ARMADA KENDARAAN")
        print("  Pilih jenis kendaraan:")
        print("  1. Motor Kecil  (< 150 cc)")
        print("  2. Motor Sedang (150–250 cc)")
        print("  3. Motor Besar  (> 250 cc)")
        print("  4. Mobil Bensin")
        print("  5. Mobil Diesel")
        print("  6. Truk")
        print("  7. Bus")
        try:
            pilihan = int(input("  Pilih (1-7): "))
            jml_unit = int(input("  Jumlah unit kendaraan jenis ini : "))
            jml_drv = int(input("  Jumlah driver untuk jenis ini   : "))
            if jml_unit <= 0 or jml_drv <= 0:
                raise ValueError("Jumlah unit dan driver harus > 0.")
        except ValueError as err:
            print(f"  [Error] {err}")
            tekan_enter()
            return

        kendaraan: Kendaraan | None = None
        _cc_preset = {1: 110, 2: 200, 3: 350}
        try:
            if pilihan in _cc_preset:
                modif = input("  Ada modifikasi mesin? (y/n): ").strip().lower() == "y"
                kendaraan = Motor(_cc_preset[pilihan], modif)
            elif pilihan == 4:
                kendaraan = MobilBensin()
            elif pilihan == 5:
                kendaraan = MobilDiesel()
            elif pilihan == 6:
                kap = float(input("  Kapasitas muatan (ton): "))
                kendaraan = Truk(kap)
            elif pilihan == 7:
                kursi = int(input("  Kapasitas penumpang: "))
                kendaraan = Bus(kursi)
            else:
                print("  [Error] Pilihan tidak valid.")
                tekan_enter()
                return
        except ValueError:
            print("  [Error] Nilai tidak valid.")
            tekan_enter()
            return

        if any(e.kendaraan.nama == kendaraan.nama for e in self._tracker.entri):
            print(f"  [Info] Armada '{kendaraan.nama}' sudah terdaftar.")
            tekan_enter()
            return

        self._tracker.tambah_entri(EntriKendaraan(kendaraan, jml_unit, jml_drv))
        print(f"\n  ✅ Armada ditambahkan: {kendaraan}")
        print(f"     Unit: {jml_unit}  ·  Driver: {jml_drv}")
        tekan_enter()

    def _input_agregasi_jarak(self) -> None:
        if not self._tracker.entri:
            print("\n  [Info] Belum ada armada. Registrasi armada dulu (Menu 1).")
            tekan_enter()
            return
        header("INPUT AGREGASI JARAK HARIAN ARMADA")
        for i, e in enumerate(self._tracker.entri, 1):
            print(f"  {i}. {e.kendaraan.nama:<30}  "
                  f"{e.jumlah_unit} unit / {e.jumlah_driver} driver  "
                  f"(total: {e.total_km} km)")
        try:
            idx = int(input("\n  Pilih armada (nomor): ")) - 1
            if not (0 <= idx < len(self._tracker.entri)):
                raise ValueError("Nomor tidak valid.")
            total_km = float(input("  Total KM seluruh armada jenis ini hari ini: "))
            if total_km < 0:
                raise ValueError("Jarak tidak boleh negatif.")
        except ValueError as err:
            print(f"  [Error] {err}")
            tekan_enter()
            return

        self._tracker.input_jarak(idx, total_km)
        e = self._tracker.entri[idx]
        print(f"\n  ✅ {total_km} km ditambahkan ke armada {e.kendaraan.nama}")
        print(f"     Akumulasi total  : {e.total_km:.1f} km")
        print(f"     Rata-rata/driver : {e.rata_km_per_driver():.1f} km/driver")
        tekan_enter()

    def _lihat_ringkasan(self) -> None:
        if not self._tracker.entri:
            print("\n  [Info] Belum ada armada terdaftar.")
            tekan_enter()
            return
        header("RINGKASAN MINGGUAN ARMADA")
        print(f"  Perusahaan : {self.username}")
        print(f"  Tanggal    : {datetime.now().strftime('%Y-%m-%d')}\n")

        print(f"  {'Armada':<26} {'Unit':>4} {'Drv':>4} {'KM Total':>10} {'KM/Drv':>8} {'Emisi(kg)':>10}")
        garis("-", 64)
        total_km_global = 0.0
        for e in self._tracker.entri:
            print(f"  {e.kendaraan.nama:<26}"
                  f"{e.jumlah_unit:>4}  {e.jumlah_driver:>4}"
                  f"{e.total_km:>10.1f}{e.rata_km_per_driver():>9.1f}"
                  f"{e.emisi_total():>10.4f}")
            total_km_global += e.total_km
        garis("-", 64)
        print(f"  {'TOTAL':<26}{'':>4}  {'':>4}"
              f"{total_km_global:>10.1f}{'':>9}"
              f"{self._tracker.total_emisi_mingguan():>10.4f}")

        print(f"\n  Emisi rata-rata/driver  : {self._tracker.emisi_ternormalisasi():.4f} kg CO₂")
        print(f"  Proyeksi/driver/tahun   : {self._tracker.proyeksi_tahunan():.2f} kg CO₂")

        print(f"\n  STATUS ARMADA vs. Standar Nasional (KM/driver/minggu):")
        garis("-", 64)
        for h in self._tracker.bandingkan_nasional():
            print(f"  {h['nama']:<32} {h['km_efektif']:>6.1f}/{h['batas_km']:<6} km  {h['status']}")
        tekan_enter()

    def _proyeksi_tahunan(self) -> None:
        if not any(e.total_km > 0 for e in self._tracker.entri):
            print("\n  [Info] Belum ada data KM armada.")
            tekan_enter()
            return
        header("SIMPAN DATA KORPORASI & PROYEKSI TAHUNAN")
        
        # Eksekusi penyimpanan ke list riwayat korporat
        self._tracker.simpan_snapshot()
        
        print("\n  Basis Proyeksi: emisi rata-rata/driver minggu ini × 52 minggu\n")
        for e in self._tracker.entri:
            emi = round(e.emisi_efektif(self.account_type) * 52, 2)
            batas = STANDAR_NASIONAL.get(e.kendaraan.label_tipe(), {}).get("batas_emisi_tahun")
            print(f"  {e.kendaraan.nama}  ({e.jumlah_unit} unit, {e.jumlah_driver} driver)")
            print(f"    KM total/minggu        : {e.total_km:.1f} km")
            print(f"    KM rata2/driver/minggu : {e.rata_km_per_driver():.1f} km")
            print(f"    Emisi/driver/minggu    : {e.emisi_efektif(self.account_type):.4f} kg CO₂")
            print(f"    Proyeksi/driver/tahun  : {emi:.2f} kg CO₂")
            if batas:
                st = "✅ AMAN" if emi <= batas else "❌ MELEWATI BATAS"
                print(f"    Batas nasional         : {batas} kg CO₂/th  →  {st}")
            print()
        print(f"  TOTAL PROYEKSI ARMADA: {self._tracker.proyeksi_tahunan():.2f} kg CO₂/driver/tahun")
        tekan_enter()

    def jalankan(self) -> None:
        if self._tracker.muat_dari_file():
            n = len(self._tracker.entri)
            print(f"\n  [Sistem] Data armada dimuat. ({n} jenis armada, "
                  f"{len(self._tracker.riwayat)} snapshot riwayat ditemukan)")
        while True:
            self.show_menu()
            try:
                pilihan = int(input("  Pilihan: "))
            except ValueError:
                print("  [Error] Masukkan angka.")
                continue

            if pilihan == 0:
                self._tracker.simpan_ke_file()
                print(f"\n  Sampai jumpa, {self.username}! 🌱")
                break
            elif pilihan == 1:
                self._registrasi_armada()
            elif pilihan == 2:
                self._input_agregasi_jarak()
            elif pilihan == 3:
                self._lihat_ringkasan()
            elif pilihan == 4:
                self._proyeksi_tahunan()
            elif pilihan == 5:
                self._bandingkan_periode()
            elif pilihan == 6:
                self._reset_data()
            else:
                print("  [Error] Pilihan tidak tersedia.")


def main_interface() -> None:
    os.system("cls" if os.name == "nt" else "clear")
    garis()
    print("    CARBONDRIVE TRACKER")
    print("    Sistem Pelacak Emisi Karbon Kendaraan")
    garis()

    username = input("  Nama Pengguna / Perusahaan: ").strip() or "Guest"

    active_user: User | None = None
    while active_user is None:
        print("\n  Pilih Tipe Akun:")
        print("  1. Pribadi (Individu)")
        print("  2. Perusahaan / Mitra Korporasi")
        try:
            pilihan = int(input("  Pilihan (1/2): "))
            if pilihan == 1:
                active_user = PrivateUser(username)
                print(f"\n  [Sistem] Berhasil masuk sebagai Akun Pribadi. 🧍")
            elif pilihan == 2:
                active_user = CorporateUser(username)
                print(f"\n  [Sistem] Berhasil masuk sebagai Akun Mitra Perusahaan. 🏢")
            else:
                print("  [Error] Masukkan 1 atau 2.")
        except ValueError:
            print("  [Input Error] Masukkan angka. Coba lagi.")

    active_user.jalankan()


if __name__ == "__main__":
    main_interface()