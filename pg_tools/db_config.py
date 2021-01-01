# -*- coding: utf-8 -*-

from dataclasses import dataclass, field


@dataclass
class DBConfig:
    host: str
    port: str
    database: str
    user: str
    password: str = field(repr=False) # exclude this field from autogenerated __repr__()

    def __str__(self):
        return f'{self.user}@{self.host}:{self.port}/{self.database}'
