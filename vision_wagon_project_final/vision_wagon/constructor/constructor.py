import logging
from typing import Dict, Any, Optional, List, Literal

logger = logging.getLogger(__name__)

from vision_wagon.core.shared_enums import ContentType, GenerationStatus
from vision_wagon.config.config_manager import get_config
from vision_wagon.security.security_validator import get_security_validator
from vision_wagon.database.database import db_manager
from vision_wagon.core.shared_models import GeneratedContent, ContentRequest

import os
import asyncio
import aiohttp
import json
import hashlib
import aiofiles
from datetime import datetime
from io import BytesIO
import base64
from PIL import Image, ImageDraw, ImageFont

class Constructor:
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa el constructor.
        
        Args:
            config: Configuración del constructor
        """
        self.config_manager = get_config()
        self.security_validator = get_security_validator()
        
        # Configuración de APIs
        self.api_configs = {
            'openai': self.config_manager.get_api_config('openai'),
            'anthropic': self.config_manager.get_api_config('anthropic'),
            'stability': self.config_manager.get_api_config('stability'),
            'elevenlabs': self.config_manager.get_api_config('elevenlabs'),
            'replicate': self.config_manager.get_api_config('replicate')
        }
        
        # Directorios de trabajo
        self.content_dir = "generated_content"
        self.temp_dir = "temp"
        self.cache_dir = "cache"
        
        # Crear directorios si no existen
        for directory in [self.content_dir, self.temp_dir, self.cache_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Cache de contenido generado
        self.content_cache: Dict[str, GeneratedContent] = {}
        self.generation_queue: Dict[str, ContentRequest] = {}
        
        # Plantillas y estilos
        self.templates = {}
        self.style_presets = {}
        
        # Métricas
        self.metrics = {
            'content_generated': 0,
            'generation_time_avg': 0.0,
            'cache_hits': 0,
            'api_calls': 0,
            'errors': 0
        }
        
        logger.info("Constructor inicializado")

    async def initialize(self) -> None:
        """Inicializa el constructor"""
        try:
            # Verificar APIs disponibles
            await self._check_api_availability()
            
            # Cargar plantillas y presets
            await self._load_templates()
            await self._load_style_presets()
            
            # Verificar directorios
            self._ensure_directories()
            
            logger.info("Constructor inicializado exitosamente")
            
        except Exception as e:
            logger.error(f"Error inicializando Constructor: {str(e)}")
            raise

    async def _check_api_availability(self) -> None:
        """Verifica disponibilidad de APIs de IA generativa"""
        available_apis = []
        
        # OpenAI
        if self.api_configs['openai']['api_key']:
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {'Authorization': f"Bearer {self.api_configs['openai']['api_key']}"}
                    async with session.get('https://api.openai.com/v1/models', headers=headers) as response:
                        if response.status == 200:
                            available_apis.append('openai')
            except Exception as e:
                logger.warning(f"OpenAI API no disponible: {str(e)}")
        
        # Stability AI
        if self.api_configs['stability']['api_key']:
            available_apis.append('stability')  # Asumimos disponible si hay key
        
        # ElevenLabs
        if self.api_configs['elevenlabs']['api_key']:
            available_apis.append('elevenlabs')
        
        logger.info(f"APIs disponibles: {available_apis}")
        self.available_apis = available_apis

    def _ensure_directories(self) -> None:
        """Asegura que existan los directorios necesarios"""
        subdirs = ['images', 'audio', 'video', 'documents', 'websites', 'social']
        
        for subdir in subdirs:
            path = os.path.join(self.content_dir, subdir)
            os.makedirs(path, exist_ok=True)

    async def _load_templates(self) -> None:
        """Carga plantillas de contenido"""
        self.templates = {
            'social_post': {
                'instagram': {
                    'dimensions': (1080, 1080),
                    'format': 'square',
                    'text_overlay': True,
                    'brand_placement': 'bottom_right'
                },
                'twitter': {
                    'dimensions': (1200, 675),
                    'format': 'landscape',
                    'text_overlay': True,
                    'character_limit': 280
                },
                'linkedin': {
                    'dimensions': (1200, 627),
                    'format': 'landscape',
                    'professional_tone': True
                }
            },
            'website': {
                'landing_page': {
                    'sections': ['hero', 'features', 'testimonials', 'cta'],
                    'responsive': True,
                    'seo_optimized': True
                },
                'blog_post': {
                    'structure': ['title', 'intro', 'body', 'conclusion', 'cta'],
                    'seo_optimized': True
                }
            },
            'document': {
                'report': {
                    'sections': ['executive_summary', 'introduction', 'analysis', 'conclusions', 'recommendations'],
                    'include_charts': True,
                    'professional_format': True
                },
                'presentation': {
                    'slide_types': ['title', 'content', 'image', 'chart', 'conclusion'],
                    'max_slides': 20,
                    'consistent_design': True
                }
            }
        }

    async def _load_style_presets(self) -> None:
        """Carga presets de estilo"""
        self.style_presets = {
            'modern': {
                'colors': ['#2563eb', '#1f2937', '#f3f4f6', '#ffffff'],
                'fonts': ['Inter', 'Roboto', 'Open Sans'],
                'style': 'clean, minimalist, professional'
            },
            'creative': {
                'colors': ['#7c3aed', '#ec4899', '#f59e0b', '#10b981'],
                'fonts': ['Poppins', 'Montserrat', 'Playfair Display'],
                'style': 'bold, artistic, expressive'
            },
            'corporate': {
                'colors': ['#1e40af', '#374151', '#6b7280', '#f9fafb'],
                'fonts': ['Arial', 'Helvetica', 'Times New Roman'],
                'style': 'professional, trustworthy, conservative'
            },
            'tech': {
                'colors': ['#0ea5e9', '#06b6d4', '#8b5cf6', '#1f2937'],
                'fonts': ['JetBrains Mono', 'Fira Code', 'Source Code Pro'],
                'style': 'futuristic, technical, innovative'
            }
        }

    async def generate_content(self, content_type: ContentType, prompt: str,
                             parameters: Dict[str, Any] = None,
                             style_guide: Dict[str, Any] = None,
                             brand_guidelines: Dict[str, Any] = None,
                             target_audience: str = None,
                             platform: str = None) -> str:
        """
        Genera contenido según los parámetros especificados.
        
        Args:
            content_type: Tipo de contenido a generar
            prompt: Prompt o descripción del contenido
            parameters: Parámetros específicos de generación
            style_guide: Guía de estilo
            brand_guidelines: Directrices de marca
            target_audience: Audiencia objetivo
            platform: Plataforma de destino
            
        Returns:
            ID de la solicitud de generación
        """
        # Crear solicitud
        request = ContentRequest(
            request_id=self._generate_request_id(),
            content_type=content_type,
            prompt=prompt,
            parameters=parameters or {},
            style_guide=style_guide,
            brand_guidelines=brand_guidelines,
            target_audience=target_audience,
            platform=platform
        )
        
        # Agregar a cola
        self.generation_queue[request.request_id] = request
        
        logger.info(f"Solicitud de generación creada: {request.request_id} ({content_type.value})")
        
        # Procesar de forma asíncrona
        asyncio.create_task(self._process_generation_request(request))
        
        return request.request_id

    def _generate_request_id(self) -> str:
        """Genera un ID único para la solicitud"""
        timestamp = str(int(datetime.utcnow().timestamp()))
        random_part = hashlib.md5(os.urandom(16)).hexdigest()[:8]
        return f"gen_{timestamp}_{random_part}"

    async def _process_generation_request(self, request: ContentRequest) -> None:
        """Procesa una solicitud de generación de contenido"""
        try:
            request.status = GenerationStatus.GENERATING
            start_time = datetime.utcnow()
            
            # Verificar cache
            cache_key = self._generate_cache_key(request)
            if cache_key in self.content_cache:
                logger.info(f"Cache hit para solicitud {request.request_id}")
                request.result = self.content_cache[cache_key].__dict__
                request.status = GenerationStatus.COMPLETED
                request.completed_at = datetime.utcnow()
                self.metrics['cache_hits'] += 1
                return
            
            # Generar contenido según el tipo
            if request.content_type == ContentType.TEXT:
                result = await self._generate_text(request)
            elif request.content_type == ContentType.IMAGE:
                result = await self._generate_image(request)
            elif request.content_type == ContentType.AUDIO:
                result = await self._generate_audio(request)
            elif request.content_type == ContentType.VIDEO:
                result = await self._generate_video(request)
            elif request.content_type == ContentType.DOCUMENT:
                result = await self._generate_document(request)
            elif request.content_type == ContentType.PRESENTATION:
                result = await self._generate_presentation(request)
            elif request.content_type == ContentType.WEBSITE:
                result = await self._generate_website(request)
            elif request.content_type == ContentType.SOCIAL_POST:
                result = await self._generate_social_post(request)
            else:
                raise ValueError(f"Tipo de contenido no soportado: {request.content_type}")
            
            # Guardar resultado
            request.result = result.__dict__
            request.status = GenerationStatus.COMPLETED
            request.completed_at = datetime.utcnow()
            
            # Agregar a cache
            self.content_cache[cache_key] = result
            
            # Actualizar métricas
            generation_time = (request.completed_at - start_time).total_seconds()
            self._update_metrics(generation_time)
            
            logger.info(f"Contenido generado exitosamente: {request.request_id}")
            
        except Exception as e:
            request.status = GenerationStatus.FAILED
            request.error = str(e)
            request.completed_at = datetime.utcnow()
            self.metrics['errors'] += 1
            
            logger.error(f"Error generando contenido {request.request_id}: {str(e)}")

    def _generate_cache_key(self, request: ContentRequest) -> str:
        """Genera clave de cache para una solicitud"""
        cache_data = {
            'content_type': request.content_type.value,
            'prompt': request.prompt,
            'parameters': request.parameters,
            'style_guide': request.style_guide,
            'platform': request.platform
        }
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()

    async def _generate_text(self, request: ContentRequest) -> GeneratedContent:
        """Genera contenido de texto usando LLMs"""
        if 'openai' not in self.available_apis:
            raise Exception("OpenAI API no disponible para generación de texto")
        
        # Construir prompt optimizado
        optimized_prompt = await self._optimize_text_prompt(request)
        
        # Parámetros de generación
        params = {
            'model': request.parameters.get('model', 'gpt-3.5-turbo'),
            'messages': [{'role': 'user', 'content': optimized_prompt}],
            'max_tokens': request.parameters.get('max_tokens', 1000),
            'temperature': request.parameters.get('temperature', 0.7),
            'top_p': request.parameters.get('top_p', 1.0)
        }
        
        # Llamada a API
        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': f"Bearer {self.api_configs['openai']['api_key']}",
                'Content-Type': 'application/json'
            }
            
            async with session.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=params
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Error en API OpenAI: {error_text}")
                
                data = await response.json()
                generated_text = data['choices'][0]['message']['content']
        
        # Crear contenido generado
        content = GeneratedContent(
            content_id=f"text_{self._generate_content_id()}",
            content_type=ContentType.TEXT,
            title=request.parameters.get('title', 'Texto Generado'),
            description=f"Texto generado basado en: {request.prompt[:100]}...",
            content_data=generated_text,
            metadata={
                'model_used': params['model'],
                'tokens_used': data.get('usage', {}).get('total_tokens', 0),
                'prompt_tokens': data.get('usage', {}).get('prompt_tokens', 0),
                'completion_tokens': data.get('usage', {}).get('completion_tokens', 0)
            },
            size_bytes=len(generated_text.encode('utf-8'))
        )
        
        # Guardar en archivo
        file_path = os.path.join(self.content_dir, 'documents', f"{content.content_id}.txt")
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(generated_text)
        
        content.file_path = file_path
        
        self.metrics['api_calls'] += 1
        return content

    async def _optimize_text_prompt(self, request: ContentRequest) -> str:
        """Optimiza el prompt para generación de texto"""
        base_prompt = request.prompt
        
        # Agregar contexto de audiencia
        if request.target_audience:
            base_prompt += f"\n\nAudiencia objetivo: {request.target_audience}"
        
        # Agregar contexto de plataforma
        if request.platform:
            base_prompt += f"\nPlataforma: {request.platform}"
        
        # Agregar guía de estilo
        if request.style_guide:
            style_info = []
            if 'tone' in request.style_guide:
                style_info.append(f"Tono: {request.style_guide['tone']}")
            if 'style' in request.style_guide:
                style_info.append(f"Estilo: {request.style_guide['style']}")
            if 'length' in request.style_guide:
                style_info.append(f"Longitud: {request.style_guide['length']}")
            
            if style_info:
                base_prompt += f"\n\nGuía de estilo: {', '.join(style_info)}"
        
        # Agregar directrices de marca
        if request.brand_guidelines:
            brand_info = []
            if 'voice' in request.brand_guidelines:
                brand_info.append(f"Voz de marca: {request.brand_guidelines['voice']}")
            if 'values' in request.brand_guidelines:
                brand_info.append(f"Valores: {', '.join(request.brand_guidelines['values'])}")
            
            if brand_info:
                base_prompt += f"\n\nDirectrices de marca: {', '.join(brand_info)}"
        
        return base_prompt

    async def _generate_image(self, request: ContentRequest) -> GeneratedContent:
        """Genera imágenes usando modelos de difusión"""
        if 'stability' not in self.available_apis:
            # Fallback: generar imagen placeholder
            return await self._generate_placeholder_image(request)
        
        # Optimizar prompt para imagen
        optimized_prompt = await self._optimize_image_prompt(request)
        
        # Parámetros de generación
        params = {
            'text_prompts': [{'text': optimized_prompt}],
            'cfg_scale': request.parameters.get('cfg_scale', 7),
            'height': request.parameters.get('height', 512),
            'width': request.parameters.get('width', 512),
            'samples': request.parameters.get('samples', 1),
            'steps': request.parameters.get('steps', 30)
        }
        
        # Llamada a Stability AI
        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': f"Bearer {self.api_configs['stability']['api_key']}",
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            async with session.post(
                'https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image',
                headers=headers,
                json=params
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Error en Stability AI: {error_text}")
                
                data = await response.json()
                
                # Obtener imagen generada
                image_data = data['artifacts'][0]['base64']
                image_bytes = base64.b64decode(image_data)
        
        # Crear contenido generado
        content = GeneratedContent(
            content_id=f"img_{self._generate_content_id()}",
            content_type=ContentType.IMAGE,
            title=request.parameters.get('title', 'Imagen Generada'),
            description=f"Imagen generada: {request.prompt[:100]}...",
            content_data=image_bytes,
            dimensions=(params['width'], params['height']),
            metadata={
                'prompt': optimized_prompt,
                'cfg_scale': params['cfg_scale'],
                'steps': params['steps']
            },
            size_bytes=len(image_bytes)
        )
        
        # Guardar imagen
        file_path = os.path.join(self.content_dir, 'images', f"{content.content_id}.png")
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(image_bytes)
        
        content.file_path = file_path
        
        # Generar thumbnail
        thumbnail_path = await self._generate_thumbnail(file_path)
        content.thumbnail = thumbnail_path
        
        self.metrics['api_calls'] += 1
        return content

    async def _generate_placeholder_image(self, request: ContentRequest) -> GeneratedContent:
        """Genera imagen placeholder cuando no hay API disponible"""
        width = request.parameters.get('width', 512)
        height = request.parameters.get('height', 512)
        
        # Crear imagen placeholder
        image = Image.new('RGB', (width, height), color='#f0f0f0')
        draw = ImageDraw.Draw(image)
        
        # Agregar texto
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        text = "Imagen Generada\n(Placeholder)"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill='#666666', font=font, align='center')
        
        # Guardar imagen
        content_id = f"img_{self._generate_content_id()}"
        file_path = os.path.join(self.content_dir, 'images', f"{content_id}.png")
        image.save(file_path)
        
        # Convertir a bytes
        img_buffer = BytesIO()
        image.save(img_buffer, format='PNG')
        image_bytes = img_buffer.getvalue()
        
        content = GeneratedContent(
            content_id=content_id,
            content_type=ContentType.IMAGE,
            title=request.parameters.get('title', 'Imagen Placeholder'),
            description=f"Imagen placeholder: {request.prompt[:100]}...",
            content_data=image_bytes,
            file_path=file_path,
            dimensions=(width, height),
            metadata={'type': 'placeholder'},
            size_bytes=len(image_bytes)
        )
        
        return content

    async def _optimize_image_prompt(self, request: ContentRequest) -> str:
        """Optimiza el prompt para generación de imágenes"""
        base_prompt = request.prompt
        
        # Agregar estilo si está especificado
        if request.style_guide and 'style' in request.style_guide:
            base_prompt += f", {request.style_guide['style']} style"
        
        # Agregar calidad y detalles técnicos
        quality_terms = request.parameters.get('quality_terms', ['high quality', 'detailed', '8k'])
        base_prompt += f", {', '.join(quality_terms)}"
        
        # Agregar términos negativos si están especificados
        negative_terms = request.parameters.get('negative_prompt')
        if negative_terms:
            base_prompt += f" --no {negative_terms}"
        
        return base_prompt

    async def _generate_thumbnail(self, image_path: str) -> str:
        """Genera thumbnail de una imagen"""
        try:
            with Image.open(image_path) as img:
                img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                
                thumbnail_path = image_path.replace('.png', '_thumb.png')
                img.save(thumbnail_path)
                
                return thumbnail_path
        except Exception as e:
            logger.error(f"Error generando thumbnail: {str(e)}")
            return None

    async def _generate_audio(self, request: ContentRequest) -> GeneratedContent:
        """Genera audio usando síntesis de voz"""
        if 'elevenlabs' not in self.available_apis:
            raise Exception("ElevenLabs API no disponible para generación de audio")
        
        text = request.prompt
        voice_id = request.parameters.get('voice_id', 'default')
        
        # Parámetros de síntesis
        params = {
            'text': text,
            'model_id': request.parameters.get('model_id', 'eleven_monolingual_v1'),
            'voice_settings': {
                'stability': request.parameters.get('stability', 0.5),
                'similarity_boost': request.parameters.get('similarity_boost', 0.5)
            }
        }
        
        # Llamada a ElevenLabs
        async with aiohttp.ClientSession() as session:
            headers = {
                'Accept': 'audio/mpeg',
                'Content-Type': 'application/json',
                'xi-api-key': self.api_configs['elevenlabs']['api_key']
            }
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            async with session.post(url, headers=headers, json=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Error en ElevenLabs: {error_text}")
                
                data = await response.read()
        
        # Crear contenido generado
        content = GeneratedContent(
            content_id=f"audio_{self._generate_content_id()}",
            content_type=ContentType.AUDIO,
            title=request.parameters.get('title', 'Audio Generado'),
            description=f"Audio generado: {text[:100]}...",
            content_data=data,
            metadata={
                'voice_id': voice_id,
                'text_length': len(text),
                'model_id': params['model_id']
            },
            size_bytes=len(data)
        )
        
        # Guardar audio
        file_path = os.path.join(self.content_dir, 'audio', f"{content.content_id}.mp3")
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(data)
        
        content.file_path = file_path
        
        self.metrics['api_calls'] += 1
        return content

    async def _generate_video(self, request: ContentRequest) -> GeneratedContent:
        """Genera video (placeholder - requiere integración con APIs de video)"""
        # Por ahora, crear un placeholder
        content = GeneratedContent(
            content_id=f"video_{self._generate_content_id()}",
            content_type=ContentType.VIDEO,
            title=request.parameters.get('title', 'Video Generado'),
            description=f"Video placeholder: {request.prompt[:100]}...",
            content_data="Video generation not implemented yet",
            metadata={'type': 'placeholder'},
            duration=request.parameters.get('duration', 30.0)
        )
        
        return content

    async def _generate_document(self, request: ContentRequest) -> GeneratedContent:
        """Genera documentos estructurados"""
        # Generar contenido de texto base
        text_request = ContentRequest(
            request_id=f"{request.request_id}_text",
            content_type=ContentType.TEXT,
            prompt=request.prompt,
            parameters=request.parameters,
            style_guide=request.style_guide,
            brand_guidelines=request.brand_guidelines
        )
        
        text_content = await self._generate_text(text_request)
        
        # Estructurar como documento
        document_content = self._structure_document(text_content.content_data, request)
        
        content = GeneratedContent(
            content_id=f"doc_{self._generate_content_id()}",
            content_type=ContentType.DOCUMENT,
            title=request.parameters.get('title', 'Documento Generado'),
            description=f"Documento: {request.prompt[:100]}...",
            content_data=document_content,
            metadata={
                'format': request.parameters.get('format', 'markdown'),
                'sections': request.parameters.get('sections', [])
            }
        )
        
        # Guardar documento
        file_extension = 'md' if request.parameters.get('format') == 'markdown' else 'txt'
        file_path = os.path.join(self.content_dir, 'documents', f"{content.content_id}.{file_extension}")
        
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(document_content)
        
        content.file_path = file_path
        content.size_bytes = len(document_content.encode('utf-8'))
        
        return content

    def _structure_document(self, text: str, request: ContentRequest) -> str:
        """Estructura texto como documento formal"""
        doc_type = request.parameters.get('document_type', 'report')
        
        if doc_type == 'report':
            # Estructurar como reporte
            structured = f"""# {request.parameters.get('title', 'Reporte Generado')}\n\n## Resumen Ejecutivo\n\n{text[:500]}...\n\n## Introducción\n\n{text}\n\n## Análisis\n\n[Análisis detallado basado en el contenido generado]\n\n## Conclusiones\n\n[Conclusiones derivadas del análisis]\n\n## Recomendaciones\n\n[Recomendaciones específicas]\n\n---\n*Documento generado automáticamente el {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}*\n"""
        else:
            # Formato básico
            structured = f"""# {request.parameters.get('title', 'Documento Generado')}\n\n{text}\n\n---\n*Generado el {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}*\n"""
        
        return structured

    async def _generate_presentation(self, request: ContentRequest) -> GeneratedContent:
        """Genera presentaciones estructuradas"""
        # Por ahora, generar estructura básica
        slides = []
        
        # Slide de título
        slides.append({
            'type': 'title',
            'title': request.parameters.get('title', 'Presentación Generada'),
            'subtitle': request.parameters.get('subtitle', 'Generada automáticamente'),
            'content': ''
        })
        
        # Generar contenido para slides
        slide_count = request.parameters.get('slide_count', 5)
        
        for i in range(1, slide_count):
            slide_prompt = f"Crear contenido para slide {i} sobre: {request.prompt}"
            
            text_request = ContentRequest(
                request_id=f"{request.request_id}_slide_{i}",
                content_type=ContentType.TEXT,
                prompt=slide_prompt,
                parameters={'max_tokens': 200}
            )
            
            text_content = await self._generate_text(text_request)
            
            slides.append({
                'type': 'content',
                'title': f'Punto {i}',
                'content': text_content.content_data
            })
        
        presentation_data = {
            'title': request.parameters.get('title', 'Presentación Generada'),
            'slides': slides,
            'theme': request.parameters.get('theme', 'modern')
        }
        
        content = GeneratedContent(
            content_id=f"pres_{self._generate_content_id()}",
            content_type=ContentType.PRESENTATION,
            title=request.parameters.get('title', 'Presentación Generada'),
            description=f"Presentación: {request.prompt[:100]}...",
            content_data=presentation_data,
            metadata={
                'slide_count': len(slides),
                'theme': presentation_data['theme']
            }
        )
        
        # Guardar como JSON
        file_path = os.path.join(self.content_dir, 'documents', f"{content.content_id}.json")
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(presentation_data, indent=2, ensure_ascii=False))
        
        content.file_path = file_path
        
        return content

    async def _generate_website(self, request: ContentRequest) -> GeneratedContent:
        """Genera sitios web básicos"""
        site_type = request.parameters.get('site_type', 'landing_page')
        
        # Generar contenido para diferentes secciones
        sections = {}
        
        if site_type == 'landing_page':
            section_prompts = {
                'hero': f"Crear sección hero para: {request.prompt}",
                'features': f"Crear sección de características para: {request.prompt}",
                'testimonials': f"Crear testimonios para: {request.prompt}",
                'cta': f"Crear call-to-action para: {request.prompt}"
            }
            
            for section_name, section_prompt in section_prompts.items():
                text_request = ContentRequest(
                    request_id=f"{request.request_id}_{section_name}",
                    content_type=ContentType.TEXT,
                    prompt=section_prompt,
                    parameters={'max_tokens': 300}
                )
                
                section_content = await self._generate_text(text_request)
                sections[section_name] = section_content.content_data
        
        # Generar HTML
        html_content = self._generate_html_template(sections, request)
        
        content = GeneratedContent(
            content_id=f"web_{self._generate_content_id()}",
            content_type=ContentType.WEBSITE,
            title=request.parameters.get('title', 'Sitio Web Generado'),
            description=f"Sitio web: {request.prompt[:100]}...",
            content_data=html_content,
            metadata={
                'site_type': site_type,
                'sections': list(sections.keys())
            }
        )
        
        # Guardar HTML
        file_path = os.path.join(self.content_dir, 'websites', f"{content.content_id}.html")
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(html_content)
        
        content.file_path = file_path
        content.size_bytes = len(html_content.encode('utf-8'))
        
        return content

    def _generate_html_template(self, sections: Dict[str, str], request: ContentRequest) -> str:
        """Genera plantilla HTML básica"""
        title = request.parameters.get('title', 'Sitio Web Generado')
        html = f"""<!DOCTYPE html>\n<html lang=\"es\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>{title}</title>\n    <style>\n        body {{\n            font-family: Arial, sans-serif;\n            margin: 0;\n            padding: 0;\n            line-height: 1.6;\n        }}\n        .container {{\n            max-width: 1200px;\n            margin: 0 auto;\n            padding: 0 20px;\n        }}\n        .section {{\n            padding: 60px 0;\n        }}\n        .hero {{\n            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);\n            color: white;\n            text-align: center;\n        }}\n        .features {{\n            background: #f8f9fa;\n        }}\n        .cta {{\n            background: #007bff;\n            color: white;\n            text-align: center;\n        }}\n        .btn {{\n            display: inline-block;\n            padding: 12px 30px;\n            background: #28a745;\n            color: white;\n            text-decoration: none;\n            border-radius: 5px;\n            margin-top: 20px;\n        }}\n    </style>\n</head>\n<body>\n"""
        
        # Agregar secciones
        for section_name, section_content in sections.items():
            html += f"""\n    <section class=\"section {section_name}\">\n        <div class=\"container\">\n            <h2>{section_name.title()}</h2>\n            <p>{section_content}</p>\n        </div>\n    </section>\n"""
        
        html += """\n</body>\n</html>\n"""
        
        return html

    async def _generate_social_post(self, request: ContentRequest) -> GeneratedContent:
        platform = request.platform or 'instagram'
        
        # Obtener plantilla de la plataforma
        platform_template = self.templates['social_post'].get(platform, {})
        
        # Generar texto del post
        text_prompt = f"Crear post para {platform} sobre: {request.prompt}"
        if 'character_limit' in platform_template:
            text_prompt += f" (máximo {platform_template['character_limit']} caracteres)"
        
        text_request = ContentRequest(
            request_id=f"{request.request_id}_text",
            content_type=ContentType.TEXT,
            prompt=text_prompt,
            parameters={'max_tokens': 150},
            style_guide=request.style_guide
        )
        
        text_content = await self._generate_text(text_request)
        
        # Generar imagen si es necesario
        image_content = None
        if platform_template.get('text_overlay') or request.parameters.get('include_image', True):
            image_prompt = f"Imagen para post de {platform}: {request.prompt}"
            
            image_request = ContentRequest(
                request_id=f"{request.request_id}_image",
                content_type=ContentType.IMAGE,
                prompt=image_prompt,
                parameters={
                    'width': platform_template.get('dimensions', (1080, 1080))[0],
                    'height': platform_template.get('dimensions', (1080, 1080))[1]
                }
            )
            
            image_content = await self._generate_image(image_request)
        
        # Combinar contenido
        post_data = {
            'platform': platform,
            'text': text_content.content_data,
            'image_path': image_content.file_path if image_content else None,
            'hashtags': request.parameters.get('hashtags', []),
            'mentions': request.parameters.get('mentions', [])
        }
        
        content = GeneratedContent(
            content_id=f"social_{self._generate_content_id()}",
            content_type=ContentType.SOCIAL_POST,
            title=f"Post para {platform.title()}",
            description=f"Post de {platform}: {request.prompt[:100]}...",
            content_data=post_data,
            metadata={
                'platform': platform,
                'has_image': image_content is not None,
                'text_length': len(text_content.content_data)
            }
        )
        
        # Guardar como JSON
        file_path = os.path.join(self.content_dir, 'social', f"{content.content_id}.json")
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(post_data, indent=2, ensure_ascii=False))
        
        content.file_path = file_path
        
        return content

    def _generate_content_id(self) -> str:
        """Genera ID único para contenido"""
        timestamp = str(int(datetime.utcnow().timestamp()))
        random_part = hashlib.md5(os.urandom(8)).hexdigest()[:6]
        return f"{timestamp}_{random_part}"

    def _update_metrics(self, generation_time: float) -> None:
        """Actualiza métricas del constructor"""
        self.metrics['content_generated'] += 1
        
        # Actualizar tiempo promedio
        current_avg = self.metrics['generation_time_avg']
        total_generated = self.metrics['content_generated']
        
        self.metrics['generation_time_avg'] = (
            (current_avg * (total_generated - 1) + generation_time) / total_generated
        )

    # Métodos de consulta
    
    def get_generation_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado de una solicitud de generación"""
        if request_id in self.generation_queue:
            request = self.generation_queue[request_id]
            return {
                'request_id': request.request_id,
                'content_type': request.content_type.value,
                'status': request.status.value,
                'created_at': request.created_at.isoformat(),
                'completed_at': request.completed_at.isoformat() if request.completed_at else None,
                'error': request.error,
                'result': request.result
            }
        
        return None

    def get_generated_content(self, content_id: str) -> Optional[GeneratedContent]:
        """Obtiene contenido generado por ID"""
        for content in self.content_cache.values():
            if content.content_id == content_id:
                return content
        
        return None

    def list_generated_content(self, content_type: ContentType = None, 
                             limit: int = 50) -> List[Dict[str, Any]]:
        """Lista contenido generado con filtros"""
        contents = list(self.content_cache.values())
        
        if content_type:
            contents = [c for c in contents if c.content_type == content_type]
        
        # Ordenar por fecha de creación (más reciente primero)
        contents.sort(key=lambda x: x.created_at, reverse=True)
        
        # Limitar resultados
        contents = contents[:limit]
        
        # Convertir a diccionarios
        return [
            {
                'content_id': c.content_id,
                'content_type': c.content_type.value,
                'title': c.title,
                'description': c.description,
                'created_at': c.created_at.isoformat(),
                'file_path': c.file_path,
                'size_bytes': c.size_bytes,
                'metadata': c.metadata
            }
            for c in contents
        ]

    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del constructor"""
        return {
            **self.metrics,
            'cache_size': len(self.content_cache),
            'queue_size': len(self.generation_queue),
            'available_apis': self.available_apis
        }

    async def cleanup(self) -> None:
        """Limpia recursos del constructor"""
        # Limpiar cache
        self.content_cache.clear()
        self.generation_queue.clear()
        
        logger.info("Constructor limpiado")

    async def generate_agent_skeleton(self, agent_id: str, agent_type: str, description: str) -> None:
        """
        Genera el esqueleto de un nuevo agente en el directorio apropiado.
        """
        agent_filename = f"{agent_id.lower()}_agent.py"
        
        if agent_type == "executive":
            agent_dir = os.path.join("/home/ubuntu/vision_wagon/agents", "executive")
        elif agent_type == "operational":
            agent_dir = os.path.join("/home/ubuntu/vision_wagon/agents", "operational")
        else:
            agent_dir = os.path.join("/home/ubuntu/vision_wagon/agents", "custom") # Directorio por defecto
            os.makedirs(agent_dir, exist_ok=True)

        agent_path = os.path.join(agent_dir, agent_filename)

        template = f"""from vision_wagon.core.base_agent import BaseAgent, AgentResult
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class {agent_id}Agent(BaseAgent):
    agent_id: str = \"{agent_id.lower()}\"
    agent_type: str = \"{agent_type}\"
    description: str = \"{description}\"
    capabilities: list = [] # Define las capacidades específicas de este agente

    async def initialize(self) -> None:
        # Lógica de inicialización específica para {agent_id}Agent
        logger.info(f\"Inicializando {{self.agent_id}}Agent...\")
        await super().initialize()

    async def process(self, context: Dict[str, Any]) -> AgentResult:
        # Lógica de procesamiento específica para {agent_id}Agent
        logger.info(f\"{{self.agent_id}}Agent procesando solicitud: {{context.get(\"operation\", \"N/A\")}}\")
        # Implementa aquí la lógica de tu agente
        # Ejemplo: return AgentResult(success=True, data={{\"message\": \"Procesado por {{self.agent_id}}\"}})
        return AgentResult(success=False, error=\"Método process no implementado para {{self.agent_id}}Agent.\")

    async def cleanup(self) -> None:
        # Lógica de limpieza específica para {agent_id}Agent
        logger.info(f\"Limpiando {{self.agent_id}}Agent...\")
        await super().cleanup()
"""

        async with aiofiles.open(agent_path, mode="w", encoding="utf-8") as f:
            await f.write(template)
        logger.info(f"Esqueleto de agente {agent_id} creado en {agent_path}")






_constructor_instance: Optional[Constructor] = None

def get_constructor() -> Constructor:
    global _constructor_instance
    if _constructor_instance is None:
        _constructor_instance = Constructor()
    return _constructor_instance


