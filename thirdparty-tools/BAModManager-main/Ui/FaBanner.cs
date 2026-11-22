using System.Drawing.Drawing2D;
using BAModManager.Core;
using static BAModManager.Core.Loc;

namespace BAModManager.Ui;

/// <summary>
/// 1.1.14 (Osama 21 Nov 2026, "make the launcher fit our website art style"): the launcher header, like the freedomarrow.app hero.
/// Assets/fa_banner.jpg is the 0.9.3 in-game menu art with the approved title logo (site/menu-bg.jpg + site/title.webp), drawn at
/// 1120x440 for a 560x220 header at 200 % scale. 1.1.15 (Osama 22 Nov 2026, "make the launcher bigger so more of it is art"):
/// a full-width 1440x320 header (2880x640, tools/distribution/make_launcher_banner.py): the art right-aligned, the logo on the left. The OPEN ALPHA badge and the launcher version are drawn here so they stay sharp
/// and follow the language.
/// </summary>
internal sealed class FaBanner : Control
{
    private const float DesignWidth = 1440f;
    private readonly Image? _art;

    /// <summary>Space kept free at the top right (design pixels) for the language button.</summary>
    public int RightInset { get; set; }

    public FaBanner(Image? art)
    {
        _art = art;
        SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
        BackColor = Theme.Background;
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        var g = e.Graphics;
        g.Clear(BackColor);
        g.InterpolationMode = InterpolationMode.HighQualityBicubic;
        g.SmoothingMode = SmoothingMode.AntiAlias;
        float k = Width / DesignWidth;
        // The art keeps its shape: full width, or (header made shorter for a small screen) scaled to the height and right-aligned.
        float s = k, x0 = 0;
        if (_art != null)
        {
            float h = Width * _art.Height / (float)_art.Width;
            if (Height < h - 1)
            {
                s = k * Height / h;
                x0 = Width - Width * Height / h;
            }
            g.DrawImage(_art, new RectangleF(x0, 0, Width - x0, Math.Min(h, Height)));
        }

        // OPEN ALPHA badge centred under the logo (logo box 52..275 x 16..266 at design size).
        var badge = T("OPEN ALPHA");
        using (var f = Theme.Head(10.5f))
        {
            var size = TextRenderer.MeasureText(g, badge, f, Size.Empty, TextFormatFlags.NoPadding);
            float bw = size.Width + 18 * s, bh = 23 * s, bx = x0 + 163.5f * s - bw / 2, by = 274 * s;
            using (var p = Theme.RoundRect(new RectangleF(bx, by, bw, bh), 3 * k))
            using (var b = new SolidBrush(Theme.Accent))
                g.FillPath(b, p);
            TextRenderer.DrawText(g, badge, f, Rectangle.Round(new RectangleF(bx, by, bw, bh)), Color.White,
                TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding | TextFormatFlags.NoPrefix);
        }

        // Launcher version, top right, like the site's top-bar tag.
        var version = T("LAUNCHER {0}", SelfUpdate.Current.ToString(3));
        using (var f = Theme.Head(9f, semi: true))
        {
            var size = TextRenderer.MeasureText(g, version, f, Size.Empty, TextFormatFlags.NoPadding);
            var r = new RectangleF(Width - size.Width - LogicalToDeviceUnits(26 + RightInset), LogicalToDeviceUnits(12), size.Width + LogicalToDeviceUnits(14), LogicalToDeviceUnits(19));   // fixed to the language button, whatever the width
            using (var p = Theme.RoundRect(r, 3 * k))
            using (var b = new SolidBrush(Color.FromArgb(150, 0, 0, 0)))
            using (var edge = new Pen(Color.FromArgb(40, 255, 255, 255)))
            {
                g.FillPath(b, p);
                g.DrawPath(edge, p);
            }
            TextRenderer.DrawText(g, version, f, Rectangle.Round(r), Theme.TextMuted,
                TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding | TextFormatFlags.NoPrefix);
        }

        // The site's red line under the hero.
        using var line = new SolidBrush(Color.FromArgb(160, Theme.Accent));
        g.FillRectangle(line, 0, Height - Math.Max(2, 2 * k), Width, Math.Max(2, 2 * k));
    }
}
