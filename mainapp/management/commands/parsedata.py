from django.core.management.base import BaseCommand
import requests

from mainapp.models import RegionModel, DistrictModel, GatheringModel, EventLocationModel
from tgbot.settings import API_URL


class Command(BaseCommand):
    help = 'ParseData'

    def handle(self, *args, **options):
        provinces = requests.post(API_URL + '/bot-provinces')

        for province in provinces.json():
            province_object, _ = RegionModel.objects.get_or_create(
                origin_id=province['id'],
                defaults={
                    'name': province['name']
                },
            )

            regions = requests.post(API_URL + '/bot-regions', data={
                'province_id': province['id']
            })

            for region in regions.json():
                region_object, _ = DistrictModel.objects.get_or_create(
                    origin_id=region['id'],
                    defaults={
                        'name': region['name'],
                        'region': province_object
                    },
                )

                mahallas = requests.post(API_URL + '/bot-mahallas', data={
                    'region_id': region['id']
                })

                for mahalla in mahallas.json():
                    mahalla_object, _ = GatheringModel.objects.get_or_create(
                        origin_id=mahalla['id'],
                        district=region_object,
                        defaults={
                            'name': mahalla['name']
                        },
                    )

                    for event_location in mahalla['event_locations']:
                        print(event_location)
                        event_location, _ = EventLocationModel.objects.get_or_create(
                            origin_id=event_location['id'],
                            gathering=mahalla_object,
                            defaults={
                                'name': event_location['name'],
                            },
                        )
