import pytest
from app.agents.communication.protocol import AgentMessage
from app.agents.communication.message_bus import message_bus
from app.agents.communication.serializer import MessageSerializer
from app.agents.communication.routing import MessageRouter

@pytest.mark.asyncio
async def test_message_bus_publish_subscribe():
    message_bus.clear()
    
    received_msgs = []
    async def handler(msg: AgentMessage):
        received_msgs.append(msg)

    # Subscribe ResearchAgent to receive messages
    message_bus.subscribe("ResearchAgent", handler)

    msg = AgentMessage(
        sender="PlannerAgent",
        receiver="ResearchAgent",
        conversation_id="conv-123",
        payload={"task": "Find quarterly summary"}
    )
    
    await message_bus.publish(msg)
    
    assert len(received_msgs) == 1
    assert received_msgs[0].sender == "PlannerAgent"
    assert received_msgs[0].payload["task"] == "Find quarterly summary"
    assert len(message_bus.get_history("conv-123")) == 1

def test_message_serializer():
    msg = AgentMessage(
        sender="CodingAgent",
        receiver="QAAgent",
        payload={"code_length": 150}
    )
    serialized = MessageSerializer.serialize(msg)
    deserialized = MessageSerializer.deserialize(serialized)
    
    assert deserialized.sender == "CodingAgent"
    assert deserialized.receiver == "QAAgent"
    assert deserialized.payload["code_length"] == 150

@pytest.mark.asyncio
async def test_message_router():
    message_bus.clear()
    
    routes_ran = []
    async def router_handler(msg: AgentMessage):
        routes_ran.append(msg)

    message_bus.subscribe("ComplianceAgent", router_handler)

    msg = AgentMessage(
        sender="SupervisorAgent",
        receiver="ComplianceAgent",
        payload={"rule": "ISO-27001"}
    )
    
    await MessageRouter.route_message(msg)
    
    assert len(routes_ran) == 1
    assert routes_ran[0].sender == "SupervisorAgent"
