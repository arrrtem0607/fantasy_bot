from datetime import datetime
from typing import List
from sqlalchemy import BigInteger, String, Integer, ForeignKey, Boolean, DateTime, func, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .core import Base

# Сущность User (Пользователь)
class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    team_name: Mapped[str] = mapped_column(String, nullable=False)
    balance: Mapped[int] = mapped_column(Integer, default=46)  # Макс 46 очков
    captain_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=True)  # Капитан команды
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Связь с FantasyTeam и Transfer с каскадным удалением
    fantasy_teams: Mapped[List["FantasyTeam"]] = relationship("FantasyTeam", back_populates="user", cascade="all, delete-orphan")
    transfers: Mapped[List["Transfer"]] = relationship("Transfer", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_user_username', 'username'),  # Индекс для ускорения поиска пользователей по имени
    )

# Сущность Player (Игрок)
class Player(Base):
    __tablename__ = 'players'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    team: Mapped[str] = mapped_column(String, nullable=False)  # Реальная команда
    price: Mapped[int] = mapped_column(Integer, nullable=False)  # Рейтинг игрока
    position: Mapped[str] = mapped_column(String, nullable=False)  # Позиция игрока (вратарь, защитник и т.д.)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # Активен в турнире или выбыл

    # Связь с FantasyTeam и PlayerStats
    fantasy_teams: Mapped[List["FantasyTeam"]] = relationship("FantasyTeam", back_populates="player")
    stats: Mapped[List["PlayerStats"]] = relationship("PlayerStats", back_populates="player")

    __table_args__ = (
        Index('ix_player_team', 'team'),  # Индекс для ускорения поиска игроков по команде
        Index('ix_player_position', 'position'),  # Индекс для ускорения поиска по позиции
    )

# Сущность FantasyTeam (Команда пользователя)
class FantasyTeam(Base):
    __tablename__ = 'fantasy_teams'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey('players.id'), index=True)
    is_captain: Mapped[bool] = mapped_column(Boolean, default=False)  # Является ли капитаном

    user: Mapped["User"] = relationship("User", back_populates="fantasy_teams")
    player: Mapped["Player"] = relationship("Player", back_populates="fantasy_teams")

# Сущность Transfer (Трансфер)
class Transfer(Base):
    __tablename__ = 'transfers'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    player_out_id: Mapped[int] = mapped_column(ForeignKey('players.id'))
    player_in_id: Mapped[int] = mapped_column(ForeignKey('players.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="transfers")

# Сущность Match (Матч)
class Match(Base):
    __tablename__ = 'matches'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    team_1: Mapped[str] = mapped_column(String, nullable=False)
    team_2: Mapped[str] = mapped_column(String, nullable=False)
    score_1: Mapped[int] = mapped_column(Integer, nullable=False)
    score_2: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index('ix_match_date', 'date'),  # Индекс для ускорения поиска матчей по дате
    )

# Сущность PlayerStats (Статистика игрока)
class PlayerStats(Base):
    __tablename__ = 'player_stats'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey('players.id'), index=True)
    match_id: Mapped[int] = mapped_column(ForeignKey('matches.id'), index=True)
    goals: Mapped[int] = mapped_column(Integer, default=0)
    assists: Mapped[int] = mapped_column(Integer, default=0)
    clean_sheets: Mapped[int] = mapped_column(Integer, default=0)  # Сухие матчи
    penalty_missed: Mapped[int] = mapped_column(Integer, default=0)
    yellow_cards: Mapped[int] = mapped_column(Integer, default=0)
    red_cards: Mapped[int] = mapped_column(Integer, default=0)
    own_goals: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    penalty_saved: Mapped[int] = mapped_column(Integer, default=0)

    player: Mapped["Player"] = relationship("Player", back_populates="stats")
    match: Mapped["Match"] = relationship("Match")

# Сущность FantasyPoints (Очки игрока)
class FantasyPoints(Base):
    __tablename__ = 'fantasy_points'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey('players.id'), index=True)
    match_id: Mapped[int] = mapped_column(ForeignKey('matches.id'), index=True)
    points: Mapped[int] = mapped_column(Integer, nullable=False)

    player: Mapped["Player"] = relationship("Player")
    match: Mapped["Match"] = relationship("Match")

    __table_args__ = (
        Index('ix_fantasy_points_player_match', 'player_id', 'match_id'),  # Индекс для ускорения поиска очков по игроку и матчу
    )