from sqlalchemy.orm import Session

from app.core.security import encrypt_secret, decrypt_secret
from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate


class AgentService:
    @staticmethod
    def create_agent(db: Session, agent_data: AgentCreate) -> Agent:
        data = agent_data.model_dump()
        data["api_key"] = encrypt_secret(data.get("api_key"))
        agent = Agent(**data)
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def get_agent(db: Session, agent_id: int) -> Agent:
        return db.query(Agent).filter(Agent.id == agent_id).first()

    @staticmethod
    def get_agent_with_decrypted_key(db: Session, agent_id: int) -> Agent:
        """
        Use only in the execution path (never in an API response). Returns
        the agent with `api_key` swapped for its decrypted plaintext value
        so it can be handed to a provider SDK.
        """
        agent = AgentService.get_agent(db, agent_id)
        if agent is not None:
            agent.api_key = decrypt_secret(agent.api_key)
        return agent

    @staticmethod
    def get_all_agents(db: Session, skip: int = 0, limit: int = 100):
        return db.query(Agent).offset(skip).limit(limit).all()

    @staticmethod
    def update_agent(db: Session, agent_id: int, agent_data: AgentUpdate) -> Agent:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if agent:
            update_data = agent_data.model_dump(exclude_unset=True)
            if "api_key" in update_data:
                update_data["api_key"] = encrypt_secret(update_data["api_key"])
            for key, value in update_data.items():
                setattr(agent, key, value)
            db.commit()
            db.refresh(agent)
        return agent

    @staticmethod
    def delete_agent(db: Session, agent_id: int) -> bool:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if agent:
            db.delete(agent)
            db.commit()
            return True
        return False

    @staticmethod
    def get_agent_by_name(db: Session, name: str) -> Agent:
        return db.query(Agent).filter(Agent.name == name).first()
