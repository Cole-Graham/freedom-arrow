using System.Drawing.Drawing2D;
using BAModManager.Core;
using static BAModManager.Core.Loc;

namespace BAModManager.Ui;

/// <summary>
/// 1.1.14 (Osama 21 Nov 2026, "make the launcher fit our website art style"): the launcher header, like the freedomarrow.app hero.
/// Assets/fa_banner.jpg is the 0.9.3 in-game menu art with the approved title logo (site/menu-bg.jpg + site/title.webp), drawn at
/// 1120x440 for a 560x220 header at 200 % scale. The OPEN ALPHA badge and the launcher version are drawn here so they stay sharp
/// and follow the language.
/// </summary>
internal sealed class FaBanner : Control
{
    private const float DesignWidth = 560f;
    private readonly Image? _art;

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
        if (_art != null)
        {
            // Cover: fill the width, keep the art's top edge.
            float h = Width * _art.Height / (float)_art.Width;
            g.DrawImage(_art, new RectangleF(0, 0, Width, Math.Max(h, Height)));
        }

        // OPEN ALPHA badge centred under the logo (logo box 29..172 x 11..171 at design size).
        var badge = T("OPEN ALPHA");
        using (var f = Theme.Head(10.5f))
        {
            var size = TextRenderer.MeasureText(g, badge, f, Size.Empty, TextFormatFlags.NoPadding);
            float bw = size.Width + 16 * k, bh = 21 * k, bx = 100.5f * k - bw / 2, by = 180 * k;
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
            var r = new RectangleF(Width - size.Width - 26 * k, 12 * k, size.Width + 14 * k, 19 * k);
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
