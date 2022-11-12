# Alexa Prompts Language Constants

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