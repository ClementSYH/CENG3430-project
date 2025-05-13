import pygame as pg
import cv2
import mediapipe as mp
from random import randrange

# --- Settings ---
WINDOW = 750
TILE_SIZE = 25
RANGE = (TILE_SIZE // 2, WINDOW - TILE_SIZE // 2, TILE_SIZE)
get_random_position = lambda: [randrange(*RANGE), randrange(*RANGE)]

# --- Init ---
pg.init()
screen = pg.display.set_mode([WINDOW] * 2)
clock = pg.time.Clock()
font = pg.font.SysFont('Arial', 36)

# Camera and Mediapipe Init
cap = cv2.VideoCapture(0)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)

# Tracking hand movement
prev_positions = {'Left': None, 'Right': None}

# --- Game State ---
def reset_game():
    global snake1, snake2, dir1, dir2, segments1, segments2, len1, len2
    global food, time, game_over

    snake1 = pg.rect.Rect([0, 0, TILE_SIZE - 2, TILE_SIZE - 2])
    snake2 = pg.rect.Rect([0, 0, TILE_SIZE - 2, TILE_SIZE - 2])
    snake1.center = get_random_position()
    snake2.center = get_random_position()
    dir1, dir2 = (0, 0), (0, 0)
    len1 = len2 = 1
    segments1 = [snake1.copy()]
    segments2 = [snake2.copy()]
    food = snake1.copy()
    food.center = get_random_position()
    time = pg.time.get_ticks()
    game_over = False

reset_game()

# --- Game Over Screen ---
def waiting_for_restart(winner_msg):
    msg1 = font.render(winner_msg, True, 'white')
    msg2 = font.render("Press SPACE to Restart", True, 'white')
    rect1 = msg1.get_rect(center=(WINDOW // 2, WINDOW // 2 - 30))
    rect2 = msg2.get_rect(center=(WINDOW // 2, WINDOW // 2 + 30))
    screen.blit(msg1, rect1)
    screen.blit(msg2, rect2)
    pg.display.flip()

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                exit()
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                reset_game()
                return
        clock.tick(10)

# --- Collision Check ---
def is_dead(snake, segments, other_segments):
    return (
        snake.left < 0 or snake.right > WINDOW or
        snake.top < 0 or snake.bottom > WINDOW or
        pg.Rect.collidelist(snake, segments[:-1]) != -1 or
        pg.Rect.collidelist(snake, other_segments) != -1
    )

# --- Hand Movement Direction ---
def get_movement_direction(prev, current, threshold=0.05):
    dx = current[0] - prev[0]
    dy = current[1] - prev[1]

    if abs(dx) > abs(dy):
        if dx > threshold:
            return (TILE_SIZE, 0)  # Right
        elif dx < -threshold:
            return (-TILE_SIZE, 0)  # Left
    else:
        if dy > threshold:
            return (0, TILE_SIZE)  # Down
        elif dy < -threshold:
            return (0, -TILE_SIZE)  # Up
    return None

# --- Get Directions from Gesture Movement ---
def get_directions_from_gestures(frame):
    global prev_positions
    h, w, _ = frame.shape
    dir1 = dir2 = None

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if results.multi_hand_landmarks and results.multi_handedness:
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            label = handedness.classification[0].label  # 'Left' or 'Right'
            lm = hand_landmarks.landmark[0]  # Wrist
            current_pos = (lm.x, lm.y)

            if prev_positions[label]:
                movement_dir = get_movement_direction(prev_positions[label], current_pos)
                if label == 'Left':
                    dir1 = movement_dir
                else:
                    dir2 = movement_dir

            prev_positions[label] = current_pos

    return dir1, dir2, frame

# --- Main Loop ---
time_step = 200

while True:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            exit()

    screen.fill('black')

    ret, frame = cap.read()
    if not ret:
        continue

    gesture_dir1, gesture_dir2, frame = get_directions_from_gestures(frame)
    # print(f'Dir1: {gesture_dir1}, Dir2: {gesture_dir2}')

    if not game_over:
        # Update direction if valid
        if gesture_dir1 and gesture_dir1 != tuple(-x for x in dir1):
            dir1 = gesture_dir1
        if gesture_dir2 and gesture_dir2 != tuple(-x for x in dir2):
            dir2 = gesture_dir2

        # Check collision
        dead1 = is_dead(snake1, segments1, segments2)
        dead2 = is_dead(snake2, segments2, segments1)

        if dead1 or dead2:
            game_over = True
            if dead1 and dead2:
                winner_msg = "Draw!"
            elif dead1:
                winner_msg = "Cyan wins!"
            else:
                winner_msg = "Green wins!"
            waiting_for_restart(winner_msg)
            prev_positions = {'Left': None, 'Right': None}
            continue

        # Food in tail check
        if pg.Rect.collidelist(food, segments1[:-1] + segments2[:-1]) != -1:
            food.center = get_random_position()

        # Check food eaten
        if snake1.center == food.center:
            food.center = get_random_position()
            len1 += 1
        if snake2.center == food.center:
            food.center = get_random_position()
            len2 += 1

        # Move snakes
        now = pg.time.get_ticks()
        if now - time > time_step:
            time = now
            snake1.move_ip(dir1)
            segments1.append(snake1.copy())
            segments1 = segments1[-len1:]
            snake2.move_ip(dir2)
            segments2.append(snake2.copy())
            segments2 = segments2[-len2:]

    # Draw food
    pg.draw.rect(screen, 'red', food)
    # Draw snakes
    for segment in segments1:
        pg.draw.rect(screen, 'green', segment)
    for segment in segments2:
        pg.draw.rect(screen, 'cyan', segment)

    # Show webcam feed on screen (optional)
    small_cam = cv2.resize(frame, (150, 100))
    cam_surface = pg.surfarray.make_surface(cv2.cvtColor(small_cam, cv2.COLOR_BGR2RGB).swapaxes(0, 1))
    screen.blit(cam_surface, (WINDOW - 160, 10))

    pg.display.flip()
    clock.tick(60)
