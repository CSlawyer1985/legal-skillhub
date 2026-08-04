#!/usr/bin/env swift

import Foundation
import Vision
import AppKit

struct OCRLine: Codable {
    let text: String
    let confidence: Float
}

struct OCROutput: Codable {
    let ok: Bool
    let file: String
    let lines: [OCRLine]
    let joinedText: String
}

func fail(_ msg: String) -> Never {
    fputs(msg + "\n", stderr)
    exit(1)
}

let args = CommandLine.arguments
guard args.count >= 2 else {
    fail("Usage: plan-c-ocr.swift <image-path>")
}

let imagePath = NSString(string: args[1]).expandingTildeInPath
let imageURL = URL(fileURLWithPath: imagePath)

guard let image = NSImage(contentsOf: imageURL) else {
    fail("Cannot load image: \(imagePath)")
}

guard let tiffData = image.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: tiffData),
      let cgImage = bitmap.cgImage else {
    fail("Cannot create CGImage from: \(imagePath)")
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true
request.recognitionLanguages = ["vi-VN", "en-US"]

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])

do {
    try handler.perform([request])
} catch {
    fail("Vision OCR failed: \(error)")
}

guard let observations = request.results else {
    fail("No OCR results")
}

let lines: [OCRLine] = observations.compactMap { obs in
    guard let top = obs.topCandidates(1).first else { return nil }
    return OCRLine(text: top.string, confidence: top.confidence)
}

let output = OCROutput(
    ok: true,
    file: imagePath,
    lines: lines,
    joinedText: lines.map { $0.text }.joined(separator: "\n")
)

let encoder = JSONEncoder()
encoder.outputFormatting = [.prettyPrinted, .withoutEscapingSlashes]
let data = try encoder.encode(output)
FileHandle.standardOutput.write(data)
