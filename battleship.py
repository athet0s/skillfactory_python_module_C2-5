from random import randint


class GameException(Exception):
    pass


class BoardOutException(GameException):
    pass


class InvalidTarget(GameException):
    pass


class InvalidShip(GameException):
    pass


class Dot:
    def __init__(self, x, y):
        self._x = x
        self._y = y

    def __eq__(self, other):
        return self.coordinates == other.coordinates

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def coordinates(self):
        return self._x, self._y


# класс клетки игрового поля
class Cell(Dot):
    STATE_EMPTY = 0
    STATE_MISSED = 1
    STATE_OCCUPIED_BY_SHIP = 2
    STATE_OCCUPIED_BY_DAMAGED_SHIP = 3

    _visualisations = ("O", "T", "■", "X")

    def __init__(self, x, y, state=None):
        super().__init__(x, y)
        if not state:
            self._state = self.STATE_EMPTY
        else:
            self.state = state

    def __str__(self):
        return self._visualisations[self._state]

    @property
    def state(self):
        return self._state

    @property
    def contains_undamaged_ship(self):
        return self._state == self.STATE_OCCUPIED_BY_SHIP

    @property
    def is_empty(self):
        return self._state == self.STATE_EMPTY

    @property
    def is_targetable(self):
        return self._state == self.STATE_OCCUPIED_BY_SHIP or self.is_empty

    @state.setter
    def state(self, value):
        self._state = value


class Ship:
    direction_horizontal = 0
    direction_vertical = 1

    SIZE_BIG = 3
    SIZE_MEDIUM = 2
    SIZE_SMALL = 1

    @staticmethod
    def get_random_direction():
        return randint(0, 1)

    def __init__(self, nose_coordinate_x, nose_coordinate_y, length, direction):
        self._direction = direction
        self._length = length
        self._health = length

        self._dots = [Dot(nose_coordinate_x + i, nose_coordinate_y)
                      if direction == self.direction_horizontal
                      else Dot(nose_coordinate_x, nose_coordinate_y + i)
                      for i in range(length)]

        self._nose_dot = self._dots[0]

    @property
    def dots(self):
        return self._dots.copy()

    @property
    def health(self):
        return self._health

    @property
    def nose(self):
        return self._nose_dot

    @property
    def is_direction_horizontal(self):
        return self._direction == self.direction_horizontal

    @property
    def length(self):
        return self._length

    def take_damage(self):
        self._health -= 1


class Board:
    @staticmethod
    def out(dot):
        return False if 0 <= dot.x <= 5 and 0 <= dot.y <= 5 else True

    def __init__(self):
        self._grid = [[Cell(j, i) for j in range(6)] for i in range(6)]
        self._hid = False
        self._ship_list = []
        self._number_of_ships_alive = 0

    # когда обращаемся к координатам через двумерный список x y идут в обратном порядке
    # потому что я рассматриваю x y как абсциссу и ординату
    # но выводить на экран проще построчно

    def _validate_ship(self, ship):
        for dot in ship.dots:
            if self.out(dot) or not self.get_cell_by_dot(dot).is_empty:
                raise InvalidShip("Ship cannot be placed at its position")
        return True

    def _validate_target(self, target_dot):
        if self.out(target_dot):
            raise BoardOutException("target dot is out of borders")
        if not self.get_cell_by_dot(target_dot).is_targetable:
            raise InvalidTarget("this dot is already been shot at")
        return True

    def get_cell_by_dot(self, dot):
        return self._grid[dot.y][dot.x]

    # чистка клеток помеченных во время создания доски
    def clean(self):
        for x in range(6):
            for y in range(6):
                if self._grid[y][x].state == Cell.STATE_MISSED:
                    self._grid[y][x].state = Cell.STATE_EMPTY

    def hide(self):
        self._hid = True
        return self

    def add_ship(self, ship):
        if self._validate_ship(ship):
            self._ship_list.append(ship)
            self._number_of_ships_alive += 1
            for dot in ship.dots:
                self.get_cell_by_dot(dot).state = Cell.STATE_OCCUPIED_BY_SHIP
            self.contour(ship)
        return True

    def contour(self, ship):
        x_increment = 2
        y_increment = ship.length + 1

        if ship.is_direction_horizontal:
            x_increment, y_increment = y_increment, x_increment

        for x in range(ship.nose.x - 1, ship.nose.x + x_increment):
            for y in range(ship.nose.y - 1, ship.nose.y + y_increment):
                if not self.out(Dot(x, y)) and self._grid[y][x].is_empty:
                    self._grid[y][x].state = Cell.STATE_MISSED
        return True

    def show(self):
        print("  | 1 | 2 | 3 | 4 | 5 | 6 |")
        for i, row in enumerate(self._grid):
            output = f"{i + 1} |"
            for cell in row:
                if self._hid and cell.contains_undamaged_ship:
                    output += f" O |"
                else:
                    output += f" {cell} |"
            print(output)
        print("")

    def shot(self, target_dot):
        if self._validate_target(target_dot):
            for ship in self._ship_list:
                if target_dot in ship.dots:
                    ship.take_damage()
                    self.get_cell_by_dot(target_dot).state = Cell.STATE_OCCUPIED_BY_DAMAGED_SHIP
                    if ship.health == 0:
                        self._number_of_ships_alive -= 1
                        self.contour(ship)
                    return True
            else:
                self.get_cell_by_dot(target_dot).state = Cell.STATE_MISSED
                return False

    @property
    def is_all_ships_destroyed(self):
        return self._number_of_ships_alive == 0

    def get_empty_cells(self):
        return [self._grid[y][x] for y in range(6) for x in range(6) if self._grid[y][x].is_empty]

    def get_targetable_cells(self):
        return [self._grid[y][x] for y in range(6) for x in range(6) if self._grid[y][x].is_targetable]


class Player:
    def __init__(self, board, enemy_board):
        self._board = board
        self._enemy_board = enemy_board

    def ask(self):
        pass

    def move(self):
        while True:
            target = self.ask()
            try:
                return self._enemy_board.shot(target)
            except BoardOutException:
                print("Вееденные вами координаты находятся вне игрового поля")
            except InvalidTarget:
                print("Вы уже стреляли в эту клетку")


class User(Player):
    def ask(self):
        while True:
            input_data = input("введите координаты:\n").split()

            if len(input_data) != 2:
                print("неверное количество координат")
                continue

            x, y = input_data
            if not x.isdigit() or not y.isdigit():
                print("координаты должны быть числами")
                continue

            return Dot(int(x) - 1, int(y) - 1)


class Ai(Player):
    def ask(self):
        targetable_cells = self._enemy_board.get_targetable_cells()
        x, y = targetable_cells[randint(0, len(targetable_cells) - 1)].coordinates
        print(f"{x + 1} {y + 1}\n")
        return Dot(x, y)


class Game:
    _required_ships = [Ship.SIZE_BIG] + [Ship.SIZE_MEDIUM] * 2 + [Ship.SIZE_SMALL] * 4

    @classmethod
    def _place_random_ship(cls, board, ship_length):
        # используется список пустых клеток что бы гарантировать что хотябы нос корабля попадет на пустую клетку
        empty_cells = board.get_empty_cells()
        if not empty_cells:
            return False
        for i in range(1000):
            if cls._attempt_single_random_ship_placement(board, empty_cells, ship_length):
                break
        else:
            return False
        return True

    @staticmethod
    def _attempt_single_random_ship_placement(board, empty_cells, ship_length):
        x, y = empty_cells[randint(0, len(empty_cells) - 1)].coordinates
        ship = Ship(x, y, ship_length, Ship.get_random_direction())
        try:
            board.add_ship(ship)
        except InvalidShip:
            return False
        else:
            return True

    @staticmethod
    def greet():
        print("Приветствуем Вас в игре морской бой")
        print("Координаты вводятся в формате x y через пробел")
        print("x координата по горизонтальной оси а y по вертикальной\n")

    def __init__(self):
        self._user_board = self.random_board()
        self._ai_board = self.random_board().hide()

        self._user = User(board=self._user_board, enemy_board=self._ai_board)
        self._ai = Ai(board=self._ai_board, enemy_board=self._user_board)

    def random_board(self):
        while True:
            board = Board()
            for ship_length in self._required_ships:
                if not self._place_random_ship(board, ship_length):
                    break
            else:
                board.clean()
                return board

    def show_boards(self):
        print("Ваша доска:")
        self._user_board.show()
        print("Доска противника:")
        self._ai_board.show()

    def loop(self):
        while True:
            turn_repeat_flag = True
            while turn_repeat_flag:
                self.show_boards()
                turn_repeat_flag = self._user.move()

                if self._ai_board.is_all_ships_destroyed:
                    self.show_boards()
                    print("Пользователь выиграл")
                    return True

            print("\nХод противника:")
            turn_repeat_flag = True
            while turn_repeat_flag:
                turn_repeat_flag = self._ai.move()
                if self._user_board.is_all_ships_destroyed:
                    self.show_boards()
                    print("Компьютер выиграл")
                    return True

    def start(self):
        self.greet()
        self.loop()


game = Game()
game.start()
