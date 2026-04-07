"""
Django Management Command to Retrain ML Weights
Usage: python manage.py retrain_ml_weights
"""

from django.core.management.base import BaseCommand
from accounts.ml_weight_optimizer import retrain_weights
import json


class Command(BaseCommand):
    help = 'Retrain ML model weights based on real placement data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n🚀 Starting ML Weight Retraining...'))
        self.stdout.write(self.style.WARNING('This may take a few minutes...\n'))

        try:
            result = retrain_weights()

            if result['success']:
                self.stdout.write(self.style.SUCCESS('\n✅ Retraining Completed Successfully!\n'))

                insights = result['insights']

                # Display summary
                self.stdout.write(self.style.SUCCESS('📊 SUMMARY:'))
                self.stdout.write(f'  Total Students: {insights["total_students"]}')
                self.stdout.write(f'  Placed Students: {insights["placed_students"]}')
                self.stdout.write(f'  Placement Rate: {insights["placement_rate"]:.1f}%\n')

                # Display optimal weights
                self.stdout.write(self.style.SUCCESS('🎯 OPTIMIZED WEIGHTS:'))
                for feature, weight in insights['optimal_weights'].items():
                    percentage = weight * 100
                    self.stdout.write(f'  {feature.title():12} : {weight:.4f} ({percentage:5.1f}%)')

                self.stdout.write('')

                # Display top factors
                self.stdout.write(
                    self.style.SUCCESS(
                        f'⭐ Most Important Factor: {insights["top_factor"].title()} '
                        f'({insights["top_factor_weight"]*100:.1f}%)'
                    )
                )

                # Display model performance
                self.stdout.write(self.style.SUCCESS('\n📈 MODEL PERFORMANCE:'))
                for model_name, metrics in insights['model_performance'].items():
                    self.stdout.write(f'\n  {model_name}:')
                    self.stdout.write(f'    ROC-AUC Score: {metrics["roc_auc"]:.4f}')
                    self.stdout.write(f'    CV Mean:       {metrics["cv_mean"]:.4f}')
                    self.stdout.write(f'    CV Std Dev:    {metrics["cv_std"]:.4f}')

                self.stdout.write(
                    self.style.SUCCESS(
                        '\n✅ Weights have been saved and will be used for future readiness'
                        ' score calculations!\n'
                    )
                )

            else:
                self.stdout.write(self.style.ERROR(f'\n❌ Error: {result["message"]}\n'))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Unexpected error: {str(e)}\n')
            )
