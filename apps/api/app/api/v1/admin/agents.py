from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import uuid
from datetime import datetime

router = APIRouter()

# Pydantic models for request/response
class AgentBase(BaseModel):
    name: str
    description: str
    system_prompt: str

class AgentCreate(AgentBase):
    brand_id: str
    configuration: dict

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    configuration: Optional[dict] = None
    status: Optional[str] = None

class Agent(AgentBase):
    id: str
    brand_id: str
    slug: str
    configuration: dict
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# In-memory storage for demo (replace with database)
agents_db = {}

def generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from the agent name."""
    return name.lower().replace(' ', '-').replace('&', 'and')

@router.get("/", response_model=List[Agent])
async def list_agents(brand_id: Optional[str] = Query(None)):
    """Get all agents, optionally filtered by brand."""
    agents = list(agents_db.values())
    if brand_id:
        agents = [agent for agent in agents if agent.brand_id == brand_id]
    return agents

@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str):
    """Get a specific agent by ID."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agents_db[agent_id]

@router.post("/", response_model=Agent)
async def create_agent(agent: AgentCreate):
    """Create a new agent."""
    agent_id = str(uuid.uuid4())
    slug = generate_slug(agent.name)
    
    # Check if slug already exists for this brand
    for existing_agent in agents_db.values():
        if existing_agent.brand_id == agent.brand_id and existing_agent.slug == slug:
            slug = f"{slug}-{agent_id[:8]}"
            break
    
    now = datetime.utcnow()
    new_agent = Agent(
        id=agent_id,
        brand_id=agent.brand_id,
        slug=slug,
        name=agent.name,
        description=agent.description,
        system_prompt=agent.system_prompt,
        configuration=agent.configuration,
        status="draft",
        created_at=now,
        updated_at=now
    )
    
    agents_db[agent_id] = new_agent
    return new_agent

@router.put("/{agent_id}", response_model=Agent)
async def update_agent(agent_id: str, agent_update: AgentUpdate):
    """Update an existing agent."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    existing_agent = agents_db[agent_id]
    update_data = agent_update.dict(exclude_unset=True)
    
    # Update slug if name changed
    if "name" in update_data:
        update_data["slug"] = generate_slug(update_data["name"])
    
    update_data["updated_at"] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(existing_agent, field, value)
    
    return existing_agent

@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    del agents_db[agent_id]
    return {"message": "Agent deleted successfully"}
