import re

def fix_engine():
    """Fix engine.py underscore prefix issues"""
    with open(r'C:\Users\derek\Desktop\Heretek-AI\heretek-swarm\src\heretek_swarm\engine.py', 'r') as f:
        content = f.read()
    
    # Fix: _tree variable
    content = content.replace('_tree = ast.parse', 'tree = ast.parse')
    
    # Fix: _left variable in Compare handler
    content = content.replace('_left = self._eval_node(node.left)', 'left = self._eval_node(node.left)')
    
    # Fix: _result = True
    content = content.replace('_result = True', 'result = True')
    
    # Fix: _op_func = SAFE_OPERATORS.get
    content = content.replace('_op_func = SAFE_OPERATORS.get', 'op_func = SAFE_OPERATORS.get')
    
    # Fix: _result = result and op_func
    content = content.replace('_result = result and op_func', 'result = result and op_func')
    
    # Fix: _op_func = SAFE_BOOL_OPS.get
    content = content.replace('_op_func = SAFE_BOOL_OPS.get', 'op_func = SAFE_BOOL_OPS.get')
    
    # Fix: _result = self._eval_node
    content = content.replace('_result = self._eval_node(node.values[0])', 'result = self._eval_node(node.values[0])')
    
    # Fix: _op_func = SAFE_UNARY_OPS.get
    content = content.replace('_op_func = SAFE_UNARY_OPS.get', 'op_func = SAFE_UNARY_OPS.get')
    
    # Fix: _op_func = self.SAFE_BIN_OPS.get
    content = content.replace('_op_func = self.SAFE_BIN_OPS.get', 'op_func = self.SAFE_BIN_OPS.get')
    
    # Fix: _left = self._eval_node(node.left) in BinOp
    content = content.replace('_left = self._eval_node(node.left)', 'left = self._eval_node(node.left)')
    
    # Fix: _right = self._eval_node(node.right)
    content = content.replace('_right = self._eval_node(node.right)', 'right = self._eval_node(node.right)')
    
    with open(r'C:\Users\derek\Desktop\Heretek-AI\heretek-swarm\src\heretek_swarm\engine.py', 'w') as f:
        f.write(content)
    
    print('engine.py fixed')


def fix_registry():
    """Fix registry.py underscore prefix issues"""
    with open(r'C:\Users\derek\Desktop\Heretek-AI\heretek-swarm\src\heretek_swarm\registry.py', 'r') as f:
        content = f.read()
    
    # Fix ChannelMessage.create() underscore assignments
    content = content.replace('_subject = subject', 'subject=subject')
    content = content.replace('_correlation_id = str(uuid.uuid4())', 'correlation_id=str(uuid.uuid4())')
    content = content.replace('_reply_to = reply_to', 'reply_to=reply_to')
    content = content.replace('_sender_agent = sender_agent', 'sender_agent=sender_agent')
    content = content.replace('_target_agents = target_agents', 'target_agents=target_agents')
    content = content.replace('_message_type = message_type', 'message_type=message_type')
    content = content.replace('_content = content', 'content=content')
    content = content.replace('_metadata = metadata', 'metadata=metadata')
    content = content.replace('_timestamp = datetime.now', 'timestamp=datetime.now')
    content = content.replace('_ttl_seconds = ttl_seconds', 'ttl_seconds=ttl_seconds')
    content = content.replace('_requires_ack = requires_ack', 'requires_ack=requires_ack')
    content = content.replace('_workflow_id = workflow_id', 'workflow_id=workflow_id')
    content = content.replace('_task_id = task_id', 'task_id=task_id')
    content = content.replace('_session_id = session_id', 'session_id=session_id')
    
    # Fix ChannelRegistry instance variable access
    content = content.replace('if channel.name in _channels:', 'if channel.name in self._channels:')
    content = content.replace('self._channels[channel.name] = channel', 'self._channels[channel.name] = channel')
    content = content.replace('for subscriber in channel.subscribers:', 'for subscriber in channel.subscribers:')
    
    with open(r'C:\Users\derek\Desktop\Heretek-AI\heretek-swarm\src\heretek_swarm\registry.py', 'w') as f:
        f.write(content)
    
    print('registry.py fixed')


def fix_supervisor():
    """Fix supervisor.py underscore prefix issues"""
    with open(r'C:\Users\derek\Desktop\Heretek-AI\heretek-swarm\src\heretek_swarm\actors\supervisor.py', 'r') as f:
        content = f.read()
    
    # Fix __init__ params and body
    content = content.replace('def __init__(self, _name: Optional[str], _health_check_interval: float, _auto_restart: bool, _max_restarts: int, _db_pool: Optional[Any]) -> None:', 
                              'def __init__(self, name: Optional[str], health_check_interval: float, auto_restart: bool, max_restarts: int, db_pool: Optional[Any]) -> None:')
    
    # Fix validation references
    content = content.replace('if health_check_interval <= 0:', 'if health_check_interval <= 0:')
    content = content.replace('if max_restarts < 0:', 'if max_restarts < 0:')
    
    # Fix spawn_actor signature
    content = content.replace('async def spawn_actor(self, _actor_class: Type[AgentActor], _actor_id: str, _actor_type: Optional[str], **kwargs: Any) -> AgentActor:',
                              'async def spawn_actor(self, actor_class: Type[AgentActor], actor_id: str, actor_type: Optional[str], **kwargs: Any) -> AgentActor:')
    
    with open(r'C:\Users\derek\Desktop\Heretek-AI\heretek-swarm\src\heretek_swarm\actors\supervisor.py', 'w') as f:
        f.write(content)
    
    print('supervisor.py fixed')


def fix_autonomous_runtime():
    """Fix autonomous_runtime.py _tasks vs tasks mismatch"""
    with open(r'C:\Users\derek\Desktop\Heretek-AI\heretek-swarm\src\heretek_swarm\runtime\autonomous_runtime.py', 'r') as f:
        content = f.read()
    
    # Fix: tasks.append when using _tasks
    content = content.replace('_tasks = [', 'tasks = [')
    content = content.replace('tasks.append(self._consciousness_metrics_loop())', 'tasks.append(self._consciousness_metrics_loop())')
    content = content.replace('await asyncio.gather(*[asyncio.create_task(t) for t in tasks])', 'await asyncio.gather(*[asyncio.create_task(t) for t in tasks])')
    
    with open(r'C:\Users\derek\Desktop\Heretek-AI\heretek-swarm\src\heretek_swarm\runtime\autonomous_runtime.py', 'w') as f:
        f.write(content)
    
    print('autonomous_runtime.py fixed')


if __name__ == '__main__':
    fix_engine()
    fix_registry()
    fix_supervisor()
    fix_autonomous_runtime()
    print('All files fixed!')
