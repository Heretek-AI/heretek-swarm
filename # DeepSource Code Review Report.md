# DeepSource Code Review Report

**Repository:** Heretek-AI/heretek-swarm
**Branch:** `main`
**Commit:** cc9cd00...7b8171c
**Run:** [https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/466a5172-b5c7-48b1-85a3-4e8230662342/](https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/466a5172-b5c7-48b1-85a3-4e8230662342/)

---

## Summary
- **JavaScript:** No issues detected- **Shell:** No issues detected- **Docker:** No issues detected- **Python:** 30129 issues- **Secrets:** No issues detected- **SQL:** No issues detected

---

## Code Review Findings
### JavaScript
**Status:** Success
**Findings:** No new issues detected
### Shell
**Status:** Success
**Findings:** No new issues detected
### Docker
**Status:** Success
**Findings:** No new issues detected
### Python
**Status:** Failure
**Findings:** 21317 new issues

1. **Unused argument 'filepath'** (`PYL-W0613`)
   **File:** `fix_syntax_errors.py`
   **Line:** 265
   ```python
   return content
   
   
   def validate_python_syntax(content: str, filepath: str) -> Tuple[bool, Optional[str]]:
       """Validate that the content is valid Python syntax."""
       try:
           ast.parse(content)
   ```
   **Category:** Anti-pattern
   **Severity:** major

2. **Unused variable 'match'** (`PYL-W0612`)
   **File:** `fix_syntax_errors.py`
   **Line:** 253
   ```python
   for pattern, replacement in TYPING_FIXES:
           matches = list(re.finditer(pattern, content))
           if matches:
               for match in matches:
                   fixes_applied += 1
                   logger.stats['typing_fixes'] += 1
   ```
   **Category:** Anti-pattern
   **Severity:** major

3. **Unused variable 'original'** (`PYL-W0612`)
   **File:** `fix_syntax_errors.py`
   **Line:** 213
   ```python
   def fix_comment_patterns(content: str, logger: FixLogger, filepath: str) -> str:
       """Fix underscore-prefixed comments that break function signatures."""
       original = content
       
       pattern, replacement = COMMENT_PATTERN
       matches = list(re.finditer(pattern, content))
   ```
   **Category:** Anti-pattern
   **Severity:** major

4. **Unused variable 'original'** (`PYL-W0612`)
   **File:** `fix_syntax_errors.py`
   **Line:** 247
   ```python
   def fix_typing_names(content: str, logger: FixLogger, filepath: str) -> str:
       """Fix underscore-prefixed typing module names."""
       original = content
       fixes_applied = 0
       
       for pattern, replacement in TYPING_FIXES:
   ```
   **Category:** Anti-pattern
   **Severity:** major

5. **Unused variable 'match'** (`PYL-W0612`)
   **File:** `fix_syntax_errors.py`
   **Line:** 233
   ```python
   for pattern, replacement in ARGS_KWARGS_PATTERNS:
           matches = list(re.finditer(pattern, content))
           if matches:
               for match in matches:
                   fixes_applied += 1
                   logger.stats['args_kwargs_fixes'] += 1
   ```
   **Category:** Anti-pattern
   **Severity:** major

6. **Unused Path imported from pathlib** (`PY-W2000`)
   **File:** `fix_syntax_errors.py`
   **Line:** 26
   ```python
   import shutil
   import sys
   from datetime import datetime
   from pathlib import Path
   from typing import Dict, List, Optional, Set, Tuple, Callable, Union
   ```
   **Category:** Anti-pattern
   **Severity:** major

7. **Unused variable 'original'** (`PYL-W0612`)
   **File:** `fix_syntax_errors.py`
   **Line:** 227
   ```python
   def fix_args_kwargs_patterns(content: str, logger: FixLogger, filepath: str) -> str:
       """Fix invalid _*args and _**kwargs patterns."""
       original = content
       fixes_applied = 0
       
       for pattern, replacement in ARGS_KWARGS_PATTERNS:
   ```
   **Category:** Anti-pattern
   **Severity:** major

8. **`fix_file_proper` has a cyclomatic complexity of 26 with "very-high" risk** (`PY-R1000`)
   **File:** `fix_underscore_params.py`
   **Line:** 261
   ```python
   return result
   
   
   def fix_file_proper(filepath: Path, fixes: List[ParameterFix], create_backup: bool = True) -> FileAnalysisResult:
       """
       Fix underscore prefix issues using proper AST-based text manipulation.
   ```
   **Category:** Anti-pattern
   **Severity:** minor

9. **`analyze_function_for_fixes` has a cyclomatic complexity of 27 with "very-high" risk** (`PY-R1000`)
   **File:** `fix_underscore_params.py`
   **Line:** 71
   ```python
   return False
   
   
   def analyze_function_for_fixes(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> List[ParameterFix]:
       """Analyze a function and return list of parameter fixes needed."""
       fixes: List[ParameterFix] = []
   ```
   **Category:** Anti-pattern
   **Severity:** minor

10. **Unused variable 'is_method'** (`PYL-W0612`)
    **File:** `fix_underscore_params.py`
    **Line:** 76
    ```python
    fixes: List[ParameterFix] = []
        
        func_name = func_node.name
        is_method = len(func_node.args.args) > 0 and func_node.args.args[0].arg in ('self', 'cls')
        is_constructor = func_name == '__init__'
        is_abstract = is_abstract_method(func_node)
    ```
    **Category:** Anti-pattern
    **Severity:** major

11. **Consider merging collapsible if statements** (`PTC-W0048`)
    **File:** `fix_underscore_params.py`
    **Line:** 398
    ```python
    if recursive:
            for path in directory.rglob('*.py'):
                if not any(skip_dir in path.parts for skip_dir in skip_dirs):
                    if 'test' not in path.parts:  # Skip test files
                        files.append(path)
        else:
    ```
    **Category:** Anti-pattern
    **Severity:** major

12. **Cell variable fix defined in loop** (`PYL-W0640`)
    **File:** `fix_underscore_params.py`
    **Line:** 355
    ```python
    ]
                    
                    for pattern in patterns:
                        new_line = re.sub(pattern, lambda m: m.group(1) + fix.new_name + m.group(2), line)
                        if new_line != line:
                            line = new_line
    ```
    **Category:** Bug risk
    **Severity:** major

13. **Unused variable 'body_line'** (`PYL-W0612`)
    **File:** `fix_underscore_params.py`
    **Line:** 371
    ```python
    if body_line_num in modified_lines and body_line_num == line_num:
                            continue
                        
                        body_line = lines[body_line_num - 1]
                        # Replace bare references to the new name (which was incorrectly used)
                        # The pattern (?<!_) ensures we don't match _param
                        # We're looking for uses of 'param' that should stay as 'param'
    ```
    **Category:** Anti-pattern
    **Severity:** major

14. **Unused variable 'tree'** (`PYL-W0612`)
    **File:** `fix_underscore_params.py`
    **Line:** 227
    ```python
    # Build a mapping of function line ranges
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # File already has syntax errors - we need to fix parameter definitions first
            # Then the references will work
    ```
    **Category:** Anti-pattern
    **Severity:** major

15. **Unused import os** (`PY-W2000`)
    **File:** `fix_underscore_params.py`
    **Line:** 16
    ```python
    """
    
    import ast
    import os
    import re
    import shutil
    import sys
    ```
    **Category:** Anti-pattern
    **Severity:** major

16. **Cell variable fix defined in loop** (`PYL-W0640`)
    **File:** `fix_underscore_params.py`
    **Line:** 305
    ```python
    for fix in func_fixes:
                        # Replace parameter definition
                        pattern = rf'(\bdef\s+\w+\s*\([^)]*){re.escape(fix.old_name)}'
                        new_line = re.sub(pattern, lambda m: m.group(1) + fix.new_name, line)
                        if new_line != line:
                            lines[line_num - 1] = new_line
                            line = new_line
    ```
    **Category:** Bug risk
    **Severity:** major

17. **Cell variable fix defined in loop** (`PYL-W0640`)
    **File:** `fix_underscore_params.py`
    **Line:** 240
    ```python
    param_pattern = rf'(\bdef\s+\w+\s*\([^)]*){re.escape(fix.old_name)}'
            
            def replace_param_def(match):
                return match.group(1) + fix.new_name
            
            content = re.sub(param_pattern, replace_param_def, content)
    ```
    **Category:** Bug risk
    **Severity:** major

18. **Consider merging collapsible if statements** (`PTC-W0048`)
    **File:** `fix_underscore_params.py`
    **Line:** 104
    ```python
    for stmt in func_node.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                            if isinstance(stmt.value, ast.Name) and stmt.value.id in all_param_names:
                                params_assigned_to_self.add(stmt.value.id)
    ```
    **Category:** Anti-pattern
    **Severity:** major

19. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 444
    ```python
    message
            )
        
        async def _send_error(self, websocket: WebSocket, error_msg: str) -> None:
            """Send error message to client."""
            await websocket.send_json({
                "type": "error",
    ```
    **Category:** Performance
    **Severity:** major

20. **Possible binding to all interfaces.** (`BAN-B104`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 124
    ```python
    import uvicorn
            _config = uvicorn.Config(
                app,
                host="0.0.0.0",
                port=self.port,
                _log_level = "info"
            )
    ```
    **Category:** Security
    **Severity:** major

21. **Undefined variable 'proposal_id'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 412
    ```python
    logger.info(
                "a2a_vote_received",
                _client_id = client_id,
                _proposal_id = proposal_id,
                _vote = vote
            )
    ```
    **Category:** Bug risk
    **Severity:** critical

22. **Undefined variable 'agent_type'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 326
    ```python
    _agent_type = message.get("agent_type")
                _filtered = [
                    a for a in self._agent_registry.values()
                    if a["agent_type"] == agent_type
                ]
                _response = {
                    "type": "discovery",
    ```
    **Category:** Bug risk
    **Severity:** critical

23. **Undefined variable 'capabilities'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 223
    ```python
    _client_id = await self.event_mesh.register(
                _websocket = websocket,
                _agent_type = agent_type,
                _capabilities = capabilities,
                _metadata = metadata
            )
    ```
    **Category:** Bug risk
    **Severity:** critical

24. **Undefined variable 'message_data'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 499
    ```python
    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                await self.redis_client.publish(channel, json.dumps(message_data))
                
            except Exception as e:
                logger.error("a2a_redis_log_failed", error=str(e))
    ```
    **Category:** Bug risk
    **Severity:** critical

25. **Undefined variable 'metadata'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 224
    ```python
    _websocket = websocket,
                _agent_type = agent_type,
                _capabilities = capabilities,
                _metadata = metadata
            )
            
            # Track connection
    ```
    **Category:** Bug risk
    **Severity:** critical

26. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 502
    ```python
    await self.redis_client.publish(channel, json.dumps(message_data))
                
            except Exception as e:
                logger.error("a2a_redis_log_failed", error=str(e))
        
        # ============== Helpers ==============
    ```
    **Category:** Bug risk
    **Severity:** critical

27. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 173
    ```python
    try:
                await websocket.accept()
                logger.info("a2a_connection_accepted", remote=websocket.client.host if websocket.client else "unknown")
                
                # Message loop
                async for raw_message in websocket.iter_json():
    ```
    **Category:** Bug risk
    **Severity:** critical

28. **Undefined variable 'filtered'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 332
    ```python
    "type": "discovery",
                    "action": "agent_list",
                    "agents": filtered,
                    "count": len(filtered)
                }
                await self.event_mesh.send_to(client_id, response)
    ```
    **Category:** Bug risk
    **Severity:** critical

29. **Undefined variable 'msg_type'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 299
    ```python
    MessageType.DECISION: self._handle_decision,
            }
            
            _handler = handler_map.get(msg_type)
            if handler:
                await handler(client_id, message)
            else:
    ```
    **Category:** Bug risk
    **Severity:** critical

30. **Undefined variable 'discovery_msg'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 480
    ```python
    "agent_type": agent_info.get("agent_type", "unknown"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await self.event_mesh.broadcast(discovery_msg)
        
        # ============== Redis Logging ==============
    ```
    **Category:** Bug risk
    **Severity:** critical

31. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 389
    ```python
    # Broadcast proposal to all agents
            await self.event_mesh.broadcast(message, exclude=[client_id])
            
            logger.info(
                "a2a_proposal_received",
                _client_id = client_id,
                _proposal_id = proposal_id
    ```
    **Category:** Bug risk
    **Severity:** critical

32. **Undefined variable 'proposal_id'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 392
    ```python
    logger.info(
                "a2a_proposal_received",
                _client_id = client_id,
                _proposal_id = proposal_id
            )
            
            await self._log_message(
    ```
    **Category:** Bug risk
    **Severity:** critical

33. **Undefined variable 'agent_type'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 234
    ```python
    # Register in agent registry
            self._agent_registry[client_id] = {
                "agent_id": client_id,
                "agent_type": agent_type,
                "capabilities": capabilities,
                "metadata": metadata,
                "connected_at": datetime.now(timezone.utc).isoformat()
    ```
    **Category:** Bug risk
    **Severity:** critical

34. **Undefined variable 'atype'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 527
    ```python
    counts: Dict[str, int] = {}
            for agent in self._agent_registry.values():
                _atype = agent.get("agent_type", "unknown")
                counts[atype] = counts.get(atype, 0) + 1
            return counts
    ```
    **Category:** Bug risk
    **Severity:** critical

35. **Undefined variable 'client_id'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 267
    ```python
    )
            
            # Broadcast discovery to other agents
            await self._broadcast_discovery(client_id, agent_type)
            
            return client_id
    ```
    **Category:** Bug risk
    **Severity:** critical

36. **Undefined variable 'msg_type'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 303
    ```python
    if handler:
                await handler(client_id, message)
            else:
                logger.warning("a2a_unknown_message_type", type=msg_type)
        
        # ============== Message Handlers ==============
    ```
    **Category:** Bug risk
    **Severity:** critical

37. **Undefined variable 'client_id'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 229
    ```python
    # Track connection
            self._connections[client_id] = websocket
            self._authenticated.add(client_id)
            
            # Register in agent registry
            self._agent_registry[client_id] = {
    ```
    **Category:** Bug risk
    **Severity:** critical

38. **Undefined variable 'status'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 370
    ```python
    # Update agent registry with status
            if client_id in self._agent_registry:
                self._agent_registry[client_id]["status"] = status
            
            # Broadcast to all
            await self.event_mesh.broadcast(message, exclude=[client_id])
    ```
    **Category:** Bug risk
    **Severity:** critical

39. **Undefined variable 'client_id'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 203
    ```python
    finally:
                # Cleanup
                if client_id:
                    await self._cleanup_connection(client_id)
        
        async def _handle_handshake(self, websocket: WebSocket, message: Dict[str, Any]) -> str:
    ```
    **Category:** Bug risk
    **Severity:** critical

40. **Undefined variable 'client_id'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 188
    ```python
    continue
                    
                    # Check authentication for other messages
                    if self.auth_required and client_id not in self._authenticated:
                        await self._send_error(
                            websocket,
                            "Not authenticated - complete handshake first"
    ```
    **Category:** Bug risk
    **Severity:** critical

41. **Undefined variable 'vote'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 413
    ```python
    "a2a_vote_received",
                _client_id = client_id,
                _proposal_id = proposal_id,
                _vote = vote
            )
            
            await self._log_message(
    ```
    **Category:** Bug risk
    **Severity:** critical

42. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 466
    ```python
    # Unregister from EventMesh
            await self.event_mesh.unregister(client_id)
            
            logger.info(
                "a2a_connection_cleaned",
                _client_id = client_id,
                _agent_type = agent_info.get("agent_type", "unknown")
    ```
    **Category:** Bug risk
    **Severity:** critical

43. **Undefined variable 'agent_type'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 267
    ```python
    )
            
            # Broadcast discovery to other agents
            await self._broadcast_discovery(client_id, agent_type)
            
            return client_id
    ```
    **Category:** Bug risk
    **Severity:** critical

44. **Undefined variable 'agent_info'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 477
    ```python
    "type": "discovery",
                "action": "agent_left",
                "agent_id": client_id,
                "agent_type": agent_info.get("agent_type", "unknown"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await self.event_mesh.broadcast(discovery_msg)
    ```
    **Category:** Bug risk
    **Severity:** critical

45. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 430
    ```python
    await self.event_mesh.broadcast(message)
            
            logger.info(
                "a2a_decision_made",
                _client_id = client_id,
                _proposal_id = proposal_id,
    ```
    **Category:** Bug risk
    **Severity:** critical

46. **Undefined variable 'client_id'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 196
    ```python
    continue
                    
                    # Route message based on type
                    await self._route_message(websocket, client_id, raw_message)
                    
            except Exception as e:
                logger.error("a2a_connection_error", error=str(e), client_id=client_id)
    ```
    **Category:** Bug risk
    **Severity:** critical

47. **Undefined variable 'agent_type'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 222
    ```python
    # Register with EventMesh
            _client_id = await self.event_mesh.register(
                _websocket = websocket,
                _agent_type = agent_type,
                _capabilities = capabilities,
                _metadata = metadata
            )
    ```
    **Category:** Bug risk
    **Severity:** critical

48. **Undefined variable 'capabilities'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 235
    ```python
    self._agent_registry[client_id] = {
                "agent_id": client_id,
                "agent_type": agent_type,
                "capabilities": capabilities,
                "metadata": metadata,
                "connected_at": datetime.now(timezone.utc).isoformat()
            }
    ```
    **Category:** Bug risk
    **Severity:** critical

49. **Undefined variable 'client_id'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 199
    ```python
    await self._route_message(websocket, client_id, raw_message)
                    
            except Exception as e:
                logger.error("a2a_connection_error", error=str(e), client_id=client_id)
                
            finally:
                # Cleanup
    ```
    **Category:** Bug risk
    **Severity:** critical

50. **Undefined variable 'response'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 334
    ```python
    "agents": filtered,
                    "count": len(filtered)
                }
                await self.event_mesh.send_to(client_id, response)
            
            # Log to Redis
            await self._log_message(
    ```
    **Category:** Bug risk
    **Severity:** critical

51. **Undefined variable 'status'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 379
    ```python
    MessageType.STATUS.value,
                client_id,
                self._get_agent_type(client_id),
                status
            )
        
        async def _handle_proposal(self, client_id: str, message: Dict[str, Any]) -> None:
    ```
    **Category:** Bug risk
    **Severity:** critical

52. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 409
    ```python
    await self.event_mesh.broadcast(message, exclude=[client_id])
            
            logger.info(
                "a2a_vote_received",
                _client_id = client_id,
                _proposal_id = proposal_id,
    ```
    **Category:** Bug risk
    **Severity:** critical

53. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 145
    ```python
    self._running = False
            if self._server:
                self._server.should_exit = True
            logger.info("a2a_server_stopped")
        
        async def _health_check(self, _request: Request) -> JSONResponse:
            """Health check endpoint."""
    ```
    **Category:** Bug risk
    **Severity:** critical

54. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 260
    ```python
    {"status": "connected"}
            )
            
            logger.info(
                "a2a_handshake_completed",
                _client_id = client_id,
                _agent_type = agent_type
    ```
    **Category:** Bug risk
    **Severity:** critical

55. **Undefined variable 'client_id'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 262
    ```python
    logger.info(
                "a2a_handshake_completed",
                _client_id = client_id,
                _agent_type = agent_type
            )
    ```
    **Category:** Bug risk
    **Severity:** critical

56. **Undefined variable 'client_id'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 244
    ```python
    _response = {
                "type": "handshake",
                "status": "ok",
                "agent_id": client_id,
                "agent_type": agent_type,
                "protocol_version": PROTOCOL_VERSION,
                "capabilities": ["broadcast", "discovery", "messaging"]
    ```
    **Category:** Bug risk
    **Severity:** critical

57. **Undefined variable 'handler'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 300
    ```python
    }
            
            _handler = handler_map.get(msg_type)
            if handler:
                await handler(client_id, message)
            else:
                logger.warning("a2a_unknown_message_type", type=msg_type)
    ```
    **Category:** Bug risk
    **Severity:** critical

58. **Undefined variable 'agent_type'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 245
    ```python
    "type": "handshake",
                "status": "ok",
                "agent_id": client_id,
                "agent_type": agent_type,
                "protocol_version": PROTOCOL_VERSION,
                "capabilities": ["broadcast", "discovery", "messaging"]
            }
    ```
    **Category:** Bug risk
    **Severity:** critical

59. **Undefined variable 'response'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 250
    ```python
    "capabilities": ["broadcast", "discovery", "messaging"]
            }
            
            await websocket.send_json(response)
            
            # Log to Redis
            await self._log_message(
    ```
    **Category:** Bug risk
    **Severity:** critical

60. **Undefined variable 'filtered'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 331
    ```python
    _response = {
                    "type": "discovery",
                    "action": "agent_list",
                    "agents": filtered,
                    "count": len(filtered)
                }
                await self.event_mesh.send_to(client_id, response)
    ```
    **Category:** Bug risk
    **Severity:** critical

61. **Undefined variable 'config'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 128
    ```python
    port=self.port,
                _log_level = "info"
            )
            self._server = uvicorn.Server(config)
            
            logger.info("a2a_server_starting", port=self.port)
    ```
    **Category:** Bug risk
    **Severity:** critical

62. **Undefined variable 'client_id'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 269
    ```python
    # Broadcast discovery to other agents
            await self._broadcast_discovery(client_id, agent_type)
            
            return client_id
        
        async def _broadcast_discovery(self, client_id: str, agent_type: str) -> None:
            """Broadcast new agent discovery to all connected agents."""
    ```
    **Category:** Bug risk
    **Severity:** critical

63. **Undefined variable 'response'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 319
    ```python
    "agents": list(self._agent_registry.values()),
                    "count": len(self._agent_registry)
                }
                await self.event_mesh.send_to(client_id, response)
                
            elif action == "by_type":
                # Filter by agent type
    ```
    **Category:** Bug risk
    **Severity:** critical

64. **Undefined variable 'action'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 311
    ```python
    """Handle discovery request - return list of all agents."""
            _action = message.get("action", "list_agents")
            
            if action == "list_agents":
                # Return all registered agents
                _response = {
                    "type": "discovery",
    ```
    **Category:** Bug risk
    **Severity:** critical

65. **Undefined variable 'agent'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 509
    ```python
    def _get_agent_type(self, client_id: str) -> str:
            """Get agent type for client ID."""
            _agent = self._agent_registry.get(client_id, {})
            return agent.get("agent_type", "unknown")
        
        def get_stats(self) -> Dict[str, Any]:
            """Get A2A Protocol statistics."""
    ```
    **Category:** Bug risk
    **Severity:** critical

66. **Undefined variable 'channel'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 499
    ```python
    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                await self.redis_client.publish(channel, json.dumps(message_data))
                
            except Exception as e:
                logger.error("a2a_redis_log_failed", error=str(e))
    ```
    **Category:** Bug risk
    **Severity:** critical

67. **Undefined variable 'agent_type'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 263
    ```python
    logger.info(
                "a2a_handshake_completed",
                _client_id = client_id,
                _agent_type = agent_type
            )
            
            # Broadcast discovery to other agents
    ```
    **Category:** Bug risk
    **Severity:** critical

68. **Undefined variable 'routes'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 119
    ```python
    Route("/health", self._health_check),
            ]
            
            _app = Starlette(routes=routes)
            
            import uvicorn
            _config = uvicorn.Config(
    ```
    **Category:** Bug risk
    **Severity:** critical

69. **Undefined variable 'content'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 361
    ```python
    MessageType.MESSAGE.value,
                client_id,
                self._get_agent_type(client_id),
                content
            )
        
        async def _handle_status(self, client_id: str, message: Dict[str, Any]) -> None:
    ```
    **Category:** Bug risk
    **Severity:** critical

70. **Undefined variable 'agent_type'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 256
    ```python
    await self._log_message(
                MessageType.HANDSHAKE.value,
                client_id,
                agent_type,
                {"status": "connected"}
            )
    ```
    **Category:** Bug risk
    **Severity:** critical

71. **Unexpected keyword argument '_log_level' in constructor call** (`PYL-E1123`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 122
    ```python
    _app = Starlette(routes=routes)
            
            import uvicorn
            _config = uvicorn.Config(
                app,
                host="0.0.0.0",
                port=self.port,
    ```
    **Category:** Bug risk
    **Severity:** critical

72. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 130
    ```python
    )
            self._server = uvicorn.Server(config)
            
            logger.info("a2a_server_starting", port=self.port)
            
            config.setup()
            self._running = True
    ```
    **Category:** Bug risk
    **Severity:** critical

73. **Undefined variable 'client_id'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 233
    ```python
    # Register in agent registry
            self._agent_registry[client_id] = {
                "agent_id": client_id,
                "agent_type": agent_type,
                "capabilities": capabilities,
                "metadata": metadata,
    ```
    **Category:** Bug risk
    **Severity:** critical

74. **Undefined variable 'target_id'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 351
    ```python
    if target_id:
                # Direct message
                await self.event_mesh.send_to(target_id, message)
            else:
                # Broadcast
                await self.event_mesh.broadcast(message, exclude=[client_id])
    ```
    **Category:** Bug risk
    **Severity:** critical

75. **Undefined variable 'action'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 321
    ```python
    }
                await self.event_mesh.send_to(client_id, response)
                
            elif action == "by_type":
                # Filter by agent type
                _agent_type = message.get("agent_type")
                _filtered = [
    ```
    **Category:** Bug risk
    **Severity:** critical

76. **Undefined variable 'client_id'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 255
    ```python
    # Log to Redis
            await self._log_message(
                MessageType.HANDSHAKE.value,
                client_id,
                agent_type,
                {"status": "connected"}
            )
    ```
    **Category:** Bug risk
    **Severity:** critical

77. **Undefined variable 'handler_map'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 299
    ```python
    MessageType.DECISION: self._handle_decision,
            }
            
            _handler = handler_map.get(msg_type)
            if handler:
                await handler(client_id, message)
            else:
    ```
    **Category:** Bug risk
    **Severity:** critical

78. **Undefined variable 'handler'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 301
    ```python
    _handler = handler_map.get(msg_type)
            if handler:
                await handler(client_id, message)
            else:
                logger.warning("a2a_unknown_message_type", type=msg_type)
    ```
    **Category:** Bug risk
    **Severity:** critical

79. **Undefined variable 'config'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 132
    ```python
    logger.info("a2a_server_starting", port=self.port)
            
            config.setup()
            self._running = True
            
            # Run server
    ```
    **Category:** Bug risk
    **Severity:** critical

80. **Undefined variable 'client_id'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 228
    ```python
    )
            
            # Track connection
            self._connections[client_id] = websocket
            self._authenticated.add(client_id)
            
            # Register in agent registry
    ```
    **Category:** Bug risk
    **Severity:** critical

81. **Undefined variable 'discovery_msg'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 282
    ```python
    }
            
            await self.event_mesh.broadcast(
                discovery_msg,
                _exclude = [client_id]
            )
    ```
    **Category:** Bug risk
    **Severity:** critical

82. **Undefined variable 'msg_type'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 183
    ```python
    _msg_type = raw_message.get("type")
                    
                    # Handle handshake first
                    if msg_type == MessageType.HANDSHAKE:
                        _client_id = await self._handle_handshake(websocket, raw_message)
                        continue
    ```
    **Category:** Bug risk
    **Severity:** critical

83. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 138
    ```python
    # Run server
            asyncio.create_task(self._server.serve())
            
            logger.info("a2a_server_started", port=self.port)
        
        async def stop_server(self) -> None:
            """Stop the WebSocket server."""
    ```
    **Category:** Bug risk
    **Severity:** critical

84. **Undefined variable 'decision'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 434
    ```python
    "a2a_decision_made",
                _client_id = client_id,
                _proposal_id = proposal_id,
                _decision = decision
            )
            
            await self._log_message(
    ```
    **Category:** Bug risk
    **Severity:** critical

85. **Undefined variable 'client_id'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 204
    ```python
    finally:
                # Cleanup
                if client_id:
                    await self._cleanup_connection(client_id)
        
        async def _handle_handshake(self, websocket: WebSocket, message: Dict[str, Any]) -> str:
            """
    ```
    **Category:** Bug risk
    **Severity:** critical

86. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 303
    ```python
    if handler:
                await handler(client_id, message)
            else:
                logger.warning("a2a_unknown_message_type", type=msg_type)
        
        # ============== Message Handlers ==============
    ```
    **Category:** Bug risk
    **Severity:** critical

87. **Undefined variable 'app'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 123
    ```python
    import uvicorn
            _config = uvicorn.Config(
                app,
                host="0.0.0.0",
                port=self.port,
                _log_level = "info"
    ```
    **Category:** Bug risk
    **Severity:** critical

88. **Undefined variable 'metadata'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 236
    ```python
    "agent_id": client_id,
                "agent_type": agent_type,
                "capabilities": capabilities,
                "metadata": metadata,
                "connected_at": datetime.now(timezone.utc).isoformat()
            }
    ```
    **Category:** Bug risk
    **Severity:** critical

89. **Undefined variable 'atype'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 527
    ```python
    counts: Dict[str, int] = {}
            for agent in self._agent_registry.values():
                _atype = agent.get("agent_type", "unknown")
                counts[atype] = counts.get(atype, 0) + 1
            return counts
    ```
    **Category:** Bug risk
    **Severity:** critical

90. **Undefined variable 'client_id'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 232
    ```python
    self._authenticated.add(client_id)
            
            # Register in agent registry
            self._agent_registry[client_id] = {
                "agent_id": client_id,
                "agent_type": agent_type,
                "capabilities": capabilities,
    ```
    **Category:** Bug risk
    **Severity:** critical

91. **Undefined variable 'agent_info'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 469
    ```python
    logger.info(
                "a2a_connection_cleaned",
                _client_id = client_id,
                _agent_type = agent_info.get("agent_type", "unknown")
            )
            
            # Broadcast disconnect
    ```
    **Category:** Bug risk
    **Severity:** critical

92. **Undefined variable 'proposal_id'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 433
    ```python
    logger.info(
                "a2a_decision_made",
                _client_id = client_id,
                _proposal_id = proposal_id,
                _decision = decision
            )
    ```
    **Category:** Bug risk
    **Severity:** critical

93. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 98
    ```python
    self._server = None
            self._running = False
            
            logger.info(
                "a2a_protocol_initialized",
                port=port,
                _redis_enabled = redis_client is not None,
    ```
    **Category:** Bug risk
    **Severity:** critical

94. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 199
    ```python
    await self._route_message(websocket, client_id, raw_message)
                    
            except Exception as e:
                logger.error("a2a_connection_error", error=str(e), client_id=client_id)
                
            finally:
                # Cleanup
    ```
    **Category:** Bug risk
    **Severity:** critical

95. **Undefined variable 'target_id'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/a2a_protocol.py`
    **Line:** 349
    ```python
    _target_id = message.get("target")
            _content = message.get("content", {})
            
            if target_id:
                # Direct message
                await self.event_mesh.send_to(target_id, message)
            else:
    ```
    **Category:** Bug risk
    **Severity:** critical

96. **Access to a protected member _message_cache of a client class** (`PYL-W0212`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 1765
    ```python
    "agent_id": self.agent_id,
                "collective_learning": {
                    "patterns_extracted": len(self.pattern_extractor._validated_patterns) if self.pattern_extractor else 0,
                    "message_cache_size": len(self.pattern_extractor._message_cache) if self.pattern_extractor else 0,
                },
                "consensus": {
                    "active_deliberations": len(self._active_deliberations),
    ```
    **Category:** Bug risk
    **Severity:** minor

97. **Access to a protected member _validated_patterns of a client class** (`PYL-W0212`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 1764
    ```python
    _status = {
                "agent_id": self.agent_id,
                "collective_learning": {
                    "patterns_extracted": len(self.pattern_extractor._validated_patterns) if self.pattern_extractor else 0,
                    "message_cache_size": len(self.pattern_extractor._message_cache) if self.pattern_extractor else 0,
                },
                "consensus": {
    ```
    **Category:** Bug risk
    **Severity:** minor

98. **Attribute '_message_handlers' defined outside __init__** (`PYL-W0201`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 265
    ```python
    def _register_handlers(self) -> None:
            """Register message handlers."""
            self._message_handlers = {
                "report_conflict": self._handle_report_conflict,
                "request_arbitration": self._handle_request_arbitration,
                "mediate_dispute": self._handle_mediate_dispute,
    ```
    **Category:** Anti-pattern
    **Severity:** minor

99. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 1373
    ```python
    ],
            }
        
        async def _resolve_generic_contention(self, _contention_type: str, _competing_agents: List[str]) -> Dict[str, Any]:
            """Resolve generic contention."""
            return {
                "contention_type": contention_type,
    ```
    **Category:** Performance
    **Severity:** major

100. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
     **File:** `src/heretek_swarm/actors/arbiter.py`
     **Line:** 1191
     ```python
     conflict.proposed_resolutions.append(proposal)
             return {"status": "proposal_generated", "strategy": "negotiation"}
         
         async def _resolve_mediation(self, _conflict: Conflict) -> Dict[str, Any]:
             """Mediation-based resolution."""
             _proposal = {
                 "strategy": "mediation",
     ```
     **Category:** Performance
     **Severity:** major

*...and 30029 more occurrences. [See full list on DeepSource](https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/466a5172-b5c7-48b1-85a3-4e8230662342/).*### Secrets
**Status:** Success
**Findings:** No new issues detected
### SQL
**Status:** Success
**Findings:** No new issues detected

21317# DeepSource Code Review Report

**Repository:** Heretek-AI/heretek-swarm
**Branch:** `main`
**Commit:** 0f4686a...0f4686a
**Run:** [https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/6ce83273-62c5-44e0-9536-f18b5e832267/](https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/6ce83273-62c5-44e0-9536-f18b5e832267/)

---

## Summary
- **Shell:** 11 issues- **Python:** 3267 issues- **Secrets:** 34 issues- **JavaScript:** 505 issues- **Docker:** 5 issues- **SQL:** No issues detected

---

## Code Review Findings
### Shell
**Status:** Failure
**Findings:** 11 new issues

1. **Quote this to prevent word splitting** (`SH-2046`)
   **File:** `deploy_full_stack.sh`
   **Line:** 14
   ```bash
   # Load environment variables
   if [ -f .env ]; then
       echo "Loading environment from .env..."
       export $(cat .env | grep -v '^#' | xargs)
   fi
   
   # Build images
   ```
   **Category:** Bug risk
   **Severity:** major

2. **Double quote to prevent globbing and word splitting** (`SH-2086`)
   **File:** `deploy.sh`
   **Line:** 196
   ```bash
   log_info "Redis is ready"
               break
           fi
           if [ $i -eq 30 ]; then
               log_warn "Redis health check timed out"
           fi
           sleep 2
   ```
   **Category:** Bug risk
   **Severity:** major

3. **Double quote to prevent globbing and word splitting** (`SH-2086`)
   **File:** `deploy.sh`
   **Line:** 183
   ```bash
   log_info "PostgreSQL is ready"
               break
           fi
           if [ $i -eq 30 ]; then
               log_warn "PostgreSQL health check timed out"
           fi
           sleep 2
   ```
   **Category:** Bug risk
   **Severity:** major

4. **In POSIX sh, =~ regex matching is undefined** (`SH-3015`)
   **File:** `deploy.sh`
   **Line:** 117
   ```bash
   if [ -f "$ENV_FILE" ]; then
           log_info "Environment file already exists: $ENV_FILE"
           read -p "Do you want to overwrite it? (y/N): " overwrite
           if [[ "$overwrite" =~ ^[Yy]$ ]]; then
               cp "$ENV_EXAMPLE" "$ENV_FILE"
               log_info "Environment file created from template"
           fi
   ```
   **Category:** Bug risk
   **Severity:** major

5. **In POSIX sh, =~ regex matching is undefined** (`SH-3015`)
   **File:** `deploy.sh`
   **Line:** 365
   ```bash
   clean)
           log_warn "This will remove all containers, networks, and volumes!"
           read -p "Are you sure? (y/N): " confirm
           if [[ "$confirm" =~ ^[Yy]$ ]]; then
               cd "$SCRIPT_DIR"
               if command -v docker-compose &> /dev/null; then
                   docker-compose down -v
   ```
   **Category:** Bug risk
   **Severity:** major

6. **Double quote to prevent globbing and word splitting** (`SH-2086`)
   **File:** `deploy.sh`
   **Line:** 209
   ```bash
   log_info "Qdrant is ready"
               break
           fi
           if [ $i -eq 30 ]; then
               log_warn "Qdrant health check timed out"
           fi
           sleep 2
   ```
   **Category:** Bug risk
   **Severity:** major

7. **COMPOSE_FILE appears unused. Verify use (or export if used externally)** (`SH-2034`)
   **File:** `deploy.sh`
   **Line:** 14
   ```bash
   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
   ENV_FILE="${SCRIPT_DIR}/.env"
   ENV_EXAMPLE="${SCRIPT_DIR}/.env.example"
   COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
   LOG_FILE="${SCRIPT_DIR}/deploy.log"
   
   # Colors for output
   ```
   **Category:** Anti-pattern
   **Severity:** major

8. **Double quote to prevent globbing and word splitting** (`SH-2086`)
   **File:** `docker/docker-entrypoint.sh`
   **Line:** 15
   ```bash
   echo "Waiting for dependencies: $DOCKER_WAIT_FOR"
       IFS=',' read -ra ADDR <<< "$DOCKER_WAIT_FOR"
       for i in "${ADDR[@]}"; do
           host=$(echo $i | cut -d':' -f1)
           port=$(echo $i | cut -d':' -f2)
           echo "  Waiting for $host:$port..."
           while ! nc -z $host $port; do
   ```
   **Category:** Bug risk
   **Severity:** major

9. **Double quote to prevent globbing and word splitting** (`SH-2086`)
   **File:** `docker/docker-entrypoint.sh`
   **Line:** 16
   ```bash
   IFS=',' read -ra ADDR <<< "$DOCKER_WAIT_FOR"
       for i in "${ADDR[@]}"; do
           host=$(echo $i | cut -d':' -f1)
           port=$(echo $i | cut -d':' -f2)
           echo "  Waiting for $host:$port..."
           while ! nc -z $host $port; do
               sleep 1
   ```
   **Category:** Bug risk
   **Severity:** major

10. **Double quote to prevent globbing and word splitting** (`SH-2086`)
    **File:** `docker/docker-entrypoint.sh`
    **Line:** 18
    ```bash
    host=$(echo $i | cut -d':' -f1)
            port=$(echo $i | cut -d':' -f2)
            echo "  Waiting for $host:$port..."
            while ! nc -z $host $port; do
                sleep 1
            done
            echo "  $host:$port is available"
    ```
    **Category:** Bug risk
    **Severity:** major

11. **Double quote to prevent globbing and word splitting** (`SH-2086`)
    **File:** `docker/docker-entrypoint.sh`
    **Line:** 18
    ```bash
    host=$(echo $i | cut -d':' -f1)
            port=$(echo $i | cut -d':' -f2)
            echo "  Waiting for $host:$port..."
            while ! nc -z $host $port; do
                sleep 1
            done
            echo "  $host:$port is available"
    ```
    **Category:** Bug risk
    **Severity:** major
### Python
**Status:** Failure
**Findings:** 3267 new issues

1. **Use lazy % formatting in logging functions** (`PYL-W1203`)
   **File:** `scripts/run_migrations.py`
   **Line:** 267
   ```python
   logger.error(f"Migration {mf.name} failed")
       
       logger.info(f"\nMigration Summary:")
       logger.info(f"  Succeeded: {success_count}")
       logger.info(f"  Failed: {failed_count}")
       
       return 1 if failed_count > 0 else 0
   ```
   **Category:** Performance
   **Severity:** minor

2. **Use lazy % formatting in logging functions** (`PYL-W1203`)
   **File:** `scripts/run_migrations.py`
   **Line:** 144
   ```python
   rows = cursor.fetchall()
               logger.info("Applied migrations:")
               for version, applied in rows:
                   logger.info(f"  {version}: {applied}")
           
           # Check if swarm_memories table exists
           cursor.execute("""
   ```
   **Category:** Performance
   **Severity:** minor

3. **Use lazy % formatting in logging functions** (`PYL-W1203`)
   **File:** `scripts/run_migrations.py`
   **Line:** 188
   ```python
   except ImportError:
           logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
       except Exception as e:
           logger.error(f"Failed to check status: {e}")
   
   
   def create_migrations_table() -> bool:
   ```
   **Category:** Performance
   **Severity:** minor

4. **Use lazy % formatting in logging functions** (`PYL-W1203`)
   **File:** `scripts/run_migrations.py`
   **Line:** 268
   ```python
   logger.info(f"\nMigration Summary:")
       logger.info(f"  Succeeded: {success_count}")
       logger.info(f"  Failed: {failed_count}")
       
       return 1 if failed_count > 0 else 0
   ```
   **Category:** Performance
   **Severity:** minor

5. **Use lazy % formatting in logging functions** (`PYL-W1203`)
   **File:** `scripts/run_migrations.py`
   **Line:** 66
   ```python
   metadata = parse_migration_header(content)
       
       logger.info(f"Executing migration: {migration_file.name}")
       logger.info(f"  Description: {metadata.get('description', 'N/A')}")
       
       try:
           # Connect to database
   ```
   **Category:** Performance
   **Severity:** minor

6. **Use lazy % formatting in logging functions** (`PYL-W1203`)
   **File:** `scripts/run_migrations.py`
   **Line:** 115
   ```python
   logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
           return False
       except Exception as e:
           logger.error(f"Migration failed: {e}")
           return False
   ```
   **Category:** Performance
   **Severity:** minor

7. **Use lazy % formatting in logging functions** (`PYL-W1203`)
   **File:** `scripts/run_migrations.py`
   **Line:** 266
   ```python
   failed_count += 1
               logger.error(f"Migration {mf.name} failed")
       
       logger.info(f"\nMigration Summary:")
       logger.info(f"  Succeeded: {success_count}")
       logger.info(f"  Failed: {failed_count}")
   ```
   **Category:** Performance
   **Severity:** minor

8. **Use lazy % formatting in logging functions** (`PYL-W1203`)
   **File:** `scripts/run_migrations.py`
   **Line:** 253
   ```python
   if args.dry_run:
           logger.info("Dry run - would execute:")
           for mf in migration_files:
               logger.info(f"  - {mf.name}")
           return 0
       
       success_count = 0
   ```
   **Category:** Performance
   **Severity:** minor

9. **Use lazy % formatting in logging functions** (`PYL-W1203`)
   **File:** `scripts/run_migrations.py`
   **Line:** 100
   ```python
   cursor.execute(stmt)
                   logger.debug(f"  Executed statement {i+1}/{len(statements)}")
               except psycopg2.Error as e:
                   logger.error(f"  Statement {i+1} failed: {e}")
                   logger.error(f"  Statement: {stmt[:200]}...")
                   conn.close()
                   return False
   ```
   **Category:** Performance
   **Severity:** minor

10. **Use lazy % formatting in logging functions** (`PYL-W1203`)
    **File:** `scripts/run_migrations.py`
    **Line:** 167
    ```python
    columns = cursor.fetchall()
                logger.info("  Columns:")
                for col in columns:
                    logger.info(f"    - {col[0]}: {col[1]} (nullable: {col[2]})")
                
                # Show indexes
                cursor.execute("""
    ```
    **Category:** Performance
    **Severity:** minor

11. **Use lazy % formatting in logging functions** (`PYL-W1203`)
    **File:** `scripts/run_migrations.py`
    **Line:** 101
    ```python
    logger.debug(f"  Executed statement {i+1}/{len(statements)}")
                except psycopg2.Error as e:
                    logger.error(f"  Statement {i+1} failed: {e}")
                    logger.error(f"  Statement: {stmt[:200]}...")
                    conn.close()
                    return False
    ```
    **Category:** Performance
    **Severity:** minor

12. **Use lazy % formatting in logging functions** (`PYL-W1203`)
    **File:** `scripts/run_migrations.py`
    **Line:** 65
    ```python
    content = migration_file.read_text()
        metadata = parse_migration_header(content)
        
        logger.info(f"Executing migration: {migration_file.name}")
        logger.info(f"  Description: {metadata.get('description', 'N/A')}")
        
        try:
    ```
    **Category:** Performance
    **Severity:** minor

13. **Use lazy % formatting in logging functions** (`PYL-W1203`)
    **File:** `scripts/run_migrations.py`
    **Line:** 178
    ```python
    indexes = cursor.fetchall()
                logger.info("  Indexes:")
                for idx_name, idx_def in indexes:
                    logger.info(f"    - {idx_name}")
            else:
                logger.info("\nswarm_memories table does not exist yet")
    ```
    **Category:** Performance
    **Severity:** minor

14. **Use lazy % formatting in logging functions** (`PYL-W1203`)
    **File:** `scripts/run_migrations.py`
    **Line:** 264
    ```python
    success_count += 1
            else:
                failed_count += 1
                logger.error(f"Migration {mf.name} failed")
        
        logger.info(f"\nMigration Summary:")
        logger.info(f"  Succeeded: {success_count}")
    ```
    **Category:** Performance
    **Severity:** minor

15. **Use lazy % formatting in logging functions** (`PYL-W1203`)
    **File:** `scripts/run_migrations.py`
    **Line:** 98
    ```python
    continue
                try:
                    cursor.execute(stmt)
                    logger.debug(f"  Executed statement {i+1}/{len(statements)}")
                except psycopg2.Error as e:
                    logger.error(f"  Statement {i+1} failed: {e}")
                    logger.error(f"  Statement: {stmt[:200]}...")
    ```
    **Category:** Performance
    **Severity:** minor

16. **Use lazy % formatting in logging functions** (`PYL-W1203`)
    **File:** `scripts/run_migrations.py`
    **Line:** 108
    ```python
    cursor.close()
            conn.close()
            
            logger.info(f"  Migration {migration_file.name} completed successfully")
            return True
            
        except ImportError:
    ```
    **Category:** Performance
    **Severity:** minor

17. **Use lazy % formatting in logging functions** (`PYL-W1203`)
    **File:** `scripts/run_migrations.py`
    **Line:** 34
    ```python
    def get_migration_files() -> list[Path]:
        """Get all SQL migration files sorted by version."""
        if not MIGRATIONS_DIR.exists():
            logger.error(f"Migrations directory not found: {MIGRATIONS_DIR}")
            return []
        
        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    ```
    **Category:** Performance
    **Severity:** minor

18. **Use lazy % formatting in logging functions** (`PYL-W1203`)
    **File:** `scripts/run_migrations.py`
    **Line:** 38
    ```python
    return []
        
        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        logger.info(f"Found {len(migration_files)} migration files")
        return migration_files
    ```
    **Category:** Performance
    **Severity:** minor

19. **Use lazy % formatting in logging functions** (`PYL-W1203`)
    **File:** `scripts/run_migrations.py`
    **Line:** 215
    ```python
    return True
            
        except Exception as e:
            logger.error(f"Failed to create migrations table: {e}")
            return False
    ```
    **Category:** Performance
    **Severity:** minor

20. **`f-string` used without any expression** (`PTC-W0027`)
    **File:** `scripts/run_migrations.py`
    **Line:** 266
    ```python
    failed_count += 1
                logger.error(f"Migration {mf.name} failed")
        
        logger.info(f"\nMigration Summary:")
        logger.info(f"  Succeeded: {success_count}")
        logger.info(f"  Failed: {failed_count}")
    ```
    **Category:** Anti-pattern
    **Severity:** major

21. **Unused variable 'idx_def'** (`PYL-W0612`)
    **File:** `scripts/run_migrations.py`
    **Line:** 177
    ```python
    """)
                indexes = cursor.fetchall()
                logger.info("  Indexes:")
                for idx_name, idx_def in indexes:
                    logger.info(f"    - {idx_name}")
            else:
                logger.info("\nswarm_memories table does not exist yet")
    ```
    **Category:** Anti-pattern
    **Severity:** major

22. **`f-string` used without any expression** (`PTC-W0027`)
    **File:** `scripts/test_mem0.py`
    **Line:** 72
    ```python
    # Try to initialize backend
            backend = Mem0Backend(config)
            print(f"\n✅ Mem0Backend created")
            
            # Try to initialize (may fail without API key)
            try:
    ```
    **Category:** Anti-pattern
    **Severity:** major

23. **`f-string` used without any expression** (`PTC-W0027`)
    **File:** `scripts/test_mem0.py`
    **Line:** 57
    ```python
    # Create config
            config = Mem0Config()
            print(f"✅ Mem0Config created")
            print(f"   Vector store: {config.vector_store_provider}")
            print(f"   Qdrant: {config.qdrant_host}:{config.qdrant_port}")
            print(f"   Collection: {config.qdrant_collection}")
    ```
    **Category:** Anti-pattern
    **Severity:** major

24. **`wire_agent_file` has a cyclomatic complexity of 20 with "high" risk** (`PY-R1000`)
    **File:** `scripts/wire_agents.py`
    **Line:** 275
    ```python
    '''
    
    
    def wire_agent_file(filepath: Path) -> bool:
        """Apply agent wiring to an agent file."""
        if not filepath.exists():
            print(f"File not found: {filepath}")
    ```
    **Category:** Anti-pattern
    **Severity:** minor

25. **Redefining name 'agents' from outer scope** (`PYL-W0621`)
    **File:** `scripts/wire_agents.py`
    **Line:** 474
    ```python
    Returns:
            Agent metadata dictionary or None if not found
        """
        agents = discover_agents(actors_dir)
        
        for agent in agents:
            if agent["type_name"] == agent_type:
    ```
    **Category:** Anti-pattern
    **Severity:** major

26. **Redefining name 'agent' from outer scope** (`PYL-W0621`)
    **File:** `scripts/wire_agents.py`
    **Line:** 476
    ```python
    """
        agents = discover_agents(actors_dir)
        
        for agent in agents:
            if agent["type_name"] == agent_type:
                return agent
    ```
    **Category:** Anti-pattern
    **Severity:** major

27. **Undefined variable 'SESSION_44_INIT_BODY'** (`PYL-E0602`)
    **File:** `scripts/wire_agents.py`
    **Line:** 325
    ```python
    match = re.search(init_body_pattern, content, re.IGNORECASE)
            if match:
                insert_pos = match.start()
                content = content[:insert_pos] + SESSION_44_INIT_BODY + "\n\n        " + content[insert_pos:]
                print(f"  Added __init__ body to {filepath.name}")
        
        # 4. Add integration methods at end of class (before last method)
    ```
    **Category:** Bug risk
    **Severity:** critical

28. **Undefined variable 'SESSION_44_INIT_PARAMS'** (`PYL-E0602`)
    **File:** `scripts/wire_agents.py`
    **Line:** 315
    ```python
    i += 1
                
                # Insert before closing parenthesis
                content = content[:i-1] + SESSION_44_INIT_PARAMS + content[i-1:]
                print(f"  Added __init__ parameters to {filepath.name}")
        
        # 3. Add __init__ body
    ```
    **Category:** Bug risk
    **Severity:** critical

29. **Undefined variable 'SESSION_44_METHODS'** (`PYL-E0602`)
    **File:** `scripts/wire_agents.py`
    **Line:** 345
    ```python
    insert_pos = match.start()
                        break
                
                content = content[:insert_pos] + SESSION_44_METHODS + "\n" + content[insert_pos:]
                print(f"  Added integration methods to {filepath.name}")
        
        # Write the modified content
    ```
    **Category:** Bug risk
    **Severity:** critical

30. **Undefined variable 'SESSION_44_IMPORTS'** (`PYL-E0602`)
    **File:** `scripts/wire_agents.py`
    **Line:** 293
    ```python
    if line.startswith('from ') or line.startswith('import '):
                    insert_idx = i + 1
            
            lines.insert(insert_idx, SESSION_44_IMPORTS)
            content = '\n'.join(lines)
            print(f"  Added imports to {filepath.name}")
    ```
    **Category:** Bug risk
    **Severity:** critical

31. **`wire_agent_file` has a cyclomatic complexity of 20 with "high" risk** (`PY-R1000`)
    **File:** `scripts/wire_agents_session44.py`
    **Line:** 273
    ```python
    '''
    
    
    def wire_agent_file(filepath: Path) -> bool:
        """Apply Session 44 wiring to an agent file."""
        if not filepath.exists():
            print(f"File not found: {filepath}")
    ```
    **Category:** Anti-pattern
    **Severity:** minor

32. **`handle_profiling_api` has a cyclomatic complexity of 20 with "high" risk** (`PY-R1000`)
    **File:** `serverless/handler.py`
    **Line:** 275
    ```python
    ).to_dict()
    
    
    def handle_profiling_api(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle behavior profiling API endpoints."""
        path = event.get("path", "")
        method = event.get("httpMethod", "GET")
    ```
    **Category:** Anti-pattern
    **Severity:** minor

33. **Using the global statement** (`PYL-W0603`)
    **File:** `serverless/handler.py`
    **Line:** 629
    ```python
    def get_profiler():
        """Get or initialize behavior profiler."""
        global _profiler
        
        if _profiler is None:
            try:
    ```
    **Category:** Anti-pattern
    **Severity:** minor

34. **`api_handler` has a cyclomatic complexity of 16 with "high" risk** (`PY-R1000`)
    **File:** `serverless/handler.py`
    **Line:** 119
    ```python
    }
    
    
    def api_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Main API Gateway handler for Heretek Swarm.
    ```
    **Category:** Anti-pattern
    **Severity:** minor

35. **Unused argument 'context'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 381
    ```python
    ).to_dict()
    
    
    def handle_observability_api(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle /api/observability routes."""
        return APIResponse(
            status_code=200,
    ```
    **Category:** Anti-pattern
    **Severity:** major

36. **Unused argument 'context'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 556
    ```python
    }
    
    
    def rag_index_optimize(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Optimize RAG vector indexes.
    ```
    **Category:** Anti-pattern
    **Severity:** major

37. **Using global for '_redis_connection' but no assignment is done** (`PYL-W0602`)
    **File:** `serverless/handler.py`
    **Line:** 68
    ```python
    This function is called once per container initialization
        to reuse connections across multiple invocations.
        """
        global _db_connection, _redis_connection, _rag_pipeline, _profiler
        
        log.info("initializing_dependencies")
    ```
    **Category:** Bug risk
    **Severity:** major

38. **Unused argument 'event'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 211
    ```python
    ).to_dict()
    
    
    def readiness_check(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Readiness check endpoint.
    ```
    **Category:** Anti-pattern
    **Severity:** major

39. **Unused argument 'event'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 381
    ```python
    ).to_dict()
    
    
    def handle_observability_api(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle /api/observability routes."""
        return APIResponse(
            status_code=200,
    ```
    **Category:** Anti-pattern
    **Severity:** major

40. **Unused argument 'context'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 211
    ```python
    ).to_dict()
    
    
    def readiness_check(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Readiness check endpoint.
    ```
    **Category:** Anti-pattern
    **Severity:** major

41. **Unused argument 'event'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 348
    ```python
    ).to_dict()
    
    
    def handle_rag_api(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle /api/rag routes."""
        return APIResponse(
            status_code=200,
    ```
    **Category:** Anti-pattern
    **Severity:** major

42. **Unused argument 'event'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 359
    ```python
    ).to_dict()
    
    
    def handle_workflows_api(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle /api/workflows routes."""
        return APIResponse(
            status_code=200,
    ```
    **Category:** Anti-pattern
    **Severity:** major

43. **Using global for '_db_connection' but no assignment is done** (`PYL-W0602`)
    **File:** `serverless/handler.py`
    **Line:** 68
    ```python
    This function is called once per container initialization
        to reuse connections across multiple invocations.
        """
        global _db_connection, _redis_connection, _rag_pipeline, _profiler
        
        log.info("initializing_dependencies")
    ```
    **Category:** Bug risk
    **Severity:** major

44. **Unused argument 'event'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 193
    ```python
    )
    
    
    def health_check(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Health check endpoint.
    ```
    **Category:** Anti-pattern
    **Severity:** major

45. **Unused argument 'context'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 392
    ```python
    ).to_dict()
    
    
    def handle_config_api(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle /api/config routes."""
        return APIResponse(
            status_code=200,
    ```
    **Category:** Anti-pattern
    **Severity:** major

46. **Using global for '_profiler' but no assignment is done** (`PYL-W0602`)
    **File:** `serverless/handler.py`
    **Line:** 68
    ```python
    This function is called once per container initialization
        to reuse connections across multiple invocations.
        """
        global _db_connection, _redis_connection, _rag_pipeline, _profiler
        
        log.info("initializing_dependencies")
    ```
    **Category:** Bug risk
    **Severity:** major

47. **Unused argument 'context'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 275
    ```python
    ).to_dict()
    
    
    def handle_profiling_api(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle behavior profiling API endpoints."""
        path = event.get("path", "")
        method = event.get("httpMethod", "GET")
    ```
    **Category:** Anti-pattern
    **Severity:** major

48. **Unused argument 'context'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 359
    ```python
    ).to_dict()
    
    
    def handle_workflows_api(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle /api/workflows routes."""
        return APIResponse(
            status_code=200,
    ```
    **Category:** Anti-pattern
    **Severity:** major

49. **Unused argument 'event'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 392
    ```python
    ).to_dict()
    
    
    def handle_config_api(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle /api/config routes."""
        return APIResponse(
            status_code=200,
    ```
    **Category:** Anti-pattern
    **Severity:** major

50. **Unused argument 'event'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 531
    ```python
    }
    
    
    def agent_state_cleanup(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Cleanup expired agent states.
    ```
    **Category:** Anti-pattern
    **Severity:** major

51. **Unused variable 'profile'** (`PYL-W0612`)
    **File:** `serverless/handler.py`
    **Line:** 607
    ```python
    results["profiles_analyzed"] = len(profiles)
            
            # Detect anomalies for each agent type
            for agent_type, profile in profiles.items():
                anomalies = profiler.detect_anomalies(f"{agent_type}-analysis")
                results["anomalies_detected"] += len(anomalies)
    ```
    **Category:** Anti-pattern
    **Severity:** major

52. **Unused argument 'context'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 531
    ```python
    }
    
    
    def agent_state_cleanup(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Cleanup expired agent states.
    ```
    **Category:** Anti-pattern
    **Severity:** major

53. **Unused argument 'context'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 504
    ```python
    # EventBridge Scheduled Handlers
    # =============================================================================
    
    def swarm_health_check(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Scheduled health check for swarm agents.
    ```
    **Category:** Anti-pattern
    **Severity:** major

54. **Using global for '_rag_pipeline' but no assignment is done** (`PYL-W0602`)
    **File:** `serverless/handler.py`
    **Line:** 68
    ```python
    This function is called once per container initialization
        to reuse connections across multiple invocations.
        """
        global _db_connection, _redis_connection, _rag_pipeline, _profiler
        
        log.info("initializing_dependencies")
    ```
    **Category:** Bug risk
    **Severity:** major

55. **Unused argument 'context'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 348
    ```python
    ).to_dict()
    
    
    def handle_rag_api(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle /api/rag routes."""
        return APIResponse(
            status_code=200,
    ```
    **Category:** Anti-pattern
    **Severity:** major

56. **Unused argument 'context'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 584
    ```python
    }
    
    
    def behavior_profile_analyzer(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Analyze agent behavior profiles and detect anomalies.
    ```
    **Category:** Anti-pattern
    **Severity:** major

57. **Unused argument 'event'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 584
    ```python
    }
    
    
    def behavior_profile_analyzer(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Analyze agent behavior profiles and detect anomalies.
    ```
    **Category:** Anti-pattern
    **Severity:** major

58. **Unused argument 'context'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 370
    ```python
    ).to_dict()
    
    
    def handle_consensus_api(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle /api/consensus routes."""
        return APIResponse(
            status_code=200,
    ```
    **Category:** Anti-pattern
    **Severity:** major

59. **Unused argument 'context'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 193
    ```python
    )
    
    
    def health_check(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Health check endpoint.
    ```
    **Category:** Anti-pattern
    **Severity:** major

60. **Unused argument 'event'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 556
    ```python
    }
    
    
    def rag_index_optimize(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Optimize RAG vector indexes.
    ```
    **Category:** Anti-pattern
    **Severity:** major

61. **Unused argument 'event'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 370
    ```python
    ).to_dict()
    
    
    def handle_consensus_api(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle /api/consensus routes."""
        return APIResponse(
            status_code=200,
    ```
    **Category:** Anti-pattern
    **Severity:** major

62. **Unused argument 'event'** (`PYL-W0613`)
    **File:** `serverless/handler.py`
    **Line:** 504
    ```python
    # EventBridge Scheduled Handlers
    # =============================================================================
    
    def swarm_health_check(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Scheduled health check for swarm agents.
    ```
    **Category:** Anti-pattern
    **Severity:** major

63. **Using the global statement** (`PYL-W0603`)
    **File:** `src/evaluation/evaluator.py`
    **Line:** 502
    ```python
    Returns:
            AgentEvaluator instance
        """
        global _evaluator_instance
        if _evaluator_instance is None:
            _evaluator_instance = AgentEvaluator()
            logger.info("evaluator_singleton_created")
    ```
    **Category:** Anti-pattern
    **Severity:** minor

64. **`f-string` used without any expression** (`PTC-W0027`)
    **File:** `src/evaluation/evaluator.py`
    **Line:** 427
    ```python
    # Check allowed patterns
            if constraints.allowed_patterns:
                if not any(re.search(pattern, output_str) for pattern in constraints.allowed_patterns):
                    errors.append(f"Output does not contain any allowed pattern")
    
            return errors
    ```
    **Category:** Anti-pattern
    **Severity:** major

65. **Consider merging collapsible if statements** (`PTC-W0048`)
    **File:** `src/evaluation/evaluator.py`
    **Line:** 408
    ```python
    if len(output_str) > constraints.max_length:
                    errors.append(f"Output exceeds max length of {constraints.max_length}")
    
            if constraints.min_length is not None:
                if len(output_str) < constraints.min_length:
                    errors.append(f"Output below min length of {constraints.min_length}")
    ```
    **Category:** Anti-pattern
    **Severity:** major

66. **Consider merging collapsible if statements** (`PTC-W0048`)
    **File:** `src/evaluation/evaluator.py`
    **Line:** 404
    ```python
    # Check length constraints
            output_str = str(output)
            if constraints.max_length is not None:
                if len(output_str) > constraints.max_length:
                    errors.append(f"Output exceeds max length of {constraints.max_length}")
    ```
    **Category:** Anti-pattern
    **Severity:** major

67. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/evaluation/evaluator.py`
    **Line:** 391
    ```python
    validation_errors=[str(e)],
                )
    
        def _validate_output(
            self,
            output: Any,
            constraints: Optional[OutputConstraints],
    ```
    **Category:** Performance
    **Severity:** major

68. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/evaluation/evaluator.py`
    **Line:** 471
    ```python
    return [e for e in evaluations if e.agent_id == agent_id]
            return evaluations
    
        def compare_agents(
            self,
            agent_evaluations: Dict[str, EvaluationResult],
        ) -> Dict[str, QualityMetrics]:
    ```
    **Category:** Performance
    **Severity:** major

69. **Unused import logging** (`PY-W2000`)
    **File:** `src/evaluation/evaluator.py`
    **Line:** 9
    ```python
    """
    
    import asyncio
    import logging
    import time
    from datetime import datetime, timezone
    from typing import Any, Dict, List, Optional, Callable, Type
    ```
    **Category:** Anti-pattern
    **Severity:** major

70. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/evaluation/evaluator.py`
    **Line:** 431
    ```python
    return errors
    
        def _calculate_metrics(self, test_results: List[TestResult]) -> QualityMetrics:
            """Calculate quality metrics from test results."""
            if not test_results:
                return QualityMetrics()
    ```
    **Category:** Performance
    **Severity:** major

71. **Consider merging collapsible if statements** (`PTC-W0048`)
    **File:** `src/evaluation/evaluator.py`
    **Line:** 425
    ```python
    errors.append(f"Output contains forbidden pattern: {pattern}")
    
            # Check allowed patterns
            if constraints.allowed_patterns:
                if not any(re.search(pattern, output_str) for pattern in constraints.allowed_patterns):
                    errors.append(f"Output does not contain any allowed pattern")
    ```
    **Category:** Anti-pattern
    **Severity:** major

72. **Attribute '_message_handlers' defined outside __init__** (`PYL-W0201`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 277
    ```python
    def _register_handlers(self) -> None:
            """Register message handlers."""
            self._message_handlers = {
                "report_conflict": self._handle_report_conflict,
                "request_arbitration": self._handle_request_arbitration,
                "mediate_dispute": self._handle_mediate_dispute,
    ```
    **Category:** Anti-pattern
    **Severity:** minor

73. **Access to a protected member _validated_patterns of a client class** (`PYL-W0212`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 1806
    ```python
    status = {
                "agent_id": self.agent_id,
                "collective_learning": {
                    "patterns_extracted": len(self.pattern_extractor._validated_patterns) if self.pattern_extractor else 0,
                    "message_cache_size": len(self.pattern_extractor._message_cache) if self.pattern_extractor else 0,
                },
                "consensus": {
    ```
    **Category:** Bug risk
    **Severity:** minor

74. **Access to a protected member _message_cache of a client class** (`PYL-W0212`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 1807
    ```python
    "agent_id": self.agent_id,
                "collective_learning": {
                    "patterns_extracted": len(self.pattern_extractor._validated_patterns) if self.pattern_extractor else 0,
                    "message_cache_size": len(self.pattern_extractor._message_cache) if self.pattern_extractor else 0,
                },
                "consensus": {
                    "active_deliberations": len(self._active_deliberations),
    ```
    **Category:** Bug risk
    **Severity:** minor

75. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 1260
    ```python
    conflict.proposed_resolutions.append(proposal)
            return {"status": "round_robin_proposed", "strategy": "round_robin"}
        
        async def _resolve_resource_pooling(self, conflict: Conflict) -> Dict[str, Any]:
            """Resource pooling resolution."""
            proposal = {
                "strategy": "resource_pooling",
    ```
    **Category:** Performance
    **Severity:** major

76. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 1192
    ```python
    return None
        
        async def _resolve_negotiation(self, conflict: Conflict) -> Dict[str, Any]:
            """Negotiation-based resolution."""
            # Generate compromise proposal
            proposal = {
    ```
    **Category:** Performance
    **Severity:** major

77. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 1203
    ```python
    conflict.proposed_resolutions.append(proposal)
            return {"status": "proposal_generated", "strategy": "negotiation"}
        
        async def _resolve_mediation(self, conflict: Conflict) -> Dict[str, Any]:
            """Mediation-based resolution."""
            proposal = {
                "strategy": "mediation",
    ```
    **Category:** Performance
    **Severity:** major

78. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 1353
    ```python
    return mediation_result
        
        async def _resolve_resource_contention(
            self,
            resource: Optional[str],
            competing_agents: List[str],
    ```
    **Category:** Performance
    **Severity:** major

79. **Unused variable 'outcome'** (`PYL-W0612`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 935
    ```python
    content = message.content
                other_agent = content.get("other_agent")
                interaction_type = content.get("interaction_type", "neutral")
                outcome = content.get("outcome", "neutral")
                trust_delta = content.get("trust_delta", 0.0)
                
                if not other_agent:
    ```
    **Category:** Anti-pattern
    **Severity:** major

80. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 1296
    ```python
    conflict.proposed_resolutions.append(proposal)
            return {"status": "compromise_proposed", "strategy": "compromise"}
        
        async def _resolve_consensus_vote(self, conflict: Conflict) -> Dict[str, Any]:
            """Consensus vote resolution."""
            proposal = {
                "strategy": "consensus_vote",
    ```
    **Category:** Performance
    **Severity:** major

81. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 1250
    ```python
    conflict.proposed_resolutions.append(proposal)
            return {"status": "priority_check_required", "strategy": "priority_based"}
        
        async def _resolve_round_robin(self, conflict: Conflict) -> Dict[str, Any]:
            """Round-robin resource allocation."""
            proposal = {
                "strategy": "round_robin",
    ```
    **Category:** Performance
    **Severity:** major

82. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 1286
    ```python
    self._stats["resolutions_escalated"] += 1
            return {"status": "escalated", "strategy": "escalation", "escalated_to": "supervisor"}
        
        async def _resolve_compromise(self, conflict: Conflict) -> Dict[str, Any]:
            """Compromise-based resolution."""
            proposal = {
                "strategy": "compromise",
    ```
    **Category:** Performance
    **Severity:** major

83. **Unused variable 'interaction_type'** (`PYL-W0612`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 1074
    ```python
    try:
                content = message.content
                other_agent = content.get("other_agent")
                interaction_type = content.get("interaction_type", "communication")
                outcome = content.get("outcome", "neutral")
                success = content.get("success", True)
    ```
    **Category:** Anti-pattern
    **Severity:** major

84. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 1121
    ```python
    logger.error("Error registering interaction", error=str(e), exc_info=True)
                await self._send_error(message, "Interaction registration failed", str(e))
        
        def _create_conflict_id(self) -> str:
            """Generate unique conflict ID."""
            import hashlib
            timestamp = datetime.now(timezone.utc).timestamp()
    ```
    **Category:** Performance
    **Severity:** major

85. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 1239
    ```python
    return {"status": "arbitration_complete", "decision": decision}
        
        async def _resolve_priority_based(self, conflict: Conflict) -> Dict[str, Any]:
            """Priority-based resolution."""
            # Assign based on priority (would need priority data from context)
            proposal = {
    ```
    **Category:** Performance
    **Severity:** major

86. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 1400
    ```python
    ],
            }
        
        async def _resolve_generic_contention(
            self,
            contention_type: str,
            competing_agents: List[str],
    ```
    **Category:** Performance
    **Severity:** major

87. **Unused variable 'validated'** (`PYL-W0612`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 538
    ```python
    priority_override = content.get("priority_override", {})
                
                # Validate
                validated = validate_message({
                    "sender_id": message.sender_id,
                    "message_type": "resolve_contention",
                    "content": content,
    ```
    **Category:** Anti-pattern
    **Severity:** major

88. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 1381
    ```python
    "suggestion": "Implement priority-based allocation for better fairness",
            }
        
        async def _resolve_task_contention(
            self,
            competing_agents: List[str],
            priority_override: Dict[str, int],
    ```
    **Category:** Performance
    **Severity:** major

89. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 1270
    ```python
    conflict.proposed_resolutions.append(proposal)
            return {"status": "pooling_proposed", "strategy": "resource_pooling"}
        
        async def _resolve_task_reassignment(self, conflict: Conflict) -> Dict[str, Any]:
            """Task reassignment resolution."""
            proposal = {
                "strategy": "task_reassignment",
    ```
    **Category:** Performance
    **Severity:** major

90. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/actors/arbiter.py`
    **Line:** 1413
    ```python
    "next_step": "Schedule mediation session",
            }
        
        def _get_next_steps(self, conflict: Conflict) -> List[str]:
            """Get recommended next steps for a conflict."""
            steps = []
    ```
    **Category:** Performance
    **Severity:** major

91. **Overlapping exceptions (Exception is an ancestor class of ImportError)** (`PYL-W0714`)
    **File:** `src/heretek_swarm/actors/base.py`
    **Line:** 1415
    ```python
    supervisor = get_supervisor()
                if supervisor and hasattr(supervisor, 'actors'):
                    return supervisor.actors
            except (ImportError, Exception):
                pass
            return None
    ```
    **Category:** Anti-pattern
    **Severity:** major

92. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/actors/base.py`
    **Line:** 1401
    ```python
    "confidence": 0.6
            }
    
        def _get_actor_registry(self) -> Optional[Dict[str, "AgentActor"]]:
            """
            Get global actor registry from supervisor.
    ```
    **Category:** Performance
    **Severity:** major

93. **Unused variable 'reg_actor_id'** (`PYL-W0612`)
    **File:** `src/heretek_swarm/actors/base.py`
    **Line:** 467
    ```python
    try:
                    # Find actors subscribed to this topic
                    delivered = False
                    for reg_actor_id, reg_actor in actor_registry.items():
                        if topic in getattr(reg_actor, 'topics', []):
                            await reg_actor.put_message(message)
                            delivered = True
    ```
    **Category:** Anti-pattern
    **Severity:** major

94. **Redefining name 'asyncio' from outer scope** (`PYL-W0621`)
    **File:** `src/heretek_swarm/actors/base.py`
    **Line:** 589
    ```python
    Raises:
                asyncio.TimeoutError: If no reply received within timeout
            """
            import asyncio
            
            # Generate unique correlation ID for this request
            correlation_id = str(uuid.uuid4())
    ```
    **Category:** Anti-pattern
    **Severity:** major

95. **Reimport 'asyncio' (imported line 12)** (`PYL-W0404`)
    **File:** `src/heretek_swarm/actors/base.py`
    **Line:** 589
    ```python
    Raises:
                asyncio.TimeoutError: If no reply received within timeout
            """
            import asyncio
            
            # Generate unique correlation ID for this request
            correlation_id = str(uuid.uuid4())
    ```
    **Category:** Bug risk
    **Severity:** major

96. **Access to a protected member _validated_patterns of a client class** (`PYL-W0212`)
    **File:** `src/heretek_swarm/actors/catalyst.py`
    **Line:** 1106
    ```python
    return {
                "agent_id": self.agent_id,
                "collective_learning": {
                    "patterns_extracted": len(self.pattern_extractor._validated_patterns) if self.pattern_extractor else 0,
                    "message_cache_size": len(self.pattern_extractor._message_cache) if self.pattern_extractor else 0,
                },
                "consensus": {
    ```
    **Category:** Bug risk
    **Severity:** minor

97. **Access to a protected member _message_cache of a client class** (`PYL-W0212`)
    **File:** `src/heretek_swarm/actors/catalyst.py`
    **Line:** 1107
    ```python
    "agent_id": self.agent_id,
                "collective_learning": {
                    "patterns_extracted": len(self.pattern_extractor._validated_patterns) if self.pattern_extractor else 0,
                    "message_cache_size": len(self.pattern_extractor._message_cache) if self.pattern_extractor else 0,
                },
                "consensus": {
                    "active_deliberations": len(self._active_deliberations),
    ```
    **Category:** Bug risk
    **Severity:** minor

98. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/actors/catalyst.py`
    **Line:** 1134
    ```python
    ),
            )
    
        def get_capabilities(self) -> List[str]:
            """Return list of capabilities this agent provides."""
            return [
                "change_management",
    ```
    **Category:** Performance
    **Severity:** major

99. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/actors/catalyst.py`
    **Line:** 842
    ```python
    oldest = sorted(self._notifications.keys())[0]
                del self._notifications[oldest]
    
        def _calculate_risk_score(self, change: ChangeRequest) -> float:
            """Calculate risk score for a change (0.0-1.0)."""
            base_scores = {
                ImpactLevel.LOW: 0.1,
    ```
    **Category:** Performance
    **Severity:** major

100. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
     **File:** `src/heretek_swarm/actors/catalyst.py`
     **Line:** 864
     ```python
     return min(score, 1.0)
     
         def _generate_recommendations(self, change: ChangeRequest) -> List[str]:
             """Generate recommendations for a change."""
             recommendations = []
     ```
     **Category:** Performance
     **Severity:** major

*...and 3167 more occurrences. [See full list on DeepSource](https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/6ce83273-62c5-44e0-9536-f18b5e832267/).*### Secrets
**Status:** Failure
**Findings:** 34 new issues

1. **Audit: Hardcoded credential "os.getenv(\"OPENAI_API_KEY\")" found in source code** (`SCT-A000`)
   **File:** `docs/DEVELOPMENT_PLAN.md`
   **Line:** 1789
   ```markdown
   config = Mem0Config(
           qdrant_host="localhost",
           qdrant_port=6333,
           openai_api_key=os.getenv("OPENAI_API_KEY")
       )
       backend = Mem0Backend(config)
       await backend.initialize()
   ```
   **Category:** Secrets
   **Severity:** minor

2. **Audit: Hardcoded credential "get_api_key()" found in source code** (`SCT-A000`)
   **File:** `docs/DEVELOPMENT_PLAN.md`
   **Line:** 1745
   ```markdown
   creds: HTTPAuthorizationCredentials = Security(security)
   ) -> str:
       """Verify Bearer token authentication."""
       expected_key = get_api_key()
       
       if creds.credentials != expected_key:
           raise HTTPException(
   ```
   **Category:** Secrets
   **Severity:** minor

3. **Audit: Hardcoded credential "htsk_your_secure_key_here" found in source code** (`SCT-A000`)
   **File:** `docs/DEVELOPMENT_PLAN.md`
   **Line:** 1759
   ```markdown
   **Environment Setup:**
   ```bash
   # .env
   HERETEK_API_KEY=
   htsk_your_secure_key_here```
   
   **Success Criteria:**
   ```
   **Category:** Secrets
   **Severity:** minor

4. **Audit: Hardcoded credential "f\"rate_limit:hourly:{tier}:{client_id}\"" found in source code** (`SCT-A000`)
   **File:** `docs/EXPANSION_ROADMAP.md`
   **Line:** 3405
   ```markdown
   )
           
           # Step 3: Hourly limit check (sliding window)
           hourly_key = f"rate_limit:hourly:{tier}:{client_id}"
           hourly_count = await self.redis.get(hourly_key)
           
           if hourly_count and int(hourly_count) >= config.requests_per_hour:
   ```
   **Category:** Secrets
   **Severity:** minor

5. **Audit: Hardcoded credential "f\"rate_limit:bucket:{tier}:{client_id}\"" found in source code** (`SCT-A000`)
   **File:** `docs/EXPANSION_ROADMAP.md`
   **Line:** 3388
   ```markdown
   )
           
           # Step 2: Token Bucket Rate Limiting
           bucket_key = f"rate_limit:bucket:{tier}:{client_id}"
           bucket = TokenBucket(self.redis, bucket_key, config)
           
           allowed, remaining = await bucket.acquire()
   ```
   **Category:** Secrets
   **Severity:** minor

6. **Audit: Hardcoded credential "heretek-swarm-secret-key" found in source code** (`SCT-A000`)
   **File:** `docs/proposal/AUTONOMOUS_WORKFLOW_DESIGN-MINIMAX.md`
   **Line:** 1129
   ```markdown
   ANTHROPIC_API_KEY: sk-ant-...
   
   # Auth
   JWT_SECRET: heretek-swarm-secret-keyNone
   API_KEY: heretek-swarm-api-key
   
   # Feature Flags
   ```
   **Category:** Secrets
   **Severity:** minor

7. **Audit: Hardcoded credential "heretek-swarm-api-key" found in source code** (`SCT-A000`)
   **File:** `docs/proposal/AUTONOMOUS_WORKFLOW_DESIGN-MINIMAX.md`
   **Line:** 1130
   ```markdown
   # Auth
   JWT_SECRET: heretek-swarm-secret-key
   API_KEY: heretek-swarm-api-keyNone
   
   # Feature Flags
   CONSCIOUSNESS_ENABLED: true
   ```
   **Category:** Secrets
   **Severity:** minor

8. **Audit: Hardcoded credential "os.environ.get(\"API_KEY\")" found in source code** (`SCT-A000`)
   **File:** `docs/REMEDIATION_GUIDE.md`
   **Line:** 779
   ```markdown
   # ✅ ALLOWED - Environment variables
   import os
   API_KEY = os.environ.get("API_KEY")
   DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD")
   ```
   ```
   **Category:** Secrets
   **Severity:** minor

9. **Audit: Hardcoded credential "os.environ.get(\"DATABASE_PASSWORD\")" found in source code** (`SCT-A000`)
   **File:** `docs/REMEDIATION_GUIDE.md`
   **Line:** 780
   ```markdown
   # ✅ ALLOWED - Environment variables
   import os
   API_KEY = os.environ.get("API_KEY")
   DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD")
   ```
   
   #### 5.1.6 No TODO/FIXME/XXX/HACK Comments
   ```
   **Category:** Secrets
   **Severity:** minor

10. **Hardcoded credential "${GRAFANA_ADMIN_PASSWORD:-admin123}" found in source code** (`SCT-1000`)
    **File:** `k8s/grafana-deployment.yaml`
    **Line:** 99
    ```yaml
    namespace: heretek-swarm
    type: Opaque
    stringData:
      admin-password: "${GRAFANA_ADMIN_PASSWORD:-admin123}"None
    
    ---
    apiVersion: v1
    ```
    **Category:** Secrets
    **Severity:** critical

11. **Audit: Hardcoded credential "your-qdrant-key" found in source code** (`SCT-A000`)
    **File:** `k8s/README.md`
    **Line:** 22
    ```markdown
    export POSTGRES_PASSWORD=your-secure-password
    export OPENAI_API_KEY=your-openai-key
    export ANTHROPIC_API_KEY=your-anthropic-key
    export QDRANT_API_KEY=
    your-qdrant-keyexport GRAFANA_ADMIN_PASSWORD=your-grafana-password
    export JWT_SECRET=your-jwt-secret
    export API_KEY=your-api-key
    ```
    **Category:** Secrets
    **Severity:** minor

12. **Audit: Hardcoded credential "your-openai-key" found in source code** (`SCT-A000`)
    **File:** `k8s/README.md`
    **Line:** 20
    ```markdown
    ```bash
    export POSTGRES_PASSWORD=your-secure-password
    export OPENAI_API_KEY=
    your-openai-keyexport ANTHROPIC_API_KEY=your-anthropic-key
    export QDRANT_API_KEY=your-qdrant-key
    export GRAFANA_ADMIN_PASSWORD=your-grafana-password
    ```
    **Category:** Secrets
    **Severity:** minor

13. **Audit: Hardcoded credential "your-anthropic-key" found in source code** (`SCT-A000`)
    **File:** `k8s/README.md`
    **Line:** 21
    ```markdown
    ```bash
    export POSTGRES_PASSWORD=your-secure-password
    export OPENAI_API_KEY=your-openai-key
    export ANTHROPIC_API_KEY=
    your-anthropic-keyexport QDRANT_API_KEY=your-qdrant-key
    export GRAFANA_ADMIN_PASSWORD=your-grafana-password
    export JWT_SECRET=your-jwt-secret
    ```
    **Category:** Secrets
    **Severity:** minor

14. **Audit: Hardcoded credential "your-api-key" found in source code** (`SCT-A000`)
    **File:** `k8s/README.md`
    **Line:** 25
    ```markdown
    export QDRANT_API_KEY=your-qdrant-key
    export GRAFANA_ADMIN_PASSWORD=your-grafana-password
    export JWT_SECRET=your-jwt-secret
    export API_KEY=
    your-api-key```
    
    ### 2. Deploy Using Script
    ```
    **Category:** Secrets
    **Severity:** minor

15. **Audit: Hardcoded credential "your-secure-password" found in source code** (`SCT-A000`)
    **File:** `k8s/README.md`
    **Line:** 19
    ```markdown
    Create a `.env` file or export required variables:
    
    ```bash
    export POSTGRES_PASSWORD=
    your-secure-passwordexport OPENAI_API_KEY=your-openai-key
    export ANTHROPIC_API_KEY=your-anthropic-key
    export QDRANT_API_KEY=your-qdrant-key
    ```
    **Category:** Secrets
    **Severity:** minor

16. **Audit: Hardcoded credential "your-grafana-password" found in source code** (`SCT-A000`)
    **File:** `k8s/README.md`
    **Line:** 23
    ```markdown
    export OPENAI_API_KEY=your-openai-key
    export ANTHROPIC_API_KEY=your-anthropic-key
    export QDRANT_API_KEY=your-qdrant-key
    export GRAFANA_ADMIN_PASSWORD=
    your-grafana-passwordexport JWT_SECRET=your-jwt-secret
    export API_KEY=your-api-key
    ```
    ```
    **Category:** Secrets
    **Severity:** minor

17. **Audit: Hardcoded credential "your-jwt-secret" found in source code** (`SCT-A000`)
    **File:** `k8s/README.md`
    **Line:** 24
    ```markdown
    export ANTHROPIC_API_KEY=your-anthropic-key
    export QDRANT_API_KEY=your-qdrant-key
    export GRAFANA_ADMIN_PASSWORD=your-grafana-password
    export JWT_SECRET=
    your-jwt-secretexport API_KEY=your-api-key
    ```
    ```
    **Category:** Secrets
    **Severity:** minor

18. **Audit: Hardcoded credential "${TELEGRAM_BOT_TOKEN:-}" found in source code** (`SCT-A000`)
    **File:** `k8s/secrets.yaml`
    **Line:** 36
    ```yaml
    type: Opaque
    stringData:
      discord-bot-token: "${DISCORD_BOT_TOKEN:-}"
      telegram-bot-token: "${TELEGRAM_BOT_TOKEN:-}"None
      slack-bot-token: "${SLACK_BOT_TOKEN:-}"
      slack-signing-secret: "${SLACK_SIGNING_SECRET:-}"
    ---
    ```
    **Category:** Secrets
    **Severity:** minor

19. **Audit: Hardcoded credential "${SLACK_BOT_TOKEN:-}" found in source code** (`SCT-A000`)
    **File:** `k8s/secrets.yaml`
    **Line:** 37
    ```yaml
    stringData:
      discord-bot-token: "${DISCORD_BOT_TOKEN:-}"
      telegram-bot-token: "${TELEGRAM_BOT_TOKEN:-}"
      slack-bot-token: "${SLACK_BOT_TOKEN:-}"None
      slack-signing-secret: "${SLACK_SIGNING_SECRET:-}"
    ---
    # LiteLLM Secret
    ```
    **Category:** Secrets
    **Severity:** minor

20. **Audit: Hardcoded credential "${SLACK_SIGNING_SECRET:-}" found in source code** (`SCT-A000`)
    **File:** `k8s/secrets.yaml`
    **Line:** 38
    ```yaml
    discord-bot-token: "${DISCORD_BOT_TOKEN:-}"
      telegram-bot-token: "${TELEGRAM_BOT_TOKEN:-}"
      slack-bot-token: "${SLACK_BOT_TOKEN:-}"
      slack-signing-secret: "${SLACK_SIGNING_SECRET:-}"None
    ---
    # LiteLLM Secret
    apiVersion: v1
    ```
    **Category:** Secrets
    **Severity:** minor

21. **Audit: Hardcoded credential "${DISCORD_BOT_TOKEN:-}" found in source code** (`SCT-A000`)
    **File:** `k8s/secrets.yaml`
    **Line:** 35
    ```yaml
    namespace: heretek-swarm
    type: Opaque
    stringData:
      discord-bot-token: "${DISCORD_BOT_TOKEN:-}"None
      telegram-bot-token: "${TELEGRAM_BOT_TOKEN:-}"
      slack-bot-token: "${SLACK_BOT_TOKEN:-}"
      slack-signing-secret: "${SLACK_SIGNING_SECRET:-}"
    ```
    **Category:** Secrets
    **Severity:** minor

22. **Audit: Hardcoded credential "api_key," found in source code** (`SCT-A000`)
    **File:** `test_results_full.txt`
    **Line:** 4815
    ```
    return embedder_instance(base_config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/mem0/embeddings/openai.py:35: in __init__
        self.client = OpenAI(api_key=api_key, base_url=base_url)                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/openai/_client.py:139: in __init__
        raise OpenAIError(
    ```
    **Category:** Secrets
    **Severity:** minor

23. **Audit: Hardcoded credential "api_key," found in source code** (`SCT-A000`)
    **File:** `test_results_full.txt`
    **Line:** 4839
    ```
    return embedder_instance(base_config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/mem0/embeddings/openai.py:35: in __init__
        self.client = OpenAI(api_key=api_key, base_url=base_url)                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/openai/_client.py:139: in __init__
        raise OpenAIError(
    ```
    **Category:** Secrets
    **Severity:** minor

24. **Audit: Hardcoded credential "api_key," found in source code** (`SCT-A000`)
    **File:** `test_results_full.txt`
    **Line:** 4515
    ```
    return embedder_instance(base_config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/mem0/embeddings/openai.py:35: in __init__
        self.client = OpenAI(api_key=api_key, base_url=base_url)                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/openai/_client.py:139: in __init__
        raise OpenAIError(
    ```
    **Category:** Secrets
    **Severity:** minor

25. **Audit: Hardcoded credential "api_key," found in source code** (`SCT-A000`)
    **File:** `test_results_full.txt`
    **Line:** 4491
    ```
    return embedder_instance(base_config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/mem0/embeddings/openai.py:35: in __init__
        self.client = OpenAI(api_key=api_key, base_url=base_url)                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/openai/_client.py:139: in __init__
        raise OpenAIError(
    ```
    **Category:** Secrets
    **Severity:** minor

26. **Audit: Hardcoded credential "api_key," found in source code** (`SCT-A000`)
    **File:** `test_results_full.txt`
    **Line:** 4767
    ```
    return embedder_instance(base_config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/mem0/embeddings/openai.py:35: in __init__
        self.client = OpenAI(api_key=api_key, base_url=base_url)                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/openai/_client.py:139: in __init__
        raise OpenAIError(
    ```
    **Category:** Secrets
    **Severity:** minor

27. **Audit: Hardcoded credential "api_key," found in source code** (`SCT-A000`)
    **File:** `test_results_full.txt`
    **Line:** 4791
    ```
    return embedder_instance(base_config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/mem0/embeddings/openai.py:35: in __init__
        self.client = OpenAI(api_key=api_key, base_url=base_url)                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/openai/_client.py:139: in __init__
        raise OpenAIError(
    ```
    **Category:** Secrets
    **Severity:** minor

28. **Audit: Hardcoded credential "api_key," found in source code** (`SCT-A000`)
    **File:** `test_results_full.txt`
    **Line:** 4539
    ```
    return embedder_instance(base_config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/mem0/embeddings/openai.py:35: in __init__
        self.client = OpenAI(api_key=api_key, base_url=base_url)                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/openai/_client.py:139: in __init__
        raise OpenAIError(
    ```
    **Category:** Secrets
    **Severity:** minor

29. **Audit: Hardcoded credential "api_key," found in source code** (`SCT-A000`)
    **File:** `test_results_full.txt`
    **Line:** 4863
    ```
    return embedder_instance(base_config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/mem0/embeddings/openai.py:35: in __init__
        self.client = OpenAI(api_key=api_key, base_url=base_url)                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/openai/_client.py:139: in __init__
        raise OpenAIError(
    ```
    **Category:** Secrets
    **Severity:** minor

30. **Audit: Hardcoded credential "api_key," found in source code** (`SCT-A000`)
    **File:** `test_results_full.txt`
    **Line:** 4419
    ```
    return embedder_instance(base_config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/mem0/embeddings/openai.py:35: in __init__
        self.client = OpenAI(api_key=api_key, base_url=base_url)                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/openai/_client.py:139: in __init__
        raise OpenAIError(
    ```
    **Category:** Secrets
    **Severity:** minor

31. **Audit: Hardcoded credential "api_key," found in source code** (`SCT-A000`)
    **File:** `test_results_full.txt`
    **Line:** 4371
    ```
    return embedder_instance(base_config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/mem0/embeddings/openai.py:35: in __init__
        self.client = OpenAI(api_key=api_key, base_url=base_url)                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/openai/_client.py:139: in __init__
        raise OpenAIError(
    ```
    **Category:** Secrets
    **Severity:** minor

32. **Audit: Hardcoded credential "api_key," found in source code** (`SCT-A000`)
    **File:** `test_results_full.txt`
    **Line:** 4395
    ```
    return embedder_instance(base_config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/mem0/embeddings/openai.py:35: in __init__
        self.client = OpenAI(api_key=api_key, base_url=base_url)                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/openai/_client.py:139: in __init__
        raise OpenAIError(
    ```
    **Category:** Secrets
    **Severity:** minor

33. **Audit: Hardcoded credential "api_key," found in source code** (`SCT-A000`)
    **File:** `test_results_full.txt`
    **Line:** 4467
    ```
    return embedder_instance(base_config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/mem0/embeddings/openai.py:35: in __init__
        self.client = OpenAI(api_key=api_key, base_url=base_url)                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/openai/_client.py:139: in __init__
        raise OpenAIError(
    ```
    **Category:** Secrets
    **Severity:** minor

34. **Audit: Hardcoded credential "api_key," found in source code** (`SCT-A000`)
    **File:** `test_results_full.txt`
    **Line:** 4443
    ```
    return embedder_instance(base_config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/mem0/embeddings/openai.py:35: in __init__
        self.client = OpenAI(api_key=api_key, base_url=base_url)                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    /usr/local/lib/python3.13/dist-packages/openai/_client.py:139: in __init__
        raise OpenAIError(
    ```
    **Category:** Secrets
    **Severity:** minor
### JavaScript
**Status:** Failure
**Findings:** 505 new issues

1. **Parsing error: 'import' and 'export' may appear only with 'sourceType: module'** (`JS-0833`)
   **File:** `dashboard/frontend/postcss.config.js`
   **Line:** 1
   ```javascript
   export default {
     plugins: {
       tailwindcss: {},
       autoprefixer: {},
   ```
   **Category:** Bug risk
   **Severity:** minor

2. **Type number trivially inferred from a number literal, remove type annotation** (`JS-0331`)
   **File:** `dashboard/frontend/src/api/agents.ts`
   **Line:** 302
   ```typescript
   */
   export const getAgentLogs = async (
     instanceId: string,
     limit: number = 100
   ): Promise<AgentLogsResponse> => {
     const response = await api.get(`/api/agents/${instanceId}/logs`, {
       params: { limit },
   ```
   **Category:** Anti-pattern
   **Severity:** major

3. **use `Boolean(API_URL)` instead** (`JS-0066`)
   **File:** `dashboard/frontend/src/api/client.ts`
   **Line:** 190
   ```typescript
   // Check if client is configured
     isConfigured: () => {
       return !!API_URL || typeof window !== 'undefined';
     },
   };
   ```
   **Category:** Anti-pattern
   **Severity:** minor

4. **Found `async` function without any `await` expressions** (`JS-0116`)
   **File:** `dashboard/frontend/src/api/client.ts`
   **Line:** 174-176
   ```typescript
   },
   
     // PUT request
     put: async <T>(url: string, data?: unknown, config?: { headers?: Record<string, string> }) => {
       return withRetry(() => apiClient.put<T>(url, data, config));
     },
   
     // PATCH request
     patch: async <T>(url: string, data?: unknown, config?: { headers?: Record<string, string> }) => {
   ```
   **Category:** Bug risk
   **Severity:** minor

5. **Found `async` function without any `await` expressions** (`JS-0116`)
   **File:** `dashboard/frontend/src/api/client.ts`
   **Line:** 75-126
   ```typescript
   // Response interceptor - Handle errors
   apiClient.interceptors.response.use(
     (response: AxiosResponse) => response,
     async (error: AxiosError) => {
       const status = error.response?.status;
       const data = error.response?.data as { message?: string } | undefined;
       const message = data?.message || error.message || 'An unexpected error occurred';
       let errorCode: ApiErrorCode;
       let errorMessage: string;
       switch (status) {
         case 401
   :        errorCode = ApiErrorCode.UNAUTHORIZED;
           errorMessage = 'Authentication failed. Please check your API key.';
           // Optionally clear invalid token
           localStorage.removeItem('api_key');
           break;
         case 403
   :        errorCode = ApiErrorCode.FORBIDDEN;
           errorMessage = 'Access denied. You do not have permission for this action.';
           break;
         case 404
   :        errorCode = ApiErrorCode.NOT_FOUND;
           errorMessage = 'The requested resource was not found.';
           break;
         case 500
   :      case 502
   :      case 503
   :      case 504
   :        errorCode = ApiErrorCode.SERVER_ERROR;
           errorMessage = 'Server error. Please try again later.';
           break;
         default:
           if (error.code === 'ECONNABORTED') {
             errorCode = ApiErrorCode.TIMEOUT;
             errorMessage = 'Request timed out. Please try again.';
           } else if (error.code === 'ERR_NETWORK') {
             errorCode = ApiErrorCode.NETWORK_ERROR;
             errorMessage = 'Network error. Please check your connection.';
           } else {
             errorCode = ApiErrorCode.UNKNOWN;
             errorMessage = message;
           }
       }
       // Show toast notification for errors
       if (toastInstance) {
         toastInstance.error('API Error', errorMessage);
       } else {
         console.error('API Error:', errorMessage);
       }
       return Promise.reject(new ApiError(errorMessage, errorCode, status, data));
     }
   );
   
   // Retry logic wrapper
   ```
   **Category:** Bug risk
   **Severity:** minor

6. **Found `async` function without any `await` expressions** (`JS-0116`)
   **File:** `dashboard/frontend/src/api/client.ts`
   **Line:** 169-171
   ```typescript
   },
   
     // POST request
     post: async <T>(url: string, data?: unknown, config?: { headers?: Record<string, string> }) => {
       return withRetry(() => apiClient.post<T>(url, data, config));
     },
   
     // PUT request
     put: async <T>(url: string, data?: unknown, config?: { headers?: Record<string, string> }) => {
   ```
   **Category:** Bug risk
   **Severity:** minor

7. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
   **File:** `dashboard/frontend/src/api/client.ts`
   **Line:** 130-159
   ```typescript
   );
   
   // Retry logic wrapper
   export async function withRetry<T>(
     fn: () => Promise<T>,
     retries = MAX_RETRIES,
     delay = RETRY_DELAY
   ): Promise<T> {
     try {
       return await fn();
     } catch (error) {
       if (retries <= 0) {
         throw error;
       }
       const apiError = error as ApiError;
           // Don't retry for client errors (4xx except 429)
       if (apiError instanceof ApiError &&
            apiError.status &&
            apiError.status >= 400 &&
            apiError.status < 500 &&
            apiError.status !== 429) {
         throw error;
       }
       // Wait before retrying
       await new Promise((resolve) => setTimeout(resolve, delay));
           // Retry with exponential backoff
       return withRetry(fn, retries - 1, delay * 2);
     }
   }
   
   // Helper methods
   export const api = {
   ```
   **Category:** Anti-pattern
   **Severity:** minor

8. **Function has a cyclomatic complexity of 13 with "medium" risk** (`JS-R1005`)
   **File:** `dashboard/frontend/src/api/client.ts`
   **Line:** 75
   ```typescript
   // Response interceptor - Handle errors
   apiClient.interceptors.response.use(
     (response: AxiosResponse) => response,
     async (error: AxiosError) => {
       const status = error.response?.status;
       const data = error.response?.data as { message?: string } | undefined;
       const message = data?.message || error.message || 'An unexpected error occurred';
   ```
   **Category:** Anti-pattern
   **Severity:** minor

9. **`withRetry` has a cyclomatic complexity of 8 with "medium" risk** (`JS-R1005`)
   **File:** `dashboard/frontend/src/api/client.ts`
   **Line:** 130
   ```typescript
   );
   
   // Retry logic wrapper
   export async function withRetry<T>(
     fn: () => Promise<T>,
     retries = MAX_RETRIES,
     delay = RETRY_DELAY
   ```
   **Category:** Anti-pattern
   **Severity:** minor

10. **Found `async` function without any `await` expressions** (`JS-0116`)
    **File:** `dashboard/frontend/src/api/client.ts`
    **Line:** 179-181
    ```typescript
    },
    
      // PATCH request
      patch: async <T>(url: string, data?: unknown, config?: { headers?: Record<string, string> }) => {
        return withRetry(() => apiClient.patch<T>(url, data, config));
      },
    
      // DELETE request
      delete: async <T>(url: string, config?: { headers?: Record<string, string> }) => {
    ```
    **Category:** Bug risk
    **Severity:** minor

11. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/api/client.ts`
    **Line:** 22-24
    ```typescript
    // Toast instance holder (for use outside React components)
    let toastInstance: { error: (title: string, message?: string) => void } | null = null;
    
    export function setToastInstance(toast: { error: (title: string, message?: string) => void }) {
      toastInstance = toast;
    }
    
    // Error types
    export enum ApiErrorCode {
    ```
    **Category:** Anti-pattern
    **Severity:** minor

12. **Found `async` function without any `await` expressions** (`JS-0116`)
    **File:** `dashboard/frontend/src/api/client.ts`
    **Line:** 164-166
    ```typescript
    // Helper methods
    export const api = {
      // GET request
      get: async <T>(url: string, config?: { headers?: Record<string, string> }) => {
        return withRetry(() => apiClient.get<T>(url, config));
      },
    
      // POST request
      post: async <T>(url: string, data?: unknown, config?: { headers?: Record<string, string> }) => {
    ```
    **Category:** Bug risk
    **Severity:** minor

13. **Found `async` function without any `await` expressions** (`JS-0116`)
    **File:** `dashboard/frontend/src/api/client.ts`
    **Line:** 184-186
    ```typescript
    },
    
      // DELETE request
      delete: async <T>(url: string, config?: { headers?: Record<string, string> }) => {
        return withRetry(() => apiClient.delete<T>(url, config));
      },
    
      // Check if client is configured
      isConfigured: () => {
    ```
    **Category:** Bug risk
    **Severity:** minor

14. **'useToast' is defined but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/api/client.ts`
    **Line:** 12
    ```typescript
    */
    
    import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
    import { useToast } from '../components/UI/Toast';
    
    // Configuration
    const API_URL = import.meta.env.VITE_API_URL || '';
    ```
    **Category:** Performance
    **Severity:** major

15. **Unexpected any. Specify a different type** (`JS-0323`)
    **File:** `dashboard/frontend/src/api/configuration.ts`
    **Line:** 137
    ```typescript
    return response.data;
      },
    
      updateConfig: async (key: string, value: any): Promise<UserConfiguration> => {
        const response = await apiClient.put(`/api/config/${key}`, { config_value: value });
        return response.data;
      },
    ```
    **Category:** Anti-pattern
    **Severity:** critical

16. **Unexpected any. Specify a different type** (`JS-0323`)
    **File:** `dashboard/frontend/src/api/configuration.ts`
    **Line:** 277
    ```typescript
    },
    
      // Migration
      migrateFromEnv: async (): Promise<any> => {
        const response = await apiClient.post('/api/config/migrate-from-env');
        return response.data;
      },
    ```
    **Category:** Anti-pattern
    **Severity:** critical

17. **Unexpected any. Specify a different type** (`JS-0323`)
    **File:** `dashboard/frontend/src/api/configuration.ts`
    **Line:** 65
    ```typescript
    agent_type: string;
      agent_id?: string;
      config_name: string;
      config_data: Record<string, any>;
      llm_provider_id?: string;
      embedding_provider_id?: string;
      is_active: boolean;
    ```
    **Category:** Anti-pattern
    **Severity:** critical

18. **Unexpected any. Specify a different type** (`JS-0323`)
    **File:** `dashboard/frontend/src/api/configuration.ts`
    **Line:** 268
    ```typescript
    return response.data;
      },
    
      importConfigurations: async (data: any, options?: any): Promise<any> => {
        const response = await apiClient.post('/api/config/import', {
          import_data: data,
          options: options || {},
    ```
    **Category:** Anti-pattern
    **Severity:** critical

19. **Unexpected any. Specify a different type** (`JS-0323`)
    **File:** `dashboard/frontend/src/api/configuration.ts`
    **Line:** 229
    ```typescript
    return response.data;
      },
    
      listEmbeddingProviderTypes: async (): Promise<any[]> => {
        const response = await apiClient.get('/api/config/embedding/types');
        return response.data.provider_types;
      },
    ```
    **Category:** Anti-pattern
    **Severity:** critical

20. **Unexpected any. Specify a different type** (`JS-0323`)
    **File:** `dashboard/frontend/src/api/configuration.ts`
    **Line:** 268
    ```typescript
    return response.data;
      },
    
      importConfigurations: async (data: any, options?: any): Promise<any> => {
        const response = await apiClient.post('/api/config/import', {
          import_data: data,
          options: options || {},
    ```
    **Category:** Anti-pattern
    **Severity:** critical

21. **Unexpected any. Specify a different type** (`JS-0323`)
    **File:** `dashboard/frontend/src/api/configuration.ts`
    **Line:** 18
    ```typescript
    export interface UserConfiguration {
      id: string;
      config_key: string;
      config_value: any;
      config_type: 'string' | 'integer' | 'float' | 'boolean' | 'json' | 'array';
      description?: string;
      category: string;
    ```
    **Category:** Anti-pattern
    **Severity:** critical

22. **Unexpected any. Specify a different type** (`JS-0323`)
    **File:** `dashboard/frontend/src/api/configuration.ts`
    **Line:** 263
    ```typescript
    },
    
      // Import/Export
      exportConfigurations: async (): Promise<any> => {
        const response = await apiClient.get('/api/config/export');
        return response.data;
      },
    ```
    **Category:** Anti-pattern
    **Severity:** critical

23. **Unexpected any. Specify a different type** (`JS-0323`)
    **File:** `dashboard/frontend/src/api/configuration.ts`
    **Line:** 268
    ```typescript
    return response.data;
      },
    
      importConfigurations: async (data: any, options?: any): Promise<any> => {
        const response = await apiClient.post('/api/config/import', {
          import_data: data,
          options: options || {},
    ```
    **Category:** Anti-pattern
    **Severity:** critical

24. **Unexpected any. Specify a different type** (`JS-0323`)
    **File:** `dashboard/frontend/src/api/configuration.ts`
    **Line:** 86
    ```typescript
    is_enabled?: boolean;
      is_default?: boolean;
      priority?: number;
      extra_config?: Record<string, any>;
    }
    
    export interface EmbeddingProviderCreate {
    ```
    **Category:** Anti-pattern
    **Severity:** critical

25. **Unexpected any. Specify a different type** (`JS-0323`)
    **File:** `dashboard/frontend/src/api/configuration.ts`
    **Line:** 188
    ```typescript
    return response.data;
      },
    
      listLLMProviderTypes: async (): Promise<any[]> => {
        const response = await apiClient.get('/api/config/llm/types');
        return response.data.provider_types;
      },
    ```
    **Category:** Anti-pattern
    **Severity:** critical

26. **Type number trivially inferred from a number literal, remove type annotation** (`JS-0331`)
    **File:** `dashboard/frontend/src/api/consciousness.ts`
    **Line:** 93
    ```typescript
    export const getTimeSeriesData = async (
      agentId: string,
      metric: string,
      hours: number = 24
    ): Promise<TimeSeriesData> => {
      const response = await api.get(
        `/api/consciousness/visualization/timeseries?agent_id=${agentId}&metric=${metric}&hours=${hours}`
    ```
    **Category:** Anti-pattern
    **Severity:** major

27. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/App.tsx`
    **Line:** 158-167
    ```typescript
    );
    }
    
    function App() {
      return (
        <ToastProvider>
          <DashboardContent />
          {/* Debug features - only visible when Developer Mode is enabled */}
          <DebugPanel />
          <PerformanceOverlay position="top-right" />
        </ToastProvider>
      );
    }
    
    export default App;
    ```
    **Category:** Anti-pattern
    **Severity:** minor

28. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/App.tsx`
    **Line:** 50-156
    ```typescript
    { id: 'settings', label: 'Settings', icon: '⚙️' },
    ];
    
    function DashboardContent() {
      const [currentView, setCurrentView] = useState<View>('home');
      const [systemStatus, setSystemStatus] = useState<'healthy' | 'degraded' | 'offline'>('healthy');
      const [showSetup, setShowSetup] = useState(false);
      const toast = useToast();
      // Check if setup is needed
      useEffect(() => {
        const isConfigured = localStorage.getItem('swarm_configured') === 'true';
        if (!isConfigured) {
          setShowSetup(true);
        }
      }, []);
      // Set toast instance for API client
      useEffect(() => {
        setToastInstance({
          error: (title, message) => toast.error(title, message),
        });
      }, [toast]);
      // Check system health periodically
      const checkSystemHealth = useCallback(async () => {
        try {
          const API_URL = import.meta.env.VITE_API_URL || '';
          const response = await fetch(`${API_URL}/api/health`);
          if (!response.ok) {
            setSystemStatus('offline');
            return;
          }
          const data = await response.json();
                const isHealthy =
             data.gateway?.status === 'healthy' &&
            data.redis?.status === 'healthy' &&
            data.postgres?.status === 'healthy' &&
            data.qdrant?.status === 'healthy';
                const isDegraded =
             data.gateway?.status === 'healthy' ||
            data.redis?.status === 'healthy' ||
            data.postgres?.status === 'healthy' ||
            data.qdrant?.status === 'healthy';
                setSystemStatus(isHealthy ? 'healthy' : isDegraded ? 'degraded' : 'offline');
        } catch {
          setSystemStatus('offline');
        }
      }, []);
      useEffect(() => {
        checkSystemHealth();
        const interval = setInterval(checkSystemHealth, 30000); // Check every 30 seconds
        return () => clearInterval(interval);
      }, [checkSystemHealth]);
      const handleNavClick = useCallback((navId: string) => {
        setCurrentView(navId as View);
      }, []);
      const renderView = () => {
        switch (currentView) {
          case 'home':
            return <HomePage />;
          case 'agents':
            return <AgentsPage />;
          case 'consciousness':
            return <ConsciousnessPage />;
          case 'workflows':
            return <WorkflowBuilder />;
          case 'logs':
            return <LogsPage />;
          case 'settings':
            return <SettingsPage />;
          // Legacy views
          case 'legacy-dashboard':
            return <Dashboard />;
          case 'legacy-canvas':
            return <CollectiveCanvas />;
          case 'legacy-observability':
            return <Observability />;
          case 'legacy-chat':
            return <ChatInterface />;
          default:
            return <HomePage />;
        }
      };
      return (
        <>
          {showSetup ? (
            <SetupWizard onComplete={() => setShowSetup(false)} />
          ) : (
            <DashboardLayout
              activeNav={currentView}
              onNavClick={handleNavClick}
              navItems={navItems}
              systemStatus={systemStatus}
            >
              <ErrorBoundary>
                {renderView()}
              </ErrorBoundary>
            </DashboardLayout>
          )}
        </>
      );
    }
    
    function App() {
      return (
    ```
    **Category:** Anti-pattern
    **Severity:** minor

29. **`renderView` has a cyclomatic complexity of 11 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/App.tsx`
    **Line:** 110
    ```typescript
    setCurrentView(navId as View);
      }, []);
    
      const renderView = () => {
        switch (currentView) {
          case 'home':
            return <HomePage />;
    ```
    **Category:** Anti-pattern
    **Severity:** minor

30. **Function has a cyclomatic complexity of 12 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/App.tsx`
    **Line:** 72
    ```typescript
    }, [toast]);
    
      // Check system health periodically
      const checkSystemHealth = useCallback(async () => {
        try {
          const API_URL = import.meta.env.VITE_API_URL || '';
          const response = await fetch(`${API_URL}/api/health`);
    ```
    **Category:** Anti-pattern
    **Severity:** minor

31. **Fragments should contain more than one child - otherwise, there’s no need for a Fragment at all** (`JS-0424`)
    **File:** `dashboard/frontend/src/App.tsx`
    **Line:** 139-154
    ```typescript
    };
    
      return (
        <>
          {showSetup ? (
            <SetupWizard onComplete={() => setShowSetup(false)} />
          ) : (
            <DashboardLayout
              activeNav={currentView}
              onNavClick={handleNavClick}
              navItems={navItems}
              systemStatus={systemStatus}
            >
              <ErrorBoundary>
                {renderView()}
              </ErrorBoundary>
            </DashboardLayout>
          )}
        </>
      );
    }
    ```
    **Category:** Anti-pattern
    **Severity:** major

32. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/AgentMetricsGrid.tsx`
    **Line:** 42-495
    ```typescript
    // Use environment variable or relative path (nginx proxies /api to api:8000)
    const API_URL = import.meta.env.VITE_API_URL || "";
    
    export function AgentMetricsGrid({
      apiBaseUrl = API_URL,
      refreshInterval = 5000,
      showFilters = true,
      showPagination = true,
      pageSize = 10,
      onAgentSelect,
    }: AgentMetricsGridProps) {
      const [agents, setAgents] = useState<Record<string, AgentMetrics>>({});
      const [loading, setLoading] = useState(true);
      const [error, setError] = useState<string | null>(null);
      const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
      const [sortField, setSortField] = useState<SortField>("health_score");
      const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
      const [filterStatus, setFilterStatus] = useState<FilterStatus>("all");
      const [filterType, setFilterType] = useState<string>("all");
      const [currentPage, setCurrentPage] = useState(1);
      const [searchQuery, setSearchQuery] = useState("");
      // Fetch agents
      const fetchAgents = useCallback(async () => {
        try {
          const response = await fetch(`${apiBaseUrl}/api/v1/observability/agents`, {
            headers: {
              Authorization: `Bearer ${localStorage.getItem("token")}`,
            },
          });
                if (!response.ok) {
            throw new Error(`Failed to fetch agents: ${response.status}`);
          }
                const data = await response.json();
          setAgents(data.agents || {});
          setError(null);
        } catch (err) {
          const errorMessage = err instanceof Error ? err.message : "Failed to fetch agents";
          setError(errorMessage);
          console.error("AgentMetricsGrid error:", err);
        } finally {
          setLoading(false);
        }
      }, [apiBaseUrl]);
      // Initial fetch and refresh interval
      useEffect(() => {
        fetchAgents();
            const interval = setInterval(() => {
          fetchAgents();
        }, refreshInterval);
            return () => clearInterval(interval);
      }, [fetchAgents, refreshInterval]);
      // Get unique agent types for filter
      const agentTypes = useMemo(() => {
        const types = new Set<string>();
        Object.values(agents).forEach((agent) => {
          types.add(agent.agent_type);
        });
        return Array.from(types);
      }, [agents]);
      // Filter and sort agents
      const filteredAndSortedAgents = useMemo(() => {
        let agentList = Object.entries(agents).map(([id, metrics]) => ({ id, ...metrics }));
        // Apply search filter
        if (searchQuery) {
          const query = searchQuery.toLowerCase();
          agentList = agentList.filter(
            (agent) =>
              agent.id.toLowerCase().includes(query) ||
              agent.agent_type.toLowerCase().includes(query)
          );
        }
        // Apply status filter
        if (filterStatus !== "all") {
          agentList = agentList.filter((agent) => {
            if (filterStatus === "healthy") return agent.health_score >= 70;
            if (filterStatus === "degraded") return agent.health_score >= 50 && agent.health_score < 70;
            if (filterStatus === "critical") return agent.health_score < 50;
            return true;
          });
        }
        // Apply type filter
        if (filterType !== "all") {
          agentList = agentList.filter((agent) => agent.agent_type === filterType);
        }
        // Apply sorting
        agentList.sort((a, b) => {
          let comparison = 0;
                if (sortField === "last_activity") {
            comparison = new Date(a.last_activity).getTime() - new Date(b.last_activity).getTime();
          } else {
            comparison = a[sortField] - b[sortField];
          }
                return sortOrder === "asc" ? comparison : -comparison;
        });
        return agentList;
      }, [agents, searchQuery, filterStatus, filterType, sortField, sortOrder]);
      // Apply pagination
      const paginatedAgents = useMemo(() => {
        if (!showPagination) return filteredAndSortedAgents;
            const startIndex = (currentPage - 1) * pageSize;
        const endIndex = startIndex + pageSize;
        return filteredAndSortedAgents.slice(startIndex, endIndex);
      }, [filteredAndSortedAgents, currentPage, pageSize, showPagination]);
      // Calculate total pages
      const totalPages = Math.ceil(filteredAndSortedAgents.length / pageSize);
      // Handle sort change
      const handleSort = (field: SortField) => {
        if (sortField === field) {
          setSortOrder(sortOrder === "asc" ? "desc" : "asc");
        } else {
          setSortField(field);
          setSortOrder("desc");
        }
      };
      // Handle agent selection
      const handleAgentClick = (agentId: string) => {
        const newSelected = selectedAgent === agentId ? null : agentId;
        setSelectedAgent(newSelected);
        onAgentSelect?.(newSelected);
      };
      // Get health color
      const getHealthColor = (score: number): string => {
        if (score >= 70) return "text-green-400";
        if (score >= 50) return "text-yellow-400";
        return "text-red-400";
      };
      // Get health bar color
      const getHealthBarColor = (score: number): string => {
        if (score >= 70) return "bg-green-500";
        if (score >= 50) return "bg-yellow-500";
        return "bg-red-500";
      };
      // Get status badge
      const getStatusBadge = (score: number) => {
        if (score >= 70) {
          return (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-900/50 text-green-400">
              Healthy
            </span>
          );
        }
        if (score >= 50) {
          return (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-900/50 text-yellow-400">
              Degraded
            </span>
          );
        }
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-900/50 text-red-400">
            Critical
          </span>
        );
      };
      // Sort icon
      const SortIcon = ({ field }: { field: SortField }) => {
        if (sortField !== field) {
          return <span className="text-gray-600">⇅</span>;
        }
        return sortOrder === "asc" ? <span className="text-blue-400">↑</span> : <span className="text-blue-400">↓</span>;
      };
      if (loading) {
        return (
          <div className="flex items-center justify-center h-64 bg-gray-800 rounded-lg border border-gray-700">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
          </div>
        );
      }
      return (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Agent Metrics</h2>
            <div className="text-sm text-gray-400">
              {filteredAndSortedAgents.length} agents
            </div>
          </div>
          {/* Error display */}
          {error && (
            <div className="mb-4 bg-red-900/30 border border-red-500 rounded-lg p-3">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}
          {/* Filters */}
          {showFilters && (
            <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Search */}
              <div>
                <label className="block text-xs text-gray-400 mb-1">Search</label>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search agents..."
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                />
              </div>
              {/* Status Filter */}
              <div>
                <label className="block text-xs text-gray-400 mb-1">Status</label>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value as FilterStatus)}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value="all">All Status</option>
                  <option value="healthy">Healthy (70+)</option>
                  <option value="degraded">Degraded (50-69)</option>
                  <option value="critical">Critical {String.fromCharCode(60)}50)</option>
                </select>
              </div>
              {/* Type Filter */}
              <div>
                <label className="block text-xs text-gray-400 mb-1">Agent Type</label>
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value="all">All Types</option>
                  {agentTypes.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>
              {/* Sort */}
              <div>
                <label className="block text-xs text-gray-400 mb-1">Sort By</label>
                <select
                  value={`${sortField}-${sortOrder}`}
                  onChange={(e) => {
                    const [field, order] = e.target.value.split("-");
                    setSortField(field as SortField);
                    setSortOrder(order as SortOrder);
                  }}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value="health_score-desc">Health (High to Low)</option>
                  <option value="health_score-asc">Health (Low to High)</option>
                  <option value="success_rate-desc">Success Rate (High to Low)</option>
                  <option value="success_rate-asc">Success Rate (Low to High)</option>
                  <option value="tasks_completed-desc">Tasks (High to Low)</option>
                  <option value="tasks_completed-asc">Tasks (Low to High)</option>
                  <option value="error_count-desc">Errors (High to Low)</option>
                  <option value="error_count-asc">Errors (Low to High)</option>
                  <option value="last_activity-desc">Recent Activity</option>
                  <option value="last_activity-asc">Oldest Activity</option>
                </select>
              </div>
            </div>
          )}
          {/* Agent Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            {paginatedAgents.map((agent) => (
              <div
                key={agent.id}
                className={`bg-gray-900 rounded-lg border p-4 cursor-pointer transition-all ${
                  selectedAgent === agent.id
                    ? "border-blue-500 bg-blue-900/20"
                    : "border-gray-700 hover:border-gray-600"
                }`}
                onClick={() => handleAgentClick(agent.id)}
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${getHealthBarColor(agent.health_score)}`} />
                    <h3 className="text-white font-mono text-sm truncate">{agent.id}</h3>
                  </div>
                  {getStatusBadge(agent.health_score)}
                </div>
                {/* Metrics */}
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Type</span>
                    <span className="text-white">{agent.agent_type}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Tasks</span>
                    <span className="text-white">
                      {agent.tasks_completed}/{agent.tasks_completed + agent.tasks_failed}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Success Rate</span>
                    <span className={agent.success_rate >= 0.8 ? "text-green-400" : "text-red-400"}>
                      {(agent.success_rate * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Errors</span>
                    <span className={agent.error_count > 5 ? "text-red-400" : "text-gray-400"}>
                      {agent.error_count}
                    </span>
                  </div>
                                {/* Health Bar */}
                  <div className="mt-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-400">Health</span>
                      <span className={`text-xs ${getHealthColor(agent.health_score)}`}>
                        {agent.health_score.toFixed(0)}
                      </span>
                    </div>
                    <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${getHealthBarColor(agent.health_score)} transition-all duration-300`}
                        style={{ width: `${agent.health_score}%` }}
                      />
                    </div>
                  </div>
                  {/* Last Activity */}
                  <div className="mt-2 text-xs text-gray-500">
                    Last activity: {new Date(agent.last_activity).toLocaleString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
          {/* Empty State */}
          {paginatedAgents.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <svg className="w-12 h-12 mx-auto mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p>No agents found matching your criteria</p>
            </div>
          )}
          {/* Pagination */}
          {showPagination && totalPages > 1 && (
            <div className="flex items-center justify-between mt-6">
              <div className="text-sm text-gray-400">
                Page {currentPage} of {totalPages}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 bg-gray-700 text-white rounded hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 bg-gray-700 text-white rounded hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          )}
          {/* Selected Agent Details */}
          {selectedAgent && agents[selectedAgent] && (
            <div className="mt-6 bg-blue-900/20 border border-blue-500/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-blue-400">
                  Selected Agent: {selectedAgent}
                </h3>
                <button
                  onClick={() => {
                    setSelectedAgent(null);
                    onAgentSelect?.(null);
                  }}
                  className="text-gray-400 hover:text-white"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div className="bg-gray-900 rounded p-3">
                  <span className="text-gray-400">Type</span>
                  <p className="text-white font-medium">{agents[selectedAgent].agent_type}</p>
                </div>
                <div className="bg-gray-900 rounded p-3">
                  <span className="text-gray-400">Tasks Completed</span>
                  <p className="text-white font-medium">{agents[selectedAgent].tasks_completed}</p>
                </div>
                <div className="bg-gray-900 rounded p-3">
                  <span className="text-gray-400">Success Rate</span>
                  <p className={`font-medium ${agents[selectedAgent].success_rate >= 0.8 ? "text-green-400" : "text-red-400"}`}>
                    {(agents[selectedAgent].success_rate * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="bg-gray-900 rounded p-3">
                  <span className="text-gray-400">Health Score</span>
                  <p className={`font-medium ${getHealthColor(agents[selectedAgent].health_score)}`}>
                    {agents[selectedAgent].health_score.toFixed(1)}
                  </p>
                </div>
                <div className="bg-gray-900 rounded p-3">
                  <span className="text-gray-400">Messages Sent</span>
                  <p className="text-white font-medium">{agents[selectedAgent].messages_sent}</p>
                </div>
                <div className="bg-gray-900 rounded p-3">
                  <span className="text-gray-400">Messages Received</span>
                  <p className="text-white font-medium">{agents[selectedAgent].messages_received}</p>
                </div>
                <div className="bg-gray-900 rounded p-3">
                  <span className="text-gray-400">Error Count</span>
                  <p className={`font-medium ${agents[selectedAgent].error_count > 5 ? "text-red-400" : "text-white"}`}>
                    {agents[selectedAgent].error_count}
                  </p>
                </div>
                <div className="bg-gray-900 rounded p-3">
                  <span className="text-gray-400">Avg Task Duration</span>
                  <p className="text-white font-medium">
                    {agents[selectedAgent].avg_task_duration_seconds.toFixed(2)}s
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      );
    }
    
    export default AgentMetricsGrid;
    ```
    **Category:** Anti-pattern
    **Severity:** minor

33. **JSX tree is too deeply nested. Found 5 levels of nesting** (`JS-0415`)
    **File:** `dashboard/frontend/src/components/AgentMetricsGrid.tsx`
    **Line:** 327-335
    ```typescript
    {/* Agent Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            {paginatedAgents.map((agent) => (
              <div
                key={agent.id}
                className={`bg-gray-900 rounded-lg border p-4 cursor-pointer transition-all ${
                  selectedAgent === agent.id
                    ? "border-blue-500 bg-blue-900/20"
                    : "border-gray-700 hover:border-gray-600"
                }`}
                onClick={() => handleAgentClick(agent.id)}
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
    ```
    **Category:** Anti-pattern
    **Severity:** minor

34. **`AgentMetricsGrid` has a cyclomatic complexity of 11 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/AgentMetricsGrid.tsx`
    **Line:** 42
    ```typescript
    // Use environment variable or relative path (nginx proxies /api to api:8000)
    const API_URL = import.meta.env.VITE_API_URL || "";
    
    export function AgentMetricsGrid({
      apiBaseUrl = API_URL,
      refreshInterval = 5000,
      showFilters = true,
    ```
    **Category:** Anti-pattern
    **Severity:** minor

35. **'SortIcon' is assigned a value but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/AgentMetricsGrid.tsx`
    **Line:** 218
    ```typescript
    };
    
      // Sort icon
      const SortIcon = ({ field }: { field: SortField }) => {
        if (sortField !== field) {
          return <span className="text-gray-600">⇅</span>;
        }
    ```
    **Category:** Performance
    **Severity:** major

36. **'handleSort' is assigned a value but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/AgentMetricsGrid.tsx`
    **Line:** 164
    ```typescript
    const totalPages = Math.ceil(filteredAndSortedAgents.length / pageSize);
    
      // Handle sort change
      const handleSort = (field: SortField) => {
        if (sortField === field) {
          setSortOrder(sortOrder === "asc" ? "desc" : "asc");
        } else {
    ```
    **Category:** Performance
    **Severity:** major

37. **Unexpected any. Specify a different type** (`JS-0323`)
    **File:** `dashboard/frontend/src/components/AgentMetricsGrid.tsx`
    **Line:** 23
    ```typescript
    success_rate: number;
      health_score: number;
      last_activity: string;
      metadata: Record<string, any>;
    }
    
    interface AgentMetricsGridProps {
    ```
    **Category:** Anti-pattern
    **Severity:** critical

38. **`AgentCard` has a cyclomatic complexity of 11 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/Agents/AgentCard.tsx`
    **Line:** 37
    ```typescript
    compact?: boolean;
    }
    
    export function AgentCard({
      agent,
      instances = [],
      onDeploy,
    ```
    **Category:** Anti-pattern
    **Severity:** minor

39. **JSX tree is too deeply nested. Found 5 levels of nesting** (`JS-0415`)
    **File:** `dashboard/frontend/src/components/Agents/AgentCard.tsx`
    **Line:** 109-112
    ```typescript
    }
    
      return (
        <div
          onClick={handleCardClick}
          className="bg-gray-800 border border-gray-700 rounded-xl p-5 hover:border-blue-500 transition-all cursor-pointer group"
        >
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
    ```
    **Category:** Anti-pattern
    **Severity:** minor

40. **JSX tree is too deeply nested. Found 5 levels of nesting** (`JS-0415`)
    **File:** `dashboard/frontend/src/components/Agents/AgentCard.tsx`
    **Line:** 77-80
    ```typescript
    if (compact) {
        return (
          <div
            onClick={handleCardClick}
            className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 hover:border-blue-500 transition-colors cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <h3 className="text-white font-semibold">{agent.type_name}</h3>
    ```
    **Category:** Anti-pattern
    **Severity:** minor

41. **`getStatusColor` has a cyclomatic complexity of 7 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/Agents/AgentCard.tsx`
    **Line:** 49
    ```typescript
    const runningCount = instances.filter(inst => inst.state === 'running').length;
      const totalCount = instances.length;
    
      const getStatusColor = (state: string): 'healthy' | 'active' | 'warning' | 'error' | 'inactive' | 'pending' => {
        switch (state) {
          case 'running':
            return 'healthy';
    ```
    **Category:** Anti-pattern
    **Severity:** minor

42. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Agents/AgentCard.tsx`
    **Line:** 37-230
    ```typescript
    compact?: boolean;
    }
    
    export function AgentCard({
      agent,
      instances = [],
      onDeploy,
      onStart,
      onStop,
      onSelect,
      compact = false,
    }: AgentCardProps) {
      const runningCount = instances.filter(inst => inst.state === 'running').length;
      const totalCount = instances.length;
      const getStatusColor = (state: string): 'healthy' | 'active' | 'warning' | 'error' | 'inactive' | 'pending' => {
        switch (state) {
          case 'running':
            return 'healthy';
          case 'deployed':
          case 'suspended':
            return 'active';
          case 'stopped':
            return 'inactive';
          case 'error':
            return 'error';
          case 'available':
            return 'pending';
          default:
            return 'inactive';
        }
      };
      const handleDeploy = useCallback(() => {
        onDeploy?.(agent.type_name);
      }, [onDeploy, agent.type_name]);
      const handleCardClick = useCallback(() => {
        onSelect?.(agent);
      }, [onSelect, agent]);
      if (compact) {
        return (
          <div
            onClick={handleCardClick}
            className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 hover:border-blue-500 transition-colors cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <h3 className="text-white font-semibold">{agent.type_name}</h3>
                <p className="text-gray-400 text-sm mt-1 line-clamp-1">{agent.description}</p>
              </div>
              <div className="flex items-center gap-2">
                <div className="text-right">
                  <div className="text-xs text-gray-500">Running</div>
                  <div className="text-lg font-bold text-green-400">{runningCount}/{totalCount}</div>
                </div>
                {onDeploy && totalCount === 0 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeploy();
                    }}
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium transition-colors"
                  >
                    Deploy
                  </button>
                )}
              </div>
            </div>
          </div>
        );
      }
      return (
        <div
          onClick={handleCardClick}
          className="bg-gray-800 border border-gray-700 rounded-xl p-5 hover:border-blue-500 transition-all cursor-pointer group"
        >
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h3 className="text-white font-bold text-lg group-hover:text-blue-400 transition-colors">
                  {agent.type_name}
                </h3>
                <span className="text-xs text-gray-500 bg-gray-700 px-2 py-0.5 rounded">
                  {agent.actor_type}
                </span>
              </div>
              <p className="text-gray-400 text-sm mt-2 line-clamp-2">{agent.description}</p>
            </div>
          </div>
          {/* Instance Status */}
          <div className="mb-4">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-gray-500">Instances</span>
              <div className="flex items-center gap-2">
                <span className="text-green-400 font-medium">{runningCount} running</span>
                <span className="text-gray-600">/</span>
                <span className="text-gray-400">{totalCount} total</span>
              </div>
            </div>
            <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-green-500 to-green-400 transition-all duration-300"
                style={{ width: `${totalCount > 0 ? (runningCount / totalCount) * 100 : 0}%` }}
              />
            </div>
          </div>
          {/* Capabilities */}
          {agent.capabilities.length > 0 && (
            <div className="mb-4">
              <div className="text-xs text-gray-500 mb-2">Capabilities</div>
              <div className="flex flex-wrap gap-1.5">
                {agent.capabilities.slice(0, 4).map((cap, idx) => (
                  <span
                    key={idx}
                    className="text-xs text-blue-300 bg-blue-900/30 px-2 py-1 rounded"
                  >
                    {cap}
                  </span>
                ))}
                {agent.capabilities.length > 4 && (
                  <span className="text-xs text-gray-500 px-1">
                    +{agent.capabilities.length - 4} more
                  </span>
                )}
              </div>
            </div>
          )}
          {/* Instance States */}
          {instances.length > 0 && (
            <div className="mb-4 pt-4 border-t border-gray-700">
              <div className="text-xs text-gray-500 mb-2">Active Instances</div>
              <div className="space-y-1.5">
                {instances.slice(0, 3).map((inst) => (
                  <div key={inst.instance_id} className="flex items-center justify-between text-sm">
                    <span className="text-gray-400 font-mono text-xs truncate max-w-[150px]">
                      {inst.instance_id}
                    </span>
                    <div className="flex items-center gap-2">
                      <StatusBadge status={getStatusColor(inst.state)} size="sm" />
                      {inst.state === 'running' && onStop && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onStop(inst.instance_id);
                          }}
                          className="text-xs text-red-400 hover:text-red-300 transition-colors"
                        >
                          Stop
                        </button>
                      )}
                      {inst.state === 'stopped' && onStart && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onStart(inst.instance_id);
                          }}
                          className="text-xs text-green-400 hover:text-green-300 transition-colors"
                        >
                          Start
                        </button>
                      )}
                    </div>
                  </div>
                ))}
                {instances.length > 3 && (
                  <div className="text-xs text-gray-500 text-center pt-1">
                    +{instances.length - 3} more instances
                  </div>
                )}
              </div>
            </div>
          )}
          {/* Actions */}
          {onDeploy && totalCount === 0 && (
            <div className="pt-4 border-t border-gray-700">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeploy();
                }}
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
              >
                🚀 Deploy Agent
              </button>
            </div>
          )}
        </div>
      );
    }
    
    export default AgentCard;
    ```
    **Category:** Anti-pattern
    **Severity:** minor

43. **Do not use Array index in keys** (`JS-0437`)
    **File:** `dashboard/frontend/src/components/Agents/AgentCard.tsx`
    **Line:** 153
    ```typescript
    <div className="flex flex-wrap gap-1.5">
                {agent.capabilities.slice(0, 4).map((cap, idx) => (
                  <span
                    key={idx}
                    className="text-xs text-blue-300 bg-blue-900/30 px-2 py-1 rounded"
                  >
                    {cap}
    ```
    **Category:** Bug risk
    **Severity:** major

44. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Agents/AgentConfigPanel.tsx`
    **Line:** 28-288
    ```typescript
    onClose: () => void;
    }
    
    export function AgentConfigPanel({
      instanceId,
      config,
      onUpdate,
      onClose,
    }: AgentConfigPanelProps) {
      const [editedConfig, setEditedConfig] = useState<AgentConfig>({ ...config });
      const [isSaving, setIsSaving] = useState(false);
      const [error, setError] = useState<string | null>(null);
      const [hasChanges, setHasChanges] = useState(false);
      useEffect(() => {
        setEditedConfig({ ...config });
        setHasChanges(false);
        setError(null);
      }, [config]);
      const updateConfigValue = useCallback((key: string, value: unknown) => {
        setEditedConfig(prev => ({ ...prev, [key]: value }));
        setHasChanges(true);
      }, []);
      const handleSave = useCallback(async () => {
        setIsSaving(true);
        setError(null);
        try {
          await onUpdate(instanceId, editedConfig);
          setHasChanges(false);
          onClose();
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Failed to save configuration');
        } finally {
          setIsSaving(false);
        }
      }, [instanceId, editedConfig, onUpdate, onClose]);
      const handleReset = useCallback(() => {
        setEditedConfig({ ...config });
        setHasChanges(false);
        setError(null);
      }, [config]);
      const renderConfigField = (key: string, value: unknown) => {
        if (key === 'agent_id') {
          return (
            <div key={key}>
              <label className="block text-sm text-gray-400 mb-1">Agent ID</label>
              <input
                type="text"
                value={value as string}
                disabled
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-gray-500 cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 mt-1">Cannot be changed</p>
            </div>
          );
        }
        if (key === 'name' || key === 'description') {
          return (
            <div key={key}>
              <label className="block text-sm text-gray-400 mb-1 capitalize">
                {key.replace(/_/g, ' ')}
              </label>
              {key === 'description' ? (
                <textarea
                  value={value as string || ''}
                  onChange={(e) => updateConfigValue(key, e.target.value)}
                  rows={3}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500 transition-colors resize-none"
                />
              ) : (
                <input
                  type="text"
                  value={value as string || ''}
                  onChange={(e) => updateConfigValue(key, e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500 transition-colors"
                />
              )}
            </div>
          );
        }
        if (key === 'max_mailbox_size' || key === 'heartbeat_interval' || key === 'persistence_interval') {
          return (
            <div key={key}>
              <label className="block text-sm text-gray-400 mb-1 capitalize">
                {key.replace(/_/g, ' ')}
              </label>
              <input
                type="number"
                value={value as number || 0}
                onChange={(e) => updateConfigValue(key, parseFloat(e.target.value) || 0)}
                min={0}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>
          );
        }
        if (Array.isArray(value)) {
          return (
            <div key={key}>
              <label className="block text-sm text-gray-400 mb-1 capitalize">
                {key.replace(/_/g, ' ')}
              </label>
              <textarea
                value={value.join(', ')}
                onChange={(e) => updateConfigValue(key, e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
                rows={3}
                placeholder="item1, item2, item3"
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors resize-none"
              />
              <p className="text-xs text-gray-500 mt-1">Comma-separated values</p>
            </div>
          );
        }
        // Default: read-only display for unknown types
        return (
          <div key={key}>
            <label className="block text-sm text-gray-400 mb-1 capitalize">
              {key.replace(/_/g, ' ')}
            </label>
            <div className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-gray-400">
              {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
            </div>
          </div>
        );
      };
      // Sort config keys: agent_id first, then alphabetically
      const configKeys = Object.keys(editedConfig).sort((a, b) => {
        if (a === 'agent_id') return -1;
        if (b === 'agent_id') return 1;
        return a.localeCompare(b);
      });
      return (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 border border-gray-700 rounded-xl max-w-3xl w-full max-h-[90vh] overflow-auto">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-700 sticky top-0 bg-gray-800 z-10">
              <div>
                <h2 className="text-xl font-bold text-white">Configure Agent</h2>
                <p className="text-sm text-gray-400 mt-1 font-mono">{instanceId}</p>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Basic Settings */}
              <div>
                <h3 className="text-sm font-semibold text-gray-300 mb-4">Basic Settings</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {configKeys.filter(k => ['agent_id', 'name', 'description'].includes(k)).map(key => (
                    renderConfigField(key, editedConfig[key])
                  ))}
                </div>
              </div>
              {/* Runtime Settings */}
              <div>
                <h3 className="text-sm font-semibold text-gray-300 mb-4">Runtime Settings</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {configKeys.filter(k => ['max_mailbox_size', 'heartbeat_interval', 'persistence_interval'].includes(k)).map(key => (
                    renderConfigField(key, editedConfig[key])
                  ))}
                </div>
              </div>
              {/* Topics & Capabilities */}
              <div>
                <h3 className="text-sm font-semibold text-gray-300 mb-4">Topics & Capabilities</h3>
                <div className="grid grid-cols-1 gap-4">
                  {configKeys.filter(k => ['topics', 'capabilities'].includes(k)).map(key => (
                    renderConfigField(key, editedConfig[key])
                  ))}
                </div>
              </div>
              {/* Other Settings */}
              {configKeys.filter(k => !['agent_id', 'name', 'description', 'max_mailbox_size', 'heartbeat_interval', 'persistence_interval', 'topics', 'capabilities'].includes(k)).length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-300 mb-4">Other Settings</h3>
                  <div className="grid grid-cols-1 gap-4">
                    {configKeys.filter(k => !['agent_id', 'name', 'description', 'max_mailbox_size', 'heartbeat_interval', 'persistence_interval', 'topics', 'capabilities'].includes(k)).map(key => (
                      renderConfigField(key, editedConfig[key])
                    ))}
                  </div>
                </div>
              )}
              {/* Error Display */}
              {error && (
                <div className="bg-red-900/30 border border-red-700 rounded-lg p-3">
                  <p className="text-red-400 text-sm">{error}</p>
                </div>
              )}
              {/* Info Note */}
              <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-3">
                <p className="text-blue-400 text-sm">
                  💡 <strong>Note:</strong> Some configuration changes may require restarting the agent to take effect.
                </p>
              </div>
            </div>
            {/* Footer Actions */}
            <div className="flex items-center justify-between p-6 border-t border-gray-700 sticky bottom-0 bg-gray-800">
              <button
                onClick={handleReset}
                disabled={!hasChanges || isSaving}
                className="px-4 py-2 text-gray-400 hover:text-white disabled:text-gray-600 transition-colors"
              >
                Reset
              </button>
              <div className="flex items-center gap-3">
                {hasChanges && (
                  <span className="text-sm text-yellow-400">Unsaved changes</span>
                )}
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={!hasChanges || isSaving}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg font-medium transition-colors flex items-center gap-2"
                >
                  {isSaving ? (
                    <>
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Saving...
                    </>
                  ) : (
                    <>
                      💾 Save Changes
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }
    
    export default AgentConfigPanel;
    ```
    **Category:** Anti-pattern
    **Severity:** minor

45. **`renderConfigField` has a cyclomatic complexity of 13 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/Agents/AgentConfigPanel.tsx`
    **Line:** 71
    ```typescript
    setError(null);
      }, [config]);
    
      const renderConfigField = (key: string, value: unknown) => {
        if (key === 'agent_id') {
          return (
            <div key={key}>
    ```
    **Category:** Anti-pattern
    **Severity:** minor

46. **`AgentConfigPanel` has a cyclomatic complexity of 7 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/Agents/AgentConfigPanel.tsx`
    **Line:** 28
    ```typescript
    onClose: () => void;
    }
    
    export function AgentConfigPanel({
      instanceId,
      config,
      onUpdate,
    ```
    **Category:** Anti-pattern
    **Severity:** minor

47. **JSX tree is too deeply nested. Found 6 levels of nesting** (`JS-0415`)
    **File:** `dashboard/frontend/src/components/Agents/AgentConfigPanel.tsx`
    **Line:** 168
    ```typescript
    });
    
      return (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 border border-gray-700 rounded-xl max-w-3xl w-full max-h-[90vh] overflow-auto">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-700 sticky top-0 bg-gray-800 z-10">
    ```
    **Category:** Anti-pattern
    **Severity:** minor

48. **use `Boolean(actionInProgress)` instead** (`JS-0066`)
    **File:** `dashboard/frontend/src/components/Agents/AgentControls.tsx`
    **Line:** 223
    ```typescript
    <span className="text-xs text-red-400">Sure?</span>
                    <button
                      onClick={handleRemove}
                      disabled={!!actionInProgress}
                      className="text-xs px-2 py-1 bg-red-600 hover:bg-red-700 rounded transition-colors"
                    >
                      Yes
    ```
    **Category:** Anti-pattern
    **Severity:** minor

49. **use `Boolean(actionInProgress)` instead** (`JS-0066`)
    **File:** `dashboard/frontend/src/components/Agents/AgentControls.tsx`
    **Line:** 107
    ```typescript
    {(isStopped || isDeployed) && onStart && (
              <button
                onClick={() => handleAction('start', onStart)}
                disabled={!!actionInProgress}
                className="text-xs text-green-400 hover:text-green-300 disabled:text-gray-600 transition-colors"
              >
                Start
    ```
    **Category:** Anti-pattern
    **Severity:** minor

50. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Agents/AgentControls.tsx`
    **Line:** 23-255
    ```typescript
    compact?: boolean;
    }
    
    export function AgentControls({
      instanceId,
      state,
      onStart,
      onStop,
      onSuspend,
      onResume,
      onRemove,
      compact = false,
    }: AgentControlsProps) {
      const [actionInProgress, setActionInProgress] = useState<string | null>(null);
      const [showConfirmRemove, setShowConfirmRemove] = useState(false);
      const getStateLabel = (s: AgentState): string => {
        const labels: Record<AgentState, string> = {
          available: 'Available',
          deployed: 'Deployed',
          running: 'Running',
          stopped: 'Stopped',
          suspended: 'Suspended',
          error: 'Error',
        };
        return labels[s] || s;
      };
      const getStateBadgeStatus = (s: AgentState): 'healthy' | 'active' | 'warning' | 'error' | 'inactive' | 'pending' => {
        const statusMap: Record<AgentState, 'healthy' | 'active' | 'warning' | 'error' | 'inactive' | 'pending'> = {
          running: 'healthy',
          deployed: 'active',
          suspended: 'active',
          stopped: 'inactive',
          error: 'error',
          available: 'pending',
        };
        return statusMap[s] || 'inactive';
      };
      const handleAction = useCallback(async (action: string, handler?: (id: string) => Promise<void>) => {
        if (!handler || actionInProgress) return;
        setActionInProgress(action);
        try {
          await handler(instanceId);
        } finally {
          setActionInProgress(null);
        }
      }, [instanceId, actionInProgress]);
      const handleRemove = useCallback(async () => {
        if (!onRemove || actionInProgress) return;
        setActionInProgress('remove');
        try {
          await onRemove(instanceId);
        } finally {
          setActionInProgress(null);
          setShowConfirmRemove(false);
        }
      }, [instanceId, onRemove, actionInProgress]);
      const isRunning = state === 'running';
      const isStopped = state === 'stopped';
      const isSuspended = state === 'suspended';
      const isDeployed = state === 'deployed';
      if (compact) {
        return (
          <div className="flex items-center gap-2">
            <StatusBadge status={getStateBadgeStatus(state)} size="sm" />
            <span className="text-xs text-gray-400">{getStateLabel(state)}</span>
                    {isRunning && onStop && (
              <button
                onClick={() => handleAction('stop', onStop)}
                disabled={!!actionInProgress}
                className="text-xs text-red-400 hover:text-red-300 disabled:text-gray-600 transition-colors"
              >
                Stop
              </button>
            )}
                    {(isStopped || isDeployed) && onStart && (
              <button
                onClick={() => handleAction('start', onStart)}
                disabled={!!actionInProgress}
                className="text-xs text-green-400 hover:text-green-300 disabled:text-gray-600 transition-colors"
              >
                Start
              </button>
            )}
                    {isRunning && onSuspend && (
              <button
                onClick={() => handleAction('suspend', onSuspend)}
                disabled={!!actionInProgress}
                className="text-xs text-yellow-400 hover:text-yellow-300 disabled:text-gray-600 transition-colors"
              >
                Suspend
              </button>
            )}
                    {isSuspended && onResume && (
              <button
                onClick={() => handleAction('resume', onResume)}
                disabled={!!actionInProgress}
                className="text-xs text-green-400 hover:text-green-300 disabled:text-gray-600 transition-colors"
              >
                Resume
              </button>
            )}
          </div>
        );
      }
      return (
        <div className="flex items-center gap-3">
          {/* Status Indicator */}
          <div className="flex items-center gap-2 min-w-[120px]">
            <StatusBadge status={getStateBadgeStatus(state)} size="md" />
            <span className="text-sm text-gray-300">{getStateLabel(state)}</span>
          </div>
          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            {/* Start Button */}
            {(isStopped || isDeployed) && onStart && (
              <button
                onClick={() => handleAction('start', onStart)}
                disabled={!!actionInProgress}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:text-gray-500 rounded text-sm font-medium transition-colors"
              >
                {actionInProgress === 'start' ? (
                  <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                ) : (
                  '▶'
                )}
                Start
              </button>
            )}
            {/* Stop Button */}
            {isRunning && onStop && (
              <button
                onClick={() => handleAction('stop', onStop)}
                disabled={!!actionInProgress}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:text-gray-500 rounded text-sm font-medium transition-colors"
              >
                {actionInProgress === 'stop' ? (
                  <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                ) : (
                  '⏹'
                )}
                Stop
              </button>
            )}
            {/* Suspend Button */}
            {isRunning && onSuspend && (
              <button
                onClick={() => handleAction('suspend', onSuspend)}
                disabled={!!actionInProgress}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-700 disabled:text-gray-500 rounded text-sm font-medium transition-colors"
              >
                ⏸ Suspend
              </button>
            )}
            {/* Resume Button */}
            {isSuspended && onResume && (
              <button
                onClick={() => handleAction('resume', onResume)}
                disabled={!!actionInProgress}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:text-gray-500 rounded text-sm font-medium transition-colors"
              >
                ▶ Resume
              </button>
            )}
            {/* Remove Button */}
            {onRemove && state !== 'running' && (
              <>
                {!showConfirmRemove ? (
                  <button
                    onClick={() => setShowConfirmRemove(true)}
                    disabled={!!actionInProgress}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 rounded text-sm font-medium transition-colors"
                  >
                    🗑 Remove
                  </button>
                ) : (
                  <div className="flex items-center gap-2 bg-red-900/30 border border-red-700 rounded px-3 py-1.5">
                    <span className="text-xs text-red-400">Sure?</span>
                    <button
                      onClick={handleRemove}
                      disabled={!!actionInProgress}
                      className="text-xs px-2 py-1 bg-red-600 hover:bg-red-700 rounded transition-colors"
                    >
                      Yes
                    </button>
                    <button
                      onClick={() => setShowConfirmRemove(false)}
                      disabled={!!actionInProgress}
                      className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded transition-colors"
                    >
                      No
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
          {/* Loading Overlay */}
          {actionInProgress && (
            <div className="absolute inset-0 bg-black/20 backdrop-blur-[1px] rounded-lg flex items-center justify-center">
              <div className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 flex items-center gap-2">
                <svg className="animate-spin h-4 w-4 text-blue-400" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span className="text-sm text-white capitalize">{actionInProgress}ing...</span>
              </div>
            </div>
          )}
        </div>
      );
    }
    
    export default AgentControls;
    ```
    **Category:** Anti-pattern
    **Severity:** minor

51. **use `Boolean(actionInProgress)` instead** (`JS-0066`)
    **File:** `dashboard/frontend/src/components/Agents/AgentControls.tsx`
    **Line:** 213
    ```typescript
    {!showConfirmRemove ? (
                  <button
                    onClick={() => setShowConfirmRemove(true)}
                    disabled={!!actionInProgress}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 rounded text-sm font-medium transition-colors"
                  >
                    🗑 Remove
    ```
    **Category:** Anti-pattern
    **Severity:** minor

52. **use `Boolean(actionInProgress)` instead** (`JS-0066`)
    **File:** `dashboard/frontend/src/components/Agents/AgentControls.tsx`
    **Line:** 170
    ```typescript
    {isRunning && onStop && (
              <button
                onClick={() => handleAction('stop', onStop)}
                disabled={!!actionInProgress}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:text-gray-500 rounded text-sm font-medium transition-colors"
              >
                {actionInProgress === 'stop' ? (
    ```
    **Category:** Anti-pattern
    **Severity:** minor

53. **use `Boolean(actionInProgress)` instead** (`JS-0066`)
    **File:** `dashboard/frontend/src/components/Agents/AgentControls.tsx`
    **Line:** 230
    ```typescript
    </button>
                    <button
                      onClick={() => setShowConfirmRemove(false)}
                      disabled={!!actionInProgress}
                      className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded transition-colors"
                    >
                      No
    ```
    **Category:** Anti-pattern
    **Severity:** minor

54. **use `Boolean(actionInProgress)` instead** (`JS-0066`)
    **File:** `dashboard/frontend/src/components/Agents/AgentControls.tsx`
    **Line:** 189
    ```typescript
    {isRunning && onSuspend && (
              <button
                onClick={() => handleAction('suspend', onSuspend)}
                disabled={!!actionInProgress}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-700 disabled:text-gray-500 rounded text-sm font-medium transition-colors"
              >
                ⏸ Suspend
    ```
    **Category:** Anti-pattern
    **Severity:** minor

55. **use `Boolean(actionInProgress)` instead** (`JS-0066`)
    **File:** `dashboard/frontend/src/components/Agents/AgentControls.tsx`
    **Line:** 117
    ```typescript
    {isRunning && onSuspend && (
              <button
                onClick={() => handleAction('suspend', onSuspend)}
                disabled={!!actionInProgress}
                className="text-xs text-yellow-400 hover:text-yellow-300 disabled:text-gray-600 transition-colors"
              >
                Suspend
    ```
    **Category:** Anti-pattern
    **Severity:** minor

56. **`AgentControls` has a cyclomatic complexity of 26 with "very-high" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/Agents/AgentControls.tsx`
    **Line:** 23
    ```typescript
    compact?: boolean;
    }
    
    export function AgentControls({
      instanceId,
      state,
      onStart,
    ```
    **Category:** Anti-pattern
    **Severity:** minor

57. **use `Boolean(actionInProgress)` instead** (`JS-0066`)
    **File:** `dashboard/frontend/src/components/Agents/AgentControls.tsx`
    **Line:** 97
    ```typescript
    {isRunning && onStop && (
              <button
                onClick={() => handleAction('stop', onStop)}
                disabled={!!actionInProgress}
                className="text-xs text-red-400 hover:text-red-300 disabled:text-gray-600 transition-colors"
              >
                Stop
    ```
    **Category:** Anti-pattern
    **Severity:** minor

58. **use `Boolean(actionInProgress)` instead** (`JS-0066`)
    **File:** `dashboard/frontend/src/components/Agents/AgentControls.tsx`
    **Line:** 200
    ```typescript
    {isSuspended && onResume && (
              <button
                onClick={() => handleAction('resume', onResume)}
                disabled={!!actionInProgress}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:text-gray-500 rounded text-sm font-medium transition-colors"
              >
                ▶ Resume
    ```
    **Category:** Anti-pattern
    **Severity:** minor

59. **use `Boolean(actionInProgress)` instead** (`JS-0066`)
    **File:** `dashboard/frontend/src/components/Agents/AgentControls.tsx`
    **Line:** 127
    ```typescript
    {isSuspended && onResume && (
              <button
                onClick={() => handleAction('resume', onResume)}
                disabled={!!actionInProgress}
                className="text-xs text-green-400 hover:text-green-300 disabled:text-gray-600 transition-colors"
              >
                Resume
    ```
    **Category:** Anti-pattern
    **Severity:** minor

60. **use `Boolean(actionInProgress)` instead** (`JS-0066`)
    **File:** `dashboard/frontend/src/components/Agents/AgentControls.tsx`
    **Line:** 151
    ```typescript
    {(isStopped || isDeployed) && onStart && (
              <button
                onClick={() => handleAction('start', onStart)}
                disabled={!!actionInProgress}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:text-gray-500 rounded text-sm font-medium transition-colors"
              >
                {actionInProgress === 'start' ? (
    ```
    **Category:** Anti-pattern
    **Severity:** minor

61. **Fragments should contain more than one child - otherwise, there’s no need for a Fragment at all** (`JS-0424`)
    **File:** `dashboard/frontend/src/components/Agents/AgentControls.tsx`
    **Line:** 209-237
    ```typescript
    {/* Remove Button */}
            {onRemove && state !== 'running' && (
              <>
                {!showConfirmRemove ? (
                  <button
                    onClick={() => setShowConfirmRemove(true)}
                    disabled={!!actionInProgress}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 rounded text-sm font-medium transition-colors"
                  >
                    🗑 Remove
                  </button>
                ) : (
                  <div className="flex items-center gap-2 bg-red-900/30 border border-red-700 rounded px-3 py-1.5">
                    <span className="text-xs text-red-400">Sure?</span>
                    <button
                      onClick={handleRemove}
                      disabled={!!actionInProgress}
                      className="text-xs px-2 py-1 bg-red-600 hover:bg-red-700 rounded transition-colors"
                    >
                      Yes
                    </button>
                    <button
                      onClick={() => setShowConfirmRemove(false)}
                      disabled={!!actionInProgress}
                      className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded transition-colors"
                    >
                      No
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
    ```
    **Category:** Anti-pattern
    **Severity:** major

62. **`AgentsPage` has a cyclomatic complexity of 19 with "high" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/Agents/AgentsPage.tsx`
    **Line:** 47
    ```typescript
    runningCount: number;
    }
    
    export function AgentsPage() {
      const [data, setData] = useState<AgentsPageData>({
        legacyAgents: [],
        instances: [],
    ```
    **Category:** Anti-pattern
    **Severity:** minor

63. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Agents/AgentsPage.tsx`
    **Line:** 47-632
    ```typescript
    runningCount: number;
    }
    
    export function AgentsPage() {
      const [data, setData] = useState<AgentsPageData>({
        legacyAgents: [],
        instances: [],
        agentTypes: [],
        total: 0,
        activeCount: 0,
        inactiveCount: 0,
        errorCount: 0,
        runningCount: 0,
      });
      const [loading, setLoading] = useState(true);
      const [viewMode, setViewMode] = useState<'list' | 'cards'>('cards');
      const [filterType, setFilterType] = useState<string>('all');
      const [selectedAgent, setSelectedAgent] = useState<LegacyAgent | null>(null);
      const [selectedInstance, setSelectedInstance] = useState<AgentInstance | null>(null);
      const [showAgentDetails, setShowAgentDetails] = useState(false);
      const [showConfigPanel, setShowConfigPanel] = useState(false);
        // Modal states
      const [showDeployModal, setShowDeployModal] = useState(false);
      const [selectedAgentType, setSelectedAgentType] = useState<AgentType | null>(null);
        const toast = useToast();
      const fetchAllData = useCallback(async () => {
        setLoading(true);
        try {
          // Fetch legacy agents (supervisor-managed)
          const legacyResponse = await getAgents();
          const legacyAgents = legacyResponse.agents || [];
          // Fetch deployed instances
          const instancesResponse = await getAgentInstances();
          const instances = instancesResponse.instances || [];
          // Fetch available agent types
          const typesResponse = await getAvailableAgentTypes();
          const agentTypes = typesResponse.available_agents || [];
          // Calculate stats
          const runningCount = instances.filter((inst: AgentInstance) => inst.state === 'running').length;
          const deployedCount = instances.filter((inst: AgentInstance) => inst.state === 'deployed' || inst.state === 'stopped').length;
          setData({
            legacyAgents,
            instances,
            agentTypes,
            total: legacyAgents.length + instances.length,
            activeCount: legacyAgents.filter((a: LegacyAgent) => a.status === 'active').length + runningCount,
            inactiveCount: legacyAgents.filter((a: LegacyAgent) => a.status === 'inactive').length + deployedCount,
            errorCount: legacyAgents.filter((a: LegacyAgent) => a.status === 'error').length + instances.filter((inst: AgentInstance) => inst.state === 'error').length,
            runningCount,
          });
        } catch (error) {
          console.error('Failed to fetch agents:', error);
          toast.error('Failed to fetch agents', error instanceof Error ? error.message : 'Unknown error');
          setData({
            legacyAgents: [],
            instances: [],
            agentTypes: [],
            total: 0,
            activeCount: 0,
            inactiveCount: 0,
            errorCount: 0,
            runningCount: 0,
          });
        } finally {
          setLoading(false);
        }
      }, [toast]);
      useEffect(() => {
        fetchAllData();
        const interval = setInterval(fetchAllData, 10000); // Refresh every 10 seconds
        return () => clearInterval(interval);
      }, [fetchAllData]);
      // Lifecycle action handlers
      const handleDeploy = useCallback(async (agentType: string, config: DeployConfig) => {
        try {
          await deployAgent(agentType, config);
          toast.success('Agent deployed', `${agentType} instance deployed successfully`);
          fetchAllData();
        } catch (error) {
          toast.error('Deployment failed', error instanceof Error ? error.message : 'Unknown error');
          throw error;
        }
      }, [toast, fetchAllData]);
      const handleStart = useCallback(async (instanceId: string) => {
        try {
          await startAgent(instanceId);
          toast.success('Agent started', `Instance ${instanceId} is now running`);
          fetchAllData();
        } catch (error) {
          toast.error('Failed to start agent', error instanceof Error ? error.message : 'Unknown error');
        }
      }, [toast, fetchAllData]);
      const handleStop = useCallback(async (instanceId: string) => {
        try {
          await stopAgent(instanceId);
          toast.success('Agent stopped', `Instance ${instanceId} has been stopped`);
          fetchAllData();
        } catch (error) {
          toast.error('Failed to stop agent', error instanceof Error ? error.message : 'Unknown error');
        }
      }, [toast, fetchAllData]);
      const handleSuspend = useCallback(async (instanceId: string) => {
        try {
          await suspendAgent(instanceId);
          toast.success('Agent suspended', `Instance ${instanceId} is now suspended`);
          fetchAllData();
        } catch (error) {
          toast.error('Failed to suspend agent', error instanceof Error ? error.message : 'Unknown error');
        }
      }, [toast, fetchAllData]);
      const handleResume = useCallback(async (instanceId: string) => {
        try {
          await resumeAgent(instanceId);
          toast.success('Agent resumed', `Instance ${instanceId} is now running`);
          fetchAllData();
        } catch (error) {
          toast.error('Failed to resume agent', error instanceof Error ? error.message : 'Unknown error');
        }
      }, [toast, fetchAllData]);
      const handleRemove = useCallback(async (instanceId: string) => {
        try {
          await removeAgent(instanceId);
          toast.success('Agent removed', `Instance ${instanceId} has been removed`);
          fetchAllData();
        } catch (error) {
          toast.error('Failed to remove agent', error instanceof Error ? error.message : 'Unknown error');
        }
      }, [toast, fetchAllData]);
      const handleUpdateConfig = useCallback(async (instanceId: string, config: AgentConfig) => {
        try {
          await updateAgentConfig(instanceId, config);
          toast.success('Configuration updated', `Agent ${instanceId} configuration saved`);
          fetchAllData();
        } catch (error) {
          toast.error('Failed to update config', error instanceof Error ? error.message : 'Unknown error');
          throw error;
        }
      }, [toast, fetchAllData]);
      const handleDeployClick = useCallback((agentType: AgentType) => {
        setSelectedAgentType(agentType);
        setShowDeployModal(true);
      }, []);
      const handleInstanceSelect = useCallback((instance: AgentInstance) => {
        setSelectedInstance(instance);
        setShowConfigPanel(true);
      }, []);
      const getStatusFromType = (type: string): 'healthy' | 'active' | 'warning' | 'error' | 'inactive' | 'pending' => {
        const statusMap: Record<string, 'healthy' | 'active' | 'warning' | 'error' | 'inactive' | 'pending'> = {
          'active': 'active',
          'inactive': 'inactive',
          'error': 'error',
          'starting': 'pending',
          'dormant': 'inactive',
          'emerging': 'warning',
          'coherent': 'healthy',
          'transcendent': 'healthy',
          'running': 'healthy',
          'deployed': 'active',
          'stopped': 'inactive',
          'suspended': 'active',
        };
        return statusMap[type.toLowerCase()] || 'inactive';
      };
      const getInstanceState = (state: string): AgentState => {
        return state as AgentState;
      };
      // Filter instances by type
      const filteredInstances = filterType === 'all'
         ? data.instances
         : data.instances.filter((inst: AgentInstance) => inst.agent_type === filterType);
      // Group instances by type for card view
      const instancesByType = filteredInstances.reduce((acc, inst) => {
        if (!acc[inst.agent_type]) {
          acc[inst.agent_type] = [];
        }
        acc[inst.agent_type].push(inst);
        return acc;
      }, {} as Record<string, AgentInstance[]>);
      const columns: Column<AgentInstance>[] = [
        {
          key: 'instance_id',
          title: 'Instance ID',
          sortable: true,
          filterable: true,
          width: '250px',
          render: (value: string | boolean | Record<string, unknown>) => (
            <span className="font-mono text-sm text-blue-400">{String(value)}</span>
          ),
        },
        {
          key: 'agent_type',
          title: 'Type',
          sortable: true,
          filterable: true,
          width: '150px',
          render: (value: string | boolean | Record<string, unknown>) => (
            <span className="text-gray-300 capitalize">{String(value)}</span>
          ),
        },
        {
          key: 'state',
          title: 'Status',
          sortable: true,
          filterable: true,
          width: '120px',
          render: (value: string | boolean | Record<string, unknown>) => (
            <StatusBadge status={getStatusFromType(String(value))} size="sm" />
          ),
        },
        {
          key: 'actions',
          title: 'Actions',
          width: '280px',
          render: (_: unknown, row: AgentInstance) => (
            <AgentControls
              instanceId={row.instance_id}
              state={getInstanceState(row.state)}
              onStart={handleStart}
              onStop={handleStop}
              onSuspend={handleSuspend}
              onResume={handleResume}
              onRemove={handleRemove}
              compact
            />
          ),
        },
      ];
      if (loading) {
        return (
          <div className="flex items-center justify-center h-full">
            <LoadingSpinner size="lg" message="Loading agents..." />
          </div>
        );
      }
      return (
        <div className="space-y-6">
          {/* Page Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Agents</h1>
              <p className="text-gray-400 text-sm mt-1">
                Manage and deploy swarm agents
              </p>
            </div>
            <div className="flex items-center gap-3">
              {/* View Toggle */}
              <div className="flex items-center bg-gray-800 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('cards')}
                  className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                    viewMode === 'cards'
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  Cards
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                    viewMode === 'list'
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  List
                </button>
              </div>
              <button
                onClick={fetchAllData}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors"
              >
                ↻ Refresh
              </button>
            </div>
          </div>
          {/* Summary Metrics */}
          <MetricCardGrid columns={4}>
            <MetricCard
              title="Total Agents"
              value={data.total}
              color="blue"
            />
            <MetricCard
              title="Running"
              value={data.runningCount}
              color="green"
            />
            <MetricCard
              title="Deployed"
              value={data.inactiveCount}
              color="gray"
            />
            <MetricCard
              title="Errors"
              value={data.errorCount}
              color={data.errorCount > 0 ? 'red' : 'green'}
            />
          </MetricCardGrid>
          {/* Filter Bar */}
          {data.agentTypes.length > 0 && (
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
              <button
                onClick={() => setFilterType('all')}
                className={`px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
                  filterType === 'all'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:text-white'
                }`}
              >
                All Types
              </button>
              {data.agentTypes.map((type) => {
                const count = instancesByType[type.type_name]?.length || 0;
                return (
                  <button
                    key={type.type_name}
                    onClick={() => setFilterType(type.type_name)}
                    className={`px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
                      filterType === type.type_name
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-800 text-gray-400 hover:text-white'
                    }`}
                  >
                    {type.type_name} ({count})
                  </button>
                );
              })}
            </div>
          )}
          {/* Content Area */}
          {viewMode === 'cards' ? (
            /* Card View */
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.agentTypes.map((agentType) => (
                <AgentCard
                  key={agentType.type_name}
                  agent={agentType}
                  instances={instancesByType[agentType.type_name] || []}
                  onDeploy={() => handleDeployClick(agentType)}
                  onStart={handleStart}
                  onStop={handleStop}
                  onSelect={(agent: { type_name: string; module_path: string; description: string; capabilities: string[]; topics: string[]; actor_type: string }) => handleDeployClick(agent as AgentType)}
                />
              ))}
                        {data.agentTypes.length === 0 && (
                <div className="col-span-full">
                  <EmptyState
                    icon="🤖"
                    title="No agent types available"
                    description="Agent types will appear here when discovered"
                    action={{
                      label: 'Refresh',
                      onClick: fetchAllData,
                    }}
                  />
                </div>
              )}
            </div>
          ) : (
            /* List View */
            <div>
              {filteredInstances.length > 0 ? (
                <DataTable
                  data={filteredInstances}
                  columns={columns}
                  keyExtractor={(instance) => instance.instance_id}
                  onRowClick={handleInstanceSelect}
                  sortable
                  filterable
                  filterPlaceholder="Search instances by ID or type..."
                  emptyMessage="No agent instances found"
                  pageSize={10}
                />
              ) : (
                <EmptyState
                  icon="🤖"
                  title="No agent instances deployed"
                  description="Deploy an agent to get started"
                  action={
                    data.agentTypes.length > 0
                      ? {
                          label: 'Deploy Agent',
                          onClick: () => handleDeployClick(data.agentTypes[0]),
                        }
                      : {
                          label: 'Refresh',
                          onClick: fetchAllData,
                        }
                  }
                />
              )}
            </div>
          )}
          {/* Deploy Modal */}
          <DeployAgentModal
            agentType={selectedAgentType}
            isOpen={showDeployModal}
            onClose={() => {
              setShowDeployModal(false);
              setSelectedAgentType(null);
            }}
            onDeploy={handleDeploy}
          />
          {/* Config Panel */}
          {showConfigPanel && selectedInstance && (
            <AgentConfigPanel
              instanceId={selectedInstance.instance_id}
              config={selectedInstance.config as AgentConfig}
              onUpdate={handleUpdateConfig}
              onClose={() => {
                setShowConfigPanel(false);
                setSelectedInstance(null);
              }}
            />
          )}
          {/* Legacy Agents Section */}
          {data.legacyAgents.length > 0 && (
            <div className="border-t border-gray-700 pt-6">
              <h2 className="text-lg font-semibold mb-4">Legacy Agents (Supervisor-Managed)</h2>
              <DataTable<LegacyAgent>
                data={data.legacyAgents}
                columns={[
                  {
                    key: 'id',
                    title: 'Agent ID',
                    sortable: true,
                    filterable: true,
                    width: '200px',
                    render: (value) => (
                      <span className="font-mono text-sm text-blue-400">{String(value)}</span>
                    ),
                  },
                  {
                    key: 'type',
                    title: 'Type',
                    sortable: true,
                    filterable: true,
                    width: '150px',
                    render: (value) => (
                      <span className="text-gray-300 capitalize">{String(value)}</span>
                    ),
                  },
                  {
                    key: 'status',
                    title: 'Status',
                    sortable: true,
                    filterable: true,
                    width: '120px',
                    render: (value) => (
                      <StatusBadge status={getStatusFromType(String(value))} size="sm" />
                    ),
                  },
                  {
                    key: 'lastActivity',
                    title: 'Last Activity',
                    sortable: true,
                    width: '180px',
                    formatValue: (value) => {
                      const strValue = typeof value === 'string' ? value : undefined;
                      if (!strValue) return 'Never';
                      return new Date(strValue).toLocaleString();
                    },
                  },
                ]}
                keyExtractor={(agent) => agent.id}
                onRowClick={(agent) => {
                  setSelectedAgent(agent);
                  setShowAgentDetails(true);
                }}
                sortable
                filterable
                filterPlaceholder="Search legacy agents..."
                emptyMessage="No legacy agents"
                pageSize={5}
              />
            </div>
          )}
          {/* Agent Details Modal (Legacy) */}
          {showAgentDetails && selectedAgent && (
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
              <div className="bg-gray-800 border border-gray-700 rounded-xl max-w-2xl w-full max-h-[80vh] overflow-auto">
                <div className="flex items-center justify-between p-6 border-b border-gray-700">
                  <h2 className="text-xl font-bold">Agent Details</h2>
                  <button
                    onClick={() => setShowAgentDetails(false)}
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <div className="p-6 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm text-gray-400">Agent ID</label>
                      <p className="font-mono text-blue-400">{selectedAgent.id}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-400">Type</label>
                      <p className="text-white capitalize">{selectedAgent.type}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-400">Status</label>
                      <StatusBadge status={getStatusFromType(selectedAgent.status)} />
                    </div>
                    <div>
                      <label className="text-sm text-gray-400">Last Activity</label>
                      <p className="text-white">
                        {selectedAgent.lastActivity
                           ? new Date(selectedAgent.lastActivity).toLocaleString()
                          : 'Never'}
                      </p>
                    </div>
                  </div>
                  {/* Consciousness Metrics */}
                  {selectedAgent.consciousness_metrics && (
                    <div className="border-t border-gray-700 pt-4">
                      <h3 className="text-sm font-semibold text-gray-400 mb-3">Consciousness Metrics</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-gray-900 rounded-lg p-3">
                          <label className="text-xs text-gray-500">GWT Score</label>
                          <p className="text-lg font-bold text-blue-400">
                            {selectedAgent.consciousness_metrics.gwt_score.toFixed(4)}
                          </p>
                        </div>
                        <div className="bg-gray-900 rounded-lg p-3">
                          <label className="text-xs text-gray-500">Phi Value</label>
                          <p className="text-lg font-bold text-purple-400">
                            {selectedAgent.consciousness_metrics.phi_value.toFixed(4)}
                          </p>
                        </div>
                        <div className="bg-gray-900 rounded-lg p-3">
                          <label className="text-xs text-gray-500">AST Competence</label>
                          <p className="text-lg font-bold text-green-400">
                            {selectedAgent.consciousness_metrics.ast_competence.toFixed(4)}
                          </p>
                        </div>
                        <div className="bg-gray-900 rounded-lg p-3">
                          <label className="text-xs text-gray-500">Free Energy</label>
                          <p className="text-lg font-bold text-yellow-400">
                            {selectedAgent.consciousness_metrics.free_energy.toFixed(4)}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      );
    }
    
    export default AgentsPage;
    ```
    **Category:** Anti-pattern
    **Severity:** minor

64. **JSX tree is too deeply nested. Found 5 levels of nesting** (`JS-0415`)
    **File:** `dashboard/frontend/src/components/Agents/AgentsPage.tsx`
    **Line:** 303
    ```typescript
    }
    
      return (
        <div className="space-y-6">
          {/* Page Header */}
          <div className="flex items-center justify-between">
            <div>
    ```
    **Category:** Anti-pattern
    **Severity:** minor

65. **JSX tree is too deeply nested. Found 6 levels of nesting** (`JS-0415`)
    **File:** `dashboard/frontend/src/components/Agents/AgentsPage.tsx`
    **Line:** 556
    ```typescript
    {/* Agent Details Modal (Legacy) */}
          {showAgentDetails && selectedAgent && (
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
              <div className="bg-gray-800 border border-gray-700 rounded-xl max-w-2xl w-full max-h-[80vh] overflow-auto">
                <div className="flex items-center justify-between p-6 border-b border-gray-700">
                  <h2 className="text-xl font-bold">Agent Details</h2>
    ```
    **Category:** Anti-pattern
    **Severity:** minor

66. **Function has a cyclomatic complexity of 6 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/Agents/AgentsPage.tsx`
    **Line:** 72
    ```typescript
    const toast = useToast();
    
      const fetchAllData = useCallback(async () => {
        setLoading(true);
        try {
          // Fetch legacy agents (supervisor-managed)
    ```
    **Category:** Anti-pattern
    **Severity:** minor

67. **'AgentInstanceType' is defined but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/Agents/AgentsPage.tsx`
    **Line:** 31
    ```typescript
    AgentType,
      AgentInstance,
    } from '../../api/agents';
    import { AgentCard, AgentInstance as AgentInstanceType } from './AgentCard';
    import { DeployAgentModal, DeployConfig } from './DeployAgentModal';
    import { AgentConfigPanel, AgentConfig } from './AgentConfigPanel';
    import { AgentControls, AgentState } from './AgentControls';
    ```
    **Category:** Performance
    **Severity:** major

68. **'getRegistryStats' is defined but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/Agents/AgentsPage.tsx`
    **Line:** 26
    ```typescript
    removeAgent,
      deployAgent,
      updateAgentConfig,
      getRegistryStats,
      Agent as LegacyAgent,
      AgentType,
      AgentInstance,
    ```
    **Category:** Performance
    **Severity:** major

69. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Agents/DeployAgentModal.tsx`
    **Line:** 28-286
    ```typescript
    onDeploy: (agentType: string, config: DeployConfig) => Promise<void>;
    }
    
    export function DeployAgentModal({
      agentType,
      isOpen,
      onClose,
      onDeploy,
    }: DeployAgentModalProps) {
      const [config, setConfig] = useState<DeployConfig>({});
      const [customName, setCustomName] = useState('');
      const [customDescription, setCustomDescription] = useState('');
      const [customTopics, setCustomTopics] = useState('');
      const [maxMailboxSize, setMaxMailboxSize] = useState<number>(1000);
      const [heartbeatInterval, setHeartbeatInterval] = useState<number>(10.0);
      const [persistenceInterval, setPersistenceInterval] = useState<number | ''>('');
      const [isDeploying, setIsDeploying] = useState(false);
      const [error, setError] = useState<string | null>(null);
      // Reset form when modal opens with new agent
      React.useEffect(() => {
        if (isOpen && agentType) {
          setCustomName('');
          setCustomDescription('');
          setCustomTopics('');
          setMaxMailboxSize(1000);
          setHeartbeatInterval(10.0);
          setPersistenceInterval('');
          setConfig({});
          setError(null);
        }
      }, [isOpen, agentType]);
      const handleDeploy = useCallback(async () => {
        if (!agentType) return;
        setIsDeploying(true);
        setError(null);
        try {
          const deployConfig: DeployConfig = {
            ...config,
          };
          // Add custom values if provided
          if (customName) {
            deployConfig.name = customName;
          }
          if (customDescription) {
            deployConfig.description = customDescription;
          }
          if (customTopics.trim()) {
            deployConfig.topics = customTopics.split(',').map(t => t.trim()).filter(Boolean);
          }
          if (maxMailboxSize !== 1000) {
            deployConfig.max_mailbox_size = maxMailboxSize;
          }
          if (heartbeatInterval !== 10.0) {
            deployConfig.heartbeat_interval = heartbeatInterval;
          }
          if (persistenceInterval !== '') {
            deployConfig.persistence_interval = typeof persistenceInterval === 'number' ? persistenceInterval : undefined;
          }
          await onDeploy(agentType.type_name, deployConfig);
          onClose();
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Failed to deploy agent');
        } finally {
          setIsDeploying(false);
        }
      }, [agentType, config, customName, customDescription, customTopics, maxMailboxSize, heartbeatInterval, persistenceInterval, onDeploy, onClose]);
      const isFormValid = useMemo(() => {
        return !!agentType;
      }, [agentType]);
      if (!isOpen || !agentType) return null;
      return (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 border border-gray-700 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-auto">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-700 sticky top-0 bg-gray-800 z-10">
              <div>
                <h2 className="text-xl font-bold text-white">Deploy Agent</h2>
                <p className="text-sm text-gray-400 mt-1">{agentType.type_name}</p>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-white transition-colors"
                disabled={isDeploying}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Agent Description */}
              <div className="bg-gray-900 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-300 mb-2">About this Agent</h3>
                <p className="text-gray-400 text-sm">{agentType.description || 'No description available'}</p>
                {agentType.capabilities.length > 0 && (
                  <div className="mt-3">
                    <div className="text-xs text-gray-500 mb-1">Capabilities</div>
                    <div className="flex flex-wrap gap-1.5">
                      {agentType.capabilities.map((cap, idx) => (
                        <span key={idx} className="text-xs text-blue-300 bg-blue-900/30 px-2 py-1 rounded">
                          {cap}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              {/* Basic Configuration */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-300">Basic Configuration</h3>
                            <div>
                  <label className="block text-sm text-gray-400 mb-1">
                    Instance Name <span className="text-gray-600">(optional)</span>
                  </label>
                  <input
                    type="text"
                    value={customName}
                    onChange={(e) => setCustomName(e.target.value)}
                    placeholder={`Auto-generated if empty`}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
                    disabled={isDeploying}
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">
                    Description <span className="text-gray-600">(optional)</span>
                  </label>
                  <textarea
                    value={customDescription}
                    onChange={(e) => setCustomDescription(e.target.value)}
                    placeholder="Optional description for this instance"
                    rows={2}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors resize-none"
                    disabled={isDeploying}
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">
                    Topics <span className="text-gray-600">(comma-separated, optional)</span>
                  </label>
                  <input
                    type="text"
                    value={customTopics}
                    onChange={(e) => setCustomTopics(e.target.value)}
                    placeholder="topic1, topic2, topic3"
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
                    disabled={isDeploying}
                  />
                </div>
              </div>
              {/* Advanced Configuration */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-300">Advanced Settings</h3>
                            <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">
                      Max Mailbox Size
                    </label>
                    <input
                      type="number"
                      value={maxMailboxSize}
                      onChange={(e) => setMaxMailboxSize(parseInt(e.target.value) || 1000)}
                      min={100}
                      max={10000}
                      step={100}
                      className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500 transition-colors"
                      disabled={isDeploying}
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">
                      Heartbeat Interval (s)
                    </label>
                    <input
                      type="number"
                      value={heartbeatInterval}
                      onChange={(e) => setHeartbeatInterval(parseFloat(e.target.value) || 10.0)}
                      min={1}
                      max={60}
                      step={0.5}
                      className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500 transition-colors"
                      disabled={isDeploying}
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">
                      Persistence Interval <span className="text-gray-600">(optional)</span>
                    </label>
                    <input
                      type="number"
                      value={persistenceInterval}
                      onChange={(e) => setPersistenceInterval(e.target.value === '' ? '' : parseInt(e.target.value) || 0)}
                      min={0}
                      placeholder="Messages"
                      className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
                      disabled={isDeploying}
                    />
                    <p className="text-xs text-gray-500 mt-1">Auto-save state after N messages</p>
                  </div>
                </div>
              </div>
              {/* Error Display */}
              {error && (
                <div className="bg-red-900/30 border border-red-700 rounded-lg p-3">
                  <p className="text-red-400 text-sm">{error}</p>
                </div>
              )}
            </div>
            {/* Footer Actions */}
            <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-700 sticky bottom-0 bg-gray-800">
              <button
                onClick={onClose}
                className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                disabled={isDeploying}
              >
                Cancel
              </button>
              <button
                onClick={handleDeploy}
                disabled={!isFormValid || isDeploying}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                {isDeploying ? (
                  <>
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Deploying...
                  </>
                ) : (
                  <>
                    🚀 Deploy Agent
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      );
    }
    
    export default DeployAgentModal;
    ```
    **Category:** Anti-pattern
    **Severity:** minor

70. **`DeployAgentModal` has a cyclomatic complexity of 8 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/Agents/DeployAgentModal.tsx`
    **Line:** 28
    ```typescript
    onDeploy: (agentType: string, config: DeployConfig) => Promise<void>;
    }
    
    export function DeployAgentModal({
      agentType,
      isOpen,
      onClose,
    ```
    **Category:** Anti-pattern
    **Severity:** minor

71. **Function has a cyclomatic complexity of 11 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/Agents/DeployAgentModal.tsx`
    **Line:** 58
    ```typescript
    }
      }, [isOpen, agentType]);
    
      const handleDeploy = useCallback(async () => {
        if (!agentType) return;
    
        setIsDeploying(true);
    ```
    **Category:** Anti-pattern
    **Severity:** minor

72. **Template string can be replaced with regular string literal** (`JS-R1004`)
    **File:** `dashboard/frontend/src/components/Agents/DeployAgentModal.tsx`
    **Line:** 156
    ```typescript
    type="text"
                    value={customName}
                    onChange={(e) => setCustomName(e.target.value)}
                    placeholder={`Auto-generated if empty`}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
                    disabled={isDeploying}
                  />
    ```
    **Category:** Anti-pattern
    **Severity:** minor

73. **JSX tree is too deeply nested. Found 8 levels of nesting** (`JS-0415`)
    **File:** `dashboard/frontend/src/components/Agents/DeployAgentModal.tsx`
    **Line:** 105
    ```typescript
    if (!isOpen || !agentType) return null;
    
      return (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 border border-gray-700 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-auto">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-700 sticky top-0 bg-gray-800 z-10">
    ```
    **Category:** Anti-pattern
    **Severity:** minor

74. **use `Boolean(agentType)` instead** (`JS-0066`)
    **File:** `dashboard/frontend/src/components/Agents/DeployAgentModal.tsx`
    **Line:** 99
    ```typescript
    }, [agentType, config, customName, customDescription, customTopics, maxMailboxSize, heartbeatInterval, persistenceInterval, onDeploy, onClose]);
    
      const isFormValid = useMemo(() => {
        return !!agentType;
      }, [agentType]);
    
      if (!isOpen || !agentType) return null;
    ```
    **Category:** Anti-pattern
    **Severity:** minor

75. **Do not use Array index in keys** (`JS-0437`)
    **File:** `dashboard/frontend/src/components/Agents/DeployAgentModal.tsx`
    **Line:** 135
    ```typescript
    <div className="text-xs text-gray-500 mb-1">Capabilities</div>
                    <div className="flex flex-wrap gap-1.5">
                      {agentType.capabilities.map((cap, idx) => (
                        <span key={idx} className="text-xs text-blue-300 bg-blue-900/30 px-2 py-1 rounded">
                          {cap}
                        </span>
                      ))}
    ```
    **Category:** Bug risk
    **Severity:** major

76. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Canvas/AgentNode.tsx`
    **Line:** 68-191
    ```typescript
    'perceiver-plus': '👁️🧠',
    };
    
    function AgentNode({ data, selected }: AgentNodeProps) {
      const colors = statusColors[data.status] || statusColors.idle;
      const icon = agentIcons[data.agentType] || '🤖';
        const timeAgo = (timestamp: string) => {
        const now = new Date();
        const past = new Date(timestamp);
        const diff = Math.floor((now.getTime() - past.getTime()) / 1000);
            if (diff < 60) return 'just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return `${Math.floor(diff / 86400)}d ago`;
      };
      const renderMetricsBar = () => {
        if (!data.consciousnessMetrics) return null;
        const { gwt_score, phi_value, ast_competence, free_energy } = data.consciousnessMetrics;
            return (
          <div className="mt-2 space-y-1">
            <div className="flex items-center text-xs">
              <span className="text-gray-400 w-6">GWT</span>
              <div className="flex-1 bg-gray-700 rounded-full h-1">
                <div className="bg-blue-500 h-1 rounded-full" style={{ width: `${gwt_score * 100}%` }} />
              </div>
            </div>
            <div className="flex items-center text-xs">
              <span className="text-gray-400 w-6">Φ</span>
              <div className="flex-1 bg-gray-700 rounded-full h-1">
                <div className="bg-purple-500 h-1 rounded-full" style={{ width: `${phi_value * 100}%` }} />
              </div>
            </div>
            <div className="flex items-center text-xs">
              <span className="text-gray-400 w-6">AST</span>
              <div className="flex-1 bg-gray-700 rounded-full h-1">
                <div className="bg-green-500 h-1 rounded-full" style={{ width: `${ast_competence * 100}%` }} />
              </div>
            </div>
            <div className="flex items-center text-xs">
              <span className="text-gray-400 w-6">FEP</span>
              <div className="flex-1 bg-gray-700 rounded-full h-1">
                <div className="bg-orange-500 h-1 rounded-full" style={{ width: `${(1 - free_energy) * 100}%` }} />
              </div>
            </div>
          </div>
        );
      };
      return (
        <div
          className={`None
            px-4 py-3 rounded-lg shadow-lg border-2 transition-all duration-200
            ${selected ? 'ring-2 ring-white ring-offset-2 ring-offset-gray-900' : ''}None
          `}
          style={{
            backgroundColor: colors.bg,
            borderColor: colors.border,
            minWidth: '240px',
            maxWidth: '300px',
          }}
        >
          {/* Target Handle (input) */}
          <Handle
            type="target"
            position={Position.Top}
            className="!bg-gray-600 !border-2 !border-gray-500"
            id="input-main"
          />
          {/* Header */}
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">{icon}</span>
            <span
              className="text-xs font-semibold px-2 py-1 rounded uppercase"
              style={{
                backgroundColor: colors.border,
                color: '#FFFFFF',
              }}
            >
              {data.status}
            </span>
          </div>
          {/* Agent Type */}
          <div className="text-white font-bold text-lg mb-1">
            {data.agentType.toString().charAt(0).toUpperCase() + data.agentType.toString().slice(1).replace('-', ' ')}
          </div>
          {/* Agent ID */}
          <div className="text-gray-400 text-xs font-mono mb-2 truncate">
            {data.agentId}
          </div>
          {/* Consciousness Metrics */}
          {renderMetricsBar()}
          {/* Activity & Message Count */}
          <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
            <span>Active: {timeAgo(data.lastActivity)}</span>
            {data.messageCount !== undefined && (
              <span>💬 {data.messageCount}</span>
            )}
          </div>
          {/* Source Handle (output) */}
          <Handle
            type="source"
            position={Position.Bottom}
            className="!bg-gray-600 !border-2 !border-gray-500"
            id="output-main"
          />
                {/* Additional handle for multi-connection support */}
          <Handle
            type="source"
            position={Position.Right}
            className="!bg-gray-600 !border-2 !border-gray-500 !w-3 !h-3"
            id="output-side"
            style={{ top: '50%', transform: 'translateY(-50%)' }}
          />
        </div>
      );
    }
    
    export default memo(AgentNode);
    ```
    **Category:** Anti-pattern
    **Severity:** minor

77. **JSX tree is too deeply nested. Found 5 levels of nesting** (`JS-0415`)
    **File:** `dashboard/frontend/src/components/Canvas/CanvasToolbar.tsx`
    **Line:** 37
    ```typescript
    disabled = false,
    }: CanvasToolbarProps) {
      return (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10">
          <div className="flex items-center gap-2 bg-gray-800 border border-gray-700 rounded-lg shadow-xl p-2">
            {/* Zoom Controls */}
            <div className="flex items-center gap-1 pr-2 border-r border-gray-700">
    ```
    **Category:** Anti-pattern
    **Severity:** minor

78. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Canvas/CanvasToolbar.tsx`
    **Line:** 23-161
    ```typescript
    disabled?: boolean;
    }
    
    export function CanvasToolbar({
      onZoomIn,
      onZoomOut,
      onFitView,
      onSaveWorkflow,
      onLoadWorkflow,
      onExecuteWorkflow,
      onClearCanvas,
      onToggleGrid,
      gridEnabled = true,
      isExecuting = false,
      disabled = false,
    }: CanvasToolbarProps) {
      return (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10">
          <div className="flex items-center gap-2 bg-gray-800 border border-gray-700 rounded-lg shadow-xl p-2">
            {/* Zoom Controls */}
            <div className="flex items-center gap-1 pr-2 border-r border-gray-700">
              <button
                onClick={onZoomOut}
                disabled={disabled}
                className="p-2 hover:bg-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Zoom Out"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                </svg>
              </button>
                        <button
                onClick={onZoomIn}
                disabled={disabled}
                className="p-2 hover:bg-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Zoom In"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </button>
                        <button
                onClick={onFitView}
                disabled={disabled}
                className="p-2 hover:bg-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Fit View"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
              </button>
            </div>
                    {/* Grid Toggle */}
            <div className="flex items-center gap-1 pr-2 border-r border-gray-700">
              <button
                onClick={onToggleGrid}
                disabled={disabled}
                className={`p-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                  gridEnabled ? 'bg-blue-600 text-white' : 'hover:bg-gray-700 text-gray-400 hover:text-white'
                }`}
                title="Toggle Grid"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
              </button>
            </div>
                    {/* Workflow Controls */}
            <div className="flex items-center gap-1 pr-2 border-r border-gray-700">
              <button
                onClick={onSaveWorkflow}
                disabled={disabled}
                className="p-2 hover:bg-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Save Workflow"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                </svg>
              </button>
                        <button
                onClick={onLoadWorkflow}
                disabled={disabled}
                className="p-2 hover:bg-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Load Workflow"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
              </button>
            </div>
                    {/* Execute & Clear */}
            <div className="flex items-center gap-1">
              <button
                onClick={onExecuteWorkflow}
                disabled={disabled || isExecuting}
                className={`None
                  px-4 py-2 rounded-lg font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                  ${isExecuting
                     ? 'bg-yellow-600 text-white animate-pulse'
                     : 'bg-green-600 hover:bg-green-700 text-white'}None
                `}
                title="Execute Workflow"
              >
                {isExecuting ? (
                  <span className="flex items-center gap-2">
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Running...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                    Execute
                  </span>
                )}
              </button>
                        <button
                onClick={onClearCanvas}
                disabled={disabled}
                className="p-2 hover:bg-red-900 rounded-lg text-gray-400 hover:text-red-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Clear Canvas"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      );
    }
    
    export default CanvasToolbar;
    ```
    **Category:** Anti-pattern
    **Severity:** minor

79. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Canvas/Canvas.tsx`
    **Line:** 41-148
    ```typescript
    const initialEdges: Edge[] = [];
    
    export function CollectiveCanvas() {
      const [nodes, setNodes, onNodesChange] = useNodesState([]);
      const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
      const [loading, setLoading] = useState(true);
      const [error, setError] = useState<string | null>(null);
      // Fetch agents from API
      const fetchAgents = useCallback(async () => {
        try {
          const response = await fetch(`${API_URL}/api/agents`);
          if (!response.ok) throw new Error('Failed to fetch agents');
                const data = await response.json();
                const agentNodes: Node<AgentData>[] = data.agents.map(
            (agent: AgentApiResponse, index: number) => ({
              id: agent.id,
              type: 'agentNode',
              position: {
                x: (index % 3) * 300 + 100,
                y: Math.floor(index / 3) * 200 + 100,
              },
              data: {
                agentId: agent.id,
                agentType: agent.type.toLowerCase() as AgentData['agentType'],
                status: agent.status as AgentData['status'],
                lastActivity: agent.lastActivity || new Date().toISOString(),
              },
            })
          );
                setNodes(agentNodes);
          setError(null);
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
          setLoading(false);
        }
      }, [setNodes]);
      // Initial fetch
      useEffect(() => {
        fetchAgents();
      }, [fetchAgents]);
      // Poll for updates every 5 seconds
      useEffect(() => {
        const interval = setInterval(fetchAgents, 5000);
        return () => clearInterval(interval);
      }, [fetchAgents]);
      // Handle node connections
      const onConnect = useCallback(
        (params: Connection) => {
          setEdges((eds: Edge[]) => addEdge(params, eds));
        },
        [setEdges]
      );
      if (loading) {
        return (
          <div className="flex items-center justify-center h-screen bg-gray-900">
            <div className="text-white text-xl">Loading swarm...</div>
          </div>
        );
      }
      if (error) {
        return (
          <div className="flex items-center justify-center h-screen bg-gray-900">
            <div className="text-red-500 text-xl">Error: {error}</div>
          </div>
        );
      }
      return (
        <div className="w-full h-screen bg-gray-900">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            fitView
            className="bg-gray-900"
          >
            <Background color="#374151" gap={20} />
            <Controls className="bg-gray-800 border-gray-700" />
            <MiniMap
              nodeColor={(node: Node) => {
                const data = node.data as AgentData;
                const status = data?.status;
                switch (status) {
                  case 'idle': return '#6B7280';
                  case 'thinking': return '#3B82F6';
                  case 'acting': return '#22C55E';
                  case 'error': return '#EF4444';
                  default: return '#6B7280';
                }
              }}
              className="bg-gray-800 border-gray-700"
              maskColor="rgba(0, 0, 0, 0.5)"
            />
          </ReactFlow>
        </div>
      );
    }
    
    export default CollectiveCanvas;
    ```
    **Category:** Anti-pattern
    **Severity:** minor

80. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Canvas/ConnectionEdge.tsx`
    **Line:** 43-122
    ```typescript
    default: 'Message',
    };
    
    function ConnectionEdge({
      id,
      sourceX,
      sourceY,
      targetX,
      targetY,
      sourcePosition,
      targetPosition,
      style = {},
      data,
      markerEnd,
    }: ConnectionEdgeProps) {
      const messageType = data?.messageType || 'default';
      const color = messageColors[messageType];
      const messageCount = data?.messageCount || 0;
      const customLabel = data?.label;
      const [edgePath, labelX, labelY] = getBezierPath({
        sourceX,
        sourceY,
        targetX,
        targetY,
        sourcePosition,
        targetPosition,
      });
      return (
        <>
          <BaseEdge
            path={edgePath}
            markerEnd={markerEnd}
            style={{
              strokeWidth: 3,
              stroke: color,
              ...style,
            }}
          />
                {/* Animated dash for message flow */}
          <BaseEdge
            path={edgePath}
            style={{
              strokeWidth: 3,
              stroke: color,
              strokeDasharray: '5, 5',
              animation: 'dashAnimation 1s linear infinite',
              opacity: 0.5,
            }}
          />
                <EdgeLabelRenderer>
            <div
              className="nodrag nopan absolute transform -translate-x-1/2 -translate-y-1/2 pointer-events-none"
              style={{
                left: labelX,
                top: labelY,
                backgroundColor: 'rgba(31, 41, 55, 0.9)',
                borderRadius: '4px',
                padding: '4px 8px',
                fontSize: '11px',
                fontWeight: '600',
                color: color,
                border: `1px solid ${color}`,
                whiteSpace: 'nowrap',
              }}
            >
              {customLabel || (messageCount > 0 ? `${messageLabels[messageType]} (${messageCount})` : messageLabels[messageType])}
            </div>
          </EdgeLabelRenderer>
                <style>{`None
            @keyframes dashAnimation {
              to {
                stroke-dashoffset: -10;
              }
            }
          `}</style>
        </>
      );
    }
    
    export default memo(ConnectionEdge);
    ```
    **Category:** Anti-pattern
    **Severity:** minor

81. **Expected property shorthand** (`JS-0240`)
    **File:** `dashboard/frontend/src/components/Canvas/ConnectionEdge.tsx`
    **Line:** 104
    ```typescript
    padding: '4px 8px',
                fontSize: '11px',
                fontWeight: '600',
                color: color,
                border: `1px solid ${color}`,
                whiteSpace: 'nowrap',
              }}
    ```
    **Category:** Anti-pattern
    **Severity:** minor

82. **'id' is defined but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/Canvas/ConnectionEdge.tsx`
    **Line:** 44
    ```typescript
    };
    
    function ConnectionEdge({
      id,
      sourceX,
      sourceY,
      targetX,
    ```
    **Category:** Performance
    **Severity:** major

83. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`
    **Line:** 174-722
    ```typescript
    // Enhanced Canvas Component
    // =============================================================================
    
    export function EnhancedCanvas() {
      const [nodes, setNodes, onNodesChange] = useNodesState([]);
      const [edges, setEdges, onEdgesChange] = useEdgesState([]);
      const [selectedNode, setSelectedNode] = useState<Node | null>(null);
      const [workflows, setWorkflows] = useState<Workflow[]>([]);
      const [currentWorkflow, setCurrentWorkflow] = useState<Workflow | null>(null);
      const [executionState, setExecutionState] = useState<ExecutionState>({
        status: 'idle',
        progress: 0,
      });
      const [isExecuting, setIsExecuting] = useState(false);
      const [showPalette, setShowPalette] = useState(true);
      const [savedWorkflows, setSavedWorkflows] = useState<Workflow[]>([]);
      const [showExecution, setShowExecution] = useState(false);
        // Metrics overlay state
      const [showMetrics, setShowMetrics] = useState(false);
      const [swarmHealth, setSwarmHealth] = useState<SwarmHealthMetrics | null>(null);
      const [consciousnessMetrics, setConsciousnessMetrics] = useState<ConsciousnessMetrics | null>(null);
      const [metricsLoading, setMetricsLoading] = useState(false);
      // Fetch agents
      const fetchAgents = useCallback(async () => {
        try {
          const response = await fetch(`${API_URL}/api/agents`);
          if (!response.ok) throw new Error('Failed to fetch agents');
                const data = await response.json();
                const agentNodes: Node<AgentData>[] = data.agents.map(
            (agent: AgentApiResponse, index: number) => ({
              id: agent.id,
              type: 'agentNode',
              position: {
                x: (index % 4) * 300 + 100,
                y: Math.floor(index / 4) * 200 + 100,
              },
              data: {
                agentId: agent.id,
                agentType: agent.type.toLowerCase() as AgentData['agentType'],
                status: agent.status as AgentData['status'],
                lastActivity: agent.lastActivity || new Date().toISOString(),
              },
            })
          );
                setNodes(agentNodes);
        } catch (err) {
          console.error('Failed to fetch agents:', err);
        }
      }, [setNodes]);
      // Save workflow
      const saveWorkflow = useCallback(async (workflow: Workflow) => {
        try {
          const response = await fetch(`${API_URL}/api/workflows`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(workflow),
          });
                if (!response.ok) throw new Error('Failed to save workflow');
                const saved = await response.json();
          setSavedWorkflows([...savedWorkflows, saved]);
          setCurrentWorkflow(saved);
        } catch (err) {
          console.error('Failed to save workflow:', err);
        }
      }, [savedWorkflows, setCurrentWorkflow]);
      // Load workflow
      const loadWorkflow = useCallback(async (workflowId: string) => {
        try {
          const response = await fetch(`${API_URL}/api/workflows/${workflowId}`);
          if (!response.ok) throw new Error('Failed to load workflow');
                const workflow = await response.json();
          setCurrentWorkflow(workflow);
          setNodes(workflow.nodes);
          setEdges(workflow.edges);
        } catch (err) {
          console.error('Failed to load workflow:', err);
        }
      }, [setCurrentWorkflow, setNodes, setEdges]);
      // Execute workflow
      const executeWorkflow = useCallback(async () => {
        if (!currentWorkflow) return;
            setIsExecuting(true);
        setExecutionState({ status: 'running', progress: 0 });
        try {
          const response = await fetch(`${API_URL}/api/workflows/${currentWorkflow.id}/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              nodes: currentWorkflow.nodes,
              edges: currentWorkflow.edges,
            }),
          });
          if (!response.ok) throw new Error('Failed to execute workflow');
                const result = await response.json();
                // Simulate execution with progress updates
          for (let i = 0; i < currentWorkflow.nodes.length; i++) {
            await new Promise(resolve => setTimeout(resolve, 500));
            setExecutionState({
              status: 'running',
              currentNode: currentWorkflow.nodes[i].id,
              progress: (i + 1) / currentWorkflow.nodes.length * 100,
              message: `Executing node ${currentWorkflow.nodes[i].id}`,
            });
          }
          setExecutionState({
            status: 'completed',
            progress: 100,
            message: 'Workflow execution completed',
          });
        } catch (err) {
          setExecutionState({
            status: 'error',
            message: err instanceof Error ? err.message : 'Unknown error',
          });
        } finally {
          setIsExecuting(false);
          setTimeout(() => setShowExecution(false), 2000);
        }
      }, [currentWorkflow, setExecutionState, setShowExecution]);
      // Create node from palette
      const addNode = useCallback((type: string, position: Position) => {
        const newNode: Node = {
          id: `node-${Date.now()}`,
          type,
          position,
          data: { isNew: true },
        };
            setNodes((nds) => [...nds, newNode]);
        return newNode;
      }, [setNodes]);
      // Handle node connections
      const onConnect = useCallback(
        (params: Connection) => {
          setEdges((eds) => addEdge(params, eds));
        },
        [setEdges]
      );
      // Handle node selection
      const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
        setSelectedNode(node);
      }, []);
      // Fetch metrics
      const fetchMetrics = useCallback(async () => {
        if (!showMetrics) return;
            setMetricsLoading(true);
        try {
          const [healthResponse, consciousnessResponse] = await Promise.all([
            fetch(`${API_URL}/api/v1/observability/swarm`, {
              headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
            }),
            fetch(`${API_URL}/api/v1/observability/consciousness`, {
              headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
            }),
          ]);
                if (healthResponse.ok) {
            const healthData = await healthResponse.json();
            setSwarmHealth(healthData);
          }
                if (consciousnessResponse.ok) {
            const consciousnessData = await consciousnessResponse.json();
            setConsciousnessMetrics(consciousnessData);
          }
        } catch (err) {
          console.error('Failed to fetch metrics:', err);
        } finally {
          setMetricsLoading(false);
        }
      }, [showMetrics]);
      // Initial fetch
      useEffect(() => {
        fetchAgents();
      }, []);
      // Poll for agent updates
      useEffect(() => {
        const interval = setInterval(fetchAgents, 5000);
        return () => clearInterval(interval);
      }, [fetchAgents]);
      // Poll for metrics updates when metrics panel is open
      useEffect(() => {
        if (showMetrics) {
          fetchMetrics();
          const interval = setInterval(fetchMetrics, 5000);
          return () => clearInterval(interval);
        }
      }, [showMetrics, fetchMetrics]);
      if (loading) {
        return (
          <div className="flex items-center justify-center h-screen bg-gray-900">
            <div className="text-white text-xl">Loading swarm...</div>
          </div>
        );
      }
      if (error) {
        return (
          <div className="flex items-center justify-center h-screen bg-gray-900">
            <div className="text-red-500 text-xl">Error: {error}</div>
          </div>
        );
      }
      // Get health color
      const getHealthColor = (score: number): string => {
        if (score >= 80) return 'text-green-400';
        if (score >= 60) return 'text-blue-400';
        if (score >= 40) return 'text-yellow-400';
        if (score >= 20) return 'text-orange-400';
        return 'text-red-400';
      };
      // Get phi color
      const getPhiColor = (score: number): string => {
        if (score >= 0.7) return 'text-green-400';
        if (score >= 0.5) return 'text-blue-400';
        if (score >= 0.3) return 'text-yellow-400';
        return 'text-red-400';
      };
      return (
        <div className="w-full h-screen flex">
          {/* Metrics Overlay Panel */}
          {showMetrics && (
            <div className="absolute top-4 left-4 z-50 w-80 bg-gray-800 border border-gray-700 rounded-lg shadow-xl p-4 max-h-[80vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-white font-bold">Swarm Metrics</h3>
                <button
                  onClick={() => setShowMetrics(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>
                        {metricsLoading && !swarmHealth && (
                <div className="text-center text-gray-400 py-4">Loading metrics...</div>
              )}
                        {swarmHealth && (
                <div className="space-y-4">
                  {/* Overall Health */}
                  <div className="bg-gray-900 rounded-lg p-3">
                    <div className="text-gray-400 text-xs uppercase mb-1">Overall Health</div>
                    <div className={`text-3xl font-bold ${getHealthColor(swarmHealth.overall_health_score)}`}>
                      {swarmHealth.overall_health_score.toFixed(1)}
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2 mt-2">
                      <div
                        className={`h-2 rounded-full ${
                          swarmHealth.overall_health_score >= 80 ? 'bg-green-500' :
                          swarmHealth.overall_health_score >= 60 ? 'bg-blue-500' :
                          swarmHealth.overall_health_score >= 40 ? 'bg-yellow-500' :
                          'bg-red-500'
                        }`}
                        style={{ width: `${swarmHealth.overall_health_score}%` }}
                      />
                    </div>
                  </div>
                                {/* Agent Stats */}
                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-gray-900 rounded-lg p-2">
                      <div className="text-gray-400 text-xs">Total Agents</div>
                      <div className="text-white font-bold">{swarmHealth.total_agents}</div>
                    </div>
                    <div className="bg-gray-900 rounded-lg p-2">
                      <div className="text-gray-400 text-xs">Active</div>
                      <div className="text-green-400 font-bold">{swarmHealth.active_agents}</div>
                    </div>
                  </div>
                                {/* Task Stats */}
                  <div className="bg-gray-900 rounded-lg p-3">
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="text-gray-400 text-xs">Tasks</div>
                        <div className="text-white">
                          <span className="text-green-400">{swarmHealth.total_tasks_completed}</span>
                          <span className="text-gray-500 mx-1">/</span>
                          <span className="text-red-400">{swarmHealth.total_tasks_failed}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                                {/* Consciousness Metrics */}
                  {consciousnessMetrics && (
                    <>
                      <div className="border-t border-gray-700 pt-3">
                        <div className="text-gray-400 text-xs uppercase mb-2">Consciousness</div>
                        <div className="bg-gray-900 rounded-lg p-3">
                          <div className="text-gray-400 text-xs mb-1">Avg Phi (IIT)</div>
                          <div className={`text-2xl font-bold ${getPhiColor(consciousnessMetrics.phi_avg)}`}>
                            {consciousnessMetrics.phi_avg.toFixed(4)}
                          </div>
                        </div>
                        <div className="bg-gray-900 rounded-lg p-3 mt-2">
                          <div className="text-gray-400 text-xs mb-1">Free Energy (FEP)</div>
                          <div className="text-green-400 text-xl font-bold">
                            {consciousnessMetrics.free_energy_avg.toFixed(4)}
                          </div>
                        </div>
                        <div className="bg-gray-900 rounded-lg p-3 mt-2">
                          <div className="text-gray-400 text-xs mb-1">Integration</div>
                          <div className="text-blue-400 font-bold capitalize">
                            {consciousnessMetrics.integration_level.replace('_', ' ')}
                          </div>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          )}
          {/* Node Palette */}
          {showPalette && (
            <div className="w-64 bg-gray-800 border-r border-gray-700 p-4 overflow-y-auto">
              <div className="text-white font-bold mb-4">Node Palette</div>
              {NODE_PALETTE.map((category) => (
                <div key={category.category} className="mb-4">
                  <div className="text-gray-400 text-sm font-semibold mb-2">
                    {category.category}
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {category.nodes.map((nodeConfig) => (
                      <button
                        key={nodeConfig.type}
                        draggable
                        onDragStart={(event) => {
                          const type = nodeConfig.type;
                          const position = {
                            x: event.clientX - 100,
                            y: event.clientY - 50,
                          };
                          addNode(type, position);
                        }}
                        className="flex items-center gap-2 p-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                        title={nodeConfig.label}
                      >
                        <span className="text-2xl">{nodeConfig.icon}</span>
                        <span className="text-sm">{nodeConfig.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
          {/* Toolbar */}
          <div className="flex-1 bg-gray-800 border-r border-gray-700 p-4">
            <button
              onClick={() => setShowMetrics(!showMetrics)}
              className={`p-2 rounded-lg transition-colors ${
                showMetrics ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-700 hover:bg-gray-600'
              }`}
              title="Toggle Metrics Overlay"
            >
              📊
            </button>
            <button
              onClick={() => setShowPalette(!showPalette)}
              className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
              title="Toggle Node Palette"
            >
              {showPalette ? '📋' : '📋'}
            </button>
            <button
              onClick={() => {
                if (currentWorkflow) {
                  saveWorkflow(currentWorkflow);
                } else {
                  const newWorkflow: Workflow = {
                    id: `workflow-${Date.now()}`,
                    name: `Workflow ${savedWorkflows.length + 1}`,
                    description: 'New workflow',
                    nodes,
                    edges,
                    createdAt: new Date().toISOString(),
                    updatedAt: new Date().toISOString(),
                  };
                  setCurrentWorkflow(newWorkflow);
                }
              }}
              disabled={!nodes.length}
              className="p-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Save Workflow"
            >
              💾
            </button>
            <button
              onClick={() => {
                if (currentWorkflow) {
                  setCurrentWorkflow(null);
                  setNodes([]);
                  setEdges([]);
                } else {
                  setCurrentWorkflow(null);
                }
              }}
              disabled={!currentWorkflow}
              className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Clear Workflow"
            >
              🗑️
            </button>
            <button
              onClick={() => setShowExecution(!showExecution)}
              disabled={!currentWorkflow || nodes.length === 0}
              className="p-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Execute Workflow"
            >
              ▶️
            </button>
          </div>
          {/* ReactFlow Canvas */}
          <div className="flex-1 bg-gray-900">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={{
                agentNode: AgentNode,
                triadNode: AgentNode,
                historianNode: AgentNode,
                toolNode: AgentNode,
                memoryNode: AgentNode,
                ragNode: AgentNode,
                conditionNode: AgentNode,
                loopNode: AgentNode,
                handoffNode: AgentNode,
                mergeNode: AgentNode,
                discordNode: AgentNode,
                telegramNode: AgentNode,
                webhookNode: AgentNode,
              }}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              onNodeDragStop={(event, node) => {
                // Update node position
                setNodes((nds) =>
                  nds.map((n) =>
                    n.id === node.id ? { ...n, position: node.position } : n
                  )
                );
              }}
              fitView
              className="bg-gray-900"
            >
              <Background color="#1a1a2a" gap={20} />
              <Controls className="bg-gray-800 border-gray-700" />
              <MiniMap
                nodeColor={(node) => {
                  const status = (node.data as AgentData)?.status;
                  switch (status) {
                    case 'idle': return NODE_COLORS.agent;
                    case 'thinking': return NODE_COLORS.triad;
                    case 'acting': return NODE_COLORS.historian;
                    default: return '#6B7280';
                  }
                }}
                className="bg-gray-800 border-gray-700"
                maskColor="rgba(0, 0, 0, 0.5)"
              />
            </ReactFlow>
            {/* Workflow Execution Panel */}
            {showExecution && (
              <div className="absolute top-4 right-4 w-96 bg-gray-800 border-l border-gray-700 rounded-lg p-4 shadow-xl">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-white text-lg font-bold">Workflow Execution</h3>
                  <button
                    onClick={() => setShowExecution(false)}
                    className="text-gray-400 hover:text-white"
                  >
                    ✕
                  </button>
                </div>
                            {executionState.status === 'running' && (
                  <div className="mb-4">
                    <div className="text-gray-400 text-sm mb-1">
                      Status: <span className="text-green-400 font-semibold">Running</span>
                    </div>
                    {executionState.currentNode && (
                      <div className="text-gray-400 text-sm mb-1">
                        Current Node: {executionState.currentNode}
                      </div>
                    )}
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-green-600 h-2 rounded-full"
                        style={{ width: `${executionState.progress}%` }}
                      />
                    </div>
                    <div className="text-gray-400 text-sm mt-1">
                      {executionState.message}
                    </div>
                  </div>
                )}
                            {executionState.status === 'completed' && (
                  <div className="text-center">
                    <div className="text-6xl mb-4">✅</div>
                    <div className="text-white text-lg">Workflow Completed Successfully</div>
                  </div>
                )}
                            {executionState.status === 'error' && (
                  <div className="text-center">
                    <div className="text-6xl mb-4">❌</div>
                    <div className="text-red-500 text-lg">{executionState.message}</div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      );
    }
    ```
    **Category:** Anti-pattern
    **Severity:** minor

84. **`EnhancedCanvas` has a cyclomatic complexity of 20 with "high" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`
    **Line:** 174
    ```typescript
    // Enhanced Canvas Component
    // =============================================================================
    
    export function EnhancedCanvas() {
      const [nodes, setNodes, onNodesChange] = useNodesState([]);
      const [edges, setEdges, onEdgesChange] = useEdgesState([]);
      const [selectedNode, setSelectedNode] = useState<Node | null>(null);
    ```
    **Category:** Anti-pattern
    **Severity:** minor

85. **Expected to return a value at the end of arrow function** (`JS-0045`)
    **File:** `dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`
    **Line:** 377
    ```typescript
    }, [fetchAgents]);
    
      // Poll for metrics updates when metrics panel is open
      useEffect(() => {
        if (showMetrics) {
          fetchMetrics();
          const interval = setInterval(fetchMetrics, 5000);
    ```
    **Category:** Anti-pattern
    **Severity:** minor

86. **JSX tree is too deeply nested. Found 6 levels of nesting** (`JS-0415`)
    **File:** `dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`
    **Line:** 438
    ```typescript
    )}
              
              {swarmHealth && (
                <div className="space-y-4">
                  {/* Overall Health */}
                  <div className="bg-gray-900 rounded-lg p-3">
                    <div className="text-gray-400 text-xs uppercase mb-1">Overall Health</div>
    ```
    **Category:** Anti-pattern
    **Severity:** minor

87. **Function has a cyclomatic complexity of 6 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`
    **Line:** 261
    ```typescript
    }, [setCurrentWorkflow, setNodes, setEdges]);
    
      // Execute workflow
      const executeWorkflow = useCallback(async () => {
        if (!currentWorkflow) return;
        
        setIsExecuting(true);
    ```
    **Category:** Anti-pattern
    **Severity:** minor

88. **'ConditionNode' is defined but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`
    **Line:** 31
    ```typescript
    import 'reactflow/dist/style.css';
    
    import { AgentNode, AgentData } from './AgentNode';
    import type { AgentNode as AgentNodeType, TriadNode, HistorianNode, ToolNode, MemoryNode, RAGNode, ConditionNode, LoopNode, HandoffNode, MergeNode, DiscordNode, TelegramNode, WebhookNode } from '../types/reactflow';
    
    // Metrics overlay types
    interface SwarmHealthMetrics {
    ```
    **Category:** Performance
    **Severity:** major

89. **'setWorkflows' is assigned a value but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`
    **Line:** 178
    ```typescript
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
      const [edges, setEdges, onEdgesChange] = useEdgesState([]);
      const [selectedNode, setSelectedNode] = useState<Node | null>(null);
      const [workflows, setWorkflows] = useState<Workflow[]>([]);
      const [currentWorkflow, setCurrentWorkflow] = useState<Workflow | null>(null);
      const [executionState, setExecutionState] = useState<ExecutionState>({
        status: 'idle',
    ```
    **Category:** Performance
    **Severity:** major

90. **Fragments should contain more than one child - otherwise, there’s no need for a Fragment at all** (`JS-0424`)
    **File:** `dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`
    **Line:** 486-508
    ```typescript
    {/* Consciousness Metrics */}
                  {consciousnessMetrics && (
                    <>
                      <div className="border-t border-gray-700 pt-3">
                        <div className="text-gray-400 text-xs uppercase mb-2">Consciousness</div>
                        <div className="bg-gray-900 rounded-lg p-3">
                          <div className="text-gray-400 text-xs mb-1">Avg Phi (IIT)</div>
                          <div className={`text-2xl font-bold ${getPhiColor(consciousnessMetrics.phi_avg)}`}>
                            {consciousnessMetrics.phi_avg.toFixed(4)}
                          </div>
                        </div>
                        <div className="bg-gray-900 rounded-lg p-3 mt-2">
                          <div className="text-gray-400 text-xs mb-1">Free Energy (FEP)</div>
                          <div className="text-green-400 text-xl font-bold">
                            {consciousnessMetrics.free_energy_avg.toFixed(4)}
                          </div>
                        </div>
                        <div className="bg-gray-900 rounded-lg p-3 mt-2">
                          <div className="text-gray-400 text-xs mb-1">Integration</div>
                          <div className="text-blue-400 font-bold capitalize">
                            {consciousnessMetrics.integration_level.replace('_', ' ')}
                          </div>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              )}
    ```
    **Category:** Anti-pattern
    **Severity:** major

91. **'executeWorkflow' is assigned a value but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`
    **Line:** 261
    ```typescript
    }, [setCurrentWorkflow, setNodes, setEdges]);
    
      // Execute workflow
      const executeWorkflow = useCallback(async () => {
        if (!currentWorkflow) return;
        
        setIsExecuting(true);
    ```
    **Category:** Performance
    **Severity:** major

92. **'RAGNode' is defined but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`
    **Line:** 31
    ```typescript
    import 'reactflow/dist/style.css';
    
    import { AgentNode, AgentData } from './AgentNode';
    import type { AgentNode as AgentNodeType, TriadNode, HistorianNode, ToolNode, MemoryNode, RAGNode, ConditionNode, LoopNode, HandoffNode, MergeNode, DiscordNode, TelegramNode, WebhookNode } from '../types/reactflow';
    
    // Metrics overlay types
    interface SwarmHealthMetrics {
    ```
    **Category:** Performance
    **Severity:** major

93. **'loadWorkflow' is assigned a value but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`
    **Line:** 246
    ```typescript
    }, [savedWorkflows, setCurrentWorkflow]);
    
      // Load workflow
      const loadWorkflow = useCallback(async (workflowId: string) => {
        try {
          const response = await fetch(`${API_URL}/api/workflows/${workflowId}`);
          if (!response.ok) throw new Error('Failed to load workflow');
    ```
    **Category:** Performance
    **Severity:** major

94. **'HandoffNode' is defined but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`
    **Line:** 31
    ```typescript
    import 'reactflow/dist/style.css';
    
    import { AgentNode, AgentData } from './AgentNode';
    import type { AgentNode as AgentNodeType, TriadNode, HistorianNode, ToolNode, MemoryNode, RAGNode, ConditionNode, LoopNode, HandoffNode, MergeNode, DiscordNode, TelegramNode, WebhookNode } from '../types/reactflow';
    
    // Metrics overlay types
    interface SwarmHealthMetrics {
    ```
    **Category:** Performance
    **Severity:** major

95. **'selectedNode' is assigned a value but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`
    **Line:** 177
    ```typescript
    export function EnhancedCanvas() {
      const [nodes, setNodes, onNodesChange] = useNodesState([]);
      const [edges, setEdges, onEdgesChange] = useEdgesState([]);
      const [selectedNode, setSelectedNode] = useState<Node | null>(null);
      const [workflows, setWorkflows] = useState<Workflow[]>([]);
      const [currentWorkflow, setCurrentWorkflow] = useState<Workflow | null>(null);
      const [executionState, setExecutionState] = useState<ExecutionState>({
    ```
    **Category:** Performance
    **Severity:** major

96. **'MergeNode' is defined but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`
    **Line:** 31
    ```typescript
    import 'reactflow/dist/style.css';
    
    import { AgentNode, AgentData } from './AgentNode';
    import type { AgentNode as AgentNodeType, TriadNode, HistorianNode, ToolNode, MemoryNode, RAGNode, ConditionNode, LoopNode, HandoffNode, MergeNode, DiscordNode, TelegramNode, WebhookNode } from '../types/reactflow';
    
    // Metrics overlay types
    interface SwarmHealthMetrics {
    ```
    **Category:** Performance
    **Severity:** major

97. **'MemoryNode' is defined but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`
    **Line:** 31
    ```typescript
    import 'reactflow/dist/style.css';
    
    import { AgentNode, AgentData } from './AgentNode';
    import type { AgentNode as AgentNodeType, TriadNode, HistorianNode, ToolNode, MemoryNode, RAGNode, ConditionNode, LoopNode, HandoffNode, MergeNode, DiscordNode, TelegramNode, WebhookNode } from '../types/reactflow';
    
    // Metrics overlay types
    interface SwarmHealthMetrics {
    ```
    **Category:** Performance
    **Severity:** major

98. **'workflows' is assigned a value but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`
    **Line:** 178
    ```typescript
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
      const [edges, setEdges, onEdgesChange] = useEdgesState([]);
      const [selectedNode, setSelectedNode] = useState<Node | null>(null);
      const [workflows, setWorkflows] = useState<Workflow[]>([]);
      const [currentWorkflow, setCurrentWorkflow] = useState<Workflow | null>(null);
      const [executionState, setExecutionState] = useState<ExecutionState>({
        status: 'idle',
    ```
    **Category:** Performance
    **Severity:** major

99. **'ToolNode' is defined but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`
    **Line:** 31
    ```typescript
    import 'reactflow/dist/style.css';
    
    import { AgentNode, AgentData } from './AgentNode';
    import type { AgentNode as AgentNodeType, TriadNode, HistorianNode, ToolNode, MemoryNode, RAGNode, ConditionNode, LoopNode, HandoffNode, MergeNode, DiscordNode, TelegramNode, WebhookNode } from '../types/reactflow';
    
    // Metrics overlay types
    interface SwarmHealthMetrics {
    ```
    **Category:** Performance
    **Severity:** major

100. **'TelegramNode' is defined but never used** (`JS-0356`)
     **File:** `dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`
     **Line:** 31
     ```typescript
     import 'reactflow/dist/style.css';
     
     import { AgentNode, AgentData } from './AgentNode';
     import type { AgentNode as AgentNodeType, TriadNode, HistorianNode, ToolNode, MemoryNode, RAGNode, ConditionNode, LoopNode, HandoffNode, MergeNode, DiscordNode, TelegramNode, WebhookNode } from '../types/reactflow';
     
     // Metrics overlay types
     interface SwarmHealthMetrics {
     ```
     **Category:** Performance
     **Severity:** major

*...and 405 more occurrences. [See full list on DeepSource](https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/6ce83273-62c5-44e0-9536-f18b5e832267/).*### Docker
**Status:** Failure
**Findings:** 5 new issues

1. **`useradd` without flag `-l` and high UID will result in excessively large Image.** (`DOK-P1004`)
   **File:** `docker/Dockerfile`
   **Line:** 35
   ```
   FROM python:3.13-slim as production
   
   # Create non-root user
   RUN useradd -m -s /bin/bash -u heretekNone
   
   # Install runtime dependencies
   RUN apt-get update && apt-get install -y --no-install-recommends \
   ```
   **Category:** Performance
   **Severity:** minor

2. **Pin versions in apt get install. Instead of `apt-get install <package>` use `apt-get install <package>=<version>`** (`DOK-DL3008`)
   **File:** `docker/Dockerfile`
   **Line:** 8
   ```
   FROM python:3.13-slim as base
   
   # Install system dependencies
   RUN apt-get update && apt-get install -y --no-install-recommends \
       gcc \
       g++ \
       curl \
   ```
   **Category:** Bug risk
   **Severity:** major

3. **Pin versions in apt get install. Instead of `apt-get install <package>` use `apt-get install <package>=<version>`** (`DOK-DL3008`)
   **File:** `docker/Dockerfile`
   **Line:** 38
   ```
   RUN useradd -m -s /bin/bash -u heretek
   
   # Install runtime dependencies
   RUN apt-get update && apt-get install -y --no-install-recommends \
       curl \
       && rm -rf /var/lib/apt/lists/*
   ```
   **Category:** Bug risk
   **Severity:** major

4. **Avoid use of cache directory with pip. Use `pip install --no-cache-dir <package>`** (`DOK-P1003`)
   **File:** `Dockerfile`
   **Line:** 26
   ```
   # Install the package in development mode
   COPY src/ ./src/
   RUN pip install -e .None
   
   # =============================================================================
   # Stage 2: Runtime
   ```
   **Category:** Performance
   **Severity:** minor

5. **Pin versions in apt get install. Instead of `apt-get install <package>` use `apt-get install <package>=<version>`** (`DOK-DL3008`)
   **File:** `Dockerfile`
   **Line:** 12
   ```
   WORKDIR /app
   
   # Install system dependencies
   RUN apt-get update && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       && rm -rf /var/lib/apt/lists/*
   ```
   **Category:** Bug risk
   **Severity:** major
### SQL
**Status:** Success
**Findings:** No new issues detected

# DeepSource Code Review Report

**Repository:** Heretek-AI/heretek-swarm
**Branch:** `main`
**Commit:** 0f4686a...eaf8b52
**Run:** [https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/18c4f891-816a-4a30-b173-84e564f0231f/](https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/18c4f891-816a-4a30-b173-84e564f0231f/)

---

## Summary
- **Shell:** No issues detected- **SQL:** No issues detected- **JavaScript:** 66 issues- **Python:** 180 issues- **Secrets:** 12 issues- **Docker:** No issues detected

---

## Code Review Findings
### Shell
**Status:** Success
**Findings:** No new issues detected
### SQL
**Status:** Success
**Findings:** No new issues detected
### JavaScript
**Status:** Failure
**Findings:** 61 new issues

1. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
   **File:** `dashboard/frontend/src/App.tsx`
   **Line:** 51-221
   ```typescript
   { id: 'settings', label: 'Settings', icon: '⚙️' },
   ];
   
   function DashboardContent() {
     const [currentView, setCurrentView] = useState<View>('home');
     const [systemStatus, setSystemStatus] = useState<'healthy' | 'degraded' | 'offline'>('healthy');
     const toast = useToast();
       // Setup store integration
     const {
        isConfigured,
        isRerunning,
       config,
       setRerunning,
       resetSetup,
     } = useSetupStore();
       const [showSetup, setShowSetup] = useState(false);
     const [isInitialized, setIsInitialized] = useState(false);
     // Check if setup is needed on mount
     useEffect(() => {
       const checkConfiguration = () => {
         const storedConfigured = localStorage.getItem('swarm_configured') === 'true';
         const storedApiHost = localStorage.getItem('swarm_api_host');
               if (!storedConfigured || !storedApiHost) {
           // Not configured or no stored API host - show setup
           setShowSetup(true);
         } else {
           // Restore config from localStorage if not in store
           if (!config.apiHost) {
             useSetupStore.getState().setConfig({
               apiHost: storedApiHost,
               apiKey: localStorage.getItem('swarm_api_key') || '',
               wsHost: localStorage.getItem('swarm_ws_host') || '',
             });
           }
           setShowSetup(false);
         }
         setIsInitialized(true);
       };
           checkConfiguration();
     }, []);
     // Set toast instance for API client
     useEffect(() => {
       setToastInstance({
         error: (title, message) => toast.error(title, message),
       });
     }, [toast]);
     // Check system health periodically
     const checkSystemHealth = useCallback(async () => {
       try {
         // Use stored API host or fall back to environment variable
         const apiHost = localStorage.getItem('swarm_api_host') || import.meta.env.VITE_API_URL || '';
         if (!apiHost) {
           setSystemStatus('offline');
           return;
         }
               const response = await fetch(`${apiHost}/api/health`);
         if (!response.ok) {
           setSystemStatus('offline');
           return;
         }
         const data = await response.json();
               const isHealthy =
            data.gateway?.status === 'healthy' &&
           data.redis?.status === 'healthy' &&
           data.postgres?.status === 'healthy' &&
           data.qdrant?.status === 'healthy';
               const isDegraded =
            data.gateway?.status === 'healthy' ||
           data.redis?.status === 'healthy' ||
           data.postgres?.status === 'healthy' ||
           data.qdrant?.status === 'healthy';
               setSystemStatus(isHealthy ? 'healthy' : isDegraded ? 'degraded' : 'offline');
       } catch {
         setSystemStatus('offline');
       }
     }, []);
     useEffect(() => {
       // Only check health if not showing setup
       if (!showSetup && isInitialized) {
         checkSystemHealth();
         const interval = setInterval(checkSystemHealth, 30000); // Check every 30 seconds
         return () => clearInterval(interval);
       }
     }, [checkSystemHealth, showSetup, isInitialized]);
     const handleNavClick = useCallback((navId: string) => {
       setCurrentView(navId as View);
     }, []);
     // Handle setup completion
     const handleSetupComplete = useCallback(() => {
       setShowSetup(false);
       // Trigger health check after setup
       setTimeout(checkSystemHealth, 1000);
     }, [checkSystemHealth]);
     // Handle re-running setup from settings
     const handleRerunSetup = useCallback(() => {
       resetSetup();
       setRerunning(true);
       setShowSetup(true);
     }, [resetSetup, setRerunning]);
     const renderView = () => {
       switch (currentView) {
         case 'home':
           return <HomePage />;
         case 'agents':
           return <AgentsPage />;
         case 'consciousness':
           return <ConsciousnessPage />;
         case 'workflows':
           return <WorkflowBuilder />;
         case 'logs':
           return <LogsPage />;
         case 'settings':
           return <SettingsPage onRerunSetup={handleRerunSetup} />;
         // Legacy views
         case 'legacy-dashboard':
           return <Dashboard />;
         case 'legacy-canvas':
           return <CollectiveCanvas />;
         case 'legacy-observability':
           return <Observability />;
         case 'legacy-chat':
           return <ChatInterface />;
         default:
           return <HomePage />;
       }
     };
     // Don't render until we've checked configuration
     if (!isInitialized) {
       return (
         <div className="min-h-screen bg-gray-950 flex items-center justify-center">
           <div className="text-center">
             <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
             <p className="mt-4 text-gray-400">Loading...</p>
           </div>
         </div>
       );
     }
     return (
       <>
         {showSetup ? (
           <SetupWizard onComplete={handleSetupComplete} />
         ) : (
           <DashboardLayout
             activeNav={currentView}
             onNavClick={handleNavClick}
             navItems={navItems}
             systemStatus={systemStatus}
           >
             <ErrorBoundary>
               {renderView()}
             </ErrorBoundary>
           </DashboardLayout>
         )}
       </>
     );
   }
   
   function App() {
     return (
   ```
   **Category:** Anti-pattern
   **Severity:** minor

2. **`renderView` has a cyclomatic complexity of 11 with "medium" risk** (`JS-R1005`)
   **File:** `dashboard/frontend/src/App.tsx`
   **Line:** 163
   ```typescript
   setShowSetup(true);
     }, [resetSetup, setRerunning]);
   
     const renderView = () => {
       switch (currentView) {
         case 'home':
           return <HomePage />;
   ```
   **Category:** Anti-pattern
   **Severity:** minor

3. **Function has a cyclomatic complexity of 14 with "medium" risk** (`JS-R1005`)
   **File:** `dashboard/frontend/src/App.tsx`
   **Line:** 102
   ```typescript
   }, [toast]);
   
     // Check system health periodically
     const checkSystemHealth = useCallback(async () => {
       try {
         // Use stored API host or fall back to environment variable
         const apiHost = localStorage.getItem('swarm_api_host') || import.meta.env.VITE_API_URL || '';
   ```
   **Category:** Anti-pattern
   **Severity:** minor

4. **Expected to return a value at the end of arrow function** (`JS-0045`)
   **File:** `dashboard/frontend/src/App.tsx`
   **Line:** 136
   ```typescript
   }
     }, []);
   
     useEffect(() => {
       // Only check health if not showing setup
       if (!showSetup && isInitialized) {
         checkSystemHealth();
   ```
   **Category:** Anti-pattern
   **Severity:** minor

5. **`checkConfiguration` has a cyclomatic complexity of 6 with "medium" risk** (`JS-R1005`)
   **File:** `dashboard/frontend/src/App.tsx`
   **Line:** 70
   ```typescript
   // Check if setup is needed on mount
     useEffect(() => {
       const checkConfiguration = () => {
         const storedConfigured = localStorage.getItem('swarm_configured') === 'true';
         const storedApiHost = localStorage.getItem('swarm_api_host');
   ```
   **Category:** Anti-pattern
   **Severity:** minor

6. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
   **File:** `dashboard/frontend/src/App.tsx`
   **Line:** 223-232
   ```typescript
   );
   }
   
   function App() {
     return (
       <ToastProvider>
         <DashboardContent />
         {/* Debug features - only visible when Developer Mode is enabled */}
         <DebugPanel />
         <PerformanceOverlay position="top-right" />
       </ToastProvider>
     );
   }
   
   export default App;
   ```
   **Category:** Anti-pattern
   **Severity:** minor

7. **Fragments should contain more than one child - otherwise, there’s no need for a Fragment at all** (`JS-0424`)
   **File:** `dashboard/frontend/src/App.tsx`
   **Line:** 204-219
   ```typescript
   }
   
     return (
       <>
         {showSetup ? (
           <SetupWizard onComplete={handleSetupComplete} />
         ) : (
           <DashboardLayout
             activeNav={currentView}
             onNavClick={handleNavClick}
             navItems={navItems}
             systemStatus={systemStatus}
           >
             <ErrorBoundary>
               {renderView()}
             </ErrorBoundary>
           </DashboardLayout>
         )}
       </>
     );
   }
   ```
   **Category:** Anti-pattern
   **Severity:** major

8. **'isConfigured' is assigned a value but never used** (`JS-0356`)
   **File:** `dashboard/frontend/src/App.tsx`
   **Line:** 58
   ```typescript
   // Setup store integration
     const { 
       isConfigured,
        isRerunning,
       config,
       setRerunning,
   ```
   **Category:** Performance
   **Severity:** major

9. **'isRerunning' is assigned a value but never used** (`JS-0356`)
   **File:** `dashboard/frontend/src/App.tsx`
   **Line:** 59
   ```typescript
   // Setup store integration
     const { 
       isConfigured, 
       isRerunning,
       config,
       setRerunning,
       resetSetup,
   ```
   **Category:** Performance
   **Severity:** major

10. **Parsing error: ';' expected** (`JS-0833`)
    **File:** `dashboard/frontend/src/components/Canvas/FlowCanvas.tsx`
    **Line:** 235
    ```typescript
    const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });
        const agentInfo = AGENT_REGISTRY[agentType as AgentType];
            agentName: agentInfo.name,
            description: agentInfo.description,
            llmModel: agentInfo.defaultLlmModel,
            llmProvider: 'openai',
            status: 'idle',
    ```
    **Category:** Bug risk
    **Severity:** minor

11. **Parsing error: ',' expected** (`JS-0833`)
    **File:** `dashboard/frontend/src/components/Observability/A2ATracker.tsx`
    **Line:** 96
    ```typescript
    subject: MESSAGE_SUBJECTS[Math.floor(Math.random() * MESSAGE_SUBJECTS.length)],
        type: ['task', 'response', 'broadcast', 'heartbeat', 'consensus'][Math.floor(Math.random() * 5)] as A2AMessage['type'],
        payload: {
          task sample: Math.random() },
        },
        latencyMs: Math.floor(Math.random() * 500) + 10,
        status: ['sent', 'delivered', 'failed', 'pending'][Math.floor(Math.random() * 4)] as A2AMessage['status'],
    ```
    **Category:** Bug risk
    **Severity:** minor

12. **`ProviderCard` has a cyclomatic complexity of 10 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/Settings/ModelGarage.tsx`
    **Line:** 171-178
    ```typescript
    };
    
    // Components
    const ProviderCard: React.FC<{
      provider: LLMProvider;
      onEdit: (provider: LLMProvider) => void;
      onTest: (id: string) => void;
      onToggle: (id: string) => void;
      onDelete: (id: string) => void;
      isTesting: boolean;
    }> = ({ provider, onEdit, onTest, onToggle, onDelete, isTesting }) => {
      const config = LLM_PROVIDER_CONFIGS[provider.type];
      
      const getStatusColor = () => {
    ```
    **Category:** Anti-pattern
    **Severity:** minor

13. **Unexpected confirm** (`JS-0052`)
    **File:** `dashboard/frontend/src/components/Settings/ModelGarage.tsx`
    **Line:** 651
    ```typescript
    }, []);
    
      const handleDeleteEmbedding = useCallback((id: string) => {
        if (confirm('Are you sure you want to delete this provider?')) {
          setEmbeddingProviders((prev) => prev.filter((p) => p.id !== id));
        }
      }, []);
    ```
    **Category:** Anti-pattern
    **Severity:** minor

14. **JSX tree is too deeply nested. Found 5 levels of nesting** (`JS-0415`)
    **File:** `dashboard/frontend/src/components/Settings/ModelGarage.tsx`
    **Line:** 191
    ```typescript
    };
    
      return (
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-gray-600 transition-colors">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: config?.color || '#6366f1' }}>
    ```
    **Category:** Anti-pattern
    **Severity:** minor

15. **Unexpected confirm** (`JS-0052`)
    **File:** `dashboard/frontend/src/components/Settings/ModelGarage.tsx`
    **Line:** 645
    ```typescript
    }, []);
    
      const handleDeleteLlm = useCallback((id: string) => {
        if (confirm('Are you sure you want to delete this provider?')) {
          setLlmProviders((prev) => prev.filter((p) => p.id !== id));
        }
      }, []);
    ```
    **Category:** Anti-pattern
    **Severity:** minor

16. **Remove redundant `undefined` from function call** (`JS-W1042`)
    **File:** `dashboard/frontend/src/components/Settings/ModelGarage.tsx`
    **Line:** 599
    ```typescript
    setLlmProviders((prev) => [...prev, provider as LLMProvider]);
        }
        setShowLlmForm(false);
        setEditingLlmProvider(undefined);
      }, [editingLlmProvider]);
    
      const handleSaveEmbeddingProvider = useCallback((provider: Partial<EmbeddingProvider>) => {
    ```
    **Category:** Anti-pattern
    **Severity:** minor

17. **Remove redundant `undefined` from function call** (`JS-W1042`)
    **File:** `dashboard/frontend/src/components/Settings/ModelGarage.tsx`
    **Line:** 609
    ```typescript
    setEmbeddingProviders((prev) => [...prev, provider as EmbeddingProvider]);
        }
        setShowEmbeddingForm(false);
        setEditingEmbeddingProvider(undefined);
      }, [editingEmbeddingProvider]);
    
      const handleTestLlm = useCallback(async (id: string) => {
    ```
    **Category:** Anti-pattern
    **Severity:** minor

18. **`ProviderForm` has a cyclomatic complexity of 10 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/Settings/ModelGarage.tsx`
    **Line:** 259-263
    ```typescript
    );
    };
    
    const ProviderForm: React.FC<{
      provider?: LLMProvider;
      onSave: (provider: Partial<LLMProvider>) => void;
      onCancel: () => void;
    }> = ({ provider, onSave, onCancel }) => {
      const [formData, setFormData] = useState<{
        name: string;
        type: ProviderType;
    ```
    **Category:** Anti-pattern
    **Severity:** minor

19. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Settings/ModelGarage.tsx`
    **Line:** 491-831
    ```typescript
    };
    
    // Main Component
    export function ModelGarage() {
      const [llmProviders, setLlmProviders] = useState<LLMProvider[]>([]);
      const [embeddingProviders, setEmbeddingProviders] = useState<EmbeddingProvider[]>([]);
      const [activeTab, setActiveTab] = useState<'llm' | 'embedding'>('llm');
      const [showLlmForm, setShowLlmForm] = useState(false);
      const [showEmbeddingForm, setShowEmbeddingForm] = useState(false);
      const [editingLlmProvider, setEditingLlmProvider] = useState<LLMProvider | undefined>();
      const [editingEmbeddingProvider, setEditingEmbeddingProvider] = useState<EmbeddingProvider | undefined>();
      const [testingId, setTestingId] = useState<string | null>(null);
      const [globalStats, setGlobalStats] = useState({
        totalRequests: 0,
        totalTokens: 0,
        avgLatency: 0,
        costEstimate: 0,
      });
      // Load providers from localStorage
      useEffect(() => {
        const savedLlm = localStorage.getItem('heretek-llm-providers');
        const savedEmbedding = localStorage.getItem('heretek-embedding-providers');
            if (savedLlm) {
          try {
            setLlmProviders(JSON.parse(savedLlm));
          } catch (e) {
            console.error('Failed to parse LLM providers:', e);
          }
        } else {
          // Add default providers
          setLlmProviders([
            {
              id: 'default-openai',
              name: 'OpenAI',
              type: 'openai',
              baseUrl: 'https://api.openai.com/v1',
              models: LLM_PROVIDER_CONFIGS.openai.models,
              selectedModel: 'gpt-4o-mini',
              isEnabled: true,
              isDefault: true,
              healthStatus: 'unknown',
            },
            {
              id: 'default-ollama',
              name: 'Ollama (Local)',
              type: 'ollama',
              baseUrl: 'http://localhost:11434',
              models: LLM_PROVIDER_CONFIGS.ollama.models,
              selectedModel: 'llama3.1',
              isEnabled: true,
              isDefault: false,
              healthStatus: 'unknown',
            },
          ]);
        }
        if (savedEmbedding) {
          try {
            setEmbeddingProviders(JSON.parse(savedEmbedding));
          } catch (e) {
            console.error('Failed to parse embedding providers:', e);
          }
        } else {
          setEmbeddingProviders([
            {
              id: 'default-embed-openai',
              name: 'OpenAI Embeddings',
              type: 'openai',
              baseUrl: 'https://api.openai.com/v1',
              model: 'text-embedding-3-small',
              dimensions: 1536,
              isEnabled: true,
              isDefault: true,
              healthStatus: 'unknown',
            },
          ]);
        }
      }, []);
      // Save providers to localStorage
      useEffect(() => {
        if (llmProviders.length > 0) {
          localStorage.setItem('heretek-llm-providers', JSON.stringify(llmProviders));
        }
        if (embeddingProviders.length > 0) {
          localStorage.setItem('heretek-embedding-providers', JSON.stringify(embeddingProviders));
        }
      }, [llmProviders, embeddingProviders]);
      // Simulate stats updates
      useEffect(() => {
        const interval = setInterval(() => {
          setGlobalStats((prev) => ({
            totalRequests: prev.totalRequests + Math.floor(Math.random() * 10),
            totalTokens: prev.totalTokens + Math.floor(Math.random() * 1000),
            avgLatency: Math.floor(Math.random() * 100) + 50,
            costEstimate: prev.costEstimate + Math.random() * 0.5,
          }));
        }, 3000);
        return () => clearInterval(interval);
      }, []);
      const handleSaveLlmProvider = useCallback((provider: Partial<LLMProvider>) => {
        if (editingLlmProvider) {
          setLlmProviders((prev) => prev.map((p) => (p.id === provider.id ? { ...p, ...provider } as LLMProvider : p)));
        } else {
          setLlmProviders((prev) => [...prev, provider as LLMProvider]);
        }
        setShowLlmForm(false);
        setEditingLlmProvider(undefined);
      }, [editingLlmProvider]);
      const handleSaveEmbeddingProvider = useCallback((provider: Partial<EmbeddingProvider>) => {
        if (editingEmbeddingProvider) {
          setEmbeddingProviders((prev) => prev.map((p) => (p.id === provider.id ? { ...p, ...provider } as EmbeddingProvider : p)));
        } else {
          setEmbeddingProviders((prev) => [...prev, provider as EmbeddingProvider]);
        }
        setShowEmbeddingForm(false);
        setEditingEmbeddingProvider(undefined);
      }, [editingEmbeddingProvider]);
      const handleTestLlm = useCallback(async (id: string) => {
        setTestingId(id);
        // Simulate test
        await new Promise((resolve) => setTimeout(resolve, 2000));
        setLlmProviders((prev) =>
          prev.map((p) =>
            p.id === id
              ? {
                  ...p,
                  healthStatus: Math.random() > 0.3 ? 'healthy' : 'unhealthy',
                  latencyMs: Math.floor(Math.random() * 200) + 50,
                  errorMessage: Math.random() > 0.3 ? undefined : 'Connection timeout',
                }
              : p
          )
        );
        setTestingId(null);
      }, []);
      const handleTestEmbedding = useCallback(async (id: string) => {
        setTestingId(id);
        await new Promise((resolve) => setTimeout(resolve, 1500));
        setEmbeddingProviders((prev) =>
          prev.map((p) =>
            p.id === id
              ? { ...p, healthStatus: Math.random() > 0.3 ? 'healthy' : 'unhealthy' }
              : p
          )
        );
        setTestingId(null);
      }, []);
      const handleDeleteLlm = useCallback((id: string) => {
        if (confirm('Are you sure you want to delete this provider?')) {
          setLlmProviders((prev) => prev.filter((p) => p.id !== id));
        }
      }, []);
      const handleDeleteEmbedding = useCallback((id: string) => {
        if (confirm('Are you sure you want to delete this provider?')) {
          setEmbeddingProviders((prev) => prev.filter((p) => p.id !== id));
        }
      }, []);
      const defaultProvider = llmProviders.find((p) => p.isDefault && p.isEnabled);
      return (
        <div className="bg-gray-900 rounded-lg border border-gray-700 p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-white">Model Garage</h2>
              <p className="text-sm text-gray-400">Manage LLM and embedding provider connections</p>
            </div>
            {defaultProvider && (
              <div className="text-right">
                <div className="text-xs text-gray-400">Default Provider</div>
                <div className="text-white font-medium">{defaultProvider.name}</div>
                <div className="text-xs text-gray-500 font-mono">{defaultProvider.selectedModel}</div>
              </div>
            )}
          </div>
          {/* Global Stats */}
          <div className="grid grid-cols-4 gap-4 mb-6 p-4 bg-gray-800 rounded-lg">
            <div>
              <div className="text-xs text-gray-400">Total Requests</div>
              <div className="text-xl font-bold text-blue-400">{globalStats.totalRequests.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-xs text-gray-400">Total Tokens</div>
              <div className="text-xl font-bold text-green-400">{globalStats.totalTokens.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-xs text-gray-400">Avg Latency</div>
              <div className="text-xl font-bold text-yellow-400">{globalStats.avgLatency}ms</div>
            </div>
            <div>
              <div className="text-xs text-gray-400">Est. Cost</div>
              <div className="text-xl font-bold text-purple-400">${globalStats.costEstimate.toFixed(2)}</div>
            </div>
          </div>
          {/* Tabs */}
          <div className="flex gap-4 mb-6">
            <button
              onClick={() => setActiveTab('llm')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'llm'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              LLM Providers ({llmProviders.length})
            </button>
            <button
              onClick={() => setActiveTab('embedding')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'embedding'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              Embedding Providers ({embeddingProviders.length})
            </button>
          </div>
          {/* Content */}
          {activeTab === 'llm' && (
            <div>
              {/* Provider List */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                {llmProviders.map((provider) => (
                  <ProviderCard
                    key={provider.id}
                    provider={provider}
                    onEdit={setEditingLlmProvider}
                    onTest={handleTestLlm}
                    onToggle={(id) =>
                      setLlmProviders((prev) =>
                        prev.map((p) => (p.id === id ? { ...p, isEnabled: !p.isEnabled } : p))
                      )
                    }
                    onDelete={handleDeleteLlm}
                    isTesting={testingId === provider.id}
                  />
                ))}
              </div>
              {/* Add Button / Form */}
              {showLlmForm || editingLlmProvider ? (
                <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                  <h3 className="text-lg font-medium text-white mb-4">
                    {editingLlmProvider ? 'Edit LLM Provider' : 'Add LLM Provider'}
                  </h3>
                  <ProviderForm
                    provider={editingLlmProvider}
                    onSave={handleSaveLlmProvider}
                    onCancel={() => {
                      setShowLlmForm(false);
                      setEditingLlmProvider(undefined);
                    }}
                  />
                </div>
              ) : (
                <button
                  onClick={() => setShowLlmForm(true)}
                  className="w-full py-4 border-2 border-dashed border-gray-600 rounded-lg text-gray-400 hover:text-white hover:border-gray-500 transition-colors flex items-center justify-center gap-2"
                >
                  <span className="text-xl">+</span>
                  <span>Add LLM Provider</span>
                </button>
              )}
            </div>
          )}
          {activeTab === 'embedding' && (
            <div>
              {/* Provider List */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                {embeddingProviders.map((provider) => (
                  <EmbeddingProviderCard
                    key={provider.id}
                    provider={provider}
                    onEdit={setEditingEmbeddingProvider}
                    onTest={handleTestEmbedding}
                    onToggle={(id) =>
                      setEmbeddingProviders((prev) =>
                        prev.map((p) => (p.id === id ? { ...p, isEnabled: !p.isEnabled } : p))
                      )
                    }
                    onDelete={handleDeleteEmbedding}
                    isTesting={testingId === provider.id}
                  />
                ))}
              </div>
              {/* Add Button */}
              {embeddingProviders.length === 0 && (
                <button
                  onClick={() => setShowEmbeddingForm(true)}
                  className="w-full py-4 border-2 border-dashed border-gray-600 rounded-lg text-gray-400 hover:text-white hover:border-gray-500 transition-colors"
                >
                  Add Embedding Provider
                </button>
              )}
            </div>
          )}
          {/* Quick Add Buttons */}
          <div className="mt-6 pt-6 border-t border-gray-700">
            <h4 className="text-sm font-medium text-gray-400 mb-3">Quick Add</h4>
            <div className="flex flex-wrap gap-2">
              {(Object.entries(LLM_PROVIDER_CONFIGS) as [ProviderType, typeof LLM_PROVIDER_CONFIGS.openai][]).map(([type, config]) => (
                <button
                  key={type}
                  onClick={() => {
                    setEditingLlmProvider({
                      id: `${type}-${Date.now()}`,
                      name: config.name,
                      type,
                      baseUrl: config.defaultUrl,
                      models: config.models,
                      selectedModel: config.models[0],
                      isEnabled: true,
                      isDefault: false,
                      healthStatus: 'unknown',
                    });
                  }}
                  className="px-3 py-1.5 text-sm bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg border border-gray-700 transition-colors"
                  style={{ borderLeftColor: config.color, borderLeftWidth: 3 }}
                >
                  + {config.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      );
    }
    
    export default ModelGarage;
    ```
    **Category:** Anti-pattern
    **Severity:** minor

20. **JSX tree is too deeply nested. Found 5 levels of nesting** (`JS-0415`)
    **File:** `dashboard/frontend/src/components/Settings/ModelGarage.tsx`
    **Line:** 435
    ```typescript
    };
    
      return (
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: config?.color || '#6366f1' }}>
    ```
    **Category:** Anti-pattern
    **Severity:** minor

21. **Remove redundant `undefined` from function call** (`JS-W1042`)
    **File:** `dashboard/frontend/src/components/Settings/ModelGarage.tsx`
    **Line:** 752
    ```typescript
    onSave={handleSaveLlmProvider}
                    onCancel={() => {
                      setShowLlmForm(false);
                      setEditingLlmProvider(undefined);
                    }}
                  />
                </div>
    ```
    **Category:** Anti-pattern
    **Severity:** minor

22. **`ModelGarage` has a cyclomatic complexity of 10 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/Settings/ModelGarage.tsx`
    **Line:** 491
    ```typescript
    };
    
    // Main Component
    export function ModelGarage() {
      const [llmProviders, setLlmProviders] = useState<LLMProvider[]>([]);
      const [embeddingProviders, setEmbeddingProviders] = useState<EmbeddingProvider[]>([]);
      const [activeTab, setActiveTab] = useState<'llm' | 'embedding'>('llm');
    ```
    **Category:** Anti-pattern
    **Severity:** minor

23. **'handleSaveEmbeddingProvider' is assigned a value but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/Settings/ModelGarage.tsx`
    **Line:** 602
    ```typescript
    setEditingLlmProvider(undefined);
      }, [editingLlmProvider]);
    
      const handleSaveEmbeddingProvider = useCallback((provider: Partial<EmbeddingProvider>) => {
        if (editingEmbeddingProvider) {
          setEmbeddingProviders((prev) => prev.map((p) => (p.id === provider.id ? { ...p, ...provider } as EmbeddingProvider : p)));
        } else {
    ```
    **Category:** Performance
    **Severity:** major

24. **'showEmbeddingForm' is assigned a value but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/Settings/ModelGarage.tsx`
    **Line:** 496
    ```typescript
    const [embeddingProviders, setEmbeddingProviders] = useState<EmbeddingProvider[]>([]);
      const [activeTab, setActiveTab] = useState<'llm' | 'embedding'>('llm');
      const [showLlmForm, setShowLlmForm] = useState(false);
      const [showEmbeddingForm, setShowEmbeddingForm] = useState(false);
      const [editingLlmProvider, setEditingLlmProvider] = useState<LLMProvider | undefined>();
      const [editingEmbeddingProvider, setEditingEmbeddingProvider] = useState<EmbeddingProvider | undefined>();
      const [testingId, setTestingId] = useState<string | null>(null);
    ```
    **Category:** Performance
    **Severity:** major

25. **'onDelete' is defined but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/Settings/ModelGarage.tsx`
    **Line:** 423
    ```typescript
    onToggle: (id: string) => void;
      onDelete: (id: string) => void;
      isTesting: boolean;
    }> = ({ provider, onEdit, onTest, onToggle, onDelete, isTesting }) => {
      const config = EMBEDDING_PROVIDER_CONFIGS[provider.type];
      
      const getStatusColor = () => {
    ```
    **Category:** Performance
    **Severity:** major

26. **`renderTabContent` has a cyclomatic complexity of 6 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/Settings/SettingsPage.tsx`
    **Line:** 76
    ```typescript
    }
      }, [toast, onRerunSetup]);
    
      const renderTabContent = () => {
        switch (activeTab) {
          case 'llm':
            return <LLMProvidersSection />;
    ```
    **Category:** Anti-pattern
    **Severity:** minor

27. **JSX tree is too deeply nested. Found 6 levels of nesting** (`JS-0415`)
    **File:** `dashboard/frontend/src/components/Settings/SettingsPage.tsx`
    **Line:** 94
    ```typescript
    };
    
      return (
        <div className="space-y-6">
          {/* Page Header */}
          <div>
            <h1 className="text-2xl font-bold">Settings</h1>
    ```
    **Category:** Anti-pattern
    **Severity:** minor

28. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Settings/SettingsPage.tsx`
    **Line:** 37-299
    ```typescript
    { id: 'import', label: 'Import/Export', icon: '📁' },
    ];
    
    export function SettingsPage({ onRerunSetup }: SettingsPageProps) {
      const [activeTab, setActiveTab] = useState<string>('llm');
      const [apiKey, setApiKey] = useState(localStorage.getItem('swarm_api_key') || '');
      const [apiUrl, setApiUrl] = useState(localStorage.getItem('swarm_api_host') || '');
      const [showResetConfirm, setShowResetConfirm] = useState(false);
      const toast = useToast();
      const handleSaveApiKey = useCallback(() => {
        localStorage.setItem('swarm_api_key', apiKey);
        toast.success('API Key Saved', 'Your API key has been stored locally');
      }, [apiKey, toast]);
      const handleSaveApiUrl = useCallback(() => {
        localStorage.setItem('swarm_api_host', apiUrl);
        // Also update WebSocket URL
        const wsUrl = apiUrl.replace(/^http/, 'ws');
        localStorage.setItem('swarm_ws_host', wsUrl);
        toast.success('API URL Saved', 'The API URL will be used on next refresh');
      }, [apiUrl, toast]);
      const handleClearApiKey = useCallback(() => {
        localStorage.removeItem('swarm_api_key');
        setApiKey('');
        toast.info('API Key Cleared', 'Your API key has been removed');
      }, [toast]);
      const handleResetConfiguration = useCallback(() => {
        // Clear all configuration
        localStorage.removeItem('swarm_api_host');
        localStorage.removeItem('swarm_api_key');
        localStorage.removeItem('swarm_ws_host');
        localStorage.removeItem('swarm_configured');
        toast.info('Configuration Reset', 'Setup wizard will run on next load');
        setShowResetConfirm(false);
        if (onRerunSetup) {
          onRerunSetup();
        }
      }, [toast, onRerunSetup]);
      const renderTabContent = () => {
        switch (activeTab) {
          case 'llm':
            return <LLMProvidersSection />;
          case 'embedding':
            return <EmbeddingProvidersSection />;
          case 'system':
            return <SystemConfigSection />;
          case 'agents':
            return <AgentDefaultsSection />;
          case 'import':
            return <ImportExportSection />;
          default:
            return null;
        }
      };
      return (
        <div className="space-y-6">
          {/* Page Header */}
          <div>
            <h1 className="text-2xl font-bold">Settings</h1>
            <p className="text-gray-400 text-sm mt-1">
              System configuration and provider management
            </p>
          </div>
          {/* Developer Mode Toggle */}
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span>🔧</span> Developer Tools
            </h2>
            <DeveloperModeToggle />
          </div>
          {/* Connection Settings */}
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span>🔌</span> Connection Settings
            </h2>
            <div className="space-y-4">
              {/* API Key */}
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  API Key
                </label>
                <div className="flex gap-2">
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="Enter your API key"
                    className="flex-1 px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    onClick={handleSaveApiKey}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
                  >
                    Save
                  </button>
                  {apiKey && (
                    <button
                      onClick={handleClearApiKey}
                      className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors"
                    >
                      Clear
                    </button>
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Your API key is stored locally in your browser and used for authenticated requests.
                </p>
              </div>
              {/* API URL */}
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  API URL
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={apiUrl}
                    onChange={(e) => setApiUrl(e.target.value)}
                    placeholder="API base URL (e.g., http://localhost:8000)"
                    className="flex-1 px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    onClick={handleSaveApiUrl}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
                  >
                    Save
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Leave empty to use the relative path (recommended for nginx proxy setup).
                </p>
              </div>
            </div>
          </div>
          {/* Reset Configuration */}
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span>🔄</span> Configuration Management
            </h2>
            {!showResetConfirm ? (
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-300">Reset Configuration</p>
                  <p className="text-xs text-gray-500">
                    Run the setup wizard again to reconfigure your connection settings
                  </p>
                </div>
                <button
                  onClick={() => setShowResetConfirm(true)}
                  className="px-4 py-2 bg-yellow-600/20 hover:bg-yellow-600/30 border border-yellow-600/50 hover:border-yellow-500 text-yellow-400 rounded-lg text-sm font-medium transition-colors"
                >
                  Reset Wizard
                </button>
              </div>
            ) : (
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                <p className="text-sm text-yellow-300 mb-3">
                  Are you sure you want to reset the configuration? The setup wizard will run again on the next page load.
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={handleResetConfiguration}
                    className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg text-sm font-medium transition-colors"
                  >
                    Yes, Reset
                  </button>
                  <button
                    onClick={() => setShowResetConfirm(false)}
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
          {/* Tab Navigation */}
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl">
            <div className="border-b border-gray-700">
              <nav className="flex overflow-x-auto">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-400'
                        : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-600'
                    }`}
                  >
                    <span>{tab.icon}</span>
                    <span>{tab.label}</span>
                  </button>
                ))}
              </nav>
            </div>
            {/* Tab Content */}
            <div className="p-6">
              {renderTabContent()}
            </div>
          </div>
          {/* About Section */}
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span>ℹ️</span> About
            </h2>
            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between py-2 border-b border-gray-700">
                <span className="text-gray-400">Version</span>
                <span className="text-white font-mono">0.2.0</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-gray-700">
                <span className="text-gray-400">Build</span>
                <span className="text-white font-mono">2026.04</span>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-gray-400">Repository</span>
                <a
                  href="https://github.com/heretek/heretek-swarm"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300 hover:underline"
                >
                  GitHub →
                </a>
              </div>
            </div>
          </div>
        </div>
      );
    }
    
    export default SettingsPage;
    ```
    **Category:** Anti-pattern
    **Severity:** minor

29. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 274-326
    ```typescript
    /**
     * Welcome step
     */
    function WelcomeStep({ onStart }: { onStart: () => void }) {
      return (
        <div className="text-center space-y-8 py-8">
          {/* Hero icon */}
          <div className="relative mx-auto w-24 h-24">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl blur-lg opacity-30" />
            <div className="relative w-full h-full bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center">
              <span className="text-4xl">🚀</span>
            </div>
          </div>
                {/* Title */}
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              Welcome to Heretek Swarm
            </h1>
            <p className="text-gray-400 mt-2">Intelligent Agent Orchestration Platform</p>
          </div>
                {/* Description */}
          <p className="text-gray-400 max-w-lg mx-auto leading-relaxed">
            Let's configure your swarm dashboard to connect to the Heretek backend services. 
            This wizard will guide you through setting up API connectivity and verifying 
            your agent infrastructure.
          </p>
          
          {/* Feature highlights */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl mx-auto pt-4">
            <InfoCard icon="🔗" title="API Setup">
              Connect to your Heretek Swarm backend with secure API credentials.
            </InfoCard>
            <InfoCard icon="📊" title="Health Check">
              Verify all agent services are running and responsive.
            </InfoCard>
            <InfoCard icon="🎯" title="Ready to Go">
              Get instant access to your swarm dashboard upon completion.
            </InfoCard>
          </div>
          
          {/* Start button */}
          <button
            onClick={onStart}
            className="px-10 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 rounded-xl font-semibold text-lg transition-all transform hover:scale-105 shadow-lg shadow-blue-500/25"
          >
            Get Started →
          </button>
          
          <p className="text-xs text-gray-600">
            This setup takes approximately 2 minutes
          </p>
        </div>
      );
    }
    
    /**
     * API Endpoint Configuration step
    ```
    **Category:** Anti-pattern
    **Severity:** minor

30. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 231-265
    ```typescript
    /**
     * Agent health card
     */
    function AgentHealthCard({ agent }: { agent: AgentHealthResult }) {
      const statusConfig = {
        online: { color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/30', icon: '●' },
        offline: { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', icon: '○' },
        degraded: { color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', icon: '◐' },
        unknown: { color: 'text-gray-400', bg: 'bg-gray-500/10', border: 'border-gray-500/30', icon: '?' },
      };
        const config = statusConfig[agent.status];
        return (
        <div className={`${config.bg} ${config.border} border rounded-lg p-3 flex items-center justify-between`}>
          <div className="flex items-center gap-3">
            <span className={`${config.color} text-lg`}>{config.icon}</span>
            <div>
              <div className="font-medium text-white">{agent.agentType}</div>
              <div className="text-xs text-gray-500">ID: {agent.agentId}</div>
            </div>
          </div>
          <div className="text-right">
            <div className={`font-medium ${config.color}`}>
              {agent.status.charAt(0).toUpperCase() + agent.status.slice(1)}
            </div>
            {agent.messageCount !== undefined && (
              <div className="text-xs text-gray-500">{agent.messageCount} messages</div>
            )}
            {agent.lastActivity && (
              <div className="text-xs text-gray-500">
                Last: {new Date(agent.lastActivity).toLocaleTimeString()}
              </div>
            )}
          </div>
        </div>
      );
    }
    
    // =============================================================================
    // Step Components
    ```
    **Category:** Anti-pattern
    **Severity:** minor

31. **`ResultCard` has a cyclomatic complexity of 9 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 195
    ```typescript
    /**
     * Result card for connection tests
     */
    function ResultCard({
       title, 
      result, 
      details
    ```
    **Category:** Anti-pattern
    **Severity:** minor

32. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 981-1122
    ```typescript
    const STEPS: WizardStep[] = ['welcome', 'api-endpoint', 'api-key', 'database-test', 'agent-health', 'complete'];
    
    export function SetupWizard({ onComplete }: SetupWizardProps) {
      const {
        currentStep,
        config,
        isConfigured,
        isRerunning,
        setStep,
        nextStep,
        prevStep,
        setConfig,
        completeSetup,
        resetSetup,
        setRerunning,
      } = useSetupStore();
      
      const toast = useToast();
      
      // Check if already configured on mount
      useEffect(() => {
        const configured = localStorage.getItem('swarm_configured') === 'true';
        if (configured && !isRerunning) {
          onComplete();
        }
      }, [isConfigured, isRerunning, onComplete]);
      
      const currentStepIndex = STEPS.indexOf(currentStep);
      
      const handleComplete = useCallback(() => {
        completeSetup();
        toast.success('Setup Complete', 'Heretek Swarm is now configured!');
        onComplete();
      }, [completeSetup, toast, onComplete]);
      
      const handleFinish = useCallback(() => {
        onComplete();
      }, [onComplete]);
      
      const renderStep = () => {
        switch (currentStep) {
          case 'welcome':
            return <WelcomeStep onStart={nextStep} />;
          
          case 'api-endpoint':
            return (
              <ApiEndpointStep
                apiHost={config.apiHost}
                onChange={(host) => setConfig({ apiHost: host, wsHost: deriveWsUrl(host) })}
                onNext={nextStep}
                onBack={prevStep}
              />
            );
          
          case 'api-key':
            return (
              <ApiKeyStep
                apiKey={config.apiKey}
                apiHost={config.apiHost}
                onChange={(key) => setConfig({ apiKey: key })}
                onNext={nextStep}
                onBack={prevStep}
              />
            );
          
          case 'database-test':
            return (
              <DatabaseTestStep
                apiHost={config.apiHost}
                apiKey={config.apiKey}
                onNext={nextStep}
                onBack={prevStep}
              />
            );
          
          case 'agent-health':
            return (
              <AgentHealthStep
                apiHost={config.apiHost}
                apiKey={config.apiKey}
                onNext={handleComplete}
                onBack={prevStep}
              />
            );
          
          case 'complete':
            return <CompleteStep onFinish={handleFinish} />;
          
          default:
            return <WelcomeStep onStart={nextStep} />;
        }
      };
      
      const showProgress = currentStep !== 'welcome' && currentStep !== 'complete';
        return (
        <div className="min-h-screen bg-gray-950 text-white flex flex-col">
          {/* Header */}
          <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-10">
            <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <span className="text-lg">🧠</span>
                </div>
                <span className="font-semibold">Heretek Swarm</span>
              </div>
                        {showProgress && (
                <StepProgress
                  currentStep={currentStep}
                  totalSteps={STEPS.length}
                  currentStepIndex={currentStepIndex}
                />
              )}
                        {/* Reset button */}
              <button
                onClick={() => {
                  resetSetup();
                  setRerunning(true);
                }}
                className="text-xs text-gray-500 hover:text-gray-300"
              >
                Reset
              </button>
            </div>
          </header>
                {/* Main content */}
          <main className="flex-1 flex items-center justify-center p-6">
            <div className="w-full max-w-2xl">
              {renderStep()}
            </div>
          </main>
                {/* Footer */}
          <footer className="border-t border-gray-800 py-4">
            <div className="max-w-4xl mx-auto px-6 text-center text-xs text-gray-600">
              Heretek Swarm Dashboard • First-run Setup Wizard
            </div>
          </footer>
        </div>
      );
    }
    
    export default SetupWizard;
    ```
    **Category:** Anti-pattern
    **Severity:** minor

33. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 331-462
    ```typescript
    /**
     * API Endpoint Configuration step
     */
    function ApiEndpointStep({
      apiHost,
      onChange,
      onNext,
      onBack,
    }: {
      apiHost: string;
      onChange: (host: string) => void;
      onNext: () => void;
      onBack: () => void;
    }) {
      const [localValue, setLocalValue] = useState(apiHost);
      const [validationStatus, setValidationStatus] = useState<'pending' | 'valid' | 'invalid'>('pending');
      const [validationError, setValidationError] = useState<string | null>(null);
      
      // Debounced validation
      useEffect(() => {
        const timer = setTimeout(() => {
          const result = validateApiHost(localValue);
          if (result.isValid) {
            setValidationStatus('valid');
            setValidationError(null);
          } else if (localValue.trim()) {
            setValidationStatus('invalid');
            setValidationError(result.error || 'Invalid URL');
          } else {
            setValidationStatus('pending');
            setValidationError(null);
          }
        }, 300);
        
        return () => clearTimeout(timer);
      }, [localValue]);
      
      const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setLocalValue(value);
        onChange(value);
      };
      
      const handleNext = () => {
        if (validationStatus === 'valid') {
          onChange(normalizeUrl(localValue));
          onNext();
        }
      };
      
      const presets = [
        { label: 'Local Development', value: 'http://localhost:8000', icon: '🏠' },
        { label: 'Docker Compose', value: 'http://localhost', icon: '🐳' },
        { label: 'Production', value: 'https://api.example.com', icon: '☁️' },
      ];
        return (
        <div className="space-y-6">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-500/20 rounded-xl mb-4">
              <span className="text-3xl">🔗</span>
            </div>
            <h2 className="text-2xl font-bold text-white">API Endpoint Configuration</h2>
            <p className="text-gray-400 mt-2">Enter the base URL of your Heretek Swarm API</p>
          </div>
                {/* Input */}
          <div className="max-w-lg mx-auto">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              API Host URL
            </label>
            <div className="relative">
              <input
                type="text"
                value={localValue}
                onChange={handleChange}
                placeholder="http://localhost:8000"
                className={`w-full px-4 py-3 bg-gray-800 border ${
                  validationStatus === 'invalid' ? 'border-red-500' :
                   validationStatus === 'valid' ? 'border-green-500' :
                   'border-gray-700'
                } rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors`}
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                <StatusIndicator status={validationStatus === 'pending' ? 'pending' : validationStatus} />
              </div>
            </div>
            {validationError && (
              <p className="mt-2 text-sm text-red-400">{validationError}</p>
            )}
            <p className="mt-2 text-xs text-gray-500">
              Include the protocol (http:// or https://) and port if needed
            </p>
          </div>
                {/* Presets */}
          <div className="max-w-lg mx-auto">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Quick Presets
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {presets.map((preset) => (
                <button
                  key={preset.label}
                  onClick={() => {
                    setLocalValue(preset.value);
                    onChange(preset.value);
                  }}
                  className="px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-sm transition-colors flex items-center gap-2"
                >
                  <span>{preset.icon}</span>
                  <span>{preset.label}</span>
                </button>
              ))}
            </div>
          </div>
                {/* Info */}
          <div className="max-w-lg mx-auto">
            <InfoCard icon="💡" title="Finding Your API URL">
              If running locally with Docker Compose, use <code className="text-blue-400">http://localhost</code>. 
              For local development, use <code className="text-blue-400">http://localhost:8000</code>.
            </InfoCard>
          </div>
                <WizardNav
            onBack={onBack}
            onNext={handleNext}
            nextLabel="Continue"
            nextDisabled={validationStatus !== 'valid'}
            hideBack
          />
        </div>
      );
    }
    
    /**
     * API Key Configuration step
    ```
    **Category:** Anti-pattern
    **Severity:** minor

34. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 178-190
    ```typescript
    /**
     * Info card component
     */
    function InfoCard({ icon, title, children }: { icon: string; title: string; children: React.ReactNode }) {
      return (
        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-2xl">{icon}</span>
            <h3 className="font-semibold text-white">{title}</h3>
          </div>
          <div className="text-sm text-gray-400">
            {children}
          </div>
        </div>
      );
    }
    
    /**
     * Result card for connection tests
    ```
    **Category:** Anti-pattern
    **Severity:** minor

35. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 62-102
    ```typescript
    /**
     * Status indicator with animation
     */
    function StatusIndicator({ status, label }: StatusIndicatorProps) {
      const statusConfig = {
        pending: {
          icon: (
            <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" strokeWidth="2" />
            </svg>
          ),
          textClass: 'text-gray-400',
        },
        loading: {
          icon: <LoadingSpinner size="sm" />,
          textClass: 'text-blue-400',
        },
        success: {
          icon: (
            <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
            </svg>
          ),
          textClass: 'text-green-400',
        },
        error: {
          icon: (
            <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          ),
          textClass: 'text-red-400',
        },
      };
        const config = statusConfig[status];
        return (
        <div className="flex items-center gap-2">
          {config.icon}
          {label && <span className={`text-sm ${config.textClass}`}>{label}</span>}
        </div>
      );
    }
    
    /**
     * Progress bar showing current step
    ```
    **Category:** Anti-pattern
    **Severity:** minor

36. **JSX tree is too deeply nested. Found 6 levels of nesting** (`JS-0415`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 1075
    ```typescript
    const showProgress = currentStep !== 'welcome' && currentStep !== 'complete';
      
      return (
        <div className="min-h-screen bg-gray-950 text-white flex flex-col">
          {/* Header */}
          <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-10">
            <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
    ```
    **Category:** Anti-pattern
    **Severity:** minor

37. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 47-57
    ```typescript
    /**
     * Animated loading spinner
     */
    function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
      const sizeClasses = {
        sm: 'w-4 h-4',
        md: 'w-6 h-6',
        lg: 'w-8 h-8',
      };
        return (
        <div className={`${sizeClasses[size]} border-2 border-blue-500 border-t-transparent rounded-full animate-spin`} />
      );
    }
    
    /**
     * Status indicator with animation
    ```
    **Category:** Anti-pattern
    **Severity:** minor

38. **`ApiKeyStep` has a cyclomatic complexity of 13 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 467
    ```typescript
    /**
     * API Key Configuration step
     */
    function ApiKeyStep({
      apiKey,
      apiHost,
      onChange,
    ```
    **Category:** Anti-pattern
    **Severity:** minor

39. **Parse errors in imported module '../../utils/setupValidation': ':' expected. (449:75)** (`JS-W1029`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 24
    ```typescript
    validateApiKey,
      normalizeUrl,
      deriveWsUrl,
    } from '../../utils/setupValidation';
    import { useToast } from '../UI/Toast';
    
    // =============================================================================
    ```
    **Category:** Bug risk
    **Severity:** minor

40. **`DatabaseTestStep` has a cyclomatic complexity of 9 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 620
    ```typescript
    /**
     * Database Connection Test step
     */
    function DatabaseTestStep({
      apiHost,
      apiKey,
      onNext,
    ```
    **Category:** Anti-pattern
    **Severity:** minor

41. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 764-905
    ```typescript
    /**
     * Agent Health Check step
     */
    function AgentHealthStep({
      apiHost,
      apiKey,
      onNext,
      onBack,
    }: {
      apiHost: string;
      apiKey: string;
      onNext: () => void;
      onBack: () => void;
    }) {
      const [agents, setAgents] = useState<AgentHealthResult[]>([]);
      const [isLoading, setIsLoading] = useState(true);
      const [error, setError] = useState<string | null>(null);
      
      const checkHealth = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        
        try {
          const results = await checkAgentHealth(apiHost, apiKey);
          setAgents(results);
        } catch (e) {
          setError(e instanceof Error ? e.message : 'Failed to check agent health');
          setAgents([]);
        }
        
        setIsLoading(false);
      }, [apiHost, apiKey]);
      
      // Auto-check on mount
      useEffect(() => {
        checkHealth();
      }, [checkHealth]);
      
      const onlineCount = agents.filter(a => a.status === 'online').length;
      const totalCount = agents.length;
      
      return (
        <div className="space-y-6">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-cyan-500/20 rounded-xl mb-4">
              <span className="text-3xl">🤖</span>
            </div>
            <h2 className="text-2xl font-bold text-white">Agent Health Check</h2>
            <p className="text-gray-400 mt-2">Verifying swarm agent status</p>
          </div>
          
          {/* Status summary */}
          <div className="max-w-lg mx-auto">
            <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-gray-400">Agent Status</div>
                  <div className="text-2xl font-bold text-white">
                    {isLoading ? (
                      <span className="text-gray-400">Checking...</span>
                    ) : (
                      <>
                        <span className={onlineCount > 0 ? 'text-green-400' : 'text-gray-400'}>
                          {onlineCount}
                        </span>
                        <span className="text-gray-500"> / {totalCount}</span>
                      </>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
                    isLoading ? 'bg-blue-500/20 text-blue-400' :
                    onlineCount > 0 ? 'bg-green-500/20 text-green-400' :
                    'bg-gray-500/20 text-gray-400'
                  }`}>
                    {isLoading ? (
                      <LoadingSpinner size="sm" />
                    ) : onlineCount > 0 ? (
                      '● Online'
                    ) : (
                      '○ No Agents'
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Agent list */}
          <div className="max-w-lg mx-auto space-y-2">
            {isLoading ? (
              <div className="text-center py-8 text-gray-400">
                <LoadingSpinner size="md" />
                <p className="mt-4">Checking agent health...</p>
              </div>
            ) : error ? (
              <div className="text-center py-8">
                <p className="text-red-400">{error}</p>
                <button
                  onClick={checkHealth}
                  className="mt-4 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg"
                >
                  Try Again
                </button>
              </div>
            ) : agents.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <p>No agent instances found</p>
                <p className="text-sm mt-2">Deploy agents to see them here</p>
              </div>
            ) : (
              agents.map((agent) => (
                <AgentHealthCard key={agent.agentId} agent={agent} />
              ))
            )}
          </div>
          
          {/* Re-check button */}
          <div className="max-w-lg mx-auto">
            <button
              onClick={checkHealth}
              disabled={isLoading}
              className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <LoadingSpinner size="sm" />
                  Checking...
                </>
              ) : (
                '↻ Refresh Status'
              )}
            </button>
          </div>
          
          <WizardNav
            onBack={onBack}
            onNext={onNext}
            nextLabel="Complete Setup"
            nextDisabled={isLoading}
          />
        </div>
      );
    }
    
    /**
     * Success/Complete step
    ```
    **Category:** Anti-pattern
    **Severity:** minor

42. **Expected to return a value at the end of arrow function** (`JS-0045`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 913
    ```typescript
    function CompleteStep({ onFinish }: { onFinish: () => void }) {
      const [countdown, setCountdown] = useState(5);
      
      useEffect(() => {
        if (countdown > 0) {
          const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
          return () => clearTimeout(timer);
    ```
    **Category:** Anti-pattern
    **Severity:** minor

43. **JSX tree is too deeply nested. Found 5 levels of nesting** (`JS-0415`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 923
    ```typescript
    }, [countdown, onFinish]);
      
      return (
        <div className="text-center space-y-8 py-8">
          {/* Success animation */}
          <div className="relative mx-auto w-32 h-32">
            <div className="absolute inset-0 bg-gradient-to-br from-green-400 to-emerald-600 rounded-full blur-xl opacity-30 animate-pulse" />
    ```
    **Category:** Anti-pattern
    **Severity:** minor

44. **`renderStep` has a cyclomatic complexity of 7 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 1018
    ```typescript
    onComplete();
      }, [onComplete]);
      
      const renderStep = () => {
        switch (currentStep) {
          case 'welcome':
            return <WelcomeStep onStart={nextStep} />;
    ```
    **Category:** Anti-pattern
    **Severity:** minor

45. **JSX tree is too deeply nested. Found 6 levels of nesting** (`JS-0415`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 803
    ```typescript
    const totalCount = agents.length;
      
      return (
        <div className="space-y-6">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-cyan-500/20 rounded-xl mb-4">
              <span className="text-3xl">🤖</span>
    ```
    **Category:** Anti-pattern
    **Severity:** minor

46. **`AgentHealthStep` has a cyclomatic complexity of 11 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 764
    ```typescript
    /**
     * Agent Health Check step
     */
    function AgentHealthStep({
      apiHost,
      apiKey,
      onNext,
    ```
    **Category:** Anti-pattern
    **Severity:** minor

47. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 107-128
    ```typescript
    /**
     * Progress bar showing current step
     */
    function StepProgress({ currentStep, totalSteps, currentStepIndex }: {
      currentStep: WizardStep;
      totalSteps: number;
      currentStepIndex: number;
    }) {
      const progress = ((currentStepIndex) / (totalSteps - 1)) * 100;
        return (
        <div className="w-full">
          <div className="flex justify-between text-xs text-gray-500 mb-2">
            <span>Step {currentStepIndex + 1} of {totalSteps - 1}</span>
            <span>{Math.round(progress)}% complete</span>
          </div>
          <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-600 to-purple-600 transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      );
    }
    
    /**
     * Navigation buttons
    ```
    **Category:** Anti-pattern
    **Severity:** minor

48. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 195-226
    ```typescript
    /**
     * Result card for connection tests
     */
    function ResultCard({
       title,
       result,
       details
     }: {
       title: string;
       result: ConnectionTestResult | null;
       details?: string
     }) {
      const status = result === null ? 'pending' : result.success ? 'success' : 'error';
        return (
        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium text-white">{title}</span>
            <StatusIndicator
               status={status}
               label={result ? (result.success ? `${result.latency}ms` : 'Failed') : 'Waiting'}
             />
          </div>
          {result?.error && (
            <p className="text-sm text-red-400 mt-1">{result.error}</p>
          )}
          {result?.details && (
            <p className="text-sm text-gray-400 mt-1 whitespace-pre-line">{result.details}</p>
          )}
          {details && !result?.details && (
            <p className="text-sm text-gray-400 mt-1">{details}</p>
          )}
        </div>
      );
    }
    
    /**
     * Agent health card
    ```
    **Category:** Anti-pattern
    **Severity:** minor

49. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 467-615
    ```typescript
    /**
     * API Key Configuration step
     */
    function ApiKeyStep({
      apiKey,
      apiHost,
      onChange,
      onNext,
      onBack,
    }: {
      apiKey: string;
      apiHost: string;
      onChange: (key: string) => void;
      onNext: () => void;
      onBack: () => void;
    }) {
      const [localValue, setLocalValue] = useState(apiKey);
      const [showKey, setShowKey] = useState(false);
      const [isTesting, setIsTesting] = useState(false);
      const [testResult, setTestResult] = useState<ConnectionTestResult | null>(null);
      const [validationStatus, setValidationStatus] = useState<'pending' | 'valid' | 'invalid'>('pending');
        // Debounced validation
      useEffect(() => {
        const timer = setTimeout(() => {
          const result = validateApiKey(localValue);
          setValidationStatus(result.isValid ? 'valid' : localValue.trim() ? 'invalid' : 'pending');
        }, 300);
            return () => clearTimeout(timer);
      }, [localValue]);
        const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setLocalValue(e.target.value);
        onChange(e.target.value);
        setTestResult(null);
      };
        const handleTestKey = async () => {
        if (!localValue.trim() || !apiHost) return;
            setIsTesting(true);
        setTestResult(null);
            try {
          const result = await testApiKey(apiHost, localValue);
          setTestResult(result);
        } catch {
          setTestResult({
            success: false,
            error: 'Failed to test API key',
          });
        }
            setIsTesting(false);
      };
        const handleNext = () => {
        onNext();
      };
        return (
        <div className="space-y-6">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-500/20 rounded-xl mb-4">
              <span className="text-3xl">🔑</span>
            </div>
            <h2 className="text-2xl font-bold text-white">API Key Configuration</h2>
            <p className="text-gray-400 mt-2">Enter your Heretek Swarm API key for authentication</p>
          </div>
                {/* Input */}
          <div className="max-w-lg mx-auto">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              API Key
            </label>
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={localValue}
                onChange={handleChange}
                placeholder="Enter your API key"
                className={`w-full px-4 py-3 pr-20 bg-gray-800 border ${
                  validationStatus === 'invalid' ? 'border-red-500' :
                   validationStatus === 'valid' ? 'border-green-500' :
                   'border-gray-700'
                } rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-colors font-mono`}
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
              >
                {showKey ? '🙈' : '👁️'}
              </button>
            </div>
            <p className="mt-2 text-xs text-gray-500">
              Your API key is stored locally and never sent to external servers
            </p>
          </div>
                {/* Test button and result */}
          <div className="max-w-lg mx-auto">
            <button
              onClick={handleTestKey}
              disabled={!localValue.trim() || isTesting}
              className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
            >
              {isTesting ? (
                <>
                  <LoadingSpinner size="sm" />
                  Testing...
                </>
              ) : (
                'Test API Key'
              )}
            </button>
                    {testResult && (
              <div className={`mt-3 p-3 rounded-lg border ${
                testResult.success ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'
              }`}>
                <div className="flex items-center gap-2">
                  <StatusIndicator status={testResult.success ? 'success' : 'error'} />
                  <span className={testResult.success ? 'text-green-400' : 'text-red-400'}>
                    {testResult.success ? 'API key is valid!' : testResult.error}
                  </span>
                </div>
                {testResult.latency && (
                  <p className="text-xs text-gray-500 mt-1">Response time: {testResult.latency}ms</p>
                )}
              </div>
            )}
          </div>
                {/* Info */}
          <div className="max-w-lg mx-auto">
            <InfoCard icon="🔒" title="Security">
              Your API key is encrypted and stored only in your browser's local storage. 
              It is transmitted securely to authenticate with your Heretek Swarm backend.
            </InfoCard>
          </div>
          
          <WizardNav
            onBack={onBack}
            onNext={handleNext}
            nextLabel="Continue"
            nextDisabled={validationStatus !== 'valid'}
          />
        </div>
      );
    }
    
    /**
     * Database Connection Test step
    ```
    **Category:** Anti-pattern
    **Severity:** minor

50. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 910-973
    ```typescript
    /**
     * Success/Complete step
     */
    function CompleteStep({ onFinish }: { onFinish: () => void }) {
      const [countdown, setCountdown] = useState(5);
      
      useEffect(() => {
        if (countdown > 0) {
          const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
          return () => clearTimeout(timer);
        } else {
          onFinish();
        }
      }, [countdown, onFinish]);
      
      return (
        <div className="text-center space-y-8 py-8">
          {/* Success animation */}
          <div className="relative mx-auto w-32 h-32">
            <div className="absolute inset-0 bg-gradient-to-br from-green-400 to-emerald-600 rounded-full blur-xl opacity-30 animate-pulse" />
            <div className="relative w-full h-full bg-gradient-to-br from-green-400 to-emerald-600 rounded-full flex items-center justify-center animate-bounce">
              <span className="text-5xl">✓</span>
            </div>
          </div>
          
          {/* Title */}
          <div>
            <h1 className="text-3xl font-bold text-white">
              Setup Complete!
            </h1>
            <p className="text-gray-400 mt-2">Your Heretek Swarm is ready to use</p>
          </div>
          
          {/* Summary */}
          <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6 max-w-md mx-auto">
            <h3 className="font-medium text-white mb-4">Configuration Summary</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">API Connected</span>
                <span className="text-green-400">✓</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">WebSocket Active</span>
                <span className="text-green-400">✓</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Credentials Saved</span>
                <span className="text-green-400">✓</span>
              </div>
            </div>
          </div>
          
          {/* Redirect message */}
          <p className="text-gray-400">
            Redirecting to dashboard in <span className="text-blue-400 font-mono">{countdown}</span> seconds...
          </p>
          
          {/* Manual continue button */}
          <button
            onClick={onFinish}
            className="px-8 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition-colors"
          >
            Go to Dashboard Now
          </button>
        </div>
      );
    }
    
    // =============================================================================
    // Main Component
    ```
    **Category:** Anti-pattern
    **Severity:** minor

51. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 133-173
    ```typescript
    /**
     * Navigation buttons
     */
    function WizardNav({
      onBack,
      onNext,
      nextLabel = 'Next',
      nextDisabled = false,
      nextLoading = false,
      hideBack = false,
    }: {
      onBack?: () => void;
      onNext?: () => void;
      nextLabel?: string;
      nextDisabled?: boolean;
      nextLoading?: boolean;
      hideBack?: boolean;
    }) {
      return (
        <div className="flex justify-between items-center pt-8 border-t border-gray-800">
          {!hideBack ? (
            <button
              onClick={onBack}
              className="px-6 py-2.5 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            >
              ← Back
            </button>
          ) : (
            <div />
          )}
                {onNext && (
            <button
              onClick={onNext}
              disabled={nextDisabled || nextLoading}
              className="px-8 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg font-semibold transition-colors flex items-center gap-2"
            >
              {nextLoading && <LoadingSpinner size="sm" />}
              {nextLabel}
            </button>
          )}
        </div>
      );
    }
    
    /**
     * Info card component
    ```
    **Category:** Anti-pattern
    **Severity:** minor

52. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 620-759
    ```typescript
    /**
     * Database Connection Test step
     */
    function DatabaseTestStep({
      apiHost,
      apiKey,
      onNext,
      onBack,
    }: {
      apiHost: string;
      apiKey: string;
      onNext: () => void;
      onBack: () => void;
    }) {
      const [isTesting, setIsTesting] = useState(false);
      const [apiResult, setApiResult] = useState<ConnectionTestResult | null>(null);
      const [wsResult, setWsResult] = useState<ConnectionTestResult | null>(null);
      const [dbResult, setDbResult] = useState<ConnectionTestResult | null>(null);
      const [hasRunTests, setHasRunTests] = useState(false);
      
      const runTests = useCallback(async () => {
        setIsTesting(true);
        setApiResult(null);
        setWsResult(null);
        setDbResult(null);
        
        // Run tests in parallel
        const [api, ws, db] = await Promise.all([
          testApiHealth(apiHost, apiKey).catch((e) => ({ success: false, error: e.message })),
          testWebSocket(deriveWsUrl(apiHost), apiKey).catch((e) => ({ success: false, error: e.message })),
          testDatabaseConnection(apiHost, apiKey).catch((e) => ({ success: false, error: e.message })),
        ]);
        
        setApiResult(api);
        setWsResult(ws);
        setDbResult(db);
        setHasRunTests(true);
        setIsTesting(false);
      }, [apiHost, apiKey]);
      
      // Auto-run tests on mount
      useEffect(() => {
        if (!hasRunTests && apiHost) {
          runTests();
        }
      }, [apiHost, apiKey, hasRunTests, runTests]);
      
      const allPassed = apiResult?.success && dbResult?.success;
      const anyPassed = apiResult?.success || dbResult?.success;
      
      return (
        <div className="space-y-6">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-500/20 rounded-xl mb-4">
              <span className="text-3xl">📊</span>
            </div>
            <h2 className="text-2xl font-bold text-white">Connection Verification</h2>
            <p className="text-gray-400 mt-2">Testing API, WebSocket, and database connectivity</p>
          </div>
          
          {/* Connection cards */}
          <div className="max-w-lg mx-auto space-y-3">
            <ResultCard 
              title="REST API" 
              result={apiResult}
              details="Testing /api/health endpoint"
            />
            <ResultCard 
              title="WebSocket" 
              result={wsResult}
              details="Testing WebSocket connection"
            />
            <ResultCard 
              title="Database Services" 
              result={dbResult}
              details="Checking Postgres, Redis, Qdrant"
            />
          </div>
          
          {/* Re-test button */}
          <div className="max-w-lg mx-auto">
            <button
              onClick={runTests}
              disabled={isTesting}
              className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
            >
              {isTesting ? (
                <>
                  <LoadingSpinner size="sm" />
                  Running tests...
                </>
              ) : (
                '↻ Re-run Tests'
              )}
            </button>
          </div>
          
          {/* Summary */}
          {hasRunTests && (
            <div className={`max-w-lg mx-auto p-4 rounded-lg border ${
              allPassed ? 'bg-green-500/10 border-green-500/30' :
              anyPassed ? 'bg-yellow-500/10 border-yellow-500/30' :
              'bg-red-500/10 border-red-500/30'
            }`}>
              <div className="flex items-center gap-3">
                {allPassed ? (
                  <>
                    <span className="text-2xl">🎉</span>
                    <div>
                      <div className="font-medium text-green-400">All connections verified</div>
                      <div className="text-sm text-gray-400">Ready to continue</div>
                    </div>
                  </>
                ) : anyPassed ? (
                  <>
                    <span className="text-2xl">⚠️</span>
                    <div>
                      <div className="font-medium text-yellow-400">Partial connectivity</div>
                      <div className="text-sm text-gray-400">Some services may be unavailable</div>
                    </div>
                  </>
                ) : (
                  <>
                    <span className="text-2xl">❌</span>
                    <div>
                      <div className="font-medium text-red-400">Connection failed</div>
                      <div className="text-sm text-gray-400">Check your API endpoint and key</div>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
          
          <WizardNav
            onBack={onBack}
            onNext={onNext}
            nextLabel="Continue"
            nextDisabled={!anyPassed}
          />
        </div>
      );
    }
    
    /**
     * Agent Health Check step
    ```
    **Category:** Anti-pattern
    **Severity:** minor

53. **'useMemo' is defined but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 12
    ```typescript
    * - Step 5: Success/Dashboard redirect
     */
    
    import React, { useState, useCallback, useEffect, useMemo } from 'react';
    import { useSetupStore, type WizardStep, type ConnectionTestResult, type AgentHealthResult } from '../../stores/setupStore';
    import {
      testApiHealth,
    ```
    **Category:** Performance
    **Severity:** major

54. **Parse errors in imported module '../../utils/setupValidation': ':' expected. (449:75)** (`JS-E1007`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 24
    ```typescript
    validateApiKey,
      normalizeUrl,
      deriveWsUrl,
    } from '../../utils/setupValidation';
    import { useToast } from '../UI/Toast';
    
    // =============================================================================
    ```
    **Category:** Bug risk
    **Severity:** major

55. **'setStep' is assigned a value but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 987
    ```typescript
    config,
        isConfigured,
        isRerunning,
        setStep,
        nextStep,
        prevStep,
        setConfig,
    ```
    **Category:** Performance
    **Severity:** major

56. **' can be escaped with &apos;** (`JS-0454`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 602
    ```typescript
    {/* Info */}
          <div className="max-w-lg mx-auto">
            <InfoCard icon="🔒" title="Security">
              Your API key is encrypted and stored only in your browser's local storage. 
              It is transmitted securely to authenticate with your Heretek Swarm backend.
            </InfoCard>
          </div>
    ```
    **Category:** Anti-pattern
    **Severity:** major

57. **'currentStep' is defined but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 107
    ```typescript
    /**
     * Progress bar showing current step
     */
    function StepProgress({ currentStep, totalSteps, currentStepIndex }: {
      currentStep: WizardStep;
      totalSteps: number;
      currentStepIndex: number;
    ```
    **Category:** Performance
    **Severity:** major

58. **' can be escaped with &apos;** (`JS-0454`)
    **File:** `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
    **Line:** 295
    ```typescript
    {/* Description */}
          <p className="text-gray-400 max-w-lg mx-auto leading-relaxed">
            Let's configure your swarm dashboard to connect to the Heretek backend services. 
            This wizard will guide you through setting up API connectivity and verifying 
            your agent infrastructure.
          </p>
    ```
    **Category:** Anti-pattern
    **Severity:** major

59. **JSX tree is too deeply nested. Found 6 levels of nesting** (`JS-0415`)
    **File:** `dashboard/frontend/src/components/SwarmControlCenter.tsx`
    **Line:** 32
    ```typescript
    const [activeView, setActiveView] = useState<View>(defaultView);
    
      return (
        <div className="min-h-screen bg-gray-950 text-white">
          {/* Header */}
          <header className="bg-gray-900 border-b border-gray-800 px-6 py-4">
            <div className="flex items-center justify-between">
    ```
    **Category:** Anti-pattern
    **Severity:** minor

60. **`SwarmControlCenter` has a cyclomatic complexity of 9 with "medium" risk** (`JS-R1005`)
    **File:** `dashboard/frontend/src/components/SwarmControlCenter.tsx`
    **Line:** 24
    ```typescript
    /**
     * SwarmControlCenter - Integrated dashboard for Heretek Swarm
     */
    export function SwarmControlCenter({
      defaultView = 'all',
      natsUrl = 'nats://localhost:4222',
      apiUrl = 'http://localhost:8000',
    ```
    **Category:** Anti-pattern
    **Severity:** minor

61. **Unexpected function declaration in the global scope, wrap in an IIFE for a local variable, assign as global property for a global variable** (`JS-0067`)
    **File:** `dashboard/frontend/src/components/SwarmControlCenter.tsx`
    **Line:** 24-149
    ```typescript
    /**
     * SwarmControlCenter - Integrated dashboard for Heretek Swarm
     */
    export function SwarmControlCenter({
      defaultView = 'all',
      natsUrl = 'nats://localhost:4222',
      apiUrl = 'http://localhost:8000',
    }: SwarmControlCenterProps) {
      const [activeView, setActiveView] = useState<View>(defaultView);
      return (
        <div className="min-h-screen bg-gray-950 text-white">
          {/* Header */}
          <header className="bg-gray-900 border-b border-gray-800 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                  Heretek Swarm Control Center
                </h1>
                <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-full">
                  Beta Agent v2.1.0
                </span>
              </div>
                        {/* View Tabs */}
              <nav className="flex items-center gap-2">
                <button
                  onClick={() => setActiveView('canvas')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    activeView === 'canvas'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-800 text-gray-400 hover:text-white'
                  }`}
                >
                  🎨 Flow Canvas
                </button>
                <button
                  onClick={() => setActiveView('tracker')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    activeView === 'tracker'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-800 text-gray-400 hover:text-white'
                  }`}
                >
                  📡 A2A Tracker
                </button>
                <button
                  onClick={() => setActiveView('garage')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    activeView === 'garage'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-800 text-gray-400 hover:text-white'
                  }`}
                >
                  🤖 Model Garage
                </button>
                <button
                  onClick={() => setActiveView('all')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    activeView === 'all'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-800 text-gray-400 hover:text-white'
                  }`}
                >
                  📊 All Views
                </button>
              </nav>
            </div>
          </header>
          {/* Main Content */}
          <main className="p-6">
            {activeView === 'canvas' && (
              <div className="h-[calc(100vh-140px)]">
                <FlowCanvas />
              </div>
            )}
            {activeView === 'tracker' && (
              <div className="h-[calc(100vh-140px)]">
                <A2ATracker natsUrl={natsUrl} />
              </div>
            )}
            {activeView === 'garage' && (
              <div className="h-[calc(100vh-140px)] overflow-auto">
                <ModelGarage />
              </div>
            )}
            {activeView === 'all' && (
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                {/* Flow Canvas - Full Width */}
                <div className="xl:col-span-2 h-[500px]">
                  <div className="h-full bg-gray-900 rounded-lg border border-gray-700">
                    <FlowCanvas />
                  </div>
                </div>
                {/* A2A Tracker */}
                <div className="h-[450px]">
                  <A2ATracker natsUrl={natsUrl} />
                </div>
                {/* Model Garage */}
                <div className="h-[450px] overflow-auto">
                  <ModelGarage />
                </div>
              </div>
            )}
          </main>
          {/* Footer */}
          <footer className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-800 px-6 py-2">
            <div className="flex items-center justify-between text-sm text-gray-500">
              <div className="flex items-center gap-4">
                <span>Agents: <span className="text-green-400">23</span></span>
                <span>Triads: <span className="text-blue-400">3</span></span>
                <span>Phase: <span className="text-purple-400">4 - A2A NATS</span></span>
              </div>
              <div className="flex items-center gap-4">
                <span>NATS: <span className="text-green-400">Connected</span></span>
                <span>API: <span className="text-green-400">Healthy</span></span>
              </div>
            </div>
          </footer>
        </div>
      );
    }
    
    export default SwarmControlCenter;
    ```
    **Category:** Anti-pattern
    **Severity:** minor

62. **'apiUrl' is assigned a value but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/SwarmControlCenter.tsx`
    **Line:** 27
    ```typescript
    export function SwarmControlCenter({
      defaultView = 'all',
      natsUrl = 'nats://localhost:4222',
      apiUrl = 'http://localhost:8000',
    }: SwarmControlCenterProps) {
      const [activeView, setActiveView] = useState<View>(defaultView);
    ```
    **Category:** Performance
    **Severity:** major

63. **'useCallback' is defined but never used** (`JS-0356`)
    **File:** `dashboard/frontend/src/components/SwarmControlCenter.tsx`
    **Line:** 8
    ```typescript
    * Combines FlowCanvas, A2ATracker, and ModelGarage into a unified interface.
     */
    
    import React, { useState, useCallback } from 'react';
    import { FlowCanvas } from '../Canvas/FlowCanvas';
    import { A2ATracker } from '../Observability/A2ATracker';
    import { ModelGarage } from '../Settings/ModelGarage';
    ```
    **Category:** Performance
    **Severity:** major

64. **Parsing error: '>' expected** (`JS-0833`)
    **File:** `dashboard/frontend/src/hooks/useDockerDetection.ts`
    **Line:** 216
    ```typescript
    : 'bg-red-500';
    
      return (
        <div className="flex items-center gap-2">
          <div className={`rounded-full ${sizeClasses[size]} ${colorClasses}`} />
          <span className="text-sm text-gray-400">
            {status.checking
    ```
    **Category:** Bug risk
    **Severity:** minor

65. **Parsing error: ':' expected** (`JS-0833`)
    **File:** `dashboard/frontend/src/utils/setupValidation.ts`
    **Line:** 449
    ```typescript
    success: false,
          latency,
          error: error instanceof Error ? error.message : 'Failed to test database connection',
          details: 'Could not connect to API to check database status', 'redis', 'postgres', 'qdrant', 'database', 'api'];
      const results: string[] = [];
      
      for (const service of services) {
    ```
    **Category:** Bug risk
    **Severity:** minor

66. **Parsing error: Unterminated string literal** (`JS-0833`)
    **File:** `electron/main.ts`
    **Line:** 1
    ```typescript
    """
    Heretek Swarm - Desktop Application Entry Point
    
    Electron main process for the Heretek Swarm desktop application.
    ```
    **Category:** Bug risk
    **Severity:** minor
### Python
**Status:** Failure
**Findings:** 168 new issues

1. **Unused import sys** (`PY-W2000`)
   **File:** `generate_docker_compose.py`
   **Line:** 1
   ```python
   import sys
   
   content = """# Heretek Swarm - Autonomous Runtime Docker Compose
   # Full stack for 24/7 continuous operation
   ```
   **Category:** Anti-pattern
   **Severity:** major

2. **Unused AlertManager imported from heretek_swarm.observability.alerting** (`PY-W2000`)
   **File:** `src/heretek_swarm/api/alerts.py`
   **Line:** 20
   ```python
   import structlog
   
   from heretek_swarm.gateway.auth import verify_auth
   from heretek_swarm.observability.alerting import (
       AlertManager,
       AlertSeverity,
       Alert,
   ```
   **Category:** Anti-pattern
   **Severity:** major

3. **Using the global statement** (`PYL-W0603`)
   **File:** `src/heretek_swarm/api/collective_evolution.py`
   **Line:** 41
   ```python
   def set_evolution_engine(engine: EvolutionEngine) -> None:
       """Set the global evolution engine instance."""
       global _evolution_engine
       _evolution_engine = engine
   ```
   **Category:** Anti-pattern
   **Severity:** minor

4. **Using the global statement** (`PYL-W0603`)
   **File:** `src/heretek_swarm/api/collective_evolution.py`
   **Line:** 61
   ```python
   def get_adaptive_learning() -> AdaptiveLearningRateController:
       """Get the adaptive learning controller, creating if necessary."""
       global _adaptive_learning
       if _adaptive_learning is None:
           _adaptive_learning = AdaptiveLearningRateController()
       return _adaptive_learning
   ```
   **Category:** Anti-pattern
   **Severity:** minor

5. **Using the global statement** (`PYL-W0603`)
   **File:** `src/heretek_swarm/api/collective_evolution.py`
   **Line:** 47
   ```python
   def set_adaptive_learning(controller: AdaptiveLearningRateController) -> None:
       """Set the global adaptive learning controller instance."""
       global _adaptive_learning
       _adaptive_learning = controller
   ```
   **Category:** Anti-pattern
   **Severity:** minor

6. **Using the global statement** (`PYL-W0603`)
   **File:** `src/heretek_swarm/api/collective_evolution.py`
   **Line:** 53
   ```python
   def get_evolution_engine() -> EvolutionEngine:
       """Get the evolution engine, creating if necessary."""
       global _evolution_engine
       if _evolution_engine is None:
           _evolution_engine = EvolutionEngine()
       return _evolution_engine
   ```
   **Category:** Anti-pattern
   **Severity:** minor

7. **Unused EvolutionResult imported from heretek_swarm.collective.adaptive_learning** (`PY-W2000`)
   **File:** `src/heretek_swarm/api/collective_evolution.py`
   **Line:** 23
   ```python
   CapabilityRecord,
       EmergentPatternDetector,
   )
   from heretek_swarm.collective.adaptive_learning import (
       AdaptiveLearningRateController,
       EvolutionResult,
       EnvironmentProfile,
   ```
   **Category:** Anti-pattern
   **Severity:** major

8. **Unused EnvironmentProfile imported from heretek_swarm.collective.adaptive_learning** (`PY-W2000`)
   **File:** `src/heretek_swarm/api/collective_evolution.py`
   **Line:** 23
   ```python
   CapabilityRecord,
       EmergentPatternDetector,
   )
   from heretek_swarm.collective.adaptive_learning import (
       AdaptiveLearningRateController,
       EvolutionResult,
       EnvironmentProfile,
   ```
   **Category:** Anti-pattern
   **Severity:** major

9. **Unused Depends imported from fastapi** (`PY-W2000`)
   **File:** `src/heretek_swarm/api/collective_evolution.py`
   **Line:** 14
   ```python
   """
   
   from typing import Any, Dict, List, Optional
   from fastapi import APIRouter, HTTPException, Depends
   import structlog
   
   from heretek_swarm.collective.emergent_detection import (
   ```
   **Category:** Anti-pattern
   **Severity:** major

10. **Unused EvolutionMetrics imported from heretek_swarm.collective.emergent_detection** (`PY-W2000`)
    **File:** `src/heretek_swarm/api/collective_evolution.py`
    **Line:** 17
    ```python
    from fastapi import APIRouter, HTTPException, Depends
    import structlog
    
    from heretek_swarm.collective.emergent_detection import (
        EvolutionEngine,
        EvolutionMetrics,
        CapabilityRecord,
    ```
    **Category:** Anti-pattern
    **Severity:** major

11. **Unused CapabilityRecord imported from heretek_swarm.collective.emergent_detection** (`PY-W2000`)
    **File:** `src/heretek_swarm/api/collective_evolution.py`
    **Line:** 17
    ```python
    from fastapi import APIRouter, HTTPException, Depends
    import structlog
    
    from heretek_swarm.collective.emergent_detection import (
        EvolutionEngine,
        EvolutionMetrics,
        CapabilityRecord,
    ```
    **Category:** Anti-pattern
    **Severity:** major

12. **Unused EmergentPatternDetector imported from heretek_swarm.collective.emergent_detection** (`PY-W2000`)
    **File:** `src/heretek_swarm/api/collective_evolution.py`
    **Line:** 17
    ```python
    from fastapi import APIRouter, HTTPException, Depends
    import structlog
    
    from heretek_swarm.collective.emergent_detection import (
        EvolutionEngine,
        EvolutionMetrics,
        CapabilityRecord,
    ```
    **Category:** Anti-pattern
    **Severity:** major

13. **Using the global statement** (`PYL-W0603`)
    **File:** `src/heretek_swarm/api/consciousness.py`
    **Line:** 64
    ```python
    def get_agency_tracker() -> AgencyMetricsTracker:
        """Get or create the agency metrics tracker instance."""
        global _agency_tracker
        if _agency_tracker is None:
            _agency_tracker = AgencyMetricsTracker()
        return _agency_tracker
    ```
    **Category:** Anti-pattern
    **Severity:** minor

14. **Unused AgencyHealthStatus imported from collective.agency_tracking** (`PY-W2000`)
    **File:** `src/heretek_swarm/api/consciousness.py`
    **Line:** 38
    ```python
    create_decision_point,
        create_resource_control,
    )
    from ..collective.agency_tracking import (
        AgencyMetricsTracker,
        AgencyMetricsSnapshot,
        AgencyThresholds,
    ```
    **Category:** Anti-pattern
    **Severity:** major

15. **Unused AgencyEvolutionData imported from collective.agency_tracking** (`PY-W2000`)
    **File:** `src/heretek_swarm/api/consciousness.py`
    **Line:** 38
    ```python
    create_decision_point,
        create_resource_control,
    )
    from ..collective.agency_tracking import (
        AgencyMetricsTracker,
        AgencyMetricsSnapshot,
        AgencyThresholds,
    ```
    **Category:** Anti-pattern
    **Severity:** major

16. **Unused create_resource_control imported from consciousness.agency_metrics** (`PY-W2000`)
    **File:** `src/heretek_swarm/api/consciousness.py`
    **Line:** 29
    ```python
    from ..plugins.manager import plugin_manager
    
    # Import agency metrics
    from ..consciousness.agency_metrics import (
        AgencyMetricsCalculator,
        AgentAgencyMetrics,
        DecisionPoint,
    ```
    **Category:** Anti-pattern
    **Severity:** major

17. **Unused create_decision_point imported from consciousness.agency_metrics** (`PY-W2000`)
    **File:** `src/heretek_swarm/api/consciousness.py`
    **Line:** 29
    ```python
    from ..plugins.manager import plugin_manager
    
    # Import agency metrics
    from ..consciousness.agency_metrics import (
        AgencyMetricsCalculator,
        AgentAgencyMetrics,
        DecisionPoint,
    ```
    **Category:** Anti-pattern
    **Severity:** major

18. **Unused AgencyMetricsSnapshot imported from collective.agency_tracking** (`PY-W2000`)
    **File:** `src/heretek_swarm/api/consciousness.py`
    **Line:** 38
    ```python
    create_decision_point,
        create_resource_control,
    )
    from ..collective.agency_tracking import (
        AgencyMetricsTracker,
        AgencyMetricsSnapshot,
        AgencyThresholds,
    ```
    **Category:** Anti-pattern
    **Severity:** major

19. **Unused AgentAgencyMetrics imported from consciousness.agency_metrics** (`PY-W2000`)
    **File:** `src/heretek_swarm/api/consciousness.py`
    **Line:** 29
    ```python
    from ..plugins.manager import plugin_manager
    
    # Import agency metrics
    from ..consciousness.agency_metrics import (
        AgencyMetricsCalculator,
        AgentAgencyMetrics,
        DecisionPoint,
    ```
    **Category:** Anti-pattern
    **Severity:** major

20. **Unused AgencyThresholds imported from collective.agency_tracking** (`PY-W2000`)
    **File:** `src/heretek_swarm/api/consciousness.py`
    **Line:** 38
    ```python
    create_decision_point,
        create_resource_control,
    )
    from ..collective.agency_tracking import (
        AgencyMetricsTracker,
        AgencyMetricsSnapshot,
        AgencyThresholds,
    ```
    **Category:** Anti-pattern
    **Severity:** major

21. **Unused variable 'calculator'** (`PYL-W0612`)
    **File:** `src/heretek_swarm/api/consciousness.py`
    **Line:** 273
    ```python
    - collective_success: Success rate of collective actions
        """
        tracker = get_agency_tracker()
        calculator = AgencyMetricsCalculator()
        
        agent_id = payload.get("agent_id")
        if not agent_id:
    ```
    **Category:** Anti-pattern
    **Severity:** major

22. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/api/logging_middleware.py`
    **Line:** 169
    ```python
    # Generate new trace ID
            return str(uuid.uuid4())
        
        def _get_client_ip(self, request: Request) -> str:
            """Get client IP address, handling proxies."""
            # Check for forwarded headers (reverse proxy)
            forwarded = request.headers.get("x-forwarded-for")
    ```
    **Category:** Performance
    **Severity:** major

23. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/api/logging_middleware.py`
    **Line:** 142
    ```python
    return False
        
        def _get_request_id(self, request: Request) -> str:
            """Extract or generate request ID."""
            # Check common request ID headers
            for header in ["x-request-id", "x-correlation-id"]:
    ```
    **Category:** Performance
    **Severity:** major

24. **Unused get_request_id imported from heretek_swarm.logging.config** (`PY-W2000`)
    **File:** `src/heretek_swarm/api/logging_middleware.py`
    **Line:** 15
    ```python
    from starlette.requests import Request
    from starlette.responses import Response
    
    from heretek_swarm.logging.config import (
        set_request_id,
        set_trace_id,
        set_agent_id,
    ```
    **Category:** Anti-pattern
    **Severity:** major

25. **Unused variable 'e'** (`PYL-W0612`)
    **File:** `src/heretek_swarm/api/logging_middleware.py`
    **Line:** 108
    ```python
    return response
                
            except Exception as e:
                # Calculate duration for error case
                duration_ms = (time.perf_counter() - start_time) * 1000
    ```
    **Category:** Anti-pattern
    **Severity:** major

26. **Using the global statement** (`PYL-W0603`)
    **File:** `src/heretek_swarm/api/main.py`
    **Line:** 84
    ```python
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan handler for startup and shutdown."""
        global supervisor, memory_store, mem0_backend
        
        # Startup
        logger.info("Starting Heretek Swarm API...")
    ```
    **Category:** Anti-pattern
    **Severity:** minor

27. **Access to a protected member _engine of a client class** (`PYL-W0212`)
    **File:** `src/heretek_swarm/api/main.py`
    **Line:** 296
    ```python
    "status": "healthy",
                    "database": "heretek_swarm",
                }
            elif memory_store and memory_store._engine:
                from sqlalchemy import text
                async with memory_store._engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
    ```
    **Category:** Bug risk
    **Severity:** minor

28. **Access to a protected member _session_factory of a client class** (`PYL-W0212`)
    **File:** `src/heretek_swarm/api/main.py`
    **Line:** 544
    ```python
    from sqlalchemy import select, func
            from heretek_swarm.memory.persistent import MemoryEntryModel
            
            async with memory_store._session_factory() as session:
                # Total count
                stmt = select(func.count()).select_from(MemoryEntryModel)
                result = await session.execute(stmt)
    ```
    **Category:** Bug risk
    **Severity:** minor

29. **Access to a protected member _engine of a client class** (`PYL-W0212`)
    **File:** `src/heretek_swarm/api/main.py`
    **Line:** 298
    ```python
    }
            elif memory_store and memory_store._engine:
                from sqlalchemy import text
                async with memory_store._engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                return {
                    "status": "healthy",
    ```
    **Category:** Bug risk
    **Severity:** minor

30. **Redefining name 'app' from outer scope** (`PYL-W0621`)
    **File:** `src/heretek_swarm/api/main.py`
    **Line:** 82
    ```python
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan handler for startup and shutdown."""
        global supervisor, memory_store, mem0_backend
    ```
    **Category:** Anti-pattern
    **Severity:** major

31. **Unused argument 'app'** (`PYL-W0613`)
    **File:** `src/heretek_swarm/api/main.py`
    **Line:** 82
    ```python
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan handler for startup and shutdown."""
        global supervisor, memory_store, mem0_backend
    ```
    **Category:** Anti-pattern
    **Severity:** major

32. **Unused get_logger imported from heretek_swarm.logging.config** (`PY-W2000`)
    **File:** `src/heretek_swarm/api/main.py`
    **Line:** 25
    ```python
    import structlog
    
    # Initialize logging with JSON output for Loki/Promtail
    from heretek_swarm.logging.config import setup_logging, get_logger, logger as logging_logger
    
    # Setup structured JSON logging
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    ```
    **Category:** Anti-pattern
    **Severity:** major

33. **Using the global statement** (`PYL-W0603`)
    **File:** `src/heretek_swarm/api/metrics.py`
    **Line:** 39
    ```python
    def get_prometheus_metrics() -> PrometheusMetrics:
        """Get or create the Prometheus metrics instance."""
        global _metrics
        if _metrics is None:
            _metrics = get_metrics()
        return _metrics
    ```
    **Category:** Anti-pattern
    **Severity:** minor

34. **SyntaxError: '(' was never closed** (`FLK-E999`)
    **File:** `src/heretek_swarm/collective/adaptive_learning.py`
    **Line:** 196
    ```python
    rate_history: List[Tuple[str, float, AdaptationReason]] = field(default_factory=list)
        
        fitness_score: float = 0.5
        behavior_pool: Dict[str, BehaviorFitness] = field(default_factory {
                "agent_id": self.agent_id,
                "current_rate": self.current_rate,
                "initial_rate": self.initial_rate,
    ```
    **Category:** Bug risk
    **Severity:** critical

35. **`AgencyMetricsTracker.get_prime_directive_report` has a cyclomatic complexity of 16 with "high" risk** (`PY-R1000`)
    **File:** `src/heretek_swarm/collective/agency_tracking.py`
    **Line:** 564
    ```python
    predicted_next=predicted_next,
            )
        
        def get_prime_directive_report(self) -> PrimeDirectiveComplianceReport:
            """
            Generate overall Prime Directive compliance report for the swarm.
    ```
    **Category:** Anti-pattern
    **Severity:** minor

36. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/collective/agency_tracking.py`
    **Line:** 742
    ```python
    # Helper methods
        
        def _calculate_std(self, values: List[float]) -> float:
            """Calculate standard deviation."""
            if len(values) < 2:
                return 0.0
    ```
    **Category:** Performance
    **Severity:** major

37. **Unused import asyncio** (`PY-W2000`)
    **File:** `src/heretek_swarm/collective/agency_tracking.py`
    **Line:** 20
    ```python
    Date: 2026-04-10
    """
    
    import asyncio
    import math
    import uuid
    from dataclasses import dataclass, field
    ```
    **Category:** Anti-pattern
    **Severity:** major

38. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/collective/agency_tracking.py`
    **Line:** 764
    ```python
    else:
                return sorted_values[n // 2]
        
        def _calculate_trend_slope(self, values: List[float]) -> float:
            """Calculate trend slope using simple linear regression."""
            if len(values) < 2:
                return 0.0
    ```
    **Category:** Performance
    **Severity:** major

39. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/collective/agency_tracking.py`
    **Line:** 751
    ```python
    variance = sum((v - mean) ** 2 for v in values) / len(values)
            return math.sqrt(variance)
        
        def _calculate_median(self, values: List[float]) -> float:
            """Calculate median."""
            if not values:
                return 0.0
    ```
    **Category:** Performance
    **Severity:** major

40. **SyntaxError: unmatched ']'** (`FLK-E999`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 92
    ```python
    first_observed: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
        last_reinforced: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
        stabilization_time: Optional]:
            return {
                "capability_id": self.capability_id,
                "capability_type": self.capability_type,
    ```
    **Category:** Bug risk
    **Severity:** critical

41. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/consciousness/agency_metrics.py`
    **Line:** 596
    ```python
    return max(0.0, min(1.0, alignment))
        
        def calculate_resource_autonomy(
            self,
            resources: List[ResourceControl],
        ) -> Tuple[float, float]:
    ```
    **Category:** Performance
    **Severity:** major

42. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/consciousness/agency_metrics.py`
    **Line:** 542
    ```python
    return self_initiated / denominator
        
        def calculate_goal_alignment_score(
            self,
            individual_actions: int,
            collective_actions: int,
    ```
    **Category:** Performance
    **Severity:** major

43. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/consciousness/agency_metrics.py`
    **Line:** 511
    ```python
    return max(0.0, min(1.0, self_det))
        
        def calculate_autonomous_action_ratio(
            self,
            actions: List[ActionOrigin],
        ) -> float:
    ```
    **Category:** Performance
    **Severity:** major

44. **Unused variable 'recommendations'** (`PYL-W0612`)
    **File:** `src/heretek_swarm/consciousness/agency_metrics.py`
    **Line:** 777
    ```python
    )
            
            # Calculate Prime Directive compliance
            compliance, details, recommendations = self.calculate_prime_directive_compliance(
                metrics, decisions
            )
            metrics.prime_directive_compliance = compliance
    ```
    **Category:** Anti-pattern
    **Severity:** major

45. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/consciousness/agency_metrics.py`
    **Line:** 448
    ```python
    return max(0.0, min(1.0, agency))
        
        def calculate_self_determination_index(
            self,
            decisions: List[DecisionPoint],
        ) -> float:
    ```
    **Category:** Performance
    **Severity:** major

46. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/consciousness/agency_metrics.py`
    **Line:** 416
    ```python
    return max(0.0, min(1.0, autonomy))
        
        def calculate_agency_score(
            self,
            autonomy_score: float,
            self_determination_index: float,
    ```
    **Category:** Performance
    **Severity:** major

47. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/consciousness/agency_metrics.py`
    **Line:** 641
    ```python
    sum(independences) / len(independences)
            )
        
        def calculate_prime_directive_compliance(
            self,
            metrics: AgentAgencyMetrics,
            decisions: List[DecisionPoint],
    ```
    **Category:** Performance
    **Severity:** major

48. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/consciousness/agency_metrics.py`
    **Line:** 357
    ```python
    message="Weights do not sum to 1.0, normalizing..."
                )
        
        def calculate_autonomy_score(
            self,
            decisions: List[DecisionPoint],
            actions: List[ActionOrigin],
    ```
    **Category:** Performance
    **Severity:** major

49. **Unused TrainingResult imported from heretek_swarm.consciousness.phi_training** (`PY-W2000`)
    **File:** `src/heretek_swarm/consciousness/__init__.py`
    **Line:** 24
    ```python
    FreeEnergyCalculator,
        FEPResult,
    )
    from heretek_swarm.consciousness.phi_training import (
        PhiTrainingEnvironment,
        TrainingScenario,
        TrainingResult,
    ```
    **Category:** Anti-pattern
    **Severity:** major

50. **Unused ScenarioType imported from heretek_swarm.consciousness.phi_training** (`PY-W2000`)
    **File:** `src/heretek_swarm/consciousness/__init__.py`
    **Line:** 24
    ```python
    FreeEnergyCalculator,
        FEPResult,
    )
    from heretek_swarm.consciousness.phi_training import (
        PhiTrainingEnvironment,
        TrainingScenario,
        TrainingResult,
    ```
    **Category:** Anti-pattern
    **Severity:** major

51. **Unused PhiTrainingEnvironment imported from heretek_swarm.consciousness.phi_training** (`PY-W2000`)
    **File:** `src/heretek_swarm/consciousness/__init__.py`
    **Line:** 24
    ```python
    FreeEnergyCalculator,
        FEPResult,
    )
    from heretek_swarm.consciousness.phi_training import (
        PhiTrainingEnvironment,
        TrainingScenario,
        TrainingResult,
    ```
    **Category:** Anti-pattern
    **Severity:** major

52. **Unused TrainingScenario imported from heretek_swarm.consciousness.phi_training** (`PY-W2000`)
    **File:** `src/heretek_swarm/consciousness/__init__.py`
    **Line:** 24
    ```python
    FreeEnergyCalculator,
        FEPResult,
    )
    from heretek_swarm.consciousness.phi_training import (
        PhiTrainingEnvironment,
        TrainingScenario,
        TrainingResult,
    ```
    **Category:** Anti-pattern
    **Severity:** major

53. **Unused TrainingMode imported from heretek_swarm.consciousness.phi_training** (`PY-W2000`)
    **File:** `src/heretek_swarm/consciousness/__init__.py`
    **Line:** 24
    ```python
    FreeEnergyCalculator,
        FEPResult,
    )
    from heretek_swarm.consciousness.phi_training import (
        PhiTrainingEnvironment,
        TrainingScenario,
        TrainingResult,
    ```
    **Category:** Anti-pattern
    **Severity:** major

54. **Unused TrainingEpisode imported from heretek_swarm.consciousness.phi_training** (`PY-W2000`)
    **File:** `src/heretek_swarm/consciousness/__init__.py`
    **Line:** 24
    ```python
    FreeEnergyCalculator,
        FEPResult,
    )
    from heretek_swarm.consciousness.phi_training import (
        PhiTrainingEnvironment,
        TrainingScenario,
        TrainingResult,
    ```
    **Category:** Anti-pattern
    **Severity:** major

55. **SyntaxError: unterminated string literal (detected at line 109)** (`FLK-E999`)
    **File:** `src/heretek_swarm/consciousness/self_model.py`
    **Line:** 109
    ```python
    "parent_goal_id": self.parent_goal_id,
                "progress": self.progress,
                "associated_beliefs": self.associated_beliefs,
                "blockedError:
                status = GoalStatus.ACTIVE
            return cls(
                goal_id=data.get("goal_id", str(uuid.uuid4())),
    ```
    **Category:** Bug risk
    **Severity:** critical

56. **SyntaxError: unterminated string literal (detected at line 99)** (`FLK-E999`)
    **File:** `src/heretek_swarm/llm/model_garage.py`
    **Line:** 99
    ```python
    timeout: float = 60.0
        retry_count: int = 3
        retry_delay: float = 1.0
        health_status: str = "unknown            "id": self.id,
                "name": self.name,
                "provider_type": self.provider_type.value,
                "base_url": self.base_url,
    ```
    **Category:** Bug risk
    **Severity:** critical

57. **Variadics removed in overriding 'ContextAdder.__call__' method** (`PYL-W0221`)
    **File:** `src/heretek_swarm/logging/config.py`
    **Line:** 89
    ```python
    class ContextAdder(Processor):
        """Processor that adds context variables to log entries."""
    
        def __call__(self, logger, method_name, event_dict):
            # Add request tracing context
            if request_id := get_request_id():
                event_dict["request_id"] = request_id
    ```
    **Category:** Bug risk
    **Severity:** minor

58. **Redefining name 'logger' from outer scope** (`PYL-W0621`)
    **File:** `src/heretek_swarm/logging/config.py`
    **Line:** 100
    ```python
    return event_dict
    
    
    def add_service_info(logger, method_name, event_dict):
        """Add service information to all log entries."""
        event_dict["service"] = "heretek-swarm"
        event_dict["environment"] = get_environment()
    ```
    **Category:** Anti-pattern
    **Severity:** major

59. **Redefining name 'logger' from outer scope** (`PYL-W0621`)
    **File:** `src/heretek_swarm/logging/config.py`
    **Line:** 89
    ```python
    class ContextAdder(Processor):
        """Processor that adds context variables to log entries."""
    
        def __call__(self, logger, method_name, event_dict):
            # Add request tracing context
            if request_id := get_request_id():
                event_dict["request_id"] = request_id
    ```
    **Category:** Anti-pattern
    **Severity:** major

60. **Unused filter_by_level imported from structlog.stdlib** (`PY-W2000`)
    **File:** `src/heretek_swarm/logging/config.py`
    **Line:** 16
    ```python
    import structlog
    from structlog.types import Processor
    from structlog.stdlib import (
        add_log_level,
        add_logger_name,
        filter_by_level,
    ```
    **Category:** Anti-pattern
    **Severity:** major

61. **Unused add_log_level imported from structlog.stdlib** (`PY-W2000`)
    **File:** `src/heretek_swarm/logging/config.py`
    **Line:** 16
    ```python
    import structlog
    from structlog.types import Processor
    from structlog.stdlib import (
        add_log_level,
        add_logger_name,
        filter_by_level,
    ```
    **Category:** Anti-pattern
    **Severity:** major

62. **Unused add_logger_name imported from structlog.stdlib** (`PY-W2000`)
    **File:** `src/heretek_swarm/logging/config.py`
    **Line:** 16
    ```python
    import structlog
    from structlog.types import Processor
    from structlog.stdlib import (
        add_log_level,
        add_logger_name,
        filter_by_level,
    ```
    **Category:** Anti-pattern
    **Severity:** major

63. **Unused argument 'logger'** (`PYL-W0613`)
    **File:** `src/heretek_swarm/logging/config.py`
    **Line:** 100
    ```python
    return event_dict
    
    
    def add_service_info(logger, method_name, event_dict):
        """Add service information to all log entries."""
        event_dict["service"] = "heretek-swarm"
        event_dict["environment"] = get_environment()
    ```
    **Category:** Anti-pattern
    **Severity:** major

64. **Unused argument 'method_name'** (`PYL-W0613`)
    **File:** `src/heretek_swarm/logging/config.py`
    **Line:** 100
    ```python
    return event_dict
    
    
    def add_service_info(logger, method_name, event_dict):
        """Add service information to all log entries."""
        event_dict["service"] = "heretek-swarm"
        event_dict["environment"] = get_environment()
    ```
    **Category:** Anti-pattern
    **Severity:** major

65. **Using the global statement** (`PYL-W0603`)
    **File:** `src/heretek_swarm/observability/alerting.py`
    **Line:** 258
    ```python
    def get_alert_manager() -> AlertManager:
        """Get the global alert manager instance."""
        global _alert_manager
        if _alert_manager is None:
            _alert_manager = AlertManager()
        return _alert_manager
    ```
    **Category:** Anti-pattern
    **Severity:** minor

66. **Consider merging collapsible `With` statements`** (`PTC-W0062`)
    **File:** `src/heretek_swarm/observability/alerting.py`
    **Line:** 181
    ```python
    "Authorization": f"GenieKey {os.getenv('OPSGENIE_API_KEY')}",
                }
    
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://api.opsgenie.com/v2/alerts",
                        json=payload,
    ```
    **Category:** Anti-pattern
    **Severity:** major

67. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/observability/alerting.py`
    **Line:** 155
    ```python
    logger.error("pagerduty_alert_error", error=str(e))
                return False
    
        async def _send_opsgenie(self, alert: Alert) -> bool:
            """Send alert to OpsGenie Alerts API."""
            try:
                import aiohttp
    ```
    **Category:** Performance
    **Severity:** major

68. **Unused import asyncio** (`PY-W2000`)
    **File:** `src/heretek_swarm/observability/alerting.py`
    **Line:** 30
    ```python
    from datetime import datetime, timezone
    from enum import Enum
    from typing import Any, Dict, List, Optional
    import asyncio
    
    import structlog
    ```
    **Category:** Anti-pattern
    **Severity:** major

69. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/observability/alerting.py`
    **Line:** 117
    ```python
    return success
    
        async def _send_pagerduty(self, alert: Alert) -> bool:
            """Send alert to PagerDuty Events API v2."""
            try:
                import aiohttp
    ```
    **Category:** Performance
    **Severity:** major

70. **Consider merging collapsible `With` statements`** (`PTC-W0062`)
    **File:** `src/heretek_swarm/observability/alerting.py`
    **Line:** 139
    ```python
    }
                }
    
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://events.pagerduty.com/v2/enqueue",
                        json=payload,
    ```
    **Category:** Anti-pattern
    **Severity:** major

71. **SyntaxError: unterminated triple-quoted string literal (detected at line 627)** (`FLK-E999`)
    **File:** `src/heretek_swarm/observability/__init__.py`
    **Line:** 595
    ```python
    # ============================================================================
    
    async def main():
        """Example usage of observability."""None
        # Initialize
        obs = await initialize_observability()
    ```
    **Category:** Bug risk
    **Severity:** critical

72. **Using the global statement** (`PYL-W0603`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 356
    ```python
    def reset_metrics() -> None:
        """Reset the global metrics instance."""
        global _metrics_instance
        _metrics_instance = None
    ```
    **Category:** Anti-pattern
    **Severity:** minor

73. **Access to a protected member _agent_types of a client class** (`PYL-W0212`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 367
    ```python
    def increment_tasks_completed(agent_id: str, task_type: str = "general") -> None:
        """Convenience function to increment completed tasks counter."""
        metrics = get_metrics()
        agent_type = metrics._agent_types.get(agent_id, "unknown")
        metrics.record_task_completed(agent_id, agent_type, task_type)
    ```
    **Category:** Bug risk
    **Severity:** minor

74. **Access to a protected member _value of a client class** (`PYL-W0212`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 222
    ```python
    agent_type = self._agent_types.pop(agent_id, "unknown")
            heretek_swarm_agents_total.labels(agent_type=agent_type).dec()
            heretek_swarm_agents_active.labels(agent_type=agent_type).dec(max(
                heretek_swarm_agents_active.labels(agent_type=agent_type)._value.get(), 0
            ))
    
        def record_task_completed(
    ```
    **Category:** Bug risk
    **Severity:** minor

75. **Using the global statement** (`PYL-W0603`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 348
    ```python
    Returns:
            The singleton PrometheusMetrics instance.
        """
        global _metrics_instance
        if _metrics_instance is None:
            _metrics_instance = PrometheusMetrics()
        return _metrics_instance
    ```
    **Category:** Anti-pattern
    **Severity:** minor

76. **Access to a protected member _agent_types of a client class** (`PYL-W0212`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 374
    ```python
    def increment_tasks_failed(agent_id: str, task_type: str = "general") -> None:
        """Convenience function to increment failed tasks counter."""
        metrics = get_metrics()
        agent_type = metrics._agent_types.get(agent_id, "unknown")
        metrics.record_task_failed(agent_id, agent_type, task_type)
    ```
    **Category:** Bug risk
    **Severity:** minor

77. **Redefining name 'time' from outer scope** (`PYL-W0621`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 437
    ```python
    from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.requests import Request
        from starlette.responses import Response
        import time
    
        class PrometheusMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next):
    ```
    **Category:** Anti-pattern
    **Severity:** major

78. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 291
    ```python
    uptime = time.time() - self._start_time
            heretek_swarm_uptime_seconds.set(uptime)
    
        def _normalize_endpoint(self, endpoint: str) -> str:
            """
            Normalize endpoint to reduce cardinality.
    ```
    **Category:** Performance
    **Severity:** major

79. **Reimport 'time' (imported line 50)** (`PYL-W0404`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 437
    ```python
    from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.requests import Request
        from starlette.responses import Response
        import time
    
        class PrometheusMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next):
    ```
    **Category:** Bug risk
    **Severity:** major

80. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 322
    ```python
    self.update_uptime()
            return generate_latest(self._registry)
    
        def get_content_type(self) -> str:
            """Get the Prometheus content type."""
            return CONTENT_TYPE_LATEST
    ```
    **Category:** Performance
    **Severity:** major

81. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 241
    ```python
    agent_id=agent_id, task_type=task_type
            ).inc()
    
        def record_message_sent(self, message_type: str = "general") -> None:
            """Record a sent message."""
            heretek_swarm_messages_total.labels(direction="sent", message_type=message_type).inc()
    ```
    **Category:** Performance
    **Severity:** major

82. **Unused wraps imported from functools** (`PY-W2000`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 51
    ```python
    )
    from typing import Optional, Dict, Any
    import time
    from functools import wraps
    
    # Default registry (use default to allow automatic metric collection)
    DEFAULT_REGISTRY = REGISTRY
    ```
    **Category:** Anti-pattern
    **Severity:** major

83. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 251
    ```python
    direction="received", message_type=message_type
            ).inc()
    
        def record_consensus_round(
            self, consensus_type: str = "deliberation", outcome: str = "success"
        ) -> None:
            """Record a consensus round."""
    ```
    **Category:** Performance
    **Severity:** major

84. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 213
    ```python
    """Record an agent becoming active."""
            heretek_swarm_agents_active.labels(agent_type=agent_type).inc()
    
        def record_agent_inactive(self, agent_id: str, agent_type: str = "unknown") -> None:
            """Record an agent becoming inactive."""
            heretek_swarm_agents_active.labels(agent_type=agent_type).dec()
    ```
    **Category:** Performance
    **Severity:** major

85. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 225
    ```python
    heretek_swarm_agents_active.labels(agent_type=agent_type)._value.get(), 0
            ))
    
        def record_task_completed(
            self, agent_id: str, agent_type: str = "unknown", task_type: str = "general"
        ) -> None:
            """Record a task completion."""
    ```
    **Category:** Performance
    **Severity:** major

86. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 209
    ```python
    self._agent_types[agent_id] = agent_type
            heretek_swarm_agents_total.labels(agent_type=agent_type).inc()
    
        def record_agent_active(self, agent_id: str, agent_type: str = "unknown") -> None:
            """Record an agent becoming active."""
            heretek_swarm_agents_active.labels(agent_type=agent_type).inc()
    ```
    **Category:** Performance
    **Severity:** major

87. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 245
    ```python
    """Record a sent message."""
            heretek_swarm_messages_total.labels(direction="sent", message_type=message_type).inc()
    
        def record_message_received(self, message_type: str = "general") -> None:
            """Record a received message."""
            heretek_swarm_messages_total.labels(
                direction="received", message_type=message_type
    ```
    **Category:** Performance
    **Severity:** major

88. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 263
    ```python
    """Record a consciousness phi score."""
            heretek_swarm_phi_score.labels(agent_id=agent_id).set(score)
    
        def record_free_energy(self, agent_id: str, energy: float) -> None:
            """Record a free energy level."""
            heretek_swarm_free_energy.labels(agent_id=agent_id).set(energy)
    ```
    **Category:** Performance
    **Severity:** major

89. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 233
    ```python
    agent_id=agent_id, task_type=task_type
            ).inc()
    
        def record_task_failed(
            self, agent_id: str, agent_type: str = "unknown", task_type: str = "general"
        ) -> None:
            """Record a task failure."""
    ```
    **Category:** Performance
    **Severity:** major

90. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 282
    ```python
    method=method, endpoint=normalized_endpoint, status=str(status)
            ).inc()
    
        def record_health_score(self, score: float) -> None:
            """Record the overall health score."""
            heretek_swarm_health_score.set(score)
    ```
    **Category:** Performance
    **Severity:** major

91. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 259
    ```python
    consensus_type=consensus_type, outcome=outcome
            ).inc()
    
        def record_phi_score(self, agent_id: str, score: float) -> None:
            """Record a consciousness phi score."""
            heretek_swarm_phi_score.labels(agent_id=agent_id).set(score)
    ```
    **Category:** Performance
    **Severity:** major

92. **Unused Response imported from starlette.responses** (`PY-W2000`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 436
    ```python
    """
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.requests import Request
        from starlette.responses import Response
        import time
    
        class PrometheusMiddleware(BaseHTTPMiddleware):
    ```
    **Category:** Anti-pattern
    **Severity:** major

93. **Using the global statement** (`PYL-W0603`)
    **File:** `src/heretek_swarm/observability/tracing.py`
    **Line:** 63
    ```python
    Returns:
            Configured tracer instance
        """
        global _tracer
        
        # Create resource with service information
        resource = Resource.create({
    ```
    **Category:** Anti-pattern
    **Severity:** minor

94. **Using the global statement** (`PYL-W0603`)
    **File:** `src/heretek_swarm/observability/tracing.py`
    **Line:** 119
    ```python
    def get_tracer() -> trace.Tracer:
        """Get the global tracer instance, initializing if necessary."""
        global _tracer
        if _tracer is None:
            _tracer = initialize_tracing()
        return _tracer
    ```
    **Category:** Anti-pattern
    **Severity:** minor

95. **Unused Context imported from opentelemetry.context** (`PY-W2000`)
    **File:** `src/heretek_swarm/observability/tracing.py`
    **Line:** 31
    ```python
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.trace import Status, StatusCode, Span
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    from opentelemetry.context import Context
    from opentelemetry.propagate import set_global_textmap
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    ```
    **Category:** Anti-pattern
    **Severity:** major

96. **SyntaxError: unterminated string literal (detected at line 52)** (`FLK-E999`)
    **File:** `temp_self_model_part1.py`
    **Line:** 52
    ```python
    "source": self.source,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "supporting_evidence": self.support_type", "factual"))
            except ValueError:
                belief_type = BeliefType.FACTUAL
            return cls(
    ```
    **Category:** Bug risk
    **Severity:** critical

97. **Unused import asyncio** (`PY-W2000`)
    **File:** `tests/collective/test_evolution_mechanisms.py`
    **Line:** 13
    ```python
    """
    
    import pytest
    import asyncio
    from datetime import datetime, timezone
    from typing import Any, Dict, List
    ```
    **Category:** Anti-pattern
    **Severity:** major

98. **Unused AdaptationReason imported from heretek_swarm.collective.adaptive_learning** (`PY-W2000`)
    **File:** `tests/collective/test_evolution_mechanisms.py`
    **Line:** 24
    ```python
    AgentCapabilitySnapshot,
        EvolutionPhase,
    )
    from heretek_swarm.collective.adaptive_learning import (
        AdaptiveLearningRateController,
        LearningRateConfig,
        LearningRateStrategy,
    ```
    **Category:** Anti-pattern
    **Severity:** major

99. **Unused AgentCapabilitySnapshot imported from heretek_swarm.collective.emergent_detection** (`PY-W2000`)
    **File:** `tests/collective/test_evolution_mechanisms.py`
    **Line:** 17
    ```python
    from datetime import datetime, timezone
    from typing import Any, Dict, List
    
    from heretek_swarm.collective.emergent_detection import (
        EvolutionEngine,
        EvolutionMetrics,
        CapabilityRecord,
    ```
    **Category:** Anti-pattern
    **Severity:** major

100. **Unused datetime imported from datetime** (`PY-W2000`)
     **File:** `tests/collective/test_evolution_mechanisms.py`
     **Line:** 14
     ```python
     import pytest
     import asyncio
     from datetime import datetime, timezone
     from typing import Any, Dict, List
     
     from heretek_swarm.collective.emergent_detection import (
     ```
     **Category:** Anti-pattern
     **Severity:** major

*...and 80 more occurrences. [See full list on DeepSource](https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/18c4f891-816a-4a30-b173-84e564f0231f/).*### Secrets
**Status:** Failure
**Findings:** 12 new issues

1. **Audit: Hardcoded credential "YOUR_SERVICE_KEY" found in source code** (`SCT-A000`)
   **File:** `docs/MONITORING.md`
   **Line:** 199
   ```markdown
   - name: 'pagerduty'
       pagerduty_configs:
         - service_key: 'YOUR_SERVICE_KEY'None
           severity: critical
           send_resolved: true
   ```
   **Category:** Secrets
   **Severity:** minor

2. **Audit: Hardcoded credential "Optional[str]" found in source code** (`SCT-A000`)
   **File:** `SECURITY_AUDIT_PART2.md`
   **Line:** 338
   ```markdown
   class WebSocketAuthManager:
       """Manages authentication for WebSocket connections."""
       
       def __init__(self, secret_key: Optional[str] = None):
           self.secret_key = secret_key or os.environ.get(
               "WEBSOCKET_SECRET_KEY", 
               secrets.token_hex(32)  # Generated at startup!
   ```
   **Category:** Secrets
   **Severity:** minor

3. **Audit: Hardcoded credential "secrets.token_urlsafe(32)" found in source code** (`SCT-A000`)
   **File:** `SECURITY_AUDIT_PART2.md`
   **Line:** 306
   ```markdown
   return self._tokens.get(token)
       
       async def generate_token(self, agent_id: str, permissions: Optional[List[str]] = None) -> str:
           token = secrets.token_urlsafe(32)
           token_data = {
               "agent_id": agent_id,
               "created_at": datetime.now(timezone.utc).isoformat(),
   ```
   **Category:** Secrets
   **Severity:** minor

4. **Audit: Hardcoded credential "{token}\"," found in source code** (`SCT-A000`)
   **File:** `SECURITY_AUDIT_PART2.md`
   **Line:** 316
   ```markdown
   if self._redis:
               await self._redis.setex(
                   f"auth_token:{token}",
                   int(self._token_expiry.total_seconds()),
                   json.dumps(token_data)
               )
   ```
   **Category:** Secrets
   **Severity:** minor

5. **Audit: Hardcoded credential "openai_api_key," found in source code** (`SCT-A000`)
   **File:** `SECURITY_AUDIT_PART2.md`
   **Line:** 622
   ```markdown
   mem0_config = Mem0Config(
       qdrant_host=qdrant_host,
       qdrant_port=int(qdrant_port),
       openai_api_key=openai_api_key,
   )
   
   # Add processor to structlog to redact sensitive values
   ```
   **Category:** Secrets
   **Severity:** minor

6. **Audit: Hardcoded credential "consensus_auth_manager.generate_token(agent_id," found in source code** (`SCT-A000`)
   **File:** `SECURITY_AUDIT_PART2.md`
   **Line:** 81
   ```markdown
   """
       Generate an authentication token for an agent.
       """
       token = consensus_auth_manager.generate_token(agent_id, permissions)
       return {
           "token": token,
           "agent_id": agent_id,
   ```
   **Category:** Secrets
   **Severity:** minor

7. **Audit: Hardcoded credential "Optional[str]" found in source code** (`SCT-A000`)
   **File:** `SECURITY_AUDIT_PART2.md`
   **Line:** 358
   ```markdown
   **Recommended Fix:**
   ```python
   class WebSocketAuthManager:
       def __init__(self, secret_key: Optional[str] = None):
           key = secret_key or os.environ.get("WEBSOCKET_SECRET_KEY")
           if not key:
               raise RuntimeError(
   ```
   **Category:** Secrets
   **Severity:** minor

8. **Audit: Hardcoded credential "openai_api_key," found in source code** (`SCT-A000`)
   **File:** `SECURITY_AUDIT_PART2.md`
   **Line:** 604
   ```markdown
   mem0_config = Mem0Config(
               qdrant_host=qdrant_host,
               qdrant_port=int(qdrant_port),
               openai_api_key=openai_api_key,  # Potentially sensitive
           )
   ```
   ```
   **Category:** Secrets
   **Severity:** minor

9. **Audit: Hardcoded credential "consensus_auth_manager.generate_token(agent_id," found in source code** (`SCT-A000`)
   **File:** `SECURITY_AUDIT_PART2.md`
   **Line:** 119
   ```markdown
   # Add rate limiting check here
       # ...
       
       token = consensus_auth_manager.generate_token(agent_id, permissions)
       return {
           "token": token,
           "agent_id": agent_id,
   ```
   **Category:** Secrets
   **Severity:** minor

10. **Audit: Hardcoded credential "{token}\")" found in source code** (`SCT-A000`)
    **File:** `SECURITY_AUDIT_PART2.md`
    **Line:** 301
    ```markdown
    async def _get_from_storage(self, token: str) -> Optional[Dict]:
            if self._redis:
                data = await self._redis.get(f"auth_token:{token}")
                return json.loads(data) if data else None
            return self._tokens.get(token)
    ```
    **Category:** Secrets
    **Severity:** minor

11. **Hardcoded credential "os.environ.get(\"CONFIG_ENCRYPTION_KEY\")" found in source code** (`SCT-1000`)
    **File:** `SECURITY_AUDIT_PART2.md`
    **Line:** 648
    ```markdown
    ```python
    # Initialize Fernet encryption for API keys
    self._fernet: Optional[Fernet] = None
    self._encryption_key = os.environ.get("CONFIG_ENCRYPTION_KEY")
    if self._encryption_key:
        self._initialize_encryption()
    else:
    ```
    **Category:** Secrets
    **Severity:** critical

12. **Hardcoded credential "os.environ.get(\"CONFIG_ENCRYPTION_KEY\")" found in source code** (`SCT-1000`)
    **File:** `SECURITY_AUDIT_PART2.md`
    **Line:** 667
    ```markdown
    **Recommended Fix:**
    ```python
    self._encryption_key = os.environ.get("CONFIG_ENCRYPTION_KEY")
    environment = os.environ.get("ENVIRONMENT", "development")
    
    if not self._encryption_key:
    ```
    **Category:** Secrets
    **Severity:** critical
### Docker
**Status:** Success
**Findings:** No new issues detected

# DeepSource Code Review Report

**Repository:** Heretek-AI/heretek-swarm
**Branch:** `main`
**Commit:** eaf8b52...3338695
**Run:** [https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/ef8adaa7-80dd-4f31-b602-a0e32523dd28/](https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/ef8adaa7-80dd-4f31-b602-a0e32523dd28/)

---

## Summary
- **Secrets:** No issues detected- **Shell:** No issues detected- **Docker:** No issues detected- **SQL:** No issues detected- **JavaScript:** No issues detected- **Python:** 32 issues

---

## Code Review Findings
### Secrets
**Status:** Success
**Findings:** No new issues detected
### Shell
**Status:** Success
**Findings:** No new issues detected
### Docker
**Status:** Success
**Findings:** No new issues detected
### SQL
**Status:** Success
**Findings:** No new issues detected
### JavaScript
**Status:** Success
**Findings:** No new issues detected
### Python
**Status:** Failure
**Findings:** 32 new issues

1. **Using the global statement** (`PYL-W0603`)
   **File:** `src/heretek_swarm/observability/__init__.py`
   **Line:** 584
   ```python
   async def initialize_observability() -> ObservabilityManager:
       """Initialize and return the global observability manager."""
       global _observability
       _observability = ObservabilityManager()
       await _observability.initialize()
       return _observability
   ```
   **Category:** Anti-pattern
   **Severity:** minor

2. **Function is missing a return type annotation** (`TYP-051`)
   **File:** `src/heretek_swarm/observability/__init__.py`
   **Line:** 600
   ```python
   obs = await initialize_observability()
   
       # Register health check
       async def check_api():
           return True  # Replace with actual check
   
       obs.register_health_check("api", check_api)
   ```
   **Category:** Type check
   **Severity:** minor

3. **Function is missing a return type annotation** (`TYP-051`)
   **File:** `src/heretek_swarm/observability/__init__.py`
   **Line:** 442
   ```python
   # Tracing
       # =========================================================================
   
       def trace_span(
           self,
           name: str,
           agent_id: Optional[str] = None,
   ```
   **Category:** Type check
   **Severity:** minor

4. **Using the global statement** (`PYL-W0603`)
   **File:** `src/heretek_swarm/observability/__init__.py`
   **Line:** 576
   ```python
   def get_observability() -> ObservabilityManager:
       """Get the global observability manager instance."""
       global _observability
       if _observability is None:
           _observability = ObservabilityManager()
       return _observability
   ```
   **Category:** Anti-pattern
   **Severity:** minor

5. **Function is missing a return type annotation** (`TYP-051`)
   **File:** `src/heretek_swarm/observability/__init__.py`
   **Line:** 594
   ```python
   # Example Usage
   # ============================================================================
   
   async def main():
       """Example usage of observability."""
       # Initialize
       obs = await initialize_observability()
   ```
   **Category:** Type check
   **Severity:** minor

6. **Function is missing a type annotation for one or more arguments** (`TYP-051`)
   **File:** `src/heretek_swarm/observability/__init__.py`
   **Line:** 458
   ```python
   return span_context(name, attributes=span_attributes)
   
       async def traced(
           self,
           name: str,
           agent_id: Optional[str] = None,
   ```
   **Category:** Type check
   **Severity:** minor

7. **Function is missing a return type annotation** (`TYP-051`)
   **File:** `src/heretek_swarm/observability/__init__.py`
   **Line:** 376
   ```python
   self.logger.info("Observability manager shutdown complete")
   
       @property
       def logger(self):
           """Get structlog logger."""
           return structlog.get_logger("observability")
   ```
   **Category:** Type check
   **Severity:** minor

8. **Function is missing a return type annotation** (`TYP-051`)
   **File:** `src/heretek_swarm/observability/__init__.py`
   **Line:** 458
   ```python
   return span_context(name, attributes=span_attributes)
   
       async def traced(
           self,
           name: str,
           agent_id: Optional[str] = None,
   ```
   **Category:** Type check
   **Severity:** minor

9. **Configuring loggers is security sensitive** (`PY-A6006`)
   **File:** `src/heretek_swarm/observability/__init__.py`
   **Line:** 92
   ```python
   # Loki Log Handler
   # ============================================================================
   
   class LokiHandler(logging.Handler):
       """
       Custom logging handler that sends logs to Loki.
   ```
   **Category:** Security
   **Severity:** minor

10. **Function is missing a return type annotation** (`TYP-051`)
    **File:** `src/heretek_swarm/observability/__init__.py`
    **Line:** 136
    ```python
    # Create current log file
            self._current_file = self.log_dir / f"{service_name}-{datetime.now().strftime('%Y%m%d')}.jsonl"
    
        async def _get_client(self):
            """Get or create HTTP client."""
            if self._http_client is None:
                import httpx
    ```
    **Category:** Type check
    **Severity:** minor

11. **Function is missing a type annotation for one or more arguments** (`TYP-051`)
    **File:** `src/heretek_swarm/observability/__init__.py`
    **Line:** 544
    ```python
    # Structured Logging
        # =========================================================================
    
        def log(
            self,
            level: LogLevel,
            message: str,
    ```
    **Category:** Type check
    **Severity:** minor

12. **Function is missing a type annotation for one or more arguments** (`TYP-051`)
    **File:** `src/heretek_swarm/observability/__init__.py`
    **Line:** 442
    ```python
    # Tracing
        # =========================================================================
    
        def trace_span(
            self,
            name: str,
            agent_id: Optional[str] = None,
    ```
    **Category:** Type check
    **Severity:** minor

13. **Redefining name 'span_context' from outer scope** (`PYL-W0621`)
    **File:** `src/heretek_swarm/observability/__init__.py`
    **Line:** 466
    ```python
    **attributes,
        ):
            """Async context manager for tracing."""
            from .tracing import span_context
            span_attributes = {**attributes}
            if agent_id:
                span_attributes["agent_id"] = agent_id
    ```
    **Category:** Anti-pattern
    **Severity:** major

14. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/observability/__init__.py`
    **Line:** 458
    ```python
    return span_context(name, attributes=span_attributes)
    
        async def traced(
            self,
            name: str,
            agent_id: Optional[str] = None,
    ```
    **Category:** Performance
    **Severity:** major

15. **Unused import uuid** (`PY-W2000`)
    **File:** `src/heretek_swarm/observability/__init__.py`
    **Line:** 30
    ```python
    from enum import Enum
    from pathlib import Path
    from typing import Any, Callable, Dict, List, Optional
    import uuid
    
    import structlog
    from prometheus_client import CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
    ```
    **Category:** Anti-pattern
    **Severity:** major

16. **Unused CollectorRegistry imported from prometheus_client** (`PY-W2000`)
    **File:** `src/heretek_swarm/observability/__init__.py`
    **Line:** 33
    ```python
    import uuid
    
    import structlog
    from prometheus_client import CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
    
    from .prometheus_metrics import PrometheusMetrics
    from .tracing import initialize_tracing, get_tracer, span_context
    ```
    **Category:** Anti-pattern
    **Severity:** major

17. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/observability/__init__.py`
    **Line:** 388
    ```python
    """Get Prometheus metrics in text format."""
            return generate_latest(self.metrics.registry)
    
        def get_metrics_content_type(self) -> str:
            """Get Prometheus metrics content type."""
            return CONTENT_TYPE_LATEST
    ```
    **Category:** Performance
    **Severity:** major

18. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/observability/__init__.py`
    **Line:** 442
    ```python
    # Tracing
        # =========================================================================
    
        def trace_span(
            self,
            name: str,
            agent_id: Optional[str] = None,
    ```
    **Category:** Performance
    **Severity:** major

19. **Unused get_tracer imported from tracing** (`PY-W2000`)
    **File:** `src/heretek_swarm/observability/__init__.py`
    **Line:** 36
    ```python
    from prometheus_client import CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
    
    from .prometheus_metrics import PrometheusMetrics
    from .tracing import initialize_tracing, get_tracer, span_context
    
    # ============================================================================
    # Configuration
    ```
    **Category:** Anti-pattern
    **Severity:** major

20. **Unused field imported from dataclasses** (`PY-W2000`)
    **File:** `src/heretek_swarm/observability/__init__.py`
    **Line:** 25
    ```python
    import logging
    import os
    import time
    from dataclasses import asdict, dataclass, field
    from datetime import datetime, timezone
    from enum import Enum
    from pathlib import Path
    ```
    **Category:** Anti-pattern
    **Severity:** major

21. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/observability/__init__.py`
    **Line:** 544
    ```python
    # Structured Logging
        # =========================================================================
    
        def log(
            self,
            level: LogLevel,
            message: str,
    ```
    **Category:** Performance
    **Severity:** major

22. **Async context manager 'generator' doesn't implement __aenter__ and __aexit__.** (`PYL-E1701`)
    **File:** `src/heretek_swarm/observability/__init__.py`
    **Line:** 473
    ```python
    if task_id:
                span_attributes["task_id"] = task_id
    
            async with span_context(name, attributes=span_attributes):
                yield
    
        # =========================================================================
    ```
    **Category:** Bug risk
    **Severity:** critical

23. **Function is missing a return type annotation** (`TYP-051`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 440
    ```python
    import time
    
        class PrometheusMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next):
                # Skip metrics endpoint itself
                if request.url.path == "/metrics":
                    return await call_next(request)
    ```
    **Category:** Type check
    **Severity:** minor

24. **Function is missing a type annotation** (`TYP-051`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 193
    ```python
    output = metrics.export_prometheus()
        """
    
        def __init__(self, registry=None):
            """
            Initialize the Prometheus metrics collector.
    ```
    **Category:** Type check
    **Severity:** minor

25. **Function is missing a type annotation for one or more arguments** (`TYP-051`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 440
    ```python
    import time
    
        class PrometheusMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next):
                # Skip metrics endpoint itself
                if request.url.path == "/metrics":
                    return await call_next(request)
    ```
    **Category:** Type check
    **Severity:** minor

26. **Function is missing a type annotation for one or more arguments** (`TYP-051`)
    **File:** `src/heretek_swarm/observability/prometheus_metrics.py`
    **Line:** 417
    ```python
    # FastAPI Middleware Helper
    # ============================================================================
    
    def setup_metrics_middleware(app) -> None:
        """
        Setup Prometheus metrics middleware for FastAPI.
    ```
    **Category:** Type check
    **Severity:** minor

27. **Function is missing a type annotation** (`TYP-051`)
    **File:** `src/heretek_swarm/observability/tracing.py`
    **Line:** 162
    ```python
    raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                tracer = get_tracer()
                with tracer.start_as_current_span(
                    name,
    ```
    **Category:** Type check
    **Severity:** minor

28. **Function is missing a type annotation** (`TYP-051`)
    **File:** `src/heretek_swarm/observability/tracing.py`
    **Line:** 425
    ```python
    # Context Propagation Helpers
    # =============================================================================
    
    async def propagate_trace_context(coro):
        """
        Execute coroutine with trace context propagation.
    ```
    **Category:** Type check
    **Severity:** minor

29. **Function is missing a type annotation** (`TYP-051`)
    **File:** `src/heretek_swarm/observability/tracing.py`
    **Line:** 145
    ```python
    """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                tracer = get_tracer()
                with tracer.start_as_current_span(
                    name,
    ```
    **Category:** Type check
    **Severity:** minor

30. **Function is missing a return type annotation** (`TYP-051`)
    **File:** `src/heretek_swarm/observability/tracing.py`
    **Line:** 187
    ```python
    @contextmanager
    def span_context(
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        kind: trace.SpanKind = trace.SpanKind.INTERNAL,
    ```
    **Category:** Type check
    **Severity:** minor

31. **Function is missing a return type annotation** (`TYP-051`)
    **File:** `src/heretek_swarm/observability/tracing.py`
    **Line:** 446
    ```python
    # Shutdown
    # =============================================================================
    
    async def shutdown_tracing():
        """Shutdown tracing provider and flush spans."""
        provider = trace.get_tracer_provider()
        if hasattr(provider, 'shutdown'):
    ```
    **Category:** Type check
    **Severity:** minor

32. **Function is missing a type annotation** (`TYP-051`)
    **File:** `src/heretek_swarm/observability/tracing.py`
    **Line:** 405
    ```python
    raise
    
    
    def setup_telemetry_middleware(app):
        """
        Add telemetry middleware to FastAPI/Starlette application.
    ```
    **Category:** Type check
    **Severity:** minor

# DeepSource Code Review Report

**Repository:** Heretek-AI/heretek-swarm
**Branch:** `main`
**Commit:** 3338695...359f94e
**Run:** [https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/12a3534b-d7cb-4588-8000-57a884298f0a/](https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/12a3534b-d7cb-4588-8000-57a884298f0a/)

---

## Summary
- **Secrets:** No issues detected- **Shell:** No issues detected- **JavaScript:** No issues detected- **Docker:** No issues detected- **SQL:** No issues detected- **Python:** 143 issues

---

## Code Review Findings
### Secrets
**Status:** Success
**Findings:** No new issues detected
### Shell
**Status:** Success
**Findings:** No new issues detected
### JavaScript
**Status:** Success
**Findings:** No new issues detected
### Docker
**Status:** Success
**Findings:** No new issues detected
### SQL
**Status:** Success
**Findings:** No new issues detected
### Python
**Status:** Failure
**Findings:** 143 new issues

1. **Function is missing a return type annotation** (`TYP-051`)
   **File:** `src/heretek_swarm/collective/adaptive_learning.py`
   **Line:** 117
   ```python
   class EnvironmentProfile:
       """Profile of the current environment for adaptive learning."""
       
       def __init__(self):
           self.stability: float = 0.5
           self.complexity: float = 0.5
           self.demand_profile: Dict[str, float] = {}
   ```
   **Category:** Type check
   **Severity:** minor

2. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
   **File:** `src/heretek_swarm/collective/adaptive_learning.py`
   **Line:** 937
   ```python
   self.population = new_population
       
       def _mutate_config(self, config: LearningRateConfig) -> LearningRateConfig:
           return LearningRateConfig(
               initial_rate=config.initial_rate + random.uniform(-0.02, 0.02),
               min_rate=config.min_rate,
   ```
   **Category:** Performance
   **Severity:** major

3. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
   **File:** `src/heretek_swarm/collective/adaptive_learning.py`
   **Line:** 844
   ```python
   return True
       
       async def _validate_pattern_adoption(self, agent_id: str, pattern: ExtractedPattern) -> bool:
           if pattern.metadata.confidence < 0.3:
               return False
           if pattern.metadata.source == PatternSource.UNKNOWN:
   ```
   **Category:** Performance
   **Severity:** major

4. **Unused variable 'state'** (`PYL-W0612`)
   **File:** `src/heretek_swarm/collective/adaptive_learning.py`
   **Line:** 490
   ```python
   async def process_learning_signal(self, signal: LearningSignal) -> None:
           for target_agent in signal.target_agents:
               state = self.get_or_create_state(target_agent)
               
               if signal.signal_type == "reward":
                   adjustment = self.config.success_boost * signal.magnitude
   ```
   **Category:** Anti-pattern
   **Severity:** major

5. **Undefined variable 'PatternSource'** (`PYL-E0602`)
   **File:** `src/heretek_swarm/collective/adaptive_learning.py`
   **Line:** 847
   ```python
   async def _validate_pattern_adoption(self, agent_id: str, pattern: ExtractedPattern) -> bool:
           if pattern.metadata.confidence < 0.3:
               return False
           if pattern.metadata.source == PatternSource.UNKNOWN:
               return False
           return True
   ```
   **Category:** Bug risk
   **Severity:** critical

6. **Access to a protected member _emergent_patterns of a client class** (`PYL-W0212`)
   **File:** `src/heretek_swarm/collective/emergent_detection.py`
   **Line:** 1334
   ```python
   return contributors[:10]
       
       def analyze_pattern_correlations(self) -> Dict[str, Any]:
           patterns = self.detector._emergent_patterns
           
           if len(patterns) < 10:
               return {"correlations": "insufficient_data"}
   ```
   **Category:** Bug risk
   **Severity:** minor

7. **Access to a protected member _emergent_patterns of a client class** (`PYL-W0212`)
   **File:** `src/heretek_swarm/collective/emergent_detection.py`
   **Line:** 1322
   ```python
   def identify_key_contributors(self) -> List[Dict[str, Any]]:
           agent_contributions: Dict[str, int] = defaultdict(int)
           
           for pattern in self.detector._emergent_patterns:
               for agent_id in pattern.participating_agents:
                   agent_contributions[agent_id] += 1
   ```
   **Category:** Bug risk
   **Severity:** minor

8. **Access to a protected member _emergent_patterns of a client class** (`PYL-W0212`)
   **File:** `src/heretek_swarm/collective/emergent_detection.py`
   **Line:** 1357
   ```python
   def get_emergence_timeline(self) -> List[Dict[str, Any]]:
           timeline = []
           
           for pattern in sorted(self.detector._emergent_patterns, key=lambda p: p.timestamp):
               timeline.append({
                   "timestamp": pattern.timestamp,
                   "pattern_class": pattern.pattern_class.value,
   ```
   **Category:** Bug risk
   **Severity:** minor

9. **Access to a protected member _create_agent_snapshot of a client class** (`PYL-W0212`)
   **File:** `src/heretek_swarm/collective/emergent_detection.py`
   **Line:** 905
   ```python
   "fitness_score": snapshot.success_rate,
                   "behaviors": snapshot.active_strategies,
               }
               self._evolution_engine._create_agent_snapshot(agent_id, agent_state)
       
       def record_collective_behavior(self, behavior: CollectiveBehavior) -> None:
           self._collective_behaviors.append(behavior)
   ```
   **Category:** Bug risk
   **Severity:** minor

10. **Access to a protected member _emergent_patterns of a client class** (`PYL-W0212`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 1295
    ```python
    logger.info("emergence_analyzer_initialized")
        
        def analyze_emergence_trends(self) -> Dict[str, Any]:
            patterns = self.detector._emergent_patterns
            
            if len(patterns) < 5:
                return {"trend": "insufficient_data"}
    ```
    **Category:** Bug risk
    **Severity:** minor

11. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 340
    ```python
    return new_capabilities
        
        def assess_fitness(
            self,
            agent_id: str,
            performance_history: List[float],
    ```
    **Category:** Performance
    **Severity:** major

12. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 1056
    ```python
    def _get_active_agents(self, window: List[AgentBehaviorSnapshot]) -> List[str]:
            return list(set(s.agent_id for s in window))
        
        def _classify_emergence_level(self, score: float) -> EmergenceLevel:
            if score >= 0.8:
                return EmergenceLevel.CRITICAL
            elif score >= 0.6:
    ```
    **Category:** Performance
    **Severity:** major

13. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 1053
    ```python
    return sum(shifts) / len(shifts)
        
        def _get_active_agents(self, window: List[AgentBehaviorSnapshot]) -> List[str]:
            return list(set(s.agent_id for s in window))
        
        def _classify_emergence_level(self, score: float) -> EmergenceLevel:
    ```
    **Category:** Performance
    **Severity:** major

14. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 1027
    ```python
    return windows
        
        def _calculate_window_metrics(self, window: List[AgentBehaviorSnapshot]) -> Dict[str, float]:
            if not window:
                return {}
    ```
    **Category:** Performance
    **Severity:** major

15. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 1205
    ```python
    return sum(factors) / len(factors)
        
        def _calculate_impact_score(self, pattern: EmergentPattern) -> float:
            level_impact = {
                EmergenceLevel.WEAK: 0.2,
                EmergenceLevel.MODERATE: 0.4,
    ```
    **Category:** Performance
    **Severity:** major

16. **Unnecessary generator - rewrite as a set comprehension** (`PTC-W0015`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 486
    ```python
    metrics.evolution_rate = metrics.total_capabilities / hours_elapsed
            
            if self._capability_records:
                types = set(r.capability_type for r in self._capability_records.values())
                metrics.capability_diversity = len(types) / max(metrics.total_capabilities, 1)
            else:
                metrics.capability_diversity = 0.0
    ```
    **Category:** Anti-pattern
    **Severity:** major

17. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 523
    ```python
    metrics.generations = self._generation_counter
            metrics.selection_fidelity = self._calculate_selection_fidelity()
        
        def _calculate_variance(self, values: List[float]) -> float:
            if len(values) < 2:
                return 0.0
            mean = sum(values) / len(values)
    ```
    **Category:** Performance
    **Severity:** major

18. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 986
    ```python
    return self._evolution_engine.get_evolution_metrics().to_dict()
            return {}
        
        async def _detect_coordination_patterns(self) -> List[EmergentPattern]:
            return []
        
        async def _detect_optimization_patterns(self) -> List[EmergentPattern]:
    ```
    **Category:** Performance
    **Severity:** major

19. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 1187
    ```python
    return existing
            return None
        
        def _calculate_statistical_significance(self, pattern: EmergentPattern) -> float:
            n_agents = len(pattern.participating_agents)
            emergence_score = pattern.emergence_score
    ```
    **Category:** Performance
    **Severity:** major

20. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 1096
    ```python
    weighted_sum = sum(b.coherence * b.intensity for b in behaviors)
            return weighted_sum / len(behaviors)
        
        def _calculate_temporal_span(self, behaviors: List[CollectiveBehavior]) -> float:
            if not behaviors:
                return 0.0
    ```
    **Category:** Performance
    **Severity:** major

21. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 1194
    ```python
    significance = 1.0 / (n_agents * (1.0 - emergence_score + 0.01))
            return min(significance, 1.0)
        
        def _calculate_confidence(self, pattern: EmergentPattern) -> float:
            factors = []
            factors.append(pattern.emergence_score)
            agent_factor = min(len(pattern.participating_agents) / 10.0, 1.0)
    ```
    **Category:** Performance
    **Severity:** major

22. **Unused variable 'current_behaviors'** (`PYL-W0612`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 318
    ```python
    current_caps = state.get("capability_levels", {})
                current_fitness = state.get("fitness_score", 0.0)
                current_behaviors = state.get("behaviors", [])
                
                if prev_snapshot:
                    for cap_type, level in current_caps.items():
    ```
    **Category:** Anti-pattern
    **Severity:** major

23. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 989
    ```python
    async def _detect_coordination_patterns(self) -> List[EmergentPattern]:
            return []
        
        async def _detect_optimization_patterns(self) -> List[EmergentPattern]:
            return []
        
        async def _detect_innovation_patterns(self) -> List[EmergentPattern]:
    ```
    **Category:** Performance
    **Severity:** major

24. **Unnecessary generator - rewrite as a set comprehension** (`PTC-W0015`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 1034
    ```python
    return {
                "avg_success_rate": sum(s.success_rate for s in window) / len(window),
                "avg_interaction_count": sum(s.interaction_count for s in window) / len(window),
                "unique_agents": len(set(s.agent_id for s in window)),
                "total_interactions": sum(s.interaction_count for s in window),
            }
    ```
    **Category:** Anti-pattern
    **Severity:** major

25. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 1089
    ```python
    return sum(baselines) / len(baselines) if baselines else 0.5
        
        def _measure_collective_capability(self, behaviors: List[CollectiveBehavior]) -> float:
            if not behaviors:
                return 0.0
    ```
    **Category:** Performance
    **Severity:** major

26. **Unnecessary generator - rewrite as a set comprehension** (`PTC-W0015`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 1054
    ```python
    return sum(shifts) / len(shifts)
        
        def _get_active_agents(self, window: List[AgentBehaviorSnapshot]) -> List[str]:
            return list(set(s.agent_id for s in window))
        
        def _classify_emergence_level(self, score: float) -> EmergenceLevel:
            if score >= 0.8:
    ```
    **Category:** Anti-pattern
    **Severity:** major

27. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 1038
    ```python
    "total_interactions": sum(s.interaction_count for s in window),
            }
        
        def _calculate_shift_score(self, prev_metrics: Dict[str, float], curr_metrics: Dict[str, float]) -> float:
            if not prev_metrics or not curr_metrics:
                return 0.0
    ```
    **Category:** Performance
    **Severity:** major

28. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 992
    ```python
    async def _detect_optimization_patterns(self) -> List[EmergentPattern]:
            return []
        
        async def _detect_innovation_patterns(self) -> List[EmergentPattern]:
            return []
        
        async def _detect_phase_transitions(self) -> List[EmergentPattern]:
    ```
    **Category:** Performance
    **Severity:** major

29. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 995
    ```python
    async def _detect_innovation_patterns(self) -> List[EmergentPattern]:
            return []
        
        async def _detect_phase_transitions(self) -> List[EmergentPattern]:
            return []
        
        def _analyze_temporal_windows(self, window_size_seconds: float) -> List[List[AgentBehaviorSnapshot]]:
    ```
    **Category:** Performance
    **Severity:** major

30. **Unused variable 'current_fitness'** (`PYL-W0612`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 317
    ```python
    prev_snapshot = self._get_latest_snapshot(agent_id)
                
                current_caps = state.get("capability_levels", {})
                current_fitness = state.get("fitness_score", 0.0)
                current_behaviors = state.get("behaviors", [])
                
                if prev_snapshot:
    ```
    **Category:** Anti-pattern
    **Severity:** major

31. **Appending to list immediately following its definition** (`PY-W0070`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 1195
    ```python
    return min(significance, 1.0)
        
        def _calculate_confidence(self, pattern: EmergentPattern) -> float:
            factors = []
            factors.append(pattern.emergence_score)
            agent_factor = min(len(pattern.participating_agents) / 10.0, 1.0)
            factors.append(agent_factor)
    ```
    **Category:** Anti-pattern
    **Severity:** major

32. **Unused variable 'level'** (`PYL-W0612`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 435
    ```python
    current_caps = state.get("capability_levels", {})
            
            if prev_snapshot:
                for cap_type, level in current_caps.items():
                    if cap_type not in prev_snapshot.capability_levels:
                        newly_acquired.append(cap_type)
    ```
    **Category:** Anti-pattern
    **Severity:** major

33. **Undefined variable 'capability_type'** (`PYL-E0602`)
    **File:** `src/heretek_swarm/collective/emergent_detection.py`
    **Line:** 327
    ```python
    if level > prev_level + 0.2 and level > 0.5:
                            record = self.record_capability_gain(
                                agent_id=agent_id,
                                capability_type=capability_type,
                                capability_name=f"{cap_type}_level_{int(level * 100)}",
                                fitness_contribution=level - prev_level,
                                description=f"Advanced {cap_type} capability",
    ```
    **Category:** Bug risk
    **Severity:** critical

34. **Function is missing a return type annotation** (`TYP-051`)
    **File:** `src/heretek_swarm/collective/knowledge_transform.py`
    **Line:** 133
    ```python
    validation_rules: Validation rules for transformed knowledge
        """
        
        def __init__(self):
            """Initialize knowledge transformer."""
            self._agent_profiles: Dict[str, AgentCapabilityProfile] = {}
            self._transformation_rules: Dict[TransformationType, Callable] = {}
    ```
    **Category:** Type check
    **Severity:** minor

35. **Function is missing a return type annotation** (`TYP-051`)
    **File:** `src/heretek_swarm/collective/knowledge_transform.py`
    **Line:** 958
    ```python
    patterns and distributing knowledge across the swarm.
        """
        
        def __init__(self):
            """Initialize knowledge transformation service."""
            self.transformer = KnowledgeTransformer()
            self._transformation_history: List[TransformationResult] = []
    ```
    **Category:** Type check
    **Severity:** minor

36. **Function is missing a type annotation for one or more arguments** (`TYP-051`)
    **File:** `src/heretek_swarm/collective/pattern_library.py`
    **Line:** 752
    ```python
    error=str(e),
                    )
        
        async def _call_callbacks(self, event: str, *args) -> None:
            """Call registered callbacks for an event."""
            for callback in self._callbacks.get(event, []):
                try:
    ```
    **Category:** Type check
    **Severity:** minor

37. **Function is missing a type annotation for one or more arguments** (`TYP-051`)
    **File:** `src/heretek_swarm/collective/society.py`
    **Line:** 586
    ```python
    return result
        
        async def _get_agent_contribution(
            self,
            actor,
            task: CollectiveTask,
    ```
    **Category:** Type check
    **Severity:** minor

38. **Function is missing a return type annotation** (`TYP-051`)
    **File:** `src/heretek_swarm/collective/society.py`
    **Line:** 201
    ```python
    Stores collective knowledge, patterns, and learnings.
        """
        
        def __init__(self):
            self._memory: Dict[str, Any] = {}
            self._patterns: List[Dict[str, Any]] = []
            self._learnings: List[Dict[str, Any]] = []
    ```
    **Category:** Type check
    **Severity:** minor

39. **Function is missing a type annotation for one or more arguments** (`TYP-051`)
    **File:** `src/heretek_swarm/collective/society.py`
    **Line:** 297
    ```python
    and emergent behavior detection.
        """
        
        def __init__(
            self,
            supervisor=None,
            contribution_cache_ttl: int = 300,
    ```
    **Category:** Type check
    **Severity:** minor

40. **Function is missing a type annotation for one or more arguments** (`TYP-051`)
    **File:** `src/heretek_swarm/collective/society.py`
    **Line:** 678
    ```python
    confidence=0.1  # Low confidence for error fallback
                )
        
        async def _request_contribution_from_actor(
            self,
            actor,
            task: CollectiveTask,
    ```
    **Category:** Type check
    **Severity:** minor

41. **Incompatible return value type (got "List[float]", expected "Tuple[float, float, float]")** (`TYP-005`)
    **File:** `src/heretek_swarm/collective/swarm_intelligence.py`
    **Line:** 1119
    ```python
    if count > 0:
                separation = tuple(s / count for s in separation)
    
            return separation
    
        def _calculate_alignment(self, agent: FlockingAgent) -> Tuple[float, float, float]:
            """Calculate alignment steering force."""
    ```
    **Category:** Type check
    **Severity:** major

42. **Incompatible return value type (got "Tuple[float, ...]", expected "Tuple[float, float, float]")** (`TYP-005`)
    **File:** `src/heretek_swarm/collective/swarm_intelligence.py`
    **Line:** 1149
    ```python
    center = tuple(c / len(agent.neighbors) for c in center)
    
            # Steering force toward center
            return tuple(c - p for c, p in zip(center, agent.position))
    
        def _update_flocking_position(self, agent: FlockingAgent) -> None:
            """Update agent position based on velocity."""
    ```
    **Category:** Type check
    **Severity:** major

43. **Incompatible return value type (got "Tuple[float, ...]", expected "Tuple[float, float, float]")** (`TYP-005`)
    **File:** `src/heretek_swarm/collective/swarm_intelligence.py`
    **Line:** 1190
    ```python
    if magnitude > 0:
                result = tuple(v / magnitude for v in result)
    
            return result
    
        def _calculate_flocking_cohesion(self) -> float:
            """Calculate overall flock cohesion."""
    ```
    **Category:** Type check
    **Severity:** major

44. **Incompatible return value type (got "Tuple[float, ...]", expected "Tuple[float, float, float]")** (`TYP-005`)
    **File:** `src/heretek_swarm/collective/swarm_intelligence.py`
    **Line:** 1172
    ```python
    for agent in self.flocking_agents.values():
                center = tuple(c + a for c, a in zip(center, agent.position))
    
            return tuple(c / len(self.flocking_agents) for c in center)
    
        def _calculate_average_heading(self) -> Tuple[float, float, float]:
            """Calculate average heading of the flock."""
    ```
    **Category:** Type check
    **Severity:** major

45. **Incompatible return value type (got "Tuple[float, ...]", expected "Tuple[float, float, float]")** (`TYP-005`)
    **File:** `src/heretek_swarm/collective/swarm_intelligence.py`
    **Line:** 1134
    ```python
    avg_velocity = tuple(v / len(agent.neighbors) for v in avg_velocity)
    
            # Steering force is difference from current velocity
            return tuple(a - c for a, c in zip(avg_velocity, agent.velocity))
    
        def _calculate_cohesion(self, agent: FlockingAgent) -> Tuple[float, float, float]:
            """Calculate cohesion steering force."""
    ```
    **Category:** Type check
    **Severity:** major

46. **Simplify chained comparison between the operands** (`PYL-R1716`)
    **File:** `src/heretek_swarm/consciousness/introspection.py`
    **Line:** 484
    ```python
    resource_availability = sum(1 for v in resources.values() if v > 0.5) / max(1, len(resources))
                    if resource_availability > 0.8 and goal.priority < 0.7:
                        goal.priority = min(1.0, goal.priority + 0.1)
                    elif resource_availability < 0.3 and goal.priority > 0.3:
                        goal.priority = max(0.0, goal.priority - 0.1)
                
                # Record evolution if changes occurred
    ```
    **Category:** Anti-pattern
    **Severity:** minor

47. **`IntrospectionModule.reflect_on_beliefs` has a cyclomatic complexity of 16 with "high" risk** (`PY-R1000`)
    **File:** `src/heretek_swarm/consciousness/introspection.py`
    **Line:** 217
    ```python
    }
            )
        
        def reflect_on_beliefs(self) -> Dict[str, Any]:
            """Analyze current belief state and return insights.
            
            Returns:
    ```
    **Category:** Anti-pattern
    **Severity:** minor

48. **Access to a protected member _maybe_take_snapshot of a client class** (`PYL-W0212`)
    **File:** `src/heretek_swarm/consciousness/introspection.py`
    **Line:** 784
    ```python
    if changes:
                self.self_model._update_count += 1
                self.self_model._maybe_take_snapshot()
            
            logger.debug(
                "Confidence decay applied",
    ```
    **Category:** Bug risk
    **Severity:** minor

49. **Access to a protected member _unblock_dependent_goals of a client class** (`PYL-W0212`)
    **File:** `src/heretek_swarm/consciousness/introspection.py`
    **Line:** 615
    ```python
    self.self_model._update_parent_progress(goal.parent_goal_id)
                
                # Unblock dependent goals
                self.self_model._unblock_dependent_goals(goal_id)
            
            # Handle success/failure
            success = outcome.get("success")
    ```
    **Category:** Bug risk
    **Severity:** minor

50. **Access to a protected member _maybe_take_snapshot of a client class** (`PYL-W0212`)
    **File:** `src/heretek_swarm/consciousness/introspection.py`
    **Line:** 391
    ```python
    self.self_model._detect_belief_conflict(belief, old_confidence)
            
            self.self_model._update_count += 1
            self.self_model._maybe_take_snapshot()
            
            logger.info(
                "Belief updated from outcome",
    ```
    **Category:** Bug risk
    **Severity:** minor

51. **Access to a protected member _detect_belief_conflict of a client class** (`PYL-W0212`)
    **File:** `src/heretek_swarm/consciousness/introspection.py`
    **Line:** 388
    ```python
    # Check for conflicts if confidence changed significantly
            if abs(new_confidence - old_confidence) > 0.2:
                self.self_model._detect_belief_conflict(belief, old_confidence)
            
            self.self_model._update_count += 1
            self.self_model._maybe_take_snapshot()
    ```
    **Category:** Bug risk
    **Severity:** minor

52. **Access to a protected member _maybe_take_snapshot of a client class** (`PYL-W0212`)
    **File:** `src/heretek_swarm/consciousness/introspection.py`
    **Line:** 651
    ```python
    self._trim_evolution_history()
            
            self.self_model._update_count += 1
            self.self_model._maybe_take_snapshot()
            
            logger.info(
                "Goal progress tracked",
    ```
    **Category:** Bug risk
    **Severity:** minor

53. **Access to a protected member _update_parent_progress of a client class** (`PYL-W0212`)
    **File:** `src/heretek_swarm/consciousness/introspection.py`
    **Line:** 612
    ```python
    # Update parent goal progress if applicable
                if goal.parent_goal_id and goal.parent_goal_id in self.self_model.goals:
                    self.self_model._update_parent_progress(goal.parent_goal_id)
                
                # Unblock dependent goals
                self.self_model._unblock_dependent_goals(goal_id)
    ```
    **Category:** Bug risk
    **Severity:** minor

54. **Access to a protected member _are_beliefs_conflicting of a client class** (`PYL-W0212`)
    **File:** `src/heretek_swarm/consciousness/introspection.py`
    **Line:** 881
    ```python
    True if beliefs are in conflict.
            """
            # Use existing method from SelfModel
            return self.self_model._are_beliefs_conflicting(b1, b2)
        
        def _suggest_resolution(
            self,
    ```
    **Category:** Bug risk
    **Severity:** minor

55. **`IntrospectionModule.evolve_goals` has a cyclomatic complexity of 30 with "very-high" risk** (`PY-R1000`)
    **File:** `src/heretek_swarm/consciousness/introspection.py`
    **Line:** 405
    ```python
    return belief
        
        def evolve_goals(self, current_state: Dict[str, Any]) -> Dict[str, Any]:
            """Update goal priorities and progress based on current system state.
            
            Args:
    ```
    **Category:** Anti-pattern
    **Severity:** minor

56. **Unused Goal imported from self_model** (`PY-W2000`)
    **File:** `src/heretek_swarm/consciousness/introspection.py`
    **Line:** 24
    ```python
    import structlog
    
    from .self_model import Belief, Goal, BeliefType, GoalStatus, SelfModel
    
    logger = structlog.get_logger("IntrospectionModule")
    ```
    **Category:** Anti-pattern
    **Severity:** major

57. **Unused timedelta imported from datetime** (`PY-W2000`)
    **File:** `src/heretek_swarm/consciousness/introspection.py`
    **Line:** 18
    ```python
    import math
    import uuid
    from dataclasses import dataclass, field
    from datetime import datetime, timezone, timedelta
    from enum import Enum
    from typing import Any, Dict, List, Optional, Tuple
    ```
    **Category:** Anti-pattern
    **Severity:** major

58. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/consciousness/introspection.py`
    **Line:** 849
    ```python
    return "decreasing"
            return "stable"
        
        def _assess_evidence_quality(self, belief: Belief) -> str:
            """Assess the quality of evidence for a belief.
            
            Args:
    ```
    **Category:** Performance
    **Severity:** major

59. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/consciousness/introspection.py`
    **Line:** 883
    ```python
    # Use existing method from SelfModel
            return self.self_model._are_beliefs_conflicting(b1, b2)
        
        def _suggest_resolution(
            self,
            b1: Belief,
            b2: Belief,
    ```
    **Category:** Performance
    **Severity:** major

60. **Unused BeliefType imported from self_model** (`PY-W2000`)
    **File:** `src/heretek_swarm/consciousness/introspection.py`
    **Line:** 24
    ```python
    import structlog
    
    from .self_model import Belief, Goal, BeliefType, GoalStatus, SelfModel
    
    logger = structlog.get_logger("IntrospectionModule")
    ```
    **Category:** Anti-pattern
    **Severity:** major

61. **Unused import uuid** (`PY-W2000`)
    **File:** `src/heretek_swarm/consciousness/introspection.py`
    **Line:** 16
    ```python
    """
    
    import math
    import uuid
    from dataclasses import dataclass, field
    from datetime import datetime, timezone, timedelta
    from enum import Enum
    ```
    **Category:** Anti-pattern
    **Severity:** major

62. **`SelfModel.__init__` has a cyclomatic complexity of 16 with "high" risk** (`PY-R1000`)
    **File:** `src/heretek_swarm/consciousness/self_model.py`
    **Line:** 306
    ```python
    COHERENCE_THRESHOLD = 0.7
        CLARITY_THRESHOLD = 0.5
        
        def __init__(
            self,
            agent_id: str,
            initial_beliefs: Optional[List[Dict[str, Any]]] = None,
    ```
    **Category:** Anti-pattern
    **Severity:** minor

63. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/consciousness/self_model.py`
    **Line:** 764
    ```python
    def get_active_goals(self) -> List[Dict[str, Any]]:
            return [goal.to_dict() for goal in self.goals.values() if goal.status == GoalStatus.ACTIVE]
        
        def _detect_belief_conflict(self, belief: Belief, old_confidence: float) -> None:
            logger.debug(
                "Significant belief change detected",
                extra={
    ```
    **Category:** Performance
    **Severity:** major

64. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `src/heretek_swarm/consciousness/self_model.py`
    **Line:** 774
    ```python
    }
            )
        
        def _are_beliefs_conflicting(self, b1: Belief, b2: Belief) -> bool:
            if b1.belief_type != b2.belief_type:
                return False
            state1_lower = b1.state.lower()
    ```
    **Category:** Performance
    **Severity:** major

65. **Unused variable 'old_state'** (`PYL-W0612`)
    **File:** `src/heretek_swarm/consciousness/self_model.py`
    **Line:** 374
    ```python
    if belief_id and belief_id in self.beliefs:
                belief = self.beliefs[belief_id]
                old_state = belief.state
                old_confidence = belief.confidence
                belief.state = state
                belief.confidence = confidence
    ```
    **Category:** Anti-pattern
    **Severity:** major

66. **Function is missing a return type annotation** (`TYP-051`)
    **File:** `src/heretek_swarm/llm/model_garage.py`
    **Line:** 883
    ```python
    # Example Usage
    # ============================================================================
    
    async def main():
        """Example usage of ModelGarage."""
        garage = await initialize_model_garage()
    ```
    **Category:** Type check
    **Severity:** minor

67. **`ModelGarage.complete` has a cyclomatic complexity of 20 with "high" risk** (`PY-R1000`)
    **File:** `src/heretek_swarm/llm/model_garage.py`
    **Line:** 763
    ```python
    return results
    
        async def complete(
            self,
            messages: List[ChatMessage],
            model: Optional[str] = None,
    ```
    **Category:** Anti-pattern
    **Severity:** minor

68. **Using the global statement** (`PYL-W0603`)
    **File:** `src/heretek_swarm/llm/model_garage.py`
    **Line:** 865
    ```python
    def get_model_garage() -> ModelGarage:
        """Get the global ModelGarage instance."""
        global _model_garage
        if _model_garage is None:
            _model_garage = ModelGarage()
        return _model_garage
    ```
    **Category:** Anti-pattern
    **Severity:** minor

69. **Function is missing a type annotation for one or more arguments** (`TYP-051`)
    **File:** `src/heretek_swarm/llm/model_garage.py`
    **Line:** 818
    ```python
    raise last_error or RuntimeError("All providers failed")
    
        async def stream(
            self,
            messages: List[ChatMessage],
            model: Optional[str] = None,
    ```
    **Category:** Type check
    **Severity:** minor

70. **Function is missing a type annotation for one or more arguments** (`TYP-051`)
    **File:** `src/heretek_swarm/llm/model_garage.py`
    **Line:** 763
    ```python
    return results
    
        async def complete(
            self,
            messages: List[ChatMessage],
            model: Optional[str] = None,
    ```
    **Category:** Type check
    **Severity:** minor

71. **Using the global statement** (`PYL-W0603`)
    **File:** `src/heretek_swarm/llm/model_garage.py`
    **Line:** 873
    ```python
    async def initialize_model_garage() -> ModelGarage:
        """Initialize and return the global ModelGarage instance."""
        global _model_garage
        _model_garage = ModelGarage()
        await _model_garage.initialize()
        return _model_garage
    ```
    **Category:** Anti-pattern
    **Severity:** minor

72. **Unused import logging** (`PY-W2000`)
    **File:** `src/heretek_swarm/llm/model_garage.py`
    **Line:** 25
    ```python
    import asyncio
    import json
    import logging
    import os
    import time
    from abc import ABC, abstractmethod
    ```
    **Category:** Anti-pattern
    **Severity:** major

73. **Unused import os** (`PY-W2000`)
    **File:** `src/heretek_swarm/llm/model_garage.py`
    **Line:** 26
    ```python
    import asyncio
    import json
    import logging
    import os
    import time
    from abc import ABC, abstractmethod
    from dataclasses import dataclass, field
    ```
    **Category:** Anti-pattern
    **Severity:** major

74. **Unused import time** (`PY-W2000`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 22
    ```python
    from datetime import datetime, timezone, timedelta
    from typing import Dict, Any
    import uuid
    import time
    
    from src.heretek_swarm.consciousness.self_model import (
        SelfModel,
    ```
    **Category:** Anti-pattern
    **Severity:** major

75. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 131
    ```python
    expected_avg = (0.9 + 0.5 + 0.2) / 3
            assert abs(result["average_confidence"] - expected_avg) < 0.01
        
        def test_insights_generated(self, introspection_with_beliefs):
            """Test that insights are generated for each belief."""
            result = introspection_with_beliefs.reflect_on_beliefs()
    ```
    **Category:** Performance
    **Severity:** major

76. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 124
    ```python
    assert dist["moderate"] == 1  # 0.5
            assert dist["low"] == 1  # 0.2
        
        def test_average_confidence_calculation(self, introspection_with_beliefs):
            """Test average confidence calculation."""
            result = introspection_with_beliefs.reflect_on_beliefs()
    ```
    **Category:** Performance
    **Severity:** major

77. **Unused Belief imported from src.heretek_swarm.consciousness.self_model** (`PY-W2000`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 24
    ```python
    import uuid
    import time
    
    from src.heretek_swarm.consciousness.self_model import (
        SelfModel,
        Belief,
        Goal,
    ```
    **Category:** Anti-pattern
    **Severity:** major

78. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 321
    ```python
    assert "constraint" in goal.blocked_by
            assert goal_id in result["new_blocked_goals"]
        
        def test_evolve_with_high_resources(self, introspection_with_goals):
            """Test goal evolution with high resource availability."""
            goal_id = list(introspection_with_goals.self_model.goals.keys())[0]
            goal = introspection_with_goals.self_model.goals[goal_id]
    ```
    **Category:** Performance
    **Severity:** major

79. **Unused variable 'result'** (`PYL-W0612`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 277
    ```python
    "constraints": [],
            }
            
            result = introspection_with_goals.evolve_goals(current_state)
            
            # Goal progress should increase when in completed_tasks
            goal = introspection_with_goals.self_model.goals[goal_id]
    ```
    **Category:** Anti-pattern
    **Severity:** major

80. **Unused variable 'result'** (`PYL-W0612`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 470
    ```python
    outcome = {"completion": True}
            
            result = introspection_with_goal.track_goal_progress(goal_id, outcome)
            
            goal = introspection_with_goal.self_model.goals[goal_id]
            assert goal.status == GoalStatus.COMPLETED
    ```
    **Category:** Anti-pattern
    **Severity:** major

81. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 338
    ```python
    assert goal.priority > 0.5
        
        def test_evolve_empty_state(self, introspection_with_goals):
            """Test goal evolution with empty state."""
            current_state = {
                "completed_tasks": [],
    ```
    **Category:** Performance
    **Severity:** major

82. **Unused variable 'old_confidence'** (`PYL-W0612`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 599
    ```python
    def test_decay_applied(self, introspection_with_beliefs):
            """Test that decay is applied to beliefs."""
            belief_id = list(introspection_with_beliefs.self_model.beliefs.keys())[0]
            old_confidence = introspection_with_beliefs.self_model.beliefs[belief_id].confidence
            
            changes = introspection_with_beliefs.apply_confidence_decay(days_elapsed=10)
    ```
    **Category:** Anti-pattern
    **Severity:** major

83. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 942
    ```python
    assert data["new_confidence"] == 0.7
            assert "timestamp" in data
        
        def test_goal_evolution_record_to_dict(self):
            """Test GoalEvolutionRecord serialization."""
            record = GoalEvolutionRecord(
                goal_id="test-id",
    ```
    **Category:** Performance
    **Severity:** major

84. **Unused variable 'result'** (`PYL-W0612`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 334
    ```python
    "constraints": [],
            }
            
            result = introspection_with_goals.evolve_goals(current_state)
            
            assert goal.priority > 0.5
    ```
    **Category:** Anti-pattern
    **Severity:** major

85. **Unused timedelta imported from datetime** (`PY-W2000`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 19
    ```python
    """
    
    import pytest
    from datetime import datetime, timezone, timedelta
    from typing import Dict, Any
    import uuid
    import time
    ```
    **Category:** Anti-pattern
    **Severity:** major

86. **Unused variable 'conflicts'** (`PYL-W0612`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 874
    ```python
    })
            
            # Detect conflicts
            conflicts = introspection.detect_conflicting_beliefs()
            
            # Get introspection report
            report = introspection.get_introspection_report()
    ```
    **Category:** Anti-pattern
    **Severity:** major

87. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 393
    ```python
    assert conflict.resolution_suggestion is not None
            assert len(conflict.resolution_suggestion) > 0
        
        def test_no_conflicts_detected(self):
            """Test with non-conflicting beliefs."""
            self_model = SelfModel(
                agent_id="test-agent",
    ```
    **Category:** Performance
    **Severity:** major

88. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 828
    ```python
    class TestIntegration:
        """Integration tests for IntrospectionModule with SelfModel."""
        
        def test_full_workflow(self):
            """Test complete introspection workflow."""
            # Create SelfModel with initial state
            self_model = SelfModel(
    ```
    **Category:** Performance
    **Severity:** major

89. **Unused datetime imported from datetime** (`PY-W2000`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 19
    ```python
    """
    
    import pytest
    from datetime import datetime, timezone, timedelta
    from typing import Dict, Any
    import uuid
    import time
    ```
    **Category:** Anti-pattern
    **Severity:** major

90. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 981
    ```python
    assert data["belief_2_id"] == "b2"
            assert data["resolution_strategy"] == "confidence_based"
        
        def test_introspection_report_to_dict(self):
            """Test IntrospectionReport serialization."""
            report = IntrospectionReport(
                agent_id="test-agent",
    ```
    **Category:** Performance
    **Severity:** major

91. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 527
    ```python
    return introspection
        
        def test_report_structure(self, introspection_with_data):
            """Test introspection report structure."""
            report = introspection_with_data.get_introspection_report()
    ```
    **Category:** Performance
    **Severity:** major

92. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 596
    ```python
    )
            return IntrospectionModule(self_model)
        
        def test_decay_applied(self, introspection_with_beliefs):
            """Test that decay is applied to beliefs."""
            belief_id = list(introspection_with_beliefs.self_model.beliefs.keys())[0]
            old_confidence = introspection_with_beliefs.self_model.beliefs[belief_id].confidence
    ```
    **Category:** Performance
    **Severity:** major

93. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 962
    ```python
    assert data["new_priority"] == 0.7
            assert "timestamp" in data
        
        def test_conflict_pair_to_dict(self):
            """Test ConflictPair serialization."""
            pair = ConflictPair(
                belief_1_id="b1",
    ```
    **Category:** Performance
    **Severity:** major

94. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 885
    ```python
    assert report.goal_count == 2
            assert len(report.evolution_history) >= 2  # At least belief update and goal tracking
        
        def test_conflict_detection_and_resolution(self):
            """Test conflict detection and resolution workflow."""
            self_model = SelfModel(
                agent_id="conflict-test-agent",
    ```
    **Category:** Performance
    **Severity:** major

95. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 67
    ```python
    assert len(introspection._belief_evolution_history) == 0
            assert len(introspection._goal_evolution_history) == 0
        
        def test_init_with_populated_self_model(self):
            """Test initialization with populated SelfModel."""
            self_model = SelfModel(
                agent_id="test-agent-2",
    ```
    **Category:** Performance
    **Severity:** major

96. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 283
    ```python
    goal = introspection_with_goals.self_model.goals[goal_id]
            assert goal.progress > 0.3
        
        def test_evolve_goal_completion(self, introspection_with_goals):
            """Test goal completion when progress reaches 1.0."""
            goal_id = list(introspection_with_goals.self_model.goals.keys())[0]
            introspection_with_goals.self_model.goals[goal_id].progress = 0.95
    ```
    **Category:** Performance
    **Severity:** major

97. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 103
    ```python
    )
            return IntrospectionModule(self_model)
        
        def test_reflect_returns_correct_structure(self, introspection_with_beliefs):
            """Test that reflect_on_beliefs returns correct structure."""
            result = introspection_with_beliefs.reflect_on_beliefs()
    ```
    **Category:** Performance
    **Severity:** major

98. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 621
    ```python
    if self_model.beliefs[belief_id].confidence > 0.5:
                    assert change < 0
        
        def test_decay_records_evolution(self, introspection_with_beliefs):
            """Test that decay creates evolution records."""
            initial_history_count = len(introspection_with_beliefs._belief_evolution_history)
    ```
    **Category:** Performance
    **Severity:** major

99. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
    **File:** `tests/consciousness/test_introspection.py`
    **Line:** 450
    ```python
    goal = introspection_with_goal.self_model.goals[goal_id]
            assert goal.progress == 0.5
        
        def test_track_negative_progress(self, introspection_with_goal):
            """Test tracking negative progress."""
            goal_id = list(introspection_with_goal.self_model.goals.keys())[0]
    ```
    **Category:** Performance
    **Severity:** major

100. **Method doesn't use the class instance and could be converted into a static method** (`PYL-R0201`)
     **File:** `tests/consciousness/test_introspection.py`
     **Line:** 730
     ```python
     return introspection
         
         def test_confidence_based_strategy(self, introspection_with_conflicts):
             """Test confidence-based resolution."""
             conflicts = introspection_with_conflicts.detect_conflicting_beliefs(
                 ConflictResolutionStrategy.CONFIDENCE_BASED
     ```
     **Category:** Performance
     **Severity:** major

*...and 43 more occurrences. [See full list on DeepSource](https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/12a3534b-d7cb-4588-8000-57a884298f0a/).*
# DeepSource Code Review Report

**Repository:** Heretek-AI/heretek-swarm
**Branch:** `main`
**Commit:** 4b14973...0cb3ece
**Run:** [https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/de3c9761-2be1-4db4-8e0b-5393ba53c9a5/](https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/de3c9761-2be1-4db4-8e0b-5393ba53c9a5/)

---

## Summary
- **Secrets:** No issues detected- **JavaScript:** No issues detected- **SQL:** No issues detected- **Shell:** No issues detected- **Docker:** No issues detected- **Python:** 12 issues

---

## Code Review Findings
### Secrets
**Status:** Success
**Findings:** No new issues detected
### JavaScript
**Status:** Success
**Findings:** No new issues detected
### SQL
**Status:** Success
**Findings:** No new issues detected
### Shell
**Status:** Success
**Findings:** No new issues detected
### Docker
**Status:** Success
**Findings:** No new issues detected
### Python
**Status:** Failure
**Findings:** 12 new issues

1. **Function is missing a type annotation for one or more arguments** (`TYP-051`)
   **File:** `src/heretek_swarm/actors/perceiver_plus.py`
   **Line:** 200
   ```python
   6. Provide actionable recommendations
       """
       
       def __init__(
           self,
           agent_id: str = "perceiver-plus",
           name: str = "Perceiver+",
   ```
   **Category:** Type check
   **Severity:** minor

2. **Simplify chained comparison between the operands** (`PYL-R1716`)
   **File:** `src/heretek_swarm/actors/perceiver_plus.py`
   **Line:** 556
   ```python
   import json
                   start_idx = result.find("{")
                   end_idx = result.rfind("}") + 1
                   if start_idx >= 0 and end_idx > start_idx:
                       parsed = json.loads(result[start_idx:end_idx])
                       findings = parsed.get("findings", [])
                       metrics = {
   ```
   **Category:** Anti-pattern
   **Severity:** minor

3. **Simplify chained comparison between the operands** (`PYL-R1716`)
   **File:** `src/heretek_swarm/actors/perceiver_plus.py`
   **Line:** 615
   ```python
   import json
                   start_idx = result.find("{")
                   end_idx = result.rfind("}") + 1
                   if start_idx >= 0 and end_idx > start_idx:
                       parsed = json.loads(result[start_idx:end_idx])
                       findings = parsed.get("predictions", [])
                       metrics = {
   ```
   **Category:** Anti-pattern
   **Severity:** minor

4. **Function is missing a return type annotation** (`TYP-051`)
   **File:** `src/heretek_swarm/collective/adaptive_learning.py`
   **Line:** 117
   ```python
   class EnvironmentProfile:
       """Profile of the current environment for adaptive learning."""
       
       def __init__(self):
           self.stability: float = 0.5
           self.complexity: float = 0.5
           self.demand_profile: Dict[str, float] = {}
   ```
   **Category:** Type check
   **Severity:** minor

5. **Function is missing a return type annotation** (`TYP-051`)
   **File:** `src/heretek_swarm/collective/knowledge_transform.py`
   **Line:** 958
   ```python
   patterns and distributing knowledge across the swarm.
       """
       
       def __init__(self):
           """Initialize knowledge transformation service."""
           self.transformer = KnowledgeTransformer()
           self._transformation_history: List[TransformationResult] = []
   ```
   **Category:** Type check
   **Severity:** minor

6. **Function is missing a return type annotation** (`TYP-051`)
   **File:** `src/heretek_swarm/collective/knowledge_transform.py`
   **Line:** 133
   ```python
   validation_rules: Validation rules for transformed knowledge
       """
       
       def __init__(self):
           """Initialize knowledge transformer."""
           self._agent_profiles: Dict[str, AgentCapabilityProfile] = {}
           self._transformation_rules: Dict[TransformationType, Callable] = {}
   ```
   **Category:** Type check
   **Severity:** minor

7. **Function is missing a type annotation for one or more arguments** (`TYP-051`)
   **File:** `src/heretek_swarm/collective/pattern_library.py`
   **Line:** 752
   ```python
   error=str(e),
                   )
       
       async def _call_callbacks(self, event: str, *args) -> None:
           """Call registered callbacks for an event."""
           for callback in self._callbacks.get(event, []):
               try:
   ```
   **Category:** Type check
   **Severity:** minor

8. **Incompatible return value type (got "Tuple[float, ...]", expected "Tuple[float, float, float]")** (`TYP-005`)
   **File:** `src/heretek_swarm/collective/swarm_intelligence.py`
   **Line:** 1190
   ```python
   if magnitude > 0:
               result = tuple(v / magnitude for v in result)
   
           return result
   
       def _calculate_flocking_cohesion(self) -> float:
           """Calculate overall flock cohesion."""
   ```
   **Category:** Type check
   **Severity:** major

9. **Incompatible return value type (got "Tuple[float, ...]", expected "Tuple[float, float, float]")** (`TYP-005`)
   **File:** `src/heretek_swarm/collective/swarm_intelligence.py`
   **Line:** 1134
   ```python
   avg_velocity = tuple(v / len(agent.neighbors) for v in avg_velocity)
   
           # Steering force is difference from current velocity
           return tuple(a - c for a, c in zip(avg_velocity, agent.velocity))
   
       def _calculate_cohesion(self, agent: FlockingAgent) -> Tuple[float, float, float]:
           """Calculate cohesion steering force."""
   ```
   **Category:** Type check
   **Severity:** major

10. **Incompatible return value type (got "List[float]", expected "Tuple[float, float, float]")** (`TYP-005`)
    **File:** `src/heretek_swarm/collective/swarm_intelligence.py`
    **Line:** 1119
    ```python
    if count > 0:
                separation = tuple(s / count for s in separation)
    
            return separation
    
        def _calculate_alignment(self, agent: FlockingAgent) -> Tuple[float, float, float]:
            """Calculate alignment steering force."""
    ```
    **Category:** Type check
    **Severity:** major

11. **Incompatible return value type (got "Tuple[float, ...]", expected "Tuple[float, float, float]")** (`TYP-005`)
    **File:** `src/heretek_swarm/collective/swarm_intelligence.py`
    **Line:** 1172
    ```python
    for agent in self.flocking_agents.values():
                center = tuple(c + a for c, a in zip(center, agent.position))
    
            return tuple(c / len(self.flocking_agents) for c in center)
    
        def _calculate_average_heading(self) -> Tuple[float, float, float]:
            """Calculate average heading of the flock."""
    ```
    **Category:** Type check
    **Severity:** major

12. **Incompatible return value type (got "Tuple[float, ...]", expected "Tuple[float, float, float]")** (`TYP-005`)
    **File:** `src/heretek_swarm/collective/swarm_intelligence.py`
    **Line:** 1149
    ```python
    center = tuple(c / len(agent.neighbors) for c in center)
    
            # Steering force toward center
            return tuple(c - p for c, p in zip(center, agent.position))
    
        def _update_flocking_position(self, agent: FlockingAgent) -> None:
            """Update agent position based on velocity."""
    ```
    **Category:** Type check
    **Severity:** major

# DeepSource Code Review Report

**Repository:** Heretek-AI/heretek-swarm
**Branch:** `main`
**Commit:** 0cb3ece...87670b9
**Run:** [https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/d75fe5fc-f085-4e9f-a0b2-aa83ad85261d/](https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/d75fe5fc-f085-4e9f-a0b2-aa83ad85261d/)

---

## Summary
- **Secrets:** No issues detected- **Docker:** No issues detected- **SQL:** No issues detected- **Shell:** No issues detected- **JavaScript:** No issues detected- **Python:** 170 issues

---

## Code Review Findings
### Secrets
**Status:** Success
**Findings:** No new issues detected
### Docker
**Status:** Success
**Findings:** No new issues detected
### SQL
**Status:** Success
**Findings:** No new issues detected
### Shell
**Status:** Success
**Findings:** No new issues detected
### JavaScript
**Status:** Success
**Findings:** No new issues detected
### Python
**Status:** Failure
**Findings:** 170 new issues

1. **`fix_unused_imports` has a cyclomatic complexity of 25 with "high" risk** (`PY-R1000`)
   **File:** `fix_antipatterns.py`
   **Line:** 37
   ```python
   return files
   
   
   def fix_unused_imports(_content: str) -> Tuple[str, int]:
       """Remove unused imports. Returns fixed content and count of fixes."""
       _lines = content.split('\n')
       _fixed_lines = []
   ```
   **Category:** Anti-pattern
   **Severity:** minor

2. **nonlocal name count found without binding** (`PYL-E0117`)
   **File:** `fix_antipatterns.py`
   **Line:** 349
   ```python
   _pattern = re.compile(r'all\(\s*\[\s*(.+?)\s+for\s+(\w+)\s+in\s+(\w+)\s*\]\s*\)')
       
       def replace_with_all(_match):
           nonlocal count
           _condition = match.group(1)
           item = match.group(2)
           _iterable = match.group(3)
   ```
   **Category:** Bug risk
   **Severity:** major

3. **Consider removing the commented out code block** (`PY-W0069`)
   **File:** `fix_antipatterns.py`
   **Line:** 59
   ```python
   _import_info = []
       for imp in imports:
           if imp.startswith('import '):
               # import os, sys
               _names = [n.strip().split('.')[0] for n in imp[7:].split(',')]
               import_info.append((imp, set(names)))
           elif imp.startswith('from '):
   ```
   **Category:** Anti-pattern
   **Severity:** major

4. **nonlocal name count found without binding** (`PYL-E0117`)
   **File:** `fix_antipatterns.py`
   **Line:** 186
   ```python
   _func_pattern = re.compile(r'^(.*?def\s+\w+\()([^)]+)(\).*:.*)$', re.MULTILINE)
       
       def fix_args(_match):
           nonlocal count
           _prefix = match.group(1)
           _args_str = match.group(2)
           _suffix = match.group(3)
   ```
   **Category:** Bug risk
   **Severity:** major

5. **Unused import os** (`PY-W2000`)
   **File:** `fix_antipatterns.py`
   **Line:** 6
   ```python
   Fixes PY-W2000, PYL-W0612, PYL-W0404, PYL-W0613, PYL-C0201, PYL-R1714, PY-W0069, PY-W0070, PY-W0075
   """
   
   import os
   import re
   from pathlib import Path
   from typing import List, Tuple
   ```
   **Category:** Anti-pattern
   **Severity:** major

6. **Unused variable 'rest'** (`PYL-W0612`)
   **File:** `fix_antipatterns.py`
   **Line:** 323
   ```python
   # Match: name = []
           match = re.match(r'^(\s*)(\w+)\s*=\s*\[\](.*)$', line)
           if match:
               indent, name, rest = match.groups()
               # Check if next line is name.append(...)
               if i + 1 < len(lines):
                   _next_line = lines[i + 1]
   ```
   **Category:** Anti-pattern
   **Severity:** major

7. **Consider removing the commented out code block** (`PY-W0069`)
   **File:** `fix_antipatterns.py`
   **Line:** 63
   ```python
   _names = [n.strip().split('.')[0] for n in imp[7:].split(',')]
               import_info.append((imp, set(names)))
           elif imp.startswith('from '):
               # from os import path, getcwd
               match = re.match(r'from\s+([\w.]+)\s+import\s+(.+)', imp)
               if match:
                   _module = match.group(1)
   ```
   **Category:** Anti-pattern
   **Severity:** major

8. **Undefined variable 'content'** (`PYL-E0602`)
   **File:** `fix_antipatterns.py`
   **Line:** 357
   ```python
   return f'all({condition} for {item} in {iterable})'
       
       _content = pattern.sub(replace_with_all, content)
       return content, count
   
   
   def main():
   ```
   **Category:** Bug risk
   **Severity:** critical

9. **Undefined variable 'import_info'** (`PYL-E0602`)
   **File:** `fix_antipatterns.py`
   **Line:** 74
   ```python
   _fixed = content
       _count = 0
       
       for imp_line, names in reversed(import_info):  # Reverse to maintain line numbers
           unused_in_this_import = set()
           for name in names:
               # Check if name is used (as variable, function call, attribute, etc.)
   ```
   **Category:** Bug risk
   **Severity:** critical

10. **Undefined variable 'args'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 209
    ```python
    _func_end = match.end()
            
            _new_args = []
            for arg, name in args:
                if name in ['self', 'cls', 'args', 'kwargs']:
                    new_args.append(arg)
                elif name.startswith('_'):
    ```
    **Category:** Bug risk
    **Severity:** critical

11. **Undefined variable 'dirs'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 29
    ```python
    def find_py_files(_dirs: List[Path]) -> List[Path]:
        """Find all Python files in the given directories."""
        _files = []
        for d in dirs:
            if d.exists():
                for f in d.rglob("*.py"):
                    if ".pytest_cache" not in str(f) and "node_modules" not in str(f):
    ```
    **Category:** Bug risk
    **Severity:** critical

12. **Undefined variable 'new_line'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 172
    ```python
    if f'\b{var_name}\b' not in rest and f'.{var_name}' not in rest:
                    # Prefix with _
                    _new_line = f'{indent}_{var_name} = {value}'
                    _content = content.replace(line, new_line)
                    count += 1
        
        return content, count
    ```
    **Category:** Bug risk
    **Severity:** critical

13. **Undefined variable 'lines'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 297
    ```python
    _commented_block = []
                j = i
                while j < len(lines) and re.match(r'^\s*#', lines[j]):
                    commented_block.append(lines[j])
                    j += 1
                
                # If we found 2+ consecutive commented lines, likely dead code
    ```
    **Category:** Bug risk
    **Severity:** critical

14. **Undefined variable 'content'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 274
    ```python
    else:
                _new = f'if {var} in ({val1}, {val2}):'
            
            _content = content[:match.start()] + content[match.start():match.end()].replace(
                match.group(0), f'{var} in ({val1}, {val2})'
            ) + content[match.end():]
            count += 1
    ```
    **Category:** Bug risk
    **Severity:** critical

15. **Undefined variable 'lines'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 45
    ```python
    _import_indices = []
        
        # Find all import lines
        for i, line in enumerate(lines):
            if re.match(r'^(import |from \w)', line):
                imports.append(line)
                import_indices.append(i)
    ```
    **Category:** Bug risk
    **Severity:** critical

16. **Undefined variable 'import_indices'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 48
    ```python
    for i, line in enumerate(lines):
            if re.match(r'^(import |from \w)', line):
                imports.append(line)
                import_indices.append(i)
        
        # Track what's used in the file
        _used_names = set()
    ```
    **Category:** Bug risk
    **Severity:** critical

17. **Undefined variable 'var'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 270
    ```python
    if more_vals:
                _all_vals = [val1, val2] + more_vals
                _new = f'if {var} in ({", ".join(all_vals)}):'
            else:
                _new = f'if {var} in ({val1}, {val2}):'
    ```
    **Category:** Bug risk
    **Severity:** critical

18. **Undefined variable 'var'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 272
    ```python
    _all_vals = [val1, val2] + more_vals
                _new = f'if {var} in ({", ".join(all_vals)}):'
            else:
                _new = f'if {var} in ({val1}, {val2}):'
            
            _content = content[:match.start()] + content[match.start():match.end()].replace(
                match.group(0), f'{var} in ({val1}, {val2})'
    ```
    **Category:** Bug risk
    **Severity:** critical

19. **Undefined variable 'append_match'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 330
    ```python
    _append_match = re.match(rf'^(\s*){re.escape(name)}\.append\(\s*([^\)]+)\s*\)(.*)$', next_line)
                    if append_match:
                        # Combine into single initialization
                        _new_line = f'{indent}{name} = [{append_match.group(2)}]{append_match.group(3)}'
                        _content = content.replace(line, new_line)
                        _content = content.replace(next_line + '\n', '').replace(next_line, '')
                        count += 1
    ```
    **Category:** Bug risk
    **Severity:** critical

20. **Undefined variable 'args_str'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 193
    ```python
    # Parse arguments
            _args = []
            for arg in args_str.split(','):
                _arg = arg.strip()
                if arg and '=' in arg:
                    _name = arg.split('=')[0].strip()
    ```
    **Category:** Bug risk
    **Severity:** critical

21. **Undefined variable 'lines'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 125
    ```python
    _merged = True
                    while j < len(lines) and merged:
                        _merged = False
                        _next_match = re.match(rf'(from\s+{re.escape(module)}\s+import\s+)(.+)', lines[j])
                        if next_match:
                            names.append(next_match.group(2).strip())
                            _merged = True
    ```
    **Category:** Bug risk
    **Severity:** critical

22. **Undefined variable 'pattern'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 248
    ```python
    # Pattern: var in (val1, val2) (possibly with extra ors)
        while True:
            _pattern = re.compile(r'\b(\w+)\s*==\s*([^\s,]+)\s+or\s+(?:\w+)\s*==\s*([^\s,]+)\b')
            match = pattern.search(content)
            if not match:
                break
    ```
    **Category:** Bug risk
    **Severity:** critical

23. **Undefined variable 'condition'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 354
    ```python
    item = match.group(2)
            _iterable = match.group(3)
            count += 1
            return f'all({condition} for {item} in {iterable})'
        
        _content = pattern.sub(replace_with_all, content)
        return content, count
    ```
    **Category:** Bug risk
    **Severity:** critical

24. **Undefined variable 'lines'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 319
    ```python
    i = 0
        
        while i < len(lines):
            _line = lines[i]
            # Match: name = []
            match = re.match(r'^(\s*)(\w+)\s*=\s*\[\](.*)$', line)
            if match:
    ```
    **Category:** Bug risk
    **Severity:** critical

25. **Undefined variable 'more_vals'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 263
    ```python
    while True:
                m = re.match(r'\s+or\s+(\w+)\s*==\s*([^\s,]+)', temp)
                if m:
                    more_vals.append(m.group(2))
                    _temp = temp[m.end():]
                else:
                    break
    ```
    **Category:** Bug risk
    **Severity:** critical

26. **Undefined variable 'module_match'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 118
    ```python
    if lines[i].startswith('from ') and ' import ' in lines[i]:
                _module_match = re.match(r'(from\s+([\w.]+)\s+import\s+)(.+)', lines[i])
                if module_match:
                    _base = module_match.group(1)
                    _module = module_match.group(2)
                    _names = [module_match.group(3).strip()]
                    j = i + 1
    ```
    **Category:** Bug risk
    **Severity:** critical

27. **Undefined variable 'module'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 125
    ```python
    _merged = True
                    while j < len(lines) and merged:
                        _merged = False
                        _next_match = re.match(rf'(from\s+{re.escape(module)}\s+import\s+)(.+)', lines[j])
                        if next_match:
                            names.append(next_match.group(2).strip())
                            _merged = True
    ```
    **Category:** Bug risk
    **Severity:** critical

28. **Undefined variable 'content'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 238
    ```python
    _content = content.replace(old, new)
            count += 1
        
        return content, count
    
    
    def fix_or_equality_comparisons(_content: str) -> Tuple[str, int]:
    ```
    **Category:** Bug risk
    **Severity:** critical

29. **Undefined variable 'content'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 285
    ```python
    def fix_commented_code(_content: str) -> Tuple[str, int]:
        """Remove commented out code - PY-W0069."""
        _count = 0
        _lines = content.split('\n')
        _fixed_lines = []
        i = 0
    ```
    **Category:** Bug risk
    **Severity:** critical

30. **Undefined variable 'more_vals'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 268
    ```python
    else:
                    break
            
            if more_vals:
                _all_vals = [val1, val2] + more_vals
                _new = f'if {var} in ({", ".join(all_vals)}):'
            else:
    ```
    **Category:** Bug risk
    **Severity:** critical

31. **Undefined variable 'names'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 137
    ```python
    if len(names) > 1:
                        # Consolidate
                        _all_names = []
                        for n in names:
                            all_names.extend([x.strip().split(' as ')[0] for x in n.split(',')])
                        lines[i] = base + ', '.join(all_names)
                        # Remove merged lines
    ```
    **Category:** Bug risk
    **Severity:** critical

32. **Undefined variable 'fixed'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 101
    ```python
    _new_names_str = ', '.join(n for n in old_names if n in new_names)
                        if new_names_str:
                            _new_line = prefix + new_names_str
                            _fixed = fixed.replace(imp_line, new_line)
                            count += 1
        
        return fixed, count
    ```
    **Category:** Bug risk
    **Severity:** critical

33. **Undefined variable 'total_fixes'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 423
    ```python
    print("="*60)
        print(f"\nFiles modified: {files_modified}")
        print("\nFixes by category:")
        for issue, count in total_fixes.items():
            if count > 0:
                print(f"  {issue}: {count}")
        print("="*60)
    ```
    **Category:** Bug risk
    **Severity:** critical

34. **Undefined variable 'fixed'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 104
    ```python
    _fixed = fixed.replace(imp_line, new_line)
                            count += 1
        
        return fixed, count
    
    
    def fix_multi_imports(_content: str) -> Tuple[str, int]:
    ```
    **Category:** Bug risk
    **Severity:** critical

35. **Undefined variable 'new_args'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 215
    ```python
    elif name.startswith('_'):
                    new_args.append(arg)  # Already prefixed
                else:
                    new_args.append(f'_{name}')
                    count += 1
            
            return prefix + ', '.join(new_args) + suffix
    ```
    **Category:** Bug risk
    **Severity:** critical

36. **Undefined variable 'append_match'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 330
    ```python
    _append_match = re.match(rf'^(\s*){re.escape(name)}\.append\(\s*([^\)]+)\s*\)(.*)$', next_line)
                    if append_match:
                        # Combine into single initialization
                        _new_line = f'{indent}{name} = [{append_match.group(2)}]{append_match.group(3)}'
                        _content = content.replace(line, new_line)
                        _content = content.replace(next_line + '\n', '').replace(next_line, '')
                        count += 1
    ```
    **Category:** Bug risk
    **Severity:** critical

37. **Undefined variable 'next_match'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 126
    ```python
    while j < len(lines) and merged:
                        _merged = False
                        _next_match = re.match(rf'(from\s+{re.escape(module)}\s+import\s+)(.+)', lines[j])
                        if next_match:
                            names.append(next_match.group(2).strip())
                            _merged = True
                            j += 1
    ```
    **Category:** Bug risk
    **Severity:** critical

38. **Undefined variable 'all_names'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 139
    ```python
    _all_names = []
                        for n in names:
                            all_names.extend([x.strip().split(' as ')[0] for x in n.split(',')])
                        lines[i] = base + ', '.join(all_names)
                        # Remove merged lines
                        lines[i+1:j] = []
            i += 1
    ```
    **Category:** Bug risk
    **Severity:** critical

39. **Undefined variable 'total_fixes'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 388
    ```python
    total_fixes['PY-W2000'] += c
                
                content, c = fix_multi_imports(content)
                total_fixes['PYL-W0404'] += c
                
                content, c = fix_unused_variables(content)
                total_fixes['PYL-W0612'] += c
    ```
    **Category:** Bug risk
    **Severity:** critical

40. **Undefined variable 'content'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 39
    ```python
    def fix_unused_imports(_content: str) -> Tuple[str, int]:
        """Remove unused imports. Returns fixed content and count of fixes."""
        _lines = content.split('\n')
        _fixed_lines = []
        _imports = []
        _import_indices = []
    ```
    **Category:** Bug risk
    **Severity:** critical

41. **Undefined variable 'val2'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 275
    ```python
    _new = f'if {var} in ({val1}, {val2}):'
            
            _content = content[:match.start()] + content[match.start():match.end()].replace(
                match.group(0), f'{var} in ({val1}, {val2})'
            ) + content[match.end():]
            count += 1
    ```
    **Category:** Bug risk
    **Severity:** critical

42. **Undefined variable 'lines'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 115
    ```python
    _lines = content.split('\n')
        i = 0
        while i < len(lines):
            if lines[i].startswith('from ') and ' import ' in lines[i]:
                _module_match = re.match(r'(from\s+([\w.]+)\s+import\s+)(.+)', lines[i])
                if module_match:
                    _base = module_match.group(1)
    ```
    **Category:** Bug risk
    **Severity:** critical

43. **Undefined variable 'content'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 230
    ```python
    # Pattern: for key in dict:
        _pattern = re.compile(r'\bfor\s+(\w+)\s+in\s+(\w+)\.keys\(\):')
        _matches = pattern.findall(content)
        
        for key, dict_name in matches:
            _old = f'for {key} in {dict_name}.keys():'
    ```
    **Category:** Bug risk
    **Severity:** critical

44. **Undefined variable 'lines'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 115
    ```python
    _lines = content.split('\n')
        i = 0
        while i < len(lines):
            if lines[i].startswith('from ') and ' import ' in lines[i]:
                _module_match = re.match(r'(from\s+([\w.]+)\s+import\s+)(.+)', lines[i])
                if module_match:
                    _base = module_match.group(1)
    ```
    **Category:** Bug risk
    **Severity:** critical

45. **Undefined variable 'lines'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 139
    ```python
    _all_names = []
                        for n in names:
                            all_names.extend([x.strip().split(' as ')[0] for x in n.split(',')])
                        lines[i] = base + ', '.join(all_names)
                        # Remove merged lines
                        lines[i+1:j] = []
            i += 1
    ```
    **Category:** Bug risk
    **Severity:** critical

46. **Undefined variable 'val1'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 269
    ```python
    break
            
            if more_vals:
                _all_vals = [val1, val2] + more_vals
                _new = f'if {var} in ({", ".join(all_vals)}):'
            else:
                _new = f'if {var} in ({val1}, {val2}):'
    ```
    **Category:** Bug risk
    **Severity:** critical

47. **Undefined variable 'match'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 205
    ```python
    # Check which args are used in the function body
            # Find function end
            _func_start = match.start()
            _func_end = match.end()
            
            _new_args = []
    ```
    **Category:** Bug risk
    **Severity:** critical

48. **Undefined variable 'imports'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 57
    ```python
    # Extract names from imports
        _import_info = []
        for imp in imports:
            if imp.startswith('import '):
                # import os, sys
                _names = [n.strip().split('.')[0] for n in imp[7:].split(',')]
    ```
    **Category:** Bug risk
    **Severity:** critical

49. **Undefined variable 'new_names_str'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 100
    ```python
    _old_names = [n.strip().split(' as ')[0] for n in old_names_str.split(',')]
                        _new_names_str = ', '.join(n for n in old_names if n in new_names)
                        if new_names_str:
                            _new_line = prefix + new_names_str
                            _fixed = fixed.replace(imp_line, new_line)
                            count += 1
    ```
    **Category:** Bug risk
    **Severity:** critical

50. **Undefined variable 'module_match'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 120
    ```python
    if module_match:
                    _base = module_match.group(1)
                    _module = module_match.group(2)
                    _names = [module_match.group(3).strip()]
                    j = i + 1
                    _merged = True
                    while j < len(lines) and merged:
    ```
    **Category:** Bug risk
    **Severity:** critical

51. **Undefined variable 'new_names_str'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 99
    ```python
    _old_names_str = match.group(2)
                        _old_names = [n.strip().split(' as ')[0] for n in old_names_str.split(',')]
                        _new_names_str = ', '.join(n for n in old_names if n in new_names)
                        if new_names_str:
                            _new_line = prefix + new_names_str
                            _fixed = fixed.replace(imp_line, new_line)
                            count += 1
    ```
    **Category:** Bug risk
    **Severity:** critical

52. **Undefined variable 'func_pattern'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 220
    ```python
    return prefix + ', '.join(new_args) + suffix
        
        _content = func_pattern.sub(fix_args, content)
        return content, count
    ```
    **Category:** Bug risk
    **Severity:** critical

53. **Undefined variable 'match'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 189
    ```python
    nonlocal count
            _prefix = match.group(1)
            _args_str = match.group(2)
            _suffix = match.group(3)
            
            # Parse arguments
            _args = []
    ```
    **Category:** Bug risk
    **Severity:** critical

54. **Undefined variable 'lines'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 52
    ```python
    # Track what's used in the file
        _used_names = set()
        non_import_lines = [l for l in lines if not re.match(r'^(import |from \w)', l)]
        _non_import_content = '\n'.join(non_import_lines)
        
        # Extract names from imports
    ```
    **Category:** Bug risk
    **Severity:** critical

55. **Undefined variable 'temp'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 264
    ```python
    m = re.match(r'\s+or\s+(\w+)\s*==\s*([^\s,]+)', temp)
                if m:
                    more_vals.append(m.group(2))
                    _temp = temp[m.end():]
                else:
                    break
    ```
    **Category:** Bug risk
    **Severity:** critical

56. **Undefined variable 'patterns'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 81
    ```python
    _patterns = [
                    rf'\b{name}\b',  # Basic word boundary
                ]
                _used = any(re.search(p, non_import_content) for p in patterns)
                if not used:
                    unused_in_this_import.add(name)
    ```
    **Category:** Bug risk
    **Severity:** critical

57. **Undefined variable 'match'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 187
    ```python
    def fix_args(_match):
            nonlocal count
            _prefix = match.group(1)
            _args_str = match.group(2)
            _suffix = match.group(3)
    ```
    **Category:** Bug risk
    **Severity:** critical

58. **Undefined variable 'lines'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 296
    ```python
    # Could be commented code, check if next few lines form a block
                _commented_block = []
                j = i
                while j < len(lines) and re.match(r'^\s*#', lines[j]):
                    commented_block.append(lines[j])
                    j += 1
    ```
    **Category:** Bug risk
    **Severity:** critical

59. **Undefined variable 'new_names'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 98
    ```python
    _prefix = match.group(1)
                        _old_names_str = match.group(2)
                        _old_names = [n.strip().split(' as ')[0] for n in old_names_str.split(',')]
                        _new_names_str = ', '.join(n for n in old_names if n in new_names)
                        if new_names_str:
                            _new_line = prefix + new_names_str
                            _fixed = fixed.replace(imp_line, new_line)
    ```
    **Category:** Bug risk
    **Severity:** critical

60. **Undefined variable 'line'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 321
    ```python
    while i < len(lines):
            _line = lines[i]
            # Match: name = []
            match = re.match(r'^(\s*)(\w+)\s*=\s*\[\](.*)$', line)
            if match:
                indent, name, rest = match.groups()
                # Check if next line is name.append(...)
    ```
    **Category:** Bug risk
    **Severity:** critical

61. **Undefined variable 'line'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 306
    ```python
    i = j
                    continue
            
            fixed_lines.append(line)
            i += 1
        
        return '\n'.join(fixed_lines), count
    ```
    **Category:** Bug risk
    **Severity:** critical

62. **Undefined variable 'imports'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 47
    ```python
    # Find all import lines
        for i, line in enumerate(lines):
            if re.match(r'^(import |from \w)', line):
                imports.append(line)
                import_indices.append(i)
        
        # Track what's used in the file
    ```
    **Category:** Bug risk
    **Severity:** critical

63. **Undefined variable 'total_fixes'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 409
    ```python
    total_fixes['PY-W0070'] += c
                
                content, c = fix_consider_using_all(content)
                total_fixes['PY-W0075'] += c
                
                if content != original:
                    filepath.write_text(content, encoding='utf-8')
    ```
    **Category:** Bug risk
    **Severity:** critical

64. **Undefined variable 'count'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 302
    ```python
    # If we found 2+ consecutive commented lines, likely dead code
                if len(commented_block) >= 2:
                    count += len(commented_block)
                    i = j
                    continue
    ```
    **Category:** Bug risk
    **Severity:** critical

65. **Undefined variable 'next_line'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 327
    ```python
    # Check if next line is name.append(...)
                if i + 1 < len(lines):
                    _next_line = lines[i + 1]
                    _append_match = re.match(rf'^(\s*){re.escape(name)}\.append\(\s*([^\)]+)\s*\)(.*)$', next_line)
                    if append_match:
                        # Combine into single initialization
                        _new_line = f'{indent}{name} = [{append_match.group(2)}]{append_match.group(3)}'
    ```
    **Category:** Bug risk
    **Severity:** critical

66. **Undefined variable 'lines'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 296
    ```python
    # Could be commented code, check if next few lines form a block
                _commented_block = []
                j = i
                while j < len(lines) and re.match(r'^\s*#', lines[j]):
                    commented_block.append(lines[j])
                    j += 1
    ```
    **Category:** Bug risk
    **Severity:** critical

67. **Undefined variable 'old_names'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 98
    ```python
    _prefix = match.group(1)
                        _old_names_str = match.group(2)
                        _old_names = [n.strip().split(' as ')[0] for n in old_names_str.split(',')]
                        _new_names_str = ', '.join(n for n in old_names if n in new_names)
                        if new_names_str:
                            _new_line = prefix + new_names_str
                            _fixed = fixed.replace(imp_line, new_line)
    ```
    **Category:** Bug risk
    **Severity:** critical

68. **Undefined variable 'count'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 333
    ```python
    _new_line = f'{indent}{name} = [{append_match.group(2)}]{append_match.group(3)}'
                        _content = content.replace(line, new_line)
                        _content = content.replace(next_line + '\n', '').replace(next_line, '')
                        count += 1
                        i += 1
                        continue
            i += 1
    ```
    **Category:** Bug risk
    **Severity:** critical

69. **Undefined variable 'lines'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 318
    ```python
    _lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            _line = lines[i]
            # Match: name = []
            match = re.match(r'^(\s*)(\w+)\s*=\s*\[\](.*)$', line)
    ```
    **Category:** Bug risk
    **Severity:** critical

70. **Undefined variable 'lines'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 326
    ```python
    indent, name, rest = match.groups()
                # Check if next line is name.append(...)
                if i + 1 < len(lines):
                    _next_line = lines[i + 1]
                    _append_match = re.match(rf'^(\s*){re.escape(name)}\.append\(\s*([^\)]+)\s*\)(.*)$', next_line)
                    if append_match:
                        # Combine into single initialization
    ```
    **Category:** Bug risk
    **Severity:** critical

71. **Undefined variable 'fixed'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 87
    ```python
    if unused_in_this_import and len(unused_in_this_import) == len(names):
                # All names unused - remove entire line
                _fixed = fixed.replace(imp_line + '\n', '').replace(imp_line, '')
                count += 1
            elif unused_in_this_import and len(names) > 1:
                # Partial - need to fix the line
    ```
    **Category:** Bug risk
    **Severity:** critical

72. **Undefined variable 'match'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 188
    ```python
    def fix_args(_match):
            nonlocal count
            _prefix = match.group(1)
            _args_str = match.group(2)
            _suffix = match.group(3)
            
            # Parse arguments
    ```
    **Category:** Bug risk
    **Severity:** critical

73. **Undefined variable 'content'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 248
    ```python
    # Pattern: var in (val1, val2) (possibly with extra ors)
        while True:
            _pattern = re.compile(r'\b(\w+)\s*==\s*([^\s,]+)\s+or\s+(?:\w+)\s*==\s*([^\s,]+)\b')
            match = pattern.search(content)
            if not match:
                break
    ```
    **Category:** Bug risk
    **Severity:** critical

74. **Undefined variable 'content'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 221
    ```python
    return prefix + ', '.join(new_args) + suffix
        
        _content = func_pattern.sub(fix_args, content)
        return content, count
    
    
    def fix_dict_keys_iteration(_content: str) -> Tuple[str, int]:
    ```
    **Category:** Bug risk
    **Severity:** critical

75. **Undefined variable 'content'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 220
    ```python
    return prefix + ', '.join(new_args) + suffix
        
        _content = func_pattern.sub(fix_args, content)
        return content, count
    ```
    **Category:** Bug risk
    **Severity:** critical

76. **Undefined variable 'prefix'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 100
    ```python
    _old_names = [n.strip().split(' as ')[0] for n in old_names_str.split(',')]
                        _new_names_str = ', '.join(n for n in old_names if n in new_names)
                        if new_names_str:
                            _new_line = prefix + new_names_str
                            _fixed = fixed.replace(imp_line, new_line)
                            count += 1
    ```
    **Category:** Bug risk
    **Severity:** critical

77. **Undefined variable 'lines'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 168
    ```python
    if var_name.startswith('_') or var_name.isupper():
                    continue
                # Check if var_name appears elsewhere in the file
                _rest = '\n'.join(lines[i+1:])
                if f'\b{var_name}\b' not in rest and f'.{var_name}' not in rest:
                    # Prefix with _
                    _new_line = f'{indent}_{var_name} = {value}'
    ```
    **Category:** Bug risk
    **Severity:** critical

78. **Undefined variable 'new_args'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 218
    ```python
    new_args.append(f'_{name}')
                    count += 1
            
            return prefix + ', '.join(new_args) + suffix
        
        _content = func_pattern.sub(fix_args, content)
        return content, count
    ```
    **Category:** Bug risk
    **Severity:** critical

79. **Undefined variable 'match'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 206
    ```python
    # Check which args are used in the function body
            # Find function end
            _func_start = match.start()
            _func_end = match.end()
            
            _new_args = []
            for arg, name in args:
    ```
    **Category:** Bug risk
    **Severity:** critical

80. **Undefined variable 'lines'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 152
    ```python
    _count = 0
        _lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Skip if already fixed or is import/class/def
            if any(x in line for x in ['import ', 'from ', 'class ', 'def ', 'async def ', '#']):
                continue
    ```
    **Category:** Bug risk
    **Severity:** critical

81. **Undefined variable 'var'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 275
    ```python
    _new = f'if {var} in ({val1}, {val2}):'
            
            _content = content[:match.start()] + content[match.start():match.end()].replace(
                match.group(0), f'{var} in ({val1}, {val2})'
            ) + content[match.end():]
            count += 1
    ```
    **Category:** Bug risk
    **Severity:** critical

82. **Undefined variable 'rest'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 169
    ```python
    continue
                # Check if var_name appears elsewhere in the file
                _rest = '\n'.join(lines[i+1:])
                if f'\b{var_name}\b' not in rest and f'.{var_name}' not in rest:
                    # Prefix with _
                    _new_line = f'{indent}_{var_name} = {value}'
                    _content = content.replace(line, new_line)
    ```
    **Category:** Bug risk
    **Severity:** critical

83. **Undefined variable 'non_import_content'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 81
    ```python
    _patterns = [
                    rf'\b{name}\b',  # Basic word boundary
                ]
                _used = any(re.search(p, non_import_content) for p in patterns)
                if not used:
                    unused_in_this_import.add(name)
    ```
    **Category:** Bug risk
    **Severity:** critical

84. **Undefined variable 'commented_block'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 297
    ```python
    _commented_block = []
                j = i
                while j < len(lines) and re.match(r'^\s*#', lines[j]):
                    commented_block.append(lines[j])
                    j += 1
                
                # If we found 2+ consecutive commented lines, likely dead code
    ```
    **Category:** Bug risk
    **Severity:** critical

85. **Undefined variable 'content'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 338
    ```python
    continue
            i += 1
        
        return content, count
    
    
    def fix_consider_using_all(_content: str) -> Tuple[str, int]:
    ```
    **Category:** Bug risk
    **Severity:** critical

86. **Undefined variable 'original'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 411
    ```python
    content, c = fix_consider_using_all(content)
                total_fixes['PY-W0075'] += c
                
                if content != original:
                    filepath.write_text(content, encoding='utf-8')
                    files_modified += 1
    ```
    **Category:** Bug risk
    **Severity:** critical

87. **Undefined variable 'content'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 315
    ```python
    def fix_list_append_after_def(_content: str) -> Tuple[str, int]:
        """Fix list.append() immediately after definition - PY-W0070."""
        _count = 0
        _lines = content.split('\n')
        i = 0
        
        while i < len(lines):
    ```
    **Category:** Bug risk
    **Severity:** critical

88. **Undefined variable 'matches'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 232
    ```python
    _pattern = re.compile(r'\bfor\s+(\w+)\s+in\s+(\w+)\.keys\(\):')
        _matches = pattern.findall(content)
        
        for key, dict_name in matches:
            _old = f'for {key} in {dict_name}.keys():'
            _new = f'for {key} in {dict_name}:'
            _content = content.replace(old, new)
    ```
    **Category:** Bug risk
    **Severity:** critical

89. **Undefined variable 'line'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 292
    ```python
    while i < len(lines):
            _line = lines[i]
            # Check for commented code patterns
            if re.match(r'^\s*#\s*(def |class |if |for |while |return |import |from )', line):
                # Could be commented code, check if next few lines form a block
                _commented_block = []
                j = i
    ```
    **Category:** Bug risk
    **Severity:** critical

90. **Undefined variable 'next_line'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 332
    ```python
    # Combine into single initialization
                        _new_line = f'{indent}{name} = [{append_match.group(2)}]{append_match.group(3)}'
                        _content = content.replace(line, new_line)
                        _content = content.replace(next_line + '\n', '').replace(next_line, '')
                        count += 1
                        i += 1
                        continue
    ```
    **Category:** Bug risk
    **Severity:** critical

91. **Undefined variable 'lines'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 141
    ```python
    all_names.extend([x.strip().split(' as ')[0] for x in n.split(',')])
                        lines[i] = base + ', '.join(all_names)
                        # Remove merged lines
                        lines[i+1:j] = []
            i += 1
        
        return '\n'.join(lines), count
    ```
    **Category:** Bug risk
    **Severity:** critical

92. **Undefined variable 'next_match'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 127
    ```python
    _merged = False
                        _next_match = re.match(rf'(from\s+{re.escape(module)}\s+import\s+)(.+)', lines[j])
                        if next_match:
                            names.append(next_match.group(2).strip())
                            _merged = True
                            j += 1
                            count += 1
    ```
    **Category:** Bug risk
    **Severity:** critical

93. **Undefined variable 'all_vals'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 270
    ```python
    if more_vals:
                _all_vals = [val1, val2] + more_vals
                _new = f'if {var} in ({", ".join(all_vals)}):'
            else:
                _new = f'if {var} in ({val1}, {val2}):'
    ```
    **Category:** Bug risk
    **Severity:** critical

94. **Undefined variable 'import_info'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 61
    ```python
    if imp.startswith('import '):
                # import os, sys
                _names = [n.strip().split('.')[0] for n in imp[7:].split(',')]
                import_info.append((imp, set(names)))
            elif imp.startswith('from '):
                # from os import path, getcwd
                match = re.match(r'from\s+([\w.]+)\s+import\s+(.+)', imp)
    ```
    **Category:** Bug risk
    **Severity:** critical

95. **Undefined variable 'files'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 34
    ```python
    for f in d.rglob("*.py"):
                    if ".pytest_cache" not in str(f) and "node_modules" not in str(f):
                        files.append(f)
        return files
    
    
    def fix_unused_imports(_content: str) -> Tuple[str, int]:
    ```
    **Category:** Bug risk
    **Severity:** critical

96. **Undefined variable 'commented_block'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 301
    ```python
    j += 1
                
                # If we found 2+ consecutive commented lines, likely dead code
                if len(commented_block) >= 2:
                    count += len(commented_block)
                    i = j
                    continue
    ```
    **Category:** Bug risk
    **Severity:** critical

97. **Undefined variable 'iterable'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 354
    ```python
    item = match.group(2)
            _iterable = match.group(3)
            count += 1
            return f'all({condition} for {item} in {iterable})'
        
        _content = pattern.sub(replace_with_all, content)
        return content, count
    ```
    **Category:** Bug risk
    **Severity:** critical

98. **Undefined variable 'content'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 276
    ```python
    _content = content[:match.start()] + content[match.start():match.end()].replace(
                match.group(0), f'{var} in ({val1}, {val2})'
            ) + content[match.end():]
            count += 1
        
        return content, count
    ```
    **Category:** Bug risk
    **Severity:** critical

99. **Undefined variable 'new_args'** (`PYL-E0602`)
    **File:** `fix_antipatterns.py`
    **Line:** 213
    ```python
    if name in ['self', 'cls', 'args', 'kwargs']:
                    new_args.append(arg)
                elif name.startswith('_'):
                    new_args.append(arg)  # Already prefixed
                else:
                    new_args.append(f'_{name}')
                    count += 1
    ```
    **Category:** Bug risk
    **Severity:** critical

100. **Undefined variable 'suffix'** (`PYL-E0602`)
     **File:** `fix_antipatterns.py`
     **Line:** 218
     ```python
     new_args.append(f'_{name}')
                     count += 1
             
             return prefix + ', '.join(new_args) + suffix
         
         _content = func_pattern.sub(fix_args, content)
         return content, count
     ```
     **Category:** Bug risk
     **Severity:** critical

*...and 70 more occurrences. [See full list on DeepSource](https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/d75fe5fc-f085-4e9f-a0b2-aa83ad85261d/).*
# DeepSource Code Review Report

**Repository:** Heretek-AI/heretek-swarm
**Branch:** `main`
**Commit:** 87670b9...6266fed
**Run:** [https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/d29461bc-d1e8-4773-8c88-08cda832b2f9/](https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/d29461bc-d1e8-4773-8c88-08cda832b2f9/)

---

## Summary
- **JavaScript:** No issues detected- **Secrets:** No issues detected- **Shell:** No issues detected- **Docker:** No issues detected- **SQL:** No issues detected- **Python:** 22065 issues

---

## Code Review Findings
### JavaScript
**Status:** Success
**Findings:** No new issues detected
### Secrets
**Status:** Success
**Findings:** No new issues detected
### Shell
**Status:** Success
**Findings:** No new issues detected
### Docker
**Status:** Success
**Findings:** No new issues detected
### SQL
**Status:** Success
**Findings:** No new issues detected
### Python
**Status:** Failure
**Findings:** 21519 new issues

1. **Undefined variable 'output_path'** (`PYL-E0602`)
   **File:** `generate_docker_compose.py`
   **Line:** 212
   ```python
   with open(output_path, "w", encoding="utf-8") as f:
       f.write(content)
   
   print(f"Successfully wrote docker-compose.autonomous.yml to {output_path}")
   ```
   **Category:** Bug risk
   **Severity:** critical

2. **Undefined variable 'output_path'** (`PYL-E0602`)
   **File:** `generate_docker_compose.py`
   **Line:** 209
   ```python
   _output_path = "C:/Users/derek/Desktop/Heretek-AI/heretek-swarm/docker-compose.autonomous.yml"
   
   with open(output_path, "w", encoding="utf-8") as f:
       f.write(content)
   
   print(f"Successfully wrote docker-compose.autonomous.yml to {output_path}")
   ```
   **Category:** Bug risk
   **Severity:** critical

3. **Undefined variable 'base_path'** (`PYL-E0602`)
   **File:** `generate_prometheus_config.py`
   **Line:** 52
   ```python
   """
   
   # Write prometheus.yml
   _prometheus_dir = os.path.join(base_path, "prometheus")
   os.makedirs(prometheus_dir, exist_ok=True)
   with open(os.path.join(prometheus_dir, "prometheus.yml"), "w", encoding="utf-8") as f:
       f.write(prometheus_yml)
   ```
   **Category:** Bug risk
   **Severity:** critical

4. **Undefined variable 'prometheus_dir'** (`PYL-E0602`)
   **File:** `generate_prometheus_config.py`
   **Line:** 54
   ```python
   # Write prometheus.yml
   _prometheus_dir = os.path.join(base_path, "prometheus")
   os.makedirs(prometheus_dir, exist_ok=True)
   with open(os.path.join(prometheus_dir, "prometheus.yml"), "w", encoding="utf-8") as f:
       f.write(prometheus_yml)
   
   print(f"Created: {os.path.join(prometheus_dir, 'prometheus.yml')}")
   ```
   **Category:** Bug risk
   **Severity:** critical

5. **Undefined variable 'prometheus_dir'** (`PYL-E0602`)
   **File:** `generate_prometheus_config.py`
   **Line:** 53
   ```python
   # Write prometheus.yml
   _prometheus_dir = os.path.join(base_path, "prometheus")
   os.makedirs(prometheus_dir, exist_ok=True)
   with open(os.path.join(prometheus_dir, "prometheus.yml"), "w", encoding="utf-8") as f:
       f.write(prometheus_yml)
   ```
   **Category:** Bug risk
   **Severity:** critical

6. **Undefined variable 'prometheus_dir'** (`PYL-E0602`)
   **File:** `generate_prometheus_config.py`
   **Line:** 57
   ```python
   with open(os.path.join(prometheus_dir, "prometheus.yml"), "w", encoding="utf-8") as f:
       f.write(prometheus_yml)
   
   print(f"Created: {os.path.join(prometheus_dir, 'prometheus.yml')}")
   
   # Docker compose overlay content (to be manually merged or used with -f flag)
   _docker_compose_additions = """
   ```
   **Category:** Bug risk
   **Severity:** critical

7. **Undefined variable 'prometheus_dir'** (`PYL-E0602`)
   **File:** `generate_prometheus_config.py`
   **Line:** 118
   ```python
   """
   
   print("Configuration files generated successfully!")
   print(f"Prometheus config: {prometheus_dir}/prometheus.yml")
   print("-" * 60)
   print("To enable Prometheus monitoring in docker-compose.autonomous.yml:")
   print("1. Add 'profiles: [default, monitoring]' to heretek-swarm service")
   ```
   **Category:** Bug risk
   **Severity:** critical

8. **Undefined variable 'name'** (`PYL-E0602`)
   **File:** `scripts/check_latency_baseline.py`
   **Line:** 53
   ```python
   })
           else:
               passes.append({
                   "name": name,
                   "mean_ms": mean_time_ms,
               })
   ```
   **Category:** Bug risk
   **Severity:** critical

9. **Undefined variable 'baseline_ms'** (`PYL-E0602`)
   **File:** `scripts/check_latency_baseline.py`
   **Line:** 43
   ```python
   _mean_time_s = bench.get("stats", {}).get("mean", 0)
           _mean_time_ms = mean_time_s * 1000
           
           if mean_time_ms > baseline_ms:
               failures.append({
                   "name": name,
                   "mean_ms": mean_time_ms,
   ```
   **Category:** Bug risk
   **Severity:** critical

10. **Undefined variable 'failures'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 64
    ```python
    print(f"Baseline threshold: {baseline_ms}ms")
        print(f"Total benchmarks: {len(benchmarks)}")
        print(f"Passed: {len(passes)}")
        print(f"Failed: {len(failures)}")
        print("=" * 60)
        
        if passes:
    ```
    **Category:** Bug risk
    **Severity:** critical

11. **Undefined variable 'mean_time_ms'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 48
    ```python
    "name": name,
                    "mean_ms": mean_time_ms,
                    "baseline_ms": baseline_ms,
                    "overage_ms": mean_time_ms - baseline_ms,
                    "overage_pct": ((mean_time_ms - baseline_ms) / baseline_ms) * 100,
                })
            else:
    ```
    **Category:** Bug risk
    **Severity:** critical

12. **Undefined variable 'benchmarks'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 62
    ```python
    print("LATENCY BASELINE CHECK REPORT")
        print("=" * 60)
        print(f"Baseline threshold: {baseline_ms}ms")
        print(f"Total benchmarks: {len(benchmarks)}")
        print(f"Passed: {len(passes)}")
        print(f"Failed: {len(failures)}")
        print("=" * 60)
    ```
    **Category:** Bug risk
    **Severity:** critical

13. **Undefined variable 'results'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 35
    ```python
    _failures = []
        _passes = []
        
        _benchmarks = results.get("benchmarks", [])
        
        for bench in benchmarks:
            _name = bench.get("name", "unknown")
    ```
    **Category:** Bug risk
    **Severity:** critical

14. **Undefined variable 'baseline'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 101
    ```python
    _benchmark_path = Path(sys.argv[1])
        _baseline = float(sys.argv[2]) if len(sys.argv) > 2 else 100.0
        
        sys.exit(check_latency_baseline(benchmark_path, baseline))
    ```
    **Category:** Bug risk
    **Severity:** critical

15. **Undefined variable 'baseline_ms'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 49
    ```python
    "mean_ms": mean_time_ms,
                    "baseline_ms": baseline_ms,
                    "overage_ms": mean_time_ms - baseline_ms,
                    "overage_pct": ((mean_time_ms - baseline_ms) / baseline_ms) * 100,
                })
            else:
                passes.append({
    ```
    **Category:** Bug risk
    **Severity:** critical

16. **Undefined variable 'failures'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 72
    ```python
    for p in passes:
                print(f"  • {p['name']}: {p['mean_ms']:.2f}ms")
        
        if failures:
            print("\n🚨 FAILING BENCHMARKS - FLAG FOR REFACTORING:")
            for f in failures:
                print(f"  ❌ {f['name']}")
    ```
    **Category:** Bug risk
    **Severity:** critical

17. **Undefined variable 'mean_time_ms'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 54
    ```python
    else:
                passes.append({
                    "name": name,
                    "mean_ms": mean_time_ms,
                })
        
        # Print report
    ```
    **Category:** Bug risk
    **Severity:** critical

18. **Undefined variable 'benchmark_file'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 26
    ```python
    1 if any benchmark exceeds baseline (flag for refactoring)
        """
        if not benchmark_file.exists():
            print(f"❌ Benchmark file not found: {benchmark_file}")
            return 1
        
        with open(benchmark_file) as f:
    ```
    **Category:** Bug risk
    **Severity:** critical

19. **Undefined variable 'mean_time_ms'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 43
    ```python
    _mean_time_s = bench.get("stats", {}).get("mean", 0)
            _mean_time_ms = mean_time_s * 1000
            
            if mean_time_ms > baseline_ms:
                failures.append({
                    "name": name,
                    "mean_ms": mean_time_ms,
    ```
    **Category:** Bug risk
    **Severity:** critical

20. **Undefined variable 'benchmarks'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 37
    ```python
    _benchmarks = results.get("benchmarks", [])
        
        for bench in benchmarks:
            _name = bench.get("name", "unknown")
            # Convert to milliseconds (benchmarks usually in seconds)
            _mean_time_s = bench.get("stats", {}).get("mean", 0)
    ```
    **Category:** Bug risk
    **Severity:** critical

21. **Undefined variable 'baseline_ms'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 48
    ```python
    "name": name,
                    "mean_ms": mean_time_ms,
                    "baseline_ms": baseline_ms,
                    "overage_ms": mean_time_ms - baseline_ms,
                    "overage_pct": ((mean_time_ms - baseline_ms) / baseline_ms) * 100,
                })
            else:
    ```
    **Category:** Bug risk
    **Severity:** critical

22. **Undefined variable 'name'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 45
    ```python
    if mean_time_ms > baseline_ms:
                failures.append({
                    "name": name,
                    "mean_ms": mean_time_ms,
                    "baseline_ms": baseline_ms,
                    "overage_ms": mean_time_ms - baseline_ms,
    ```
    **Category:** Bug risk
    **Severity:** critical

23. **Undefined variable 'benchmark_file'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 29
    ```python
    print(f"❌ Benchmark file not found: {benchmark_file}")
            return 1
        
        with open(benchmark_file) as f:
            _results = json.load(f)
        
        _failures = []
    ```
    **Category:** Bug risk
    **Severity:** critical

24. **Undefined variable 'passes'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 63
    ```python
    print("=" * 60)
        print(f"Baseline threshold: {baseline_ms}ms")
        print(f"Total benchmarks: {len(benchmarks)}")
        print(f"Passed: {len(passes)}")
        print(f"Failed: {len(failures)}")
        print("=" * 60)
    ```
    **Category:** Bug risk
    **Severity:** critical

25. **Undefined variable 'passes'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 69
    ```python
    if passes:
            print("\n✅ PASSING BENCHMARKS:")
            for p in passes:
                print(f"  • {p['name']}: {p['mean_ms']:.2f}ms")
        
        if failures:
    ```
    **Category:** Bug risk
    **Severity:** critical

26. **Undefined variable 'baseline_ms'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 47
    ```python
    failures.append({
                    "name": name,
                    "mean_ms": mean_time_ms,
                    "baseline_ms": baseline_ms,
                    "overage_ms": mean_time_ms - baseline_ms,
                    "overage_pct": ((mean_time_ms - baseline_ms) / baseline_ms) * 100,
                })
    ```
    **Category:** Bug risk
    **Severity:** critical

27. **Undefined variable 'mean_time_s'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 41
    ```python
    _name = bench.get("name", "unknown")
            # Convert to milliseconds (benchmarks usually in seconds)
            _mean_time_s = bench.get("stats", {}).get("mean", 0)
            _mean_time_ms = mean_time_s * 1000
            
            if mean_time_ms > baseline_ms:
                failures.append({
    ```
    **Category:** Bug risk
    **Severity:** critical

28. **Undefined variable 'benchmark_path'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 101
    ```python
    _benchmark_path = Path(sys.argv[1])
        _baseline = float(sys.argv[2]) if len(sys.argv) > 2 else 100.0
        
        sys.exit(check_latency_baseline(benchmark_path, baseline))
    ```
    **Category:** Bug risk
    **Severity:** critical

29. **Undefined variable 'failures'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 81
    ```python
    print("\n" + "=" * 60)
        
        if failures:
            print("❌ LATENCY BASELINE CHECK FAILED")
            print(f"   {len(failures)} module(s) exceed {baseline_ms}ms baseline")
            print("   FLAG FOR REFACTORING per Phase Directives")
    ```
    **Category:** Bug risk
    **Severity:** critical

30. **Undefined variable 'mean_time_ms'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 46
    ```python
    if mean_time_ms > baseline_ms:
                failures.append({
                    "name": name,
                    "mean_ms": mean_time_ms,
                    "baseline_ms": baseline_ms,
                    "overage_ms": mean_time_ms - baseline_ms,
                    "overage_pct": ((mean_time_ms - baseline_ms) / baseline_ms) * 100,
    ```
    **Category:** Bug risk
    **Severity:** critical

31. **Undefined variable 'failures'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 83
    ```python
    if failures:
            print("❌ LATENCY BASELINE CHECK FAILED")
            print(f"   {len(failures)} module(s) exceed {baseline_ms}ms baseline")
            print("   FLAG FOR REFACTORING per Phase Directives")
            return 1
    ```
    **Category:** Bug risk
    **Severity:** critical

32. **Undefined variable 'passes'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 52
    ```python
    "overage_pct": ((mean_time_ms - baseline_ms) / baseline_ms) * 100,
                })
            else:
                passes.append({
                    "name": name,
                    "mean_ms": mean_time_ms,
                })
    ```
    **Category:** Bug risk
    **Severity:** critical

33. **Undefined variable 'passes'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 67
    ```python
    print(f"Failed: {len(failures)}")
        print("=" * 60)
        
        if passes:
            print("\n✅ PASSING BENCHMARKS:")
            for p in passes:
                print(f"  • {p['name']}: {p['mean_ms']:.2f}ms")
    ```
    **Category:** Bug risk
    **Severity:** critical

34. **Undefined variable 'failures'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 44
    ```python
    _mean_time_ms = mean_time_s * 1000
            
            if mean_time_ms > baseline_ms:
                failures.append({
                    "name": name,
                    "mean_ms": mean_time_ms,
                    "baseline_ms": baseline_ms,
    ```
    **Category:** Bug risk
    **Severity:** critical

35. **Undefined variable 'failures'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 74
    ```python
    if failures:
            print("\n🚨 FAILING BENCHMARKS - FLAG FOR REFACTORING:")
            for f in failures:
                print(f"  ❌ {f['name']}")
                print(f"     Mean: {f['mean_ms']:.2f}ms")
                print(f"     Overage: +{f['overage_ms']:.2f}ms ({f['overage_pct']:.1f}% over baseline)")
    ```
    **Category:** Bug risk
    **Severity:** critical

36. **Undefined variable 'baseline_ms'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 83
    ```python
    if failures:
            print("❌ LATENCY BASELINE CHECK FAILED")
            print(f"   {len(failures)} module(s) exceed {baseline_ms}ms baseline")
            print("   FLAG FOR REFACTORING per Phase Directives")
            return 1
    ```
    **Category:** Bug risk
    **Severity:** critical

37. **Undefined variable 'baseline_ms'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 61
    ```python
    print("\n" + "=" * 60)
        print("LATENCY BASELINE CHECK REPORT")
        print("=" * 60)
        print(f"Baseline threshold: {baseline_ms}ms")
        print(f"Total benchmarks: {len(benchmarks)}")
        print(f"Passed: {len(passes)}")
        print(f"Failed: {len(failures)}")
    ```
    **Category:** Bug risk
    **Severity:** critical

38. **Undefined variable 'benchmark_file'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 25
    ```python
    0 if all benchmarks pass
            1 if any benchmark exceeds baseline (flag for refactoring)
        """
        if not benchmark_file.exists():
            print(f"❌ Benchmark file not found: {benchmark_file}")
            return 1
    ```
    **Category:** Bug risk
    **Severity:** critical

39. **Undefined variable 'mean_time_ms'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 49
    ```python
    "mean_ms": mean_time_ms,
                    "baseline_ms": baseline_ms,
                    "overage_ms": mean_time_ms - baseline_ms,
                    "overage_pct": ((mean_time_ms - baseline_ms) / baseline_ms) * 100,
                })
            else:
                passes.append({
    ```
    **Category:** Bug risk
    **Severity:** critical

40. **Undefined variable 'baseline_ms'** (`PYL-E0602`)
    **File:** `scripts/check_latency_baseline.py`
    **Line:** 49
    ```python
    "mean_ms": mean_time_ms,
                    "baseline_ms": baseline_ms,
                    "overage_ms": mean_time_ms - baseline_ms,
                    "overage_pct": ((mean_time_ms - baseline_ms) / baseline_ms) * 100,
                })
            else:
                passes.append({
    ```
    **Category:** Bug risk
    **Severity:** critical

41. **Undefined variable 'database_url'** (`PYL-E0602`)
    **File:** `scripts/run_migration.py`
    **Line:** 37
    ```python
    import asyncpg
            
            # Connect to database
            _conn = await asyncpg.connect(database_url)
            
            # Read migration file
            _migration_path = Path(__file__).parent.parent / "migrations" / "001_create_swarm_memories.sql"
    ```
    **Category:** Bug risk
    **Severity:** critical

42. **Undefined variable 'result'** (`PYL-E0602`)
    **File:** `scripts/run_migration.py`
    **Line:** 60
    ```python
    )
            """)
            
            if result:
                print("✅ Table verification passed")
            else:
                print("❌ Table verification failed")
    ```
    **Category:** Bug risk
    **Severity:** critical

43. **Undefined variable 'database_url'** (`PYL-E0602`)
    **File:** `scripts/run_migration.py`
    **Line:** 29
    ```python
    # Convert to asyncpg format
        if database_url.startswith("postgresql+asyncpg://"):
            _database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        
        print(f"Connecting to database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}")
    ```
    **Category:** Bug risk
    **Severity:** critical

44. **Undefined variable 'conn'** (`PYL-E0602`)
    **File:** `scripts/run_migration.py`
    **Line:** 47
    ```python
    print(f"Reading migration from: {migration_path}")
            
            # Execute migration
            await conn.execute(migration_sql)
            
            print("✅ Migration completed successfully!")
            print("✅ swarm_memories table created")
    ```
    **Category:** Bug risk
    **Severity:** critical

45. **Undefined variable 'database_url'** (`PYL-E0602`)
    **File:** `scripts/run_migration.py`
    **Line:** 31
    ```python
    if database_url.startswith("postgresql+asyncpg://"):
            _database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        
        print(f"Connecting to database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}")
        
        try:
            import asyncpg
    ```
    **Category:** Bug risk
    **Severity:** critical

46. **Undefined variable 'conn'** (`PYL-E0602`)
    **File:** `scripts/run_migration.py`
    **Line:** 67
    ```python
    return False
            
            # Close connection
            await conn.close()
            
            return True
    ```
    **Category:** Bug risk
    **Severity:** critical

47. **Undefined variable 'migration_path'** (`PYL-E0602`)
    **File:** `scripts/run_migration.py`
    **Line:** 41
    ```python
    # Read migration file
            _migration_path = Path(__file__).parent.parent / "migrations" / "001_create_swarm_memories.sql"
            with open(migration_path, 'r') as f:
                _migration_sql = f.read()
            
            print(f"Reading migration from: {migration_path}")
    ```
    **Category:** Bug risk
    **Severity:** critical

48. **Undefined variable 'migration_sql'** (`PYL-E0602`)
    **File:** `scripts/run_migration.py`
    **Line:** 47
    ```python
    print(f"Reading migration from: {migration_path}")
            
            # Execute migration
            await conn.execute(migration_sql)
            
            print("✅ Migration completed successfully!")
            print("✅ swarm_memories table created")
    ```
    **Category:** Bug risk
    **Severity:** critical

49. **Undefined variable 'success'** (`PYL-E0602`)
    **File:** `scripts/run_migration.py`
    **Line:** 83
    ```python
    if __name__ == "__main__":
        _success = asyncio.run(run_migration())
        sys.exit(0 if success else 1)
    ```
    **Category:** Bug risk
    **Severity:** critical

50. **Undefined variable 'database_url'** (`PYL-E0602`)
    **File:** `scripts/run_migration.py`
    **Line:** 31
    ```python
    if database_url.startswith("postgresql+asyncpg://"):
            _database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        
        print(f"Connecting to database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}")
        
        try:
            import asyncpg
    ```
    **Category:** Bug risk
    **Severity:** critical

51. **Undefined variable 'migration_path'** (`PYL-E0602`)
    **File:** `scripts/run_migration.py`
    **Line:** 44
    ```python
    with open(migration_path, 'r') as f:
                _migration_sql = f.read()
            
            print(f"Reading migration from: {migration_path}")
            
            # Execute migration
            await conn.execute(migration_sql)
    ```
    **Category:** Bug risk
    **Severity:** critical

52. **Undefined variable 'conn'** (`PYL-E0602`)
    **File:** `scripts/run_migration.py`
    **Line:** 53
    ```python
    print("✅ swarm_memories table created")
            
            # Verify table exists
            _result = await conn.fetchval("""None
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'swarm_memories'
    ```
    **Category:** Bug risk
    **Severity:** critical

53. **Undefined variable 'database_url'** (`PYL-E0602`)
    **File:** `scripts/run_migration.py`
    **Line:** 28
    ```python
    )
        
        # Convert to asyncpg format
        if database_url.startswith("postgresql+asyncpg://"):
            _database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        
        print(f"Connecting to database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}")
    ```
    **Category:** Bug risk
    **Severity:** critical

54. **`f-string` used without any expression** (`PTC-W0027`)
    **File:** `scripts/run_migrations.py`
    **Line:** 266
    ```python
    failed_count += 1
                logger.error(f"Migration {mf.name} failed")
        
        logger.info(f"\nMigration Summary:")
        logger.info(f"  Succeeded: {success_count}")
        logger.info(f"  Failed: {failed_count}")
    ```
    **Category:** Anti-pattern
    **Severity:** major

55. **Unused variable 'idx_def'** (`PYL-W0612`)
    **File:** `scripts/run_migrations.py`
    **Line:** 177
    ```python
    """)
                _indexes = cursor.fetchall()
                logger.info("  Indexes:")
                for idx_name, idx_def in indexes:
                    logger.info(f"    - {idx_name}")
            else:
                logger.info("\nswarm_memories table does not exist yet")
    ```
    **Category:** Anti-pattern
    **Severity:** major

56. **Undefined variable 'content'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 63
    ```python
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        _content = migration_file.read_text()
        _metadata = parse_migration_header(content)
        
        logger.info(f"Executing migration: {migration_file.name}")
        logger.info(f"  Description: {metadata.get('description', 'N/A')}")
    ```
    **Category:** Bug risk
    **Severity:** critical

57. **Undefined variable 'statements'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 92
    ```python
    _current_stmt = []
            
            # Execute each statement
            for i, stmt in enumerate(statements):
                _stmt = stmt.strip()
                if not stmt:
                    continue
    ```
    **Category:** Bug risk
    **Severity:** critical

58. **Undefined variable 'cursor'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 140
    ```python
    logger.info("No migrations table found. Run migrations to create it.")
            else:
                # Get applied migrations
                cursor.execute("SELECT version, applied_at FROM schema_migrations ORDER BY version")
                _rows = cursor.fetchall()
                logger.info("Applied migrations:")
                for version, applied in rows:
    ```
    **Category:** Bug risk
    **Severity:** critical

59. **Undefined variable 'current_stmt'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 86
    ```python
    continue
                current_stmt.append(line)
                if stripped.endswith(";"):
                    _stmt = "\n".join(current_stmt)
                    if stmt.strip():
                        statements.append(stmt)
                    _current_stmt = []
    ```
    **Category:** Bug risk
    **Severity:** critical

60. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 267
    ```python
    logger.error(f"Migration {mf.name} failed")
        
        logger.info(f"\nMigration Summary:")
        logger.info(f"  Succeeded: {success_count}")
        logger.info(f"  Failed: {failed_count}")
        
        return 1 if failed_count > 0 else 0
    ```
    **Category:** Bug risk
    **Severity:** critical

61. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 186
    ```python
    conn.close()
            
        except ImportError:
            logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
        except Exception as e:
            logger.error(f"Failed to check status: {e}")
    ```
    **Category:** Bug risk
    **Severity:** critical

62. **Undefined variable 'migration_file'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 62
    ```python
    import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        _content = migration_file.read_text()
        _metadata = parse_migration_header(content)
        
        logger.info(f"Executing migration: {migration_file.name}")
    ```
    **Category:** Bug risk
    **Severity:** critical

63. **Undefined variable 'cursor'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 128
    ```python
    _cursor = conn.cursor()
            
            # Check if migrations table exists
            cursor.execute("""None
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'schema_migrations'
    ```
    **Category:** Bug risk
    **Severity:** critical

64. **Undefined variable 'parser'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 231
    ```python
    _action = "store_true",
            _help = "Show what would be executed without running"
        )
        parser.add_argument(
            "--force",
            _action = "store_true",
            _help = "Force run all migrations (skip tracking)"
    ```
    **Category:** Bug risk
    **Severity:** critical

65. **Undefined variable 'cursor'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 170
    ```python
    logger.info(f"    - {col[0]}: {col[1]} (nullable: {col[2]})")
                
                # Show indexes
                cursor.execute("""None
                    SELECT indexname, indexdef 
                    FROM pg_indexes 
                    WHERE tablename = 'swarm_memories'
    ```
    **Category:** Bug risk
    **Severity:** critical

66. **Undefined variable 'conn'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 102
    ```python
    except psycopg2.Error as e:
                    logger.error(f"  Statement {i+1} failed: {e}")
                    logger.error(f"  Statement: {stmt[:200]}...")
                    conn.close()
                    return False
            
            cursor.close()
    ```
    **Category:** Bug risk
    **Severity:** critical

67. **Undefined variable 'migration_files'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 252
    ```python
    if args.dry_run:
            logger.info("Dry run - would execute:")
            for mf in migration_files:
                logger.info(f"  - {mf.name}")
            return 0
    ```
    **Category:** Bug risk
    **Severity:** critical

68. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 101
    ```python
    logger.debug(f"  Executed statement {i+1}/{len(statements)}")
                except psycopg2.Error as e:
                    logger.error(f"  Statement {i+1} failed: {e}")
                    logger.error(f"  Statement: {stmt[:200]}...")
                    conn.close()
                    return False
    ```
    **Category:** Bug risk
    **Severity:** critical

69. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 165
    ```python
    ORDER BY ordinal_position
                """)
                _columns = cursor.fetchall()
                logger.info("  Columns:")
                for col in columns:
                    logger.info(f"    - {col[0]}: {col[1]} (nullable: {col[2]})")
    ```
    **Category:** Bug risk
    **Severity:** critical

70. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 180
    ```python
    for idx_name, idx_def in indexes:
                    logger.info(f"    - {idx_name}")
            else:
                logger.info("\nswarm_memories table does not exist yet")
            
            cursor.close()
            conn.close()
    ```
    **Category:** Bug risk
    **Severity:** critical

71. **Undefined variable 'match'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 51
    ```python
    header["version"] = match.group(1)
        
        _match = re.search(r"-- Description: (.+)", content)
        if match:
            header["description"] = match.group(1)
        
        return header
    ```
    **Category:** Bug risk
    **Severity:** critical

72. **Undefined variable 'args'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 250
    ```python
    # Get and execute migrations
        _migration_files = get_migration_files()
        
        if args.dry_run:
            logger.info("Dry run - would execute:")
            for mf in migration_files:
                logger.info(f"  - {mf.name}")
    ```
    **Category:** Bug risk
    **Severity:** critical

73. **Undefined variable 'statements'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 98
    ```python
    continue
                try:
                    cursor.execute(stmt)
                    logger.debug(f"  Executed statement {i+1}/{len(statements)}")
                except psycopg2.Error as e:
                    logger.error(f"  Statement {i+1} failed: {e}")
                    logger.error(f"  Statement: {stmt[:200]}...")
    ```
    **Category:** Bug risk
    **Severity:** critical

74. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 144
    ```python
    _rows = cursor.fetchall()
                logger.info("Applied migrations:")
                for version, applied in rows:
                    logger.info(f"  {version}: {applied}")
            
            # Check if swarm_memories table exists
            cursor.execute("""
    ```
    **Category:** Bug risk
    **Severity:** critical

75. **Undefined variable 'cursor'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 105
    ```python
    conn.close()
                    return False
            
            cursor.close()
            conn.close()
            
            logger.info(f"  Migration {migration_file.name} completed successfully")
    ```
    **Category:** Bug risk
    **Severity:** critical

76. **Undefined variable 'migration_file'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 65
    ```python
    _content = migration_file.read_text()
        _metadata = parse_migration_header(content)
        
        logger.info(f"Executing migration: {migration_file.name}")
        logger.info(f"  Description: {metadata.get('description', 'N/A')}")
        
        try:
    ```
    **Category:** Bug risk
    **Severity:** critical

77. **Undefined variable 'conn'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 198
    ```python
    try:
            _conn = psycopg2.connect(DATABASE_URL)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            _cursor = conn.cursor()
            
            cursor.execute("""
    ```
    **Category:** Bug risk
    **Severity:** critical

78. **Undefined variable 'conn'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 183
    ```python
    logger.info("\nswarm_memories table does not exist yet")
            
            cursor.close()
            conn.close()
            
        except ImportError:
            logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
    ```
    **Category:** Bug risk
    **Severity:** critical

79. **Undefined variable 'parser'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 221
    ```python
    def main():
        _parser = argparse.ArgumentParser(description="Run database migrations")
        parser.add_argument(
            "--status", 
            _action = "store_true", 
            _help = "Check migration status"
    ```
    **Category:** Bug risk
    **Severity:** critical

80. **Undefined variable 'cursor'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 153
    ```python
    WHERE table_name = 'swarm_memories'
                );
            """)
            _exists = cursor.fetchone()[0]
            
            if exists:
                logger.info("\nswarm_memories table exists")
    ```
    **Category:** Bug risk
    **Severity:** critical

81. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 156
    ```python
    _exists = cursor.fetchone()[0]
            
            if exists:
                logger.info("\nswarm_memories table exists")
                # Show table structure
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
    ```
    **Category:** Bug risk
    **Severity:** critical

82. **Undefined variable 'exists'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 136
    ```python
    """)
            _exists = cursor.fetchone()[0]
            
            if not exists:
                logger.info("No migrations table found. Run migrations to create it.")
            else:
                # Get applied migrations
    ```
    **Category:** Bug risk
    **Severity:** critical

83. **Undefined variable 'conn'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 71
    ```python
    try:
            # Connect to database
            _conn = psycopg2.connect(DATABASE_URL)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            _cursor = conn.cursor()
            
            # Split and execute statements (handling semicolons)
    ```
    **Category:** Bug risk
    **Severity:** critical

84. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 251
    ```python
    _migration_files = get_migration_files()
        
        if args.dry_run:
            logger.info("Dry run - would execute:")
            for mf in migration_files:
                logger.info(f"  - {mf.name}")
            return 0
    ```
    **Category:** Bug risk
    **Severity:** critical

85. **Undefined variable 'content'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 46
    ```python
    """Parse migration file header for metadata."""
        _header = {}
        # Extract migration number and description from comments
        _match = re.search(r"-- Migration: (\d+)", content)
        if match:
            header["version"] = match.group(1)
    ```
    **Category:** Bug risk
    **Severity:** critical

86. **Undefined variable 'cursor'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 182
    ```python
    else:
                logger.info("\nswarm_memories table does not exist yet")
            
            cursor.close()
            conn.close()
            
        except ImportError:
    ```
    **Category:** Bug risk
    **Severity:** critical

87. **Undefined variable 'match'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 52
    ```python
    _match = re.search(r"-- Description: (.+)", content)
        if match:
            header["description"] = match.group(1)
        
        return header
    ```
    **Category:** Bug risk
    **Severity:** critical

88. **Undefined variable 'migration_files'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 38
    ```python
    return []
        
        _migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        logger.info(f"Found {len(migration_files)} migration files")
        return migration_files
    ```
    **Category:** Bug risk
    **Severity:** critical

89. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 38
    ```python
    return []
        
        _migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        logger.info(f"Found {len(migration_files)} migration files")
        return migration_files
    ```
    **Category:** Bug risk
    **Severity:** critical

90. **Undefined variable 'cursor'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 147
    ```python
    logger.info(f"  {version}: {applied}")
            
            # Check if swarm_memories table exists
            cursor.execute("""None
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'swarm_memories'
    ```
    **Category:** Bug risk
    **Severity:** critical

91. **Undefined variable 'stripped'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 85
    ```python
    if stripped.startswith("--") and not stripped.startswith("-- Migration"):
                    continue
                current_stmt.append(line)
                if stripped.endswith(";"):
                    _stmt = "\n".join(current_stmt)
                    if stmt.strip():
                        statements.append(stmt)
    ```
    **Category:** Bug risk
    **Severity:** critical

92. **Undefined variable 'cursor'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 201
    ```python
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            _cursor = conn.cursor()
            
            cursor.execute("""None
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(50) PRIMARY KEY,
                    description TEXT,
    ```
    **Category:** Bug risk
    **Severity:** critical

93. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 98
    ```python
    continue
                try:
                    cursor.execute(stmt)
                    logger.debug(f"  Executed statement {i+1}/{len(statements)}")
                except psycopg2.Error as e:
                    logger.error(f"  Statement {i+1} failed: {e}")
                    logger.error(f"  Statement: {stmt[:200]}...")
    ```
    **Category:** Bug risk
    **Severity:** critical

94. **Undefined variable 'match'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 47
    ```python
    _header = {}
        # Extract migration number and description from comments
        _match = re.search(r"-- Migration: (\d+)", content)
        if match:
            header["version"] = match.group(1)
        
        _match = re.search(r"-- Description: (.+)", content)
    ```
    **Category:** Bug risk
    **Severity:** critical

95. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 115
    ```python
    logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
            return False
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    ```
    **Category:** Bug risk
    **Severity:** critical

96. **Undefined variable 'header'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 52
    ```python
    _match = re.search(r"-- Description: (.+)", content)
        if match:
            header["description"] = match.group(1)
        
        return header
    ```
    **Category:** Bug risk
    **Severity:** critical

97. **Undefined variable 'conn'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 199
    ```python
    try:
            _conn = psycopg2.connect(DATABASE_URL)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            _cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
    ```
    **Category:** Bug risk
    **Severity:** critical

98. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 167
    ```python
    _columns = cursor.fetchall()
                logger.info("  Columns:")
                for col in columns:
                    logger.info(f"    - {col[0]}: {col[1]} (nullable: {col[2]})")
                
                # Show indexes
                cursor.execute("""
    ```
    **Category:** Bug risk
    **Severity:** critical

99. **Undefined variable 'logger'** (`PYL-E0602`)
    **File:** `scripts/run_migrations.py`
    **Line:** 100
    ```python
    cursor.execute(stmt)
                    logger.debug(f"  Executed statement {i+1}/{len(statements)}")
                except psycopg2.Error as e:
                    logger.error(f"  Statement {i+1} failed: {e}")
                    logger.error(f"  Statement: {stmt[:200]}...")
                    conn.close()
                    return False
    ```
    **Category:** Bug risk
    **Severity:** critical

100. **Undefined variable 'cursor'** (`PYL-E0602`)
     **File:** `scripts/run_migrations.py`
     **Line:** 141
     ```python
     else:
                 # Get applied migrations
                 cursor.execute("SELECT version, applied_at FROM schema_migrations ORDER BY version")
                 _rows = cursor.fetchall()
                 logger.info("Applied migrations:")
                 for version, applied in rows:
                     logger.info(f"  {version}: {applied}")
     ```
     **Category:** Bug risk
     **Severity:** critical

*...and 21965 more occurrences. [See full list on DeepSource](https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/d29461bc-d1e8-4773-8c88-08cda832b2f9/).*
# DeepSource Code Review Report

**Repository:** Heretek-AI/heretek-swarm
**Branch:** `main`
**Commit:** 6266fed...e7f886f
**Run:** [https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/f89e19aa-1d2a-415f-9a2f-154b611e2148/](https://app.deepsource.com/gh/Heretek-AI/heretek-swarm/run/f89e19aa-1d2a-415f-9a2f-154b611e2148/)

---

## Summary
- **SQL:** No issues detected- **Docker:** No issues detected- **Shell:** No issues detected- **Secrets:** No issues detected- **Python:** 11 issues- **JavaScript:** No issues detected

---

## Code Review Findings
### SQL
**Status:** Success
**Findings:** No new issues detected
### Docker
**Status:** Success
**Findings:** No new issues detected
### Shell
**Status:** Success
**Findings:** No new issues detected
### Secrets
**Status:** Success
**Findings:** No new issues detected
### Python
**Status:** Failure
**Findings:** 11 new issues

1. **Function is missing a return type annotation** (`TYP-051`)
   **File:** `fix_antipatterns_v2.py`
   **Line:** 443
   ```python
   return False
   
   
   def main():
       """Main function."""
       script_dir = Path(__file__).parent
       files = find_py_files(script_dir)
   ```
   **Category:** Type check
   **Severity:** minor

2. **`fix_unused_imports` has a cyclomatic complexity of 23 with "high" risk** (`PY-R1000`)
   **File:** `fix_antipatterns_v2.py`
   **Line:** 104
   ```python
   return content, count
   
   
   def fix_unused_imports(content: str) -> Tuple[str, int]:
       """Fix PY-W2000: Unused imports."""
       count = 0
       lines = content.split('\n')
   ```
   **Category:** Anti-pattern
   **Severity:** minor

3. **Function is missing a type annotation** (`TYP-051`)
   **File:** `fix_antipatterns_v2.py`
   **Line:** 207
   ```python
   count = 0
       
       # Pattern for function definitions
       def replace_func(_match):
           nonlocal count
           prefix = match.group(1)
           args = match.group(2)
   ```
   **Category:** Type check
   **Severity:** minor

4. **Consider merging collapsible if statements** (`PTC-W0048`)
   **File:** `fix_antipatterns_v2.py`
   **Line:** 38
   ```python
   files = []
       skip_dirs = {'.pytest_cache', 'node_modules', '__pycache__', '.git', '.venv', 'venv'}
       for d in root.rglob('*'):
           if d.is_file() and d.suffix == '.py':
               if not any(skip in d.parts for skip in skip_dirs):
                   files.append(d)
       return files
   ```
   **Category:** Anti-pattern
   **Severity:** major

5. **Undefined variable 'match'** (`PYL-E0602`)
   **File:** `fix_antipatterns_v2.py`
   **Line:** 209
   ```python
   # Pattern for function definitions
       def replace_func(_match):
           nonlocal count
           prefix = match.group(1)
           args = match.group(2)
           suffix = match.group(3)
   ```
   **Category:** Bug risk
   **Severity:** critical

6. **Undefined variable 'match'** (`PYL-E0602`)
   **File:** `fix_antipatterns_v2.py`
   **Line:** 211
   ```python
   nonlocal count
           prefix = match.group(1)
           args = match.group(2)
           suffix = match.group(3)
           
           # Parse arguments
           parsed_args = []
   ```
   **Category:** Bug risk
   **Severity:** critical

7. **Undefined variable 'match'** (`PYL-E0602`)
   **File:** `fix_antipatterns_v2.py`
   **Line:** 210
   ```python
   def replace_func(_match):
           nonlocal count
           prefix = match.group(1)
           args = match.group(2)
           suffix = match.group(3)
           
           # Parse arguments
   ```
   **Category:** Bug risk
   **Severity:** critical

8. **Function is missing a return type annotation** (`TYP-051`)
   **File:** `search_except.py`
   **Line:** 22
   ```python
   matches.append((i, line.rstrip()))
       return matches
   
   def main():
       if len(sys.argv) < 2:
           print("Usage: python search_except.py <file_path>")
           sys.exit(1)
   ```
   **Category:** Type check
   **Severity:** minor

9. **Function is missing a type annotation** (`TYP-051`)
   **File:** `search_except.py`
   **Line:** 7
   ```python
   import os
   import sys
   
   def search_file(_filepath):
       """Search for except patterns in a file."""
       try:
           with open(filepath, 'r', encoding='utf-8') as f:
   ```
   **Category:** Type check
   **Severity:** minor

10. **Undefined variable 'filepath'** (`PYL-E0602`)
    **File:** `search_except.py`
    **Line:** 13
    ```python
    with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return []
        
        matches = []
    ```
    **Category:** Bug risk
    **Severity:** critical

11. **Undefined variable 'filepath'** (`PYL-E0602`)
    **File:** `search_except.py`
    **Line:** 10
    ```python
    def search_file(_filepath):
        """Search for except patterns in a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
    ```
    **Category:** Bug risk
    **Severity:** critical
### JavaScript
**Status:** Success
**Findings:** No new issues detected

