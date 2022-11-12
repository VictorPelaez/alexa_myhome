# -*- coding: utf-8 -*-
"""HONEYWELL Total Connect app."""

from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.api_client import DefaultApiClient

from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractRequestInterceptor, AbstractResponseInterceptor)
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model.ui import StandardCard
from ask_sdk_model import Response
from ask_sdk_model.ui import AskForPermissionsConsentCard

import logging
import json
import urllib.request
from urllib.request import HTTPError
import requests
from datetime import datetime, timedelta

from utils import readConfig, clean_slot
from cognito import get_u_p



# =========================================================================================================================================
# The items below are the main comments.
# =========================================================================================================================================
SKILL_NAME = 'mi cueva'
BREAK_TIME = '<break time="0.3s"/>'
WELCOME_MESSAGE = ('<say-as interpret-as=\"interjection\">aloha</say-as>' +
                   '.' + BREAK_TIME +
                   '¡bienvenido a ' + SKILL_NAME + '!')
ASK_FOR_HELP = ('Si necesitas ayuda, simplemente di, \'Ayúdame\'.')
ASK_CONTINUE = '¿Te ayudo en algo más?'
HELP_MESSAGE = ('Puedes pedirme que te diga la temperatura de una habitación, \
                por ejemplo diciendo: \'Alexa, Dime la temperatura de salón\'.\
                También puedes preguntarme a qué temperatura esta \
                puesto el punto de consigna en una habitación, simplemente \
                di: \'Alexa,  Qué temperatura hay puesta en salón\'.\
                Puedes cambiar una temperatura, por ejemplo diciendo: \
                \'Alexa,  Pon veinte grados en salón\'. Además puedo darte un \
                resumen de la temperaturas de tu casa y del exterior. \
                Simplemente dime: \'Alexa,  ¿Qué tal mi casa?\' \
                . También acabo de aprender a decirte la habitación más \
                calurosa. Simplemente pregunta: \'Alexa,  ¿Dónde hay la \
                mayor temperatura?\' ')

TEMPERATURE_MESSAGE = ('La temperatura en la habitación {} es de {} grados')
SET_TEMP_MESSAGE = ('La temperatura en la habitación {} está \
                   puesta en {} grados.')
SUMMARY_MESSAGE = ('Tienes {} habitaciones registradas, que se llaman: {}. \
                    La temperatura media en la casa es de {} grados. \
                    {} Además puedo decirte que \
                    afuera hay {} grados con una humedad del {} %')
HELP_REPROMPT = ('¿En qué puedo ayudarte?')
CONFIRM_MESSAGE = '¡vale!'
STOP_MESSAGE = '<say-as interpret-as=\"interjection\">hasta luego</say-as>'
EXCEPTION_MESSAGE = 'Perdona. No puedo ayudarte con eso.'

NOTIFY_MISSING_PERMISSIONS = ('No sé tú email. Necesitaría que me dieras  \
                              permisos en la app de Alexa.')
permissions = ["alexa::profile:email:read"]



def get_session_id(user, password):
    """
    This part generates a session identifier necessary for the rest of requests
    Return:
        - sessionId
        - userID
    """

    config = readConfig()
    hsession_config = config['home_session']

    payload = {}
    payload['username'] = user
    payload['password'] = password
    payload['applicationId'] = hsession_config['application_id']

    url = "https://mytotalconnectcomfort.com/WebApi/api/session"
    params = bytes(json.dumps(payload), encoding="utf-8")
    headers = {'Content-Type': 'application/json'}

    try:
        req = urllib.request.Request(url=url, data=params, headers=headers)
        result = urllib.request.urlopen(req).read().decode("utf-8")
        response = json.loads(result)
        return (response['sessionId'], response['userInfo']['userID'])
    except HTTPError as error:
        print("ERROR skill.index.handler.error:", error)
        return error


def get_temperature(session_id, room_id, mode_temp=True):
    """
    explain this funtion
    """
    hostname = 'https://mytotalconnectcomfort.com'
    path = '/WebApi/api/devices?deviceId=' + str(room_id) + '&allData=True&include={name}'
    url = hostname + path
    headers = {'SessionID': session_id}
    try:
        # If you do not pass the data argument, urllib uses a GET request.
        req = urllib.request.Request(url=url, headers=headers)
        result = urllib.request.urlopen(req).read().decode("utf-8")
        response = json.loads(result)
        if mode_temp:
            return response['thermostat']['indoorTemperature']
        else:
            return response['thermostat']['changeableValues']['heatSetpoint']['value']
    except HTTPError as error:
        print("ERROR skill.index.handler.error:", error)
        return error

    except ValueError as error:
        print("ERROR skill.index.handler.error:", error)
        return error


def set_temperature(session_id, room_id, desired_temp,
                    status="Hold", hours=""):
    """
    Documentation:
    http://docs.python-requests.org/en/latest/user/quickstart/
    {
    "value": 1.0,
    "status": "Scheduled",
    "nextTime": "2019-01-12T14:14:38.8948359-05:00"
    }

    Parameters:
        - session_id
        - room_id
        - desired_temp
    Return:
    """
    if status == "Hold":
        nextTime = ""
    else:
        # SPAIN: GMT+1
        GMT_1 = 1.0
        t = datetime.now() + timedelta(hours=float(hours)+GMT_1)
        nextTime = t.strftime("%Y-%m-%dT%H:%M:%S")

    hostname = 'https://mytotalconnectcomfort.com'
    path = '/WebApi/api/devices/' + str(room_id) + '/thermostat/changeableValues/heatSetpoint'
    url = hostname + path
    headers = {'SessionID': session_id, 'content-type': 'application/json'}
    payload = {"value": float(desired_temp),
               "status": status,
               "nextTime": nextTime}
    try:
        requests.put(url, data=json.dumps(payload), headers=headers)
    except HTTPError as error:
        print("ERROR skill.index.handler.error:", error)
        return error

    except ValueError as error:
        print("ERROR skill.index.handler.error:", error)
        return error


def get_summary(session_id, user_id):
    """
    explain this funtion
    Return:
        - Dictionary with room names and identifiers
        - Temperature outsite, weather
        - Humidity
    """
    hostname = 'https://mytotalconnectcomfort.com'
    path = ('/WebApi/api/locations?userId={}&allData=True&include=thermostatResponse').format(str(user_id))
    url = hostname + path
    headers = {'sessionId': session_id}
    req = urllib.request.Request(url=url, headers=headers)
    result = urllib.request.urlopen(req).read().decode("utf-8")

    # response = json.loads(result[1:-2])
    index_st = result.find("locationID")
    index_end = result.find("canSearchForContractors")
    i_start = index_st-12
    i_end = index_end+len("canSearchForContractors")+12
    response = json.loads(result[i_start:i_end])

    ROOMS = {}
    TEMPS = {}
    for d in response['devices']:
        ROOMS[d['name'].lower()] = d['deviceID']
        TEMPS[d['name'].lower()] = d['thermostat']['indoorTemperature']
    return (ROOMS, TEMPS, response['weather']['temperature'],
            response['weather']['humidity'])


# Utility functions
def get_resolved_value(request, slot_name):
    """Resolve the slot name from the request"""
    try:
        return (request.intent.slots[slot_name].value)
    except (AttributeError, ValueError, KeyError, IndexError, TypeError) as e:
        logger.info("Couldn't resolve {} for request: {}".format(slot_name,
                                                                 request))
        logger.info(str(e))
        return None

# =========================================================================================================================================
# Main skill.
# =========================================================================================================================================


sb = CustomSkillBuilder(api_client=DefaultApiClient())
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# Built-in Intent Handlers
class GetLaunchHandler(AbstractRequestHandler):
    """Handler for Skill Launch Intent."""
    def can_handle(self, handler_input):
        return (is_request_type("LaunchRequest")(handler_input))

    def handle(self, handler_input):
        logger.info("In GetLaunchHandler")
        req_envelope = handler_input.request_envelope
        service_client_fact = handler_input.service_client_factory
        attr = handler_input.attributes_manager.session_attributes

        if not bool(attr):
            attr = {}

        if is_request_type("LaunchRequest")(handler_input):
            attr['welcome'] = WELCOME_MESSAGE

            if not (req_envelope.context.system.user.permissions and
                    req_envelope.context.system.user.permissions.consent_token):
                speech = (WELCOME_MESSAGE + '<break time="0.6s"/>' +
                          NOTIFY_MISSING_PERMISSIONS)
                handler_input.response_builder.set_card(
                    AskForPermissionsConsentCard(permissions=permissions))

            else:
                logger.info('Getting email')
                # get email from user
                user_preferences_client = service_client_fact.get_ups_service()
                email = user_preferences_client.get_profile_email()
                # get email and pass
                logger.info('Logging in cognito with: ' + email)
                (u, p) = get_u_p(email)
                logger.info('Logged in Cognito: ' + u + "...")

                (attr['session_id'],
                 attr['user_id']) = get_session_id(user=u, password=p)
                (attr['rooms'], attr['temperatures'],
                 attr['weather_temperature'],
                 attr['humidity']) = get_summary(attr['session_id'],
                                                 attr['user_id'])

                speech = (WELCOME_MESSAGE + '<break time="0.6s"/>' +
                          ASK_FOR_HELP)

                title_card = 'Mi cueva by @pyhome'
                text_card = 'Skill Alexa Evo Home - Honeywell Total Connect Español'
                handler_input.response_builder.set_card(StandardCard(title=title_card,
                                                                     text=text_card))

        handler_input.attributes_manager.session_attributes = attr
        handler_input.response_builder.speak(speech).ask(HELP_REPROMPT)
        return handler_input.response_builder.response


class GetTemperatureHandler(AbstractRequestHandler):
    """Handler for GetTemperature Intent."""
    def can_handle(self, handler_input):
        return is_intent_name("GetTemperatureIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("In GetTemperatureHandler")

        attr = handler_input.attributes_manager.session_attributes
        if ('session_id' in attr):
            room_name = handler_input.request_envelope.request.intent.slots['room'].value
            room_name = clean_slot(room_name)
            room_id = attr['rooms'][room_name]
            temperature = get_temperature(attr['session_id'], room_id, True)
            speech_ = TEMPERATURE_MESSAGE.format(room_name, str(temperature))
            speech = speech_ + '<break time="0.8s"/>' + ASK_CONTINUE

            card_ = StandardCard(title='Mi casa by @pyhome',
                                 text=speech_)

        else:
            speech = 'perdon, error'
        handler_input.response_builder.speak(speech).ask(HELP_REPROMPT)
        handler_input.response_builder.set_card(card_)
        return handler_input.response_builder.response


class GetMaxTemperatureHandler(AbstractRequestHandler):
    """Handler for Get Maximum Temperature Intent."""
    def can_handle(self, handler_input):
        return is_intent_name("GetMaxTemperatureIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("In GetMaxTemperatureHandler")
        attr = handler_input.attributes_manager.session_attributes

        if ('session_id' in attr):
            temps = attr['temperatures']  # dict with temperatures
            speech = '<say-as interpret-as=\"interjection\">mmh</say-as>' + BREAK_TIME
            speech += 'En la habitación ' + max(temps, key=temps.get)

        else:
            speech = 'perdon, error'
        handler_input.response_builder.speak(speech).ask(HELP_REPROMPT)
        return handler_input.response_builder.response


class GetSetpointHandler(AbstractRequestHandler):
    """Handler for GetTemperature Intent."""
    def can_handle(self, handler_input):
        return is_intent_name("GetSetpointIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("In GetSetpointHandler")

        attr = handler_input.attributes_manager.session_attributes
        if ('session_id' in attr):
            room_name = handler_input.request_envelope.request.intent.slots['room'].value
            room_name = clean_slot(room_name)
            room_id = attr['rooms'][room_name]
            setpoint = get_temperature(attr['session_id'], room_id, False)
            speech = SET_TEMP_MESSAGE.format(room_name, str(setpoint))
            speech = speech + '<break time="0.8s"/>' + ASK_CONTINUE
        else:
            speech = 'perdon, error'
        handler_input.response_builder.speak(speech).ask(HELP_REPROMPT)
        return handler_input.response_builder.response


class SetTemperatureHandler(AbstractRequestHandler):
    """Handler for SetTemperatureIntent."""
    def can_handle(self, handler_input):
        return is_intent_name("SetTemperatureIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("In SetTemperatureIntent")
        attr = handler_input.attributes_manager.session_attributes

        if ('session_id' in attr):
            session_id = attr['session_id']
            room_name = handler_input.request_envelope.request.intent.slots['room'].value
            room_name = clean_slot(room_name)
            room_id = attr['rooms'][room_name]
            desired_temp = handler_input.request_envelope.request.intent.slots['temperature'].value

            resolved_value = (
                get_resolved_value(handler_input.request_envelope.request,
                                   'hours'))
            if (resolved_value is not None):
                status = 'Temporary'
                hours = resolved_value
            else:
                status = 'Hold'
                hours = ""
            set_temperature(session_id, room_id, desired_temp, status, hours)

            speech = CONFIRM_MESSAGE + '<break time="0.8s"/>' + ASK_CONTINUE
        else:
            speech = 'perdon, error'
        handler_input.response_builder.speak(speech).ask(HELP_REPROMPT)
        return handler_input.response_builder.response


class SetTurnOffHandler(AbstractRequestHandler):
    """Handler for SetTemperatureIntent."""
    def can_handle(self, handler_input):
        return is_intent_name("SetTurnOff")(handler_input)

    def handle(self, handler_input):
        logger.info("In SetTurnOff")
        attr = handler_input.attributes_manager.session_attributes

        if ('session_id' in attr):
            session_id = attr['session_id']
            resolved_value = (
                get_resolved_value(handler_input.request_envelope.request,
                                   'hours'))
            if (resolved_value is not None):
                status = 'Temporary'
                hours = resolved_value
            else:
                status = 'Hold'
                hours = ""

            for r in attr['rooms'].values():
                set_temperature(session_id, room_id=r, desired_temp=5,
                                status=status, hours=hours)
            speech = CONFIRM_MESSAGE + '<break time="0.8s"/>' + ASK_CONTINUE
        else:
            speech = 'perdon, error'
        handler_input.response_builder.speak(speech).ask(HELP_REPROMPT)
        return handler_input.response_builder.response


class GetSummaryHandler(AbstractRequestHandler):
    """Handler for GetSummaryIntent."""
    def can_handle(self, handler_input):
        return is_intent_name("GetSummaryIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("In GetSummaryIntent")
        attr = handler_input.attributes_manager.session_attributes

        # session identifier exists
        if ('session_id' in attr):
            rooms = attr['rooms']  # dict with rooms
            temps = attr['temperatures']  # dict with temperatures

            str_Nrooms = str(len(rooms))
            list_rooms = ','.join(list(rooms.keys()))
            Ntemps = len(temps)
            mean_temperature = sum(temps.values())/Ntemps
            str_means = str(float("{0:.2f}".format(mean_temperature)))
            your_temps = ''
            for r in attr['rooms'].keys():
                your_temps += TEMPERATURE_MESSAGE.format(r,
                                                         str(temps[r]))
                your_temps += BREAK_TIME

            weather_temp = attr['weather_temperature']
            humidity = attr['humidity']
            speech = (CONFIRM_MESSAGE + '<break time="0.6s"/>' +
                      SUMMARY_MESSAGE.format(str_Nrooms, list_rooms,
                                             str_means, your_temps,
                                             weather_temp, humidity))
            speech = speech + '<break time="0.8s"/>' + HELP_REPROMPT
            card_ = StandardCard(title='Mi casa by @pyhome',
                                 text=your_temps)
        else:
            speech = 'perdon, error'
        handler_input.response_builder.speak(speech).ask(HELP_REPROMPT)
        handler_input.response_builder.set_card(card_)
        return handler_input.response_builder.response


# Help and Cancel Intent Handlers

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In HelpIntentHandler")
        attr = handler_input.attributes_manager.session_attributes
        if ('session_id' in attr):
            speech = HELP_MESSAGE + HELP_REPROMPT
        else:
            speech = 'perdon, error'

        handler_input.response_builder.speak(speech).ask(HELP_REPROMPT)
        return handler_input.response_builder.response


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In CancelOrStopIntentHandler")

        handler_input.response_builder.speak(STOP_MESSAGE)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In SessionEndedRequestHandler")

        logger.info("Session ended reason: {}".format(
            handler_input.request_envelope.request.reason))
        return handler_input.response_builder.response


# Exception Handler
class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Catch all exception handler, log exception and
    respond with custom message.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.info("In CatchAllExceptionHandler")
        logger.error(exception, exc_info=True)

        speech = EXCEPTION_MESSAGE
        handler_input.response_builder.speak(speech).ask(
            HELP_REPROMPT)

        return handler_input.response_builder.response


# Request and Response loggers
class RequestLogger(AbstractRequestInterceptor):
    """Log the alexa requests."""
    def process(self, handler_input):
        # type: (HandlerInput) -> None
        logger.debug("Alexa Request: {}".format(
            handler_input.request_envelope.request))


class ResponseLogger(AbstractResponseInterceptor):
    """Log the alexa responses."""
    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        logger.debug("Alexa Response: {}".format(response))


# Register intent handlers
sb.add_request_handler(GetLaunchHandler())
sb.add_request_handler(GetTemperatureHandler())
sb.add_request_handler(GetMaxTemperatureHandler())
sb.add_request_handler(GetSetpointHandler())
sb.add_request_handler(SetTemperatureHandler())
sb.add_request_handler(SetTurnOffHandler())
sb.add_request_handler(GetSummaryHandler())

sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

# Register exception handlers
sb.add_exception_handler(CatchAllExceptionHandler())

# TODO: Uncomment the following lines of code for request, response logs.
# sb.add_global_request_interceptor(RequestLogger())
# sb.add_global_response_interceptor(ResponseLogger())

# Handler name that is used on AWS lambda
lambda_handler = sb.lambda_handler()
