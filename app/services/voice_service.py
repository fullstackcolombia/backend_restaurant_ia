import openai
from typing import Optional
import json
import re
from app.config import get_settings
from app.services.menu_service import menu_service
from app.services.table_service import table_service

settings = get_settings()

# Configurar OpenAI
if settings.openai_api_key:
    openai.api_key = settings.openai_api_key


class VoiceService:
    """Servicio para procesar comandos de voz y transcripciones"""
    
    @staticmethod
    async def transcribe_audio(audio_file) -> dict:
        """Transcribe audio usando Whisper de OpenAI"""
        if not settings.openai_api_key:
            return {"error": "OpenAI API key not configured", "text": ""}
        
        try:
            client = openai.OpenAI(api_key=settings.openai_api_key)
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="es"
            )
            return {
                "text": transcript.text,
                "language": "es"
            }
        except Exception as e:
            return {"error": str(e), "text": ""}
    
    @staticmethod
    async def process_voice_command(text: str) -> dict:
        """Procesa un comando de voz y extrae la intención y los items"""
        
        # Primero verificar comandos especiales (mesa y confirmar)
        special_command = await VoiceService._check_special_commands(text)
        if special_command:
            return special_command
        
        if not settings.openai_api_key:
            return await VoiceService._process_command_locally(text)
        
        try:
            # Obtener el menú actual para contexto
            menu = await menu_service.get_full_menu()
            menu_context = VoiceService._format_menu_for_ai(menu)
            
            client = openai.OpenAI(api_key=settings.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"""Eres un asistente de restaurante que procesa pedidos por voz.
                        
MENÚ DISPONIBLE:
{menu_context}

Tu tarea es:
1. Entender el pedido del cliente
2. Identificar los items del menú que quiere
3. Extraer cantidades
4. Responder en formato JSON

COMANDOS ESPECIALES QUE DEBES DETECTAR:
- Si el usuario dice "mesa X" o "quiero mesa X" o "para la mesa X", la acción es "select_table" y debes incluir table_number
- Si el usuario dice "confirmar", "enviar pedido", "listo", "confirmar pedido", la acción es "confirm_order"
- Si el usuario dice "cancelar pedido" o "borrar todo", la acción es "clear_cart"

Responde SIEMPRE con este formato JSON:
{{
    "understood": true/false,
    "action": "order" | "question" | "cancel" | "modify" | "select_table" | "confirm_order" | "clear_cart" | "unknown",
    "items": [
        {{"name": "nombre del item", "quantity": número, "menu_item_id": id_si_lo_conoces}}
    ],
    "table_number": número_de_mesa_si_aplica,
    "message": "Resumen de lo entendido",
    "suggested_response": "Respuesta sugerida para el cliente"
}}

Si no entiendes algo, pregunta amablemente."""
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            
            # Intentar parsear el JSON
            try:
                # Buscar JSON en la respuesta
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
            
            return {
                "understood": True,
                "action": "unknown",
                "items": [],
                "message": result,
                "suggested_response": result
            }
            
        except Exception as e:
            return {
                "understood": False,
                "action": "error",
                "items": [],
                "message": f"Error procesando comando: {str(e)}",
                "suggested_response": "Lo siento, hubo un error. ¿Podrías repetir tu pedido?"
            }
    
    @staticmethod
    async def _check_special_commands(text: str) -> Optional[dict]:
        """Detecta comandos especiales como selección de mesa y confirmación"""
        text_lower = text.lower().strip()
        
        # Log para debug
        print(f"[VOICE] Procesando comando: '{text_lower}'")
        
        # Detectar pregunta por mesas disponibles
        available_patterns = [
            r'(?:qué|que|cuáles|cuales)\s+mesas?\s+(?:hay|están|estan|tenemos|tienen)\s*(?:disponibles?|libres?)?',
            r'mesas?\s+(?:disponibles?|libres?)',
            r'(?:hay|tienen|tenemos)\s+mesas?\s+(?:disponibles?|libres?)',
            r'(?:dime|dame|muéstrame|muestrame)\s+(?:las\s+)?mesas?\s*(?:disponibles?|libres?)?',
            r'(?:cuántas|cuantas)\s+mesas?\s+(?:hay|quedan)',
        ]
        
        for pattern in available_patterns:
            if re.search(pattern, text_lower):
                print(f"[VOICE] Coincidió patrón mesas disponibles: {pattern}")
                # Consultar mesas disponibles
                tables = await table_service.get_tables()
                available_tables = [t for t in tables if t.get('status') == 'available']
                
                if available_tables:
                    table_numbers = [str(t['number']) for t in available_tables]
                    if len(available_tables) == 1:
                        response = f"Hay una mesa disponible: la mesa {table_numbers[0]}."
                    else:
                        response = f"Hay {len(available_tables)} mesas disponibles: {', '.join(table_numbers[:-1])} y {table_numbers[-1]}."
                else:
                    response = "Lo siento, no hay mesas disponibles en este momento."
                
                return {
                    "understood": True,
                    "action": "list_tables",
                    "items": [],
                    "available_tables": [t['number'] for t in available_tables],
                    "message": f"Mesas disponibles: {len(available_tables)}",
                    "suggested_response": response
                }
        
        # Detectar selección de mesa - Patrones muy flexibles
        # Captura: "mesa 3", "meza 5", "mesa número 5", "la mesa 2", "en mesa 4", "quiero mesa 1"
        # También números escritos: "mesa tres", "mesa cinco"
        
        # Primero intentar extraer número del texto
        numero_palabras = {
            'uno': 1, 'una': 1, 'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5,
            'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10,
            'once': 11, 'doce': 12
        }
        
        table_patterns = [
            r'(?:quiero|dame|para|en|la|ponme|asigna)?\s*(?:mesa|meza)\s*(?:número|numero|#)?\s*(\d+)',
            r'(?:mesa|meza)\s+(\d+)',
            r'(?:mesa|meza)\s+(uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce)',
        ]
        
        for pattern in table_patterns:
            match = re.search(pattern, text_lower)
            if match:
                captured = match.group(1)
                # Convertir palabra a número si es necesario
                if captured in numero_palabras:
                    table_num = numero_palabras[captured]
                else:
                    table_num = int(captured)
                
                print(f"[VOICE] Mesa detectada: {table_num} del patrón: {pattern}")
                
                # Verificar si la mesa está disponible
                tables = await table_service.get_tables()
                target_table = next((t for t in tables if t['number'] == table_num), None)
                available_tables = [t for t in tables if t.get('status') == 'available']
                
                if target_table is None:
                    # La mesa no existe
                    available_nums = [str(t['number']) for t in available_tables]
                    if available_nums:
                        response = f"La mesa {table_num} no existe. Las mesas disponibles son: {', '.join(available_nums)}."
                    else:
                        response = f"La mesa {table_num} no existe y no hay mesas disponibles."
                    return {
                        "understood": True,
                        "action": "table_error",
                        "items": [],
                        "available_tables": [t['number'] for t in available_tables],
                        "message": f"Mesa {table_num} no existe",
                        "suggested_response": response
                    }
                elif target_table.get('status') != 'available':
                    # La mesa existe pero no está disponible
                    available_nums = [str(t['number']) for t in available_tables]
                    status_text = {
                        'occupied': 'ocupada',
                        'reserved': 'reservada',
                        'cleaning': 'en limpieza'
                    }.get(target_table.get('status'), 'no disponible')
                    
                    if available_nums:
                        response = f"La mesa {table_num} está {status_text}. Las mesas disponibles son: {', '.join(available_nums)}."
                    else:
                        response = f"La mesa {table_num} está {status_text} y no hay otras mesas disponibles."
                    return {
                        "understood": True,
                        "action": "table_unavailable",
                        "items": [],
                        "table_number": table_num,
                        "available_tables": [t['number'] for t in available_tables],
                        "message": f"Mesa {table_num} {status_text}",
                        "suggested_response": response
                    }
                else:
                    # La mesa está disponible
                    return {
                        "understood": True,
                        "action": "select_table",
                        "items": [],
                        "table_number": table_num,
                        "message": f"Seleccionando mesa {table_num}",
                        "suggested_response": f"Perfecto, he seleccionado la mesa {table_num}."
                    }
        
        # Detectar nombre del cliente - MUY FLEXIBLE
        # Patrones: "a nombre de X", "es para X", "pedido para X", "cliente X", etc.
        name_patterns = [
            r'(?:a\s+)?nombre\s+(?:de\s+)?([a-záéíóúñü]+)',
            r'(?:es\s+)?para\s+([a-záéíóúñü]+)',
            r'(?:el\s+)?(?:pedido|orden)\s+(?:es\s+)?(?:para|de)\s+([a-záéíóúñü]+)',
            r'(?:el\s+)?cliente\s+(?:es\s+|se\s+llama\s+)?([a-záéíóúñü]+)',
            r'se\s+llama\s+([a-záéíóúñü]+)',
            r'(?:ponlo|ponle|registra(?:lo)?|anota(?:lo)?)\s+(?:a\s+nombre\s+de\s+|como\s+|para\s+)?([a-záéíóúñü]+)',
            r'(?:mi\s+)?nombre\s+(?:es\s+)?([a-záéíóúñü]+)',
            r'soy\s+([a-záéíóúñü]+)',
            r'(?:pedido|orden)\s+de\s+([a-záéíóúñü]+)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text_lower)
            if match:
                # Capitalizar el nombre
                customer_name = match.group(1).capitalize()
                print(f"[VOICE] Nombre detectado: {customer_name}")
                return {
                    "understood": True,
                    "action": "set_customer_name",
                    "items": [],
                    "customer_name": customer_name,
                    "message": f"Nombre: {customer_name}",
                    "suggested_response": f"Perfecto, el pedido está a nombre de {customer_name}."
                }
        
        # Detectar confirmación de pedido
        confirm_patterns = [
            r'\b(?:confirmar?|enviar?|mandar?)\s*(?:el\s+)?(?:pedido|orden)\b',
            r'\b(?:confirmar?|confirma|enviar?|envía|listo|lista)\b',
            r'\beso\s+es\s+todo\b',
            r'\bproceder\b',
            r'\bhaz\s+(?:el\s+)?pedido\b',
        ]
        
        for pattern in confirm_patterns:
            if re.search(pattern, text_lower):
                return {
                    "understood": True,
                    "action": "confirm_order",
                    "items": [],
                    "message": "Confirmando pedido",
                    "suggested_response": "¡Perfecto! Enviando tu pedido a cocina."
                }
        
        # Detectar cancelación/limpiar carrito
        clear_patterns = [
            r'\b(?:cancelar?|borrar?|limpiar?|vaciar?)\s*(?:el\s+)?(?:pedido|carrito|orden|todo)\b',
            r'\b(?:quitar?|eliminar?)\s+todo\b',
            r'\bempezar?\s+de\s+nuevo\b',
        ]
        
        for pattern in clear_patterns:
            if re.search(pattern, text_lower):
                return {
                    "understood": True,
                    "action": "clear_cart",
                    "items": [],
                    "message": "Cancelando pedido",
                    "suggested_response": "He cancelado tu pedido. ¿Deseas ordenar algo más?"
                }
        
        return None  # No es un comando especial
    
    @staticmethod
    def _format_menu_for_ai(menu: dict) -> str:
        """Formatea el menú para el contexto de la IA"""
        lines = []
        for category in menu.get("categories", []):
            lines.append(f"\n## {category.get('name', 'Sin categoría')}")
            for item in category.get("items", []):
                lines.append(f"- ID:{item.get('id')} {item.get('name')} - ${item.get('price', 0):.2f}")
                if item.get('description'):
                    lines.append(f"  ({item.get('description')})")
        return "\n".join(lines)
    
    @staticmethod
    async def _process_command_locally(text: str) -> dict:
        """Procesamiento básico sin IA (fallback)"""
        text_lower = text.lower()
        
        # Palabras clave para detectar intención
        order_keywords = ["quiero", "dame", "quisiera", "me da", "ponme", "tráeme", "pido"]
        cancel_keywords = ["cancelar", "cancela", "quitar", "eliminar"]
        question_keywords = ["tienen", "hay", "cuánto", "qué", "cuál", "precio"]
        
        action = "unknown"
        if any(kw in text_lower for kw in order_keywords):
            action = "order"
        elif any(kw in text_lower for kw in cancel_keywords):
            action = "cancel"
        elif any(kw in text_lower for kw in question_keywords):
            action = "question"
        
        # Buscar items en el menú
        menu_items = await menu_service.get_menu_items()
        found_items = []
        
        for item in menu_items:
            if item["name"].lower() in text_lower:
                # Intentar encontrar cantidad
                quantity = 1
                words = text_lower.split()
                for i, word in enumerate(words):
                    if item["name"].lower() in word or word in item["name"].lower():
                        # Buscar número antes del item
                        if i > 0:
                            prev_word = words[i-1]
                            if prev_word.isdigit():
                                quantity = int(prev_word)
                            elif prev_word in ["una", "un", "uno"]:
                                quantity = 1
                            elif prev_word in ["dos", "doble"]:
                                quantity = 2
                            elif prev_word in ["tres", "triple"]:
                                quantity = 3
                
                found_items.append({
                    "name": item["name"],
                    "quantity": quantity,
                    "menu_item_id": item["id"]
                })
        
        return {
            "understood": len(found_items) > 0 or action != "unknown",
            "action": action,
            "items": found_items,
            "message": f"Entendí: {text}",
            "suggested_response": "¿Es correcto tu pedido?" if found_items else "¿Podrías repetir tu pedido?"
        }


voice_service = VoiceService()
