import logging
import sys

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from telegram import \
    Update, \
    Bot, ReplyKeyboardMarkup, \
    KeyboardButton, ReplyKeyboardRemove
from telegram.ext import \
    CallbackContext, \
    MessageHandler, \
    Filters, \
    Updater, \
    ConversationHandler, \
    CommandHandler
from telegram.utils.request import Request

from mainapp.models import \
    RegionModel, \
    DistrictModel, \
    GatheringModel, \
    EventLocationModel, \
    UserProfile, \
    Register
from tgbot.settings import API_URL

SELECTING_REGION, \
SELECTING_DISTRICT, \
SELECTING_GATHERING, \
SELECTING_EVENT_LOCATION, \
SELECTING_CHOICE, \
SEND_LOCATION \
    = range(6)

logger = logging.getLogger(__name__)


def log_errors(f):
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:

            error_message = f'Хатолик юз берди: {e}'
            print(error_message)
            raise e

    return inner


def _update_profile_and_get(
        update: Update,
        update_region: bool = True,
        region: RegionModel = None,
        update_district: bool = True,
        district: DistrictModel = None,
        update_gathering: bool = True,
        gathering: GatheringModel = None,
        update_event_location: bool = True,
        event_location: EventLocationModel = None,
) -> UserProfile:
    user = update.message.from_user.username
    chat_id = update.message.chat_id
    profile, _ = UserProfile.objects.get_or_create(
        external_id=chat_id,
        defaults={
            'name': user,
            'chat_id': chat_id,
        }
    )

    if update_region:
        profile.region = region

    if update_district:
        profile.district = district

    if update_gathering:
        profile.gathering = gathering

    if update_event_location:
        profile.event_location = event_location

    profile.save()
    return profile


def _show_keyboard(update: Update, message: str, keyboard: list):
    update.message.bot.send_message(
        text=message,
        chat_id=update.message.chat_id, reply_markup=ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
        )
    )


def _region_keyboard(update: Update, message: str):
    _show_keyboard(update=update, message=message, keyboard=[
        [KeyboardButton(s.name)]
        for s in RegionModel.objects.all()
    ])


def _district_keyboard(update: Update, message: str, region: RegionModel):
    districts = DistrictModel.objects.filter(region=region)

    button_list = [
        [KeyboardButton(s.name)]
        for s in districts
    ]

    button_list.insert(0, ['◀️ Ортга қайтиш'])

    _show_keyboard(update=update, message=message, keyboard=button_list)


def _gathering_keyboard(update: Update, message: str, district: DistrictModel):
    gatherings = GatheringModel.objects.filter(district=district)

    button_list = [
        [KeyboardButton(s.name)]
        for s in gatherings
    ]

    button_list.insert(0, ['◀️ Ортга қайтиш'])

    _show_keyboard(update=update, message=message, keyboard=button_list)


def _event_location_keyboard(update: Update, message: str, gathering: GatheringModel):
    event_locations = EventLocationModel.objects.filter(gathering=gathering)

    button_list = [
        [KeyboardButton(s.name)]
        for s in event_locations
    ]

    button_list.insert(0, ['◀️ Ортга қайтиш'])

    _show_keyboard(update=update, message=message, keyboard=button_list)


def _choice_keyboard(update: Update, message: str):
    _show_keyboard(update=update, message=message, keyboard=[
        [KeyboardButton(text="◀️ Ортга қайтиш", resize_keyboard=True)],
        [KeyboardButton(text="Жойлашувни жўнатиш 📍", resize_keyboard=True, request_location=True)]
    ])


def entry(update: Update, context: CallbackContext) -> str:
    user = update.message.from_user.username
    chat_id = update.message.chat_id
    profile, _ = UserProfile.objects.get_or_create(
        external_id=chat_id,
        defaults={
            'name': user,
            'chat_id': chat_id,
        }
    )

    if profile.region is None:
        return region_select(update=update, context=context)
    elif profile.district is None:
        return district_select(update=update, context=context)
    elif profile.gathering is None:
        return gathering_select(update=update, context=context)
    elif profile.event_location is None:
        return event_location_select(update=update, context=context)
    else:
        return start(update=update, context=context)


def start(update: Update, context: CallbackContext) -> str:
    update.message.bot.send_message(
        text=f'Ассалому алайкум, \'{update.message.from_user.username}\'! Янги Ўзбекистон ботга хуш келибсиз!\n\n'
             'Қуйидаги кетма-кетликлар орқали ўз манзилингизни тасдиқлашингиз мумкин.',
        chat_id=update.message.chat_id
    )

    return region_select(update, context)


def region_select(update: Update, context: CallbackContext) -> str:
    profile = _update_profile_and_get(update=update)

    _region_keyboard(update=update, message='\n\nИлтимос, қуйидаги рўйхатдан вилоятингизни танланг! 🔽')

    return SELECTING_REGION


def region_validate(update: Update, context: CallbackContext) -> str:
    text = update.message.text
    profile = _update_profile_and_get(update=update)

    region = RegionModel.objects.filter(name=text).first()

    if region is None:
        _region_keyboard(update=update, message="Афсуски, ушбу жойлашув мавжуд эмас. Қайтадан ҳаракат қилиб кўринг.")
    else:
        profile.region = region
        profile.save()

        return district_select(update=update, context=context)


def district_select(update: Update, context: CallbackContext) -> str:
    profile = _update_profile_and_get(update=update, update_region=False)

    _district_keyboard(
        update=update,
        message=f'Сиз \'{profile.region.name}\'ни танладингиз. Ана энди, туманни танланг! 🔽',
        region=profile.region,
    )

    return SELECTING_DISTRICT


def district_validate(update: Update, context: CallbackContext) -> str:
    text = update.message.text
    profile = _update_profile_and_get(update=update, update_region=False)

    district = DistrictModel.objects.filter(name=text, region=profile.region).first()

    if district is None:
        _district_keyboard(
            update=update,
            message="Афсуски, ушбу жойлашув мавжуд эмас. Қайтадан ҳаракат қилиб кўринг.",
            region=profile.region
        )
    else:
        profile.district = district
        profile.save()

        return gathering_select(update=update, context=context)


def gathering_select(update: Update, context: CallbackContext) -> str:
    profile = _update_profile_and_get(update=update, update_region=False, update_district=False)

    _gathering_keyboard(
        update=update,
        message=f'Қуйидаги рўйхатдан ўз маҳаллангизни танланг. 🔽',
        district=profile.district
    )

    return SELECTING_GATHERING


def gathering_validate(update: Update, context: CallbackContext) -> str:
    text = update.message.text
    profile = _update_profile_and_get(update=update, update_region=False, update_district=False)

    gathering = GatheringModel.objects.filter(name=text, district=profile.district).first()

    if gathering is None:
        _gathering_keyboard(
            update=update,
            message="Афсуски, ушбу жойлашув мавжуд эмас. Қайтадан ҳаракат қилиб кўринг.",
            district=profile.district
        )
    else:
        profile.gathering = gathering
        profile.save()

        event_locations = EventLocationModel.objects.filter(gathering=profile.gathering)

        if len(event_locations) is 0:
            _gathering_keyboard(
                update=update,
                message="Афсуски, ушбу маҳаллада ҳеч қандай тадбир жойи йўқ. Илтимос, модераторингиз "
                        "билан боғланинг.",
                district=profile.district
            )
        else:
            return event_location_select(update=update, context=context)


def event_location_select(update: Update, context: CallbackContext) -> str:
    profile = _update_profile_and_get(update=update, update_region=False, update_district=False, update_gathering=False)

    _event_location_keyboard(
        update=update,
        message=f'Қуйидаги рўйхатдан тадбир ўтказиладиган жойни танланг. 🔽',
        gathering=profile.gathering
    )

    return SELECTING_EVENT_LOCATION


def event_location_validate(update: Update, context: CallbackContext) -> str:
    text = update.message.text
    profile = _update_profile_and_get(
        update=update,
        update_region=False,
        update_district=False,
        update_gathering=False,
    )

    event_location = EventLocationModel.objects.filter(name=text, gathering=profile.gathering).first()

    if event_location is None:
        _event_location_keyboard(
            update=update,
            message="Афсуски, ушбу жойлашув мавжуд эмас. Қайтадан ҳаракат қилиб кўринг.",
            gathering=profile.gathering,
        )

        return gathering_select(update=update, context=context)
    else:
        profile.event_location = event_location
        profile.save()

        return choice_select(update=update, context=context)


def choice_select(update: Update, context: CallbackContext) -> str:
    _choice_keyboard(update=update, message=f'Ана энди аниқ жойлашувингизни жўнатинг.')
    return SELECTING_CHOICE


def choice_validate(update: Update, context: CallbackContext) -> str:
    user_location = update.message.location
    profile = _update_profile_and_get(
        update=update,
        update_region=False,
        update_district=False,
        update_gathering=False,
        update_event_location=False,
    )

    if user_location is None:
        _choice_keyboard(update=update, message=f'Илтимос, жойлашув тугмасидан фойдаланинг.')
    else:
        update.message.reply_text(
            'Жойлашувингизни қабул қилдим. Ботдан фойдаланганингиз учун раҳмат! 😊'
        )

        Register(
            user=profile,
            event_location=profile.event_location,
            lat=user_location.latitude,
            long=user_location.longitude,
        ).save()

        requests.post(API_URL + '/bot-event-location', data={
            'event_location_id': profile.event_location.origin_id,
            'latitude': user_location.latitude,
            'longitude': user_location.longitude,
        })

        return gathering_select(update=update, context=context)


def cancel(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        'Сиз жараённи бекор қилдингиз. Қайтадан бошлаш учун /start\'ни босинг', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


class Command(BaseCommand):
    help = 'TelegramBot'

    def handle(self, *args, **options):
        request = Request(
            connect_timeout=0.5,
            read_timeout=1.0,
        )
        bot = Bot(
            request=request,
            token=settings.TOKEN,
        )

        print(bot.get_me())

        updater = Updater(
            bot=bot,
            use_context=True
        )
        conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(Filters.all, entry)
            ],
            states={
                SELECTING_REGION: [
                    CommandHandler('start', start),
                    CommandHandler('cancel', cancel),
                    MessageHandler(
                        Filters.text,
                        region_validate
                    )
                ],
                SELECTING_DISTRICT: [
                    CommandHandler('start', start),
                    CommandHandler('cancel', cancel),
                    MessageHandler(Filters.text("◀️ Ортга қайтиш"), region_select),
                    MessageHandler(
                        Filters.text,
                        district_validate
                    )
                ],
                SELECTING_GATHERING: [
                    CommandHandler('start', start),
                    CommandHandler('cancel', cancel),
                    MessageHandler(Filters.text("◀️ Ортга қайтиш"), district_select),
                    MessageHandler(
                        Filters.text,
                        gathering_validate
                    )
                ],
                SELECTING_EVENT_LOCATION: [
                    CommandHandler('start', start),
                    CommandHandler('cancel', cancel),
                    MessageHandler(Filters.text("◀️ Ортга қайтиш"), gathering_select),
                    MessageHandler(
                        Filters.text,
                        event_location_validate
                    )
                ],
                SELECTING_CHOICE: [
                    CommandHandler('start', start),
                    CommandHandler('cancel', cancel),
                    MessageHandler(Filters.text("◀️ Ортга қайтиш"), event_location_select),
                    MessageHandler(
                        Filters.location | Filters.text,
                        choice_validate
                    ),
                ],
            },
            fallbacks=[
                CommandHandler(
                    'cancel', cancel
                )
            ],
        )

        try:
            updater.dispatcher.add_handler(conv_handler)
            updater.start_polling()
            updater.idle()
        except:
            sys.exit()
