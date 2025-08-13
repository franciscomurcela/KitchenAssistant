# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from rasa_sdk import Action
from rasa_sdk.events import SlotSet
import pymongo

class ActionStoreFeedback(Action):
    def name(self):
        return "action_store_feedback"

    def run(self, dispatcher, tracker, domain):
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client["assessment_db"]
        collection = db["feedback"]

        feedback_text = tracker.latest_message['text']
        collection.insert_one({"feedback": feedback_text})

        dispatcher.utter_message(text="Obrigado pelo teu feedback!")
        return []
