"""mdir custom color themes."""

from textual.theme import Theme

# Korean flag: white, blue (#0047A0), red (#CD2E3A), black.
# Landscape: deep blue mountains, clear river water, bright sky.

KOREA_THEME = Theme(
    name="korea",
    primary="#0047A0",
    secondary="#5BA4D9",
    accent="#CD2E3A",
    warning="#E8A04C",
    error="#CD2E3A",
    success="#3A9E6F",
    foreground="#F2F6FC",
    background="#0B1420",
    surface="#132238",
    panel="#1A3050",
    dark=True,
    variables={
        "footer-key-foreground": "#5BA4D9",
        "footer-background": "#132238",
        "footer-description-foreground": "#A8C4E0",
        "border": "#0047A0",
        "border-blurred": "#2A4568",
        "block-cursor-background": "#0047A0",
        "block-cursor-foreground": "#F2F6FC",
        "block-cursor-text-style": "none",
        "input-cursor-background": "#CD2E3A",
        "input-cursor-foreground": "#F2F6FC",
        "input-selection-background": "#0047A0 45%",
        "button-color-foreground": "#0B1420",
        "scrollbar": "#0047A0",
        "scrollbar-hover": "#5BA4D9",
    },
)

KOREA_LIGHT_THEME = Theme(
    name="korea-light",
    primary="#0047A0",
    secondary="#2E6DB4",
    accent="#CD2E3A",
    warning="#C47A28",
    error="#CD2E3A",
    success="#2E7D52",
    foreground="#141820",
    background="#FAFCFF",
    surface="#EAF2FA",
    panel="#D4E6F5",
    dark=False,
    variables={
        "footer-key-foreground": "#0047A0",
        "footer-background": "#EAF2FA",
        "footer-description-foreground": "#3A5070",
        "border": "#0047A0",
        "border-blurred": "#A8C4E0",
        "block-cursor-background": "#0047A0",
        "block-cursor-foreground": "#FAFCFF",
        "block-cursor-text-style": "none",
        "input-cursor-background": "#CD2E3A",
        "input-cursor-foreground": "#FAFCFF",
        "input-selection-background": "#5BA4D9 35%",
        "button-color-foreground": "#FAFCFF",
        "scrollbar": "#0047A0",
        "scrollbar-hover": "#2E6DB4",
    },
)

MDIR_THEMES = (KOREA_THEME, KOREA_LIGHT_THEME)
