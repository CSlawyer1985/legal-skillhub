import unittest
import os
import sys
import tempfile
import shutil
import csv

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from scripts.pdf_parser import (
    extract_trademark_dispatch_number,
    validate_trademark_dispatch_number,
    TRADEMARK_DISPATCH_NUMBER_RULES,
    TRADEMARK_DISPATCH_NUMBER_BHFS_RULES,
    process_trademark_file,
    detect_trademark_type,
)
from scripts.config import TRADEMARK_CSV_COLUMNS
from scripts.script1_process import _check_duplicate, _build_csv_record
from scripts.csv_manager import write_csv, read_csv, init_csv


class TestExtractTrademarkDispatchNumber(unittest.TestCase):
    def test_extract_zcsl(self):
        text = "TMZC73055497ZCSL01商标注册申请受理通知书"
        result = extract_trademark_dispatch_number(text)
        self.assertEqual(result, "TMZC73055497ZCSL01")

    def test_extract_jftz(self):
        text = "TMZC73055497JFTZ01商标注册申请缴费通知书"
        result = extract_trademark_dispatch_number(text)
        self.assertEqual(result, "TMZC73055497JFTZ01")

    def test_extract_bfbh(self):
        text = "TMZC73055497BFBH01商标部分驳回通知书"
        result = extract_trademark_dispatch_number(text)
        self.assertEqual(result, "TMZC73055497BFBH01")

    def test_extract_csgg(self):
        text = "TMZC73055497CSGG商标注册申请初步审定公告通知书"
        result = extract_trademark_dispatch_number(text)
        self.assertEqual(result, "TMZC73055497CSGG")

    def test_extract_bhtz(self):
        text = "TMZC73051073BHTZ01商标驳回通知书"
        result = extract_trademark_dispatch_number(text)
        self.assertEqual(result, "TMZC73051073BHTZ01")

    def test_extract_8digit_app_number(self):
        text = "TMZC12345678ZCSL02商标注册申请受理通知书"
        result = extract_trademark_dispatch_number(text)
        self.assertEqual(result, "TMZC12345678ZCSL02")

    def test_extract_no_match(self):
        text = "这是一段没有发文编号的普通文本"
        result = extract_trademark_dispatch_number(text)
        self.assertEqual(result, "")

    def test_extract_empty_string(self):
        result = extract_trademark_dispatch_number("")
        self.assertEqual(result, "")

    def test_extract_multiple_serial_digits(self):
        text = "TMZC73055497ZCSL123商标注册申请受理通知书"
        result = extract_trademark_dispatch_number(text)
        self.assertEqual(result, "TMZC73055497ZCSL123")

    def test_extract_in_longer_text(self):
        text = "国家知识产权局TMZC73055497BHTZ01根据商标法"
        result = extract_trademark_dispatch_number(text)
        self.assertEqual(result, "TMZC73055497BHTZ01")

    def test_extract_bhfs_csgg(self):
        text = "BHFS20240000151499CSGG01商标注册申请初步审定公告通知书"
        result = extract_trademark_dispatch_number(text)
        self.assertEqual(result, "BHFS20240000151499CSGG01")

    def test_extract_bhfs_in_longer_text(self):
        text = "国家知识产权局BHFS20240000151499CSGG01根据商标法"
        result = extract_trademark_dispatch_number(text)
        self.assertEqual(result, "BHFS20240000151499CSGG01")

    def test_extract_bhfs_without_serial_not_matched(self):
        text = "BHFS20240000151499CSGG商标注册申请初步审定公告通知书"
        result = extract_trademark_dispatch_number(text)
        self.assertEqual(result, "")

    def test_extract_tmzc_priority_over_bhfs(self):
        text = "TMZC73055497CSGGBHFS20240000151499CSGG01"
        result = extract_trademark_dispatch_number(text)
        self.assertEqual(result, "TMZC73055497CSGG")


class TestValidateTrademarkDispatchNumber(unittest.TestCase):
    def test_valid_zcsl(self):
        self.assertTrue(validate_trademark_dispatch_number(
            "TMZC73055497ZCSL01", "商标注册申请受理通知书"))

    def test_valid_jftz(self):
        self.assertTrue(validate_trademark_dispatch_number(
            "TMZC73055497JFTZ01", "商标注册申请缴费通知书"))

    def test_valid_bfbh(self):
        self.assertTrue(validate_trademark_dispatch_number(
            "TMZC73055497BFBH01", "商标部分驳回通知书"))

    def test_valid_csgg_no_serial(self):
        self.assertTrue(validate_trademark_dispatch_number(
            "TMZC73055497CSGG", "商标注册申请初步审定公告通知书"))

    def test_valid_bhtz(self):
        self.assertTrue(validate_trademark_dispatch_number(
            "TMZC73051073BHTZ01", "商标驳回通知书"))

    def test_invalid_csgg_with_serial(self):
        self.assertFalse(validate_trademark_dispatch_number(
            "TMZC73055497CSGG01", "商标注册申请初步审定公告通知书"))

    def test_invalid_zcsl_without_serial(self):
        self.assertFalse(validate_trademark_dispatch_number(
            "TMZC73055497ZCSL", "商标注册申请受理通知书"))

    def test_invalid_wrong_type_code(self):
        self.assertFalse(validate_trademark_dispatch_number(
            "TMZC73055497JFTZ01", "商标注册申请受理通知书"))

    def test_invalid_no_tmzc_prefix(self):
        self.assertFalse(validate_trademark_dispatch_number(
            "73055497ZCSL01", "商标注册申请受理通知书"))

    def test_invalid_short_app_number(self):
        self.assertFalse(validate_trademark_dispatch_number(
            "TMZC123ZCSL01", "商标注册申请受理通知书"))

    def test_invalid_empty_dispatch_number(self):
        self.assertFalse(validate_trademark_dispatch_number(
            "", "商标注册申请受理通知书"))

    def test_invalid_empty_notification_type(self):
        self.assertFalse(validate_trademark_dispatch_number(
            "TMZC73055497ZCSL01", ""))

    def test_unknown_notification_type_passes(self):
        self.assertTrue(validate_trademark_dispatch_number(
            "TMZC73055497ZCSL01", "商标评审申请受理通知书"))

    def test_valid_8digit_app_number(self):
        self.assertTrue(validate_trademark_dispatch_number(
            "TMZC12345678ZCSL01", "商标注册申请受理通知书"))

    def test_valid_multi_digit_serial(self):
        self.assertTrue(validate_trademark_dispatch_number(
            "TMZC73055497BHTZ123", "商标驳回通知书"))

    def test_valid_bhfs_csgg_with_serial(self):
        self.assertTrue(validate_trademark_dispatch_number(
            "BHFS20240000151499CSGG01", "商标注册申请初步审定公告通知书"))

    def test_valid_bhfs_csgg_multi_digit_serial(self):
        self.assertTrue(validate_trademark_dispatch_number(
            "BHFS20240000151499CSGG123", "商标注册申请初步审定公告通知书"))

    def test_invalid_bhfs_csgg_without_serial(self):
        self.assertFalse(validate_trademark_dispatch_number(
            "BHFS20240000151499CSGG", "商标注册申请初步审定公告通知书"))

    def test_invalid_bhfs_wrong_type_code(self):
        self.assertFalse(validate_trademark_dispatch_number(
            "BHFS20240000151499ZCSL01", "商标注册申请初步审定公告通知书"))

    def test_invalid_bhfs_no_review_serial(self):
        self.assertFalse(validate_trademark_dispatch_number(
            "BHFSCSGG01", "商标注册申请初步审定公告通知书"))

    def test_invalid_bhfs_for_wrong_notification_type(self):
        self.assertFalse(validate_trademark_dispatch_number(
            "BHFS20240000151499CSGG01", "商标注册申请受理通知书"))

    def test_bhfs_unknown_notification_type_fails(self):
        self.assertFalse(validate_trademark_dispatch_number(
            "BHFS20240000151499CSGG01", "商标评审申请受理通知书"))


class TestProcessTrademarkFileDispatchNumber(unittest.TestCase):
    def test_notification_includes_dispatch_number(self):
        text_no_space = "申请号：73055497TMZC73055497ZCSL01商标注册申请受理通知书根据商标法"
        text = text_no_space
        trademark_type = "商标注册申请受理通知书"
        result = process_trademark_file(text_no_space, text, trademark_type)
        self.assertEqual(result.get("trademark_dispatch_number"), "TMZC73055497ZCSL01")

    def test_notification_empty_dispatch_number(self):
        text_no_space = "申请号：73055497商标评审申请受理通知书"
        text = text_no_space
        trademark_type = "商标评审申请受理通知书"
        result = process_trademark_file(text_no_space, text, trademark_type)
        self.assertEqual(result.get("trademark_dispatch_number"), "")

    def test_certificate_no_dispatch_number(self):
        text_no_space = "第55012345号商标注册证注册人：公司A注册人地址"
        text = text_no_space
        trademark_type = "商标注册证"
        result = process_trademark_file(text_no_space, text, trademark_type)
        self.assertNotIn("trademark_dispatch_number", result)

    def test_renewal_proof_includes_dispatch_number(self):
        text_no_space = "申请号：73055497TMZC73055497ZCSL01商标续展注册证明"
        text = text_no_space
        trademark_type = "商标续展注册证明"
        result = process_trademark_file(text_no_space, text, trademark_type)
        self.assertEqual(result.get("trademark_dispatch_number"), "TMZC73055497ZCSL01")

    def test_bhfs_csgg_notification_includes_dispatch_number(self):
        text_no_space = "申请号：73055497BHFS20240000151499CSGG01商标注册申请初步审定公告通知书根据商标法"
        text = text_no_space
        trademark_type = "商标注册申请初步审定公告通知书"
        result = process_trademark_file(text_no_space, text, trademark_type)
        self.assertEqual(result.get("trademark_dispatch_number"), "BHFS20240000151499CSGG01")


class TestIdempotencyRules(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.csv_path = os.path.join(self.temp_dir, "trademark_files_archive.csv")
        init_csv(self.csv_path, TRADEMARK_CSV_COLUMNS)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_trademark_duplicate_with_dispatch_number(self):
        info = {
            "trademark_application_number": "73055497",
            "trademark_notification_name": "商标注册申请受理通知书",
            "trademark_dispatch_number": "TMZC73055497ZCSL01",
            "applicant": "公司A",
        }
        record = {col: "" for col in TRADEMARK_CSV_COLUMNS}
        record["申请号"] = "73055497"
        record["通知书名称"] = "商标注册申请受理通知书"
        record["发文编号"] = "TMZC73055497ZCSL01"
        record["子类型"] = "商标通知书"
        write_csv(self.csv_path, [record], TRADEMARK_CSV_COLUMNS)

        dup = _check_duplicate(self.csv_path, "商标通知书", info)
        self.assertIsNotNone(dup)

    def test_trademark_different_dispatch_number_not_duplicate(self):
        info_existing = {
            "trademark_application_number": "73055497",
            "trademark_notification_name": "商标注册申请受理通知书",
            "trademark_dispatch_number": "TMZC73055497ZCSL01",
            "applicant": "公司A",
        }
        record = {col: "" for col in TRADEMARK_CSV_COLUMNS}
        record["申请号"] = "73055497"
        record["通知书名称"] = "商标注册申请受理通知书"
        record["发文编号"] = "TMZC73055497ZCSL01"
        record["子类型"] = "商标通知书"
        write_csv(self.csv_path, [record], TRADEMARK_CSV_COLUMNS)

        info_new = {
            "trademark_application_number": "73055497",
            "trademark_notification_name": "商标注册申请受理通知书",
            "trademark_dispatch_number": "TMZC73055497ZCSL02",
            "applicant": "公司A",
        }
        dup = _check_duplicate(self.csv_path, "商标通知书", info_new)
        self.assertIsNone(dup)

    def test_trademark_bhfs_duplicate_with_dispatch_number(self):
        info = {
            "trademark_application_number": "73055497",
            "trademark_notification_name": "商标注册申请初步审定公告通知书",
            "trademark_dispatch_number": "BHFS20240000151499CSGG01",
            "applicant": "公司A",
        }
        record = {col: "" for col in TRADEMARK_CSV_COLUMNS}
        record["申请号"] = "73055497"
        record["通知书名称"] = "商标注册申请初步审定公告通知书"
        record["发文编号"] = "BHFS20240000151499CSGG01"
        record["子类型"] = "商标通知书"
        write_csv(self.csv_path, [record], TRADEMARK_CSV_COLUMNS)

        dup = _check_duplicate(self.csv_path, "商标通知书", info)
        self.assertIsNotNone(dup)

    def test_trademark_bhfs_different_dispatch_number_not_duplicate(self):
        record = {col: "" for col in TRADEMARK_CSV_COLUMNS}
        record["申请号"] = "73055497"
        record["通知书名称"] = "商标注册申请初步审定公告通知书"
        record["发文编号"] = "BHFS20240000151499CSGG01"
        record["子类型"] = "商标通知书"
        write_csv(self.csv_path, [record], TRADEMARK_CSV_COLUMNS)

        info_new = {
            "trademark_application_number": "73055497",
            "trademark_notification_name": "商标注册申请初步审定公告通知书",
            "trademark_dispatch_number": "BHFS20240000151499CSGG02",
            "applicant": "公司A",
        }
        dup = _check_duplicate(self.csv_path, "商标通知书", info_new)
        self.assertIsNone(dup)

    def test_trademark_tmzc_and_bhfs_same_notification_not_duplicate(self):
        record = {col: "" for col in TRADEMARK_CSV_COLUMNS}
        record["申请号"] = "73055497"
        record["通知书名称"] = "商标注册申请初步审定公告通知书"
        record["发文编号"] = "TMZC73055497CSGG"
        record["子类型"] = "商标通知书"
        write_csv(self.csv_path, [record], TRADEMARK_CSV_COLUMNS)

        info_new = {
            "trademark_application_number": "73055497",
            "trademark_notification_name": "商标注册申请初步审定公告通知书",
            "trademark_dispatch_number": "BHFS20240000151499CSGG01",
            "applicant": "公司A",
        }
        dup = _check_duplicate(self.csv_path, "商标通知书", info_new)
        self.assertIsNone(dup)

    def test_patent_register_copy_duplicate_with_date(self):
        from scripts.config import PATENT_CSV_COLUMNS
        patent_csv = os.path.join(self.temp_dir, "patent_files_archive.csv")
        init_csv(patent_csv, PATENT_CSV_COLUMNS)

        info = {
            "patent_number": "CN202010123456.1",
            "cnipa_date": "2024年01月15日",
        }
        record = {col: "" for col in PATENT_CSV_COLUMNS}
        record["申请号"] = "CN202010123456.1"
        record["子类型"] = "专利登记簿副本"
        record["发文日期"] = "2024年01月15日"
        write_csv(patent_csv, [record], PATENT_CSV_COLUMNS)

        dup = _check_duplicate(patent_csv, "专利登记簿副本", info)
        self.assertIsNotNone(dup)

    def test_patent_register_copy_different_date_not_duplicate(self):
        from scripts.config import PATENT_CSV_COLUMNS
        patent_csv = os.path.join(self.temp_dir, "patent_files_archive.csv")
        init_csv(patent_csv, PATENT_CSV_COLUMNS)

        record = {col: "" for col in PATENT_CSV_COLUMNS}
        record["申请号"] = "CN202010123456.1"
        record["子类型"] = "专利登记簿副本"
        record["发文日期"] = "2024年01月15日"
        write_csv(patent_csv, [record], PATENT_CSV_COLUMNS)

        info_new = {
            "patent_number": "CN202010123456.1",
            "cnipa_date": "2024年06月20日",
        }
        dup = _check_duplicate(patent_csv, "专利登记簿副本", info_new)
        self.assertIsNone(dup)


class TestBuildCsvRecordDispatchNumber(unittest.TestCase):
    def test_trademark_record_includes_dispatch_number(self):
        from scripts.config import TRADEMARK_CSV_COLUMNS
        temp_dir = tempfile.mkdtemp()
        try:
            csv_path = os.path.join(temp_dir, "trademark_files_archive.csv")
            init_csv(csv_path, TRADEMARK_CSV_COLUMNS)

            result = {
                "main_type": "商标文件",
                "sub_type": "商标通知书",
                "info": {
                    "trademark_application_number": "73055497",
                    "trademark_notification_name": "商标注册申请受理通知书",
                    "trademark_dispatch_number": "TMZC73055497ZCSL01",
                    "applicant": "公司A",
                    "application_date": "2023年07月25日",
                    "trademark_category": "第7类",
                    "review_agent": "",
                },
                "new_filename": "73055497_商标注册申请受理通知书_公司A.pdf",
                "original_filename": "test.pdf",
                "dispatch_date": "",
                "notification_name": "商标注册申请受理通知书",
                "error": None,
            }
            record = _build_csv_record(result, csv_path, TRADEMARK_CSV_COLUMNS)
            self.assertEqual(record["发文编号"], "TMZC73055497ZCSL01")
            self.assertEqual(record["申请号"], "73055497")
        finally:
            shutil.rmtree(temp_dir)


class TestSoftwareStorageStructure(unittest.TestCase):
    def test_software_two_level_folder(self):
        from scripts.script2_sync import _sync_csv
        from scripts import config

        temp_dir = tempfile.mkdtemp()
        original_repo_dir = config.REPO_DIR
        original_csv_dir = config.CSV_DIR
        original_software_csv = config.SOFTWARE_CSV
        try:
            config.REPO_DIR = os.path.join(temp_dir, "archives")
            config.CSV_DIR = os.path.join(temp_dir, "csv")
            config.SOFTWARE_CSV = os.path.join(config.CSV_DIR, "software_files_archive.csv")
            os.makedirs(os.path.join(config.REPO_DIR, "软著"), exist_ok=True)
            os.makedirs(config.CSV_DIR, exist_ok=True)

            sw_csv = config.SOFTWARE_CSV
            init_csv(sw_csv, config.SOFTWARE_CSV_COLUMNS)

            record = {col: "" for col in config.SOFTWARE_CSV_COLUMNS}
            record["子类型"] = "软著证书"
            record["受理号"] = "2023R11S1234567"
            record["登记号"] = "2024SR1234567"
            record["软件名称"] = "测试软件"
            record["著作权人"] = "公司A"
            record["法律状态"] = "登记下证"
            record["标识号"] = "2024SR1234567"
            record["文件名"] = "测试软件_软著证书_2025年11月04日_公司A.pdf"
            record["文件路径"] = os.path.join("软著", "测试软件_软著证书_2025年11月04日_公司A.pdf")
            record["处理时间"] = "2025-01-01 00:00:00"
            record["原始文件名"] = "test.pdf"
            write_csv(sw_csv, [record], config.SOFTWARE_CSV_COLUMNS)

            src_file = os.path.join(config.REPO_DIR, "软著", "测试软件_软著证书_2025年11月04日_公司A.pdf")
            with open(src_file, "w", encoding="utf-8") as f:
                f.write("test")

            _sync_csv(sw_csv, "软著")

            expected_dir = os.path.join(config.REPO_DIR, "软著", "公司A", "2024SR1234567-登记下证-公司A")
            self.assertTrue(os.path.exists(expected_dir))

            expected_file = os.path.join(expected_dir, "测试软件_软著证书_2025年11月04日_公司A.pdf")
            self.assertTrue(os.path.exists(expected_file))
        finally:
            config.REPO_DIR = original_repo_dir
            config.CSV_DIR = original_csv_dir
            config.SOFTWARE_CSV = original_software_csv
            shutil.rmtree(temp_dir)


class TestConfigColumns(unittest.TestCase):
    def test_trademark_csv_has_dispatch_number(self):
        self.assertIn("发文编号", TRADEMARK_CSV_COLUMNS)

    def test_dispatch_number_after_notification_name(self):
        idx_notification = TRADEMARK_CSV_COLUMNS.index("通知书名称")
        idx_dispatch = TRADEMARK_CSV_COLUMNS.index("发文编号")
        self.assertEqual(idx_dispatch, idx_notification + 1)


class TestBhfsRulesConstants(unittest.TestCase):
    def test_bhfs_rules_has_csgg_entry(self):
        self.assertIn("商标注册申请初步审定公告通知书", TRADEMARK_DISPATCH_NUMBER_BHFS_RULES)

    def test_bhfs_rules_type_code(self):
        rule = TRADEMARK_DISPATCH_NUMBER_BHFS_RULES["商标注册申请初步审定公告通知书"]
        self.assertEqual(rule["type_code"], "CSGG")

    def test_bhfs_rules_has_serial(self):
        rule = TRADEMARK_DISPATCH_NUMBER_BHFS_RULES["商标注册申请初步审定公告通知书"]
        self.assertTrue(rule["has_serial"])


class TestDetectTrademarkTypeBhfs(unittest.TestCase):
    def test_detect_bhfs_csgg(self):
        text_no_space = "BHFS20240000151499CSGG01商标注册申请初步审定公告通知书"
        result = detect_trademark_type(text_no_space)
        self.assertEqual(result, "商标注册申请初步审定公告通知书")

    def test_detect_csgg_still_works(self):
        text_no_space = "TMZC73055497CSGG商标注册申请初步审定公告通知书"
        result = detect_trademark_type(text_no_space)
        self.assertEqual(result, "商标注册申请初步审定公告通知书")


class TestDetectTrademarkChangeCorrection(unittest.TestCase):
    def test_detect_change_correction_with_bgbz(self):
        text_no_space = "TMBG20240001568099BGBZ01商标变更申请补正通知书"
        result = detect_trademark_type(text_no_space)
        self.assertEqual(result, "商标变更申请补正通知书")

    def test_detect_change_correction_without_bgbz(self):
        text_no_space = "商标变更申请补正通知书变更申请号20240001568099"
        result = detect_trademark_type(text_no_space)
        self.assertEqual(result, "商标变更申请补正通知书")


class TestExtractTmbgDispatchNumber(unittest.TestCase):
    def test_extract_tmbg_bgbz(self):
        from scripts.pdf_parser import extract_trademark_dispatch_number
        text = "TMBG20240001568099BGBZ01商标变更申请补正通知书"
        result = extract_trademark_dispatch_number(text)
        self.assertEqual(result, "TMBG20240001568099BGBZ01")

    def test_extract_tmbg_bgbz_multi_digit(self):
        from scripts.pdf_parser import extract_trademark_dispatch_number
        text = "TMBG20240001568099BGBZ123商标变更申请补正通知书"
        result = extract_trademark_dispatch_number(text)
        self.assertEqual(result, "TMBG20240001568099BGBZ123")

    def test_tmbg_priority_after_tmzc(self):
        from scripts.pdf_parser import extract_trademark_dispatch_number
        text = "TMZC73055497ZCSL01TMBG20240001568099BGBZ01"
        result = extract_trademark_dispatch_number(text)
        self.assertEqual(result, "TMZC73055497ZCSL01")


class TestValidateTmbgDispatchNumber(unittest.TestCase):
    def test_valid_tmbg_bgbz(self):
        from scripts.pdf_parser import validate_trademark_dispatch_number
        self.assertTrue(validate_trademark_dispatch_number(
            "TMBG20240001568099BGBZ01", "商标变更申请补正通知书"))

    def test_valid_tmbg_bgbz_multi_digit_serial(self):
        from scripts.pdf_parser import validate_trademark_dispatch_number
        self.assertTrue(validate_trademark_dispatch_number(
            "TMBG20240001568099BGBZ123", "商标变更申请补正通知书"))

    def test_invalid_tmbg_without_serial(self):
        from scripts.pdf_parser import validate_trademark_dispatch_number
        self.assertFalse(validate_trademark_dispatch_number(
            "TMBG20240001568099BGBZ", "商标变更申请补正通知书"))

    def test_invalid_tmbg_wrong_type_code(self):
        from scripts.pdf_parser import validate_trademark_dispatch_number
        self.assertFalse(validate_trademark_dispatch_number(
            "TMBG20240001568099ZCSL01", "商标变更申请补正通知书"))

    def test_invalid_tmbg_no_change_app_number(self):
        from scripts.pdf_parser import validate_trademark_dispatch_number
        self.assertFalse(validate_trademark_dispatch_number(
            "TMBGBGBZ01", "商标变更申请补正通知书"))


class TestExtractChangeCorrectionInfo(unittest.TestCase):
    def test_extract_all_fields(self):
        from scripts.pdf_parser import extract_trademark_change_correction_info
        text = "商标变更申请补正通知书变更申请号20240001568099商标注册号73051080变更事项变更名义/地址申请人某公司"
        result = extract_trademark_change_correction_info(text)
        self.assertEqual(result["change_application_number"], "20240001568099")
        self.assertEqual(result["trademark_application_number"], "73051080")
        self.assertEqual(result["change_items"], "变更名义/地址")

    def test_extract_change_application_number(self):
        from scripts.pdf_parser import extract_trademark_change_correction_info
        text = "变更申请号20240001568099"
        result = extract_trademark_change_correction_info(text)
        self.assertEqual(result["change_application_number"], "20240001568099")

    def test_extract_change_items(self):
        from scripts.pdf_parser import extract_trademark_change_correction_info
        text = "变更事项变更名义/地址"
        result = extract_trademark_change_correction_info(text)
        self.assertEqual(result["change_items"], "变更名义/地址")


class TestSoftwareLegalStatus(unittest.TestCase):
    def test_acceptance_status(self):
        from scripts.legal_status import SOFTWARE_LEGAL_STATUS_MAP
        self.assertEqual(SOFTWARE_LEGAL_STATUS_MAP["软著受理通知书"], "受理申请")

    def test_certificate_status(self):
        from scripts.legal_status import SOFTWARE_LEGAL_STATUS_MAP
        self.assertEqual(SOFTWARE_LEGAL_STATUS_MAP["软著证书"], "登记下证")


class TestConfigNewColumns(unittest.TestCase):
    def test_trademark_csv_has_change_columns(self):
        from scripts.config import TRADEMARK_CSV_COLUMNS
        self.assertIn("变更申请号", TRADEMARK_CSV_COLUMNS)
        self.assertIn("变更事项", TRADEMARK_CSV_COLUMNS)

    def test_trademark_report_has_change_columns(self):
        from scripts.config import TRADEMARK_REPORT_COLUMNS
        self.assertIn("变更申请号", TRADEMARK_REPORT_COLUMNS)
        self.assertIn("变更事项", TRADEMARK_REPORT_COLUMNS)

    def test_software_csv_legal_status_before_identifier(self):
        from scripts.config import SOFTWARE_CSV_COLUMNS
        idx_legal = SOFTWARE_CSV_COLUMNS.index("法律状态")
        idx_id = SOFTWARE_CSV_COLUMNS.index("标识号")
        self.assertLess(idx_legal, idx_id)

    def test_software_report_legal_status_first(self):
        from scripts.config import SOFTWARE_REPORT_COLUMNS
        self.assertEqual(SOFTWARE_REPORT_COLUMNS[0], "法律状态")

    def test_trademark_csv_identifier_early(self):
        from scripts.config import TRADEMARK_CSV_COLUMNS
        idx_sub = TRADEMARK_CSV_COLUMNS.index("子类型")
        idx_id = TRADEMARK_CSV_COLUMNS.index("标识号")
        self.assertEqual(idx_id, idx_sub + 1)


class TestResolveNotificationStatus(unittest.TestCase):
    def test_single_notification(self):
        from scripts.legal_status import _resolve_notification_status
        self.assertEqual(_resolve_notification_status("驳回决定"), "驳回")

    def test_compound_notification_higher_priority_wins(self):
        from scripts.legal_status import _resolve_notification_status
        result = _resolve_notification_status("驳回决定&第一次审查意见通知书")
        self.assertEqual(result, "驳回")

    def test_compound_notification_same_status(self):
        from scripts.legal_status import _resolve_notification_status
        result = _resolve_notification_status("第一次审查意见通知书&补正通知书")
        self.assertEqual(result, "实审")

    def test_none_notification(self):
        from scripts.legal_status import _resolve_notification_status
        self.assertIsNone(_resolve_notification_status("手续合格通知书"))

    def test_withdrawal_procedure_notification(self):
        from scripts.legal_status import _resolve_notification_status
        self.assertEqual(_resolve_notification_status("撤回专利申请手续合格通知书"), "撤回")

    def test_regex_match_in_compound(self):
        from scripts.legal_status import _resolve_notification_status
        result = _resolve_notification_status("第五次审查意见通知书&补正通知书")
        self.assertEqual(result, "实审")


class TestRegisterStatusExtraction(unittest.TestCase):
    def test_extract_patent_right_valid(self):
        from scripts.pdf_parser import extract_register_status
        text = "法律状态专利权有效国家知识产权局"
        self.assertEqual(extract_register_status(text), "授权")

    def test_extract_patent_right_terminated(self):
        from scripts.pdf_parser import extract_register_status
        text = "法律状态专利权终止国家知识产权局"
        self.assertEqual(extract_register_status(text), "失效")

    def test_extract_no_legal_status(self):
        from scripts.pdf_parser import extract_register_status
        text = "专利权人某公司专利权人地址"
        self.assertEqual(extract_register_status(text), "")

    def test_extract_empty_text(self):
        from scripts.pdf_parser import extract_register_status
        self.assertEqual(extract_register_status(""), "")


class TestRegisterStatusFallback(unittest.TestCase):
    def test_register_status_used_instead_of_unknown(self):
        from scripts.legal_status import _determine_patent_legal_status
        records = [
            {"子类型": "专利登记簿副本", "通知书名称": "", "登记簿状态": "授权", "处理时间": "2024-01-01 00:00:00", "序号": "1"},
        ]
        result = _determine_patent_legal_status("专利登记簿副本", "", records)
        self.assertEqual(result, "授权")

    def test_procedure_qualified_only_gives_shouli(self):
        from scripts.legal_status import _determine_patent_legal_status
        records = [
            {"子类型": "专利通知书", "通知书名称": "手续合格通知书", "处理时间": "2024-01-01 00:00:00", "序号": "1"},
        ]
        result = _determine_patent_legal_status("专利通知书", "手续合格通知书", records)
        self.assertEqual(result, "受理")

    def test_register_status_takes_priority_over_procedure(self):
        from scripts.legal_status import _determine_patent_legal_status
        records = [
            {"子类型": "专利登记簿副本", "通知书名称": "", "登记簿状态": "授权", "处理时间": "2024-01-01 00:00:00", "序号": "1"},
            {"子类型": "专利通知书", "通知书名称": "手续合格通知书", "处理时间": "2024-01-01 00:00:00", "序号": "2"},
        ]
        result = _determine_patent_legal_status("专利通知书", "手续合格通知书", records)
        self.assertEqual(result, "授权")

    def test_normal_status_takes_priority_over_register(self):
        from scripts.legal_status import _determine_patent_legal_status
        records = [
            {"子类型": "专利登记簿副本", "通知书名称": "", "登记簿状态": "授权", "处理时间": "2024-01-01 00:00:00", "序号": "1"},
            {"子类型": "专利通知书", "通知书名称": "驳回决定", "处理时间": "2024-01-02 00:00:00", "序号": "2"},
        ]
        result = _determine_patent_legal_status("专利通知书", "驳回决定", records)
        self.assertEqual(result, "驳回")


class TestWithdrawalProcedureDetection(unittest.TestCase):
    def test_detect_withdrawal_procedure_notification(self):
        from scripts.pdf_parser import detect_patent_type
        text = "手续合格通知书同意撤回专利申请ZL202010123456.1"
        sub_type, notifications = detect_patent_type(text)
        self.assertEqual(sub_type, "专利通知书")
        self.assertIn("撤回专利申请手续合格通知书", notifications)
        self.assertNotIn("手续合格通知书", notifications)

    def test_normal_procedure_notification_unchanged(self):
        from scripts.pdf_parser import detect_patent_type
        text = "手续合格通知书ZL202010123456.1"
        sub_type, notifications = detect_patent_type(text)
        self.assertEqual(sub_type, "专利通知书")
        self.assertIn("手续合格通知书", notifications)
        self.assertNotIn("撤回专利申请手续合格通知书", notifications)


class TestConfigRegisterStatusColumn(unittest.TestCase):
    def test_patent_csv_has_register_status(self):
        from scripts.config import PATENT_CSV_COLUMNS
        self.assertIn("登记簿状态", PATENT_CSV_COLUMNS)

    def test_patent_report_has_register_status(self):
        from scripts.config import PATENT_REPORT_COLUMNS
        self.assertIn("登记簿状态", PATENT_REPORT_COLUMNS)


class TestPatentLegalStatusMapWithdrawal(unittest.TestCase):
    def test_withdrawal_procedure_maps_to_withdraw(self):
        from scripts.legal_status import PATENT_LEGAL_STATUS_MAP
        self.assertEqual(PATENT_LEGAL_STATUS_MAP["撤回专利申请手续合格通知书"], "撤回")


if __name__ == "__main__":
    unittest.main()
