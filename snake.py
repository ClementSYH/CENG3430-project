import copy
import curses
import random
import os
import time
from pynq import Overlay


# Defining objects for type hints
#Food = List[int]  # size 2, [x,y] coordinates
#Snake = List[List[int]]  # size Nx2, with N being Snake's length
#Grid = List[List[str]]  # size NxM, with N being the height and M being the width of the grid
# VGA allows 12 bit color video output



DIFFICULTIES = {
    '1': 500,
    '2': 200,
    '3': 40
}

class GameBody:
    def __init__(self, bitfile_path):
        self.ol = Overlay(bitfile_path)
        print("Available IPs in overlay:")
        for name in self.ol.ip_dict:
            print(name)
        print("End of IP block")
        self.led = self.ol.led.channel1
        self.switches = self.ol.sw.channel1
        self.btn = self.ol.btn.channel1
        self.score = 0
        self.w, self.h = 1024, 600 # VGA/display dimension
        self.grid = [[' ' for _ in range(self.w)] for _ in range(self.h)]
        self.last_1hz = time.time() #probably needs the clock to maintain system
        self.last_4hz = time.time()
        self.last_btn_press = time.time()
        self.btn_pressed = False

    def read_inputs(self):
        current_time = time.time()
        self.last_btn_press = current_time
        btn_val = self.btn.read()
        return {
            'din': self.switches.read() & 0x0F,
            'btn_c': (btn_val & 0x01) == 0x01,     # bit 0 -> Center
            'btn_u': (btn_val & 0x02) == 0x02,     # bit 1 -> Up
            'btn_d': (btn_val & 0x04) == 0x04,     # bit 2 -> Down
            'btn_l': (btn_val & 0x08) == 0x08,     # bit 3 -> Left
            'btn_r': (btn_val & 0x10) == 0x10,     # bit 4 -> Right
        }

    def inputs_to_key(self, inputs):
        # converts input to key
        if inputs['btn_u']:
            return 'up'
        elif inputs['btn_d']:
            return 'down'
        elif inputs['btn_l']:
            return 'left'
        elif inputs['btn_r']:
            return 'right'
        return None

    def select_difficulty(self):
        while True:
            answer = input('Select game difficulty:\n(1): Easy\n(2): Normal\n(3): Hard\nYour choice: ')
            if answer in DIFFICULTIES.keys():
                print("Difficulty is : ", answer)
                return DIFFICULTIES[answer]
            print('Invalid option, please type 1, 2 or 3.\n')

    def init_snake(self):
        snake1 = [
            [15, 10],
            [14, 10],
            [13, 10],
        ]
        return snake1

    def draw_snake(self, snake):
        #grid: Grid, snake: Snake -> None, controls VGA
        snake_head, snake_body = snake[0], snake[1:]
        self.grid[snake_head[0]][snake_head[1]] = '@'
        for part in snake_body:
            self.grid[part[0]][part[1]] = '#'

    def draw_food(self, food):
                #grid: Grid, food: Food -> None, controls VGA
        self.grid[food[0]][food[1]] = 'F'

    def snake_hit_wall(self, snake, window_size):
        #snake: Snake, window_size: Tuple[int, int] -> bool, T if snake hits wall
        head = snake[0]
        for dim, h in zip(window_size, head):
            if not 0 < h < (dim-1):
                return True
        return False

    def snake_hit_self(self, snake):
        #snake: Snake -> bool , T if snake hit itself
        return snake[0] in snake[1:]

    def snake_changed_direction(self, direction, inputs):
        """Checks whether the user pressed a key that's in a different direction
        compared to the direction of the snake's movement."""
        # direction: str, inputs: dict -> bool
        Opposite = {
                'btn_u': 'down',
                'btn_d': 'up',
                'btn_l': 'right',
                'btn_r': 'left'
                }
        for k, d in Opposite.items():
            if key == k and direction == d:
                return False
        return True
    
    def extend_snake_head(self, snake, direction):
        """Extends the snake head one space in the given direction.
        The body remains in the same position."""
        #snake: Snake, direction: str -> None
        head = copy.copy(snake[0])
        if direction == 'left':  # increase X coord by 1
            head[1] -= 1
        elif direction == 'right':  # decrease X coord by 1
            head[1] += 1
        elif direction == 'up':  # decrease Y coord by 1
            head[0] -= 1
        elif direction == 'down':  # increase Y coord by 1
            head [0] += 1
        print(direction)
        snake.insert(0, head)

    def Gen_food(self, Widow_size):
        #window_size: tuple[int, int] -> None
        food = [random.randint(1, self.h-2), random.randint(1, self.w-2)]
        return food

    def snake_ate_food(self, snake, food):
        #snake: Snake, food: Food -> snake[0]
        """Checks whether the Snake has eaten the Food."""
        return snake[0] == food

    def shorten_snake(self, snake):
        #snake: Snake
        tail = snake.pop()
        #window.addch(*tail, ' ') # clears the tail on screen, figure out how to do this without window

    def game_is_over(self, snake, window_size):
        #snake: SNAKE, window_size: tuple[int, int] -> bool
        print("hit wall: ", self.snake_hit_wall(snake, window_size))
        print("hit self: ", self.snake_hit_self(snake))
        return self.snake_hit_wall(snake, window_size) or self.snake_hit_self(snake)

    def run(self):
        #Game logic, returns score: int
        window_size = [self.w, self.h]  # (x, y) of VGA display
        snake = self.init_snake()  # starting snake
        self.draw_snake(snake)
        food = self.Gen_food(window_size)  # generate food
        self.draw_food(food)  # draw food on the screen
        inputs = self.read_inputs()
        DIRECTIONS = {
            inputs['btn_l']: 'left',
            inputs['btn_r']: 'right',
            inputs['btn_u']: 'up',
            inputs['btn_d']: 'down'
        }
        # set initial direction for snake 1
        key, direction = 'btn_d', 'down'
        print(inputs)
        print(self.last_btn_press, self.btn_pressed)
        while inputs['btn_c'] == 0:
            time.sleep(0.01)  # wait for signal
            inputs = self.read_inputs() # need to loop func to read signal
            print("press BTNC to start")
        print("Signal received!")
        while True:
            next_key = self.inputs_to_key(self.read_inputs())
            key = next_key if next_key != -1 else key
            print("This is Key: ", key)
            direction = DIRECTIONS[key] if self.snake_changed_direction(direction, key) else direction
            self.extend_snake_head(snake, direction) # changes the snake direction
            if self.snake_ate_food(snake, food):
                food = self.Gen_food(window_size)
                self.draw_food(self.grid, food)
                self.score += 1
            else:
                tail = self.shorten_snake(self.grid, snake)
            if self.game_is_over(snake, window_size):
                return self.score
            self.draw_snake(self.grid, snake)

def print_score(score):
    """Prints the score onto the screen."""
    print('Game Over!')
    print('Best Score:', score)

def main():
    #return none
    game = GameBody("./Zedboard_AXIGPIO.bit") #pass the difficulty in later
    score = game.run()
    print_score(score=score)


if __name__ == '__main__':
    main()