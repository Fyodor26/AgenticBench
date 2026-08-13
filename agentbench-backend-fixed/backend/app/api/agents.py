import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security import decrypt_secret
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from app.services.agent_service import AgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/", response_model=AgentResponse)
def create_agent(
    agent_data: AgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new agent. Requires authentication - agent configs can hold
    third-party provider credentials, so this must not be open to anonymous
    callers."""
    existing = AgentService.get_agent_by_name(db, agent_data.name)
    if existing:
        raise HTTPException(status_code=400, detail="Agent with this name already exists")

    agent = AgentService.create_agent(db, agent_data)
    return agent


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific agent"""
    agent = AgentService.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.get("/", response_model=list[AgentResponse])
def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all agents"""
    agents = AgentService.get_all_agents(db, skip, limit)
    return agents


@router.put("/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: int,
    agent_data: AgentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an agent"""
    agent = AgentService.update_agent(db, agent_id, agent_data)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.delete("/{agent_id}")
def delete_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an agent"""
    success = AgentService.delete_agent(db, agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": "Agent deleted successfully"}


@router.post("/{agent_id}/test")
async def test_agent_connection(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fire a trivial prompt at the agent's provider to verify credentials /
    connectivity work, without creating a full Evaluation record. Used by
    the "Test" button on the Agents page.
    """
    from app.agents.executor import AgentExecutor

    agent = AgentService.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    api_key = decrypt_secret(agent.api_key) if agent.api_key else None

    try:
        result = await AgentExecutor.execute(
            prompt="Reply with the single word: OK",
            provider=agent.provider,
            model=agent.model,
            api_key=api_key,
            api_endpoint=agent.api_endpoint if agent.provider == "generic" else None,
            timeout=15,
        )
    except Exception as e:
        logger.error("Agent connection test failed for agent %s: %s", agent_id, e)
        return {"success": False, "message": str(e)}

    return {
        "success": result.success,
        "message": "Connection OK" if result.success else (result.error or "Connection failed"),
        "latency_seconds": result.execution_time,
    }
