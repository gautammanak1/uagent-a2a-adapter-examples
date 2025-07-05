"""Text file processing agent."""

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Part, TextPart
from a2a.utils import new_agent_text_message
from typing_extensions import override
from pathlib import Path
import re


class TextProcessorExecutor(AgentExecutor):
    """Specialized agent for text file processing."""
    
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
            if message_content.startswith("PROCESS_TEXT:"):
                await self._process_text_file(message_content, event_queue)
            elif message_content.startswith("ANALYZE_TEXT:"):
                await self._analyze_text_content(message_content, event_queue)
            elif message_content.startswith("SEARCH_TEXT:"):
                await self._search_in_text(message_content, event_queue)
            elif message_content.startswith("CREATE_TEXT:"):
                await self._create_text_file(message_content, event_queue)
            else:
                await self._show_text_help(event_queue)
        except Exception as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ Text processing error: {str(e)}")
            )
    
    async def _process_text_file(self, command: str, event_queue: EventQueue):
        """Process a text file with advanced analysis."""
        filename = command.replace("PROCESS_TEXT:", "").strip()
        file_path = self.upload_dir / filename
        
        if not file_path.exists():
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ Text file not found: {filename}")
            )
            return
        
        content = file_path.read_text(encoding='utf-8')
        
        # Advanced text analysis
        lines = content.split('\n')
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # Word frequency analysis
        word_freq = {}
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if clean_word:
                word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
        
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Reading time estimation (average 200 words per minute)
        reading_time = len(words) / 200
        
        result = f"""
📄 Advanced Text Analysis: {filename}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Statistics:
   • Lines: {len(lines)}
   • Words: {len(words)}
   • Sentences: {len([s for s in sentences if s.strip()])}
   • Paragraphs: {len(paragraphs)}
   • Characters: {len(content)}
   • Reading Time: {reading_time:.1f} minutes

🔤 Top Words:
{chr(10).join([f"   • {word}: {count}" for word, count in top_words])}

📝 Content Preview:
{content[:300]}{'...' if len(content) > 300 else ''}

✅ Text analysis complete!
        """
        
        await event_queue.enqueue_event(new_agent_text_message(result))
    
    async def _analyze_text_content(self, command: str, event_queue: EventQueue):
        """Analyze text content for readability and structure."""
        filename = command.replace("ANALYZE_TEXT:", "").strip()
        file_path = self.upload_dir / filename
        
        if not file_path.exists():
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ Text file not found: {filename}")
            )
            return
        
        content = file_path.read_text(encoding='utf-8')
        
        # Readability analysis
        sentences = re.split(r'[.!?]+', content)
        words = content.split()
        
        avg_sentence_length = len(words) / max(len([s for s in sentences if s.strip()]), 1)
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)
        
        # Text complexity indicators
        long_words = [w for w in words if len(w) > 6]
        complexity_score = len(long_words) / max(len(words), 1) * 100
        
        result = f"""
🔍 Text Content Analysis: {filename}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Readability Metrics:
   • Average Sentence Length: {avg_sentence_length:.1f} words
   • Average Word Length: {avg_word_length:.1f} characters
   • Complex Words (>6 chars): {len(long_words)} ({complexity_score:.1f}%)
   • Readability: {'Easy' if complexity_score < 20 else 'Medium' if complexity_score < 40 else 'Complex'}

📋 Structure Analysis:
   • Estimated Grade Level: {min(12, max(1, int(avg_sentence_length / 2 + complexity_score / 10)))}
   • Text Density: {'Dense' if avg_sentence_length > 20 else 'Moderate' if avg_sentence_length > 15 else 'Light'}

✅ Content analysis complete!
        """
        
        await event_queue.enqueue_event(new_agent_text_message(result))
    
    async def _search_in_text(self, command: str, event_queue: EventQueue):
        """Search for patterns in text files."""
        parts = command.replace("SEARCH_TEXT:", "").split(":")
        if len(parts) < 2:
            await event_queue.enqueue_event(
                new_agent_text_message("❌ Usage: SEARCH_TEXT:filename:search_term")
            )
            return
        
        filename = parts[0].strip()
        search_term = parts[1].strip()
        file_path = self.upload_dir / filename
        
        if not file_path.exists():
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ Text file not found: {filename}")
            )
            return
        
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        # Search for term
        matches = []
        for i, line in enumerate(lines, 1):
            if search_term.lower() in line.lower():
                matches.append((i, line.strip()))
        
        if matches:
            result = f"""
🔍 Search Results in {filename}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Found {len(matches)} matches for "{search_term}":

{chr(10).join([f"Line {line_num}: {line}" for line_num, line in matches[:10]])}
{'...' if len(matches) > 10 else ''}

✅ Search complete!
            """
        else:
            result = f"🔍 No matches found for '{search_term}' in {filename}"
        
        await event_queue.enqueue_event(new_agent_text_message(result))
    
    async def _create_text_file(self, command: str, event_queue: EventQueue):
        """Create a sample text file."""
        parts = command.replace("CREATE_TEXT:", "").split(":")
        filename = parts[0].strip()
        content_type = parts[1].strip() if len(parts) > 1 else "sample"
        
        file_path = self.upload_dir / f"{filename}.txt"
        
        if content_type == "lorem":
            content = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo."""
        
        elif content_type == "story":
            content = """The Digital Frontier

In the year 2045, artificial intelligence had become as common as smartphones once were. Sarah, a data analyst, worked alongside her AI companion, ARIA, to solve complex problems that would have taken humans months to unravel.

"ARIA, can you analyze the pattern in these customer complaints?" Sarah asked, uploading a dataset of thousands of entries.

"Certainly, Sarah. I've identified three primary clusters of issues. The most significant relates to delivery delays, affecting 34% of complaints. Shall I generate a detailed report?"

As Sarah reviewed ARIA's analysis, she marveled at how technology had evolved. What once seemed like science fiction was now her daily reality. The partnership between human intuition and artificial intelligence had opened doors to possibilities she never imagined.

The future was here, and it was collaborative."""
        
        else:  # sample
            content = f"""Sample Text Document
Created by Text Processing Agent

This is a sample text file for testing various text processing capabilities.

Key Features:
- Multiple paragraphs for structure analysis
- Various sentence lengths for readability testing
- Different word complexities for vocabulary analysis
- Searchable content for pattern matching

Technical Details:
- File format: Plain text (.txt)
- Encoding: UTF-8
- Purpose: Demonstration and testing
- Agent: Text Processing Specialist

You can use this file to test commands like:
- PROCESS_TEXT:{filename}.txt
- ANALYZE_TEXT:{filename}.txt  
- SEARCH_TEXT:{filename}.txt:sample
"""
        
        file_path.write_text(content)
        await event_queue.enqueue_event(
            new_agent_text_message(f"✅ Created text file: {file_path.name}")
        )
    
    async def _show_text_help(self, event_queue: EventQueue):
        """Show text processing help."""
        help_text = """
📄 Text Processing Agent Help
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 Available Commands:
   • PROCESS_TEXT:filename.txt - Advanced text analysis
   • ANALYZE_TEXT:filename.txt - Readability analysis  
   • SEARCH_TEXT:filename.txt:term - Search for text patterns
   • CREATE_TEXT:name:type - Create sample text (types: sample, lorem, story)

📊 Analysis Features:
   • Word frequency analysis
   • Readability metrics
   • Structure analysis
   • Reading time estimation
   • Pattern searching

💡 Examples:
   • CREATE_TEXT:sample:story
   • PROCESS_TEXT:sample.txt
   • SEARCH_TEXT:sample.txt:artificial
   • ANALYZE_TEXT:sample.txt

🎯 Specialized for .txt, .md files
        """
        
        await event_queue.enqueue_event(new_agent_text_message(help_text))
    
    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(new_agent_text_message("Text processing cancelled."))
