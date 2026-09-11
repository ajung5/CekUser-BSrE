import unittest
from abc import ABC, abstractmethod
from unittest.mock import patch

import cek_nik_bsre_spreadseheet_merge as app


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


class FakeExecute:
    def __init__(self, payload):
        self.payload = payload

    def execute(self):
        return self.payload


class FakeSpreadsheets:
    def __init__(self, payload):
        self.payload = payload

    def get(self, **kwargs):
        return FakeExecute(self.payload)


class FakeSheetsService:
    def __init__(self, payload):
        self.payload = payload

    def spreadsheets(self):
        return FakeSpreadsheets(self.payload)


class FakeWorksheet:
    title = "Data"


class TestHelperFunctions(unittest.TestCase):
    def test_format_durasi(self):
        self.assertEqual(app.format_durasi(0), "00:00:00")
        self.assertEqual(app.format_durasi(61), "00:01:01")
        self.assertEqual(app.format_durasi(3661), "01:01:01")

    def test_normalisasi_tanggal_berbagai_format(self):
        expected = "2026-08-12"
        values = [
            "2026-08-12",
            "12-08-2026",
            "12/08/2026",
            "12-Agu-2026",
            "12-Aug-2026",
            "12 Agustus 2026",
            "12 August 2026",
        ]

        for value in values:
            with self.subTest(value=value):
                self.assertEqual(app.normalisasi_tanggal(value), expected)

    def test_nilai_tanggal_berubah(self):
        self.assertFalse(
            app.nilai_tanggal_berubah("12-Agu-2026", "2026-08-12")
        )
        self.assertTrue(
            app.nilai_tanggal_berubah("12-Agu-2026", "2027-08-12")
        )

    def test_nilai_teks_berubah(self):
        self.assertFalse(app.nilai_teks_berubah(" Verified ", "Verified"))
        self.assertTrue(app.nilai_teks_berubah("Issued", "Expired"))


class TestBSrEStatus(unittest.TestCase):
    def setUp(self):
        self.base_url = app.BASE_URL
        self.username = app.USERNAME
        self.password = app.PASSWORD

        app.BASE_URL = "https://example.test"
        app.USERNAME = "user"
        app.PASSWORD = "pass"

    def tearDown(self):
        app.BASE_URL = self.base_url
        app.USERNAME = self.username
        app.PASSWORD = self.password

    @patch.object(app.requests, "get")
    def test_status_issue(self, mock_get):
        mock_get.return_value = FakeResponse(
            200,
            {"status": "ISSUE"},
        )

        result = app.cek_status_sertifikat("1234567890123456")

        self.assertTrue(result["update"])
        self.assertEqual(result["status_api"], "ISSUE")
        self.assertEqual(result["status_pengguna"], "Verified")
        self.assertEqual(result["status_sertifikat"], "Issued")

    @patch.object(app.requests, "get")
    def test_status_not_registered_tidak_update(self, mock_get):
        mock_get.return_value = FakeResponse(
            200,
            {"status": "NOT_REGISTERED"},
        )

        result = app.cek_status_sertifikat("1234567890123456")

        self.assertFalse(result["update"])
        self.assertEqual(result["status_api"], "NOT_REGISTERED")
        self.assertIsNone(result["status_pengguna"])
        self.assertIsNone(result["status_sertifikat"])


class TestBSrEProfile(unittest.TestCase):
    def setUp(self):
        self.base_url = app.BASE_URL
        self.username = app.USERNAME
        self.password = app.PASSWORD

        app.BASE_URL = "https://example.test"
        app.USERNAME = "user"
        app.PASSWORD = "pass"

    def tearDown(self):
        app.BASE_URL = self.base_url
        app.USERNAME = self.username
        app.PASSWORD = self.password

    @patch.object(app.requests, "get")
    def test_profile_memilih_sertifikat_terbaru(self, mock_get):
        mock_get.return_value = FakeResponse(
            200,
            {
                "success": True,
                "data": {
                    "sertifikat": [
                        {"berlaku_sampai": "12-08-2026"},
                        {"berlaku_sampai": "12-08-2028"},
                    ]
                },
            },
        )

        result = app.cek_profile_sertifikat("1234567890123456")

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["tanggal_terbit"], "2026-08-12")
        self.assertEqual(result["tanggal_berakhir"], "2028-08-12")

    @patch.object(app.requests, "get")
    def test_profile_tanpa_sertifikat(self, mock_get):
        mock_get.return_value = FakeResponse(
            200,
            {
                "success": True,
                "data": {"sertifikat": []},
            },
        )

        result = app.cek_profile_sertifikat("1234567890123456")

        self.assertEqual(result["status"], "NO_CERTIFICATE")
        self.assertEqual(result["tanggal_terbit"], "")
        self.assertEqual(result["tanggal_berakhir"], "")

    @patch.object(app.requests, "get")
    def test_profile_404(self, mock_get):
        mock_get.return_value = FakeResponse(404, {})

        result = app.cek_profile_sertifikat("1234567890123456")

        self.assertEqual(result["status"], "NOT_FOUND")
        self.assertEqual(result["tanggal_terbit"], "")
        self.assertEqual(result["tanggal_berakhir"], "")


class TestVisibleRows(unittest.TestCase):
    def test_ambil_row_terlihat(self):
        payload = {
            "sheets": [
                {
                    "data": [
                        {
                            "startRow": 0,
                            "rowMetadata": [
                                {},
                                {"hiddenByFilter": True},
                                {"hiddenByUser": True},
                                {},
                            ],
                        }
                    ]
                }
            ]
        }

        service = FakeSheetsService(payload)
        worksheet = FakeWorksheet()

        original_spreadsheet_id = app.SPREADSHEET_ID
        app.SPREADSHEET_ID = "test-spreadsheet"

        try:
            result = app.ambil_row_terlihat(service, worksheet)
        finally:
            app.SPREADSHEET_ID = original_spreadsheet_id

        self.assertEqual(result, [1, 4])


class self(ABC):
    @property
    @abstractmethod
    def name(self):
        """Return the instance name."""
        return self.__class__.__name__

    @abstractmethod
    def run(self):
        """Execute the concrete implementation."""
        return {"name": self.name, "status": "ready"}


class ConcreteSelf(self):
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    def run(self):
        return {"name": self._name, "status": "ready"}


if __name__ == "__main__":
    unittest.main()
