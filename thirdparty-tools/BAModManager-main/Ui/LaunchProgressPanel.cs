using System.Diagnostics;
using System.Drawing.Drawing2D;
using BAModManager.Core;
using static BAModManager.Core.Loc;

namespace BAModManager.Ui;

/// <summary>
/// 1.1.14 (Osama 21 Nov 2026: "People don't know if it's downloading something or stalling"): the launcher's PLAY progress.
/// A step list, the current action with a percentage bar, MB done / total, speed, time left, time spent, and a live line
/// that says when data last arrived, so a stalled download looks different from a slow one. Retries are shown, not hidden.
/// Everything is drawn here; the core code only reports <see cref="LaunchProgress"/>.
/// </summary>
internal sealed class LaunchProgressPanel : Control
{
    private enum Mode { Idle, Running, Done, Failed }

    private static readonly LaunchStage[] Steps = { LaunchStage.Mod, LaunchStage.Loader, LaunchStage.Assets, LaunchStage.Verify, LaunchStage.Start };

    // Seconds without new data before the live line changes colour. The downloads themselves retry after 60 s with no data.
    private const double QuietAfter = 4, WaitingAfter = 20, ProblemAfter = 90, NoteFor = 20;

    private readonly System.Windows.Forms.Timer _tick = new() { Interval = 100 };
    private readonly Stopwatch _clock = Stopwatch.StartNew();
    private Mode _mode = Mode.Idle;
    private LaunchStage? _stage;
    private string _title = "";
    private double? _fraction;
    private long? _done, _total;
    private double _rate;               // bytes per second, smoothed
    private long _sampleBytes;
    private double _sampleAt;
    private double _startedAt, _reportAt, _bytesAt, _stageAt;
    private string? _note;
    private double _noteAt;
    private float _phase;

    public LaunchProgressPanel()
    {
        SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
        BackColor = Theme.Background;
        _tick.Tick += (_, _) => { _phase = (_phase + 0.02f) % 1f; Invalidate(); };
    }

    private double Now => _clock.Elapsed.TotalSeconds;
    public bool Running => _mode == Mode.Running;

    /// <summary>Percent shown in the window title while running, or null.</summary>
    public int? Percent => _mode == Mode.Running && _fraction is double f ? (int)Math.Floor(Math.Clamp(f, 0, 1) * 100) : null;

    public void Begin(LaunchStage stage, string title)
    {
        _mode = Mode.Running;
        _startedAt = _reportAt = _bytesAt = _stageAt = Now;
        _note = null;
        SetStage(stage);
        _title = title;
        _fraction = null;
        _tick.Start();
        Invalidate();
    }

    public void Report(LaunchProgress p)
    {
        if (_mode != Mode.Running) Begin(p.Stage ?? LaunchStage.Mod, p.Text);
        var now = Now;
        _reportAt = now;
        if (p.Stage is LaunchStage s && s != _stage) SetStage(s);
        if (!string.IsNullOrEmpty(p.Text)) _title = p.Text;
        _fraction = p.Fraction;
        if (p.Done is long done && p.Total is long total && total > 0)
        {
            if (_done == null || done < _sampleBytes) { _sampleBytes = done; _sampleAt = now; _rate = 0; _bytesAt = now; }
            if (done > (_done ?? -1)) _bytesAt = now;
            var dt = now - _sampleAt;
            if (dt >= 0.75)
            {
                var rate = Math.Max(0, (done - _sampleBytes) / dt);
                _rate = _rate <= 0 ? rate : _rate * 0.75 + rate * 0.25;
                _sampleBytes = done;
                _sampleAt = now;
            }
            _done = done;
            _total = total;
        }
        else
        {
            _done = _total = null;
        }
        if (p.Note != null) { _note = p.Note; _noteAt = now; }
        Invalidate();
    }

    /// <summary>Ends the run: every step ticked (success) or the current step marked red, with <paramref name="message"/> as the title.</summary>
    public void Finish(bool ok, string message)
    {
        if (_mode != Mode.Running) return;
        _mode = ok ? Mode.Done : Mode.Failed;
        if (ok) _stage = null;
        _title = message;
        _note = null;
        _tick.Stop();
        Invalidate();
    }

    /// <summary>A plain message when no run is shown (and the last line under a finished run).</summary>
    public void SetMessage(string text)
    {
        if (_mode == Mode.Running) { if (text.Length > 0) { _title = text; Invalidate(); } return; }
        if (_mode is Mode.Done or Mode.Failed && (text.Length == 0 || text == _title)) return;   // keep the finished run on screen
        if (_mode == Mode.Failed) _mode = Mode.Idle;
        _title = text;
        Invalidate();
    }

    private void SetStage(LaunchStage stage)
    {
        _stage = stage;
        _note = null;   // a retry note belongs to the step it happened in
        _stageAt = _bytesAt = Now;
        _done = _total = null;
        _rate = 0;
        _sampleBytes = 0;
        _sampleAt = Now;
    }

    private float Dpi => DeviceDpi / 96f;
    private int S(float v) => (int)Math.Round(v * Dpi);

    protected override void OnPaint(PaintEventArgs e)
    {
        var g = e.Graphics;
        g.Clear(BackColor);
        g.SmoothingMode = SmoothingMode.AntiAlias;
        int w = Width;

        if (_mode == Mode.Idle)
        {
            using var f = Theme.Ui(9.5f);
            var idle = _title.Length > 0 ? _title : T("Press PLAY: the launcher checks and updates Freedom Arrow, shows every step here, then starts the game.");
            TextRenderer.DrawText(g, idle, f, new Rectangle(0, S(6), w, Height - S(6)), Theme.TextMuted,
                TextFormatFlags.WordBreak | TextFormatFlags.NoPrefix | TextFormatFlags.Left | TextFormatFlags.Top);
            return;
        }

        int y = 0;
        bool showSteps = _stage != LaunchStage.Launcher;
        if (showSteps) { DrawSteps(g, w); y = S(46); }

        // ── title + percent ──
        var titleColor = _mode switch { Mode.Done => Theme.Good, Mode.Failed => Theme.Bad, _ => Theme.Text };
        using (var pf = Theme.Head(17f))
        {
            string pct = _mode == Mode.Running && _fraction is double fr ? Math.Floor(Math.Clamp(fr, 0, 1) * 100) + "%" : "";
            int pw = pct.Length == 0 ? 0 : TextRenderer.MeasureText(g, pct, pf).Width;
            if (pct.Length > 0)
                TextRenderer.DrawText(g, pct, pf, new Rectangle(w - pw, y - S(2), pw, S(26)), Theme.Accent,
                    TextFormatFlags.Right | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPrefix);
            using var tf = Theme.Semibold(10.5f);
            TextRenderer.DrawText(g, _title, tf, new Rectangle(0, y, w - pw - S(8), S(24)), titleColor,
                TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.EndEllipsis | TextFormatFlags.NoPrefix);
        }
        y += S(28);

        // ── bar ──
        DrawBar(g, new RectangleF(0, y, w, S(8)));
        y += S(16);

        // ── MB, speed, time left | time spent ──
        using (var df = Theme.Ui(9f))
        {
            var spent = T("Time {0}", Clock(Now - _startedAt));
            int sw = TextRenderer.MeasureText(g, spent, df).Width;
            if (_mode == Mode.Running) TextRenderer.DrawText(g, spent, df, new Rectangle(w - sw, y, sw, S(20)), Theme.TextMuted, TextFormatFlags.Right | TextFormatFlags.NoPrefix);
            TextRenderer.DrawText(g, Details(), df, new Rectangle(0, y, w - sw - S(8), S(20)), Theme.TextMuted,
                TextFormatFlags.Left | TextFormatFlags.EndEllipsis | TextFormatFlags.NoPrefix);
        }
        y += S(22);

        // ── live line ──
        if (_mode == Mode.Running) DrawLiveLine(g, new Rectangle(0, y, w, Height - y));
    }

    private void DrawSteps(Graphics g, int w)
    {
        int n = Steps.Length;
        float seg = w / (float)n, r = S(9), cy = S(11);
        int active = _mode == Mode.Done ? n : _stage is LaunchStage st ? Array.IndexOf(Steps, st) : -1;
        // track
        using (var track = new Pen(Theme.Border, S(2)))
            g.DrawLine(track, seg / 2, cy, w - seg / 2, cy);
        if (active > 0)
            using (var done = new Pen(Theme.Accent, S(2)))
                g.DrawLine(done, seg / 2, cy, seg / 2 + seg * Math.Min(active, n - 1), cy);
        using var label = Theme.Head(9.5f, semi: true);
        using var num = Theme.Head(9f);
        for (int i = 0; i < n; i++)
        {
            float cx = seg * i + seg / 2;
            var dot = new RectangleF(cx - r, cy - r, r * 2, r * 2);
            bool done = i < active, now = i == active, failed = now && _mode == Mode.Failed;
            if (done || now)
            {
                if (now && !failed && _mode == Mode.Running)
                {
                    float pulse = (float)(0.5 + 0.5 * Math.Sin(_phase * Math.PI * 2));
                    float grow = r * (0.35f + 0.35f * pulse);
                    using var halo = new SolidBrush(Color.FromArgb((int)(90 * (1 - pulse * 0.6)), Theme.Accent));
                    g.FillEllipse(halo, cx - r - grow, cy - r - grow, (r + grow) * 2, (r + grow) * 2);
                }
                using var fill = new SolidBrush(failed ? Theme.Bad : Theme.Accent);
                g.FillEllipse(fill, dot);
                if (done)
                {
                    using var tick = new Pen(Color.White, S(2)) { StartCap = LineCap.Round, EndCap = LineCap.Round, LineJoin = LineJoin.Round };
                    g.DrawLines(tick, new[] { new PointF(cx - r * 0.45f, cy), new PointF(cx - r * 0.1f, cy + r * 0.38f), new PointF(cx + r * 0.5f, cy - r * 0.38f) });
                }
                else
                {
                    TextRenderer.DrawText(g, failed ? "!" : (i + 1).ToString(), num, Rectangle.Round(dot), Color.White,
                        TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding);
                }
            }
            else
            {
                using var fill = new SolidBrush(Theme.Surface);
                using var edge = new Pen(Theme.Border, S(1.5f));
                g.FillEllipse(fill, dot);
                g.DrawEllipse(edge, dot);
                TextRenderer.DrawText(g, (i + 1).ToString(), num, Rectangle.Round(dot), Theme.TextMuted,
                    TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding);
            }
            var text = StepName(Steps[i]).ToUpperInvariant();
            // A label wider than its step (MelonLoader in Chinese fonts) gets a smaller font instead of "…".
            using var small = TextRenderer.MeasureText(g, text, label).Width > seg - S(4) ? Theme.Head(8f, semi: true) : null;
            TextRenderer.DrawText(g, text, small ?? label, new Rectangle((int)(seg * i), (int)(cy + r + S(3)), (int)seg, S(18)),
                done || now ? Theme.Text : Theme.TextMuted, TextFormatFlags.HorizontalCenter | TextFormatFlags.Top | TextFormatFlags.NoPrefix | TextFormatFlags.EndEllipsis);
        }
    }

    private void DrawBar(Graphics g, RectangleF r)
    {
        using (var track = Theme.RoundRect(r, r.Height / 2))
        using (var tb = new SolidBrush(Theme.Surface))
            g.FillPath(tb, track);
        var color = _mode == Mode.Failed ? Theme.Bad : _mode == Mode.Done ? Theme.Good : Theme.Accent;
        if (_mode == Mode.Running && _fraction == null)
        {
            // Work without a percentage: a moving segment, so the window never looks frozen.
            float seg = r.Width * 0.28f, x = r.X + (_phase * 1.28f - 0.28f) * r.Width;
            var part = RectangleF.Intersect(new RectangleF(x, r.Y, seg, r.Height), r);
            if (part.Width > 1)
                using (var p = Theme.RoundRect(part, r.Height / 2))
                using (var b = new SolidBrush(color))
                    g.FillPath(b, p);
            return;
        }
        float f = _mode == Mode.Done ? 1f : (float)Math.Clamp(_fraction ?? 0, 0, 1);
        if (f <= 0) return;
        var fill = new RectangleF(r.X, r.Y, Math.Max(r.Height, r.Width * f), r.Height);
        using (var p = Theme.RoundRect(fill, r.Height / 2))
        using (var b = new SolidBrush(color))
            g.FillPath(b, p);
        if (_mode != Mode.Running || Now - _reportAt > QuietAfter) return;
        // A light sweep over the filled part while reports keep arriving.
        float sweep = fill.Width * 0.3f, sx = fill.X + (_phase * 1.3f - 0.3f) * fill.Width;
        var band = RectangleF.Intersect(new RectangleF(sx, fill.Y, sweep, fill.Height), fill);
        if (band.Width < 2) return;
        using var lg = new LinearGradientBrush(new RectangleF(band.X - 1, band.Y, band.Width + 2, band.Height), Color.FromArgb(0, Color.White), Color.FromArgb(0, Color.White), 0f);
        lg.InterpolationColors = new ColorBlend
        {
            Colors = new[] { Color.FromArgb(0, Color.White), Color.FromArgb(70, Color.White), Color.FromArgb(0, Color.White) },
            Positions = new[] { 0f, 0.5f, 1f },
        };
        using (var p = Theme.RoundRect(band, r.Height / 2)) g.FillPath(lg, p);
    }

    private string Details()
    {
        if (_mode != Mode.Running || _done is not long done || _total is not long total) return "";
        var parts = new List<string> { T("{0} / {1} MB", Mb(done), Mb(total)) };
        if (Now - _bytesAt >= QuietAfter) return parts[0];   // no data: no speed or time left that would look like progress
        if (_rate > 1024) parts.Add(T("{0} MB/s", (_rate / 1048576.0).ToString(_rate < 10 * 1048576.0 ? "0.0" : "0")));
        if (_rate > 1024 && total > done) parts.Add(T("about {0} left", Clock((total - done) / _rate)));
        return string.Join("   ·   ", parts);
    }

    private void DrawLiveLine(Graphics g, Rectangle r)
    {
        var now = Now;
        Color dot; string text;
        bool downloading = _done != null;
        double quiet = now - (downloading ? _bytesAt : _reportAt);
        if (_note != null && now - _noteAt < NoteFor) { dot = Theme.Warn; text = _note; }
        else if (downloading)
        {
            int s = (int)quiet;
            if (quiet < QuietAfter) { dot = Theme.Good; text = T("Downloading: data is arriving."); }
            else if (quiet < WaitingAfter) { dot = Theme.Warn; text = T("No data for {0} s. Waiting for the server…", s); }
            else if (quiet < ProblemAfter) { dot = Theme.Warn; text = T("No data for {0} s. Still waiting; the download restarts by itself at 60 s.", s); }
            else { dot = Theme.Bad; text = T("No data for {0} s. Check your internet or VPN. Closing and pressing PLAY again keeps finished files.", s); }
        }
        else
        {
            int s = (int)(now - _stageAt);
            if (quiet < QuietAfter) { dot = Theme.Good; text = T("Working: nothing to download in this step."); }
            else { dot = Theme.Warn; text = T("Still working on this step ({0} s). Checking big files can take minutes.", s); }
        }
        float pulse = (float)(0.55 + 0.45 * Math.Sin(_phase * Math.PI * 2));
        float d = S(8);
        using (var b = new SolidBrush(Color.FromArgb((int)(255 * pulse), dot)))
            g.FillEllipse(b, r.X, r.Y + S(5), d, d);
        using var f = Theme.Ui(9f);
        TextRenderer.DrawText(g, text, f, new Rectangle(r.X + S(16), r.Y, r.Width - S(16), r.Height), dot == Theme.Good ? Theme.TextMuted : dot,
            TextFormatFlags.Left | TextFormatFlags.Top | TextFormatFlags.WordBreak | TextFormatFlags.NoPrefix);
    }

    private static string StepName(LaunchStage s) => s switch
    {
        LaunchStage.Mod => T("Mod"),
        LaunchStage.Loader => "MelonLoader",
        LaunchStage.Assets => T("Models & music"),
        LaunchStage.Verify => T("Check"),
        LaunchStage.Start => T("Start"),
        _ => T("Launcher"),
    };

    private static string Mb(long bytes) => (bytes / 1048576.0).ToString(bytes < 10 * 1048576L ? "0.0" : "#,0");

    private static string Clock(double seconds)
    {
        var t = TimeSpan.FromSeconds(Math.Max(0, Math.Round(seconds)));
        return t.TotalHours >= 1 ? $"{(int)t.TotalHours}:{t.Minutes:00}:{t.Seconds:00}" : $"{t.Minutes}:{t.Seconds:00}";
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing) _tick.Dispose();
        base.Dispose(disposing);
    }
}
