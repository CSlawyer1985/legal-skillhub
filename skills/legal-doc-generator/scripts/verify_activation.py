#!/usr/bin/env python3
"""
Activation verifier for legal-doc-generator
Usage: python3 verify_activation.py <activation_code>
Output: VALID or INVALID
"""
import hmac, hashlib, sys, os

SECRET = "8dd308cb820abfd9599633c234ea8b16"
MARKER = os.path.expanduser("~/.legal-doc-generator.activated")

# Pre-computed HMAC hashes for valid activation codes
VALID_HASHES = {
    "c9245c7cd531fd34": "LDG-2F7R-M3PB-K96N",
    "ddb5f3d85e40f20b": "LDG-2NAS-GZHW-NAUF",
    "80aaeb7248b3877d": "LDG-2NGR-VKFJ-KSDT",
    "2ffa0d330026025e": "LDG-3XAY-RXH9-ZNAV",
    "1efc04fb3101a2e3": "LDG-47TC-H4DG-N8KV",
    "09acf2507fd955c0": "LDG-4AQG-UUUQ-MMXS",
    "7388a16c8ae005d2": "LDG-5FR4-VYEC-W6HX",
    "cbd19627ffb15563": "LDG-5TGE-M8KR-M2T9",
    "b622a060030da219": "LDG-5US7-3EH5-6FGY",
    "66ce2665f7d258f1": "LDG-682J-82A5-R9HY",
    "494d0630108d4619": "LDG-6964-JZ77-GZTN",
    "48402b6c6f6cb9a1": "LDG-6G6S-BD9P-XEJ2",
    "4bc8480960219ac5": "LDG-6G7S-GZYR-VDD5",
    "a5fc4cc7f625a232": "LDG-6JPW-72ZW-3BJ6",
    "e275097af65eff57": "LDG-6JU3-DG88-F9BH",
    "4d13fe0bccdcab24": "LDG-6KBW-XEPY-9E7Y",
    "7c578c645883f792": "LDG-6YTJ-EF7W-5RV7",
    "a4b2fe2a3f6997a6": "LDG-7AYP-JA78-4MPZ",
    "ff5b7ca6df2bae31": "LDG-7BM7-2TNH-WRP3",
    "007ba250c614ec22": "LDG-84HB-BB6K-F9TW",
    "fe2258200d73745d": "LDG-8P8D-D5YY-3DPS",
    "34fb39fb76545a6b": "LDG-96CT-WNYS-9WGV",
    "37770c0ed42aefdd": "LDG-9EJ2-7VDB-TJVW",
    "40bce2b6276cbc43": "LDG-A5XA-ER5B-R7QG",
    "d7992b3e399a66d0": "LDG-AVPQ-CW88-FEN7",
    "3661a9fff52a03ba": "LDG-AWH2-NH77-YYFD",
    "21b7df575bd4a1cd": "LDG-AXNN-WETM-A4ZH",
    "efb6d61738f10bd2": "LDG-BZQR-7245-XM8D",
    "546bea4971f2463f": "LDG-C2RM-2FDF-3CC6",
    "2a4c47ffefd9a435": "LDG-C5PA-Z9SP-KJ9A",
    "7e338e53ceb1483a": "LDG-CD2S-DDBT-URB5",
    "747c23b47b96de45": "LDG-CDVU-KGVN-4N5Q",
    "94dd51e129b5fcf6": "LDG-CF4Q-RTCA-TJKK",
    "e306df28f3373512": "LDG-CJVP-4M4T-57JN",
    "b7bf64223d786b62": "LDG-D2RG-QQFB-99W3",
    "61c4dc93a308c43c": "LDG-DXAW-SNP2-KKAA",
    "cdc6b22fd66aa1bb": "LDG-DXKR-FNAN-66GK",
    "ac30862ec574ef40": "LDG-DYRP-KFW9-WYFB",
    "871e6f7028df10f2": "LDG-E9W8-5BRT-UC6K",
    "5383910149d34441": "LDG-EV68-WK3M-UM9J",
    "3f9a2c6d69e0f92f": "LDG-EZ2B-K262-YMCF",
    "0c6f546878630d2d": "LDG-EZJS-R3KX-7QGV",
    "1ea5b9ed4bafe99a": "LDG-F362-2FDT-CXH3",
    "261be9e6193a7739": "LDG-FERB-57CZ-YRJW",
    "83282983e568696b": "LDG-FMUR-49VB-GKCY",
    "7ca784fbe732bcf9": "LDG-FXB7-488A-MTRG",
    "4a37bf437ab8248f": "LDG-FY4C-224P-YUA6",
    "7c713481668a80a3": "LDG-GTBB-YD33-3YGA",
    "bc0cae81adb288a7": "LDG-GUNA-CYVZ-BBS3",
    "73e9a99a4b8d1597": "LDG-HTYT-STZP-28AP",
    "2a2278ef76a09e34": "LDG-HVDC-22GK-AH66",
    "8a44309c2a68cd03": "LDG-J9TB-5NT9-E8WE",
    "6106d99abeb8d3bd": "LDG-J9YS-GTND-EQWA",
    "9db4b40382feb9ea": "LDG-JHM3-GRDJ-J3W2",
    "1364c909d1fe3b7c": "LDG-JRST-T7NY-Q5J7",
    "25468cb951a4eef0": "LDG-JY9B-W2DM-6RQF",
    "a6e279ac6e84bb51": "LDG-K6KA-VAPC-JQTV",
    "c54a05522f05f8ff": "LDG-KRKD-F4TR-UXNE",
    "0d2d50d79ef27903": "LDG-M2T2-CKBU-N4YU",
    "d0f0a27c9c6c9e4c": "LDG-M8TV-4RPX-YGTA",
    "eda74d35c5aa5d5e": "LDG-MMUS-WVZR-DMQM",
    "0b2f8e530d706eab": "LDG-MYUY-AAP6-CN97",
    "c1aea88ae7db5c9a": "LDG-NA2R-3MST-523Y",
    "14bf5154497fe472": "LDG-NNFE-ASFE-5RBS",
    "9a4a6494ceb752fa": "LDG-NNHT-H38U-BJSY",
    "36c56f010f941796": "LDG-P7RK-N5N2-274W",
    "067f60ecf2ea720e": "LDG-PHQN-PBRU-AWQC",
    "5dc1a5a8e424f316": "LDG-QWNB-7SKN-VA8G",
    "d61cb379ae76b3d5": "LDG-QZCG-TYFV-KQBY",
    "a1039f18a22c5326": "LDG-RGR6-DC4W-SDNT",
    "5476c4c79827cf86": "LDG-S2J6-CSZM-7VMP",
    "68a308cd6a3242d3": "LDG-S67N-4BQY-XCFV",
    "ab6eea04cca4ff89": "LDG-SAVS-U3NV-TA9Q",
    "9a2778aae671dcb3": "LDG-SBDA-PP7C-46YY",
    "38c4e3904fbae52f": "LDG-SPXA-QH4U-YTKV",
    "3650d321efbddfc6": "LDG-TRXP-QBH2-TFC6",
    "fd902fbd9037203b": "LDG-U2S6-UN34-WN64",
    "a21c1559d5974ba4": "LDG-UM5U-7UFN-X4VB",
    "f837a203b48ea2a1": "LDG-UM8E-YR38-856X",
    "1efd50170e590846": "LDG-URFR-KVTN-HEXN",
    "efb32b541ac60f1f": "LDG-UZ9F-N4RR-G4VR",
    "f8c02b99512896d6": "LDG-V23R-KXM9-SQCT",
    "ef34356f50299b55": "LDG-VAVA-K5CQ-GT37",
    "6ee59dac37690a89": "LDG-VGMC-K7B8-VHNJ",
    "68dab8eda78d24bb": "LDG-VKBR-EMYR-8QPE",
    "76291c6d05aa1afc": "LDG-VRDA-CMSG-PA83",
    "5130412fbd0b4e25": "LDG-WN9K-PVM5-Y7BU",
    "f634d5b374f65958": "LDG-WQ7A-Z6YH-24VW",
    "6c4eb5c728726e59": "LDG-WRDT-6YEF-YNCJ",
    "a511e03432a058c7": "LDG-WWGW-WEZC-B9ZT",
    "549432ac902ef101": "LDG-X3BS-AUYK-44HW",
    "3f8118ba9ca11f88": "LDG-X5UE-KYMT-N259",
    "a5f6fd890eebe80c": "LDG-XDPU-T52B-PBH8",
    "927c82123174729d": "LDG-XQTV-5FM3-VUCA",
    "ce116d23a6fa55b2": "LDG-YA6T-ZN6D-GQH2",
    "af03cb8158a8b270": "LDG-YJN5-UFJC-UPP9",
    "b910dcaaecb29723": "LDG-YQNX-58UC-PC7R",
    "748b896d7f06fb99": "LDG-Z83F-3R2A-C5T4",
    "58ebf80241cd6dd4": "LDG-ZXC8-S9NM-FFRF",
    "07b803a80c9a7296": "LDG-ZYGQ-A7UD-N3KB",
}


def verify(code):
    code = code.strip().upper()
    h = hmac.new(SECRET.encode(), code.encode(), hashlib.sha256).hexdigest()[:16]
    if h in VALID_HASHES:
        return True
    return False

def main():
    if len(sys.argv) != 2:
        print("INVALID")
        sys.exit(0)
    
    code = sys.argv[1].strip()
    
    if verify(code):
        with open(MARKER, "w") as f:
            f.write(code)
        print("VALID")
        sys.exit(0)
    
    print("INVALID")
    sys.exit(0)

if __name__ == "__main__":
    main()
