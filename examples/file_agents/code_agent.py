"""Code file processing agent."""

import ast
import re
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Part, TextPart
from a2a.utils import new_agent_text_message
from typing_extensions import override
from pathlib import Path
from typing import Dict, List, Any


class CodeProcessorExecutor(AgentExecutor):
    """Specialized agent for code file processing."""
    
    def __init__(self):
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
        self.supported_languages = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.go': 'Go',
            '.rs': 'Rust'
        }
    
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        message_content = ""
        for part in context.message.parts:
            if isinstance(part, Part) and isinstance(part.root, TextPart):
                message_content = part.root.text
                break
        
        try:
            if message_content.startswith("PROCESS_CODE:"):
                await self._process_code_file(message_content, event_queue)
            elif message_content.startswith("ANALYZE_CODE:"):
                await self._analyze_code_structure(message_content, event_queue)
            elif message_content.startswith("LINT_CODE:"):
                await self._lint_code_file(message_content, event_queue)
            elif message_content.startswith("CREATE_CODE:"):
                await self._create_code_file(message_content, event_queue)
            elif message_content.startswith("EXTRACT_CODE:"):
                await self._extract_code_elements(message_content, event_queue)
            else:
                await self._show_code_help(event_queue)
        except Exception as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ Code processing error: {str(e)}")
            )
    
    async def _process_code_file(self, command: str, event_queue: EventQueue):
        """Process and analyze code file."""
        filename = command.replace("PROCESS_CODE:", "").strip()
        file_path = self.upload_dir / filename
        
        if not file_path.exists():
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ Code file not found: {filename}")
            )
            return
        
        content = file_path.read_text(encoding='utf-8')
        extension = file_path.suffix.lower()
        language = self.supported_languages.get(extension, 'Unknown')
        
        # Basic code analysis
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        # Comment analysis
        comment_patterns = {
            '.py': [r'#.*', r'""".*?"""', r"'''.*?'''"],
            '.js': [r'//.*', r'/\*.*?\*/'],
            '.java': [r'//.*', r'/\*.*?\*/'],
            '.cpp': [r'//.*', r'/\*.*?\*/'],
            '.c': [r'//.*', r'/\*.*?\*/']
        }
        
        comment_lines = 0
        if extension in comment_patterns:
            for pattern in comment_patterns[extension]:
                comment_lines += len(re.findall(pattern, content, re.DOTALL))
        
        # Function/method detection
        function_patterns = {
            '.py': r'def\s+(\w+)\s*\(',
            '.js': r'function\s+(\w+)\s*\(|(\w+)\s*=\s*\(',
            '.java': r'(public|private|protected)?\s*(static)?\s*\w+\s+(\w+)\s*\(',
            '.cpp': r'\w+\s+(\w+)\s*\(',
            '.c': r'\w+\s+(\w+)\s*\('
        }
        
        functions = []
        if extension in function_patterns:
            matches = re.findall(function_patterns[extension], content)
            functions = [match if isinstance(match, str) else [m for m in match if m][0] for match in matches]
        
        # Class detection (for OOP languages)
        class_patterns = {
            '.py': r'class\s+(\w+)',
            '.java': r'class\s+(\w+)',
            '.cpp': r'class\s+(\w+)',
            '.js': r'class\s+(\w+)'
        }
        
        classes = []
        if extension in class_patterns:
            classes = re.findall(class_patterns[extension], content)
        
        result = f"""
💻 Code File Analysis: {filename}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Basic Statistics:
   • Language: {language}
   • Total Lines: {len(lines)}
   • Non-empty Lines: {len(non_empty_lines)}
   • Comment Lines: {comment_lines}
   • Code Lines: {len(non_empty_lines) - comment_lines}
   • File Size: {len(content)} characters

🏗️ Structure:
   • Functions/Methods: {len(functions)}
   • Classes: {len(classes)}

📝 Functions Found:
{chr(10).join([f"   • {func}" for func in functions[:10]])}
{'   • ...' if len(functions) > 10 else ''}

🎯 Classes Found:
{chr(10).join([f"   • {cls}" for cls in classes[:5]])}
{'   • ...' if len(classes) > 5 else ''}

📝 Code Preview (first 10 lines):
{chr(10).join([f"{i+1:2d}: {line}" for i, line in enumerate(lines[:10])])}

✅ Code analysis complete!
        """
        
        await event_queue.enqueue_event(new_agent_text_message(result))
    
    async def _analyze_code_structure(self, command: str, event_queue: EventQueue):
        """Analyze code structure and complexity."""
        filename = command.replace("ANALYZE_CODE:", "").strip()
        file_path = self.upload_dir / filename
        
        if not file_path.exists():
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ Code file not found: {filename}")
            )
            return
        
        content = file_path.read_text(encoding='utf-8')
        extension = file_path.suffix.lower()
        
        # Complexity analysis
        complexity_indicators = {
            'if_statements': len(re.findall(r'\bif\b', content)),
            'loops': len(re.findall(r'\b(for|while)\b', content)),
            'try_catch': len(re.findall(r'\b(try|catch|except)\b', content)),
            'nested_blocks': content.count('{') + content.count(':') if extension in ['.py'] else content.count('{')
        }
        
        # Calculate cyclomatic complexity (simplified)
        decision_points = complexity_indicators['if_statements'] + complexity_indicators['loops']
        cyclomatic_complexity = decision_points + 1
        
        # Code quality indicators
        long_lines = len([line for line in content.split('\n') if len(line) > 80])
        deep_nesting = max([line.count('    ') for line in content.split('\n')] + [0])
        
        # Import/dependency analysis
        import_patterns = {
            '.py': r'(?:from\s+\S+\s+)?import\s+(\S+)',
            '.js': r'(?:import|require)\s*\(?[\'"]([^\'"]+)[\'"]',
            '.java': r'import\s+([^;]+);'
        }
        
        imports = []
        if extension in import_patterns:
            imports = re.findall(import_patterns[extension], content)
        
        result = f"""
🔍 Code Structure Analysis: {filename}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Complexity Metrics:
   • Cyclomatic Complexity: {cyclomatic_complexity}
   • If Statements: {complexity_indicators['if_statements']}
   • Loops: {complexity_indicators['loops']}
   • Try/Catch Blocks: {complexity_indicators['try_catch']}
   • Nested Blocks: {complexity_indicators['nested_blocks']}

📏 Code Quality:
   • Lines > 80 chars: {long_lines}
   • Max Nesting Depth: {deep_nesting}
   • Complexity Rating: {'Low' if cyclomatic_complexity < 10 else 'Medium' if cyclomatic_complexity < 20 else 'High'}

📦 Dependencies:
   • Imports/Requires: {len(imports)}
{chr(10).join([f"   • {imp}" for imp in imports[:10]])}
{'   • ...' if len(imports) > 10 else ''}

💡 Recommendations:
{self._get_code_recommendations(cyclomatic_complexity, long_lines, deep_nesting)}

✅ Structure analysis complete!
        """
        
        await event_queue.enqueue_event(new_agent_text_message(result))
    
    def _get_code_recommendations(self, complexity: int, long_lines: int, nesting: int) -> str:
        """Generate code improvement recommendations."""
        recommendations = []
        
        if complexity > 15:
            recommendations.append("   • Consider breaking down complex functions")
        if long_lines > 5:
            recommendations.append("   • Consider shortening long lines for readability")
        if nesting > 4:
            recommendations.append("   • Reduce nesting depth for better maintainability")
        if not recommendations:
            recommendations.append("   • Code structure looks good!")
        
        return chr(10).join(recommendations)
    
    async def _lint_code_file(self, command: str, event_queue: EventQueue):
        """Perform basic linting on code file."""
        filename = command.replace("LINT_CODE:", "").strip()
        file_path = self.upload_dir / filename
        
        if not file_path.exists():
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ Code file not found: {filename}")
            )
            return
        
        content = file_path.read_text(encoding='utf-8')
        extension = file_path.suffix.lower()
        lines = content.split('\n')
        
        issues = []
        warnings = []
        
        # Common linting checks
        for i, line in enumerate(lines, 1):
            # Long lines
            if len(line) > 100:
                warnings.append(f"Line {i}: Line too long ({len(line)} chars)")
            
            # Trailing whitespace
            if line.endswith(' ') or line.endswith('\t'):
                issues.append(f"Line {i}: Trailing whitespace")
            
            # Mixed tabs and spaces (Python specific)
            if extension == '.py' and '\t' in line and '    ' in line:
                issues.append(f"Line {i}: Mixed tabs and spaces")
        
        # Language-specific checks
        if extension == '.py':
            # Python-specific linting
            try:
                ast.parse(content)
            except SyntaxError as e:
                issues.append(f"Syntax Error: {e}")
            
            # Check for common Python issues
            if 'import *' in content:
                warnings.append("Wildcard imports found (not recommended)")
        
        # Unused variables (basic check)
        variable_pattern = r'(\w+)\s*='
        variables = re.findall(variable_pattern, content)
        for var in set(variables):
            if content.count(var) == 1:  # Only appears once (definition)
                warnings.append(f"Potentially unused variable: {var}")
        
        result = f"""
🔍 Code Linting Results: {filename}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Summary:
   • Issues: {len(issues)}
   • Warnings: {len(warnings)}
   • Status: {'✅ Clean' if not issues else '⚠️ Issues Found'}

{'❌ Issues:' + chr(10) + chr(10).join(issues) if issues else ''}

{'⚠️ Warnings:' + chr(10) + chr(10).join(warnings) if warnings else ''}

{'✅ No issues found!' if not issues and not warnings else ''}

✅ Linting complete!
        """
        
        await event_queue.enqueue_event(new_agent_text_message(result))
    
    async def _extract_code_elements(self, command: str, event_queue: EventQueue):
        """Extract specific code elements like functions, classes, etc."""
        parts = command.replace("EXTRACT_CODE:", "").split(":")
        if len(parts) < 2:
            await event_queue.enqueue_event(
                new_agent_text_message("❌ Usage: EXTRACT_CODE:filename:element_type (functions, classes, imports)")
            )
            return
        
        filename = parts[0].strip()
        element_type = parts[1].strip().lower()
        file_path = self.upload_dir / filename
        
        if not file_path.exists():
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ Code file not found: {filename}")
            )
            return
        
        content = file_path.read_text(encoding='utf-8')
        extension = file_path.suffix.lower()
        
        if element_type == "functions":
            if extension == '.py':
                # Extract Python functions with their signatures
                pattern = r'def\s+(\w+)\s*$$[^)]*$$:'
                matches = re.finditer(pattern, content)
                elements = []
                for match in matches:
                    start = match.start()
                    line_start = content.rfind('\n', 0, start) + 1
                    line_end = content.find('\n', match.end())
                    if line_end == -1:
                        line_end = len(content)
                    elements.append(content[line_start:line_end].strip())
            else:
                elements = ["Function extraction not implemented for this language"]
        
        elif element_type == "classes":
            if extension == '.py':
                pattern = r'class\s+(\w+)(?:$$[^)]*$$)?:'
                matches = re.finditer(pattern, content)
                elements = []
                for match in matches:
                    start = match.start()
                    line_start = content.rfind('\n', 0, start) + 1
                    line_end = content.find('\n', match.end())
                    if line_end == -1:
                        line_end = len(content)
                    elements.append(content[line_start:line_end].strip())
            else:
                elements = ["Class extraction not implemented for this language"]
        
        elif element_type == "imports":
            if extension == '.py':
                import_pattern = r'(?:from\s+\S+\s+)?import\s+[^\n]+'
                elements = re.findall(import_pattern, content)
            elif extension == '.js':
                import_pattern = r'(?:import|require)[^\n]+'
                elements = re.findall(import_pattern, content)
            else:
                elements = ["Import extraction not implemented for this language"]
        
        else:
            elements = [f"Unknown element type: {element_type}"]
        
        result = f"""
🔍 Code Element Extraction: {filename}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Element Type: {element_type.title()}
📊 Found: {len(elements)} items

📝 Extracted Elements:
{chr(10).join([f"   • {elem}" for elem in elements[:15]])}
{'   • ...' if len(elements) > 15 else ''}

✅ Extraction complete!
        """
        
        await event_queue.enqueue_event(new_agent_text_message(result))
    
    async def _create_code_file(self, command: str, event_queue: EventQueue):
        """Create sample code files."""
        parts = command.replace("CREATE_CODE:", "").split(":")
        filename = parts[0].strip()
        code_type = parts[1].strip() if len(parts) > 1 else "python"
        
        if code_type == "python":
            file_path = self.upload_dir / f"{filename}.py"
            content = '''#!/usr/bin/env python3
"""
Sample Python module for code analysis testing.
This module demonstrates various Python constructs.
"""

import os
import sys
from typing import List, Dict, Optional


class DataProcessor:
    """A sample class for data processing operations."""
    
    def __init__(self, name: str):
        self.name = name
        self.data: List[Dict] = []
    
    def add_data(self, item: Dict) -> None:
        """Add an item to the data collection."""
        if self._validate_item(item):
            self.data.append(item)
        else:
            raise ValueError("Invalid data item")
    
    def _validate_item(self, item: Dict) -> bool:
        """Validate a data item."""
        return isinstance(item, dict) and 'id' in item
    
    def process_data(self) -> Optional[List[Dict]]:
        """Process the collected data."""
        if not self.data:
            return None
        
        processed = []
        for item in self.data:
            try:
                # Complex processing logic
                if item.get('active', True):
                    processed_item = {
                        'id': item['id'],
                        'processed': True,
                        'timestamp': item.get('timestamp', 0)
                    }
                    processed.append(processed_item)
            except KeyError as e:
                print(f"Error processing item: {e}")
                continue
        
        return processed


def calculate_statistics(numbers: List[float]) -> Dict[str, float]:
    """Calculate basic statistics for a list of numbers."""
    if not numbers:
        return {}
    
    total = sum(numbers)
    count = len(numbers)
    mean = total / count
    
    # Calculate variance
    variance = sum((x - mean) ** 2 for x in numbers) / count
    std_dev = variance ** 0.5
    
    return {
        'count': count,
        'sum': total,
        'mean': mean,
        'variance': variance,
        'std_dev': std_dev,
        'min': min(numbers),
        'max': max(numbers)
    }


def main():
    """Main function to demonstrate the module."""
    processor = DataProcessor("Sample Processor")
    
    # Add sample data
    sample_data = [
        {'id': 1, 'value': 10, 'active': True},
        {'id': 2, 'value': 20, 'active': False},
        {'id': 3, 'value': 30, 'active': True}
    ]
    
    for item in sample_data:
        processor.add_data(item)
    
    # Process data
    result = processor.process_data()
    print(f"Processed {len(result)} items")
    
    # Calculate statistics
    values = [item['value'] for item in sample_data]
    stats = calculate_statistics(values)
    print(f"Statistics: {stats}")


if __name__ == "__main__":
    main()
'''
        
        elif code_type == "javascript":
            file_path = self.upload_dir / f"{filename}.js"
            content = '''/**
 * Sample JavaScript module for code analysis testing.
 * This module demonstrates various JavaScript constructs.
 */

class DataProcessor {
    constructor(name) {
        this.name = name;
        this.data = [];
    }
    
    addData(item) {
        if (this.validateItem(item)) {
            this.data.push(item);
        } else {
            throw new Error('Invalid data item');
        }
    }
    
    validateItem(item) {
        return typeof item === 'object' && item !== null && 'id' in item;
    }
    
    processData() {
        if (this.data.length === 0) {
            return null;
        }
        
        const processed = [];
        
        for (const item of this.data) {
            try {
                if (item.active !== false) {
                    const processedItem = {
                        id: item.id,
                        processed: true,
                        timestamp: item.timestamp || Date.now()
                    };
                    processed.push(processedItem);
                }
            } catch (error) {
                console.error(`Error processing item: ${error.message}`);
                continue;
            }
        }
        
        return processed;
    }
}

function calculateStatistics(numbers) {
    if (!Array.isArray(numbers) || numbers.length === 0) {
        return {};
    }
    
    const total = numbers.reduce((sum, num) => sum + num, 0);
    const count = numbers.length;
    const mean = total / count;
    
    const variance = numbers.reduce((sum, num) => sum + Math.pow(num - mean, 2), 0) / count;
    const stdDev = Math.sqrt(variance);
    
    return {
        count: count,
        sum: total,
        mean: mean,
        variance: variance,
        stdDev: stdDev,
        min: Math.min(...numbers),
        max: Math.max(...numbers)
    };
}

function main() {
    const processor = new DataProcessor('Sample Processor');
    
    const sampleData = [
        { id: 1, value: 10, active: true },
        { id: 2, value: 20, active: false },
        { id: 3, value: 30, active: true }
    ];
    
    sampleData.forEach(item => processor.addData(item));
    
    const result = processor.processData();
    console.log(`Processed ${result.length} items`);
    
    const values = sampleData.map(item => item.value);
    const stats = calculateStatistics(values);
    console.log('Statistics:', stats);
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DataProcessor, calculateStatistics };
}

// Run main if this is the entry point
if (require.main === module) {
    main();
}
'''
        
        else:  # Default to simple Python
            file_path = self.upload_dir / f"{filename}.py"
            content = '''def hello_world():
    """A simple hello world function."""
    print("Hello, World!")
    return "Hello from Python!"

def add_numbers(a, b):
    """Add two numbers together."""
    return a + b

def main():
    """Main function."""
    result = hello_world()
    print(f"Result: {result}")
    
    sum_result = add_numbers(5, 3)
    print(f"5 + 3 = {sum_result}")

if __name__ == "__main__":
    main()
'''
        
        file_path.write_text(content)
        await event_queue.enqueue_event(
            new_agent_text_message(f"✅ Created code file: {file_path.name}")
        )
    
    async def _show_code_help(self, event_queue: EventQueue):
        """Show code processing help."""
        help_text = """
💻 Code Processing Agent Help
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 Available Commands:
   • PROCESS_CODE:filename - Analyze code structure
   • ANALYZE_CODE:filename - Complexity analysis
   • LINT_CODE:filename - Basic code linting
   • EXTRACT_CODE:filename:type - Extract elements (functions, classes, imports)
   • CREATE_CODE:name:type - Create sample code (python, javascript)

📊 Analysis Features:
   • Function and class detection
   • Complexity metrics
   • Code quality assessment
   • Import/dependency analysis
   • Basic linting checks

💡 Examples:
   • CREATE_CODE:sample:python
   • PROCESS_CODE:sample.py
   • ANALYZE_CODE:sample.py
   • LINT_CODE:sample.py
   • EXTRACT_CODE:sample.py:functions

🎯 Supported: .py, .js, .ts, .java, .cpp, .c, .go, .rs
        """
        
        await event_queue.enqueue_event(new_agent_text_message(help_text))
    
    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(new_agent_text_message("Code processing cancelled."))
