// macOS-only document verification helper; no role in the experiment.
import Foundation
import AppKit
import PDFKit

guard CommandLine.arguments.count == 3 else {
    fatalError("Usage: swift inspect_pdf.swift input.pdf new-output-directory")
}
let input = URL(fileURLWithPath: CommandLine.arguments[1])
let output = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
guard let document = PDFDocument(url: input) else { fatalError("Could not open PDF") }
try FileManager.default.createDirectory(at: output, withIntermediateDirectories: false)
var counts: [Int] = []
for index in 0..<document.pageCount {
    guard let page = document.page(at: index) else { fatalError("Missing page") }
    counts.append((page.string ?? "").count)
    let preview = page.thumbnail(of: NSSize(width: 850, height: 1100), for: .mediaBox)
    guard let tiff = preview.tiffRepresentation,
          let bitmap = NSBitmapImageRep(data: tiff),
          let png = bitmap.representation(using: .png, properties: [:]) else {
        fatalError("Could not render page")
    }
    try png.write(to: output.appendingPathComponent("page-\(index + 1).png"))
}
try (document.string ?? "").write(to: output.appendingPathComponent("text.txt"),
                                 atomically: true, encoding: .utf8)
let summary: [String: Any] = ["pages": document.pageCount,
                              "characters_per_page": counts,
                              "renderer": "macOS PDFKit"]
let data = try JSONSerialization.data(withJSONObject: summary, options: [.prettyPrinted, .sortedKeys])
try data.write(to: output.appendingPathComponent("inspection.json"))
print(String(data: data, encoding: .utf8)!)
