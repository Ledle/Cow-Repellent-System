from functools import cached_property


class Config:
    @cached_property
    def expensive_value(self):
        print("Вычисляем...")
        return sum(range(10_000_000))

    def get_value(self):
        return self.expensive_value


cfg = Config()

print("Объект создан")
print(cfg.get_value())  # вычисление происходит здесь
print(cfg.expensive_value)  # берётся из кэша
