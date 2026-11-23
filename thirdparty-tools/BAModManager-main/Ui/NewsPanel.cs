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
    private readonly StatTiles _tiles = new() { Dock = DockStyle.Top, Height = 68 };
    /// <summary>Osama 23 Nov 2026: "add the players in game graph to the launcher", "above the battlefield report area": the series is
    /// handed to the header (FaBanner), which draws the chart in the dark space of the art above this column.</summary>
    public event Action<IReadOnlyList<LauncherNews.OnlinePoint>>? OnlineLoaded;
    private readonly RichTextBox _notes;
    private readonly Button _more;
    private string _link = LauncherNews.Site;
    // NEW FEATURES next to PATCH NOTES (Osama 22 Nov 2026: "add the gif with changing the paint scheme in the launcher under a
    // new feature category", then "we have so much space we should be able to fit the patch notes and features")
    private readonly TableLayoutPanel _cols;
    private readonly Panel _feature;
    private readonly Label _featureTitle, _featureText;
    private readonly PictureBox _featureImage;
    private MemoryStream? _imageData;   // an animated GIF needs its stream for as long as it plays

    public NewsPanel()
    {
        BackColor = Theme.Panel;
        Padding = new Padding(24, 18, 24, 16);
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
        _more = Theme.MakeButton(T("Full notes →"), ButtonKind.Ghost);
        _more.Dock = DockStyle.Right;   // beside the PATCH NOTES heading, so the notes get the height
        _more.AutoSize = true;
        _more.Click += (_, _) => LauncherNews.Open(_link);

        _featureTitle = new Label { Dock = DockStyle.Top, Height = 28, Font = Theme.Head(15f), ForeColor = Theme.Text, BackColor = Theme.Panel, UseMnemonic = false };
        _featureText = new Label { Dock = DockStyle.Top, Height = 48, ForeColor = Theme.TextMuted, BackColor = Theme.Panel, UseMnemonic = false };
        // full column width, its own height: the picture sits right under the text
        _featureImage = new PictureBox { Dock = DockStyle.Top, SizeMode = PictureBoxSizeMode.Zoom, BackColor = Theme.Panel, Cursor = Cursors.Hand, Height = 0 };
        _featureImage.Resize += (_, _) => FitImage();
        _featureImage.Click += (_, _) => LauncherNews.Open(LauncherNews.Site);
        _feature = new Panel { Dock = DockStyle.Fill, BackColor = Theme.Panel, Margin = new Padding(0, 0, 14, 0) };
        _feature.Controls.Add(_featureImage);
        _feature.Controls.Add(Gap(4));
        _feature.Controls.Add(_featureText);
        _feature.Controls.Add(_featureTitle);
        _feature.Controls.Add(Title(T("NEW FEATURES")));
        var notes = new Panel { Dock = DockStyle.Fill, BackColor = Theme.Panel, Margin = new Padding(14, 0, 0, 0) };
        var notesHead = new Panel { Dock = DockStyle.Top, Height = 30, BackColor = Theme.Panel };
        var notesTitle = Title(T("PATCH NOTES"));
        notesTitle.Dock = DockStyle.Fill;
        notesHead.Controls.Add(notesTitle);
        notesHead.Controls.Add(_more);
        notes.Controls.Add(_notes);
        notes.Controls.Add(notesHead);
        _cols = new TableLayoutPanel { Dock = DockStyle.Fill, BackColor = Theme.Panel, ColumnCount = 2, RowCount = 1, Margin = Padding.Empty, Padding = Padding.Empty };
        _cols.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 0));   // the features column opens when a feature arrives
        _cols.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        _cols.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        _cols.Controls.Add(_feature, 0, 0);
        _cols.Controls.Add(notes, 1, 0);

        // Docked top controls are added bottom-up
        Controls.Add(_cols);
        Controls.Add(Gap(12));
        Controls.Add(_tiles);
        Controls.Add(Title(T("BATTLEFIELD REPORT")));
        ShowText(T("Loading news…"));
        _refresh.Tick += async (_, _) => await RefreshAsync();
        Disposed += (_, _) => _refresh.Dispose();
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
        _refresh.Start();
        var news = await LauncherNews.LoadAsync();
        if (IsDisposed) return;
        if (news == null) { ShowText(T("News is unavailable right now. It doesn't affect PLAY.")); return; }
        _loaded = true;
        _tiles.Set(news.Stats);
        OnlineLoaded?.Invoke(news.Online);
        if (news.Notes.Count > 0) _link = news.Notes[0].Link;
        Render(news.Notes);
        if (news.Features.Count > 0) await ShowFeature(news.Features[0]);
    }

    // Osama 23 Nov 2026: "the launcher's online now never updates, this should poll information every 5 minutes".
    // Every 5 minutes the battlefield numbers are read again (the site writes news.json every 5 minutes); the notes stay as they are,
    // so the reader's scroll position is kept. If the first read failed, the whole news is tried again.
    private readonly System.Windows.Forms.Timer _refresh = new() { Interval = 5 * 60 * 1000 };
    private bool _loaded;

    private async Task RefreshAsync()
    {
        if (!_loaded) { await LoadAsync(); return; }
        var news = await LauncherNews.LoadAsync();
        if (news != null && !IsDisposed) { _tiles.Set(news.Stats); OnlineLoaded?.Invoke(news.Online); }
    }

    /// <summary>The newest feature, shown first: title, a line of text and its animated picture.</summary>
    private async Task ShowFeature(LauncherNews.Feature f)
    {
        _featureTitle.Text = Loc.IsChinese && f.TitleZh.Length > 0 ? f.TitleZh : f.Title;
        _featureText.Text = Loc.IsChinese && f.TextZh.Length > 0 ? f.TextZh : f.Text;
        _cols.ColumnStyles[0] = new ColumnStyle(SizeType.Percent, 50);
        _cols.ColumnStyles[1] = new ColumnStyle(SizeType.Percent, 50);
        if (f.Image.Length == 0) return;
        var bytes = await LauncherNews.LoadImageAsync(f.Image);
        if (bytes == null || IsDisposed) return;
        try
        {
            _imageData = new MemoryStream(bytes);
            _featureImage.Image = Image.FromStream(_imageData);   // PictureBox plays an animated GIF by itself
            FitImage();
        }
        catch (Exception) { _imageData = null; }
    }

    private void FitImage()
    {
        if (_featureImage.Image is not Image img || img.Width == 0) return;
        var h = _featureImage.Width * img.Height / img.Width;
        if (_featureImage.Height != h) _featureImage.Height = h;
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

    private static Control Gap(int h, DockStyle dock = DockStyle.Top) => new Panel { Dock = dock, Height = h, BackColor = Theme.Panel };

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

    /// <summary>4 tiles in a row, like the front page's Battlefield report.</summary>
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
                (T("PEAK, ALL TIME"), _s?.PeakAllTime, T("players in game")),
                (T("PLAYERS"), _s?.Players, T("all time")),
                (T("MATCHES"), _s?.Matches, T("all time")),
            };
            int gap = LogicalToDeviceUnits(8);
            int w = (Width - 3 * gap) / 4, h = Height;   // one row of 4
            using var label = Theme.Head(9.5f, semi: true);
            using var value = Theme.Head(19f);
            using var sub = Theme.Ui(8.25f);
            for (int i = 0; i < items.Length; i++)
            {
                var r = new Rectangle(i * (w + gap), 0, w, h);
                using (var fill = new SolidBrush(Theme.Surface)) g.FillRectangle(fill, r);
                using (var edge = new Pen(Theme.Border)) g.DrawRectangle(edge, r.X, r.Y, r.Width - 1, r.Height - 1);
                using (var strip = new SolidBrush(i == 0 ? Theme.Accent : Theme.Border))
                    g.FillRectangle(strip, r.X, r.Y, r.Width, Math.Max(2, LogicalToDeviceUnits(2)));
                int pad = LogicalToDeviceUnits(10);
                var f = TextFormatFlags.NoPadding | TextFormatFlags.NoPrefix | TextFormatFlags.EndEllipsis;
                TextRenderer.DrawText(g, items[i].Label, label, new Rectangle(r.X + pad, r.Y + LogicalToDeviceUnits(8), r.Width - 2 * pad, LogicalToDeviceUnits(16)), Theme.TextMuted, f);
                TextRenderer.DrawText(g, items[i].Value?.ToString("N0") ?? "—", value, new Rectangle(r.X + pad, r.Y + LogicalToDeviceUnits(21), r.Width - 2 * pad, LogicalToDeviceUnits(28)), Theme.Text, f);
                TextRenderer.DrawText(g, items[i].Sub, sub, new Rectangle(r.X + pad, r.Bottom - LogicalToDeviceUnits(18), r.Width - 2 * pad, LogicalToDeviceUnits(15)), Theme.TextMuted, f);
            }
        }
    }
}
