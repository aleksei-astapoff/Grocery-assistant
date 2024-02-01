# users models

MAX_LENGTH_EMAIL_FIELD = 254
MAX_LENGTH_CHAR_FIELD = 150
USERNAME = 'email'

# recipes models

MAX_LENGTH_CHAR_FIELD = 200
MAX_VALUE_TIME = 1440
MIN_VALUE_TIME = 1
MAX_VALUE_AMOUNT = 20
MIN_VALUE_AMOUNT = 1

COLOR_PALETTE = [
    ("#FF0000", "Красный"),
    ("#00FF00", "Зеленый"),
    ("#0000FF", "Синий"),
    ("#FFFF00", "Желтый"),
    ("#FFA500", "Оранжевый"),
    ("#800080", "Фиолетовый"),
    ("#008000", "Темно-зеленый"),
    ("#800000", "Темно-красный"),
]

# recipes admin

MIN_VALUE_IGRREDIENTS_ADMIN = 1
RECIPE_LIMIT_SHOW = 5
NO_VALUE = '-Не задано-'

# recipes management/commands/load_data

data = (
    {'name': 'Завтрак', 'color': '#FF0000', 'slug': 'breakfast'},
    {'name': 'Обед', 'color': '#00FF00', 'slug': 'lunch'},
    {'name': 'Ужин', 'color': '#0000FF', 'slug': 'dinner'},
)
