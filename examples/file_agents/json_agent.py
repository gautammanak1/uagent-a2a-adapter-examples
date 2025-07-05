"""JSON file processing agent."""

import json
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Part, TextPart
from a2a.utils import new_agent_text_message
from typing_extensions import override
from pathlib import Path
from typing import Any, Dict, List


class JSONProcessorExecutor(AgentExecutor):
    """Specialized agent for JSON file processing."""
    
    def __init__(self):
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
    
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        message_content = ""
        for part in context.message.parts:
            if isinstance(part, Part) and isinstance(part.root, TextPart):
                message_content = part.root.text
                break
        
        try:
            if message_content.startswith("PROCESS_JSON:"):
                await self._process_json_file(message_content, event_queue)
            elif message_content.startswith("VALIDATE_JSON:"):
                await self._validate_json_file(message_content, event_queue)
            elif message_content.startswith("QUERY_JSON:"):
                await self._query_json_data(message_content, event_queue)
            elif message_content.startswith("CREATE_JSON:"):
                await self._create_json_file(message_content, event_queue)
            elif message_content.startswith("TRANSFORM_JSON:"):
                await self._transform_json_data(message_content, event_queue)
            else:
                await self._show_json_help(event_queue)
        except Exception as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ JSON processing error: {str(e)}")
            )
    
    async def _process_json_file(self, command: str, event_queue: EventQueue):
        """Process and analyze JSON file structure."""
        filename = command.replace("PROCESS_JSON:", "").strip()
        file_path = self.upload_dir / filename
        
        if not file_path.exists():
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ JSON file not found: {filename}")
            )
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Analyze JSON structure
            analysis = self._analyze_json_structure(data)
            
            result = f"""
📋 JSON File Analysis: {filename}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 Structure Analysis:
{analysis['structure']}

📊 Statistics:
   • Total Keys: {analysis['total_keys']}
   • Max Depth: {analysis['max_depth']}
   • Arrays Found: {analysis['arrays']}
   • Objects Found: {analysis['objects']}
   • Data Types: {', '.join(analysis['data_types'])}

📝 Content Preview:
{json.dumps(data, indent=2)[:400]}{'...' if len(str(data)) > 400 else ''}

✅ JSON analysis complete!
            """
            
            await event_queue.enqueue_event(new_agent_text_message(result))
            
        except json.JSONDecodeError as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ Invalid JSON file: {str(e)}")
            )
    
    def _analyze_json_structure(self, data: Any, depth: int = 0) -> Dict[str, Any]:
        """Analyze JSON structure recursively."""
        analysis = {
            'structure': '',
            'total_keys': 0,
            'max_depth': depth,
            'arrays': 0,
            'objects': 0,
            'data_types': set()
        }
        
        if isinstance(data, dict):
            analysis['objects'] += 1
            analysis['total_keys'] += len(data)
            analysis['structure'] = f"Object with {len(data)} keys"
            analysis['data_types'].add('object')
            
            for key, value in data.items():
                sub_analysis = self._analyze_json_structure(value, depth + 1)
                analysis['max_depth'] = max(analysis['max_depth'], sub_analysis['max_depth'])
                analysis['arrays'] += sub_analysis['arrays']
                analysis['objects'] += sub_analysis['objects']
                analysis['total_keys'] += sub_analysis['total_keys']
                analysis['data_types'].update(sub_analysis['data_types'])
        
        elif isinstance(data, list):
            analysis['arrays'] += 1
            analysis['structure'] = f"Array with {len(data)} items"
            analysis['data_types'].add('array')
            
            for item in data:
                sub_analysis = self._analyze_json_structure(item, depth + 1)
                analysis['max_depth'] = max(analysis['max_depth'], sub_analysis['max_depth'])
                analysis['arrays'] += sub_analysis['arrays']
                analysis['objects'] += sub_analysis['objects']
                analysis['total_keys'] += sub_analysis['total_keys']
                analysis['data_types'].update(sub_analysis['data_types'])
        
        else:
            analysis['data_types'].add(type(data).__name__)
            analysis['structure'] = f"{type(data).__name__}: {str(data)[:50]}"
        
        return analysis
    
    async def _validate_json_file(self, command: str, event_queue: EventQueue):
        """Validate JSON file and check for common issues."""
        filename = command.replace("VALIDATE_JSON:", "").strip()
        file_path = self.upload_dir / filename
        
        if not file_path.exists():
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ JSON file not found: {filename}")
            )
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                data = json.loads(content)
            
            # Validation checks
            issues = []
            warnings = []
            
            # Check for common issues
            if ',' in content and content.rstrip().endswith(','):
                warnings.append("Trailing comma detected (may cause issues in some parsers)")
            
            # Check for duplicate keys (basic check)
            if isinstance(data, dict):
                key_count = len(str(data).split('"'))
                unique_keys = len(set(data.keys()))
                if key_count != unique_keys * 2 + 1:  # Rough estimate
                    warnings.append("Possible duplicate keys detected")
            
            # File size check
            file_size = file_path.stat().st_size
            if file_size > 1024 * 1024:  # 1MB
                warnings.append(f"Large file size: {file_size / 1024 / 1024:.1f}MB")
            
            result = f"""
✅ JSON Validation: {filename}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Validation Status: {'✅ VALID' if not issues else '❌ INVALID'}

{'📋 Issues Found:' + chr(10) + chr(10).join([f'   • {issue}' for issue in issues]) if issues else ''}

{'⚠️ Warnings:' + chr(10) + chr(10).join([f'   • {warning}' for warning in warnings]) if warnings else ''}

📊 File Info:
   • Size: {file_size} bytes
   • Valid JSON: ✅
   • Parseable: ✅

✅ Validation complete!
            """
            
            await event_queue.enqueue_event(new_agent_text_message(result))
            
        except json.JSONDecodeError as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"""
❌ JSON Validation Failed: {filename}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚫 Error: {str(e)}
📍 Line: {getattr(e, 'lineno', 'Unknown')}
📍 Column: {getattr(e, 'colno', 'Unknown')}

💡 Common fixes:
   • Check for missing quotes around strings
   • Ensure proper comma placement
   • Verify bracket/brace matching
   • Remove trailing commas
                """)
            )
    
    async def _query_json_data(self, command: str, event_queue: EventQueue):
        """Query JSON data using simple path notation."""
        parts = command.replace("QUERY_JSON:", "").split(":")
        if len(parts) < 2:
            await event_queue.enqueue_event(
                new_agent_text_message("❌ Usage: QUERY_JSON:filename.json:path.to.key")
            )
            return
        
        filename = parts[0].strip()
        query_path = parts[1].strip()
        file_path = self.upload_dir / filename
        
        if not file_path.exists():
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ JSON file not found: {filename}")
            )
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Simple path traversal
            result_data = data
            path_parts = query_path.split('.')
            
            for part in path_parts:
                if isinstance(result_data, dict) and part in result_data:
                    result_data = result_data[part]
                elif isinstance(result_data, list) and part.isdigit():
                    index = int(part)
                    if 0 <= index < len(result_data):
                        result_data = result_data[index]
                    else:
                        raise KeyError(f"Index {index} out of range")
                else:
                    raise KeyError(f"Path '{part}' not found")
            
            result = f"""
🔍 JSON Query Result: {filename}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Query Path: {query_path}
📊 Result Type: {type(result_data).__name__}

📝 Result:
{json.dumps(result_data, indent=2)[:500]}{'...' if len(str(result_data)) > 500 else ''}

✅ Query complete!
            """
            
            await event_queue.enqueue_event(new_agent_text_message(result))
            
        except (json.JSONDecodeError, KeyError) as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ Query failed: {str(e)}")
            )
    
    async def _create_json_file(self, command: str, event_queue: EventQueue):
        """Create sample JSON files."""
        parts = command.replace("CREATE_JSON:", "").split(":")
        filename = parts[0].strip()
        json_type = parts[1].strip() if len(parts) > 1 else "sample"
        
        file_path = self.upload_dir / f"{filename}.json"
        
        if json_type == "users":
            data = {
                "users": [
                    {
                        "id": 1,
                        "name": "Alice Johnson",
                        "email": "alice@example.com",
                        "age": 30,
                        "active": True,
                        "roles": ["admin", "user"]
                    },
                    {
                        "id": 2,
                        "name": "Bob Smith",
                        "email": "bob@example.com", 
                        "age": 25,
                        "active": False,
                        "roles": ["user"]
                    }
                ],
                "total": 2,
                "page": 1
            }
        
        elif json_type == "config":
            data = {
                "application": {
                    "name": "Sample App",
                    "version": "1.0.0",
                    "debug": False
                },
                "database": {
                    "host": "localhost",
                    "port": 5432,
                    "name": "sample_db",
                    "ssl": True
                },
                "features": {
                    "authentication": True,
                    "logging": True,
                    "caching": False
                }
            }
        
        else:  # sample
            data = {
                "name": "Sample JSON Data",
                "version": "1.0",
                "created": "2024-01-01T00:00:00Z",
                "items": [
                    {"id": 1, "name": "Item 1", "value": 100, "active": True},
                    {"id": 2, "name": "Item 2", "value": 200, "active": False}
                ],
                "metadata": {
                    "author": "JSON Processing Agent",
                    "description": "Sample data for testing JSON operations",
                    "tags": ["sample", "test", "json"]
                }
            }
        
        file_path.write_text(json.dumps(data, indent=2))
        await event_queue.enqueue_event(
            new_agent_text_message(f"✅ Created JSON file: {file_path.name}")
        )
    
    async def _transform_json_data(self, command: str, event_queue: EventQueue):
        """Transform JSON data (basic operations)."""
        parts = command.replace("TRANSFORM_JSON:", "").split(":")
        if len(parts) < 2:
            await event_queue.enqueue_event(
                new_agent_text_message("❌ Usage: TRANSFORM_JSON:filename.json:operation")
            )
            return
        
        filename = parts[0].strip()
        operation = parts[1].strip()
        file_path = self.upload_dir / filename
        
        if not file_path.exists():
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ JSON file not found: {filename}")
            )
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if operation == "minify":
                # Create minified version
                minified_path = self.upload_dir / f"{filename.replace('.json', '')}_minified.json"
                minified_path.write_text(json.dumps(data, separators=(',', ':')))
                result = f"✅ Created minified version: {minified_path.name}"
            
            elif operation == "pretty":
                # Create pretty-printed version
                pretty_path = self.upload_dir / f"{filename.replace('.json', '')}_pretty.json"
                pretty_path.write_text(json.dumps(data, indent=4, sort_keys=True))
                result = f"✅ Created pretty-printed version: {pretty_path.name}"
            
            elif operation == "keys":
                # Extract all keys
                keys = self._extract_all_keys(data)
                result = f"🔑 All keys found: {', '.join(sorted(keys))}"
            
            else:
                result = f"❌ Unknown operation: {operation}. Available: minify, pretty, keys"
            
            await event_queue.enqueue_event(new_agent_text_message(result))
            
        except json.JSONDecodeError as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ Transform failed: {str(e)}")
            )
    
    def _extract_all_keys(self, data: Any, keys: set = None) -> set:
        """Extract all keys from nested JSON structure."""
        if keys is None:
            keys = set()
        
        if isinstance(data, dict):
            keys.update(data.keys())
            for value in data.values():
                self._extract_all_keys(value, keys)
        elif isinstance(data, list):
            for item in data:
                self._extract_all_keys(item, keys)
        
        return keys
    
    async def _show_json_help(self, event_queue: EventQueue):
        """Show JSON processing help."""
        help_text = """
📋 JSON Processing Agent Help
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 Available Commands:
   • PROCESS_JSON:filename.json - Analyze JSON structure
   • VALIDATE_JSON:filename.json - Validate JSON syntax
   • QUERY_JSON:filename.json:path - Query JSON data
   • CREATE_JSON:name:type - Create sample JSON (types: sample, users, config)
   • TRANSFORM_JSON:filename.json:operation - Transform JSON (minify, pretty, keys)

📊 Analysis Features:
   • Structure analysis and statistics
   • Validation with error reporting
   • Path-based data querying
   • Data transformation utilities

💡 Examples:
   • CREATE_JSON:users:users
   • PROCESS_JSON:users.json
   • QUERY_JSON:users.json:users.0.name
   • VALIDATE_JSON:users.json
   • TRANSFORM_JSON:users.json:pretty

🎯 Specialized for .json files
        """
        
        await event_queue.enqueue_event(new_agent_text_message(help_text))
    
    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(new_agent_text_message("JSON processing cancelled."))
