"""CSV file processing agent."""

import csv
import io
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Part, TextPart
from a2a.utils import new_agent_text_message
from typing_extensions import override
from pathlib import Path
from typing import List, Dict, Any
import statistics


class CSVProcessorExecutor(AgentExecutor):
    """Specialized agent for CSV file processing."""
    
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
            if message_content.startswith("PROCESS_CSV:"):
                await self._process_csv_file(message_content, event_queue)
            elif message_content.startswith("ANALYZE_CSV:"):
                await self._analyze_csv_data(message_content, event_queue)
            elif message_content.startswith("QUERY_CSV:"):
                await self._query_csv_data(message_content, event_queue)
            elif message_content.startswith("CREATE_CSV:"):
                await self._create_csv_file(message_content, event_queue)
            elif message_content.startswith("STATS_CSV:"):
                await self._calculate_csv_stats(message_content, event_queue)
            else:
                await self._show_csv_help(event_queue)
        except Exception as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ CSV processing error: {str(e)}")
            )
    
    async def _process_csv_file(self, command: str, event_queue: EventQueue):
        """Process and analyze CSV file structure."""
        filename = command.replace("PROCESS_CSV:", "").strip()
        file_path = self.upload_dir / filename
        
        if not file_path.exists():
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ CSV file not found: {filename}")
            )
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Detect CSV dialect
                sample = f.read(1024)
                f.seek(0)
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)
                
                reader = csv.reader(f, dialect=dialect)
                rows = list(reader)
            
            if not rows:
                await event_queue.enqueue_event(
                    new_agent_text_message("❌ Empty CSV file")
                )
                return
            
            headers = rows[0] if rows else []
            data_rows = rows[1:] if len(rows) > 1 else []
            
            # Analyze data types for each column
            column_analysis = {}
            for i, header in enumerate(headers):
                column_data = [row[i] if i < len(row) else '' for row in data_rows]
                column_analysis[header] = self._analyze_column(column_data)
            
            result = f"""
📊 CSV File Analysis: {filename}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Basic Statistics:
   • Total Rows: {len(rows)}
   • Data Rows: {len(data_rows)}
   • Columns: {len(headers)}
   • Delimiter: '{dialect.delimiter}'
   • Quote Character: '{dialect.quotechar}'

🏷️ Column Analysis:
{chr(10).join([f"   • {col}: {info['type']} ({info['non_empty']}/{len(data_rows)} non-empty)" for col, info in column_analysis.items()])}

📝 Sample Data (first 3 rows):
{chr(10).join([str(row) for row in data_rows[:3]])}

✅ CSV analysis complete!
            """
            
            await event_queue.enqueue_event(new_agent_text_message(result))
            
        except Exception as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ Error processing CSV: {str(e)}")
            )
    
    def _analyze_column(self, column_data: List[str]) -> Dict[str, Any]:
        """Analyze a single column's data type and characteristics."""
        non_empty = [val for val in column_data if val.strip()]
        
        if not non_empty:
            return {'type': 'empty', 'non_empty': 0}
        
        # Try to determine data type
        numeric_count = 0
        date_like_count = 0
        
        for val in non_empty:
            # Check if numeric
            try:
                float(val)
                numeric_count += 1
            except ValueError:
                pass
            
            # Check if date-like (basic check)
            if any(sep in val for sep in ['-', '/', '.']):
                parts = val.replace('-', '/').replace('.', '/').split('/')
                if len(parts) >= 2 and all(part.isdigit() for part in parts):
                    date_like_count += 1
        
        total = len(non_empty)
        if numeric_count > total * 0.8:
            data_type = 'numeric'
        elif date_like_count > total * 0.5:
            data_type = 'date-like'
        else:
            data_type = 'text'
        
        return {
            'type': data_type,
            'non_empty': len(non_empty),
            'unique_values': len(set(non_empty)),
            'sample_values': non_empty[:3]
        }
    
    async def _analyze_csv_data(self, command: str, event_queue: EventQueue):
        """Perform detailed data analysis on CSV."""
        filename = command.replace("ANALYZE_CSV:", "").strip()
        file_path = self.upload_dir / filename
        
        if not file_path.exists():
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ CSV file not found: {filename}")
            )
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if not rows:
                await event_queue.enqueue_event(
                    new_agent_text_message("❌ No data rows found")
                )
                return
            
            # Data quality analysis
            total_rows = len(rows)
            complete_rows = sum(1 for row in rows if all(val.strip() for val in row.values()))
            
            # Find duplicates
            row_strings = [str(sorted(row.items())) for row in rows]
            duplicates = len(row_strings) - len(set(row_strings))
            
            # Column completeness
            column_completeness = {}
            for col in rows[0].keys():
                non_empty = sum(1 for row in rows if row[col].strip())
                column_completeness[col] = (non_empty / total_rows) * 100
            
            result = f"""
🔍 CSV Data Analysis: {filename}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Data Quality:
   • Total Rows: {total_rows}
   • Complete Rows: {complete_rows} ({complete_rows/total_rows*100:.1f}%)
   • Duplicate Rows: {duplicates}
   • Data Completeness: {sum(column_completeness.values())/len(column_completeness):.1f}%

📈 Column Completeness:
{chr(10).join([f"   • {col}: {comp:.1f}%" for col, comp in column_completeness.items()])}

🎯 Data Quality Score: {((complete_rows/total_rows) * 0.5 + (1 - duplicates/total_rows) * 0.3 + (sum(column_completeness.values())/len(column_completeness)/100) * 0.2) * 100:.1f}%

✅ Analysis complete!
            """
            
            await event_queue.enqueue_event(new_agent_text_message(result))
            
        except Exception as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ Error analyzing CSV: {str(e)}")
            )
    
    async def _query_csv_data(self, command: str, event_queue: EventQueue):
        """Query CSV data with simple filtering."""
        parts = command.replace("QUERY_CSV:", "").split(":")
        if len(parts) < 3:
            await event_queue.enqueue_event(
                new_agent_text_message("❌ Usage: QUERY_CSV:filename.csv:column:value")
            )
            return
        
        filename = parts[0].strip()
        column = parts[1].strip()
        value = parts[2].strip()
        file_path = self.upload_dir / filename
        
        if not file_path.exists():
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ CSV file not found: {filename}")
            )
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if column not in rows[0].keys():
                await event_queue.enqueue_event(
                    new_agent_text_message(f"❌ Column '{column}' not found. Available: {', '.join(rows[0].keys())}")
                )
                return
            
            # Filter rows
            matching_rows = [row for row in rows if value.lower() in row[column].lower()]
            
            if matching_rows:
                result = f"""
🔍 CSV Query Results: {filename}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Query: {column} contains "{value}"
📊 Found: {len(matching_rows)} matches

📝 Results (first 5):
{chr(10).join([str(dict(row)) for row in matching_rows[:5]])}
{'...' if len(matching_rows) > 5 else ''}

✅ Query complete!
                """
            else:
                result = f"🔍 No matches found for '{value}' in column '{column}'"
            
            await event_queue.enqueue_event(new_agent_text_message(result))
            
        except Exception as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ Query failed: {str(e)}")
            )
    
    async def _calculate_csv_stats(self, command: str, event_queue: EventQueue):
        """Calculate statistics for numeric columns."""
        parts = command.replace("STATS_CSV:", "").split(":")
        filename = parts[0].strip()
        column = parts[1].strip() if len(parts) > 1 else None
        file_path = self.upload_dir / filename
        
        if not file_path.exists():
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ CSV file not found: {filename}")
            )
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if not rows:
                await event_queue.enqueue_event(
                    new_agent_text_message("❌ No data found")
                )
                return
            
            # Find numeric columns
            numeric_columns = []
            for col in rows[0].keys():
                values = [row[col] for row in rows if row[col].strip()]
                try:
                    [float(val) for val in values[:5]]  # Test first 5 values
                    numeric_columns.append(col)
                except ValueError:
                    continue
            
            if column and column not in numeric_columns:
                await event_queue.enqueue_event(
                    new_agent_text_message(f"❌ Column '{column}' is not numeric. Numeric columns: {', '.join(numeric_columns)}")
                )
                return
            
            # Calculate statistics
            stats_results = {}
            columns_to_analyze = [column] if column else numeric_columns
            
            for col in columns_to_analyze:
                values = []
                for row in rows:
                    if row[col].strip():
                        try:
                            values.append(float(row[col]))
                        except ValueError:
                            continue
                
                if values:
                    stats_results[col] = {
                        'count': len(values),
                        'mean': statistics.mean(values),
                        'median': statistics.median(values),
                        'min': min(values),
                        'max': max(values),
                        'std_dev': statistics.stdev(values) if len(values) > 1 else 0
                    }
            
            if stats_results:
                result = f"""
📊 CSV Statistics: {filename}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{chr(10).join([f"""
🔢 Column: {col}
   • Count: {stats['count']}
   • Mean: {stats['mean']:.2f}
   • Median: {stats['median']:.2f}
   • Min: {stats['min']:.2f}
   • Max: {stats['max']:.2f}
   • Std Dev: {stats['std_dev']:.2f}""" for col, stats in stats_results.items()])}

✅ Statistics complete!
                """
            else:
                result = "❌ No numeric data found for statistics"
            
            await event_queue.enqueue_event(new_agent_text_message(result))
            
        except Exception as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ Statistics calculation failed: {str(e)}")
            )
    
    async def _create_csv_file(self, command: str, event_queue: EventQueue):
        """Create sample CSV files."""
        parts = command.replace("CREATE_CSV:", "").split(":")
        filename = parts[0].strip()
        csv_type = parts[1].strip() if len(parts) > 1 else "sample"
        
        file_path = self.upload_dir / f"{filename}.csv"
        
        if csv_type == "sales":
            data = [
                ["Date", "Product", "Quantity", "Price", "Total"],
                ["2024-01-01", "Widget A", "10", "25.50", "255.00"],
                ["2024-01-02", "Widget B", "5", "45.00", "225.00"],
                ["2024-01-03", "Widget A", "8", "25.50", "204.00"],
                ["2024-01-04", "Widget C", "12", "15.75", "189.00"],
                ["2024-01-05", "Widget B", "3", "45.00", "135.00"]
            ]
        
        elif csv_type == "employees":
            data = [
                ["ID", "Name", "Department", "Salary", "Years", "Active"],
                ["1", "Alice Johnson", "Engineering", "75000", "3", "True"],
                ["2", "Bob Smith", "Marketing", "65000", "2", "True"],
                ["3", "Carol Davis", "Engineering", "80000", "5", "False"],
                ["4", "David Wilson", "Sales", "70000", "1", "True"],
                ["5", "Eve Brown", "HR", "60000", "4", "True"]
            ]
        
        else:  # sample
            data = [
                ["Name", "Age", "City", "Score"],
                ["Alice", "30", "New York", "85.5"],
                ["Bob", "25", "San Francisco", "92.0"],
                ["Charlie", "35", "Chicago", "78.5"],
                ["Diana", "28", "Boston", "88.0"],
                ["Eve", "32", "Seattle", "91.5"]
            ]
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(data)
        
        await event_queue.enqueue_event(
            new_agent_text_message(f"✅ Created CSV file: {file_path.name}")
        )
    
    async def _show_csv_help(self, event_queue: EventQueue):
        """Show CSV processing help."""
        help_text = """
📊 CSV Processing Agent Help
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 Available Commands:
   • PROCESS_CSV:filename.csv - Analyze CSV structure
   • ANALYZE_CSV:filename.csv - Data quality analysis
   • QUERY_CSV:filename.csv:column:value - Filter CSV data
   • STATS_CSV:filename.csv:column - Calculate statistics
   • CREATE_CSV:name:type - Create sample CSV (types: sample, sales, employees)

📊 Analysis Features:
   • Data type detection
   • Quality assessment
   • Statistical calculations
   • Data filtering and querying
   • Duplicate detection

💡 Examples:
   • CREATE_CSV:sales:sales
   • PROCESS_CSV:sales.csv
   • STATS_CSV:sales.csv:Price
   • QUERY_CSV:sales.csv:Product:Widget
   • ANALYZE_CSV:sales.csv

🎯 Specialized for .csv files
        """
        
        await event_queue.enqueue_event(new_agent_text_message(help_text))
    
    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(new_agent_text_message("CSV processing cancelled."))
