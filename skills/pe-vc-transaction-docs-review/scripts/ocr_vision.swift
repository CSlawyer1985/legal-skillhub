import Foundation
import Vision
import AppKit

guard CommandLine.arguments.count >= 2 else {
    fputs("Usage: ocr_vision.swift image.png\n", stderr)
    exit(2)
}

let path = CommandLine.arguments[1]
guard let image = NSImage(contentsOfFile: path),
      let tiff = image.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: tiff),
      let cgImage = bitmap.cgImage else {
    fputs("Cannot load image: \(path)\n", stderr)
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true
if #available(macOS 11.0, *) {
    request.recognitionLanguages = ["zh-Hans", "en-US"]
}

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
do {
    try handler.perform([request])
    let observations = (request.results ?? []).compactMap { observation -> (VNRectangleObservation, String)? in
        guard let text = observation.topCandidates(1).first?.string else { return nil }
        return (observation, text)
    }
    let lines = observations.sorted { left, right in
        let verticalDelta = left.0.boundingBox.midY - right.0.boundingBox.midY
        if abs(verticalDelta) > 0.01 {
            return verticalDelta > 0
        }
        return left.0.boundingBox.minX < right.0.boundingBox.minX
    }.map { $0.1 }
    print(lines.joined(separator: "\n"))
} catch {
    fputs("OCR failed: \(error)\n", stderr)
    exit(1)
}
