use std::{
    collections::HashMap,
    fs,
    io::{stdout, Read},
    path::{Path, PathBuf},
    process::Command,
    time::{Duration, Instant},
};

use anyhow::{bail, Context, Result};
use crossterm::{
    event::{self, Event, KeyCode, KeyEventKind},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use directories::BaseDirs;
use ratatui::{
    backend::CrosstermBackend,
    prelude::*,
    widgets::{Block, Borders, List, ListItem, ListState, Paragraph, Wrap},
    Terminal,
};
use serde::Deserialize;
use unicode_width::UnicodeWidthChar;

const CONFIG_RELATIVE_PATH: &str = ".config/claude-switcher/config.json";
const TICK_RATE: Duration = Duration::from_millis(200);
const STATUS_TTL: Duration = Duration::from_secs(8);

fn main() -> Result<()> {
    let config_path = resolve_config_path()?;
    let config = load_config(&config_path)?;
    let mut app = AppState::new(config_path, config);
    run_app(&mut app)
}

fn resolve_config_path() -> Result<PathBuf> {
    let base_dirs = BaseDirs::new().context("无法定位用户主目录，请确认系统用户信息")?;
    Ok(base_dirs.home_dir().join(CONFIG_RELATIVE_PATH))
}

fn load_config(path: &Path) -> Result<ConfigFile> {
    let mut file = fs::File::open(path).with_context(|| {
        format!(
            "无法读取配置文件：{}\n请先运行 vibe-switcher 完成至少一次配置",
            path.display()
        )
    })?;
    let mut buf = String::new();
    file.read_to_string(&mut buf)?;
    let config: ConfigFile =
        serde_json::from_str(&buf).context("配置文件格式错误，无法解析 JSON")?;
    Ok(config)
}

fn run_app(app: &mut AppState) -> Result<()> {
    enable_raw_mode()?;
    let mut stdout = stdout();
    execute!(stdout, EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;
    let result = app_loop(app, &mut terminal);
    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    terminal.show_cursor()?;
    result
}

fn app_loop<B: Backend>(app: &mut AppState, terminal: &mut Terminal<B>) -> Result<()> {
    loop {
        terminal.draw(|frame| draw_ui(frame, app))?;
        if event::poll(TICK_RATE)? {
            if let Event::Key(key_event) = event::read()? {
                if key_event.kind == KeyEventKind::Press {
                    match key_event.code {
                        KeyCode::Char('q') | KeyCode::Esc => break,
                        KeyCode::Tab | KeyCode::BackTab => app.toggle_service(),
                        KeyCode::Char('h') => app.select_service(ServiceKind::Claude),
                        KeyCode::Char('l') => app.select_service(ServiceKind::Codex),
                        KeyCode::Up | KeyCode::Char('k') => app.move_selection(-1),
                        KeyCode::Down | KeyCode::Char('j') => app.move_selection(1),
                        KeyCode::Enter => match app.switch_current_provider() {
                            Ok(()) => app.set_status(StatusMessage::success(
                                "切换完成，配置已刷新".to_string(),
                            )),
                            Err(err) => {
                                app.set_status(StatusMessage::error(format!("切换失败：{err}")))
                            }
                        },
                        KeyCode::Char('r') => match app.manual_reload() {
                            Ok(()) => app
                                .set_status(StatusMessage::info("已重新读取配置文件".to_string())),
                            Err(err) => {
                                app.set_status(StatusMessage::error(format!("刷新失败：{err}")))
                            }
                        },
                        _ => {}
                    }
                }
            }
        }
        app.on_tick();
    }
    Ok(())
}

fn draw_ui(frame: &mut Frame<'_>, app: &AppState) {
    let layout = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),
            Constraint::Min(10),
            Constraint::Length(7),
        ])
        .split(frame.size());

    let top_text = Paragraph::new(
        "Tab/Shift+Tab 或 h/l 切换服务，↑/↓ 选择中转商，Enter 执行切换，r 重新读取配置，q 退出",
    )
    .block(Block::default().borders(Borders::ALL).title("使用提示"));
    frame.render_widget(top_text, layout[0]);

    let lists_area = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(50), Constraint::Percentage(50)])
        .split(layout[1]);

    render_provider_list(
        frame,
        lists_area[0],
        "Claude Code",
        &app.claude,
        app.selected_service == ServiceKind::Claude,
        app.claude_index,
    );
    render_provider_list(
        frame,
        lists_area[1],
        "Codex",
        &app.codex,
        app.selected_service == ServiceKind::Codex,
        app.codex_index,
    );

    let bottom_area = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Min(4), Constraint::Length(3)])
        .split(layout[2]);

    render_detail(frame, bottom_area[0], app.current_provider());
    render_status(frame, bottom_area[1], app.status.as_ref());
}

fn render_provider_list(
    frame: &mut Frame<'_>,
    area: Rect,
    title: &str,
    providers: &[ProviderDisplay],
    is_active: bool,
    index: usize,
) {
    let inner_width = area.width.saturating_sub(6).max(10) as usize;
    let items: Vec<ListItem> = providers
        .iter()
        .map(|p| p.to_list_item(inner_width))
        .collect();
    let block = Block::default()
        .title(title)
        .borders(Borders::ALL)
        .border_style(if is_active {
            Style::default().fg(Color::Cyan)
        } else {
            Style::default().fg(Color::DarkGray)
        });
    let list = List::new(items)
        .highlight_style(Style::default().add_modifier(Modifier::BOLD))
        .highlight_symbol("")
        .block(block);
    let mut state = ListState::default();
    if !providers.is_empty() {
        state.select(Some(index.min(providers.len() - 1)));
    }
    frame.render_stateful_widget(list, area, &mut state);
}

fn render_detail(frame: &mut Frame<'_>, area: Rect, provider: Option<&ProviderDisplay>) {
    let block = Block::default().title("详细信息").borders(Borders::ALL);
    let text = match provider {
        Some(p) => p.detail_text(),
        None => Paragraph::new("暂无数据，先在配置中添加中转商。").alignment(Alignment::Center),
    };
    frame.render_widget(text.block(block), area);
}

fn render_status(frame: &mut Frame<'_>, area: Rect, status: Option<&StatusMessage>) {
    let (content, style) = match status {
        Some(message) => (message.text.clone(), message.style()),
        None => (
            "随时按 r 刷新配置，Enter 应用选择".to_string(),
            Style::default(),
        ),
    };
    let paragraph = Paragraph::new(content)
        .style(style)
        .block(Block::default().borders(Borders::ALL).title("状态"));
    frame.render_widget(paragraph, area);
}

#[derive(Debug, Clone, Deserialize, Default)]
struct ConfigFile {
    #[serde(default)]
    providers: HashMap<String, ClaudeProvider>,
    #[serde(default)]
    codex_providers: HashMap<String, CodexProvider>,
    #[serde(default)]
    current: Option<String>,
    #[serde(default)]
    current_codex: Option<String>,
}

#[derive(Debug, Clone, Deserialize, Default)]
struct ClaudeProvider {
    #[serde(default)]
    token: String,
    #[serde(default)]
    base_url: String,
}

#[derive(Debug, Clone, Deserialize, Default)]
struct CodexProvider {
    #[serde(default)]
    api_key: String,
    #[serde(default)]
    base_url: String,
    #[serde(default)]
    network_access: String,
    #[serde(default)]
    requires_openai_auth: Option<bool>,
    #[serde(default)]
    disable_response_storage: Option<bool>,
    #[serde(default)]
    wire_api: Option<String>,
    #[serde(default)]
    env_key: Option<String>,
}

#[derive(Debug, Clone)]
struct ProviderDisplay {
    name: String,
    base_url: String,
    credential_label: String,
    credential_preview: String,
    extras_line: Option<String>,
    detail_fields: Vec<DetailField>,
    is_current: bool,
    configured: bool,
}

impl ProviderDisplay {
    fn to_list_item(&self, width: usize) -> ListItem<'static> {
        let marker = if self.is_current {
            "[当前]"
        } else {
            "[候选]"
        };
        let mut content = vec![
            format!("{marker} {}", self.name),
            format!("URL: {}", self.base_url),
            format!("{}: {}", self.credential_label, self.credential_preview),
        ];
        if let Some(extra) = &self.extras_line {
            content.push(extra.clone());
        }
        if !self.configured {
            content.push("状态: 尚未配置凭证".to_string());
        }
        let lines = boxed_lines(&content, width);
        ListItem::new(lines)
    }

    fn detail_text(&self) -> Paragraph<'static> {
        let mut content = String::new();
        for DetailField { label, value } in &self.detail_fields {
            content.push_str(label);
            content.push_str(": ");
            content.push_str(value);
            content.push('\n');
        }
        Paragraph::new(content).wrap(Wrap { trim: true })
    }
}

#[derive(Debug, Clone)]
struct DetailField {
    label: &'static str,
    value: String,
}

impl DetailField {
    fn new(label: &'static str, value: impl Into<String>) -> Self {
        Self {
            label,
            value: value.into(),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ServiceKind {
    Claude,
    Codex,
}

impl ServiceKind {
    fn to_cli_namespace(self) -> &'static str {
        match self {
            ServiceKind::Claude => "claude",
            ServiceKind::Codex => "codex",
        }
    }
}

struct AppState {
    config_path: PathBuf,
    config: ConfigFile,
    claude: Vec<ProviderDisplay>,
    codex: Vec<ProviderDisplay>,
    claude_index: usize,
    codex_index: usize,
    selected_service: ServiceKind,
    status: Option<StatusMessage>,
}

impl AppState {
    fn new(config_path: PathBuf, config: ConfigFile) -> Self {
        let mut app = Self {
            config_path,
            config,
            claude: Vec::new(),
            codex: Vec::new(),
            claude_index: 0,
            codex_index: 0,
            selected_service: ServiceKind::Claude,
            status: None,
        };
        app.rebuild_providers();
        if app.claude.is_empty() && !app.codex.is_empty() {
            app.selected_service = ServiceKind::Codex;
        }
        app.focus_current(app.selected_service);
        app
    }

    fn rebuild_providers(&mut self) {
        self.claude =
            build_claude_providers(&self.config.providers, self.config.current.as_deref());
        self.codex = build_codex_providers(
            &self.config.codex_providers,
            self.config.current_codex.as_deref(),
        );
        self.sync_indexes();
    }

    fn sync_indexes(&mut self) {
        self.claude_index = clamp_index(
            &self.claude,
            self.config.current.as_deref(),
            self.claude_index,
        );
        self.codex_index = clamp_index(
            &self.codex,
            self.config.current_codex.as_deref(),
            self.codex_index,
        );
    }

    fn toggle_service(&mut self) {
        self.selected_service = match self.selected_service {
            ServiceKind::Claude => ServiceKind::Codex,
            ServiceKind::Codex => ServiceKind::Claude,
        };
        self.focus_current(self.selected_service);
    }

    fn select_service(&mut self, service: ServiceKind) {
        self.selected_service = service;
        self.focus_current(service);
    }

    fn move_selection(&mut self, delta: isize) {
        match self.selected_service {
            ServiceKind::Claude => {
                self.claude_index = move_index(self.claude_index, self.claude.len(), delta);
            }
            ServiceKind::Codex => {
                self.codex_index = move_index(self.codex_index, self.codex.len(), delta);
            }
        }
    }

    fn current_provider(&self) -> Option<&ProviderDisplay> {
        match self.selected_service {
            ServiceKind::Claude => self.claude.get(self.claude_index),
            ServiceKind::Codex => self.codex.get(self.codex_index),
        }
    }

    fn current_selection_name(&self) -> Option<&str> {
        self.current_provider().map(|p| p.name.as_str())
    }

    fn switch_current_provider(&mut self) -> Result<()> {
        let provider = self
            .current_selection_name()
            .context("没有可用的中转商，请先在配置中添加")?;
        let service = self.selected_service;
        let output = Command::new("vibe-switcher")
            .arg(service.to_cli_namespace())
            .arg("switch")
            .arg(provider)
            .output()
            .with_context(|| {
                format!(
                    "调用 vibe-switcher {} switch {} 失败",
                    service.to_cli_namespace(),
                    provider
                )
            })?;
        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            bail!("vibe-switcher 返回错误：{}", stderr.trim());
        }
        self.reload_config()?;
        Ok(())
    }

    fn manual_reload(&mut self) -> Result<()> {
        self.reload_config()
    }

    fn reload_config(&mut self) -> Result<()> {
        self.config = load_config(&self.config_path)?;
        self.rebuild_providers();
        Ok(())
    }

    fn set_status(&mut self, status: StatusMessage) {
        self.status = Some(status);
    }

    fn focus_current(&mut self, service: ServiceKind) {
        match service {
            ServiceKind::Claude => {
                self.claude_index = clamp_index(
                    &self.claude,
                    self.config.current.as_deref(),
                    self.claude_index,
                );
            }
            ServiceKind::Codex => {
                self.codex_index = clamp_index(
                    &self.codex,
                    self.config.current_codex.as_deref(),
                    self.codex_index,
                );
            }
        }
    }

    fn on_tick(&mut self) {
        if let Some(status) = &self.status {
            if status.created_at.elapsed() > STATUS_TTL {
                self.status = None;
            }
        }
    }
}

fn move_index(current: usize, len: usize, delta: isize) -> usize {
    if len == 0 {
        return 0;
    }
    let len_i = len as isize;
    let mut new = current as isize + delta;
    if new < 0 {
        new = len_i - 1;
    } else if new >= len_i {
        new = 0;
    }
    new as usize
}

fn clamp_index(
    providers: &[ProviderDisplay],
    current_name: Option<&str>,
    fallback: usize,
) -> usize {
    if providers.is_empty() {
        return 0;
    }
    if let Some(name) = current_name {
        if let Some(idx) = providers.iter().position(|p| p.name == name) {
            return idx;
        }
    }
    fallback.min(providers.len() - 1)
}

fn build_claude_providers(
    providers: &HashMap<String, ClaudeProvider>,
    current: Option<&str>,
) -> Vec<ProviderDisplay> {
    let mut entries: Vec<_> = providers.iter().collect();
    entries.sort_by(|a, b| a.0.cmp(b.0));
    entries
        .into_iter()
        .map(|(name, provider)| {
            let configured = !provider.token.trim().is_empty();
            ProviderDisplay {
                name: name.clone(),
                base_url: provider.base_url.clone(),
                credential_label: "Token".to_string(),
                credential_preview: mask_secret(&provider.token),
                extras_line: None,
                detail_fields: vec![
                    DetailField::new("服务", "Claude Code"),
                    DetailField::new("基础地址", &provider.base_url),
                    DetailField::new("Token", mask_secret(&provider.token)),
                ],
                is_current: current == Some(name.as_str()),
                configured,
            }
        })
        .collect()
}

fn build_codex_providers(
    providers: &HashMap<String, CodexProvider>,
    current: Option<&str>,
) -> Vec<ProviderDisplay> {
    let mut entries: Vec<_> = providers.iter().collect();
    entries.sort_by(|a, b| a.0.cmp(b.0));
    entries
        .into_iter()
        .map(|(name, provider)| {
            let configured = !provider.api_key.trim().is_empty();
            let extras = if provider.network_access.is_empty() {
                None
            } else {
                Some(format!("网络权限: {}", provider.network_access))
            };
            let mut detail_fields = vec![
                DetailField::new("服务", "Codex"),
                DetailField::new("基础地址", &provider.base_url),
                DetailField::new("API Key", mask_secret(&provider.api_key)),
            ];
            if !provider.network_access.is_empty() {
                detail_fields.push(DetailField::new("Network Access", &provider.network_access));
            }
            if let Some(flag) = provider.requires_openai_auth {
                detail_fields.push(DetailField::new(
                    "Requires OpenAI Auth",
                    if flag { "是" } else { "否" },
                ));
            }
            if let Some(flag) = provider.disable_response_storage {
                detail_fields.push(DetailField::new(
                    "Disable Storage",
                    if flag { "是" } else { "否" },
                ));
            }
            if let Some(wire_api) = &provider.wire_api {
                detail_fields.push(DetailField::new("Wire API", wire_api));
            }
            if let Some(env_key) = &provider.env_key {
                detail_fields.push(DetailField::new("绑定环境变量", env_key));
            }
            ProviderDisplay {
                name: name.clone(),
                base_url: provider.base_url.clone(),
                credential_label: "API Key".to_string(),
                credential_preview: mask_secret(&provider.api_key),
                extras_line: extras,
                detail_fields,
                is_current: current == Some(name.as_str()),
                configured,
            }
        })
        .collect()
}

fn mask_secret(secret: &str) -> String {
    let trimmed = secret.trim();
    if trimmed.is_empty() {
        "未配置".to_string()
    } else if trimmed.len() <= 6 {
        format!("{}***", &trimmed[..1])
    } else {
        format!(
            "{}***{}",
            &trimmed[..3.min(trimmed.len())],
            &trimmed[trimmed.len().saturating_sub(2)..]
        )
    }
}

fn boxed_lines(content: &[String], width: usize) -> Vec<Line<'static>> {
    let inner_width = width.saturating_sub(2).max(4);
    let horizontal = "─".repeat(inner_width);
    let mut lines = Vec::with_capacity(content.len() + 3);
    lines.push(Line::from(format!("┌{}┐", horizontal)));
    for item in content {
        lines.push(Line::from(format!("│{}│", pad_text(item, inner_width))));
    }
    lines.push(Line::from(format!("└{}┘", horizontal)));
    lines.push(Line::from(""));
    lines
}

fn pad_text(text: &str, inner_width: usize) -> String {
    if inner_width == 0 {
        return String::new();
    }
    let trimmed = text.trim();
    if trimmed.is_empty() {
        return " ".repeat(inner_width);
    }
    let mut buf = String::new();
    let mut width = 0;
    let mut truncated = false;
    for ch in trimmed.chars() {
        let ch_width = UnicodeWidthChar::width(ch).unwrap_or(1);
        if width + ch_width > inner_width {
            truncated = true;
            break;
        }
        buf.push(ch);
        width += ch_width;
    }
    if truncated {
        let ellipsis_width = UnicodeWidthChar::width('…').unwrap_or(1);
        if ellipsis_width <= inner_width {
            let target = inner_width - ellipsis_width;
            buf.clear();
            width = 0;
            for ch in trimmed.chars() {
                let ch_width = UnicodeWidthChar::width(ch).unwrap_or(1);
                if width + ch_width > target {
                    break;
                }
                buf.push(ch);
                width += ch_width;
            }
            buf.push('…');
            width += ellipsis_width;
        }
    }
    if width < inner_width {
        buf.push_str(&" ".repeat(inner_width - width));
    }
    buf
}

#[derive(Debug, Clone)]
struct StatusMessage {
    text: String,
    kind: StatusKind,
    created_at: Instant,
}

impl StatusMessage {
    fn info(text: String) -> Self {
        Self {
            text,
            kind: StatusKind::Info,
            created_at: Instant::now(),
        }
    }

    fn success(text: String) -> Self {
        Self {
            text,
            kind: StatusKind::Success,
            created_at: Instant::now(),
        }
    }

    fn error(text: String) -> Self {
        Self {
            text,
            kind: StatusKind::Error,
            created_at: Instant::now(),
        }
    }

    fn style(&self) -> Style {
        match self.kind {
            StatusKind::Info => Style::default().fg(Color::White),
            StatusKind::Success => Style::default().fg(Color::Green),
            StatusKind::Error => Style::default().fg(Color::Red),
        }
    }
}

#[derive(Debug, Clone, Copy)]
enum StatusKind {
    Info,
    Success,
    Error,
}
