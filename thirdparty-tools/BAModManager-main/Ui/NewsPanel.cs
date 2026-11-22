using System.Runtime.InteropServices;
using BAModManager.Core;
using static BAModManager.Core.Loc;

namespace BAModManager.Ui;

/// <summary>
/// 1.1.15 (Osama 22 Nov 2026, "can we add a news section on the launcher? like the battle stats and patch notes?"):
/// the right-hand column of the Freedom Arrow launcher. Battlefield report numbers from freedomarrow.app and the short
/// release announcements (中文 when the launcher is in Chinese), with a link to the full notes on the site. See LauncherNews.
/// </summary>
internal sealed class NewsPanel : Panel
{
    private readonly StatTiles _tiles = new() { Dock = DockStyle.Top, Height = 156 };
    private readonly RichTextBox _notes;
    private readonly Button _more;
    private string _link = LauncherNews.Site;

    public NewsPanel()
    {
        BackColor = Theme.Panel;
        Padding = new Padding(20, 16, 18, 14);
        _notes = new RichTextBox
        {
            Dock = DockStyle.Fill,
            ReadOnly = true,
            BorderStyle = BorderStyle.None,
            BackColor = Theme.Panel,
            ForeColor = Theme.Text,
            DetectUrls = false,
            ScrollBars = RichTextBoxScrollBars.Vertical,
            Font = Body(),
            TabStop = false,
            Cursor = Cursors.Default,
            ShortcutsEnabled = false,
        };
        // Windows 10/11 dark scroll bar, like the rest of the launcher (ignored where the theme doesn't exist)
        _notes.HandleCreated += (_, _) => { try { SetWindowTheme(_notes.Handle, "DarkMode_Explorer", null); } catch (Exception) { } };
        _more = Theme.MakeButton(T("Full patch notes and statistics →"), ButtonKind.Ghost);
        _more.Dock = DockStyle.Bottom;
        _more.AutoSize = false;
        _more.Height = 34;
        _more.Click += (_, _) => LauncherNews.Open(_link);

        // Docked top controls are added bottom-up
        Controls.Add(_notes);
        Controls.Add(Title(T("PATCH NOTES")));
        Controls.Add(Gap(14));
        Controls.Add(_tiles);
        Controls.Add(Title(T("BATTLEFIELD REPORT")));
        Controls.Add(_more);
        ShowText(T("Loading news…"));
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        // the site's card edge on the left, against the launcher column
        using var edge = new SolidBrush(Theme.Border);
        e.Graphics.FillRectangle(edge, 0, 0, Math.Max(1, LogicalToDeviceUnits(1)), Height);
    }

    public async Task LoadAsync()
    {
        var news = await LauncherNews.LoadAsync();
        if (IsDisposed) return;
        if (news == null) { ShowText(T("News is unavailable right now. It doesn't affect PLAY.")); return; }
        _tiles.Set(news.Stats);
        if (news.Notes.Count > 0) _link = news.Notes[0].Link;
        Render(news.Notes);
    }

    private void ShowText(string text)
    {
        _notes.Clear();
        Append(text, Body(), Theme.TextMuted);
    }

    private void Render(IReadOnlyList<LauncherNews.Note> notes)
    {
        _notes.SuspendLayout();
        _notes.Clear();
        bool first = true;
        foreach (var n in notes)
        {
            var text = Loc.IsChinese && n.Chinese.Length > 0 ? n.Chinese : n.English;
            if (!first) Append("\n\n", Body(), Theme.Text);
            first = false;
            Append("Freedom Arrow " + n.Version, VersionFont, Theme.Text);
            if (n.Date.Length > 0) Append("   " + Date(n.Date), DateFont, Theme.TextMuted);
            Append("\n", Body(), Theme.Text);
            foreach (var raw in text.Replace("\r", "").Split('\n'))
            {
                var line = raw.TrimEnd();
                if (line.Length == 0 || line.Trim() == "---") continue;
                if (line.StartsWith("#"))
                {
                    Append("\n" + Heading(line) + "\n", SectionFont, Theme.Accent);
                    continue;
                }
                int indent = line.Length - line.TrimStart().Length;
                var body = line.TrimStart();
                string lead = "";
                if (body.StartsWith("- ") || body.StartsWith("* "))
                {
                    body = body[2..];
                    lead = indent >= 2 ? "      ◦  " : "•  ";
                }
                Append(lead, Body(), indent >= 2 ? Theme.TextMuted : Theme.Accent);
                Inline(body, indent >= 2 ? Theme.TextMuted : Theme.Text);
                Append("\n", Body(), Theme.Text);
            }
        }
        _notes.SelectionStart = 0;
        _notes.ScrollToCaret();
        _notes.ResumeLayout();
    }

    /// <summary>**bold** runs; every other character is shown as it is.</summary>
    private void Inline(string text, Color color)
    {
        var parts = text.Split("**");
        for (int i = 0; i < parts.Length; i++)
            if (parts[i].Length > 0) Append(parts[i], i % 2 == 1 ? BoldFont : Body(), i % 2 == 1 ? Theme.Text : color);
    }

    /// <summary>"## ⚔️ Combat" -> "Combat": the emoji in front of a heading don't render in every Windows font.</summary>
    private static string Heading(string line)
    {
        var t = line.TrimStart('#', ' ');
        int i = 0;
        while (i < t.Length && !char.IsLetterOrDigit(t[i])) i++;
        return i < t.Length ? t[i..] : t;
    }

    /// <summary>"21 November 2026" -> "2026 年 11 月 21 日" in Chinese.</summary>
    private static string Date(string date) =>
        Loc.IsChinese && DateTime.TryParseExact(date, "d MMMM yyyy", System.Globalization.CultureInfo.InvariantCulture, System.Globalization.DateTimeStyles.None, out var d)
            ? $"{d.Year} 年 {d.Month} 月 {d.Day} 日" : date;

    [DllImport("uxtheme.dll", CharSet = CharSet.Unicode)]
    private static extern int SetWindowTheme(IntPtr hwnd, string? appName, string? idList);

    private void Append(string text, Font font, Color color)
    {
        _notes.SelectionStart = _notes.TextLength;
        _notes.SelectionLength = 0;
        _notes.SelectionFont = font;
        _notes.SelectionColor = color;
        _notes.AppendText(text);
    }

    // One set of fonts for the whole text (the RichTextBox copies them into its runs)
    private static readonly Font BodyFont = Theme.Ui(9.75f), BoldFont = Theme.Semibold(9.75f), DateFont = Theme.Ui(9f),
        VersionFont = Theme.Head(17f), SectionFont = Theme.Head(12.5f, semi: true);

    private static Font Body() => BodyFont;

    private static Control Gap(int h) => new Panel { Dock = DockStyle.Top, Height = h, BackColor = Theme.Panel };

    private static Control Title(string text) => new Label
    {
        Text = text,
        Dock = DockStyle.Top,
        Height = 30,
        Font = Theme.Head(13f),
        ForeColor = Theme.Text,
        BackColor = Theme.Panel,
        TextAlign = ContentAlignment.TopLeft,
        UseMnemonic = false,
    };

    /// <summary>2 x 2 tiles like the front page's Battlefield report.</summary>
    private sealed class StatTiles : Control
    {
        private LauncherNews.Stats? _s;

        public StatTiles()
        {
            SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
            BackColor = Theme.Panel;
        }

        public void Set(LauncherNews.Stats s) { _s = s; Invalidate(); }

        protected override void OnPaint(PaintEventArgs e)
        {
            var g = e.Graphics;
            g.Clear(BackColor);
            var items = new (string Label, int? Value, string Sub)[]
            {
                (T("ONLINE NOW"), _s?.Online, T("in the mod lobby")),
                (T("PEAK, 24 H"), _s?.Peak24, T("players in game")),
                (T("PLAYERS"), _s?.Players, T("all time")),
                (T("MATCHES"), _s?.Matches, T("all time")),
            };
            int gap = LogicalToDeviceUnits(8);
            int w = (Width - gap) / 2, h = (Height - gap) / 2;
            using var label = Theme.Head(9.5f, semi: true);
            using var value = Theme.Head(21f);
            using var sub = Theme.Ui(8.25f);
            for (int i = 0; i < items.Length; i++)
            {
                var r = new Rectangle(i % 2 * (w + gap), i / 2 * (h + gap), w, h);
                using (var fill = new SolidBrush(Theme.Surface)) g.FillRectangle(fill, r);
                using (var edge = new Pen(Theme.Border)) g.DrawRectangle(edge, r.X, r.Y, r.Width - 1, r.Height - 1);
                using (var strip = new SolidBrush(i == 0 ? Theme.Accent : Theme.Border))
                    g.FillRectangle(strip, r.X, r.Y, r.Width, Math.Max(2, LogicalToDeviceUnits(2)));
                int pad = LogicalToDeviceUnits(10);
                var f = TextFormatFlags.NoPadding | TextFormatFlags.NoPrefix | TextFormatFlags.EndEllipsis;
                TextRenderer.DrawText(g, items[i].Label, label, new Rectangle(r.X + pad, r.Y + LogicalToDeviceUnits(8), r.Width - 2 * pad, LogicalToDeviceUnits(16)), Theme.TextMuted, f);
                TextRenderer.DrawText(g, items[i].Value?.ToString("N0") ?? "—", value, new Rectangle(r.X + pad, r.Y + LogicalToDeviceUnits(24), r.Width - 2 * pad, LogicalToDeviceUnits(32)), Theme.Text, f);
                TextRenderer.DrawText(g, items[i].Sub, sub, new Rectangle(r.X + pad, r.Bottom - LogicalToDeviceUnits(19), r.Width - 2 * pad, LogicalToDeviceUnits(15)), Theme.TextMuted, f);
            }
        }
    }
}
