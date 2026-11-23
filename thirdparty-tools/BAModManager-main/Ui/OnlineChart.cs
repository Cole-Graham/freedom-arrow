using System.Drawing.Drawing2D;
using BAModManager.Core;
using static BAModManager.Core.Loc;

namespace BAModManager.Ui;

/// <summary>
/// 1.1.18 (Osama 23 Nov 2026, "add the players in game graph to the launcher", "above the battlefield report area"): the front
/// page's Players in game chart (players with the mod running per 30 minutes, from the game logs), last 7 days: area under a red
/// line, 0 / half / max on the left, one label per day at local midnight. Drawn by FaBanner on a dark glass box in the empty
/// part of the header art, the same box style as the launcher-version tag. No data = nothing drawn.
/// </summary>
internal static class OnlineChart
{
    public static void Draw(Graphics g, RectangleF box, IReadOnlyList<LauncherNews.OnlinePoint> p, float u)
    {
        // Osama 23 Nov 2026: "graph should be set to last 7 days": the axis is always exactly the 7 days up to the newest point.
        if (p.Count > 0) { var from = p[^1].Time.AddDays(-7); p = p.Where(q => q.Time >= from).ToList(); }
        if (p.Count < 2 || box.Width < 120 * u || box.Height < 60 * u) return;
        var old = g.SmoothingMode;
        g.SmoothingMode = SmoothingMode.AntiAlias;
        using (var path = Theme.RoundRect(box, 4 * u))
        using (var fill = new SolidBrush(Color.FromArgb(170, 8, 9, 11)))
        using (var edge = new Pen(Color.FromArgb(40, 255, 255, 255)))
        {
            g.FillPath(fill, path);
            g.DrawPath(edge, path);
        }
        var f = TextFormatFlags.NoPadding | TextFormatFlags.NoPrefix | TextFormatFlags.EndEllipsis;
        using var label = Theme.Head(9.5f, semi: true);
        using var small = Theme.Ui(8.25f);
        float pad = 12 * u;
        TextRenderer.DrawText(g, T("PLAYERS IN GAME · LAST 7 DAYS"), label, Rectangle.Round(new RectangleF(box.X + pad, box.Y + 8 * u, box.Width - 2 * pad, 18 * u)), Theme.TextMuted, f);
        int max = Math.Max(4, p.Max(x => x.Players));
        float left = box.X + 36 * u, top = box.Y + 34 * u, bottom = box.Bottom - 22 * u, right = box.Right - pad;
        long t1 = p[^1].Time.ToUnixTimeSeconds(), t0 = t1 - 7 * 86400;
        float X(DateTimeOffset t) => left + (right - left) * (float)(t.ToUnixTimeSeconds() - t0) / (t1 - t0);
        float Y(int n) => bottom - (bottom - top) * (float)n / max;
        using (var grid = new Pen(Color.FromArgb(45, 255, 255, 255)))
        {
            foreach (var v in new[] { 0, max / 2, max })
            {
                g.DrawLine(grid, left, Y(v), right, Y(v));
                TextRenderer.DrawText(g, v.ToString(), small, Rectangle.Round(new RectangleF(box.X, Y(v) - 7 * u, left - box.X - 6 * u, 14 * u)), Theme.TextMuted, f | TextFormatFlags.Right);
            }
            for (var d = DateTimeOffset.FromUnixTimeSeconds(t0).ToLocalTime().Date.AddDays(1); d <= p[^1].Time.ToLocalTime().DateTime; d = d.AddDays(1))
            {
                var x = X(new DateTimeOffset(d));
                g.DrawLine(grid, x, top, x, bottom);
                var txt = Loc.IsChinese ? $"{d.Month}月{d.Day}日" : d.ToString("MMM d", System.Globalization.CultureInfo.InvariantCulture);
                TextRenderer.DrawText(g, txt, small, Rectangle.Round(new RectangleF(x - 32 * u, bottom + 4 * u, 64 * u, 14 * u)), Theme.TextMuted, f | TextFormatFlags.HorizontalCenter);
            }
        }
        var pts = p.Select(q => new PointF(X(q.Time), Y(q.Players))).ToList();
        var area = new List<PointF>(pts) { new(pts[^1].X, bottom), new(pts[0].X, bottom) };
        using (var wash = new SolidBrush(Color.FromArgb(70, Theme.Accent))) g.FillPolygon(wash, area.ToArray());
        using (var line = new Pen(Theme.Accent, Math.Max(1.5f, 2 * u))) g.DrawLines(line, pts.ToArray());
        g.SmoothingMode = old;
    }
}
