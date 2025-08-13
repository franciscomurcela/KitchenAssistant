# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from .consts import * # O "." é o caminho relativo para o arquivo consts.py
                                        # É necessário meter este "."  caso contrário o rasa não consegue encontrar o arquivo consts.py
import random
import requests
import recipedb_queries as q


class ActionRandomRecipe(Action):
 
    def name(self) -> Text:
        return "action_random_recipe" 
    
    def get_ingredients(self, recipe_id):
        ingredients = q.getIngredients(recipe_id)
        return ingredients
    
    def get_tools(self, recipe_id):
        tools = q.getTools(recipe_id)
        return tools
    
    # Retorna uma receita aleatória id, nome
    def Random(self):
        random_recipe_id = q.getRandomRecipe()
        random_recipe_name = q.getRecipeName(random_recipe_id)
        
        return random_recipe_id, random_recipe_name


    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker, 
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        recipe_id, name = self.Random()
        r_ingredients = self.get_ingredients(recipe_id)
        r_tools = self.get_tools(recipe_id)
        
        message = f"Receita: {name}\n\n\nIngredientes: {r_ingredients}\n\n\nUtensílios: {r_tools}"
        
        dispatcher.utter_message(text=message)
        if recipe_id:
            return [SlotSet("recipe_id", recipe_id)]
        else:
            return []


class ActionSpecifRecipe(Action):
     
        def name(self) -> Text:
            return "action_specific_recipe" 
        
        def get_ingredients(self, recipe_id):
            ingredients = q.getIngredients(recipe_id)
            return ingredients
    
        def get_tools(self, recipe_id):
            tools = q.getTools(recipe_id)
            return tools
        
        def get_recipe_id(self, tag):
            r_id = q.getRecipeByTag(tag)
            return r_id
        
        def run(self, dispatcher: CollectingDispatcher,
                tracker: Tracker, 
                domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            
            tag = tracker.get_slot("receita")
            print("TAG: ", tag)
            
            recipe_id = self.get_recipe_id(tag)[0] 
            print("RECEITA ID: ", recipe_id)
            name = q.getRecipeName(recipe_id)
            print("RECIPE NAME: ",name)
            r_ingredients = self.get_ingredients(recipe_id)
            r_tools = self.get_tools(recipe_id)
            
            message = f"Receita: {name}\n\n\nIngredientes: {r_ingredients}\n\n\nUtensílios: {r_tools}"
            

            dispatcher.utter_message(text=message)
            return []
            
       
class ActionRepeteStep(Action):
    def name(self) -> Text:
        return "action_repeat_step"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker, 
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        r_id = tracker.get_slot("recipe_id")
        s_id = 0
        if r_id == 0:
            message = "Não Existe receita selecionada"
        else:
            next_inst = q.getNextInstruction(r_id, s_id)
            s_id += 1
            message = f"Passo {s_id}: {next_inst}"
        
        dispatcher.utter_message(text=message)
        return []
    
class ActionLogInteraction(Action):
    def name(self) -> Text:
        return "action_log_interaction"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Dados da interação
        user_message = tracker.latest_message.get('text')  # Mensagem do usuário
        intent = tracker.latest_message.get('intent').get('name')  # Intenção detectada
        confidence = tracker.latest_message.get('intent').get('confidence')  # Confiança da intenção
        assistant_response = tracker.latest_message.get('response')  # Resposta do assistente

        # Dados para enviar ao Assessment Manager
        interaction_data = {
            "user_message": user_message,
            "intent": intent,
            "confidence": confidence,
            "assistant_response": assistant_response,
            "interaction_type": "voice_command"  # Ou "touch", dependendo da interação
        }

        # Enviar dados para o Assessment Manager
        try:
            response = requests.post("http://localhost:5002/evaluate", json=interaction_data)
            if response.status_code == 200:
                dispatcher.utter_message(text="Interação registrada com sucesso.")
            else:
                dispatcher.utter_message(text="Erro ao registrar interação.")
        except Exception as e:
            dispatcher.utter_message(text=f"Erro ao conectar ao Assessment Manager: {e}")

        return []