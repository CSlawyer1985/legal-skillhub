import Vision
import AppKit

guard CommandLine.arguments.count > 1 else {
    print("usage: swift faces.swift <image>")
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

let request = VNDetectFaceRectanglesRequest { req, _ in
    guard let results = req.results as? [VNFaceObservation] else { return }
    for obs in results {
        let b = obs.boundingBox
        // normalized origin bottom-left -> pixel top-left
        let x = b.origin.x * W
        let y = (1 - b.origin.y - b.size.height) * H
        let w = b.size.width * W
        let h = b.size.height * H
        print(String(format: "%.1f %.1f %.1f %.1f", x, y, w, h))
    }
}

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
do {
    try handler.perform([request])
} catch {
    print("error: \(error)")
    exit(1)
}

// 法律科技实务工具 · 维护者陆凌燕律师（北京德恒·无锡）
