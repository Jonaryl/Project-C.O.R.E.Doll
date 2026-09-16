import asyncio
import threading

from core.agent import Agent
from interface.main_interface import App

# You should now have access to our previous message in this conversation. From my introduction. Tell me if you can't access them.
# Hello, i'm Jonaryl, the developpeur of your cognitive systems.
agent = Agent()
app = App(agent=agent)


def start_asyncio_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

async def agent_startup():
    await agent.main()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    
    asyncio_thread = threading.Thread(target=start_asyncio_loop, args=(loop,),name="AsyncioLoop", daemon=True)
    asyncio_thread.start()    
    agent_future = asyncio.run_coroutine_threadsafe(agent_startup(), loop)    

    try:
        app.mainloop()
    finally:
        print("SHUTTING DOWN")

        agent.stop()
        loop.call_soon_threadsafe(loop.stop)
        asyncio_thread.join(timeout=3)

        print("END")



# NEXT : 

#### IDEA
#### generates pairs of responses for the same prompt. Evaluates which response is better based on ?

# v1 tout les engine : 
## Perception Engine
### VISION

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! A FAIRE
# regarder pour mettre focus
# regarder pour ajouter objet de la scene
# STOP apres face model
# regarder pour mettre modele vrai analyse  


### SENSORS

## Attention Engine - détection de changements / événements importants
## Data Engine - mémoire + connaissances + état
## World Model Engine - environnement, objets, personnes, temps, état - Maintenir une représentation de la situation actuelle
## Self / Consciousness Engine - identité, capacités, état interne, limites - Maintenir le modèle de soi
## Priority Engine - urgence, danger, intérêt, besoins, objectifs - Évaluer ce qui est important maintenant
## Planning Engine - étapes, alternatives, conséquences prévues - Transformer objectifs + situation en plan
## Consequence Engine - résultat, erreur, nouvelle information, expérience - Analyser ce qui s'est passé après une action
## 
## Learning Engine - propositions de nouvelles connaissances/règles
## Consolidation Engine - fusion, oubli, classement, résumé, relations
## 
## 
## Action Engine ??? texte, mouvement, appel d'outil, etc.
## Emotion Engine ??? valence, activation, déclencheurs, évolution
###### A VOIR AUSSI : PREDICTIONS

# DONE : 

### AUDIO : V2 : better person manager