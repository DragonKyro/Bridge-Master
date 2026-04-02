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
SOUTH_Y = 100
SOUTH_X_START = SCREEN_WIDTH // 2 - 6 * CARD_FAN_OFFSET

# North (top, dummy) - fanned horizontally
NORTH_Y = SCREEN_HEIGHT - 100
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

# Colors
BG_COLOR = (0, 100, 0)       # dark green felt
TEXT_COLOR = (255, 255, 255)
HIGHLIGHT_COLOR = (255, 255, 0, 80)
BUTTON_COLOR = (50, 50, 120)
BUTTON_HOVER = (80, 80, 160)
BUTTON_TEXT = (255, 255, 255)

# Fonts
FONT_SIZE_LARGE = 28
FONT_SIZE_MEDIUM = 18
FONT_SIZE_SMALL = 14
