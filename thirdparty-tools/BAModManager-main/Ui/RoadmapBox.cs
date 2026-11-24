using System.Drawing.Drawing2D;
using BAModManager.Core;
using static BAModManager.Core.Loc;

namespace BAModManager.Ui;

/// <summary>
/// 1.1.18 (Osama 23 Nov 2026: the roadmap "is its own thing" and goes in the header, "a lot of dead space between our logo and the
/// american flag"): the roadmap steps as a numbered list on the same dark glass box as the players chart. The current step is red with
/// its NOW tag, the milestone gold, the after-the-new-year step dashed. Text, not a picture, so it stays readable at any size.
/// FaBanner draws it and opens the roadmap page on a click.
/// </summary>
internal static class RoadmapBox
{
    static readonly Color Gold = Color.FromArgb(245, 197, 66);

    public static void Draw(Graphics g, RectangleF box, LauncherNews.Roadmap? road, float u)
    {
        if (road == null || road.Steps.Count == 0 || box.Width < 140 * u || box.Height < 80 * u) return;
        var old = g.SmoothingMode;
        g.SmoothingMode = SmoothingMode.AntiAlias;
        using (var path = Theme.RoundRect(box, 4 * u))
        using (var fill = new SolidBrush(Color.FromArgb(170, 8, 9, 11)))
        using (var edge = new Pen(Color.FromArgb(40, 255, 255, 255)))
        {
            g.FillPath(fill, path);
            g.DrawPath(edge, path);
        }
        var f = TextFormatFlags.NoPadding | TextFormatFlags.NoPrefix | TextFormatFlags.EndEllipsis | TextFormatFlags.VerticalCenter;
        using var label = Theme.Head(9.5f, semi: true);
        using var title = Theme.Ui(8.75f);
        using var num = Theme.Head(8f, semi: true);
        using var tagFont = Theme.Head(7.5f, semi: true);
        float pad = 12 * u;
        TextRenderer.DrawText(g, T("ROADMAP"), label, Rectangle.Round(new RectangleF(box.X + pad, box.Y + 8 * u, box.Width - 2 * pad, 18 * u)), Theme.TextMuted, f);
        float top = box.Y + 32 * u, rowH = Math.Min(28 * u, (box.Bottom - 8 * u - top) / road.Steps.Count), d = Math.Min(18 * u, rowH - 4 * u);
        for (int i = 0; i < road.Steps.Count; i++)
        {
            var s = road.Steps[i];
            float y = top + i * rowH, cy = y + rowH / 2;
            var ring = s.Tag == "now" ? Theme.Accent : s.Tag == "milestone" ? Gold : Color.FromArgb(110, 255, 255, 255);
            var circle = new RectangleF(box.X + pad, cy - d / 2, d, d);
            if (s.Tag == "now") using (var b = new SolidBrush(Theme.Accent)) g.FillEllipse(b, circle);
            using (var pen = new Pen(ring, Math.Max(1f, 1.5f * u)) { DashStyle = s.Tag == "after" ? DashStyle.Dash : DashStyle.Solid }) g.DrawEllipse(pen, circle);
            TextRenderer.DrawText(g, (i + 1).ToString(), num, Rectangle.Round(circle), s.Tag == "now" ? Color.White : s.Tag == "milestone" ? Gold : Theme.TextMuted,
                TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding | TextFormatFlags.NoPrefix);
            float tx = circle.Right + 8 * u, right = box.Right - pad;
            float tagW = 0;
            if (s.TagLabel.Length > 0)
            {
                var text = s.TagLabel;   // no ★/→: the condensed head font has no glyph for them
                var sz = TextRenderer.MeasureText(g, text, tagFont, Size.Empty, TextFormatFlags.NoPadding);
                tagW = sz.Width + 10 * u;
                var r = new RectangleF(right - tagW, cy - 8 * u, tagW, 16 * u);
                var c = s.Tag == "now" ? Theme.Accent : s.Tag == "milestone" ? Gold : Theme.TextMuted;
                using (var p = Theme.RoundRect(r, 2 * u))
                using (var pen = new Pen(Color.FromArgb(170, c)))
                    g.DrawPath(pen, p);
                TextRenderer.DrawText(g, text, tagFont, Rectangle.Round(r), s.Tag == "now" ? Color.White : c,
                    TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding | TextFormatFlags.NoPrefix);
            }
            TextRenderer.DrawText(g, s.Title, title, Rectangle.Round(new RectangleF(tx, y, right - tx - tagW - 6 * u, rowH)), s.Tag == "now" ? Color.White : Theme.Text, f);
        }
        g.SmoothingMode = old;
    }
}
