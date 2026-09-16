import inspect
import traceback
from collections.abc import Callable
from typing import Any


class ManageError:
    def _error(self, variables: dict[str, Any], conditions: dict[str, Callable] | None = None):
        erreurs = []
        
        for nom, valeur in variables.items():
            if valeur is None:
                erreurs.append(f"'{nom}' is None")
            
            if conditions and nom in conditions and not conditions[nom](valeur):
                    erreurs.append(f"'{nom}' = {valeur!r} does not meet the condition")
        
        if erreurs:
            frame = inspect.currentframe().f_back
            ligne = frame.f_lineno
            fichier = frame.f_code.co_filename
            
            message = (
                f"[Verification ERROR] (file: {fichier}, line: {ligne})\n"
                + "\n".join(f"  - {e}" for e in erreurs)
            )
            print(message)
            # raise ValueError(message)
            return True
        return False


    def ma_fonction(self, variable1, variable2, variable3=None):
        # Vérification en une seule ligne
        self._verifier(
            variables={
                "variable1": variable1,
                "variable2": variable2,
                "variable3": variable3,
            },
            conditions={
                "variable1": lambda v: isinstance(v, (int, float)) and v > 0,
                "variable2": lambda v: isinstance(v, str) and len(v) > 0,
                "variable3": lambda v: v is None or isinstance(v, list),
            }
        )