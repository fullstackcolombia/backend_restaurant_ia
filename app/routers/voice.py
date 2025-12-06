from fastapi import APIRouter, HTTPException, UploadFile, File
from app.models import VoiceCommand, VoiceCommandResponse
from app.services.voice_service import voice_service
import tempfile
import os

router = APIRouter(prefix="/voice", tags=["Voice"])


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe un archivo de audio a texto usando Whisper.
    Formatos soportados: mp3, mp4, mpeg, mpga, m4a, wav, webm
    """
    allowed_types = ["audio/mpeg", "audio/mp4", "audio/wav", "audio/webm", "audio/m4a", "audio/x-m4a"]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo de archivo no soportado: {file.content_type}. Use: mp3, mp4, wav, webm, m4a"
        )
    
    # Guardar temporalmente el archivo
    suffix = os.path.splitext(file.filename)[1] if file.filename else ".wav"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        with open(temp_file_path, "rb") as audio_file:
            result = await voice_service.transcribe_audio(audio_file)
        
        if "error" in result and result["error"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    finally:
        # Limpiar archivo temporal
        os.unlink(temp_file_path)


@router.post("/process", response_model=VoiceCommandResponse)
async def process_voice_command(command: VoiceCommand):
    """
    Procesa un comando de voz (texto) y extrae la intención y los items del pedido.
    Usa IA para entender el lenguaje natural.
    """
    if not command.text.strip():
        raise HTTPException(status_code=400, detail="El comando no puede estar vacío")
    
    result = await voice_service.process_voice_command(command.text)
    return VoiceCommandResponse(**result)


@router.post("/order-from-audio")
async def order_from_audio(file: UploadFile = File(...)):
    """
    Pipeline completo: transcribe audio y procesa el pedido.
    Combina transcripción Whisper + procesamiento de IA.
    """
    # Primero transcribir
    allowed_types = ["audio/mpeg", "audio/mp4", "audio/wav", "audio/webm", "audio/m4a", "audio/x-m4a"]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no soportado: {file.content_type}"
        )
    
    suffix = os.path.splitext(file.filename)[1] if file.filename else ".wav"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        with open(temp_file_path, "rb") as audio_file:
            transcription = await voice_service.transcribe_audio(audio_file)
        
        if "error" in transcription and transcription["error"]:
            raise HTTPException(status_code=500, detail=transcription["error"])
        
        # Procesar el texto transcrito
        text = transcription.get("text", "")
        if not text:
            return {
                "transcription": transcription,
                "order": {
                    "understood": False,
                    "message": "No se pudo transcribir el audio"
                }
            }
        
        order_result = await voice_service.process_voice_command(text)
        
        return {
            "transcription": transcription,
            "order": order_result
        }
    finally:
        os.unlink(temp_file_path)
