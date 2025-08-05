from database import SessionLocal
from models import Team

with SessionLocal() as session:
    teams = session.query(Team).order_by(Team.name).limit(10).all()
    for team in teams:
        print(f"{team.name}: {team.wins}-{team.losses}-{team.ties} (Conf: {team.conf_wins}-{team.conf_losses}), Preseason Rank: {team.preseason_rank}, Tier: {team.tier}")
