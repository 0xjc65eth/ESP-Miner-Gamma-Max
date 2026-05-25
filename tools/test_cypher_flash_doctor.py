#!/usr/bin/env python3

import unittest

import cypher_flash_doctor as doctor


class CypherFlashDoctorTest(unittest.TestCase):
    def test_detects_post_flash_mismatch_latency_and_errors(self):
        info = {
            "hostname": "Bitaxe",
            "ASICModel": "BM1368",
            "boardVersion": "Gamma",
            "version": "cypher-gamma-max-v0.6.2",
            "axeOSVersion": "7afa9af",
            "responseTime": 1498.9,
            "errorPercentage": 5.26,
            "isUsingFallbackStratum": 1,
            "sharesAccepted": 36,
            "sharesRejected": 2,
            "sharesRejectedReasons": [{"message": "Stale", "count": 2}],
            "temp": 74,
            "wifiRSSI": -78,
            "expectedHashrate": 1220,
            "hashRate_10m": 1120,
            "uptimeSeconds": 900,
        }

        findings = doctor.diagnose(info)
        codes = {finding.code for finding in findings}

        self.assertIn("VERSION_MISMATCH", codes)
        self.assertIn("HIGH_RESPONSE_TIME", codes)
        self.assertIn("HIGH_ASIC_ERROR", codes)
        self.assertIn("FALLBACK_POOL", codes)
        self.assertEqual(doctor.worst_severity(findings), "critical")

    def test_healthy_device_returns_ok(self):
        info = {
            "hostname": "Bitaxe",
            "ASICModel": "BM1370",
            "boardVersion": "602",
            "version": "v2.13.1",
            "axeOSVersion": "v2.13.1",
            "responseTime": 80,
            "errorPercentage": 0.2,
            "isUsingFallbackStratum": 0,
            "sharesAccepted": 100,
            "sharesRejected": 0,
            "temp": 64,
            "wifiRSSI": -62,
            "expectedHashrate": 1200,
            "hashRate_10m": 1180,
            "uptimeSeconds": 900,
        }

        findings = doctor.diagnose(info)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].code, "HEALTHY")
        self.assertEqual(doctor.worst_severity(findings), "ok")


if __name__ == "__main__":
    unittest.main()
