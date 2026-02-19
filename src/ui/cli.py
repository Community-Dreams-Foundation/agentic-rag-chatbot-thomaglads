"""Command-line interface for Codex."""

import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agent import ComplianceAgent
from src.utils import logger

# Load environment variables
load_dotenv()

# Setup logging
logger.info("Starting Codex CLI")


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """Codex - Operational Risk & Compliance Agent"""
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose
    
    # Check for NVIDIA API key
    if not os.getenv('NVIDIA_API_KEY'):
        click.echo("[ERROR] NVIDIA_API_KEY not found in environment.", err=True)
        click.echo("Please set your NVIDIA API key in .env file or environment.", err=True)
        sys.exit(1)


@cli.command()
@click.argument('files', nargs=-1, required=True)
@click.option('--type', '-t', default='safety_manual', help='Document type')
@click.pass_context
def ingest(ctx, files, type):
    """Ingest documents into the system"""
    click.echo("[INIT] Initializing Codex...")
    agent = ComplianceAgent()
    
    click.echo(f"[FILE] Ingesting {len(files)} document(s)...")
    chunks = agent.ingest_documents(list(files), document_type=type)
    
    click.echo(f"[OK] Ingested {chunks} chunks successfully!")
    
    if ctx.obj['VERBOSE']:
        stats = agent.get_stats()
        click.echo(f"[STATS] Total documents in database: {stats['documents']['document_count']}")


@cli.command()
@click.option('--site', '-s', required=True, help='Site location (e.g., "Boston")')
@click.option('--operation', '-o', default='outdoor work', help='Type of operation')
@click.pass_context
def check(ctx, site, operation):
    """Check safety compliance for a site"""
    click.echo("[INIT] Initializing Codex...")
    agent = ComplianceAgent()
    
    click.echo(f"\n[CHECK] Checking safety for {operation} at {site}...")
    click.echo("=" * 60)
    
    decision = agent.check_site_safety(
        site_location=site,
        operation_type=operation,
    )
    
    # Display results
    click.echo(f"\n📍 Site: {decision.site_location}")
    click.echo(f"🔧 Operation: {decision.operation_type}")
    click.echo(f"⏰ Check Time: {decision.timestamp}")
    
    # Display weather
    if decision.weather_compliance:
        weather = decision.weather_compliance
        click.echo(f"\n[WEATHER]  Weather Compliance:")
        click.echo(f"   Status: {weather['compliance_status']}")
        
        if weather['violations']:
            click.echo(f"   [WARN]  Violations Found:")
            for v in weather['violations']:
                click.echo(f"      - {v['date']}:")
                for issue in v['issues']:
                    click.echo(f"        - {issue}")
    
    # Display decision
    click.echo(f"\n[OK] DECISION:")
    status = "[OK] SAFE TO PROCEED" if decision.can_proceed else "[FAIL] DO NOT PROCEED"
    click.echo(f"   {status}")
    click.echo(f"\n[INFO] Reasoning:")
    click.echo(f"   {decision.reasoning}")
    
    if decision.recommendations:
        click.echo(f"\n[TIP] Recommendations:")
        for rec in decision.recommendations:
            click.echo(f"   - {rec}")
    
    # Display citations
    if decision.citations:
        click.echo(f"\n[DOC] Sources:")
        for citation in decision.citations[:3]:  # Show top 3
            click.echo(f"   [{citation['number']}] {citation['filename']} "
                      f"(relevance: {citation['relevance_score']})")
    
    if decision.new_memories:
        click.echo(f"\n[SAVE] New memories saved:")
        for mem in decision.new_memories:
            click.echo(f"   - [{mem['type']}] {mem['content']}")


@cli.command()
@click.argument('question')
@click.option('--site', '-s', help='Site context')
@click.pass_context
def ask(ctx, question, site):
    """Ask a question about compliance/safety"""
    click.echo("[INIT] Initializing Codex...")
    agent = ComplianceAgent()
    
    click.echo(f"\n[Q] Question: {question}")
    click.echo("=" * 60)
    
    result = agent.ask_question(question, site_location=site)
    
    click.echo(f"\n[A] Answer:")
    click.echo(result['answer'])
    
    if result['citations']:
        click.echo(f"\n[DOC] Sources:")
        for citation in result['citations'][:3]:
            click.echo(f"   [{citation['number']}] {citation['filename']}")


@cli.command()
def stats():
    """Show system statistics"""
    click.echo("[INIT] Initializing Codex...")
    agent = ComplianceAgent()
    
    stats = agent.get_stats()
    
    click.echo("\n[STATS] System Statistics:")
    click.echo("=" * 40)
    click.echo(f"Documents in database: {stats['documents']['document_count']}")
    click.echo(f"Collection: {stats['documents']['collection_name']}")
    click.echo(f"Storage: {stats['documents']['persist_directory']}")


@cli.command()
def demo():
    """Run a demo safety check"""
    click.echo("[DEMO] Running Demo...")
    click.echo("=" * 60)
    
    agent = ComplianceAgent()
    
    # Demo scenarios
    scenarios = [
        {
            "site": "Boston",
            "operation": "crane operation",
        },
        {
            "site": "Site Alpha",
            "operation": "roof repair",
        },
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        click.echo(f"\n[SCENARIO] Scenario {i}: {scenario['operation']} at {scenario['site']}")
        click.echo("-" * 60)
        
        decision = agent.check_site_safety(
            site_location=scenario['site'],
            operation_type=scenario['operation'],
        )
        
        status = "[OK] SAFE" if decision.can_proceed else "[FAIL] UNSAFE"
        click.echo(f"Result: {status}")
        click.echo(f"Reasoning: {decision.reasoning[:100]}...")
        
        if decision.weather_compliance:
            click.echo(f"Weather: {decision.weather_compliance['compliance_status']}")


def main():
    """Entry point"""
    cli()


if __name__ == '__main__':
    main()
