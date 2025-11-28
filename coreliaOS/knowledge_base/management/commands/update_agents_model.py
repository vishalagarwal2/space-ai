"""
Management command to update AI agents to use cheaper models (gpt-4o-mini)
"""
from django.core.management.base import BaseCommand
from knowledge_base.models import AIAgent


class Command(BaseCommand):
    help = 'Update AI agents to use gpt-4o-mini model (cheaper alternative)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--model',
            type=str,
            default='gpt-4o-mini',
            help='Model to update agents to (default: gpt-4o-mini)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        target_model = options['model']
        
        # Find agents using models that should be updated to gpt-4o-mini
        # Includes expensive models (gpt-4 variants) and older models (gpt-3.5-turbo)
        models_to_update = ['gpt-4', 'gpt-4-turbo', 'gpt-4-32k', 'gpt-3.5-turbo']
        agents_to_update = AIAgent.objects.filter(
            model_provider='openai',
            model_name__in=models_to_update
        )
        
        count = agents_to_update.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('No agents found that need updating.')
            )
            return
        
        self.stdout.write(
            f'Found {count} agent(s) to update:'
        )
        
        for agent in agents_to_update:
            self.stdout.write(
                f'  - {agent.name} (ID: {agent.id}) - Current: {agent.model_name}'
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\nDRY RUN: Would update {count} agent(s) to {target_model}'
                )
            )
        else:
            updated = agents_to_update.update(model_name=target_model)
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSuccessfully updated {updated} agent(s) to {target_model}'
                )
            )

