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

DATA_DIR = "data"


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
        return f"{self._nama}  [faktor: {self._faktor_emisi} kg CO\u2082/km]"


class Motor(Kendaraan):

    _TABEL: list[tuple] = [
        (150,          "Motor Kecil",  0.055),
        (251,          "Motor Sedang", 0.075),
        (float("inf"), "Motor Besar",  0.095),
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
        self._kendaraan    = kendaraan
        self._jumlah_unit  = jumlah_unit
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
        entri._total_km  = data.get("total_km", 0.0)
        entri._log_harian = data.get("log", [])
        return entri


class EmissionTracker:

    def __init__(self, pengguna) -> None:
        self._pengguna = pengguna
        self._entri:   list[EntriKendaraan] = []
        self._riwayat: list[dict] = []

    @property
    def entri(self) -> list:
        return self._entri

    @property
    def riwayat(self) -> list:
        return self._riwayat

    def _data_file(self) -> str:
        os.makedirs(DATA_DIR, exist_ok=True)
        safe = "".join(
            c for c in self._pengguna.username
            if c.isalnum() or c in ("-", "_")
        )
        return os.path.join(DATA_DIR, f"{safe or 'guest'}.json")

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
            batas  = std["batas_km_minggu"]
            rasio  = km_eff / batas if batas > 0 else 0.0
            if rasio <= 0.8:
                status = "AMAN"
            elif rasio <= 1.0:
                status = "PERHATIAN"
            else:
                status = "KRITIS"
            hasil.append({
                "nama":       e.kendaraan.nama,
                "km_efektif": km_eff,
                "batas_km":   batas,
                "rasio":      round(rasio, 2),
                "status":     status,
            })
        return hasil

    def simpan_snapshot(self) -> None:
        now = datetime.now()
        self._riwayat.append({
            "tanggal":     now.strftime("%Y-%m-%d"),
            "minggu":      now.isocalendar()[1],
            "bulan":       now.month,
            "tahun":       now.year,
            "emisi_kg":    self.emisi_ternormalisasi(),
            "proyeksi_kg": self.proyeksi_tahunan(),
            "entri":       [e.ke_dict() for e in self._entri],
        })

    def bandingkan_periode(self, periode: str) -> dict | None:
        if not self._riwayat:
            return None
        now = datetime.now()
        cal = now.isocalendar()
        if periode == "minggu":
            mw = cal[1] - 1 if cal[1] > 1 else 52
            mt = cal[0] if cal[1] > 1 else cal[0] - 1
            cocok = [h for h in self._riwayat
                     if h["minggu"] == mw and h["tahun"] == mt]
        elif periode == "bulan":
            bm = now.month - 1 if now.month > 1 else 12
            bt = now.year if now.month > 1 else now.year - 1
            cocok = [h for h in self._riwayat
                     if h["bulan"] == bm and h["tahun"] == bt]
        elif periode == "tahun":
            cocok = [h for h in self._riwayat if h["tahun"] == now.year - 1]
        else:
            return None

        if not cocok:
            return None

        emisi_lama = cocok[-1]["emisi_kg"]
        emisi_skrg = self.emisi_ternormalisasi()
        selisih    = round(emisi_skrg - emisi_lama, 4)
        persen     = round(selisih / emisi_lama * 100, 1) if emisi_lama > 0 else 0.0
        tren       = "naik" if selisih > 0 else ("turun" if selisih < 0 else "sama")
        return {
            "periode":    periode,
            "emisi_skrg": emisi_skrg,
            "emisi_lama": emisi_lama,
            "selisih":    selisih,
            "persen":     persen,
            "tren":       tren,
        }

    def reset_data(self) -> None:
        if any(e.total_km > 0 for e in self._entri):
            self.simpan_snapshot()
        for e in self._entri:
            e.reset()

    def simpan_ke_file(self) -> None:
        data = {
            "username":     self._pengguna.username,
            "account_type": self._pengguna.account_type,
            "entri":        [e.ke_dict() for e in self._entri],
            "riwayat":      self._riwayat,
        }
        try:
            with open(self._data_file(), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as err:
            print(f"[Peringatan] Gagal menyimpan: {err}")

    def muat_dari_file(self) -> bool:
        path = self._data_file()
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
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
        self._username     = username
        self._account_type = account_type
        self._tracker      = EmissionTracker(self)

    @property
    def username(self) -> str:
        return self._username

    @property
    def account_type(self) -> str:
        return self._account_type

    @property
    def tracker(self) -> EmissionTracker:
        return self._tracker


class PrivateUser(User):
    def __init__(self, username: str) -> None:
        super().__init__(username, "Pribadi")


class CorporateUser(User):
    def __init__(self, username: str) -> None:
        super().__init__(username, "Perusahaan/Mitra")