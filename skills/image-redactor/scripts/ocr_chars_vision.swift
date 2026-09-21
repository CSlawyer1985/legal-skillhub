import Vision
import AppKit

// 逐字符 OCR：在整行 bbox 之外，额外给出每个字符的像素 bbox。
// 用途：需要遮盖「行内子串」时（如「徐建新案件」只盖「徐建新」、「2025-6206（何玉）」只盖「2025-6206」），
// 整行 bbox 不够用，必须拿到字符级坐标。
//
// 输出（TSV，左上角原点，像素坐标）：
//   ITEM <idx> <text> x y w h
//   CHAR <item_idx> <char_idx> <char> x y w h

guard CommandLine.arguments.count > 1 else {
    print("usage: swift ocr_chars_vision.swift <image>")
    exit(1)
}
let path = CommandLine.arguments[1]
guard let img = NSImage(contentsOfFile: path),
      let cgImage = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    print("cannot load image")
    exit(1)
}

let W = CGFloat(cgImage.width)
let H = CGFloat(cgImage.height)

func px(_ b: CGRect) -> (Double, Double, Double, Double) {
    let x = b.origin.x * W
    let y = (1 - b.origin.y - b.size.height) * H
    return (Double(x), Double(y), Double(b.size.width * W), Double(b.size.height * H))
}

let request = VNRecognizeTextRequest { req, _ in
    guard let results = req.results as? [VNRecognizedTextObservation] else { return }
    for (i, obs) in results.enumerated() {
        guard let top = obs.topCandidates(1).first else { continue }
        let (x, y, w, h) = px(obs.boundingBox)
        print(String(format: "ITEM\t%d\t%@\t%.1f\t%.1f\t%.1f\t%.1f", i, top.string, x, y, w, h))
        let s = top.string
        for (ci, ch) in s.enumerated() {
            let a = s.index(s.startIndex, offsetBy: ci)
            let b = s.index(a, offsetBy: 1)
            if let cb = try? top.boundingBox(for: a..<b) {
                let (cx, cy, cw, chh) = px(cb.boundingBox)
                print(String(format: "CHAR\t%d\t%d\t%@\t%.1f\t%.1f\t%.1f\t%.1f",
                             i, ci, String(ch), cx, cy, cw, chh))
            }
        }
    }
}
request.recognitionLevel = .accurate
request.recognitionLanguages = ["zh-Hans", "en-US"]
request.usesLanguageCorrection = true

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
do {
    try handler.perform([request])
} catch {
    print("error: \(error)")
    exit(1)
}

// 法律科技实务工具 · 维护者陆凌燕律师（北京德恒·无锡）
