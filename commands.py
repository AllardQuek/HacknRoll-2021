from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler, CallbackContext
from general_helpers import user_search

import logging
import ratings
import spoonacular as sp


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


# Instantiate spoonacular api
api_instance = sp.API("7622a72decf948a0b1fb094128e2f884")

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""

    command_options = "As the best MasterChef, there many things I can do. Try me:\n\nsubstitute: Where's the LAMB SAUCE?\n/trivia: Don't be an idiot sandwich.\n/hungry: Freakin' delicious.\n/joke: Very funny!"
    update.message.reply_text(command_options)


def trivia_command(update: Update, context: CallbackContext) -> None:
    """Return a random food trivia."""
    try:
        # Get Random food trivia
        api_response = api_instance.get_random_food_trivia()
        result = api_response.json()['text']
        logger.info(f"Here is the result: {result}")

        return update.message.reply_text(result)
    except Exception as e:
        print("Exception when calling DefaultApi->get_random_food_trivia: %s\n" % e)

    update.message.reply_text(result)


def substitute(update: Update, context: CallbackContext) -> None:
    """Return ingredient substitute(s)."""
    ingredient = update.message.text         # String
    user_id = update.message.from_user.id    # Integer

    logger.info(f"Going to get {ingredient} substitutes...")
    # Query sqlite database for substitute(s)
    sub = user_search(ingredient)
    # * TODO: Ask user for rating
    # STEP 1: Query database to check if user has already rated
    rated = ratings.check_rating(str(user_id), ingredient)     
    
    # STEP 2A: If rated already
    if rated == True:
        # Return formatted response
        update.message.reply_text(text=sub, parse_mode = ParseMode.HTML)
        update.message.reply_text(text="What else do you want to substitute?")
    else:
        # STEP 2B: Else haven't rated
        keyboard = [
            [
                InlineKeyboardButton("Useful", callback_data=f"Useful {ingredient}"),
                InlineKeyboardButton("Not Useful", callback_data=f"Not Useful {ingredient}"),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Return formatted response with ratings
        update.message.reply_text(sub, parse_mode = ParseMode.HTML, reply_markup=reply_markup) 


def hungry_command(update: Update, context: CallbackContext) -> None:
    """Return a random recipe."""
    try:
        # Query for random recipe
        # api_response = api_instance.get_random_recipes(limit_license=limit_license, tags=tags, number=number)
        api_response = api_instance.get_random_recipes(number=1)
        recipe_res = api_response.json()['recipes'][0]
        logger.info(f"Here is the response: {api_response}")

        title = recipe_res['title']
        image = recipe_res['image']
        url = recipe_res['spoonacularSourceUrl']

        update.message.reply_text(f"This will satisfy your hunger!\n\n{title}: {url}")
        update.message.reply_photo(image)
    except Exception as e:
        print("Exception when calling DefaultApi->get_random_food_trivia: %s\n" % e)


def joke_command(update: Update, context: CallbackContext) -> None:
    """Return a random food joke."""
    try:
        # Get a random food joke
        response = api_instance.get_a_random_food_joke()
        data = response.json()
        joke = data['text']
        logger.info(f"Here is the response: {response}")

        update.message.reply_text(joke)
    except Exception as e:
        print("Exception when calling DefaultApi->get_random_food_trivia: %s\n" % e)


def update_rating(update: Update, context: CallbackContext) -> None:
    """Update database with user's usefulness rating."""
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    reply_list = query.data.split()

    # Extract callback data: usefulness and ingredient
    if reply_list[0] == "Useful":
        usefulness = "Useful"
        ingredient = " ".join(reply_list[1:])
    else:
        usefulness = "Not Useful"
        ingredient = " ".join(reply_list[2:])

    # Reply with what the user selected
    reply_markup = InlineKeyboardMarkup([])
    query.edit_message_reply_markup(reply_markup)
    query.message.reply_text(text=f"Thank you for your feedback! You selected: {usefulness}\n\nWhat else do you want to substitute?")

    user_id = query.from_user.id    # Integer

    # Update the database with user's rating
    if usefulness == "Useful":
        logger.info("Adding positive rating...")
        ratings.positive_rating(str(user_id), ingredient)      
    else:
        logger.info("Adding negative rating...")
        ratings.negative_rating(str(user_id), ingredient)


def end(update: Update, context: CallbackContext) -> int:
    """/end will say bye if user wants to end the session."""
    # TODO: Tell bot to stop listening for input
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)

    # https://giphy.com/gifs/foxtv-gordon-ramsay-hells-kitchen-f-off-ylyUQnaWJp7TRAGInK
    update.message.reply_video("https://media.giphy.com/media/ylyUQnaWJp7TRAGInK/giphy.mp4")