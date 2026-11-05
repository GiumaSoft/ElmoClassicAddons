// Draw the project's own logo in the existing Elmo icon style.
import AppKit

let gold = NSColor(calibratedRed: 0.96, green: 0.72, blue: 0.30, alpha: 1)
let pale = NSColor(calibratedRed: 0.94, green: 0.92, blue: 0.85, alpha: 1)
let background = NSColor(calibratedRed: 0.045, green: 0.065, blue: 0.10, alpha: 1)
func box(_ x: CGFloat, _ y: CGFloat, _ w: CGFloat, _ h: CGFloat, _ color: NSColor, _ radius: CGFloat = 0) {
    color.setFill()
    NSBezierPath(roundedRect: NSRect(x: x, y: y, width: w, height: h), xRadius: radius, yRadius: radius).fill()
}
func line(_ points: [NSPoint], _ color: NSColor, _ width: CGFloat) {
    color.setStroke()
    let path = NSBezierPath()
    path.move(to: points[0])
    for point in points.dropFirst() { path.line(to: point) }
    path.lineWidth = width
    path.lineCapStyle = .round
    path.lineJoinStyle = .round
    path.stroke()
}
func label(_ text: String, _ y: CGFloat, _ size: CGFloat, _ color: NSColor) {
    let value = NSAttributedString(string: text, attributes: [
        .font: NSFont.systemFont(ofSize: size, weight: .bold), .foregroundColor: color, .kern: 4
    ])
    value.draw(at: NSPoint(x: (400 - value.size().width) / 2, y: y))
}
let image = NSImage(size: NSSize(width: 400, height: 400))
image.lockFocus()
box(0, 0, 400, 400, background)
box(12, 12, 376, 376, gold, 48)
box(18, 18, 364, 364, background, 43)
box(88, 167, 224, 171, gold, 18)
box(98, 177, 204, 151, background, 10)
line([NSPoint(x: 144, y: 171), NSPoint(x: 122, y: 135), NSPoint(x: 193, y: 171)], gold, 10)
line([NSPoint(x: 139, y: 256), NSPoint(x: 181, y: 216), NSPoint(x: 263, y: 293)], pale, 17)
label("ELMO", 72, 42, gold)
label("QUEST REPORT", 43, 15, pale)
image.unlockFocus()
let bitmap = NSBitmapImageRep(data: image.tiffRepresentation!)!
try bitmap.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: CommandLine.arguments[1]))
