"""GUI constants and layout configuration."""

# Window
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 900
SCREEN_TITLE = "Bridge Master"

# Card images
CARD_WIDTH = 100
CARD_HEIGHT = 140
CARD_SCALE = 0.85
CARD_FAN_OFFSET = 28  # horizontal offset when fanning cards in a hand

# Table layout (positions for the 4 hands)
# South (bottom, declarer) - fanned horizontally
SOUTH_Y = 90
SOUTH_X_START = SCREEN_WIDTH // 2 - 6 * CARD_FAN_OFFSET

# North (top, dummy) - fanned horizontally
NORTH_Y = SCREEN_HEIGHT - 120
NORTH_X_START = SCREEN_WIDTH // 2 - 6 * CARD_FAN_OFFSET

# West (left) - fanned vertically (face down or small)
WEST_X = 120
WEST_Y_START = SCREEN_HEIGHT // 2 + 6 * 20

# East (right) - fanned vertically (face down or small)
EAST_X = SCREEN_WIDTH - 120
EAST_Y_START = SCREEN_HEIGHT // 2 + 6 * 20

# Trick area (center of table)
TRICK_CENTER_X = SCREEN_WIDTH // 2
TRICK_CENTER_Y = SCREEN_HEIGHT // 2
TRICK_OFFSETS = {
    # direction: (dx, dy) from center for played cards
    "SOUTH": (0, -70),
    "NORTH": (0, 70),
    "WEST": (-90, 0),
    "EAST": (90, 0),
}

# Direction label offsets from card positions
LABEL_SOUTH_Y = SOUTH_Y - 75
LABEL_NORTH_Y = NORTH_Y + 75
LABEL_WEST_Y = SCREEN_HEIGHT // 2 + 175
LABEL_EAST_Y = SCREEN_HEIGHT // 2 + 175

# Status bar
STATUS_BAR_Y = SCREEN_HEIGHT - 22
TOOLBAR_Y = SCREEN_HEIGHT - 55

# Trick history panel (bottom-left corner)
TRICK_PANEL_W = 220
TRICK_PANEL_H = 200
TRICK_PANEL_X = TRICK_PANEL_W // 2 + 10
TRICK_PANEL_Y = TRICK_PANEL_H // 2 + 10

# Animation
CARD_ANIM_SPEED = 1200  # pixels per second
TRICK_PAUSE_DURATION = 1.0  # seconds to show completed trick

# Colors
BG_COLOR = (0, 100, 0)       # dark green felt
TEXT_COLOR = (255, 255, 255)
HIGHLIGHT_COLOR = (255, 255, 0, 100)
INVALID_TINT = (150, 150, 150)
BUTTON_COLOR = (50, 50, 120)
BUTTON_HOVER = (80, 80, 160)
BUTTON_TEXT = (255, 255, 255)
NS_WIN_COLOR = (100, 200, 255)
EW_WIN_COLOR = (255, 160, 100)
PANEL_BG = (20, 60, 20, 200)

# Fonts
FONT_SIZE_LARGE = 28
FONT_SIZE_MEDIUM = 18
FONT_SIZE_SMALL = 14
FONT_SIZE_TINY = 11
