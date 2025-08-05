from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    wins = Column(Integer)
    losses = Column(Integer)
    ties = Column(Integer)
    conf_wins = Column(Integer)
    conf_losses = Column(Integer)
    preseason_rank = Column(Integer)
    tier = Column(Integer)


class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)


class PlayerPick(Base):
    __tablename__ = "player_picks"
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))

    UniqueConstraint("player_id", "team_id")
