// Draw companion project logos using the established Elmo style.
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
let rare = CommandLine.arguments[2] == "rare"
if rare {
    gold.setStroke()
    let outer = NSBezierPath(ovalIn: NSRect(x: 108, y: 180, width: 172, height: 172))
    outer.lineWidth = 12; outer.stroke()
    let inner = NSBezierPath(ovalIn: NSRect(x: 140, y: 212, width: 108, height: 108))
    inner.lineWidth = 3; inner.stroke()
    line([NSPoint(x: 194, y: 266), NSPoint(x: 270, y: 321)], pale, 6)
    gold.setFill(); NSBezierPath(ovalIn: NSRect(x: 235, y: 292, width: 23, height: 23)).fill()
    line([NSPoint(x: 200, y: 184), NSPoint(x: 200, y: 167)], gold, 5)
    line([NSPoint(x: 108, y: 266), NSPoint(x: 91, y: 266)], gold, 5)
} else {
    line([NSPoint(x: 200, y: 348), NSPoint(x: 280, y: 322), NSPoint(x: 270, y: 241),
        NSPoint(x: 243, y: 199), NSPoint(x: 200, y: 174), NSPoint(x: 157, y: 199),
        NSPoint(x: 130, y: 241), NSPoint(x: 120, y: 322), NSPoint(x: 200, y: 348)], gold, 9)
    box(185, 228, 30, 82, pale, 5); box(159, 254, 82, 30, pale, 5)
}
label("ELMO", 72, 42, gold)
label(rare ? "RARE ALERTS" : "BUFF ASSIST", 43, 15, pale)
image.unlockFocus()
let bitmap = NSBitmapImageRep(data: image.tiffRepresentation!)!
try bitmap.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: CommandLine.arguments[1]))
