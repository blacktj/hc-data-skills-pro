"""Tests for the PHI guard scanner."""

from pathlib import Path

from hcskills.guard import scan_paths, scan_text


class TestScanText:
    def test_detects_ssn(self):
        findings = scan_text("Patient SSN: 987-65-4320")
        assert any(f["pattern_name"] == "SSN" for f in findings)

    def test_detects_phone(self):
        findings = scan_text("Call: (555) 867-5309")
        assert any(f["pattern_name"] == "Phone number" for f in findings)

    def test_detects_email(self):
        findings = scan_text("Email: john.doe@hospital.org")
        assert any(f["pattern_name"] == "Email address" for f in findings)

    def test_detects_mrn(self):
        findings = scan_text("MRN: 123456789")
        assert any(f["pattern_name"] == "MRN-like ID (MRN prefix)" for f in findings)

    def test_detects_dob_label(self):
        findings = scan_text("DOB: 03/15/1985")
        assert any(f["pattern_name"] == "Date of birth with label" for f in findings)

    def test_detects_address(self):
        findings = scan_text("Lives at 742 Evergreen Terrace Ave")
        assert any(f["pattern_name"] == "Street address" for f in findings)

    def test_skips_phi_safe_comment(self):
        findings = scan_text("SSN: 999-99-9999  # phi-safe")
        assert len(findings) == 0

    def test_clean_text_no_findings(self):
        findings = scan_text("diagnosis_code,plan_type,gender\nE11.9,HMO,F")
        assert len(findings) == 0

    def test_detects_zip_plus_4(self):
        findings = scan_text("ZIP: 12345-6789")
        assert any(f["pattern_name"] == "ZIP+4 code" for f in findings)


class TestScanPaths:
    def test_scan_file_with_phi(self, tmp_path: Path):
        phi_file = tmp_path / "data.csv"
        phi_file.write_text("name,ssn\nFake Person,987-65-4320\n")
        findings = scan_paths([phi_file])
        assert len(findings) > 0

    def test_scan_clean_file(self, tmp_path: Path):
        clean_file = tmp_path / "clean.csv"
        clean_file.write_text("diagnosis_code,plan_type\nE11.9,HMO\n")
        findings = scan_paths([clean_file])
        assert len(findings) == 0

    def test_skip_binary(self, tmp_path: Path):
        bin_file = tmp_path / "image.png"
        bin_file.write_bytes(b"\x89PNG\r\n")
        findings = scan_paths([bin_file])
        assert len(findings) == 0
